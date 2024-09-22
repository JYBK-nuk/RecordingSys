import threading
import queue
import time
from datetime import datetime
from capture.video_capture import VideoCapture
from capture.audio_capture import AudioCapture
from typing import List, Optional
from collections import defaultdict
from .logger import logger
from models.frame_data_model import FrameDataModel
from pipeline.pipeline_stage import PipelineStage
from storage.storage_module import StorageModule
import cv2
import numpy as np


class VideoSource:
    def __init__(
        self,
        source: Optional[int] = None,
        pipelines: Optional[List[PipelineStage]] = [],
    ):
        self.source = source
        self.pipelines = pipelines


class AudioSource:
    def __init__(self, source: Optional[int] = None, samplerate=44100, channels=1):
        self.source = source
        self.samplerate = samplerate
        self.channels = channels


class CaptureModule:
    def __init__(
        self,
        video_sources: List[VideoSource] = [],
        audio_sources: List[AudioSource] = [],
    ):
        """
        初始化捕獲模組，包含影片和音頻來源。

        參數：
        - video_sources: 影片來源列表。
        - audio_sources: 音頻來源列表。
        """
        self.video_captures: List[VideoCapture] = []
        self.audio_captures: List[AudioCapture] = []
        self.audio_buffers: dict = {}  # 將來源ID映射到音頻緩衝區
        self.storage_module: Optional[StorageModule] = None
        self.preview_windows = {}
        self.is_running = True

        # 初始化影片捕獲
        for source in video_sources:
            vc = VideoCapture(
                source.source,
                source.pipelines,
            )
            self.video_captures.append(vc)

        logger.info(f"Video sources: {[vc.source for vc in self.video_captures]}")

        # 初始化音頻捕獲
        for source in audio_sources:
            ac = AudioCapture(
                source=source.source,
                samplerate=source.samplerate,
                channels=source.channels,
            )
            self.audio_captures.append(ac)
            self.audio_buffers[source.source] = ac.audio_buffer

        # 開始所有捕獲
        self.start_all_captures()

    def start_preview(self):
        """
        開始預覽，創建一個獨立的線程來顯示影片幀。
        """
        threading.Thread(target=self.__preview_loop, daemon=True).start()

    def __preview_loop(self):
        """
        預覽循環，持續顯示所有影片來源的最新幀。
        """
        # 初始化每個影片來源的預覽視窗
        for video_capture in self.video_captures:
            source_id = video_capture.source
            window_name = f"Preview - {source_id}"
            self.preview_windows[source_id] = window_name

            # 為每個影片來源創建視窗
            logger.info(f"👀 Starting preview: {source_id}")
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        # 顯示預覽的主循環
        while self.is_running:
            for video_capture in self.video_captures:
                frame = video_capture.buffer.get("frame")
                if frame is not None:
                    # 檢查影像格式並處理
                    if len(frame.shape) == 2:
                        # 單通道灰階影像，轉換為 BGR
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    else:
                        frame_bgr = frame

                    # 顯示影像
                    window_name = self.preview_windows[video_capture.source]
                    cv2.imshow(window_name, frame_bgr)

            # 處理視窗事件和顯示延遲
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.is_running = False

        # 停止預覽時清理並關閉所有視窗
        cv2.destroyAllWindows()

    def get_frame_buffer(self):
        """
        獲取所有影片來源的幀、資料和時間戳。

        返回：
        - videos: 影片幀字典，鍵為來源ID。
        - data: 資料字典，鍵為來源ID。
        - timestamp: 時間戳字典，鍵為來源ID。
        """
        videos = {}
        data = {}
        timestamp = {}
        for vc in self.video_captures:
            videos[vc.source] = vc.buffer.get("frame")
            data[vc.source] = vc.buffer.get("data")
            timestamp[vc.source] = vc.buffer.get("timestamp")
        return videos, data, timestamp

    def check_all_ready(self):
        """
        檢查所有影片來源是否已準備好影片幀。

        返回：
        - True 如果所有影片來源都有幀，否則 False。
        """
        for vc in self.video_captures:
            if vc.buffer.get("frame") is None:
                return False
        return True

    def start_all_captures(self):
        """
        開始所有影片和音頻捕獲，並啟動預覽。
        """
        for vc in self.video_captures:
            logger.info(f"📹 Starting video capture: {vc.source}")
            vc.start()
        for ac in self.audio_captures:
            logger.info(f"🎙️ Starting audio capture: {ac.source}")
            ac.start()
        self.start_preview()

    def stop_all_captures(self):
        """
        停止所有影片和音頻捕獲，並關閉預覽視窗。如果正在錄製，則停止錄製。
        """
        self.is_running = False
        logger.info("🛑 Stopping all captures")
        for vc in self.video_captures:
            vc.stop()
        for ac in self.audio_captures:
            ac.stop()
        cv2.destroyAllWindows()
        # 如果錄製正在進行，停止它
        if self.storage_module:
            self.storage_module.stop()

    def start_recording(self) -> None:
        """
        開始錄製，初始化 StorageModule 並啟動保存線程。
        """
        file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.storage_module = StorageModule(file_name, self)
        while not self.check_all_ready():
            time.sleep(0.1)  # 避免忙等待
        self.storage_module.start()

    def stop_recording(self) -> None:
        """
        停止錄製，並釋放 StorageModule 資源。
        """
        if self.storage_module:
            self.storage_module.stop()
            self.storage_module = None
