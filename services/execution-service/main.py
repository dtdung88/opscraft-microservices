from contextlib import asynccontextmanager

from app.api import routes
from shared.config.service_factory import ServiceFactory


# Custom lifespan with Celery
@asynccontextmanager
async def execution_lifespan(app):
    # Startup
    from app.workers.celery_worker import celery_app

    app.state.celery = celery_app

    yield


app = ServiceFactory.create_app(
    service_name="execution-service",
    service_version="1.0.0",
    service_port=8003,
    routers=[(routes.router, "/api/v1/executions", ["executions"])],
    lifespan_handler=execution_lifespan,
)
