from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField("账号", validators=[DataRequired(), Length(max=64)])
    password = PasswordField("密码", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("登录")
