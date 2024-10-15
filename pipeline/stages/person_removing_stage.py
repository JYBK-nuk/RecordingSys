# pipeline/stages/image_cropping_stage.py

from typing import Any, Tuple
from pipeline import PipelineStage
from models import FrameDataModel
import numpy as np
import supervision as sv


class PersonRemovingStage(PipelineStage):
    def __init__(self, crop_size: Tuple[int, int] = (100, 100)):
        """
        初始化圖像裁剪階段

        參數：
        - crop_size: 裁剪尺寸（寬，高）
        """
        self.crop_size: Tuple[int, int] = crop_size
        self.first_frame = True
        self.canvas = None

    def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
        """
        執行圖像裁剪

        參數：
        - frame: 當前影片幀
        - data: 當前幀的數據模型

        返回：
        - frame: 處理後的影片幀
        - data: 更新後的數據模型
        """
        if self.first_frame:
            self.canvas = np.zeros_like(frame)
            self.first_frame = False

        # 去除黑板區域中的人遮擋的地方 如果有做人的偵測的話
        self.canvas = self.process_people_area(
            frame=frame, data=data, canvas=self.canvas, padding=31
        )

        return self.canvas, data


    def process_people_area(self, frame, data: FrameDataModel, canvas, padding=30):
        # 移除 frame 中的人物區域
        for box in data.people_boxes:
            px1, py1, px2, py2 = map(int, box)
            # 計算去除人物區域的範圍，加入 padding 以涵蓋邊緣
            bx1 = max(px1 - padding, 0)
            by1 = max(py1 - padding, 0)
            bx2 = min(px2 + padding, frame.shape[1])
            by2 = min(py2 + padding, frame.shape[0])

            # 將人物區域設為 0 (黑色)，移除該區域
            frame[by1:by2, bx1:bx2] = 0

        # 獲取 frame 中非零區域的索引
        non_zero_indices = np.where(frame != 0)

        # 使用非零索引來更新 canvas，保持原有的零值部分
        canvas[non_zero_indices] = frame[non_zero_indices]
        
        return canvas
