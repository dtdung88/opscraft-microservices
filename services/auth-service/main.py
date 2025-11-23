from app.api import routes
from shared.config.service_factory import ServiceFactory

app = ServiceFactory.create_app(
    service_name="auth-service",
    service_version="1.0.0",
    service_port=8001,
    routers=[(routes.router, "/api/v1/auth", ["auth"])],
)
