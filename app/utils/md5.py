from hashlib import md5


def md5_with_salt(data, salt):
    m = md5()
    if isinstance(data, str):
        data = data.encode(encoding="utf8")
    if isinstance(salt, str):
        salt = salt.encode(encoding="utf8")
    m.update(data)
    if len(salt) > 0:
        m.update(salt)
    return m.hexdigest()
