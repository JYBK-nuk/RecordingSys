# models/frame_data_model.py

from pydantic import BaseModel
from typing import List, Any
from ultralytics import YOLOWorld
import supervision as sv


class FrameDataModel(BaseModel):
    timestamp: float
    person_positions: List[Any] = []
    # 初始化YOLO model/分類類別 /偵測到的物件們
    model: YOLOWorld
    detection_class: List[str] = []
    detections: sv.Detections
    # 單獨物件列表
    people_boxes: List[Any] = []
    combined_boxes: List[Any] = []
    # 可以快速添加新的屬性，例如：
    # additional_info: dict = {}

    def serialized(self):
        return self.model_dump_json()
