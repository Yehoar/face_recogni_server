from app import create_app, init_env
from config import AppConfig

if __name__ == '__main__':
    # 启动redis-server
    # os.system("start /B redis-server")
    application = create_app()
    init_env(application)
    application.run(debug=AppConfig.DEBUG, host=AppConfig.HOST, port=AppConfig.PORT)
