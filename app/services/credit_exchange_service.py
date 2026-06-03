from datetime import datetime
from decimal import Decimal

from app.extensions import db
from app.models.credit_exchange_application import CreditExchangeApplication
from app.models.credit_exchange_record import CreditExchangeRecord
from app.models.student_hour_account import StudentHourAccount
from app.models.student_hour_transaction import StudentHourTransaction
from app.services.config_service import calculate_credits_from_hours, get_credit_exchange_ratio
from app.utils.number_generator import generate_application_no


def calculate_estimated_credits(requested_hours):
    if not requested_hours:
        return Decimal("0.00")
    return calculate_credits_from_hours(requested_hours)


def create_credit_exchange_application(student_id, requested_hours, description):
    account = StudentHourAccount.query.filter_by(student_id=student_id).first()
    available_hours = Decimal(str(account.available_hours if account else 0))
    requested = Decimal(str(requested_hours))
    if requested > available_hours:
        raise ValueError("可用课时不足，无法提交兑换申请。")

    application = CreditExchangeApplication(
        exchange_no=generate_application_no("EX"),
        student_id=student_id,
        requested_hours=requested,
        estimated_credits=calculate_estimated_credits(requested),
        description=description,
        status="submitted",
    )
    db.session.add(application)
    db.session.commit()
    return application


def list_credit_exchange_applications_for_student(student_id):
    return (
        CreditExchangeApplication.query.filter_by(student_id=student_id)
        .order_by(CreditExchangeApplication.created_at.desc(), CreditExchangeApplication.id.desc())
        .all()
    )


def get_credit_exchange_detail_for_student(student_id, application_id):
    return CreditExchangeApplication.query.filter_by(
        id=application_id,
        student_id=student_id,
    ).first()


def list_credit_exchange_applications_for_admin():
    return (
        CreditExchangeApplication.query.order_by(
            CreditExchangeApplication.created_at.desc(),
            CreditExchangeApplication.id.desc(),
        ).all()
    )


def get_credit_exchange_detail_for_admin(application_id):
    return CreditExchangeApplication.query.filter_by(id=application_id).first()


def submit_credit_exchange_review(application, action, review_comment, admin_user_id):
    if application.status != "submitted":
        raise ValueError("当前兑换申请已处理，不能重复审核。")

    application.reviewed_by_admin_id = admin_user_id
    application.review_comment = review_comment

    if action == "approve":
        approve_credit_exchange(application, admin_user_id)
    else:
        application.status = "rejected"

    db.session.commit()
    return application


def approve_credit_exchange(application, admin_user_id):
    account = StudentHourAccount.query.filter_by(student_id=application.student_id).first()
    if not account:
        raise ValueError("未找到学生课时账户。")

    requested_hours = Decimal(str(application.requested_hours))
    before_hours = Decimal(str(account.available_hours))
    if requested_hours > before_hours:
        raise ValueError("可用课时不足，无法通过兑换申请。")

    after_hours = before_hours - requested_hours
    estimated_credits = Decimal(str(application.estimated_credits))
    ratio_hours, ratio_credits = get_credit_exchange_ratio()

    account.total_exchanged_hours = Decimal(str(account.total_exchanged_hours)) + requested_hours
    account.available_hours = after_hours

    application.status = "approved"
    application.approved_at = datetime.now()

    db.session.add(
        StudentHourTransaction(
            student_id=application.student_id,
            biz_type="credit_exchange",
            biz_id=application.id,
            change_type="decrease",
            hours_change=requested_hours,
            before_hours=before_hours,
            after_hours=after_hours,
            remark=f"学分兑换 {application.exchange_no} 审核通过",
            created_by=admin_user_id,
        )
    )
    db.session.add(
        CreditExchangeRecord(
            exchange_application_id=application.id,
            student_id=application.student_id,
            used_hours=requested_hours,
            exchanged_credits=estimated_credits,
            rule_snapshot={
                "credit_exchange_ratio": f"{ratio_hours}:{ratio_credits}",
            },
        )
    )
