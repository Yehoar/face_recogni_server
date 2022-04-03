"""
google 人脸检测+关键点检测
ref https://google.github.io/mediapipe/solutions/face_mesh.html
"""

import cv2
import glob
import mediapipe as mp

# mp_drawing = mp.solutions.drawing_utils
# mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh


class LandmarkDetector:

    def detect(self, images):
        """
        检测图片中的人脸及关键点
        :param images: List of images|paths
        :return: faces in each images [[{boundingbox:[left,top,right,bottom],landmarks:[[x,y,z]...]}]]
        """
        faces = []
        with mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.50) as face_mesh:
            for idx, file in enumerate(images):
                if isinstance(file, str):
                    image = cv2.imread(file)
                else:
                    image = file
                h, w, c = image.shape
                # Convert the BGR image to RGB before processing.
                results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                # Print and draw face mesh landmarks on the image.
                if not results.multi_face_landmarks:
                    continue

                # faces in image
                faces_in_image = []
                for face_landmarks in results.multi_face_landmarks:
                    face = {"boundingbox": None, "landmarks": []}
                    x_min, y_min, x_max, y_max = 1e4, 1e4, -1e4, -1e4  # 最小人脸框

                    for landmark in face_landmarks.landmark:  # 转换保存格式
                        x, y, z = landmark.x * w, landmark.y * h, landmark.z
                        x_min = min(x, x_min)
                        y_min = min(y, y_min)
                        x_max = max(x, x_max)
                        y_max = max(y, y_max)
                        face["landmarks"].append((x, y, z))
                    face["boundingbox"] = [x_min, y_min, x_max, y_max]
                    faces_in_image.append(face)
                faces.append(faces_in_image)
        return faces

    def crop_faces(self, images, annotations):
        """
        从图片中裁剪人脸
        :param images:
        :param annotations: return from LandmarkDetector.detect
        :return: List of faces
        """
        faces = []
        for idx, image in enumerate(images):
            if isinstance(image, str):
                image = cv2.imread(image)
            faces_in_image = []
            for face in annotations[idx]:
                bbox = face["boundingbox"]
                left, top, right, bottom = list(map(int, bbox))
                crop = image[top:bottom, left:right, :]
                faces_in_image.append(crop)
            faces.append(faces_in_image)
        return faces


if __name__ == '__main__':
    import os

    # For static images:
    IMAGE_FILES = glob.glob(r"D:\Repository\Datasets\facev5_160\**\*.png")
    Detector = LandmarkDetector()
    ret = Detector.detect(IMAGE_FILES)
    faces = Detector.crop_faces(IMAGE_FILES, ret)
    dst_root = r"D:\MyProjects\PyCharm\face_recogni_server\test\casia_v5"

    for idx, image in enumerate(IMAGE_FILES):
        _, name = os.path.split(image)
        if idx % 5 == 0:
            os.makedirs(os.path.join(dst_root, name[:3]), exist_ok=True)
        face = faces[idx][0]
        face = cv2.resize(face, (112, 112))
        cv2.imwrite(os.path.join(dst_root, name[:3], name), face)
