__all__ = ["AESCrypto"]

import base64
from typing import Tuple
from Crypto.Cipher import AES
from app.utils.utils import random_str
from app.config import BaseConfig

# 初始化AES参数
_SIZE = 128 // 8
_MODE = AES.MODE_CBC
_crypto_type = BaseConfig.CRYPTO_TYPE.upper()
if _crypto_type.startswith("AES"):
    _, _SIZE, _MODE = _crypto_type.split("-")
    _SIZE = int(_SIZE) // 8
    _MODE = AES.__dict__.get(f"MODE_{_MODE}", AES.MODE_CBC)


class AESCrypto:
    def __init__(self, key, iv):
        """
        参考：https://zhuanlan.zhihu.com/p/184968023
        :param key: 长度为16的字符串
        :param iv: 长度为16的字符串
        """
        if not isinstance(key, str) or len(key) != _SIZE:
            raise ValueError("Invalid Key")
        if not isinstance(iv, str) or len(iv) != _SIZE:
            raise ValueError("Invalid iv")
        self.key = key.encode("utf-8")
        self.iv = iv.encode("utf-8")

    @staticmethod
    def pkcs7padding(text):
        """
        使用PKCS7填充字节
        :param text bytes
        """
        string_length = len(text)
        bytes_length = len(text.encode('utf-8'))
        padding_size = string_length if (bytes_length == string_length) else bytes_length
        padding = 16 - padding_size % 16
        padding_text = text + chr(padding) * padding
        return padding_text

    @staticmethod
    def pkcs7strip(text: bytes) -> bytes:
        """
        移除PKCS7填充字节
        :param text bytes
        :return bytes
        """
        if isinstance(text, str):
            text = text.encode("utf-8")
        padding_length = -1 * text[-1]
        body = text[:padding_length]
        padding = text[padding_length:]
        if len(set(padding)) != 1:
            raise Exception("错误的填充字节")
        return body

    @staticmethod
    def gen_key(size: int = 128) -> Tuple[str, str]:
        """
        生成 size bit 密钥
        :param size: int
        :return: key,iv
        """
        char_nums = size // 8
        key = random_str(char_nums)
        iv = random_str(char_nums)
        return key, iv

    def encrypt(self, data: str) -> str:
        """
        加密
        :param data: 明文字符串
        :return: base64 字符串
        """
        crypto = AES.new(self.key, _MODE, self.iv)
        padding_data = self.pkcs7padding(data)
        enc_data = crypto.encrypt(padding_data.encode("utf-8"))
        enc_data = base64.b64encode(enc_data).decode("utf-8")
        return enc_data

    def decrypt(self, data: str) -> str:
        """
        解密
        :param data: 密文字符串 base64编码
        :return: 明文字符串
        """
        crypto = AES.new(self.key, _MODE, self.iv)
        content = base64.b64decode(data)
        dec_data = crypto.decrypt(content)
        dec_data = self.pkcs7strip(dec_data)
        return dec_data.decode("utf-8")


if __name__ == '__main__':
    key, iv = AESCrypto.gen_key()
    print(key)
    print(iv)
    a = AESCrypto(key=key, iv=iv)
    e = a.encrypt('0123456789abcdef')
    d = a.decrypt(e)
    print("加密:", e)
    print("解密:", d)
    print(len(d.encode("utf-8")))
