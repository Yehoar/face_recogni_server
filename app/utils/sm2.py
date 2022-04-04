"""
SM2 公私钥生成
来源博客 https://blog.csdn.net/u014651560/article/details/113744296
"""

__all__ = ["gen_key_pair", "SM2Crypto"]

from random import SystemRandom


class CurveFp:
    def __init__(self, A, B, P, N, Gx, Gy, name):
        self.A = A
        self.B = B
        self.P = P
        self.N = N
        self.Gx = Gx
        self.Gy = Gy
        self.name = name


sm2p256v1 = CurveFp(
    name="sm2p256v1",
    A=0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC,
    B=0x28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93,
    P=0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF,
    N=0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123,
    Gx=0x32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7,
    Gy=0xBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0
)


def multiply(a, n, N, A, P):
    return fromJacobian(jacobianMultiply(toJacobian(a), n, N, A, P), P)


def add(a, b, A, P):
    return fromJacobian(jacobianAdd(toJacobian(a), toJacobian(b), A, P), P)


def inv(a, n):
    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high // low
        nm, new = hm - lm * r, high - low * r
        lm, low, hm, high = nm, new, lm, low
    return lm % n


def toJacobian(Xp_Yp):
    Xp, Yp = Xp_Yp
    return (Xp, Yp, 1)


def fromJacobian(Xp_Yp_Zp, P):
    Xp, Yp, Zp = Xp_Yp_Zp
    z = inv(Zp, P)
    return ((Xp * z ** 2) % P, (Yp * z ** 3) % P)


def jacobianDouble(Xp_Yp_Zp, A, P):
    Xp, Yp, Zp = Xp_Yp_Zp
    if not Yp:
        return (0, 0, 0)
    ysq = (Yp ** 2) % P
    S = (4 * Xp * ysq) % P
    M = (3 * Xp ** 2 + A * Zp ** 4) % P
    nx = (M ** 2 - 2 * S) % P
    ny = (M * (S - nx) - 8 * ysq ** 2) % P
    nz = (2 * Yp * Zp) % P
    return (nx, ny, nz)


def jacobianAdd(Xp_Yp_Zp, Xq_Yq_Zq, A, P):
    Xp, Yp, Zp = Xp_Yp_Zp
    Xq, Yq, Zq = Xq_Yq_Zq
    if not Yp:
        return (Xq, Yq, Zq)
    if not Yq:
        return (Xp, Yp, Zp)
    U1 = (Xp * Zq ** 2) % P
    U2 = (Xq * Zp ** 2) % P
    S1 = (Yp * Zq ** 3) % P
    S2 = (Yq * Zp ** 3) % P
    if U1 == U2:
        if S1 != S2:
            return (0, 0, 1)
        return jacobianDouble((Xp, Yp, Zp), A, P)
    H = U2 - U1
    R = S2 - S1
    H2 = (H * H) % P
    H3 = (H * H2) % P
    U1H2 = (U1 * H2) % P
    nx = (R ** 2 - H3 - 2 * U1H2) % P
    ny = (R * (U1H2 - nx) - S1 * H3) % P
    nz = (H * Zp * Zq) % P
    return (nx, ny, nz)


def jacobianMultiply(Xp_Yp_Zp, n, N, A, P):
    Xp, Yp, Zp = Xp_Yp_Zp
    if Yp == 0 or n == 0:
        return (0, 0, 1)
    if n == 1:
        return (Xp, Yp, Zp)
    if n < 0 or n >= N:
        return jacobianMultiply((Xp, Yp, Zp), n % N, N, A, P)
    if (n % 2) == 0:
        return jacobianDouble(jacobianMultiply((Xp, Yp, Zp), n // 2, N, A, P), A, P)
    if (n % 2) == 1:
        return jacobianAdd(jacobianDouble(jacobianMultiply((Xp, Yp, Zp), n // 2, N, A, P), A, P), (Xp, Yp, Zp), A, P)


class PrivateKey:
    def __init__(self, curve=sm2p256v1, secret=None):
        self.curve = curve
        self.secret = secret or SystemRandom().randrange(1, curve.N)

    def publicKey(self):
        curve = self.curve
        xPublicKey, yPublicKey = multiply((curve.Gx, curve.Gy), self.secret, A=curve.A, P=curve.P, N=curve.N)
        return PublicKey(xPublicKey, yPublicKey, curve)

    def toString(self):
        return "{}".format(str(hex(self.secret))[2:].zfill(64))


class PublicKey:
    def __init__(self, x, y, curve):
        self.x = x
        self.y = y
        self.curve = curve

    def toString(self, compressed=False):
        return {
            True: str(hex(self.x))[2:],
            False: "{}{}".format(str(hex(self.x))[2:].zfill(64), str(hex(self.y))[2:].zfill(64))
        }.get(compressed)


def gen_key_pair():
    """
    生成公私钥
    :return: private_key,public_key (str,str)
    """
    private_key = PrivateKey()
    public_key = private_key.publicKey()
    return private_key.toString(), public_key.toString(compressed=False)


from gmssl import sm2


class SM2Crypto:
    """
    C1C3C2
    SM2解密，前端使用sm-crypto,跟gmssl有些不同,公私钥都使用js端生成的
    ref https://blog.csdn.net/weixin_45471729/article/details/121488452
    :return:
    """
    gen_key = gen_key_pair  # 生成密钥

    def __init__(self, private_key, public_key):
        if public_key is None:
            public_key = ""
        if private_key is None:
            private_key = ""
        if public_key == "" and private_key == "":
            raise Exception("Invalid Keys")  # 不能同时为空

        if public_key.startswith("04") and len(public_key) == 130:
            public_key = public_key[2:]
        self.public_key = public_key
        self.private_key = private_key
        self.sm2_crypt = sm2.CryptSM2(public_key=public_key,
                                      private_key=private_key)

    def decrypt(self, data):
        """
        解密
        :param data: str
        :return: str
        """
        if len(self.private_key) != 64:
            print(self.private_key)
            raise Exception("Invalid Keys")
        if isinstance(data, str):
            data = bytes.fromhex(data)
        elif not isinstance(data, bytes):
            raise Exception("Invalid DataType")
        raw = self.sm2_crypt.decrypt(data)
        return raw.decode("utf8")

    def encrypt(self, data):
        """
        加密
        :param data: str
        :return: str
        """
        if len(self.public_key) != 128:
            print(self.public_key)
            raise Exception("Invalid Keys")
        data = data.encode(encoding="utf-8")
        raw = self.sm2_crypt.encrypt(data)
        return raw.hex()

    @staticmethod
    def init_session(session, request):
        """
        向会话存入加密参数
        :param session:
        :param request:
        :return:
        """
        private_key, public_key = gen_key_pair()
        public_key = "04" + public_key  # 前端解密公钥需要130bit
        session['private_key'] = private_key
        session['public_key'] = public_key
        session["client_key"] = request.get("publicKey")
        return private_key, public_key


if __name__ == "__main__":
    import time
    import json

    form = {
        "userId": "20189990001",
        "userName": "sad0001",
        "department": "asd",
        "major": "asd",
        "clazz": "3",
        "passwd": "20180001",
        "timestamp": time.time_ns()
    }
    data = json.dumps(form, ensure_ascii=False)

    begin = time.time()
    priKey, pubKey = gen_key_pair()
    crypto = SM2Crypto(priKey, pubKey)
    enc_data = crypto.encrypt(data)
    dec_data = crypto.decrypt(enc_data)
    end = time.time()
    print(end - begin)
    print(priKey, pubKey)
    print(enc_data)
    print(dec_data)
