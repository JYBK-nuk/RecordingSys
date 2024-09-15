# capture/audio_capture.py

import av
import threading
from datetime import timedelta
import time
from typing import Optional, Callable

from tqdm import tqdm


class AudioCapture:
    def __init__(self, source=None, process_func: Optional[Callable] = None):
        """
        初始化音頻捕捉模塊

        參數：
        - source: 音頻設備名稱或文件路徑
        - process_func: 處理函數，如果提供，則音頻幀將被傳遞給該函數處理
        """
        if source is None:
            source = "default"  # 使用默認音頻設備
        self.source = source
        # 根據操作系統設置適當的輸入格式
        self.container = av.open(source, format='alsa', mode='r')
        self.audio_stream = self.container.streams.audio[0]
        self.is_running: bool = False
        self.start_time: Optional[float] = None
        self.thread: Optional[threading.Thread] = None
        self.process_func = process_func  # 處理函數

    def get_elapsed_time(self) -> str:
        """
        獲取錄音已經進行的時間
        """
        if self.start_time is None:
            return "00:00:00"
        elapsed_seconds = int(time.time() - self.start_time)
        return str(timedelta(seconds=elapsed_seconds))

    def capture_loop(self) -> None:
        """
        捕捉循環，持續捕捉音頻數據
        """
        with tqdm(total=0, bar_format="{desc}") as t:
            for packet in self.container.demux(self.audio_stream):
                if not self.is_running:
                    break
                for frame in packet.decode():
                    timestamp = time.time()
                    if self.process_func:
                        # 將音頻幀和時間戳傳遞給處理函數
                        self.process_func(frame, timestamp)
                    else:
                        pass
                    # 更新錄音時間顯示
                    t.set_description(f"錄音時間：{self.get_elapsed_time()}")
                    t.refresh()
        self.container.close()

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
        self.container.close()
