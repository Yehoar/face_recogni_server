from . import bp_service
from flask_cors import cross_origin
# from flask_login import login_required


@bp_service.route("/model/<name>/<file>", methods=["GET"])
@cross_origin(supports_credentials=True)
def download_model(name, file):
    return bp_service.send_static_file(f"model/{name}/{file}")


@bp_service.route("/css/<file>", methods=["GET"])
def download_css(file):
    return bp_service.send_static_file(f"css/{file}")


@bp_service.route("/js/<file>", methods=["GET"])
def download_js(file):
    return bp_service.send_static_file(f"js/{file}")
