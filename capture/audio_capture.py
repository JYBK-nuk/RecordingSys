import threading
import queue
import time
from typing import Optional
import sounddevice as sd
from .logger import logger


class AudioCapture:
    def __init__(
        self,
        source: Optional[int] = None,
        samplerate: int = 44100,
        channels: int = 1,
        blocksize: int = 1024,
    ):
        """
        初始化音頻捕獲模組。

        參數：
        - source: 麥克風設備索引或音頻設備名稱。
        - samplerate: 取樣率（Hz）。
        - channels: 音頻通道數。
        - blocksize: 每個區塊的幀數。
        """
        self.source = source
        self.samplerate = samplerate
        self.channels = channels
        self.blocksize = blocksize

        self.is_running: bool = False
        self.thread: Optional[threading.Thread] = None
        self.audio_buffer = queue.Queue()

        self.stream = None

    def _callback(self, indata, frames, time_info, status):
        """
        由 sounddevice 呼叫的回調函數，每當有新的音頻區塊可用時觸發。

        參數：
        - indata: 輸入的音頻數據。
        - frames: 幀數。
        - time_info: 包含時間信息的字典。
        - status: 音頻流狀態。
        """
        if status:
            logger.error(f"Audio capture status: {status}")
        # 將音頻數據和當前時間戳放入緩衝區
        if self.audio_buffer is not None:
            self.audio_buffer.put((indata.copy(), time.time()))

    def start(self) -> None:
        """
        開始音頻捕獲，通過開啟 InputStream 並開始回調。
        """
        if self.is_running:
            logger.warning("Audio capture is already running.")
            return

        self.is_running = True
        try:
            self.stream = sd.InputStream(
                device=self.source,
                samplerate=self.samplerate,
                channels=self.channels,
                blocksize=self.blocksize,
                callback=self._callback,
            )
            self.stream.start()
            logger.info(f"🎙️ Started audio capture: Source={self.source}")
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            self.is_running = False

    def stop(self) -> None:
        """
        停止音頻捕獲，通過停止並關閉 InputStream。
        """
        if not self.is_running:
            logger.warning("Audio capture is not running.")
            return

        self.is_running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            logger.info(f"🎙️ Stopped audio capture: Source={self.source}")
