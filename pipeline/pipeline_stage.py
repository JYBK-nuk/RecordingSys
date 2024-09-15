# pipeline/pipeline_stage.py

from typing import Any, Tuple
from models import FrameDataModel


class PipelineStage:
    def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
        """
        處理視頻幀的抽象方法

        參數：
        - frame: 當前視頻幀
        - data: 當前幀的數據模型

        返回：
        - frame: 處理後的視頻幀
        - data: 更新後的數據模型
        """
        raise NotImplementedError("Subclasses must implement this method")
