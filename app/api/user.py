"""
user.py
与用户相关的操作
"""
from . import bp_service

import time
import base64
import traceback

from flask import request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import login_manager
from app.models.models import User
from app.api.forms import UserLoginForm, RegisterForm

from app.utils.utils import parse_request
from app.utils.aes import AESCrypto
from app.config import AppConfig

SESSION_LIFETIME = AppConfig.PERMANENT_SESSION_LIFETIME  # 会话有效期


@bp_service.route("/init", methods=['POST'])
def init_session():
    """
    创建会话
    :return: Response
    """
    try:
        # 参数检查
        key = session.get("aes_key", None)
        iv = session.get("aes_iv", None)
        lifetime = session.get("lifetime", None)
        user = ""
        if None in (key, iv, lifetime):  # 新的会话
            key, iv = AESCrypto.gen_key()
            lifetime = str(int((time.time() + SESSION_LIFETIME) * 1000))
            session["aes_key"] = key
            session["aes_iv"] = iv
            session["lifetime"] = lifetime
        elif current_user.is_active:
            crypto = AESCrypto(key, iv)
            user = crypto.encrypt(str(current_user))
        # 混淆token
        token = "|".join([lifetime, key, iv])
        token = token[0::2] + token[1::2]
        token = base64.b64encode(token.encode("utf-8")).decode("gbk")
        return jsonify(status_code="success", message="ok", token=token, user=user)
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
    return User.query.filter_by(uuid=user_id).first()


@bp_service.route("/login", methods=['POST'])
def login():
    """
    用户根据学号,密码进行登录，以绑定身份  POST 上传表单
    {
        encrypt: bool 是否加密 必须为True
        userId: str 账号
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
        form = UserLoginForm(formdata=None, data=data)
        if not form.validate():
            return jsonify(status_code="fail", message=form.errors)
        data = form.data  # dict
        user = User.query.filter_by(userId=data["userId"]).first()
        if user is None:
            return jsonify(status_code="fail", message="该账号未注册")
        if not user.validate_password(data["passwd"]):
            return jsonify(status_code="fail", message="密码错误")
        if login_user(user):  # flask-login 记录用户
            return jsonify(status_code="success", message="ok", userType=user.role.name)
    except Exception:
        traceback.print_exc()
    return jsonify(status_code="fail", message="服务器错误")


@bp_service.route("/register", methods=['POST'])
def register():
    """
    用户注册 POST 上传表单
    {
        encrypt: bool 是否加密 必须为True
        "userId", "passwd", "name", "department", "major", "clazz"
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
        form = RegisterForm(formdata=None, data=data)
        if not form.validate():
            return jsonify(status_code="fail", message=form.errors)

        data = form.data  # dict
        data["userType"] = "Student"
        user = User.query.filter_by(userId=data["userId"]).first()
        if user is not None:
            return jsonify(status_code="fail", message="用户已存在")
        # 创建用户并更新数据库
        user = User.add(data)
        if login_user(user):  # 添加用户后执行登录
            return jsonify(status_code="success", message="ok", userType=user.role.name)
    except Exception:
        traceback.print_exc()
    return jsonify(status_code="fail", message="注册失败")


@bp_service.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    """
    用户登出
    """
    logout_user()
    return jsonify(status_code="success", message="ok")


