# pipeline/stages/person_detection_stage.py

import json
import random
from typing import Any, Tuple
from pipeline import PipelineStage
from models import FrameDataModel
import numpy as np


class PersonDetectionStage(PipelineStage):
    def __init__(self, threshold: float = 0.5):
        """
        初始化人物檢測階段

        參數：
        - threshold: 檢測閾值
        """
        self.threshold: float = threshold

    def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
        """
        執行人物檢測

        參數：
        - frame: 當前視頻幀
        - data: 當前幀的數據模型

        返回：
        - frame: 處理後的視頻幀
        - data: 更新後的數據模型
        """

        data.person_positions = self.__test_generate_random_positions()
        return frame, data

    def __test_generate_random_positions(self) -> Any:
        test = [
            {
                "x": random.randint(0, 1920),
                "y": random.randint(0, 1080),
            }
            for _ in range(random.randint(0, 10))
        ]
        return json.dumps(test)
        
