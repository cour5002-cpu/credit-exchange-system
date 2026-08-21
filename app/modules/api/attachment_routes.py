import os
import uuid

from flask import current_app, request, send_file
from flask_login import current_user, login_required

from app.core.responses import fail, handle_business, ok
from app.core.validation import parse_bool_query, parse_pagination_args
from app.extensions import db
from app.models.attachment import Attachment
from app.models.college_task import CollegeTask
from app.models.credit_exchange_application import CreditExchangeApplication
from app.models.hour_application import HourApplication
from app.models.operation_log import OperationLog
from app.modules.api.blueprint import api_bp
from app.schemas.base import attachment_summary, operation_record_summary
from app.services.attachment_access_service import can_access_attachment
from app.utils.pagination import paginate_query
from app.utils.permissions import role_required
from app.utils.time_utils import business_now


@api_bp.route("/attachments", methods=["POST"])
@login_required
def upload_attachment():
    file_storage = request.files.get("file")
    biz_type = (request.form.get("biz_type") or "").strip()
    if not file_storage or not file_storage.filename:
        return fail("请上传文件")
    if biz_type not in {
        "hour_application",
        "extension_request",
        "task",
        "task_result",
        "credit_exchange",
        "appeal",
        "complaint",
        "rule_file",
    }:
        return fail("附件业务类型不合法")
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt"}
    extension = os.path.splitext(file_storage.filename)[1].lower()
    if extension not in allowed_extensions:
        return fail("附件类型不支持")
    upload_root = current_app.config["UPLOAD_FOLDER"]
    attachment_dir = os.path.join(upload_root, "attachments", biz_type)
    os.makedirs(attachment_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{extension}"
    stored_path = os.path.join(attachment_dir, stored_name)
    file_storage.save(stored_path)
    relative_path = os.path.relpath(stored_path, current_app.root_path).replace("\\", "/")
    size = os.path.getsize(stored_path)
    attachment = Attachment(
        biz_type=biz_type,
        file_name=file_storage.filename,
        file_path=relative_path,
        file_size=size,
        mime_type=file_storage.mimetype,
        uploaded_by=current_user.id,
    )
    db.session.add(attachment)
    db.session.commit()
    return ok(attachment_summary(attachment))


@api_bp.route("/attachments/<int:attachment_id>", methods=["GET"])
@login_required
def get_attachment(attachment_id):
    attachment = Attachment.query.filter_by(id=attachment_id, status="active").first()
    if not attachment:
        return fail("附件不存在", code=40401, status=404)
    if not can_access_attachment(current_user, attachment):
        return fail("无权访问该附件", code=40301, status=403)
    if parse_bool_query(request.args.get("download")):
        path = os.path.join(current_app.root_path, attachment.file_path)
        return send_file(path, as_attachment=True, download_name=attachment.file_name)
    return ok(attachment_summary(attachment))


@api_bp.route("/attachments/<int:attachment_id>", methods=["DELETE"])
@login_required
def delete_attachment(attachment_id):
    attachment = db.session.get(Attachment, attachment_id)
    if not attachment or attachment.status != "active":
        return fail("附件不存在", code=40401, status=404)
    data = request.get_json(silent=True) or {}
    bound_to_draft = _attachment_bound_to_draft(attachment)
    uploader_can_delete = attachment.uploaded_by == current_user.id and (
        not attachment.owner_id or bound_to_draft
    )
    if uploader_can_delete:
        action = "delete"
        attachment.status = "deleted"
        reason = (data.get("reason") or "上传者删除未绑定或草稿附件").strip()
    elif current_user.has_role("admin"):
        reason = (data.get("reason") or "").strip()
        if not reason:
            return fail("管理员作废已提交附件时必须填写原因")
        action = "void"
        attachment.status = "voided"
    elif attachment.uploaded_by == current_user.id:
        return fail("正式提交后的附件不能由上传者删除", code=40901, status=409)
    else:
        return fail("无权作废该附件", code=40301, status=403)
    attachment.voided_by = current_user.id
    attachment.voided_at = business_now()
    attachment.void_reason = reason
    db.session.add(OperationLog(
        user_id=current_user.id,
        module="attachment",
        biz_type="attachment",
        biz_id=attachment.id,
        action=action,
        detail=reason,
    ))
    db.session.commit()
    return ok(attachment_summary(attachment))


@api_bp.route("/admin/attachments/<int:attachment_id>/operation-records", methods=["GET"])
@login_required
@role_required("admin")
def admin_attachment_operation_records(attachment_id):
    attachment = db.session.get(Attachment, attachment_id)
    if not attachment:
        return fail("附件不存在", code=40401, status=404)

    def payload():
        page, page_size = parse_pagination_args(
            request.args.get("page", 1),
            request.args.get("page_size", 20),
        )
        result = paginate_query(
            OperationLog.query.filter_by(
                biz_type="attachment",
                biz_id=attachment.id,
            ).order_by(OperationLog.id.desc()),
            page,
            page_size,
        )
        return ok({
            "attachment": attachment_summary(attachment),
            "items": [operation_record_summary(item) for item in result.items],
            "page": result.page,
            "page_size": result.page_size,
            "total": result.total,
            "pages": result.pages,
        })

    return handle_business(payload)


def _attachment_bound_to_draft(attachment):
    if not attachment.owner_id:
        return False
    if attachment.owner_type == "hour_application":
        owner = db.session.get(HourApplication, attachment.owner_id)
        return bool(owner and owner.status == "draft")
    if attachment.owner_type == "credit_exchange":
        owner = db.session.get(CreditExchangeApplication, attachment.owner_id)
        return bool(owner and owner.status == "draft")
    if attachment.owner_type == "college_task":
        owner = db.session.get(CollegeTask, attachment.owner_id)
        return bool(owner and owner.status == "draft")
    return False
