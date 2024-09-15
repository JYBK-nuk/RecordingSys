# pipeline/stages/image_cropping_stage.py

from typing import Any, Tuple
from pipeline import PipelineStage
from models import FrameDataModel


class ImageCroppingStage(PipelineStage):
    def __init__(self, crop_size: Tuple[int, int] = (100, 100)):
        """
        初始化圖像裁剪階段

        參數：
        - crop_size: 裁剪尺寸（寬，高）
        """
        self.crop_size: Tuple[int, int] = crop_size

    def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
        """
        執行圖像裁剪

        參數：
        - frame: 當前視頻幀
        - data: 當前幀的數據模型

        返回：
        - frame: 處理後的視頻幀
        - data: 更新後的數據模型
        """
        # TODO: 添加實際的裁剪代碼
        return frame, data
