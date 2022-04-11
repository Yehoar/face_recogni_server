from flask import Blueprint
from app.config import BaseConfig

bp_debug = Blueprint(name="Debug",
                     import_name=__name__,
                     static_folder=BaseConfig.STATIC_FOLDER,
                     template_folder=BaseConfig.TEMPLATE_FOLDER)

from flask import request, jsonify


@bp_debug.route("/debug/show_request", methods=["GET", "POST"])
def show_request():
    print(request)
    print(request.form)
    print(request.get_json())
    print(request.get_data())
    return jsonify(status_code="success", message="ok")

