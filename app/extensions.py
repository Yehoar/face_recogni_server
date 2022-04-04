"""
Flask 插件
"""
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_login import LoginManager
from flask_babelex import Babel
from flask_admin import Admin

sess = Session()
db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()
admin = Admin(name=u"后台管理", template_mode="bootstrap2")


@babel.localeselector
def get_locale():
    """
    设置时区
    :return:
    """
    from flask import session
    override = 'zh_CN'
    if override:
        session['lang'] = override
    return session.get('lang', 'en')


