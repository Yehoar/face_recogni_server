__all__ = ["random_str", "parse_request", "base64_to_image"]

import json
import base64
import traceback
from PIL import Image
from random import sample
from app.config import BaseConfig


def random_str(size=32):
    base = "qwertyuiopasdfghjklzxcvbnm" \
           "QWERTYUIOPASDFGHJKLZXCVBNM" \
           "1234567890+-*/@!&^%$#~{}[](),.?:;<>"
    return "".join(sample(base, size))


def get_crypto(session):
    if BaseConfig.CRYPTO_TYPE.startswith("AES"):
        from app.utils.aes import AESCrypto
        key = session.get("aes_key", None)
        iv = session.get("aes_iv", None)
        if None in (key, iv):
            return None
        crypto = AESCrypto(key, iv)
        return crypto
    elif BaseConfig.CRYPTO_TYPE == "SM2":
        # from app.utils.sm2 import SM2Crypto
        # private_key = session.get("private_key", None)
        # public_key = session.get("public_key", None)
        # if private_key is None:
        #     return None
        # crypto = SM2Crypto(private_key, public_key)
        # return crypto
        raise Exception("弃用的加密算法")
    else:
        raise NotImplemented("不支持的加密算法")


def parse_request(data, session):
    """
    解析加密的request
    :param data: request.json
    :param session:
    :return:
    """
    if data is None:
        return False, "参数错误"
    try:
        if data.get("encrypt", False):  # 如果有加密，解析加密内容
            enc_data = data.get("json", None)
            if enc_data is None:
                return False, "参数错误"
            crypto = get_crypto(session)
            if crypto is None:
                return False, "错误的会话"
            data = crypto.decrypt(enc_data)  # 解密得到明文字符串
            data = json.loads(data)  # 解析为json
            data["encrypt"] = True
        else:
            data["encrypt"] = False
        return True, data
    except (UnicodeDecodeError, TypeError):
        return False, "解密失败"
    except Exception:
        traceback.print_exc()
    return False, "服务器内部错误"


def base64_to_image(b64_str, size, mode="RGBA"):
    """
    从base64获取PIL.Image对象
    :param b64_str:
    :param size:
    :param mode:
    :return:
    """
    accept_type = ("RGBA", "RGB")
    if b64_str is None or b64_str == "":
        return False, "图片为空"
    if mode is None or mode == "" or mode not in accept_type:
        return False, "错误的图片格式"
    im_raw = base64.b64decode(b64_str)
    try:
        im0 = Image.frombuffer(mode=mode, size=size, data=im_raw)
        if mode != "RGB":
            im0 = im0.convert(mode="RGB")
        return True, im0
    except ValueError:
        traceback.print_exc()
    return False, "图片转换失败"
