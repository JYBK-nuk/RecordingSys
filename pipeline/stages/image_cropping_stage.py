# pipeline/stages/image_cropping_stage.py

from typing import Any, Tuple, List, Optional
from pipeline import PipelineStage
from models import FrameDataModel
import numpy as np
import cv2


class ImageCroppingStage(PipelineStage):
    def __init__(self, crop_size: Tuple[int, int] = (100, 100)):
        """
        初始化圖片裁切階段。

        參數:
        - crop_size: 裁切後的尺寸 (寬度, 高度)。 (目前未使用，但如果需要可以用於調整尺寸)
        """
        self.crop_size: Tuple[int, int] = crop_size

    def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
        """
        執行圖片裁切，通過合併黑板框並裁切最大的框。

        參數:
        - frame: 當前的視頻幀。
        - data: 當前幀的數據模型。

        回傳:
        - frame: 處理後的視頻幀。
        - data: 更新後的數據模型。
        """
        # 確保有黑板框可以處理
        if not data.blackboard_boxes:
            return frame, data

        # 合併所有黑板框以找到最大的邊界框
        largest_box = self.get_largest_box(data.blackboard_boxes)

        if largest_box:
            x1, y1, x2, y2 = largest_box

            # 確保座標在幀的邊界內
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

            # 將幀裁切到最大的黑板區域
            cropped_frame = frame[y1:y2, x1:x2]
            cropped_frame = cv2.resize(cropped_frame, self.crop_size)

            # 更新幀和數據模型
            frame = cropped_frame
            return frame, data

        # 如果沒有找到有效的框，返回原始幀和數據
        return frame, data

    def get_largest_box(self, boxes: List[Any]) -> Optional[List[int]]:
        """
        從框列表中根據面積識別最大的框。

        參數:
        - boxes: 包含多個邊界框的列表，每個框由 [x1, y1, x2, y2] 定義。

        回傳:
        - 最大的框作為列表 [x1, y1, x2, y2]，如果沒有提供框則回傳 None。
        """
        if not boxes:
            return None

        # 計算每個框的面積並識別最大的那一個
        largest_box = max(boxes, key=lambda box: (box[2] - box[0]) * (box[3] - box[1]))
        return [int(coord) for coord in largest_box[:4]]
