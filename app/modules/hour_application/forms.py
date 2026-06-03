from flask_wtf import FlaskForm
from wtforms import DecimalField, HiddenField, IntegerField, SelectField, SubmitField, TextAreaField, StringField
from wtforms.validators import DataRequired, Length, NumberRange

from app.services.form_option_service import get_test_course_map, get_test_major_options


class HourApplicationForm(FlaskForm):
    task_type_code = StringField("任务类别", validators=[DataRequired(), Length(max=64)])
    title = TextAreaField("任务详情描述", validators=[DataRequired(), Length(max=200)])
    participant_count = IntegerField("参与人数", validators=[DataRequired(), NumberRange(min=1, max=50)], default=1)
    participant_members = HiddenField("参与人员", validators=[DataRequired(), Length(max=2000)])
    major_name = StringField("专业", validators=[DataRequired(), Length(max=128)])
    course_name = StringField("课程", validators=[DataRequired(), Length(max=128)])
    instructor_name = StringField("课任/指导老师", validators=[DataRequired(), Length(max=128)])
    requested_hours = DecimalField(
        "兑换课程课时",
        validators=[DataRequired(), NumberRange(min=0.01, max=9999)],
        places=2,
    )
    submit = SubmitField("提交申请")

    def validate(self, extra_validators=None):
        valid = super().validate(extra_validators=extra_validators)

        valid_majors = set(get_test_major_options())
        course_map = get_test_course_map()
        selected_major = (self.major_name.data or "").strip()
        selected_course = (self.course_name.data or "").strip()

        if selected_major not in valid_majors:
            self.major_name.errors.append("请选择有效的专业。")
            valid = False

        allowed_courses = set(course_map.get(selected_major, []))
        if selected_course not in allowed_courses:
            self.course_name.errors.append("请选择有效的课程。")
            valid = False

        raw_members = self.participant_members.data or ""
        members = [item.strip() for item in raw_members.split("||")]
        expected_count = self.participant_count.data or 0
        if expected_count > 0:
            if len(members) != expected_count or any(not item for item in members):
                self.participant_members.errors.append("请完整填写每一位参与人员姓名。")
                valid = False

        return valid


class AssignTeacherForm(FlaskForm):
    teacher_id = StringField("分配审核教师", validators=[DataRequired()])
    submit = SubmitField("确认分配")
