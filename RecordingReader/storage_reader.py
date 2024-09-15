# storage_reader.py

import h5py
import numpy as np
from typing import List, Dict, Any

class StorageReader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.timestamps: List[float] = []
        self.frame_indices: List[str] = []
        self.data: List[Dict[str, Any]] = []
        self._load_indices()

    def _load_indices(self):
        with h5py.File(self.file_path, 'r') as hf:
            for timestamp in sorted(hf.keys(), key=float):
                grp = hf[timestamp]
                attrs = dict(grp.attrs)
                self.timestamps.append(float(timestamp))
                self.frame_indices.append(timestamp)
                self.data.append(attrs)

    def get_frame(self, index: int) -> np.ndarray:
        timestamp = self.frame_indices[index]
        with h5py.File(self.file_path, 'r') as hf:
            frame = hf[timestamp]['frame'][()]
        return frame
