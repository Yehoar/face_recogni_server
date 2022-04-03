from app import create_app

if __name__ == '__main__':
    # 启动redis-server
    # os.system("start /B redis-server")
    application = create_app()
    application.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
