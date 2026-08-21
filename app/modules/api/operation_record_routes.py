from flask import request
from flask_login import current_user, login_required

from app.core.responses import fail, handle_business as _handle_business, ok
from app.models.operation_log import OperationLog
from app.modules.api.blueprint import api_bp
from app.schemas.base import operation_record_summary as _operation_record_summary
from app.modules.api.route_helpers import (
    paged_response as _paged_response,
    paginate_operation_records as _paginate_operation_records,
)
from app.schemas.operation_record import operation_target_summary as _operation_target_summary
from app.utils.permissions import role_required


@api_bp.route("/operation-records", methods=["GET"])
@login_required
@role_required("advisor", "reviewer", "admin")
def operation_records():
    role_scope = (request.args.get("role_scope") or "").strip()
    if role_scope not in {"advisor", "reviewer", "admin"} or not current_user.has_role(role_scope):
        return fail("role_scope 与当前用户角色不匹配", code=40301, status=403)
    query = OperationLog.query.filter_by(user_id=current_user.id)
    biz_type = (request.args.get("biz_type") or "").strip()
    if biz_type:
        query = query.filter_by(biz_type=biz_type)
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: _paginate_operation_records(query.order_by(OperationLog.id.desc()), page, page_size),
        _operation_record_summary,
    ))


@api_bp.route("/operation-records/<int:record_id>", methods=["GET"])
@login_required
@role_required("advisor", "reviewer", "admin")
def operation_record_detail(record_id):
    record = OperationLog.query.filter_by(id=record_id, user_id=current_user.id).first()
    if not record:
        return fail("处理记录不存在或无权查看", code=40401, status=404)
    return ok({"record": _operation_record_summary(record), "target": _operation_target_summary(record)})
