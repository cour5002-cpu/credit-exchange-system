from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_FLOOR, ROUND_HALF_UP

from sqlalchemy import and_, or_

from app.extensions import db
from app.models.application_advisor import ApplicationAdvisor
from app.models.attachment import Attachment
from app.models.credit_conversion_rule import CreditConversionRule
from app.models.credit_exchange_allocation import CreditExchangeAllocation
from app.models.credit_exchange_application import CreditExchangeApplication
from app.models.credit_exchange_record import CreditExchangeRecord
from app.models.hour_application_member import HourApplicationMember
from app.models.hour_award_record import HourAwardRecord
from app.models.operation_log import OperationLog
from app.models.rule_file import RuleFile
from app.models.student_credit_record import StudentCreditRecord
from app.services.week3_hour_application_service import BusinessError, current_student, current_teacher
from app.utils.number_generator import generate_application_no
from app.utils.pagination import finish_query
from app.utils.time_utils import business_now, format_api_datetime, parse_api_datetime


VALID_RULE_TYPES = {"hour_rule", "credit_rule", "other"}
VALID_RULE_USAGES = {"reference_only", "calculation_basis"}
VALID_ROUNDING_MODES = {"floor", "keep_2", "round_half_up"}


def create_rule_file(user, payload):
    title = _required_str(payload, "title")
    rule_type = _required_choice(payload.get("rule_type"), VALID_RULE_TYPES, "规则文件类型不合法")
    usage_type = _required_choice(payload.get("usage_type"), VALID_RULE_USAGES, "规则文件用途不合法")
    attachment_id = _required_int(payload, "attachment_id")
    attachment = Attachment.query.filter_by(id=attachment_id, biz_type="rule_file", status="active").first()
    if not attachment or attachment.uploaded_by != user.id:
        raise BusinessError("规则文件附件不存在或无权使用", code=40301, status=403)
    if attachment.owner_id:
        raise BusinessError("附件已绑定其他规则文件", code=40902, status=409)

    item = RuleFile(
        title=title,
        rule_type=rule_type,
        usage_type=usage_type,
        description=(payload.get("description") or "").strip() or None,
        attachment_id=attachment.id,
        version_no=(payload.get("version_no") or "").strip() or None,
        uploaded_by=user.id,
    )
    db.session.add(item)
    db.session.flush()
    attachment.owner_type = "rule_file"
    attachment.owner_id = item.id
    _add_operation(user.id, "rule_file", item.id, "create", None, item.status)
    db.session.commit()
    return item


def list_rule_files(keyword=None, rule_type=None, usage_type=None):
    query = RuleFile.query.filter_by(status="active")
    if keyword:
        query = query.filter(RuleFile.title.like(f"%{keyword}%"))
    if rule_type:
        query = query.filter_by(rule_type=rule_type)
    if usage_type:
        query = query.filter_by(usage_type=usage_type)
    return query.order_by(RuleFile.created_at.desc(), RuleFile.id.desc()).all()


def get_rule_file(rule_file_id):
    item = RuleFile.query.filter_by(id=rule_file_id, status="active").first()
    if not item:
        raise BusinessError("规则文件不存在", code=40401, status=404)
    return item


def create_conversion_rule(user, payload):
    data = _conversion_rule_payload(payload)
    rule_file = get_rule_file(data["rule_file_id"])
    if rule_file.usage_type != "calculation_basis":
        raise BusinessError("只有作为结构化兑换规则依据的规则文件才能关联兑换规则")
    _ensure_no_active_rule_overlap(data["effective_at"], data["expires_at"])
    item = CreditConversionRule(created_by=user.id, status="active", **data)
    db.session.add(item)
    db.session.flush()
    _add_operation(user.id, "credit_conversion_rule", item.id, "create", None, item.status)
    db.session.commit()
    return item


