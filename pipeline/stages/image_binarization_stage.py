# pipeline/stages/image_binarization_stage.py

from typing import Any, Tuple
from pipeline import PipelineStage
from models import FrameDataModel
import cv2
import numpy as np


class ImageBinarizationStage(PipelineStage):
    def __init__(self, threshold: int = 127):
        """
        初始化圖像二值化階段

        參數：
        - threshold: 用於二值化的閾值（0-255）
        """
        self.threshold: int = threshold
        self.SauvolaWindowSize: int = 3
        self.dilate_iterations: int = 3

    def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
        """
        執行圖像二值化

        參數：
        - frame: 當前影片幀
        - data: 當前幀的數據模型

        返回：
        - frame: 處理後的二值化影片幀
        - data: 更新後的數據模型
        """
        # 假設輸入的 frame 是灰度圖像，否則需要先將其轉換為灰度圖
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray_frame = frame

        # 二值化處理
        _, binarized_frame = cv2.threshold(
            gray_frame, self.threshold, 255, cv2.THRESH_BINARY
        )
        
        data.image_binarization_stage_finish = True
        # 返回處理後的幀和更新後的數據模型
        return binarized_frame, data

    def adjust_contrast(image: np.ndarray, factor: float) -> np.ndarray:
        mean = np.mean(image)
        return np.clip((1 - factor) * mean + factor * image, 0, 255).astype(np.uint8)

    def process_image(self, image: np.ndarray) -> np.ndarray:
        from skimage import img_as_ubyte
        from skimage.filters import threshold_sauvola

        # 调整对比度
        low_contrast_image = self.adjust_contrast(image, factor=1.7)

        # Sauvola 二值化处理
        window_size = (
            self.SauvolaWindowSize
        )  # Sauvola 方法的窗口大小，需根据图像大小调整
        sauvola_thresh = threshold_sauvola(low_contrast_image, window_size=window_size)
        binary_image = low_contrast_image > sauvola_thresh
        binary_image = img_as_ubyte(binary_image)  # 将布尔图像转换为 uint8 类型

        # 負片效果
        binary_image = 255 - binary_image
        return binary_image

    def binarization(self, image: np.ndarray) -> np.ndarray:
        # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        source_image = image.copy()
        image = self.process_image(image)
        # 使用形態學操作來加強文字區域
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.dilate(image.copy(), kernel, iterations=self.dilate_iterations)

        # BINARIZATION
        _, binary = cv2.threshold(source_image, self.threshold, 255, cv2.THRESH_BINARY)
        # and operation mask and binary image
        image = cv2.bitwise_and(binary, mask)
        # convert to rgb color
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        return image
