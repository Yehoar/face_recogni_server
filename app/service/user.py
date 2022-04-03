"""
user.py
与用户相关的操作
"""
from . import bp_service

import json
import requests
import traceback
from datetime import datetime

from flask import request, session, jsonify
from flask_login import login_user, logout_user, login_required

from app.config import BaseConfig
from app.db import db
from app.db.models import User, Role
from app import login_manager

from app.utils.utils import create_salt, md5_with_salt, parse_request
from app.utils.sm2utils import gen_key_pair, SM2Crypto


@bp_service.route("/init", methods=['POST'])
def init_session():
    """
    创建会话，每次打开小程序都视为新的访问
    {
        publicKey: str 前端加密公钥 十六进制字符串数组
    }
    :return: Response
    """
    try:
        # 参数检查
        data = request.json
        if data.get("publicKey", None) is None:
            return jsonify(status_code="fail", message="参数错误")

        private_key, public_key = gen_key_pair()
        public_key = "04" + public_key  # 前端解密公钥需要130bit
        session['private_key'] = private_key
        session['public_key'] = public_key
        session["client_key"] = data.get("publicKey")
        return jsonify(status_code="success", message="ok", publicKey=public_key)
    except Exception:
        traceback.print_exc()
        return jsonify(status_code="fail", message="服务器内部错误")

    # # 获取微信openid
    # url = BaseConfig.CODE_TO_SESSION.get('URL')
    # params = BaseConfig.CODE_TO_SESSION.get('PARAMS').copy()
    # params['js_code'] = data.get('code')
    # # 向微信code2session换取id
    # resp = requests.get(url, params=params).json()

    # # 检查获取结果
    # errcode = resp.get('errcode', None)
    # if not errcode:
    #     # 为会话生成公私钥
    #     private_key, public_key = gen_key_pair()
    #     public_key = "04" + public_key  # 前端解密公钥需要130bit
    #     session['session_key'] = resp.get('session_key', None)
    #     session['openid'] = resp.get('openid', None)
    #     session['private_key'] = private_key
    #     session['public_key'] = public_key
    #     session["client_key"] = data.get("publicKey")
    #     return jsonify(status_code="success", message="ok", publicKey=public_key)
    # else:
    #     return jsonify(status_code="fail", message=errcode)


@login_manager.user_loader
def user_loader(user_id):
    """ 通过user_id从session还原用户 """
    return User.query.filter_by(user_id=user_id).first()


@bp_service.route("/login", methods=['POST'])
def login():
    """
    用户根据学号,密码进行登录，以绑定身份  POST 上传表单
    {
        encrypt: bool 是否加密 必须为True
        account: str 账号
        passwd: str 密码
    }
    :return:
    """
    # noinspection PyBroadException
    try:
        data = request.get_json()
        ret, data = parse_request(data, session)
        if not ret:
            return jsonify(status_code="fail", message=data)
        user_id = data.get("account", None)
        passwd = data.get("passwd", None)
        if user_id is None or passwd is None or len(passwd) < 8 or len(passwd) > 16:
            return jsonify(status_code="fail", message="参数错误")

        user = User.query.filter_by(user_id=user_id).first()
        if user is None:
            return jsonify(status_code="fail", message="该账号未注册")
        passwd = md5_with_salt(passwd, user.salt)
        if user.passwd != passwd:
            return jsonify(status_code="fail", message="密码错误")
        if login_user(user):  # flask-login 记录用户
            return jsonify(status_code="success", message="ok", userType=user.role_id)
    except Exception:
        traceback.print_exc()
    return jsonify(status_code="fail", message="服务器错误")


@bp_service.route("/register", methods=['POST'])
def register():
    """
    用户注册 POST 上传表单
    {
        encrypt: bool 是否加密 必须为True
        "userId", "passwd", "userName", "college", "major", "clazz"
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
            return jsonify(status_code="fail", message="注册失败")

        for attr in ("userId", "passwd", "userName", "college", "major", "clazz"):
            val = data.get(attr, None)
            if val is None or val == "":
                return jsonify(status_code="fail", message="信息不完整")

        user = User.query.get(data["userId"])
        if user is not None:
            return jsonify(status_code="fail", message="用户已存在")
        # 创建用户
        # 加盐再md5加密
        salt = create_salt(length=32)
        passwd = md5_with_salt(data["passwd"], salt)
        # 更新数据库
        role = Role.query.filter_by(role_name="Student").first()
        user = User(
            user_id=data["userId"],
            user_name=data["userName"],
            passwd=passwd,
            salt=salt,
            college=data["college"],
            major=data["major"],
            clazz=data["clazz"],
            create_time=datetime.now(),
            role_id=role.role_id
        )
        db.session.add(user)
        db.session.commit()
        if login_user(user):  # 添加用户后执行登录
            return jsonify(status_code="success", message="ok", userType=user.role_id)
    except Exception:
        traceback.print_exc()
    return jsonify(status_code="fail", message="注册失败")


@bp_service.route("/logout", methods=['POST'])
@login_required
def logout():
    """
    用户登出
    """
    logout_user()
    return jsonify(status_code="success", message="ok")
