from app.api import routes
from shared.config.service_factory import ServiceFactory

app = ServiceFactory.create_app(
    service_name="secret-service",
    service_version="1.0.0",
    service_port=8004,
    routers=[(routes.router, "/api/v1/secrets", ["secrets"])],
)
