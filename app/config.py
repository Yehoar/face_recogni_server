import os
import redis
import platform

# 暂时禁用GPU
os.environ['CUDA_VISIBLE_DEVICES'] = "0"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


# 保存app中不使用的全局设置
class BaseConfig:
    DEBUG = True
    BASE_PATH = os.path.dirname(__file__)
    PLATFORM = platform.platform().lower()
    # 外部资源文件夹
    RESOURCE_FOLDER = os.path.join(BASE_PATH, os.path.pardir, "resources")
    # 人脸识别模型
    FACE_RECOGNI_MODEL_PATH = os.path.join(RESOURCE_FOLDER, "FaceRecogniModel")

    # Flask资源文件
    TEMPLATE_FOLDER = f"{BASE_PATH}/templates"
    STATIC_FOLDER = f"{BASE_PATH}/static"

    CRYPTO_TYPE = "AES"  # 加密类型

    # Redis
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PWD = "for_pwd_in_redis"

    # MySQL
    DB_DIALECT = "mysql"
    DB_DRIVER = "pymysql"
    DB_USER = "root"
    DB_PWD = "for_pwd_in_mysql"
    DB_HOST = "127.0.0.1"
    DB_PORT = "3306"
    DB_DATABASE = "face_recogni"
    DB_CHARSET = "utf8"

    # 微信前端交互
    CODE_TO_SESSION = {
        "URL": "https://api.weixin.qq.com/sns/jscode2session",
        'PARAMS': {
            "appid": "wx10fcf8a3c36da964",
            "secret": "216c7bf9c00b761e8b12bcffc2f3ad6a",
            "js_code": None,
            "grant_type": "authorization_code"
        }
    }

    # debug参数
    TMP_PATH = r"D:\MyProjects\PyCharm\face_recogni_server\app\tmp"


# 只保存flask中用到的配置
class AppConfig:
    # flask 配置
    DEBUG = BaseConfig.DEBUG
    SECRET_KEY = "for_pwd_in_Flask"
    # 解决中文乱码
    JSON_AS_ASCII = False

    # 将session保存到服务端 https://flask-session.readthedocs.io/en/latest/
    # 在Redis中保存session
    SESSION_TYPE = "redis"
    # 签名
    SESSION_USE_SIGNER = True
    # session有效期/秒
    PERMANENT_SESSION_LIFETIME = 7200  # 默认120分钟
    # Redis连接
    SESSION_REDIS = redis.Redis(host=BaseConfig.REDIS_HOST,
                                port=BaseConfig.REDIS_PORT,
                                db=BaseConfig.REDIS_DB,
                                # password=BaseConfig.REDIS_PWD
                                )

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset={}".format(
        BaseConfig.DB_DIALECT,
        BaseConfig.DB_DRIVER,
        BaseConfig.DB_USER,
        BaseConfig.DB_PWD,
        BaseConfig.DB_HOST,
        BaseConfig.DB_PORT,
        BaseConfig.DB_DATABASE,
        BaseConfig.DB_CHARSET
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭警告
    SQLALCHEMY_POOL_RECYCLE = 4 * 60 * 60  # 连接池归还时间


__all__ = ["BaseConfig", "AppConfig"]