def update_conversion_rule(user, rule_id, payload):
    rule = _get_conversion_rule(rule_id)
    merged = {
        "rule_name": payload.get("rule_name", rule.rule_name),
        "hours_per_credit": payload.get("hours_per_credit", rule.hours_per_credit),
        "max_single_exchange_hours": payload.get("max_single_exchange_hours", rule.max_single_exchange_hours),
        "rounding_mode": payload.get("rounding_mode", rule.rounding_mode),
        "effective_at": payload.get("effective_at", rule.effective_at),
        "expires_at": payload.get("expires_at", rule.expires_at),
        "rule_file_id": payload.get("rule_file_id", rule.rule_file_id),
    }
    data = _conversion_rule_payload(merged)
    rule_file = get_rule_file(data["rule_file_id"])
    if rule_file.usage_type != "calculation_basis":
        raise BusinessError("只有作为结构化兑换规则依据的规则文件才能关联兑换规则")
    if rule.status == "active":
        _ensure_no_active_rule_overlap(data["effective_at"], data["expires_at"], exclude_rule_id=rule.id)
    for key, value in data.items():
        setattr(rule, key, value)
    _add_operation(user.id, "credit_conversion_rule", rule.id, "update", rule.status, rule.status)
    db.session.commit()
    return rule


def list_conversion_rules(status=None, keyword=None):
    now = business_now()
    query = CreditConversionRule.query
    if status == "expired":
        query = query.filter(CreditConversionRule.expires_at <= now)
    elif status:
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(CreditConversionRule.rule_name.like(f"%{keyword}%"))
    return query.order_by(CreditConversionRule.effective_at.desc(), CreditConversionRule.id.desc()).all()


def current_conversion_rule():
    now = business_now()
    return (
        CreditConversionRule.query.filter(
            CreditConversionRule.status == "active",
            CreditConversionRule.effective_at <= now,
            CreditConversionRule.expires_at > now,
        )
        .order_by(CreditConversionRule.effective_at.desc(), CreditConversionRule.id.desc())
        .first()
    )


def set_conversion_rule_status(user, rule_id, status):
    rule = _get_conversion_rule(rule_id)
    if status == "active":
        _ensure_no_active_rule_overlap(rule.effective_at, rule.expires_at, exclude_rule_id=rule.id)
    before = rule.status
    rule.status = status
    _add_operation(user.id, "credit_conversion_rule", rule.id, status, before, status)
    db.session.commit()
    return rule


def list_available_hour_awards(user, page=None, page_size=None):
    student = current_student(user)
    query = (
        HourAwardRecord.query.join(
            HourApplicationMember,
            HourApplicationMember.application_id == HourAwardRecord.application_id,
        )
        .filter(
            HourAwardRecord.is_exchanged.is_(False),
            HourApplicationMember.student_id == student.id,
            HourApplicationMember.can_apply_credit_exchange.is_(True),
            HourApplicationMember.status == "active",
        )
        .order_by(HourAwardRecord.awarded_at.desc(), HourAwardRecord.id.desc())
    )
    return finish_query(query, page, page_size)


def get_exchange_form_data(user, hour_award_record_id):
    award = _get_available_award_for_student(user, hour_award_record_id)
    members = _active_members_for_award(award)
    rule = current_conversion_rule()
    if not rule:
        return award, members, None, None, False
    return award, members, rule, calculate_credits(award.total_hours, rule), True


def submit_credit_exchange(user, payload, submit=True):
    student = current_student(user)
    award = _get_available_award_for_student(user, _required_int(payload, "hour_award_record_id"))
    rule = current_conversion_rule()
    if submit and not rule:
        raise BusinessError("当前没有生效结构化兑换规则，不能提交兑换申请")
    total_hours = Decimal(str(award.total_hours))
    if submit and total_hours > Decimal(str(rule.max_single_exchange_hours)):
        raise BusinessError("本次兑换课时超过当前规则允许的最大单次兑换课时")

    attachment_ids = _normalize_id_list(payload.get("attachment_ids"))
    allocations_payload = payload.get("allocations") or []
    if submit and not attachment_ids:
        raise BusinessError("兑换申请必须上传学时学分分配证明附件")
    if submit and not allocations_payload:
        raise BusinessError("正式提交兑换申请必须填写完整的成员课时分配表")
    if submit and not payload.get("confirm_calculated_credits"):
        raise BusinessError("必须确认系统计算出的成员学分分配结果")
    calculated_allocations = _calculate_allocations(award, rule, allocations_payload, require_complete=submit)
    estimated_credits = calculate_credits(total_hours, rule) if rule else None

    application = CreditExchangeApplication(
        exchange_no=generate_application_no("EX"),
        student_id=student.id,
        applicant_student_id=student.id,
        hour_application_id=award.application_id,
        hour_award_record_id=award.id,
        advisor_teacher_id=_primary_advisor_id(award.application_id),
        requested_hours=total_hours,
        total_hours=total_hours,
        estimated_credits=estimated_credits,
        estimated_total_credits=estimated_credits,
        description=(payload.get("description") or "").strip() or None,
        status="submitted" if submit else "draft",
        rule_id=rule.id if rule else None,
        rule_snapshot=conversion_rule_snapshot(rule) if rule else None,
    )
    db.session.add(application)
    db.session.flush()

    for item in calculated_allocations:
        db.session.add(
            CreditExchangeAllocation(
                exchange_application_id=application.id,
                student_id=item["student_id"],
                allocated_hours=item["allocated_hours"],
                credit_type=item["credit_type"],
                allocated_credits=item["allocated_credits"],
                remark=item.get("remark"),
            )
        )
    _bind_exchange_attachments(application.id, attachment_ids, user.id)
    _add_operation(user.id, "credit_exchange", application.id, "submit" if submit else "draft", None, application.status)
    db.session.commit()
    return application


