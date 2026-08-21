from decimal import Decimal

from app.extensions import db
from app.models.credit_exchange_record import CreditExchangeRecord
from app.models.student_hour_account import StudentHourAccount
from app.models.student_hour_transaction import StudentHourTransaction


def get_or_create_account(student_id):
    account = StudentHourAccount.query.filter_by(student_id=student_id).first()
    if account:
        return account

    account = StudentHourAccount(
        student_id=student_id,
        total_earned_hours=Decimal("0.00"),
        total_exchanged_hours=Decimal("0.00"),
        available_hours=Decimal("0.00"),
    )
    db.session.add(account)
    db.session.flush()
    return account


def add_hours(student_id, hours, biz_type, biz_id, created_by, remark):
    account = get_or_create_account(student_id)
    before_hours = Decimal(str(account.available_hours))
    change_hours = Decimal(str(hours))
    after_hours = before_hours + change_hours

    account.total_earned_hours = Decimal(str(account.total_earned_hours)) + change_hours
    account.available_hours = after_hours

    transaction = StudentHourTransaction(
        student_id=student_id,
        biz_type=biz_type,
        biz_id=biz_id,
        change_type="increase",
        hours_change=change_hours,
        before_hours=before_hours,
        after_hours=after_hours,
        remark=remark,
        created_by=created_by,
    )
    db.session.add(transaction)
    return account, transaction


def get_total_exchanged_credits(student_id):
    records = CreditExchangeRecord.query.filter_by(student_id=student_id).all()
    total = Decimal("0.00")
    for record in records:
        total += Decimal(str(record.exchanged_credits))
    return total
