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


class CaptureModule:
    def __init__(
        self,
        storage_module: StorageModule,
        video_sources: List[VideoSource] = [],
        audio_sources: List[str] = [],
    ):
        """
        初始化捕捉模塊，管理多個視頻和音頻捕捉

        參數：
        - video_sources: 視頻源列表，可以是攝像頭索引或視頻文件路徑
        - audio_sources: 音頻源列表，可以是音頻設備名稱或文件路徑
        """
        self.video_captures = []
        self.audio_captures = []
        self.storage_module = storage_module

        # 創建視頻捕獲實例
        for idx, source in enumerate(video_sources):
            print("Initializing video capture module with source:", source.source)
            # 將處理函數傳遞給 VideoCapture
            vc = VideoCapture(
                source.source,
                source.pipelines,
                self.process_video_frame,
            )

            self.video_captures.append(vc)

        # 創建音頻捕獲實例
        for source in audio_sources:
            # TODO
            # ac = AudioCapture(source=source, out_func=None)
            # self.audio_captures.append(ac)
            pass

        logger.info("Capture module initialized.\n")
        print("Sources:", video_sources, audio_sources)

    def process_video_frame(self, frame, timestamp: float, data: FrameDataModel):
        self.storage_module.save_frame(frame, timestamp, data)

    def process_audio_frame(self, frame, timestamp: float):
        # TODO
        pass

    def start_capture(self) -> None:
        """
        開始所有視頻和音頻捕捉
        """
        for vc in self.video_captures:
            print("Starting video capture :", vc.source)
            vc.start()
        for ac in self.audio_captures:
            print("Starting audio capture :", ac.source)
            ac.start()

    def stop_capture(self) -> None:
        """
        停止所有視頻和音頻捕捉
        """
        for vc in self.video_captures:
            vc.stop()
        for ac in self.audio_captures:
            ac.stop()
