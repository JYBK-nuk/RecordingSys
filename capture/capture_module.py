# capture/capture_module.py

from capture.video_capture import VideoCapture
from capture.audio_capture import AudioCapture
from typing import List, Optional
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


class CaptureModule:
    def __init__(
        self,
        storage_module: StorageModule,
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
        self.storage_module = storage_module

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

    def process_video_frame(
        self, frame, timestamp: float, data: FrameDataModel, source: int
    ):
        self.storage_module.save_frame(frame, timestamp, data, source)

    def process_audio_frame(self, frame, timestamp: float, source: int):
        self.storage_module.save_audio_frame(frame, timestamp, source)

    def start_capture(self) -> None:
        """
        開始所有視頻和音頻捕捉
        """

        for vc in self.video_captures:
            logger.info(f"👀 Starting video capture : {vc.source}")
            vc.start()
        for ac in self.audio_captures:
            logger.info(f"👀 Starting audio capture : {ac.source}")
            self.storage_module.open_wav_file(ac.source, ac.samplerate, ac.channels)
            ac.start()
        self.storage_module.start_video_writer_thread(
            sources=[vc.source for vc in self.video_captures]
        )

    def stop_capture(self) -> None:
        """
        停止所有視頻和音頻捕捉
        """
        logger.info("🛑 Stopping capture module...")
        for vc in self.video_captures:
            vc.stop()
        for ac in self.audio_captures:
            ac.stop()
            self.storage_module.close_wav_file(ac.source)
        self.storage_module.stop_video_writer_thread()
