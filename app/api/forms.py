__all__ = ["LoginForm"]

from wtforms import Form, StringField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError


def _DataRequired(message=u"字段不能为空"):
    return DataRequired(message=message)


def _Length(_min=-1, _max=-1, message="格式错误"):
    return Length(_min, _max, message)


class LoginForm(Form):
    """ 登录 """
    userId = StringField(label="userId", validators=[_DataRequired(), _Length(8, 12)])
    passwd = StringField(label="passwd", validators=[_DataRequired(), _Length(8, 16)])


class RegisterForm(Form):
    """ 注册 """
    userId = StringField(label="userId", validators=[_DataRequired(), _Length(8, 12)])
    passwd = StringField(label="passwd", validators=[_DataRequired(), _Length(8, 16)])
    name = StringField(label="userId", validators=[_DataRequired(), _Length(2, 32)])
    department = StringField(label="department", validators=[_DataRequired(), _Length(2, 32)])
    major = StringField(label="major", validators=[_DataRequired(), _Length(2, 32)])
    clazz = IntegerField(label="clazz", validators=[_DataRequired(), NumberRange(1, 999, "不允许的班级号")])


