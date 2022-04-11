from gevent import monkey
from gevent.pywsgi import WSGIServer

monkey.patch_all()

import os
import sys


def main():
    # 切换工作目录
    workspace = os.path.dirname(os.path.abspath(__file__))
    os.chdir(workspace)
    # 将父目录加入到搜索路径
    workspace = os.path.abspath(os.path.join(workspace, ".."))
    sys.path.append(workspace)

    from app.config import AppConfig
    from app import create_app, ensure_mysql, ensure_redis, init_env

    application = create_app()
    ensure_mysql()
    ensure_redis()
    init_env(application)
    server = WSGIServer((AppConfig.HOST, AppConfig.PORT), application=application)
    server.serve_forever()


if __name__ == '__main__':
    main()
