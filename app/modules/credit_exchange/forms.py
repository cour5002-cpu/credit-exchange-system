from flask_wtf import FlaskForm
from wtforms import DecimalField, RadioField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional


class CreditExchangeApplicationForm(FlaskForm):
    requested_hours = DecimalField(
        "本次申请兑换课时数",
        validators=[DataRequired(), NumberRange(min=0.01, max=9999)],
        places=2,
    )
    description = TextAreaField("兑换说明", validators=[Optional()])
    submit = SubmitField("提交兑换申请")


class CreditExchangeReviewForm(FlaskForm):
    action = RadioField(
        "审核结果",
        validators=[DataRequired()],
        choices=[("approve", "通过"), ("reject", "驳回")],
    )
    review_comment = TextAreaField("审核意见", validators=[Optional()])
    submit = SubmitField("提交审核")
