# models/frame_data_model.py

from pydantic import BaseModel, ConfigDict
from typing import List, Any, Optional
from ultralytics import YOLOWorld
import supervision as sv


class FrameDataModel(BaseModel):
    timestamp: float

    person_detection_stage_finish: bool = False  # 是這樣嗎xd
    image_cropping_stage_finish: bool = False
    image_binarization_stage_finish: bool = False
    deblurring_stage_finish: bool = False

    # 初始化YOLO model/分類類別 /偵測到的物件們
    model: Optional[YOLOWorld] = None
    detection_class: List[str] = []
    detections: Optional[sv.Detections] = None

    # 單獨物件列表
    people_boxes: List[Any] = []
    blackboard_boxes: List[Any] = []

    # 配置项，允许任意类型
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def serialized(self):
        return str(
            {
                "timestamp": self.timestamp,
                "people_boxes": self.people_boxes,
            }
        )
