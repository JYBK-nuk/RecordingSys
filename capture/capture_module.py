# capture/capture_module.py

from capture.video_capture import VideoCapture
from capture.audio_capture import AudioCapture
from typing import List, Optional
from collections import defaultdict
from .logger import logger
from models.frame_data_model import FrameDataModel
from pipeline.pipeline_stage import PipelineStage
from storage.storage_module import StorageModule


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


class CaptureBuffer:
    videos = {}
    audios = defaultdict(callable)

    def save_frame(self, frame, timestamp: float, data: FrameDataModel):
        self.videos[timestamp] = (frame, data, timestamp)

    def set_audio_callback(self, source: int, callback: callable):
        self.audios[source] = callback


class CaptureModule:
    def __init__(
        self,
        video_sources: List[VideoSource] = [],
        audio_sources: List[AudioSource] = [],
    ):
        """
        初始化捕捉模塊，管理多個視頻和音頻捕捉

        參數：
        - video_sources: 視頻源列表，可以是攝像頭索引或視頻文件路徑
        - audio_sources: 音頻源列表，可以是音頻設備名稱或文件路徑
        """
        self.video_captures: List[VideoCapture] = []
        self.audio_captures: List[AudioCapture] = []

        self.buffer: CaptureBuffer = CaptureBuffer()

        # 創建視頻捕獲實例
        for idx, source in enumerate(video_sources):
            # 將處理函數傳遞給 VideoCapture
            vc = VideoCapture(
                source.source,
                source.pipelines,
                self.process_video_frame,
            )

            self.video_captures.append(vc)

        # 創建音頻捕獲實例
        for idx, source in enumerate(audio_sources):
            ac = AudioCapture(
                source=source.source,
                out_func=self.process_audio_frame,
                samplerate=source.samplerate,
                channels=source.channels,
            )
            self.audio_captures.append(ac)

    def process_video_frame(self, frame, timestamp: float, data: FrameDataModel):
        self.storage_module.save_frame(frame, timestamp, data)

    def process_audio_frame(self, frame, timestamp: float, source: int):
        self.storage_module.save_audio_frame(frame, timestamp, source)

    def capture_kernel_start(self):
        for vc in self.video_captures:
            logger.info(f"👀 Starting video capture : {vc.source}")
            vc.start()
        for ac in self.audio_captures:
            logger.info(f"👀 Starting audio capture : {ac.source}")
            ac.start()

    def capture_kernel_stop(self):
        for vc in self.video_captures:
            logger.info(f"🛑 Stopping video capture : {vc.source}")
            vc.stop()
        for ac in self.audio_captures:
            logger.info(f"🛑 Stopping audio capture : {ac.source}")
            ac.stop()
