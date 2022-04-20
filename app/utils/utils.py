__all__ = ["random_str", "parse_request", "encrypt_response", "base64_to_image", "parse_df"]

from app.config import BaseConfig

import json
import base64
import traceback
from PIL import Image
from random import sample

import io
import pandas as pd


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
        return False, "缺少参数"
    # noinspection PyBroadException
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


def encrypt_response(resp, session):
    """
    加密响应内容
    :param resp:
    :param session:
    :return:
    """
    try:
        crypto = get_crypto(session)
        if not isinstance(resp, str):
            resp = json.dumps(resp, ensure_ascii=False)
        enc_data = crypto.encrypt(resp)
        resp = {"encrypt": True, "json": enc_data}
        return True, resp
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


def parse_df(filename: str, file_data: bytes, try_convert=False) -> pd.DataFrame:
    """
    从字节流中将csv/xlsx解析成pandas.DataFrame
    :param filename: str
    :param file_data: utf-8 bytes
    :param try_convert: 尝试编码转换
    :return: pd.DataFrame
    """
    df = None

    if try_convert:  # 尝试转换编码
        try:
            tmp = file_data.decode("gbk").encode("utf8")
            file_data = tmp
        except UnicodeDecodeError:
            pass

    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_data))
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(file_data), sheet_name=0)

    return df
