import os
import redis
import platform

# 暂时禁用GPU
os.environ['CUDA_VISIBLE_DEVICES'] = "0"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


class MySQL:
    """
    MySQL参数
    """
    DB_DIALECT = "mysql"
    DB_DRIVER = "pymysql"
    DB_USER = "root"
    DB_PWD = "for_pwd_in_mysql"
    DB_HOST = "127.0.0.1"
    DB_PORT = "3306"
    DB_DATABASE = "face_recogni"
    DB_CHARSET = "utf8"

    @classmethod
    def url(cls):
        return "{}+{}://{}:{}@{}:{}/{}?charset={}".format(
            cls.DB_DIALECT, cls.DB_DRIVER, cls.DB_USER, cls.DB_PWD,
            cls.DB_HOST, cls.DB_PORT, cls.DB_DATABASE, cls.DB_CHARSET
        )


class Redis:
    """
    Redis 参数
    """
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PWD = "for_pwd_in_redis"


class Default:
    ROLES = {  # 默认角色及权限
        "Student": 0x0001,
        "Teacher": 0x0010,
        "Administrator": 0x0100,
    }
    ADMIN = {
        "userId": "admin2022",
        "name": "admin2022",
        "passwd": "admin2022",
        "department": "ADMIN",
        "major": "ADMIN",
        "clazz": 0,
        "rName": "Administrator"
    }


# 保存app中不使用的全局设置
class BaseConfig:
    DEBUG = False
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    PLATFORM = platform.platform().lower()
    # 外部资源文件夹
    RESOURCE_FOLDER = os.path.join(BASE_PATH, os.path.pardir, "resources")
    # 人脸识别模型
    FACE_RECOGNI_MODEL_PATH = os.path.join(RESOURCE_FOLDER, "FaceRecogniModel")
    # 用户上传文件
    UPLOAD_FILES = os.path.join(RESOURCE_FOLDER, "UploadFiles")
    # 初始化标志
    INIT_FLAG = os.path.join(RESOURCE_FOLDER, "flask.init")
    # 启动服务端人脸识别
    USE_FACE_RECOGNI = False

    # Flask资源文件
    TEMPLATE_FOLDER = f"{BASE_PATH}/templates"
    STATIC_FOLDER = f"{BASE_PATH}/static"

    # 是否加密传输
    CRYPTO_TYPE = "AES-128-CBC"

    # 临时文件存放
    TMP_PATH = os.path.join(BASE_PATH, "tmp")

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


# 只保存flask中用到的配置
class AppConfig:
    # flask 配置
    DEBUG = BaseConfig.DEBUG
    HOST = "0.0.0.0"
    PORT = 5000
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
    SESSION_REDIS = redis.Redis(host=Redis.REDIS_HOST,
                                port=Redis.REDIS_PORT,
                                db=Redis.REDIS_DB,
                                # password=Redis.REDIS_PWD
                                )

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = MySQL.url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 4 * 60 * 60  # 连接池归还时间

    # 语言
    BABEL_DEFAULT_TIMEZONE = "UTC"
    BABEL_DEFAULT_LOCALE = "zh_CN"

    # 关闭WTF的CSRF
    WTF_CSRF_CHECK_DEFAULT = False
