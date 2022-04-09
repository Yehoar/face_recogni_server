"""
Flask 插件
"""
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_login import LoginManager
from flask_babelex import Babel

sess = Session()
db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()

from app.api.admin import init_admin

admin = init_admin(db)


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
