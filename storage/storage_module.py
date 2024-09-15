import h5py
import wave
import numpy as np
import os
from typing import Any
from models import FrameDataModel
from datetime import datetime


class StorageModule:
    def __init__(self, options: dict) -> None:
        self.file_name = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )  # 默認保存為 WAV
        self.file_path = options.get("file_path", "recordings")
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)

        # 打開文件對象
        self.wav_files = {}

    def set_file_name(self, file_name: str) -> None:
        self.file_name = file_name

    def save_frame(self, frame: Any, timestamp: float, data: FrameDataModel) -> None:
        """
        保存視頻幀和附加數據
        """
        frame_array: np.ndarray = np.array(frame)
        full_file_path = os.path.join(self.file_path, self.file_name)

        with h5py.File(f"{full_file_path}.h5", "a") as hf:
            grp = hf.create_group(str(timestamp))
            grp.create_dataset("frame", data=frame_array)
            grp.attrs["person_positions"] = data.person_positions

    def open_wav_file(self, source, samplerate: int, channels: int) -> None:
        """
        打開 WAV 文件進行音頻保存
        """
        full_file_path = os.path.join(self.file_path, f"{self.file_name}_{source}.wav")
        self.wav_files[source] = wave.open(full_file_path, "wb")
        self.wav_files[source].setnchannels(channels)
        self.wav_files[source].setsampwidth(2)  # 采樣寬度，16位（2字節）
        self.wav_files[source].setframerate(samplerate)

    def save_audio_frame(
        self, frame: np.ndarray, timestamp: float, source: int
    ) -> None:
        """
        保存音頻幀到 WAV 文件
        """
        if self.wav_files[source] is not None:
            audio_data = (frame * 32767).astype(np.int16)  # 轉換為 16 位 PCM 格式
            self.wav_files[source].writeframes(audio_data.tobytes())

    def close_wav_file(self, source: int) -> None:
        """
        關閉 WAV 文件
        """
        if self.wav_files[source] is not None:
            self.wav_files[source].close()
            self.wav_files.pop(source)
