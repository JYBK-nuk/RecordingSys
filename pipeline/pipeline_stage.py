# pipeline/pipeline_stage.py

from typing import Any, Tuple
from models import FrameDataModel


class PipelineStage:
    def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
        """
        處理影片幀的抽象方法

        參數：
        - frame: 當前影片幀
        - data: 當前幀的數據模型

        返回：
        - frame: 處理後的影片幀
        - data: 更新後的數據模型
        """
        raise NotImplementedError("Subclasses must implement this method")

    def get_parameters(self) -> dict:
        """
        獲取處理階段的參數

        返回：
        - params: 參數字典
        """
        pass

    def set_parameters(self, params: dict) -> None:
        pass
