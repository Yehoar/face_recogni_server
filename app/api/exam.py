"""
exam.py
与考试信息相关的操作
"""

from . import bp_service

import traceback
from datetime import datetime
from flask import request, session, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.models.models import User, ExamInfo, ExamList
from app.api.forms import ExamInfoForm
from app.config import BaseConfig
from app.utils.utils import parse_request, encrypt_response, parse_df


@bp_service.route("/create_exam", methods=['POST'])
@login_required
def create_exam():
    """
    新建考试信息  默认不加密
    form:{}
    file: csv
    :return:
    """
    # noinspection PyBroadException
    try:
        data = request.form.to_dict()
        file = request.files.to_dict().get("file")

        ret, data = parse_request(data, session)
        if not ret or not file:
            return jsonify(status_code="fail", message=data)
        form = ExamInfoForm(formdata=None, data=data)
        if not form.validate():
            return jsonify(status_code="fail", message=form.errors)
        if not current_user.is_active or current_user.role.power <= 0x01:
            return jsonify(status_code="fail", message="权限不足")

        data = form.data  # dict
        # header = ["学号","姓名"]
        df = parse_df(file.filename, file.read(), try_convert=True)
        if df is None:
            return jsonify(status_code="fail", message="文件类型错误")

        if "学号" not in df.columns:
            return jsonify(status_code="fail", message="找不到学号信息")
        if any(df.isnull().any()) or any(df.isna().any()):
            return jsonify(status_code="fail", message="存在空字段")

        # 更新数据库
        student_ids = df.loc[:, "学号"].to_list()
        students = User.query.filter(User.userId.in_(student_ids)).all()

        exam = ExamInfo(
            subject=data["subject"],
            examRoom=data["examRoom"],
            userId=current_user.get_id(),
            beginTime=datetime.strptime(data["beginTime"], "%Y-%m-%d %H:%M"),
            endTime=datetime.strptime(data["endTime"], "%Y-%m-%d %H:%M")
        )
        db.session.add(exam)
        db.session.flush()  # 获取主键

        examList = []
        for student in students:
            p = ExamList(examId=exam.uuid, userId=student.uuid)
            examList.append(p)
        db.session.add_all(examList)
        db.session.commit()
        return jsonify(status_code="success", message="ok", nums=len(examList), examId=exam.uuid)
    except Exception:
        traceback.print_exc()
    return jsonify(status_code="fail", message="服务器内部错误")


@bp_service.route("/del_exam", methods=['POST'])
@login_required
def del_exam():
    """
    删除考试信息
    :return:
    """
    try:
        data = request.get_json()
        ret, data = parse_request(data, session)
        if not ret:
            return jsonify(status_code="fail", message=data)
        if not current_user.is_active or current_user.role.power <= 0x01:
            return jsonify(status_code="fail", message="权限不足")

        examId = data.get("examId", None)
        if examId is None:
            return jsonify(status_code="fail", message="缺失参数")
        exam = ExamInfo.query.filter_by(uuid=examId, userId=current_user.get_id()).first()
        if exam is None:
            return jsonify(status_code="fail", message="找不到相关记录")
        ExamList.query.filter_by(examId=examId).delete()
        ExamInfo.query.filter_by(uuid=examId).delete()
        db.session.commit()
        return jsonify(status_code="success", message="ok")
    except Exception:
        traceback.print_exc()
    return jsonify(status_code="fail", message="服务器内部错误")


@bp_service.route("/get_exam_list", methods=['GET'])
@login_required
def get_exam_list():
    # noinspection PyBroadException
    try:
        args = request.args.to_dict()
        nums = args.get("nums", 10)
        if not isinstance(nums, int) or nums < 1 or nums > 20:
            nums = 10
        if not current_user.is_active or current_user.role.power <= 0x01:
            return jsonify(status_code="fail", message="权限不足")
        exams = ExamInfo.query.filter_by(userId=current_user.uuid).order_by(ExamInfo.createTime.desc()).limit(nums).all()
        info = []
        for exam in exams:
            beginTime = exam.beginTime.strftime("%Y-%m-%d %H:%M")
            endTime = exam.endTime.strftime("%Y-%m-%d %H:%M").split(" ")[-1]
            time = f"{beginTime}-{endTime}"
            cur = {
                "uuid": exam.uuid,
                "subject": exam.subject,
                "examRoom": exam.examRoom,
                "time": time,
                "nums": ExamList.query.filter_by(examId=exam.uuid).count()
            }
            info.append(cur)
        return jsonify(status_code="success", message="ok", info=info)

    except Exception:
        traceback.print_exc()
    return jsonify(status_code="fail", message="服务器内部错误")


@bp_service.route("/load_exam_data", methods=["GET"])
@login_required
def load_exam_data():
    """
    加载考试名单和人脸编码
    """
    try:
        args = request.args.to_dict()
        examId = args.get("examId", None)
        if examId is None:
            return jsonify(status_code="fail", message="参数错误")

        if not current_user.is_active or current_user.role.power <= 0x01:
            return jsonify(status_code="fail", message="权限不足")

        exam = ExamInfo.query.filter_by(uuid=examId).first()
        if exam is None:
            return jsonify(status_code="fail", message="未查询到相关记录")
        students = User.query.join(ExamList, User.uuid == ExamList.userId).filter(ExamList.examId == exam.uuid).all()
        if students is None or len(students) <= 0:
            return jsonify(status_code="fail", message="未查询到考试名单")
        examList = []
        for student in students:
            info = {
                "userId": student.userId,
                "name": student.name,
                "department": student.department,
                "major": student.major,
                "clazz": student.clazz,
                "embd1": "",
                "embd2": "",
            }
            for idx, embedding in enumerate(student.embedding, 1):
                info[f"embd{idx}"] = embedding.embdBytes
                info[f"img{idx}"] = embedding.base64Img
            examList.append(info)
        if examList and BaseConfig.CRYPTO_TYPE:
            ret, data = encrypt_response(examList, session)
            if not ret:  # 加密失败
                return jsonify(status_code="fail", message=data)
            examList = data
        return jsonify(status_code="success", message="ok", examList=examList)
    except Exception:
        traceback.print_exc()
    return jsonify(status_code="fail", message="服务器内部错误")
