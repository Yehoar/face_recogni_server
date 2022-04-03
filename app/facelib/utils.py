import cv2
import numpy as np


def resize_image(img: np.ndarray, new_shape, padding=True):
    """
    :param img:
    :param new_shape: (w, h)
    :param padding:
    :return: resize image
    """
    if img.shape[:2] == new_shape[:2:-1]:
        return img
    if not padding:
        return cv2.resize(img, new_shape)
    h, w, c = img.shape
    scale = min(new_shape[0] / w, new_shape[1] / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    img = cv2.resize(img, (new_w, new_h))
    border = np.ones(shape=(new_shape[0], new_shape[1], c), dtype=np.uint8) * 128
    pad_w = (new_shape[1] - new_w) // 2
    pad_h = (new_shape[0] - new_h) // 2
    border[pad_h:pad_h + new_h, pad_w:pad_w + new_w, :] = img
    return border
