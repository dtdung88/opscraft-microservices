from prometheus_client import Counter, Histogram, Gauge

# Metrics
scripts_total = Counter(
    'script_scripts_total',
    'Total number of scripts',
    ['script_type', 'status']
)

script_operations = Counter(
    'script_operations_total',
    'Total script operations',
    ['operation', 'status']
)

request_duration = Histogram(
    'script_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

active_scripts = Gauge(
    'script_active_scripts',
    'Number of active scripts'
)

def init_metrics():
    """Initialize metrics"""
    pass