import logging
from flask import Flask
from flask_session import Session
from flask_login import LoginManager

sess = Session()
login_manager = LoginManager()


def init_logger():
    logging.basicConfig(level=logging.DEBUG)


def create_app():
    # 避免循环导入
    from app.db import db, models
    from app.config import AppConfig, BaseConfig
    from app.service import bp_service

    init_logger()  # 初始化日志
    app = Flask(
        __name__,
        template_folder=BaseConfig.TEMPLATE_FOLDER,
        static_folder=BaseConfig.STATIC_FOLDER
    )

    # 加载配置
    app.config.from_object(AppConfig)
    # 注册蓝图
    app.register_blueprint(bp_service)
    if BaseConfig.DEBUG:
        from app.service.debug import bp_debug
        app.register_blueprint(bp_debug)

    # 加载扩展
    db.init_app(app)
    sess.init_app(app)
    login_manager.init_app(app)

    # 初始化数据库
    # if AppConfig.DEBUG:
    #     with app.app_context():
    #         db.drop_all()
    #         db.create_all()
    #         models.Role.insert_roles()
    #         models.User.insert_users()
    return app
