# pipeline/stages/person_detection_stage.py

import json
import random
from typing import Any, Tuple
from pipeline import PipelineStage
from models import FrameDataModel
import numpy as np
from ultralytics import YOLOWorld
import supervision as sv


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
        - frame: 當前影片幀
        - data: 當前幀的數據模型

        返回：
        - frame: 處理後的影片幀
        - data: 更新後的數據模型
        """

        data.person_positions = self.__test_generate_random_positions()
        data = self.init_object_detection_model(data)  # 初始化YOLO model/分類類別
        data.detections = self.get_detections(frame, data.model)  # 偵測到的物件們
        data.people_boxes, data.combined_boxes = self.get_people_boxes(  # 單獨物件列表
            data.detections
        )
        return frame, data

    def __test_generate_random_positions(self) -> Any:
        test = [
            {
                "x": random.randint(0, 1920),
                "y": random.randint(0, 1080),
            }
            for _ in range(random.randint(0, 10))
        ]
        return test

    def init_object_detection_model(self, data: FrameDataModel):
        data.detection_class = ["person", "blackboard"]
        data.model = YOLOWorld("yolov8s-world.pt")
        data.model.set_classes(data.detection_class)
        return data

    def get_detections(self, frame, model):
        results = model.predict(frame, conf=0.5)
        detection = sv.Detections.from_ultralytics(results[0])
        return detection

    # 把畫面中的人加入=>人列表
    def get_people_boxes(self, detection):
        people_boxes_temp = []
        combined_boxes_temp = []
        for i, (box, class_id) in enumerate(zip(detection.xyxy, detection.class_id)):
            if class_id == 0:  # Person class
                people_boxes_temp.append(box)
            elif class_id != 1:  # Exclude blackboard
                x1, y1, x2, y2 = map(int, box)
                combined_boxes_temp.append([x1, y1, x2, y2, class_id])
        return people_boxes_temp, combined_boxes_temp
