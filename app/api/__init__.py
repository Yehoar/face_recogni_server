from flask import Blueprint
from app.config import BaseConfig

# 基础功能
bp_service = Blueprint(name="Service",
                       import_name=__name__,
                       static_folder=BaseConfig.STATIC_FOLDER,
                       template_folder=BaseConfig.TEMPLATE_FOLDER)

# 加载路由，必须在最后
from .admin import init_admin
from . import views
