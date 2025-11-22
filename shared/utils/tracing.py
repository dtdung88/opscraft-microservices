"""Distributed tracing utilities using OpenTelemetry."""
import logging
import os
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)


def setup_tracing(
    service_name: str,
    jaeger_host: str = "jaeger",
    jaeger_port: int = 6831,
    enabled: bool = True,
) -> Optional[trace.Tracer]:
    """Initialize distributed tracing with OpenTelemetry and Jaeger."""
    if not enabled:
        logger.info("Tracing is disabled")
        return None

    try:
        resource = Resource.create({
            "service.name": service_name,
            "service.version": os.getenv("SERVICE_VERSION", "1.0.0"),
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })

        provider = TracerProvider(resource=resource)

        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_host,
            agent_port=jaeger_port,
        )

        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        trace.set_tracer_provider(provider)

        set_global_textmap(B3MultiFormat())

        logger.info(f"Tracing initialized for {service_name} -> {jaeger_host}:{jaeger_port}")

        return trace.get_tracer(service_name)

    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        return None


def instrument_app(app: Any, engine: Optional[Any] = None):
    """Instrument FastAPI app and common libraries."""
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation enabled")
    except Exception as e:
        logger.warning(f"FastAPI instrumentation failed: {e}")

    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumentation enabled")
    except Exception as e:
        logger.warning(f"HTTPX instrumentation failed: {e}")

    try:
        RedisInstrumentor().instrument()
        logger.info("Redis instrumentation enabled")
    except Exception as e:
        logger.warning(f"Redis instrumentation failed: {e}")

    if engine:
        try:
            SQLAlchemyInstrumentor().instrument(engine=engine)
            logger.info("SQLAlchemy instrumentation enabled")
        except Exception as e:
            logger.warning(f"SQLAlchemy instrumentation failed: {e}")


def traced(
    name: Optional[str] = None,
    attributes: Optional[dict[str, Any]] = None,
):
    """Decorator to create a span for a function."""
    def decorator(func: Callable) -> Callable:
        span_name = name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, v)
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, v)
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


@contextmanager
def trace_span(
    name: str,
    attributes: Optional[dict[str, Any]] = None,
):
    """Context manager for creating a span."""
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def add_span_attributes(attributes: dict[str, Any]):
    """Add attributes to the current span."""
    span = trace.get_current_span()
    if span:
        for k, v in attributes.items():
            span.set_attribute(k, v)


def add_span_event(name: str, attributes: Optional[dict[str, Any]] = None):
    """Add an event to the current span."""
    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})


def get_trace_id() -> Optional[str]:
    """Get the current trace ID."""
    span = trace.get_current_span()
    if span:
        ctx = span.get_span_context()
        if ctx.is_valid:
            return format(ctx.trace_id, "032x")
    return None


def get_span_id() -> Optional[str]:
    """Get the current span ID."""
    span = trace.get_current_span()
    if span:
        ctx = span.get_span_context()
        if ctx.is_valid:
            return format(ctx.span_id, "016x")
    return None