def list_student_credit_exchanges(user, status=None, page=None, page_size=None):
    student = current_student(user)
    query = CreditExchangeApplication.query.outerjoin(
        CreditExchangeAllocation,
        CreditExchangeAllocation.exchange_application_id == CreditExchangeApplication.id,
    ).filter(
        or_(
            CreditExchangeApplication.applicant_student_id == student.id,
            CreditExchangeApplication.student_id == student.id,
            CreditExchangeAllocation.student_id == student.id,
        )
    )
    if status:
        query = query.filter(CreditExchangeApplication.status == status)
    query = query.order_by(CreditExchangeApplication.created_at.desc(), CreditExchangeApplication.id.desc()).distinct()
    return finish_query(query, page, page_size)


def get_student_credit_exchange(user, exchange_id):
    for item in list_student_credit_exchanges(user):
        if item.id == exchange_id:
            return item
    raise BusinessError("兑换申请不存在或不可见", code=40401, status=404)


def list_advisor_pending_credit_exchanges(user, page=None, page_size=None):
    teacher = current_teacher(user, "advisor")
    query = (
        CreditExchangeApplication.query.filter_by(advisor_teacher_id=teacher.id, status="submitted")
        .order_by(CreditExchangeApplication.created_at.desc(), CreditExchangeApplication.id.desc())
    )
    return finish_query(query, page, page_size)


def get_advisor_credit_exchange(user, exchange_id):
    teacher = current_teacher(user, "advisor")
    item = _get_credit_exchange(exchange_id)
    if item.advisor_teacher_id != teacher.id:
        raise BusinessError("当前教师不是该兑换申请的指导老师", code=40301, status=403)
    return item


def advisor_approve_credit_exchange(user, exchange_id, comment=None):
    item = get_advisor_credit_exchange(user, exchange_id)
    _require_exchange_status(item, "submitted")
    before = item.status
    item.status = "pending_admin_final"
    item.advisor_reviewed_by = user.id
    item.advisor_review_comment = (comment or "").strip() or None
    item.advisor_reviewed_at = business_now()
    _add_operation(user.id, "credit_exchange", item.id, "advisor_approved", before, item.status)
    db.session.commit()
    return item


def advisor_reject_credit_exchange(user, exchange_id, comment):
    if not comment:
        raise BusinessError("驳回原因不能为空")
    item = get_advisor_credit_exchange(user, exchange_id)
    _require_exchange_status(item, "submitted")
    before = item.status
    item.status = "advisor_rejected"
    item.advisor_reviewed_by = user.id
    item.advisor_review_comment = comment
    item.advisor_reviewed_at = business_now()
    _add_operation(user.id, "credit_exchange", item.id, "advisor_rejected", before, item.status)
    db.session.commit()
    return item


def list_admin_pending_final_credit_exchanges(page=None, page_size=None):
    query = (
        CreditExchangeApplication.query.filter_by(status="pending_admin_final")
        .order_by(CreditExchangeApplication.created_at.desc(), CreditExchangeApplication.id.desc())
    )
    return finish_query(query, page, page_size)


def get_admin_credit_exchange(exchange_id):
    return _get_credit_exchange(exchange_id)


