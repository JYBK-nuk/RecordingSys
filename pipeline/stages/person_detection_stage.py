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

        data.detections = self.get_detections(frame, data.model)  # 偵測到的物件們
        
        # === preview ===
        # using supervisor to draw the boxes
        round_box_annotator = sv.RoundBoxAnnotator()
        annotated_frame = round_box_annotator.annotate(
            scene=frame.copy(),
            detections=data.detections,
        )
        cv2.imshow("preview_log_person", annotated_frame)
        cv2.waitKey(1)
        # === preview ===
        
        data.people_boxes, data.combined_boxes = self.get_people_boxes(  # 單獨物件列表
            data.detections
        )
        data.person_detection_stage_finish = True
        
        return frame, data

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
