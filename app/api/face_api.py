"""
facelib.py
与人脸识别相关的交互
"""
import json

from . import bp_service
from app.config import BaseConfig, AppConfig
from app.facelib.face_recogni import FaceRecogni
from app.models.models import Embedding, User
from app.utils.utils import parse_request, base64_to_image
from app.extensions import db

import os
import time
import base64
import warnings
import traceback
import numpy as np
from flask import request, jsonify, current_app, session
from flask_login import login_required, current_user

# FaceHandler = False
# if BaseConfig.USE_FACE_RECOGNI:
#     FaceHandler = FaceRecogni.get_instance()
FaceHandler = FaceRecogni.get_instance()


@bp_service.route("/anti_spoof", methods=["POST"])
@login_required
def anti_spoof():
    """
    接受前端上传的人脸图片，通过模型编码保存特征
    {
        mode: "RGB"|"RGBA"
        width: int 图片宽度
        height: int 图片高度
        encoding: str 图片编码格式 base64
        nums: int 图片数量
        im$: 图片 base64
    }
    :return:
    """
    warnings.warn("该方法产生的编码精度存在问题", DeprecationWarning)
    if BaseConfig.USE_FACE_RECOGNI:
        return jsonify(status_code="fail", message="服务器未启用功能")

    logger = current_app.logger
    # 参数检查
    if request.json is None:
        return jsonify(status_code="fail", message="请求错误")
    data = request.json
    mode = data.get("mode", None)
    im_w = data.get("width", None)
    im_h = data.get("height", None)
    encoding = data.get("encoding", None)
    nums = data.get("nums", None)
    if None in (mode, im_w, im_h, encoding, nums):
        return jsonify(status_code="fail", message="缺少参数")
    if nums <= 1 or nums >= 10:
        return jsonify(status_code="fail", message="图片数量错误")
    mode = mode.upper()

    # noinspection PyBroadException
    try:
        images = []
        for i in range(nums):
            im_raw = data.get(f"im{i}", None)  # base64 编码的图片
            ret = base64_to_image(im_raw, size=(im_w, im_h), mode=mode)
            if not ret[0]:
                return jsonify(status_code="fail", message=ret[1])
            im_rgb = ret[1]
            if AppConfig.DEBUG:  # 测试条件下保存图片
                im_rgb.save(os.path.join(BaseConfig.TMP_PATH, f"{time.time_ns()}.png"))
            images.append(np.array(im_rgb))

        # 比对距离
        embeddings = FaceHandler.predict(images)
        dist = FaceHandler.calculate_distance(embeddings)
        issame = np.all(dist < FaceHandler.threshold)
        logger.debug(dist)

        if not issame:
            return jsonify(status_code="fail", message="识别失败", socre=f"{np.mean(dist):2.4f}")

        for embedding in embeddings:
            embedding = base64.b64encode(embedding.tobytes()).decode("utf-8")
            embedding = Embedding(embdBytes=embedding, userId=current_user.get_id())
            db.session.add(embedding)
        db.session.commit()
        return jsonify(status_code="success", message="ok", socre=f"{np.mean(dist):2.4f}")

    except Exception:
        traceback.print_exc()
        return jsonify(status_code="fail", message="服务器内部出错")


@bp_service.route("/collect", methods=["POST"])
@login_required
def face_collect():
    """
    接受前端上传的人脸特征编码
    {
        encrypt: bool 必须为True
        json:{
            nums: int 数量
            embedding$: 特征向量 base64
            timestamp: 时间戳
        }
    }
    }
    :return:
    """
    try:
        logger = current_app.logger
        data = request.get_json()
        ret, data = parse_request(data, session)
        if not ret:
            return jsonify(status_code="fail", message=data)
        if not data.get("encrypt", False):
            return jsonify(status_code="fail", message="识别失败")

        nums = data.get("nums", 0)
        if nums <= 1 or nums >= 5:
            return jsonify(status_code="fail", message="参数错误")
        embeddings = []
        embdBytes = []
        for idx in range(nums):
            embd = data.get(f"embedding{idx}", None)
            if embd is None or embd == "":
                return jsonify(status_code="fail", message="参数错误")
            embdBytes.append(embd)
            embd = base64.b64decode(embd)
            embd = np.frombuffer(embd, dtype=np.float32)
            embeddings.append(embd)
        embeddings = np.vstack(embeddings)
        dist = FaceHandler.calculate_distance(embeddings)
        issame = np.all(dist < FaceHandler.threshold)
        logger.debug(dist)

        if not issame:
            return jsonify(status_code="fail", message="识别失败", socre=f"{np.mean(dist):2.4f}")
        for embedding in embdBytes:
            embedding = Embedding(embdBytes=embedding, userId=current_user.get_id())
            db.session.add(embedding)
        db.session.commit()
        return jsonify(status_code="success", message="ok", socre=f"{np.mean(dist):2.4f}")
    except Exception:
        traceback.print_exc()
        return jsonify(status_code="fail", message="服务器内部错误")


@bp_service.route("/recogni", methods=["POST"])
@login_required
def face_recogni():
    """
    前端上传Embedding，进行人脸检索
    {
        encrypt: bool 是否加密
        embedding: 人脸编码 base64
    }
    :return:
    """
    # noinspection PyBroadException
    try:
        data = request.get_json()
        ret, data = parse_request(data, session)
        if not ret:
            return jsonify(status_code="fail", message=data)
        if not data.get("encrypt", False):
            return jsonify(status_code="fail", message="识别失败")
        embedding = data.get("embedding", None)
        if embedding is None:
            return jsonify(status_code="fail", message="参数错误")
        # base64 To Embedding
        embedding = base64.b64decode(embedding)
        query = np.frombuffer(embedding, dtype=np.float32)
        query = np.expand_dims(query, axis=0)

        # 分页查询
        offset = 0
        page_size = 200
        while True:
            embeddings = Embedding.query.offset(offset).limit(page_size).all()
            if embeddings is None or len(embeddings) <= 0:
                db.session.remove()
                return jsonify(status_code="fail", message="not found")
            gallery = []
            for embedding in embeddings:
                embedding = base64.b64decode(embedding.embdBytes.encode("utf-8"))
                embedding = np.frombuffer(embedding, dtype=np.float32)
                gallery.append(embedding)
            gallery = np.vstack(gallery)
            dist = np.linalg.norm(np.subtract(query, gallery), axis=1)
            dist_argmin = np.argmin(dist)
            dist_min = dist[dist_argmin]
            if dist_min <= FaceHandler.threshold:
                user = embeddings[dist_argmin].user
                user = User.query.filter_by(uuid=user.uuid).first()
                resp = dict(
                    status_code="success",
                    message="ok",
                    info=str(user),
                    score=str(dist_min)
                )
                db.session.remove()  # 防止连接池耗尽
                return jsonify(resp)
            offset += page_size

    except Exception:
        traceback.print_exc()
    return jsonify(status_code="fail", message="服务器内部出错")
