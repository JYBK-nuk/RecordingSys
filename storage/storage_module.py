import cv2
import h5py
import wave
import numpy as np
import os
from typing import Any, List
from models import FrameDataModel
from datetime import datetime
import threading
import time


class StorageModule:
    frame_buffer: dict[int, dict] = {}
    wav_files = {}
    video_files = {}
    video_threads = {}

    def __init__(
        self,
        options: dict = {
            "file_path": "recordings",
        },
    ) -> None:
        self.file_name = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )  # 預設儲存為 WAV/MP4
        self.file_path = options.get("file_path", "recordings")
        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)

    def set_file_name(self, file_name: str) -> None:
        self.file_name = file_name

    def save_frame(
        self, frame: Any, timestamp: float, data: FrameDataModel, source=0
    ) -> None:
        """
        Frame和附加資料放入快取
        """
        self.frame_buffer[source] = {
            "frame": frame,
            "data": data,
            "timestamp": timestamp,
        }

    # Audio storage
    def open_wav_file(self, source, samplerate: int, channels: int) -> None:
        """
        開啟 WAV 檔案進行音訊儲存
        """
        full_file_path = os.path.join(self.file_path, f"{self.file_name}_{source}.wav")
        self.wav_files[source] = wave.open(full_file_path, "wb")
        self.wav_files[source].setnchannels(channels)
        self.wav_files[source].setsampwidth(2)  # 取樣寬度，16位（2位元組）
        self.wav_files[source].setframerate(samplerate)

    def save_audio_frame(
        self, frame: np.ndarray, timestamp: float, source: int
    ) -> None:
        """
        儲存音訊幀到 WAV 檔案
        """
        if self.wav_files[source] is not None:
            audio_data = (frame * 32767).astype(np.int16)  # 轉換為 16 位 PCM 格式
            self.wav_files[source].writeframes(audio_data.tobytes())

    def close_wav_file(self, source: int) -> None:
        """
        關閉 WAV 檔案
        """
        if source in self.wav_files and self.wav_files[source] is not None:
            self.wav_files[source].close()
            self.wav_files.pop(source)

    # Video storage
    def start_video_writer_thread(self, sources: List[int], fps: int = 30) -> None:
        """
        建立一個影片寫入的執行緒，根據FPS從buffer中讀取並寫入到檔案
        """
        self.frame_buffer = {source: None for source in sources}
        for source in self.frame_buffer:

            def write_video():
                interval = 1.0 / fps
                while source in self.video_threads:
                    start_time = time.time()

                    # 儲存幀
                    self.__save_video_frame()
                    self.__save_attached_data()

                    # 控制幀率
                    elapsed = time.time() - start_time
                    time.sleep(max(0, interval - elapsed))

            # 開啟影片檔案
            if source not in self.video_files:
                self.__open_video_file(source, fps=fps)

            # 建立並啟動影片寫入執行緒
            self.video_threads[source] = threading.Thread(target=write_video)
            self.video_threads[source].start()

    def stop_video_writer_thread(self) -> None:
        """
        停止指定source的影片寫入執行緒
        """

        for source in self.frame_buffer:
            # 停止執行緒
            if self.video_threads.get(source) is not None:
                self.video_threads.pop(source, None)
            self.__close_video_file(source)
        self.frame_buffer.clear()

    def __save_video_frame(self) -> None:
        """
        儲存影片幀到檔案
        """
        for source, buffer in self.frame_buffer.items():
            if source in self.video_files and buffer is not None:
                self.video_files[source].write(buffer["frame"])

    def __open_video_file(self, source: int, fps: int = 30) -> None:
        """
        開啟影片檔案進行儲存
        """
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # 使用 MPEG-4 編碼器

        full_file_path = os.path.join(self.file_path, f"{self.file_name}_{source}.mp4")
        self.video_files[source] = cv2.VideoWriter(
            full_file_path, fourcc, fps, (640, 480)
        )

    def __close_video_file(self, source: int) -> None:
        """
        關閉影片檔案
        """
        if source in self.video_files and self.video_files[source] is not None:
            self.video_files[source].release()
            self.video_files.pop(source)

    def __save_attached_data(self) -> None:
        """
        儲存附加資料到 H5 檔案
        """
        full_file_path = os.path.join(self.file_path, f"{self.file_name}.h5")
        for source, buffer in self.frame_buffer.items():
            if buffer is not None:
                with h5py.File(full_file_path, "a") as hf:
                    if f"source_{source}" not in hf:
                        group = hf.create_group(f"source_{source}")
                    else:
                        group = hf[f"source_{source}"]

                    timestamp_key = f"{buffer['timestamp']}"
                    if timestamp_key not in group:
                        sub_group = group.create_group(timestamp_key)
                        sub_group.create_dataset(
                            "data", data=buffer["data"].serialized()
                        )
