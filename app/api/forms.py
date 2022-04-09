from app.models.models import User

from wtforms import Form, StringField, IntegerField, DateTimeField, PasswordField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError


def _DataRequired(message=u"字段不能为空"):
    return DataRequired(message=message)


def _Length(_min=-1, _max=-1, message="格式错误"):
    return Length(_min, _max, message)


class UserLoginForm(Form):
    """ 用户登录 """
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


class ExamInfoForm(Form):
    """ 创建考试 """
    subject = StringField(label="subject", validators=[_DataRequired()])
    examRoom = StringField(label="examRoom", validators=[_DataRequired()])
    beginTime = DateTimeField(label="beginTime", format="%Y-%m-%d %H:%M", validators=[_DataRequired()])
    endTime = DateTimeField(label="endTime", format="%Y-%m-%d %H:%M", validators=[_DataRequired()])
    filetype = StringField(label="filetype", validators=[_DataRequired()])


class AdminLoginForm(Form):
    """ 管理员登录 """
    account = StringField(label="账号",
                          validators=[_DataRequired(), _Length(8, 12)],
                          description='账号',
                          render_kw={
                              'class': "form-control",
                              'placeholder': "请输入账号",
                              'required': 'required',
                          })
    passwd = PasswordField(label="密码",
                           validators=[_DataRequired(), _Length(8, 16)],
                           description='密码',
                           render_kw={
                               'class': "form-control",
                               'placeholder': "请输入密码",
                               'required': 'required',
                           }
                           )

    def validate_account(self, field):
        """ 登录验证 """
        user = self.load_user()
        if user is None:
            raise ValidationError(message=u"用户不存在")
        if user.get_role_name() != "Administrator":
            raise ValidationError(message=u"权限不足")
        if not user.validate_password(self.passwd.data):
            raise ValidationError(message=u"密码错误")

    def load_user(self):
        return User.query.filter_by(userId=self.account.data).first()
