"""
Monitoring Service - Advanced Alerting and Anomaly Detection
Port: 8013
Provides intelligent alerting, anomaly detection, and metric aggregation.
"""
import asyncio
import hashlib
import logging
import statistics
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Callable, Optional

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    SERVICE_NAME: str = "monitoring-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8013
    REDIS_URL: str = "redis://redis:6379/10"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    ALERT_DEDUP_WINDOW_SECONDS: int = 300
    ANOMALY_WINDOW_SIZE: int = 100
    ANOMALY_THRESHOLD: float = 2.5
    SLACK_WEBHOOK_URL: Optional[str] = None
    PAGERDUTY_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class Metric:
    """Represents a metric data point."""

    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class Alert:
    """Represents an alert."""

    id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    source: str
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    fired_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    acknowledged_by: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None


@dataclass
class AlertRule:
    """Defines an alerting rule."""

    name: str
    expression: str
    threshold: float
    comparison: str
    severity: AlertSeverity
    for_duration: int = 0
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


class AnomalyDetector:
    """Statistical anomaly detection using Z-score and IQR methods."""

    def __init__(self, window_size: int = 100, threshold: float = 2.5):
        self.window_size = window_size
        self.threshold = threshold
        self.metric_windows: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=window_size)
        )

    def add_metric(self, metric: Metric) -> Optional[dict]:
        """Add metric and check for anomalies."""
        key = f"{metric.name}:{':'.join(f'{k}={v}' for k, v in sorted(metric.labels.items()))}"
        window = self.metric_windows[key]
        window.append(metric.value)

        if len(window) < 10:
            return None

        anomaly = self._detect_zscore(list(window), metric.value)
        if anomaly:
            return {
                "metric": metric.name,
                "value": metric.value,
                "expected_range": anomaly["expected_range"],
                "zscore": anomaly["zscore"],
                "labels": metric.labels,
            }
        return None

    def _detect_zscore(self, values: list[float], current: float) -> Optional[dict]:
        """Detect anomaly using Z-score method."""
        if len(values) < 3:
            return None

        mean = statistics.mean(values[:-1])
        stdev = statistics.stdev(values[:-1]) if len(values) > 2 else 0

        if stdev == 0:
            return None

        zscore = (current - mean) / stdev

        if abs(zscore) > self.threshold:
            return {
                "zscore": round(zscore, 2),
                "expected_range": (
                    round(mean - self.threshold * stdev, 2),
                    round(mean + self.threshold * stdev, 2),
                ),
            }
        return None


