"""
admin.py
后台管理界面
"""
from app.api.forms import AdminLoginForm

from flask import url_for, request, redirect
from flask_login import current_user, login_user, logout_user, login_required

from flask_admin import Admin, expose, AdminIndexView, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.fileadmin import FileAdmin, gettext, secure_filename
from app.utils.utils import parse_df


class BaseModelView(ModelView):
    page_size = 50

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin.index"))


# 数据库视图
class UserView(BaseModelView):
    """用户表"""
    column_list = ('uuid', 'userId', 'name', 'department', 'major', 'clazz', 'createTime', "updateTime", 'roleId')
    column_labels = dict(
        uuid=u"用户编号", userId=u"学号", name=u"姓名", department=u"学院", major=u"专业", clazz=u"班级",
        passwd=u"密码", createTime=u"注册时间", updateTime="上次修改", roleId=u"用户类型"
    )

    column_exclude_list = ('passwd',)
    # form_excluded_columns = ['passwd', ]

    column_searchable_list = ["uuid", "userId", "name", "department", "major", "clazz"]
    column_filters = ["department", "major"]
    column_editable_list = ["userId", "name", "department", "major", "clazz", "passwd"]

    def __init__(self, table, session, **kwargs):
        super(UserView, self).__init__(table, session, **kwargs)

    def on_model_change(self, form, model, is_created):
        # 创建或修改用户时，自动加密密码
        passwd = model.passwd
        if not passwd.startswith("pbkdf2:sha256:260000$"):
            model.set_password(passwd)


class EmbeddingView(BaseModelView):
    """人脸编码"""
    can_edit = False
    can_create = False

    column_list = ("uuid", "userId", "createTime", "embdBytes")
    column_labels = dict(uuid=u"特征编号", userId=u"学号", createTime=u"创建时间", embdBytes="特征值")
    column_searchable_list = ["uuid", "userId"]

    def __init__(self, table, session, **kwargs):
        super(EmbeddingView, self).__init__(table, session, **kwargs)


class ExamInfoView(BaseModelView):
    """考试信息表"""
    column_list = ('uuid', 'subject', 'examRoom', 'userId', 'beginTime', 'endTime', 'createTime', 'updateTime')
    column_labels = dict(
        uuid=u"考试编号", subject=u"考试科目", examRoom=u"考场信息", userId=u"用户编号",
        beginTime=u"起始时间", endTime=u"结束时间", createTime=u"创建时间", updateTime=u"上次修改",
    )
    column_searchable_list = ['uuid', 'subject', 'examRoom', 'userId']
    column_editable_list = ['subject', 'examRoom', 'beginTime', 'endTime']

    def __init__(self, table, session, **kwargs):
        super(ExamInfoView, self).__init__(table, session, **kwargs)


class ExamListView(BaseModelView):
    """考试名单"""
    column_list = ('uuid', 'examId', 'userId')
    column_labels = dict(uuid=u"记录编号", userId=u"考生编号", examId=u"考试编号")
    column_searchable_list = ['userId', 'examId']


class RoleView(BaseModelView):
    """角色表"""
    column_list = ('uuid', 'name', 'power', 'createTime', 'updateTime')
    column_labels = dict(uuid=u"角色编号", name=u"角色名", power=u"权限", createTime=u"创建时间", updateTime="上次修改")
    column_searchable_list = ['uuid', 'name']


# 管理界面视图
class AdminView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/admin.html',
                           form=AdminLoginForm(),
                           current_user=current_user,
                           link=url_for("admin.login"))

    @expose('/login', methods=["GET", "POST"])
    def login(self):
        form = AdminLoginForm(formdata=request.form)
        if request.method == "POST" and form.validate():
            user = form.load_user()
            login_user(user)
            return redirect(url_for("admin.index"))
        return self.render('admin/admin.html', form=form, current_user=current_user, link=url_for("admin.login"))


# 管理员退出登录
class LogoutView(BaseView):
    @expose("/")
    @login_required
    def index(self):
        logout_user()
        return redirect(url_for("admin.index"))

    def is_accessible(self):
        return current_user.is_authenticated


# 上传文件，用于批量导入
class MyFileAdmin(FileAdmin):
    allowed_extensions = ("csv", "xlsx")

    def __init__(self, *args, **kwargs):
        from app.config import BaseConfig
        basepath = BaseConfig.UPLOAD_FILES
        super().__init__(base_path=basepath, *args, **kwargs)

    def _save_form_files(self, directory, path, form):
        # 重载文件上传
        filename = self._separator.join([directory, secure_filename(form.upload.data.filename)])
        if self.storage.path_exists(filename):
            secure_name = self._separator.join([path, secure_filename(form.upload.data.filename)])
            raise Exception(gettext('File "%(name)s" already exists.', name=secure_name))
        else:
            file_data = form.upload.data.read()
            try:  # 尝试转换编码
                tmp = file_data.decode("gbk").encode("utf8")
                file_data = tmp
            except UnicodeDecodeError:
                pass
            self.process(filename, file_data)
            self.write_file(filename, file_data)

    def write_file(self, path, content):
        with open(path, 'wb') as f:
            f.write(content)

    def process(self, filename, file_data):
        df = parse_df(filename, file_data)
        need = {"学号", "姓名", "密码", "学院", "专业", "班级", "角色"}
        offer = set(df.columns.to_list())
        if len(need.intersection(offer)) != len(need):
            not_found = ",".join(need.difference(offer))
            raise Exception(gettext(f"缺失字段: {not_found}"))
        if not df["角色"].isin(("教师", "学生")).all():
            raise Exception(gettext(f"存在错误的角色(只能创建'教师'或'学生')"))
        if any(df.isnull().any()) or any(df.isna().any()):
            raise Exception(gettext("存在空字段"))

        from app.extensions import db
        from app.models.models import User, Role
        role_student = Role.query.filter_by(name="Student").first()
        role_teacher = Role.query.filter_by(name="Teacher").first()
        buffer = []
        exists = User.query.filter(User.userId.in_(df["学号"].to_list())).all()
        if len(exists) != 0:
            exists_userId = [user.userId for user in exists]
            message = ",".join(exists_userId)
            raise Exception(gettext(f"用户已存在: {message}"))

        for idx, row in df.iterrows():
            role_id = role_teacher.uuid if row["角色"] == "教师" else role_student.uuid
            user = User(
                userId=row["学号"],
                name=row["姓名"],
                department=row["学院"],
                major=row["专业"],
                clazz=row["班级"],
                roleId=role_id
            )
            user.set_password(row["密码"])
            buffer.append(user)
        db.session.add_all(buffer)
        db.session.commit()

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin.index"))


def init_admin(db):
    from app.models import models
    admin = Admin(name=u"后台管理", template_mode="bootstrap2", index_view=AdminView(name=u"首页"))

    admin.add_view(UserView(models.User, db.session, name=u"用户信息"))
    admin.add_view(EmbeddingView(models.Embedding, db.session, name=u"人脸特征"))
    admin.add_view(ExamInfoView(models.ExamInfo, db.session, name=u"考试信息"))
    admin.add_view(ExamListView(models.ExamList, db.session, name=u"考生名单"))
    admin.add_view(RoleView(models.Role, db.session, name=u"角色表"))
    admin.add_view(MyFileAdmin(name=u"导入用户"))

    admin.add_view(LogoutView(name=u"退出"))

    return admin
