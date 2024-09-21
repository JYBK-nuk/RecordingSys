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

    def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
        """
        執行圖像二值化

        參數：
        - frame: 當前視頻幀
        - data: 當前幀的數據模型

        返回：
        - frame: 處理後的二值化視頻幀
        - data: 更新後的數據模型
        """
        # 假設輸入的 frame 是灰度圖像，否則需要先將其轉換為灰度圖
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray_frame = frame

        # 二值化處理
        _, binarized_frame = cv2.threshold(gray_frame, self.threshold, 255, cv2.THRESH_BINARY)

        # 返回處理後的幀和更新後的數據模型
        return binarized_frame, data
