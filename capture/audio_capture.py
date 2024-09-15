# capture/audio_capture.py

import threading
from datetime import timedelta
import time
from typing import Optional, Callable
import numpy as np
import sounddevice as sd


class AudioCapture:
    def __init__(
        self,
        source: int = None,
        out_func: Optional[Callable] = None,
        samplerate=44100,
        channels=1,
    ):
        """
        初始化音頻捕捉模塊

        參數：
        - source: 音頻設備名稱或文件路徑
        - out_func: 處理音頻數據的函數 (indata, timestamp, source)
        """
        self.source = source
        self.samplerate = samplerate
        self.channels = channels
        self.out_func = out_func
        self.is_running: bool = False
        self.start_time: Optional[float] = None
        self.thread: Optional[threading.Thread] = None

    def get_elapsed_time(self) -> str:
        """
        獲取錄音已經進行的時間
        """
        if self.start_time is None:
            return "00:00:00"
        elapsed_seconds = int(time.time() - self.start_time)
        return str(timedelta(seconds=elapsed_seconds))

    def audio_callback(self, indata: np.ndarray, frames: int, time, status):
        """
        音频输入设备的回调函数，用于处理捕获的音频帧

        参数：
        - indata: 输入音频数据
        - frames: 每次回调中的帧数
        - time: 时间信息
        - status: 状态信息
        """
        if not self.is_running:
            return
        timestamp = time.inputBufferAdcTime  # 取得音频输入时间戳
        if self.out_func:
            self.out_func(indata, timestamp, self.source)

    def capture_loop(self) -> None:
        """
        捕獲音頻數據循環，通過 sounddevice 的輸入流進行捕捉
        """
        with sd.InputStream(
            device=self.source,
            channels=self.channels,
            samplerate=self.samplerate,
            callback=self.audio_callback,
        ):
            while self.is_running:
                time.sleep(0.1)

    def start(self) -> None:
        """
        開始音頻捕捉
        """
        if self.is_running:
            return
        self.is_running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self.capture_loop)
        self.thread.start()

    def stop(self) -> None:
        """
        停止音頻捕捉
        """
        self.is_running = False
        if self.thread is not None:
            self.thread.join()
