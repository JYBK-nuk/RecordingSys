import os
import cv2
import numpy as np


def adjust_contrast(image: np.ndarray, factor: float) -> np.ndarray:
    mean = np.mean(image)
    return np.clip((1 - factor) * mean + factor * image, 0, 255).astype(np.uint8)


def process_image(image: np.ndarray) -> np.ndarray:
    from skimage import img_as_ubyte
    from skimage.filters import threshold_sauvola

    # 调整对比度
    low_contrast_image = adjust_contrast(image, factor=1.7)

    # Sauvola 二值化处理
    window_size = 3  # Sauvola 方法的窗口大小，需根据图像大小调整
    sauvola_thresh = threshold_sauvola(low_contrast_image, window_size=window_size)
    binary_image = low_contrast_image > sauvola_thresh
    binary_image = img_as_ubyte(binary_image)  # 将布尔图像转换为 uint8 类型
    
    # 負片效果
    binary_image = 255 - binary_image
    return binary_image


def draw_contours(image: np.ndarray, contours: list) -> np.ndarray:
    output = image.copy()
    cv2.drawContours(output, contours, -1, (0, 255, 0), 2)
    return output

def binarization(image: np.ndarray) -> np.ndarray:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        source_image = image.copy()
        image = process_image(image)
        # 使用形態學操作來加強文字區域
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.dilate(image.copy(), kernel, iterations=3)

        # BINARIZATION
        _, binary = cv2.threshold(source_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # and operation mask and binary image
        image = cv2.bitwise_and(binary, mask)
        #convert to rgb color
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        return image
        

