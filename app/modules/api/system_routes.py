from app.core.responses import ok
from app.modules.api.blueprint import api_bp
from app.utils.time_utils import system_time_payload


@api_bp.route("/system/time")
def get_system_time():
    return ok(system_time_payload())
