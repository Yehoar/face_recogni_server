"""
数据库模型
"""
import json
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class Role(db.Model):
    """ 角色表 """
    __tablename__ = "Roles"
    uuid = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='角色编号')
    name = db.Column(db.String(255), comment='名称')
    power = db.Column(db.Integer, nullable=False, comment="权限")
    createTime = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updateTime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    user = db.relationship("User", backref="role", lazy='dynamic')

    def __repr__(self):
        return f"Role({self.name})"


class User(db.Model, UserMixin):
    """ 用户表 """
    __tablename__ = "Users"

    uuid = db.Column(db.Integer, autoincrement=True, primary_key=True, comment='用户编号')
    userId = db.Column(db.String(16), unique=True, comment="账号")
    name = db.Column(db.String(64), nullable=False, comment="姓名")
    passwd = db.Column(db.String(256), nullable=False, comment="密码")
    department = db.Column(db.String(64), nullable=False, comment="学院")
    major = db.Column(db.String(64), comment="专业")
    clazz = db.Column(db.Integer, comment="班级")
    roleId = db.Column(db.Integer, db.ForeignKey('Roles.uuid'), comment="角色编号")
    createTime = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updateTime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    embedding = db.relationship("Embedding", backref="user", lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def __repr__(self):
        return f"User(userId:{self.userId})"

    def __str__(self):
        """
        转换成前端需要的json字符串
        :return:
        """
        info = {
            "userId": self.userId,
            "name": self.name,
            "department": self.department,
            "major": self.major,
            "clazz": self.clazz,
            "userType": self.role.name
        }
        return json.dumps(info)

    def get_id(self):
        return str(self.uuid)

    def set_password(self, passwd):
        self.passwd = generate_password_hash(passwd, method="pbkdf2:sha256", salt_length=16)

    def validate_password(self, passwd):
        return check_password_hash(self.passwd, passwd)

    def get_role_name(self):
        return self.role.name

    @staticmethod
    def add(data):
        role = Role.query.filter_by(name=data["userType"]).first()
        user = User(
            userId=data["userId"],
            name=data["name"],
            department=data["department"],
            major=data["major"],
            clazz=data["clazz"],
            roleId=role.uuid
        )
        user.set_password(data["passwd"])
        db.session.add(user)
        db.session.commit()
        return user


class Embedding(db.Model):
    """ 人脸特征表 """
    __tablename__ = "Embeddings"
    uuid = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='特征编号')
    userId = db.Column(db.Integer, db.ForeignKey("Users.uuid"), nullable=False, comment='用户编号')
    createTime = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    embdBytes = db.Column(db.Text, nullable=False, comment='特征值')
    base64Img = db.Column(db.Text, nullable=False, comment='人脸图片')

    def __repr__(self):
        return f"Embedding(id:{self.uuid})"


# 中间表
class ExamList(db.Model):
    """ 考试名单表 """
    __tablename__ = "ExamList"
    uuid = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='标识')
    examId = db.Column(db.Integer, db.ForeignKey("ExamInfo.uuid"), comment='考试编号')
    userId = db.Column(db.Integer, db.ForeignKey("Users.uuid"), comment='用户编号')

    def __repr__(self):
        return f"ExamList(uuid:{self.uuid})"


class ExamInfo(db.Model):
    """ 考试信息表 """
    __tablename__ = "ExamInfo"
    uuid = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='考试编号')
    subject = db.Column(db.String(64), nullable=False, comment="考试科目")
    examRoom = db.Column(db.String(128), nullable=False, comment="考场信息")
    userId = db.Column(db.Integer, db.ForeignKey("Users.uuid"), comment='用户编号')
    beginTime = db.Column(db.DateTime, comment='开始时间')
    endTime = db.Column(db.DateTime, comment='结束时间')
    createTime = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updateTime = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def __repr__(self):
        return f"ExamInfo(id:{self.uuid})"