class AlertManager:
    """Advanced alerting with deduplication and routing."""

    def __init__(self):
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: deque[Alert] = deque(maxlen=1000)
        self.alert_counts: dict[str, int] = defaultdict(int)
        self.last_alert_time: dict[str, float] = {}
        self.rules: dict[str, AlertRule] = {}
        self.anomaly_detector = AnomalyDetector(
            window_size=settings.ANOMALY_WINDOW_SIZE,
            threshold=settings.ANOMALY_THRESHOLD,
        )

    def add_rule(self, rule: AlertRule):
        """Add or update an alerting rule."""
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, name: str):
        """Remove an alerting rule."""
        self.rules.pop(name, None)

    async def process_metric(self, metric: Metric) -> list[Alert]:
        """Process a metric and check against all rules."""
        alerts: list[Alert] = []

        anomaly = self.anomaly_detector.add_metric(metric)
        if anomaly:
            alert = await self._create_anomaly_alert(metric, anomaly)
            if alert:
                alerts.append(alert)

        for rule in self.rules.values():
            if not rule.enabled:
                continue
            if self._matches_rule(metric, rule):
                alert = await self._evaluate_rule(metric, rule)
                if alert:
                    alerts.append(alert)

        return alerts

    def _matches_rule(self, metric: Metric, rule: AlertRule) -> bool:
        """Check if metric matches rule expression."""
        return metric.name in rule.expression

    async def _evaluate_rule(self, metric: Metric, rule: AlertRule) -> Optional[Alert]:
        """Evaluate a rule against a metric."""
        triggered = False

        if rule.comparison == ">":
            triggered = metric.value > rule.threshold
        elif rule.comparison == ">=":
            triggered = metric.value >= rule.threshold
        elif rule.comparison == "<":
            triggered = metric.value < rule.threshold
        elif rule.comparison == "<=":
            triggered = metric.value <= rule.threshold
        elif rule.comparison == "==":
            triggered = metric.value == rule.threshold
        elif rule.comparison == "!=":
            triggered = metric.value != rule.threshold

        if triggered:
            return await self._create_alert(metric, rule)
        return None

    async def _create_alert(self, metric: Metric, rule: AlertRule) -> Optional[Alert]:
        """Create an alert if not duplicate."""
        alert_key = f"{rule.name}:{metric.name}"

        if self._is_duplicate(alert_key):
            return None

        alert_id = hashlib.md5(
            f"{alert_key}:{time.time()}".encode()
        ).hexdigest()[:12]

        alert = Alert(
            id=alert_id,
            name=rule.name,
            severity=rule.severity,
            status=AlertStatus.FIRING,
            message=self._format_message(rule, metric),
            source=metric.labels.get("service", "unknown"),
            labels={**rule.labels, **metric.labels},
            annotations=rule.annotations,
            value=metric.value,
            threshold=rule.threshold,
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.last_alert_time[alert_key] = time.time()
        self.alert_counts[alert_key] += 1

        await self._route_alert(alert)
        return alert

    async def _create_anomaly_alert(
        self, metric: Metric, anomaly: dict
    ) -> Optional[Alert]:
        """Create an alert for detected anomaly."""
        alert_key = f"anomaly:{metric.name}"

        if self._is_duplicate(alert_key):
            return None

        alert_id = hashlib.md5(
            f"{alert_key}:{time.time()}".encode()
        ).hexdigest()[:12]

        alert = Alert(
            id=alert_id,
            name=f"Anomaly: {metric.name}",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.FIRING,
            message=(
                f"Anomaly detected in {metric.name}: "
                f"value={anomaly['value']}, "
                f"expected={anomaly['expected_range']}, "
                f"zscore={anomaly['zscore']}"
            ),
            source=metric.labels.get("service", "unknown"),
            labels=metric.labels,
            annotations={"type": "anomaly", "zscore": str(anomaly["zscore"])},
            value=anomaly["value"],
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.last_alert_time[alert_key] = time.time()

        await self._route_alert(alert)
        return alert

    def _is_duplicate(self, alert_key: str) -> bool:
        """Check if alert is duplicate within dedup window."""
        last_time = self.last_alert_time.get(alert_key, 0)
        return (time.time() - last_time) < settings.ALERT_DEDUP_WINDOW_SECONDS

    def _format_message(self, rule: AlertRule, metric: Metric) -> str:
        """Format alert message."""
        return (
            f"{rule.name}: {metric.name} is {metric.value} "
            f"(threshold: {rule.comparison} {rule.threshold})"
        )

    async def _route_alert(self, alert: Alert):
        """Route alert to appropriate channels based on severity."""
        logger.info(f"Alert fired: [{alert.severity.value}] {alert.name}: {alert.message}")

        if alert.severity in (AlertSeverity.CRITICAL, AlertSeverity.ERROR):
            await self._send_to_slack(alert)
            if alert.severity == AlertSeverity.CRITICAL:
                await self._send_to_pagerduty(alert)

    async def _send_to_slack(self, alert: Alert):
        """Send alert to Slack."""
        if not settings.SLACK_WEBHOOK_URL:
            return

        color_map = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffc107",
            AlertSeverity.ERROR: "#ff5722",
            AlertSeverity.CRITICAL: "#dc3545",
        }

        payload = {
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "#808080"),
                    "title": f"[{alert.severity.value.upper()}] {alert.name}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Source", "value": alert.source, "short": True},
                        {"title": "Status", "value": alert.status.value, "short": True},
                    ],
                    "footer": "OpsCraft Monitoring",
                    "ts": int(alert.fired_at),
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                await client.post(settings.SLACK_WEBHOOK_URL, json=payload, timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    async def _send_to_pagerduty(self, alert: Alert):
        """Send alert to PagerDuty."""
        if not settings.PAGERDUTY_API_KEY:
            return

        payload = {
            "routing_key": settings.PAGERDUTY_API_KEY,
            "event_action": "trigger",
            "dedup_key": alert.id,
            "payload": {
                "summary": f"{alert.name}: {alert.message}",
                "severity": alert.severity.value,
                "source": alert.source,
                "timestamp": datetime.fromtimestamp(
                    alert.fired_at, tz=timezone.utc
                ).isoformat(),
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload,
                    timeout=5.0,
                )
        except Exception as e:
            logger.error(f"Failed to send PagerDuty alert: {e}")

    async def acknowledge_alert(self, alert_id: str, user: str) -> Optional[Alert]:
        """Acknowledge an alert."""
        alert = self.active_alerts.get(alert_id)
        if alert:
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = user
            return alert
        return None

    async def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """Resolve an alert."""
        alert = self.active_alerts.pop(alert_id, None)
        if alert:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = time.time()
            return alert
        return None

    def get_active_alerts(
        self, severity: Optional[AlertSeverity] = None
    ) -> list[Alert]:
        """Get all active alerts, optionally filtered by severity."""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda a: a.fired_at, reverse=True)

    def get_alert_stats(self) -> dict:
        """Get alerting statistics."""
        active = list(self.active_alerts.values())
        return {
            "total_active": len(active),
            "by_severity": {
                s.value: len([a for a in active if a.severity == s])
                for s in AlertSeverity
            },
            "by_status": {
                s.value: len([a for a in active if a.status == s])
                for s in AlertStatus
            },
            "total_fired_24h": sum(
                1
                for a in self.alert_history
                if a.fired_at > time.time() - 86400
            ),
        }


class MetricRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    value: float
    labels: dict[str, str] = Field(default_factory=dict)
    metric_type: str = "gauge"


class AlertRuleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    expression: str
    threshold: float
    comparison: str = Field(..., pattern="^(>|>=|<|<=|==|!=)$")
    severity: str = Field(..., pattern="^(info|warning|error|critical)$")
    for_duration: int = 0
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)


