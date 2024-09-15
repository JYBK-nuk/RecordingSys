import h5py
import numpy as np
import os
from typing import Any
from models import FrameDataModel
from datetime import datetime


class StorageModule:
    def __init__(self, options: dict) -> None:
        self.file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.h5")
        self.file_path = options.get("file_path", "recordings")
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)

    def set_file_name(self, file_name: str) -> None:
        self.file_name = file_name

    def save_frame(self, frame: Any, timestamp: float, data: FrameDataModel) -> None:
        """
        保存視頻幀和附加數據

        參數：
        - frame: 處理後的幀
        - data: 當前幀的數據模型
        """
        frame_array: np.ndarray = np.array(frame)

        full_file_path = os.path.join(self.file_path, self.file_name)

        with h5py.File(full_file_path, "a") as hf:
            grp = hf.create_group(str(timestamp))
            grp.create_dataset("frame", data=frame_array)
            grp.attrs["person_positions"] = data.person_positions
