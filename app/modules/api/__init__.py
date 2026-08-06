from app.modules.api.blueprint import api_bp

# Import route modules after the shared blueprint is created so their decorators
# register endpoints without making business modules depend on one another.
from app.modules.api import (  # noqa: F401,E402
    auth_routes,
    attachment_routes,
    import_export_routes,
    lookup_routes,
    routes,
    appeal_routes,
    credit_exchange_routes,
    hour_application_routes,
    rule_routes,
    system_routes,
    task_routes,
    task_type_routes,
)


__all__ = ["api_bp"]
