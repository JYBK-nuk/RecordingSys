# pipeline/stages/person_detection_stage.py

import json
import random
from typing import Any, Tuple

import cv2
from pipeline import PipelineStage
from models import FrameDataModel
import numpy as np
from ultralytics import YOLOWorld
import supervision as sv


class ObjectDetectionStage(PipelineStage):
    def __init__(self, conf=0.5):
        """
        初始化物件檢測階段

        參數：
        -
        """
        self.classes = ["person", "blackboard"]
        self.conf = conf

    def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
        """
        執行物件檢測

        參數：
        - frame: 當前影片幀
        - data: 當前幀的數據模型

        返回：
        - frame: 處理後的影片幀
        - data: 更新後的數據模型
        """
        data.model.set_classes(self.classes)
        data.detections = self.get_detections(frame, data.model)  # 偵測到的物件們
        data.people_boxes, data.blackboard_boxes = self.annotate_box(
            data.detections
        )  # 單獨物件列表
        

        # === preview ===
        # using supervisor to draw the boxes
        round_box_annotator = sv.RoundBoxAnnotator()
        annotated_frame = round_box_annotator.annotate(
            scene=frame.copy(),
            detections=data.detections,
        )
        cv2.imshow("obj_preview_log", annotated_frame)
        cv2.waitKey(1)
        # === preview ===

        return frame, data

    def get_detections(self, frame, model: YOLOWorld):
        results = model.predict(frame, conf=self.conf, verbose=False)
        detection = sv.Detections.from_ultralytics(results[0])
        return detection

    def annotate_box(self, detection):
        people_boxes = []
        blackboard_boxes = []

        for i, (box, class_id) in enumerate(zip(detection.xyxy, detection.class_id)):
            if class_id == 0:  # Person class
                people_boxes.append(box)
            elif class_id == 1:  # Blackboard class
                blackboard_boxes.append(box)
        return people_boxes, blackboard_boxes
