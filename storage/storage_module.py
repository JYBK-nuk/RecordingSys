from collections import defaultdict
import queue
import cv2
import h5py
import wave
import numpy as np
import os
from typing import List, Tuple, Dict, Any, TYPE_CHECKING
from models import FrameDataModel
from datetime import datetime
import threading
import time
import json
from logger import logger

if TYPE_CHECKING:
    from capture.capture_module import CaptureModule


class SaveThread(threading.Thread):
    def __init__(self, storage_module: "StorageModule", fps: int = 30):
        super().__init__()
        self.storage_module = storage_module
        self.is_running = True
        self.fps = fps
        self.video_writers: Dict[str, cv2.VideoWriter] = {}
        self.h5_files: Dict[str, h5py.File] = {}
        self.audio_files: Dict[str, wave.Wave_write] = {}  # 用於存儲音頻文件
        self.frame_counters: Dict[str, int] = {}  # 用於記錄每個 ID 的幀索引

        self.lock = threading.Lock()

    def run(self):
        base_path = os.path.join(
            self.storage_module.base_path, self.storage_module.recording_name, "videos"
        )
        audio_base_path = os.path.join(
            self.storage_module.base_path, self.storage_module.recording_name, "audios"
        )
        os.makedirs(audio_base_path, exist_ok=True)  # 創建音頻存儲目錄

        frame_duration = 1 / self.fps  # 每一幀應該持續的時間

        while self.is_running:
            start_time = time.time()  # 記錄開始時間

            # 獲取視頻幀
            frames, datas, _ = self.storage_module.capture_module.get_frame_buffer()

            # 處理視頻幀
            for id_, frame in frames.items():
                data = datas.get(id_)

                if frame is None:
                    continue

                # 初始化幀索引
                if id_ not in self.frame_counters:
                    self.frame_counters[id_] = 0

                frame_index = self.frame_counters[id_]
                self.frame_counters[id_] += 1  # 更新幀索引

                if data is None:
                    data_model = FrameDataModel(timestamp=time.time())
                else:
                    data_model = data  # 假設 data 已經是 FrameDataModel 的實例

                serialized_data = json.loads(data_model.serialized())

                # 確保線程安全地訪問 writers 和 files
                with self.lock:
                    # 初始化 video_writers 和 h5_files 如果尚未完成
                    if id_ not in self.video_writers:
                        video_dir = os.path.join(base_path, str(id_))
                        os.makedirs(video_dir, exist_ok=True)
                        video_path = os.path.join(video_dir, "video.mp4")
                        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                        height, width = frame.shape[:2]
                        self.video_writers[id_] = cv2.VideoWriter(
                            video_path, fourcc, self.fps, (width, height)
                        )

                    if id_ not in self.h5_files:
                        h5_path = os.path.join(base_path, str(id_), "data.h5")
                        self.h5_files[id_] = h5py.File(h5_path, "a")
                        # 創建 datasets 如果不存在
                        if "frame_indices" not in self.h5_files[id_]:
                            self.h5_files[id_].create_dataset(
                                "frame_indices", shape=(0,), maxshape=(None,), dtype="i"
                            )
                        if "timestamps" not in self.h5_files[id_]:
                            self.h5_files[id_].create_dataset(
                                "timestamps", shape=(0,), maxshape=(None,), dtype="f"
                            )
                        if "data" not in self.h5_files[id_]:
                            self.h5_files[id_].create_dataset(
                                "data",
                                shape=(0,),
                                maxshape=(None,),
                                dtype=h5py.string_dtype(encoding="utf-8"),
                            )

                    # 檢查影像格式並處理
                    if len(frame.shape) == 2:
                        # 影像是單通道（灰階），需要轉換為 BGR 格式
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    else:
                        # 影像已經是 BGR 格式，不需要轉換
                        frame_bgr = frame

                    # 確保尺寸與 VideoWriter 初始化時的尺寸一致（可選）
                    frame_bgr_resized = cv2.resize(frame_bgr, (width, height))

                    # 寫入 VideoWriter
                    self.video_writers[id_].write(frame_bgr_resized)

                    # 附加資料到 h5 文件
                    h5_file = self.h5_files[id_]

                    # 更新 frame_indices
                    h5_file["frame_indices"].resize(
                        (h5_file["frame_indices"].shape[0] + 1,)
                    )
                    h5_file["frame_indices"][-1] = frame_index

                    # 更新 timestamps
                    timestamp = serialized_data.get("timestamp", time.time())
                    h5_file["timestamps"].resize((h5_file["timestamps"].shape[0] + 1,))
                    h5_file["timestamps"][-1] = timestamp

                    # 更新 data
                    h5_file["data"].resize((h5_file["data"].shape[0] + 1,))
                    h5_file["data"][-1] = json.dumps(serialized_data)

            # 處理音頻幀
            with self.lock:
                for (
                    source_id,
                    audio_queue,
                ) in self.storage_module.audio_buffers.items():
                    if source_id not in self.audio_files:
                        # 初始化音頻文件
                        audio_dir = os.path.join(
                            self.storage_module.base_path,
                            self.storage_module.recording_name,
                            "audios",
                            str(source_id),
                        )
                        os.makedirs(audio_dir, exist_ok=True)
                        audio_path = os.path.join(audio_dir, "audio.wav")
                        self.audio_files[source_id] = wave.open(audio_path, "wb")
                        # 設定音頻參數
                        # 假設採樣率和通道數與 AudioCapture 一致
                        capture = next(
                            (
                                ac
                                for ac in self.storage_module.capture_module.audio_captures
                                if ac.source == source_id
                            ),
                            None,
                        )
                        if capture:
                            self.audio_files[source_id].setnchannels(capture.channels)
                            self.audio_files[source_id].setsampwidth(
                                2
                            )  # 假設 16-bit 音頻
                            self.audio_files[source_id].setframerate(capture.samplerate)
                        else:
                            logger.error(
                                f"No matching AudioCapture found for source {source_id}"
                            )

                    while not audio_queue.empty():
                        audio_frame, audio_timestamp = audio_queue.get()
                        # 將音頻數據轉換為適合寫入 WAV 的格式
                        audio_data = (audio_frame * 32767).astype(
                            np.int16
                        )  # 假設 float32 到 int16
                        self.audio_files[source_id].writeframes(audio_data.tobytes())

            # 計算該次迴圈所花的時間
            end_time = time.time()
            elapsed_time = end_time - start_time

            # 如果處理速度過快，則休眠剩餘時間來保持 FPS 穩定
            sleep_time = frame_duration - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)

        # 清理：釋放所有 video writers 和關閉 h5 文件，並關閉音頻文件
        with self.lock:
            for writer in self.video_writers.values():
                writer.release()
            self.video_writers.clear()

            for h5_file in self.h5_files.values():
                h5_file.close()
            self.h5_files.clear()

            for audio_writer in self.audio_files.values():
                audio_writer.close()
            self.audio_files.clear()

    def stop(self):
        self.is_running = False


class StorageModule:
    def __init__(
        self,
        recording_name: str,
        capture_module: "CaptureModule",
        fps: int = 30,
        base_path: str = "recordings",
    ):
        self.recording_name = recording_name
        self.capture_module = capture_module
        self.save_thread = SaveThread(self, fps=fps)
        self.base_path = base_path
        self.audio_buffers = defaultdict(queue.Queue)

    def start(self):
        # 創建基礎錄製目錄
        video_path = os.path.join(self.base_path, self.recording_name, "videos")
        audio_path = os.path.join(self.base_path, self.recording_name, "audios")
        os.makedirs(video_path, exist_ok=True)
        os.makedirs(audio_path, exist_ok=True)
        # 開始保存線程
        self.save_thread.start()
        logger.info(f"StorageModule started recording: {self.recording_name}")

    def stop(self):
        # 停止保存線程
        self.save_thread.stop()
        logger.info(f"StorageModule stopped recording: {self.recording_name}")