def admin_final_approve_credit_exchange(user, exchange_id, comment=None):
    from app.services.appeal_lifecycle import complete_appeal_for_target

    item = _get_credit_exchange(exchange_id)
    _require_exchange_status(item, "pending_admin_final")
    if CreditExchangeRecord.query.filter_by(exchange_application_id=item.id).first():
        raise BusinessError("该兑换申请已经生成学分到账记录", code=40902, status=409)
    award = db.session.get(HourAwardRecord, item.hour_award_record_id)
    if not award or award.is_exchanged:
        raise BusinessError("对应课时已兑换或不可用", code=40902, status=409)
    before = item.status
    item.status = "final_approved"
    item.admin_reviewed_by = user.id
    item.admin_review_comment = (comment or "").strip() or None
    item.admin_reviewed_at = business_now()
    item.reviewed_by_admin_id = user.id
    item.review_comment = item.admin_review_comment
    item.approved_at = item.admin_reviewed_at
    award.is_exchanged = True

    record = CreditExchangeRecord(
        exchange_application_id=item.id,
        student_id=item.applicant_student_id or item.student_id,
        used_hours=item.total_hours or item.requested_hours,
        exchanged_credits=item.estimated_total_credits or item.estimated_credits,
        total_used_hours=item.total_hours or item.requested_hours,
        total_credits=item.estimated_total_credits or item.estimated_credits,
        rule_snapshot=item.rule_snapshot,
    )
    db.session.add(record)
    db.session.flush()
    for allocation in item.allocations:
        db.session.add(
            StudentCreditRecord(
                exchange_record_id=record.id,
                exchange_application_id=item.id,
                student_id=allocation.student_id,
                credit_type=allocation.credit_type,
                credits=allocation.allocated_credits,
                source_hours=allocation.allocated_hours,
            )
        )
    _add_operation(user.id, "credit_exchange", item.id, "final_approved", before, item.status)
    complete_appeal_for_target("credit_exchange", item.id, "completed")
    db.session.commit()
    return item, record


def admin_final_reject_credit_exchange(user, exchange_id, comment):
    from app.services.appeal_lifecycle import complete_appeal_for_target

    if not comment:
        raise BusinessError("最终驳回原因不能为空")
    item = _get_credit_exchange(exchange_id)
    _require_exchange_status(item, "pending_admin_final")
    before = item.status
    item.status = "final_rejected"
    item.admin_reviewed_by = user.id
    item.admin_review_comment = comment
    item.admin_reviewed_at = business_now()
    item.reviewed_by_admin_id = user.id
    item.review_comment = comment
    _add_operation(user.id, "credit_exchange", item.id, "final_rejected", before, item.status)
    complete_appeal_for_target("credit_exchange", item.id, "completed")
    db.session.commit()
    return item


def admin_batch_final_approve_credit_exchanges(user, exchange_ids, comment=None):
    ids = _normalize_id_list(exchange_ids)
    if not ids:
        raise BusinessError("请选择要批量通过的兑换申请")
    results = []
    for exchange_id in ids:
        try:
            item, record = admin_final_approve_credit_exchange(user, exchange_id, comment)
            results.append({
                "id": item.id,
                "success": True,
                "status": item.status,
                "credit_exchange_record_id": record.id,
                "error_code": None,
                "error_message": None,
            })
        except BusinessError as exc:
            db.session.rollback()
            results.append({
                "id": exchange_id,
                "success": False,
                "status": None,
                "credit_exchange_record_id": None,
                "error_code": exc.code,
                "error_message": str(exc),
            })
    return results


def calculate_credits(hours, rule):
    value = Decimal(str(hours)) / Decimal(str(rule.hours_per_credit))
    if rule.rounding_mode == "floor":
        return value.to_integral_value(rounding=ROUND_FLOOR).quantize(Decimal("0.01"))
    if rule.rounding_mode == "round_half_up":
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return value.quantize(Decimal("0.01"))


def conversion_rule_snapshot(rule):
    return {
        "rule_id": rule.id,
        "rule_name": rule.rule_name,
        "hours_per_credit": str(rule.hours_per_credit),
        "max_single_exchange_hours": str(rule.max_single_exchange_hours),
        "rounding_mode": rule.rounding_mode,
        "effective_at": format_api_datetime(rule.effective_at),
        "expires_at": format_api_datetime(rule.expires_at),
        "rule_file_id": rule.rule_file_id,
    }


