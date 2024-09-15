# models/frame_data_model.py

from pydantic import BaseModel
from typing import List, Any


class FrameDataModel(BaseModel):
    timestamp: float
    person_positions: List[Any] = []

    # 可以快速添加新的屬性，例如：
    # additional_info: dict = {}
