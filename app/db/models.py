from . import db

import numpy as np
from datetime import datetime
from flask_login import UserMixin


class Role(db.Model):
    """
    角色表
    """
    __tablename__ = "Roles"
    role_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_name = db.Column(db.String(32), nullable=False, unique=True)
    user = db.relationship("User", backref="Role", lazy='dynamic')

    def __repr__(self):
        return f"Role(name:{self.role_name})"

    @staticmethod
    def insert_roles():  # 创建默认角色
        roles = ["Student", "Teacher", "Administrator"]
        for r in roles:
            role = Role.query.filter_by(role_name=r).first()
            if role is None:
                role = Role(role_name=r)
            db.session.add(role)
        db.session.commit()


class User(db.Model, UserMixin):
    """
    用户表
    user_id 学号
    user_name  姓名
    passwd  密码
    salt  随机盐
    college  学院
    major  专业
    clazz  班级
    """
    __tablename__ = "Users"

    user_id = db.Column(db.String(16), primary_key=True)
    user_name = db.Column(db.String(64), nullable=False)
    passwd = db.Column(db.String(33), nullable=False)
    salt = db.Column(db.String(64), nullable=False)
    college = db.Column(db.String(64))
    major = db.Column(db.String(64))
    clazz = db.Column(db.Integer)
    role_id = db.Column(db.Integer, db.ForeignKey("Roles.role_id"), nullable=False)
    embedding = db.relationship("Embedding", backref="User", lazy='dynamic')
    create_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def __repr__(self):
        return f"User(id:{self.user_id})"

    def get_id(self):
        return str(self.user_id)

    @staticmethod
    def insert_users():
        from app.utils.utils import create_salt, md5_with_salt
        role = Role.query.filter_by(role_name="Administrator").first()
        if role is None:
            Role.insert_roles()
        salt = create_salt()
        passwd = md5_with_salt("admin2022", salt)
        admin = User(
            user_id="admin2022",
            user_name="admin2022",
            passwd=passwd,
            salt=salt,
            college="None",
            major="None",
            clazz=0,
            create_time=datetime.now(),
            role_id=role.role_id
        )
        db.session.add(admin)
        db.session.commit()


class Embedding(db.Model):
    """
    人脸特征表
    embd_id  特征ID
    embd_bytes  特征字节数组
    user_id  用户ID
    create_time  创建时间
    """
    __tablename__ = "Embeddings"
    embd_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    embd_bytes = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.String(16), db.ForeignKey("Users.user_id"), nullable=False)
    create_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"Embedding(id:{self.embd_id})"


class ExamInfo(db.Model):
    """
    考试信息表
    """
    __tablename__ = "ExamInfo"
    exam_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    begin_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    def __repr__(self):
        return f"ExamInfo(id:{self.exam_id})"
