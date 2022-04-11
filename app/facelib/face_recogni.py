import os
import sys

project_path = os.path.join(os.path.dirname(__file__), os.path.pardir)
sys.path.append(project_path)

from app.config import BaseConfig
from .utils import resize_image

import time
import logging
import yaml
import numpy as np
import tensorflow as tf
from tensorflow.keras import Model
from tensorflow.keras.models import load_model
from scipy.spatial.distance import pdist

logger = None


def timeit(prefix):
    global logger
    if logger is None:
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def decorator(func):
        def inner(*args, **kwargs):
            enter_time = time.time()
            func(*args, **kwargs)
            exit_time = time.time()
            logger.info(f"{prefix}time used: {exit_time - enter_time:3.3f}s")

        return inner

    return decorator


class FaceRecogni:
    INSTANCE = None

    def __init__(self):
        self.metric = None
        self.model_format = None
        self.model_path = None
        self.input_shape = None
        self.output_shape = None
        self.normalize = None
        self.config = None
        self.model = None
        self.threshold = None

    @timeit(prefix="FaceRecogni Prepare: ")
    def prepare(self):
        # 加载配置
        config_yaml = os.path.join(BaseConfig.FACE_RECOGNI_MODEL_PATH, "config.yaml")
        with open(config_yaml, 'r', encoding="utf-8") as stream:
            config = yaml.safe_load(stream)
        # 模型路径
        self.model_path = os.path.join(BaseConfig.FACE_RECOGNI_MODEL_PATH, config["name"])
        self.model_path = os.path.abspath(self.model_path)
        # 输入图片格式
        self.input_shape = config["input_shape"]
        self.output_shape = config["output_shape"]
        # 预处理
        rgb_mean = np.array(config["mean"], dtype=np.float32)
        rgb_std = np.array(config["std"], dtype=np.float32)
        self.normalize = lambda x: (x / 255.0 - rgb_mean) / rgb_std
        # 后处理
        self.metric = config["metric"].lower()
        self.threshold = config["threshold"]

        # 加载模型
        self.model_format = config["format"].upper()
        self.model: Model = load_model(self.model_path)
        # self.model.summary()

        self.config = config

    @timeit(prefix="FaceRecogni WarmUp ")
    def warm_up(self, n: int = 2):
        # 预热一次
        inputs = np.random.randint(0, 255, (1, 112, 112, 3))
        inputs = self.normalize(inputs)
        for i in range(n):
            self.model(inputs, training=False)

    def preprocessing(self, faces):
        """
        预处理
        :param faces: RGB人脸图片 np.ndarray/tf.Tensor/List of RGB Image
        :return: np.ndarray [batch,height,width,channel]
        """
        if isinstance(faces, list):
            faces_list = [resize_image(face, new_shape=self.input_shape, padding=True) for face in faces]
            faces = np.array(faces_list)
        elif isinstance(faces, tf.Tensor):
            faces = faces.numpy()
        elif not isinstance(faces, np.ndarray):
            raise TypeError("只接受numpy Array或Tensorflow Tensor")

        if len(faces.shape) == 3:
            np.expand_dims(faces, axis=0)

        if len(faces.shape) != 4:
            raise ValueError("只接受一副或多幅RGB图片")

        faces = np.array(faces, dtype=np.float32)
        faces = self.normalize(faces)

        return faces

    def postprocessing(self, embeddings):
        """
        后处理, 对特征向量L2正则化
        :param norm embeddings:
        :return:
        """
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        if isinstance(embeddings, tf.Tensor):
            embeddings = embeddings.numpy()
        embeddings = embeddings.astype(np.float32)
        return embeddings

    def predict(self, faces):
        """
        :param faces: RGB人脸图片 np.ndarray
        :return:  Numpy array of embeddings.
        """
        faces = self.preprocessing(faces)
        embs = self.model.predict(faces)
        embs = self.postprocessing(embs)
        return embs

    def calculate_distance(self, embeddings, metric=None) -> np.ndarray:
        """
        计算Embeddings两两之间的距离
        :param embeddings
        :param metric:
        :return: distances
        """
        embeddings = np.array(embeddings)
        if metric is None:
            metric = self.metric

        if metric == "l2":
            metric = "euclidean"

        return pdist(embeddings, metric=metric)

    @staticmethod
    def get_instance():
        """
        只是减少模块重复导入时的创建，非线程安全单例
        :return:
        """
        if FaceRecogni.INSTANCE is None:
            FaceHandler = FaceRecogni()  # 只会创建一次
            FaceHandler.prepare()  # 加载配置
            if BaseConfig.USE_FACE_RECOGNI:
                FaceHandler.warm_up(5)  # 预热
            FaceRecogni.INSTANCE = FaceHandler

        return FaceRecogni.INSTANCE
