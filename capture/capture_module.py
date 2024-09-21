from capture.video_capture import VideoCapture
from capture.audio_capture import AudioCapture
from typing import List, Optional
from collections import defaultdict
from .logger import logger
from models.frame_data_model import FrameDataModel
from pipeline.pipeline_stage import PipelineStage
from storage.storage_module import StorageModule
import cv2
import threading


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
        self.video_captures: List[VideoCapture] = []
        self.audio_captures: List[AudioCapture] = []
        self.storage_module: StorageModule = None
        self.preview_windows = {}
        self.is_running = True

        # 創建視頻捕獲實例
        for idx, source in enumerate(video_sources):
            vc = VideoCapture(
                source.source,
                source.pipelines,
            )
            self.video_captures.append(vc)

        print("\n".join([str(vc.source) for vc in self.video_captures]))

        # 創建音頻捕獲實例
        for idx, source in enumerate(audio_sources):
            ac = AudioCapture(
                source=source.source,
                out_func=self.process_audio_frame,
                samplerate=source.samplerate,
                channels=source.channels,
            )
            self.audio_captures.append(ac)

        # 啟動所有捕獲
        self.start_all_captures()

    def process_audio_frame(self, frame, timestamp: float, source: int):
        # 將音頻數據保存到 buffer
        pass

    def start_preview(self):
        threading.Thread(target=self._start_preview).start()

    def _start_preview(self):
        # Initialize preview windows for each video capture source
        for video_capture in self.video_captures:
            source_id = video_capture.source
            window_name = f"Preview - {source_id}"
            self.preview_windows[source_id] = window_name

            # Create window for each video source
            logger.info(f"👀 Starting preview : {source_id}")
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        # Main loop for showing preview
        while self.is_running:
            for video_capture in self.video_captures:
                frame = None
                frame = video_capture.buffer.get("frame")
                if frame is not None:
                    # Show frame in the corresponding preview window
                    window_name = self.preview_windows[video_capture.source]
                    cv2.imshow(window_name, frame)

            # Process window events and display delay
            cv2.waitKey(1)

        # Clean up and close all windows when preview is stopped
        cv2.destroyAllWindows()

    def start_all_captures(self):
        for vc in self.video_captures:
            logger.info(f"👀 Starting video capture : {vc.source}")
            vc.start()
        for ac in self.audio_captures:
            logger.info(f"👀 Starting audio capture : {ac.source}")
            ac.start()
        self.start_preview()

    def stop_all_captures(self):
        self.is_running = False
        for vc in self.video_captures:
            vc.stop()
        for ac in self.audio_captures:
            ac.stop()
        cv2.destroyAllWindows()
        # If recording is in progress, stop it
        if self.storage_module:
            self.storage_module.stop_video_writer_thread()
            
    # TODO: Implement the following methods
    def start_recording(self) -> None:
        self.storage_module = StorageModule()

    def stop_recording(self) -> None:
        if self.storage_module:
            pass
