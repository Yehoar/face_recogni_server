from flask import Blueprint
from app.config import BaseConfig

bp_debug = Blueprint(name="Debug",
                     import_name=__name__,
                     static_folder=BaseConfig.STATIC_FOLDER,
                     template_folder=BaseConfig.TEMPLATE_FOLDER)

import os
import base64
import numpy as np
from PIL import Image
from flask import request, jsonify


@bp_debug.route("/debug/show_request", methods=["GET", "POST"])
def show_request():
    data = request.get_json()
    img_raw = data.get("img", None)
    img_raw = base64.b64decode(img_raw)
    im_rgb = Image.frombuffer(mode="RGB", size=(112, 112), data=img_raw)
    im_rgb.save(os.path.join(BaseConfig.TMP_PATH, f"recogni.png"))
    return jsonify(status_code="success", message="ok")

