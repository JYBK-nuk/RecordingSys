import threading
from datetime import timedelta
import time
from typing import List, Optional, Callable
import cv2
from tqdm import tqdm
from .logger import logger
from pipeline import ProcessingPipeline
from pipeline.pipeline_stage import PipelineStage


class VideoCapture:
    def __init__(
        self,
        source=0,
        pipelines: Optional[List[PipelineStage]] = [],
        out_func: Optional[Callable] = None,
    ):
        """
        初始化視頻捕捉模塊

        參數：
        - source: 攝像頭索引或視頻文件路徑
        - pipelines: 處理管道階段列表
        - out_func: 輸出函數，用於處理後的視頻幀
        """
        self.source = source
        # Use OpenCV to capture video
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            raise Exception(f"Error: Unable to open video source {source}")

        self.is_running: bool = False
        self.start_time: Optional[float] = None
        self.thread: Optional[threading.Thread] = None
        self.processing_pipeline = self._initialize_pipeline(pipelines, out_func)

    def _initialize_pipeline(
        self,
        pipelines: Optional[List[PipelineStage]] = [],
        out_func: Optional[Callable] = None,
    ) -> ProcessingPipeline:
        processing_pipeline = ProcessingPipeline(out_func, source=self.source)
        for stage in pipelines:
            processing_pipeline.add_stage(stage.__class__.__name__, stage)

        logger.info(
            "Processing pipeline initialized with stages: {}",
            ", ".join([name for name, _ in processing_pipeline.stages]),
        )
        return processing_pipeline

    def get_elapsed_time(self) -> str:
        """
        獲取錄制已經進行的時間
        """
        if self.start_time is None:
            return "00:00:00"
        elapsed_seconds = int(time.time() - self.start_time)
        return str(timedelta(seconds=elapsed_seconds))

    def capture_loop(self) -> None:
        """
        捕捉循環，持續捕捉視頻幀，並根據需要處理
        """
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Error: Failed to grab frame.")
                break
            timestamp = time.time()

            # Process the frame using the pipeline
            self.processing_pipeline.process(frame, timestamp)
        self.cap.release()

    def start(self) -> None:
        """
        開始視頻捕捉
        """
        if self.is_running:
            return
        self.is_running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self.capture_loop)
        self.thread.start()

    def stop(self) -> None:
        """
        停止視頻捕捉
        """
        self.is_running = False
        if self.thread is not None:
            self.thread.join()
        self.cap.release()
