from app.api import routes
from app.api.templates import router as template_router
from shared.config.service_factory import ServiceFactory

app = ServiceFactory.create_app(
    service_name="script-service",
    service_version="1.0.0",
    service_port=8002,
    routers=[
        (routes.router, "/api/v1/scripts", ["scripts"]),
        (template_router, "/api/v1/templates", ["templates"]),
    ],
)
