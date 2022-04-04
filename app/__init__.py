import logging
from flask import Flask


def init_logger():
    logging.basicConfig(level=logging.DEBUG)


def create_app():
    # 避免循环导入
    from app.config import AppConfig, BaseConfig
    from app.api import bp_service, init_admin
    from app.extensions import db, sess, login_manager, babel, admin
    from app.models import models

    init_logger()  # 初始化日志
    application = Flask(
        __name__,
        template_folder=BaseConfig.TEMPLATE_FOLDER,
        static_folder=BaseConfig.STATIC_FOLDER
    )

    # 加载配置
    application.config.from_object(AppConfig)
    # 注册蓝图
    application.register_blueprint(bp_service)

    if BaseConfig.DEBUG:
        from app.api.debug import bp_debug
        application.register_blueprint(bp_debug)

    # 加载扩展
    db.init_app(application)
    sess.init_app(application)
    login_manager.init_app(application)
    admin.init_app(application)
    babel.init_app(application)

    # 初始化后台
    init_admin(admin, db)

    # 初始化数据库
    if AppConfig.DEBUG:
        with application.app_context():
            db.drop_all()
            db.create_all()
            models.Role.insert_roles()
            models.User.insert_users()

    return application