def _conversion_rule_payload(payload):
    effective_at = _parse_datetime(payload.get("effective_at"))
    expires_at = _parse_datetime(payload.get("expires_at"))
    if not effective_at or not expires_at or expires_at <= effective_at:
        raise BusinessError("兑换规则失效时间必须晚于生效时间")
    return {
        "rule_name": _required_str(payload, "rule_name"),
        "hours_per_credit": _positive_decimal(payload.get("hours_per_credit"), "每学分所需课时必须大于 0"),
        "max_single_exchange_hours": _positive_decimal(payload.get("max_single_exchange_hours"), "最大单次兑换课时必须大于 0"),
        "rounding_mode": _required_choice(payload.get("rounding_mode"), VALID_ROUNDING_MODES, "取整方式不合法"),
        "effective_at": effective_at,
        "expires_at": expires_at,
        "rule_file_id": _required_int(payload, "rule_file_id"),
    }


def _ensure_no_active_rule_overlap(effective_at, expires_at, exclude_rule_id=None):
    query = CreditConversionRule.query.filter(
        CreditConversionRule.status == "active",
        CreditConversionRule.effective_at < expires_at,
        CreditConversionRule.expires_at > effective_at,
    )
    if exclude_rule_id:
        query = query.filter(CreditConversionRule.id != exclude_rule_id)
    if query.first():
        raise BusinessError("同一时间不允许存在多条有效期重叠的 active 兑换规则", code=40902, status=409)


def _get_conversion_rule(rule_id):
    item = db.session.get(CreditConversionRule, rule_id)
    if not item:
        raise BusinessError("结构化兑换规则不存在", code=40401, status=404)
    return item


def _get_credit_exchange(exchange_id):
    item = db.session.get(CreditExchangeApplication, exchange_id)
    if not item:
        raise BusinessError("兑换申请不存在", code=40401, status=404)
    return item


def _get_available_award_for_student(user, hour_award_record_id):
    student = current_student(user)
    award = (
        HourAwardRecord.query.join(
            HourApplicationMember,
            HourApplicationMember.application_id == HourAwardRecord.application_id,
        )
        .filter(
            HourAwardRecord.id == hour_award_record_id,
            HourAwardRecord.is_exchanged.is_(False),
            HourApplicationMember.student_id == student.id,
            HourApplicationMember.can_apply_credit_exchange.is_(True),
            HourApplicationMember.status == "active",
        )
        .first()
    )
    if not award:
        raise BusinessError("可兑换课时不存在或当前学生不是队长", code=40401, status=404)
    return award


def _active_members_for_award(award):
    return (
        HourApplicationMember.query.filter_by(application_id=award.application_id, status="active")
        .order_by(HourApplicationMember.is_leader.desc(), HourApplicationMember.id.asc())
        .all()
    )


def _primary_advisor_id(application_id):
    link = ApplicationAdvisor.query.filter_by(application_id=application_id, advisor_role="primary", can_operate=True).first()
    if not link:
        raise BusinessError("原课时申请缺少主指导老师，不能发起兑换")
    return link.teacher_id


