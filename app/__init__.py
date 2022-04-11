import os
import sys
import time
import logging
import traceback

from flask import Flask

logger = logging.getLogger(__name__)


def init_logger():
    from app.config import BaseConfig
    level = logging.DEBUG if BaseConfig.DEBUG else logging.INFO
    logging.basicConfig(level=level)


def create_app():
    # 避免循环导入
    from app.config import AppConfig, BaseConfig
    from app.api import bp_service
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

    return application


def init_env(application):
    """
    首次启动时初始化环境
    :return:
    """
    from app.config import BaseConfig, Default, AppConfig
    from app.extensions import db
    from app.models.models import User, Role

    try:
        logger.info("Initializing")
        if not os.path.exists(BaseConfig.INIT_FLAG):
            with application.app_context():
                # DEBUG
                if BaseConfig.DEBUG:
                    db.drop_all()

                # 初始化数据库
                db.create_all()

                # 添加角色
                for name, power in Default.ROLES.items():
                    role = Role.query.filter_by(name=name).first()
                    if role is None:
                        role = Role(name=name, power=power)
                    db.session.add(role)

                # 创建管理员
                admin_cfg = Default.ADMIN
                role = Role.query.filter_by(name=admin_cfg["rName"]).first()
                admin = User(
                    userId=admin_cfg["userId"],
                    name=admin_cfg["name"],
                    department=admin_cfg["department"],
                    major=admin_cfg["major"],
                    clazz=admin_cfg["clazz"],
                    roleId=role.uuid
                )
                admin.set_password(admin_cfg["passwd"])
                db.session.add(admin)
                db.session.commit()

            with open(BaseConfig.INIT_FLAG, 'w') as f:
                f.write(str(time.time_ns()))
        logger.info("Initialization Complete")
    except Exception:
        traceback.print_exc()
        logger.error("Initialization Failed")
        sys.exit(-1)


def ensure_mysql():
    """
    确保mysql可用
    """

    import pymysql
    from app.config import MySQL
    try:
        mysql = pymysql.connect(host=MySQL.DB_HOST,
                                port=int(MySQL.DB_PORT),
                                user=MySQL.DB_USER,
                                passwd=MySQL.DB_PWD,
                                db=MySQL.DB_DATABASE,
                                charset=MySQL.DB_CHARSET
                                )
        cursor = mysql.cursor()
        cursor.execute("SELECT VERSION()")
        data = cursor.fetchone()
        logger.info(f"MySQL Version: {data}")
        mysql.close()
        logger.info("MySQL is Ready")
    except pymysql.err.MySQLError:
        logger.error("MySQL Test Failed")
        traceback.print_exc()
        sys.exit(-1)


def ensure_redis():
    import redis
    from app.config import Redis
    try:
        r = redis.Redis(host=Redis.REDIS_HOST,
                        port=Redis.REDIS_PORT,
                        db=Redis.REDIS_DB,
                        # password=Redis.REDIS_PWD
                        )
        redis_info = r.info()
        logger.info(f"Redis Connected Clients: {redis_info.get('connected_clients', 'FAILED')}")
        r.close()
        logger.info("Redis is Ready")
    except redis.exceptions.RedisError:
        logger.error("Redis Test Failed")
        traceback.print_exc()
        sys.exit(-1)