alert_manager = AlertManager()
router = APIRouter()


@router.post("/metrics")
async def ingest_metric(request: MetricRequest):
    """Ingest a metric and check for alerts."""
    metric = Metric(
        name=request.name,
        value=request.value,
        labels=request.labels,
        metric_type=MetricType(request.metric_type),
    )

    alerts = await alert_manager.process_metric(metric)
    return {
        "received": True,
        "alerts_triggered": len(alerts),
        "alert_ids": [a.id for a in alerts],
    }


@router.get("/alerts")
async def list_alerts(severity: Optional[str] = None):
    """List active alerts."""
    sev = AlertSeverity(severity) if severity else None
    alerts = alert_manager.get_active_alerts(sev)
    return {
        "alerts": [
            {
                "id": a.id,
                "name": a.name,
                "severity": a.severity.value,
                "status": a.status.value,
                "message": a.message,
                "source": a.source,
                "fired_at": datetime.fromtimestamp(a.fired_at, tz=timezone.utc).isoformat(),
            }
            for a in alerts
        ]
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, user: str = "system"):
    """Acknowledge an alert."""
    alert = await alert_manager.acknowledge_alert(alert_id, user)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"acknowledged": True, "alert_id": alert_id}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert."""
    alert = await alert_manager.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"resolved": True, "alert_id": alert_id}


@router.get("/alerts/stats")
async def get_alert_stats():
    """Get alerting statistics."""
    return alert_manager.get_alert_stats()


@router.post("/rules")
async def create_rule(request: AlertRuleRequest):
    """Create an alerting rule."""
    rule = AlertRule(
        name=request.name,
        expression=request.expression,
        threshold=request.threshold,
        comparison=request.comparison,
        severity=AlertSeverity(request.severity),
        for_duration=request.for_duration,
        labels=request.labels,
        annotations=request.annotations,
    )
    alert_manager.add_rule(rule)
    return {"created": True, "rule_name": rule.name}


@router.get("/rules")
async def list_rules():
    """List all alerting rules."""
    return {
        "rules": [
            {
                "name": r.name,
                "expression": r.expression,
                "threshold": r.threshold,
                "comparison": r.comparison,
                "severity": r.severity.value,
                "enabled": r.enabled,
            }
            for r in alert_manager.rules.values()
        ]
    }


@router.delete("/rules/{name}")
async def delete_rule(name: str):
    """Delete an alerting rule."""
    alert_manager.remove_rule(name)
    return {"deleted": True, "rule_name": name}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")

    alert_manager.add_rule(AlertRule(
        name="HighErrorRate",
        expression="error_rate",
        threshold=0.05,
        comparison=">",
        severity=AlertSeverity.ERROR,
        annotations={"description": "Error rate exceeds 5%"},
    ))
    alert_manager.add_rule(AlertRule(
        name="HighMemoryUsage",
        expression="memory_usage_percent",
        threshold=90,
        comparison=">",
        severity=AlertSeverity.WARNING,
        annotations={"description": "Memory usage exceeds 90%"},
    ))
    alert_manager.add_rule(AlertRule(
        name="ServiceDown",
        expression="service_up",
        threshold=0,
        comparison="==",
        severity=AlertSeverity.CRITICAL,
        annotations={"description": "Service is down"},
    ))

    yield
    logger.info(f"Shutting down {settings.SERVICE_NAME}")


app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1/monitoring", tags=["monitoring"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "active_alerts": len(alert_manager.active_alerts),
    }