def _calculate_allocations(award, rule, allocations_payload, require_complete=False):
    members = _active_members_for_award(award)
    member_ids = {item.student_id for item in members}
    if not allocations_payload:
        return []
    if not isinstance(allocations_payload, list):
        raise BusinessError("allocations 必须是成员课时分配数组")

    seen = set()
    normalized = []
    total_hours = Decimal("0.00")
    for item in allocations_payload:
        if not isinstance(item, dict):
            raise BusinessError("allocations 中的每一项都必须是成员分配对象")
        student_id = _required_int(item, "student_id")
        if student_id not in member_ids:
            raise BusinessError("分配学生必须来自原课时申请成员")
        if student_id in seen:
            raise BusinessError("分配学生不能重复")
        seen.add(student_id)
        raw_hours = item.get("hours")
        if raw_hours in (None, ""):
            if require_complete:
                raise BusinessError("正式提交时每名成员的课时都必须填写")
            continue
        hours = _non_negative_decimal(raw_hours, "成员分配课时不能为负数")
        total_hours += hours
        normalized.append(
            {
                "student_id": student_id,
                "allocated_hours": hours,
                "credit_type": (item.get("credit_type") or "innovation_credit").strip(),
                "remark": (item.get("remark") or "").strip() or None,
            }
        )
    award_hours = Decimal(str(award.total_hours))
    if total_hours > award_hours:
        raise BusinessError("成员分配课时合计不能超过本次兑换总课时")
    allocation_is_complete = seen == member_ids and len(normalized) == len(member_ids)
    if require_complete and not allocation_is_complete:
        raise BusinessError("课时分配表必须包含原课时申请的全部有效成员")
    if (require_complete or allocation_is_complete) and total_hours != award_hours:
        raise BusinessError("成员分配课时合计必须等于本次兑换总课时")
    if require_complete and total_hours <= 0:
        raise BusinessError("至少一名成员的分配课时必须大于 0")
    if not rule:
        for item in normalized:
            item["allocated_credits"] = None
        return normalized

    total_credits = calculate_credits(total_hours, rule)
    running = Decimal("0.00")
    positive_indexes = [
        index for index, item in enumerate(normalized)
        if item["allocated_hours"] > 0
    ]
    last_positive_index = positive_indexes[-1] if positive_indexes else None
    for index, item in enumerate(normalized):
        if item["allocated_hours"] == 0:
            credits = Decimal("0.00")
        elif require_complete and index == last_positive_index:
            credits = total_credits - running
        else:
            credits = calculate_credits(item["allocated_hours"], rule)
            if require_complete:
                running += credits
        item["allocated_credits"] = credits
    return normalized


def _non_negative_decimal(value, message):
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise BusinessError("成员分配课时必须是数字")
    if parsed < 0:
        raise BusinessError(message)
    return parsed


def _bind_exchange_attachments(exchange_id, attachment_ids, user_id):
    if not attachment_ids:
        return
    attachments = Attachment.query.filter(Attachment.id.in_(attachment_ids), Attachment.status == "active").all()
    if len(attachments) != len(set(attachment_ids)):
        raise BusinessError("附件不存在或无权使用", code=40301, status=403)
    for attachment in attachments:
        if attachment.uploaded_by != user_id or attachment.biz_type != "credit_exchange":
            raise BusinessError("附件不存在或无权使用", code=40301, status=403)
        if attachment.owner_id and attachment.owner_id != exchange_id:
            raise BusinessError("附件已绑定其他业务", code=40902, status=409)
        attachment.owner_type = "credit_exchange"
        attachment.owner_id = exchange_id


def _require_exchange_status(item, expected_status):
    if item.status != expected_status:
        raise BusinessError("当前状态不允许执行该操作", code=40901, status=409)


def _add_operation(user_id, biz_type, biz_id, action, before_status, after_status):
    db.session.add(
        OperationLog(
            user_id=user_id,
            module="credit_exchange",
            biz_type=biz_type,
            biz_id=biz_id,
            action=action,
            detail=f"{before_status}->{after_status}",
        )
    )


def _required_str(payload, key):
    value = (payload.get(key) or "").strip()
    if not value:
        raise BusinessError(f"{key} 不能为空")
    return value


def _required_int(payload, key):
    value = payload.get(key)
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise BusinessError(f"{key} 必须是整数")
    if value <= 0:
        raise BusinessError(f"{key} 必须大于 0")
    return value


def _positive_decimal(value, message):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise BusinessError(message)
    if number <= 0:
        raise BusinessError(message)
    return number.quantize(Decimal("0.01"))


def _required_choice(value, choices, message):
    value = (value or "").strip()
    if value not in choices:
        raise BusinessError(message)
    return value


def _normalize_id_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        value = [item.strip() for item in value.split(",") if item.strip()]
    if not isinstance(value, (list, tuple, set)):
        raise BusinessError("ID 列表格式不正确")
    ids = []
    for item in value:
        try:
            item_id = int(item)
        except (TypeError, ValueError):
            raise BusinessError("ID 列表只能包含整数")
        if item_id <= 0:
            raise BusinessError("ID 列表只能包含正整数")
        if item_id not in ids:
            ids.append(item_id)
    return ids


def _parse_datetime(value):
    try:
        return parse_api_datetime(value)
    except (TypeError, ValueError):
        raise BusinessError("时间格式必须是 ISO 8601 字符串")
