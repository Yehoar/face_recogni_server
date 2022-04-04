from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView


class UserView(ModelView):
    # column_list = ('uuid', 'userId', 'name', 'department', 'major', 'clazz', 'createTime', 'Role')
    # column_labels = dict(
    #     user_id=u"学号", user_name=u"姓名", college=u"学院", major=u"专业", clazz=u"班级",
    #     passwd=u"密码", salt=u"随机盐", create_time=u"注册时间", Role=u"用户类型"
    # )
    # column_exclude_list = ('passwd', 'salt')
    # form_excluded_columns = ['passwd', 'salt']
    #
    # column_searchable_list = ["user_id", "user_name", "department", "major", "clazz"]
    # column_filters = ["department", "major"]
    # column_editable_list = ["user_id", "user_name", "department", "major", "clazz", "Role"]
    page_size = 50

    def __init__(self, table, session, **kwargs):
        super(UserView, self).__init__(table, session, **kwargs)


class EmbeddingView(ModelView):

    def __init__(self, table, session, **kwargs):
        super(EmbeddingView, self).__init__(table, session, **kwargs)


def init_admin(admin, db):
    from app.models import models

    admin.add_view(UserView(models.User, db.session, name=u"用户信息"))
    admin.add_view(EmbeddingView(models.Embedding, db.session, name=u"人脸特征"))
