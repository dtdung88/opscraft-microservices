"""Service factory for standardized service initialization"""
import logging
from contextlib import asynccontextmanager
from typing import Optional, Type

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from shared.config.base_settings import (
    DatabaseSettings,
    KafkaSettings,
    RedisSettings,
    SecuritySettings,
    ServiceSettings,
)
from shared.middleware.correlation_middleware import CorrelationMiddleware
from shared.middleware.error_handlers import register_exception_handlers
from shared.middleware.logging_middleware import LoggingMiddleware
from shared.middleware.rate_limiter import RateLimiter, RateLimitMiddleware
from shared.security.secrets import secrets_manager
from shared.utils.logger import setup_logger

logger = logging.getLogger(__name__)


class ServiceFactory:
    """Factory for creating standardized FastAPI services"""

    @staticmethod
    def create_app(
        service_name: str,
        service_version: str,
        service_port: int,
        routers: list = None,
        enable_rate_limiting: bool = True,
        enable_metrics: bool = True,
        lifespan_handler: Optional[callable] = None,
    ) -> FastAPI:
        """
        Create standardized FastAPI application

        Args:
            service_name: Name of the service
            service_version: Version string
            service_port: Port number
            routers: List of (router, prefix, tags) tuples
            enable_rate_limiting: Enable rate limiting middleware
            enable_metrics: Enable Prometheus metrics
            lifespan_handler: Custom lifespan context manager

        Returns:
            Configured FastAPI application
        """
        # Load configuration
        config = ServiceFactory._load_config(
            service_name, service_version, service_port
        )

        # Setup logging
        setup_logger(service_name, config.service.LOG_LEVEL)

        # Create lifespan handler
        if lifespan_handler is None:
            lifespan_handler = ServiceFactory._default_lifespan(config)

        # Create FastAPI app
        app = FastAPI(
            title=service_name,
            version=service_version,
            lifespan=lifespan_handler,
            docs_url="/docs" if config.service.DEBUG else None,
            redoc_url="/redoc" if config.service.DEBUG else None,
        )

        # Store config in app state
        app.state.config = config

        # Register middlewares
        ServiceFactory._register_middlewares(app, config, enable_rate_limiting)

        # Register exception handlers
        register_exception_handlers(app)

        # Register routers
        if routers:
            for router_config in routers:
                if len(router_config) == 3:
                    router, prefix, tags = router_config
                    app.include_router(router, prefix=prefix, tags=tags)
                else:
                    router, prefix = router_config
                    app.include_router(router, prefix=prefix)

        # Add metrics endpoint
        if enable_metrics:
            metrics_app = make_asgi_app()
            app.mount("/metrics", metrics_app)

        # Add health endpoints
        ServiceFactory._add_health_endpoints(app, config)

        logger.info(
            f"Service initialized: {service_name} v{service_version} on port {service_port}"
        )

        return app

    @staticmethod
    def _load_config(service_name: str, service_version: str, service_port: int):
        """Load and validate configuration"""
        from shared.config.base_settings import validate_required_env_vars

        # Validate environment variables
        validate_required_env_vars()

        # Create configuration object
        class ServiceConfig:
            def __init__(self):
                self.service = ServiceSettings(
                    SERVICE_NAME=service_name,
                    SERVICE_VERSION=service_version,
                    SERVICE_PORT=service_port,
                )
                self.database = DatabaseSettings()
                self.redis = RedisSettings()
                self.kafka = KafkaSettings()
                self.security = SecuritySettings()

        return ServiceConfig()

    @staticmethod
    def _register_middlewares(app: FastAPI, config, enable_rate_limiting: bool) -> None:
        """Register all middlewares"""
        # CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.service.CORS_ORIGINS,
            allow_credentials=config.service.CORS_ALLOW_CREDENTIALS,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Rate limiting
        if enable_rate_limiting and config.security.RATE_LIMIT_ENABLED:
            app.add_middleware(
                RateLimitMiddleware,
                redis_url=config.redis.REDIS_URL,
                default_limit=config.security.RATE_LIMIT_PER_MINUTE,
                default_window=60,
            )

            # Store rate limiter in app state
            app.state.rate_limiter = RateLimiter(config.redis.REDIS_URL)

        # Correlation ID
        app.add_middleware(CorrelationMiddleware)

        # Logging
        app.add_middleware(LoggingMiddleware)

    @staticmethod
    def _default_lifespan(config):
        """Default lifespan handler"""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            logger.info(f"Starting {config.service.SERVICE_NAME}")

            # Initialize database
            from sqlalchemy import create_engine

            from shared.database.session import init_db

            engine = create_engine(
                config.database.DATABASE_URL,
                pool_size=config.database.DB_POOL_SIZE,
                max_overflow=config.database.DB_MAX_OVERFLOW,
                pool_pre_ping=config.database.DB_POOL_PRE_PING,
                echo=config.database.DB_ECHO,
            )
            init_db(engine)
            app.state.db_engine = engine

            logger.info("Database initialized")

            yield

            # Shutdown
            logger.info(f"Shutting down {config.service.SERVICE_NAME}")
            if hasattr(app.state, "db_engine"):
                app.state.db_engine.dispose()

        return lifespan

    @staticmethod
    def _add_health_endpoints(app: FastAPI, config) -> None:
        """Add standard health check endpoints"""

        @app.get("/health")
        async def health():
            """Basic health check"""
            return {
                "status": "healthy",
                "service": config.service.SERVICE_NAME,
                "version": config.service.SERVICE_VERSION,
            }

        @app.get("/ready")
        async def readiness():
            """Readiness check with dependency validation"""
            checks = {"database": False, "redis": False}

            # Check database
            try:
                from sqlalchemy import text

                from shared.database.session import SessionLocal

                db = SessionLocal()
                db.execute(text("SELECT 1"))
                db.close()
                checks["database"] = True
            except Exception as e:
                logger.error(f"Database health check failed: {e}")

            # Check Redis
            try:
                import redis.asyncio as redis

                r = redis.from_url(config.redis.REDIS_URL)
                await r.ping()
                await r.close()
                checks["redis"] = True
            except Exception as e:
                logger.error(f"Redis health check failed: {e}")

            all_healthy = all(checks.values())
            status_code = 200 if all_healthy else 503

            return {"status": "ready" if all_healthy else "not ready", "checks": checks}
