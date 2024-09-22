# pipeline/processing_pipeline.py

import time
from typing import List, Tuple, Dict, Any, TYPE_CHECKING
from models import FrameDataModel
from .pipeline_stage import PipelineStage


class ProcessingPipeline:
    def __init__(self, source=0) -> None:
        """
        初始化處理管道，管理處理階段和其配置

        out_func: (frame: Any, data: FrameDataModel) -> None
        """
        self.source = source
        self.stages: List[Tuple[str, PipelineStage]] = []
        self.stage_configs: Dict[str, Dict[str, Any]] = {}

    def add_stage(self, stage_name: str, stage: PipelineStage) -> None:
        """
        添加處理階段

        參數：
        - stage_name: 處理階段名稱，需唯一
        - stage: 處理階段實例
        """
        self.stages.append((stage_name, stage))
        self.stage_configs[stage_name] = {"enabled": True}

    def set_stage_enabled(self, stage_name: str, enabled: bool) -> None:
        """
        設置處理階段的啟用狀態

        參數：
        - stage_name: 處理階段名稱
        - enabled: 布爾值，True 為啟用，False 為禁用
        """
        if stage_name in self.stage_configs:
            self.stage_configs[stage_name]["enabled"] = enabled
            print(f"Stage '{stage_name}' enabled: {enabled}")

    def set_stage_parameter(self, stage_name: str, param_name: str, value: Any) -> None:
        """
        設置處理階段的參數

        參數：
        - stage_name: 處理階段名稱
        - param_name: 參數名稱
        - value: 參數值
        """
        for name, stage in self.stages:
            if name == stage_name:
                setattr(stage, param_name, value)
                print(
                    f"Set parameter '{param_name}' of stage '{stage_name}' to {value}"
                )

    def process(
        self, frame: Any, timestamp: float
    ) -> Tuple[Any, FrameDataModel, float]:
        """
        處理影片幀，按照添加的處理階段順序進行處理

        參數：
        - frame: 待處理的影片幀
        - timestamp: 幀的時間戳
        """
        data = FrameDataModel(timestamp=timestamp)
        for stage_name, stage in self.stages:
            if self.stage_configs[stage_name]["enabled"]:
                frame, data = stage.process(frame, data)

        return frame, data, timestamp
