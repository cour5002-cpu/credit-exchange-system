from flask_wtf import FlaskForm
from wtforms import DecimalField, RadioField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional


class ReviewHourApplicationForm(FlaskForm):
    action = RadioField(
        "审核结果",
        validators=[DataRequired()],
        choices=[("approve", "通过"), ("reject", "驳回")],
    )
    approved_hours = DecimalField(
        "最终认定课时数",
        validators=[Optional(), NumberRange(min=0, max=9999)],
        places=2,
    )
    comment = TextAreaField("审核意见")
    submit = SubmitField("提交审核")
