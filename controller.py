# controller.py

import asyncio
from functools import partial
import json
from typing import Dict, Callable
import socketio
from logger import logger

retry_interval = 3  # 重試間隔（秒）


class ControllerModule:
    def __init__(self, ws_uri: str, token: str):
        """
        初始化 ControllerModule，使用 Socket.IO 連接到伺服器並進行 JWT 認證。

        參數：
        - ws_uri: Socket.IO 伺服器的 URI。
        - token: JWT Token，包含機器ID。
        """
        self.ws_uri: str = ws_uri
        self.token: str = token
        self.event_handlers: Dict[str, Callable] = {}
        self.manual_disconnect: bool = False  # 標誌是否手動斷開
        self.sio = socketio.AsyncClient(
            reconnection=False  # 禁用內建的自動重連，改為手動控制
        )
        self.watchdog_task: asyncio.Task = None
        self._register_internal_handlers()

    def _register_internal_handlers(self):
        """
        註冊內部 Socket.IO 事件處理器。
        """

        @self.sio.event
        async def connect():
            logger.info(f"Connected to server at {self.ws_uri} 🎉")

        @self.sio.event
        async def disconnect():
            if self.manual_disconnect:
                logger.info("Manually disconnected from server.")
                self.manual_disconnect = False  # 重置標誌
            else:
                logger.warning("Disconnected from server.")
                logger.info(
                    f"Will attempt to reconnect in {retry_interval} seconds... ⏳"
                )

        @self.sio.event
        async def connect_error(data):
            logger.error(f"Connection failed: {data}")
            logger.info(f"Will attempt to reconnect in {retry_interval} seconds... ⏳")

        @self.sio.on("*")
        async def catch_all(event, data):
            handler = self.event_handlers.get(event)
            if handler:
                logger.debug(f"Received event: {event} with data: {data}")
                await handler(data)
            else:
                logger.warning(f"Unhandled event: {event}")

    def register_event_handler(self, event_name: str, handler: Callable) -> None:
        """
        註冊事件處理函數。

        參數：
        - event_name: 事件名稱。
        - handler: 處理函數。
        """
        self.event_handlers[event_name] = handler
        logger.info(f"Registered handler for event: {event_name}")

    async def _watchdog(self):
        """
        監控連接狀態，如果斷開則重新連接。
        """
        while not self.manual_disconnect:
            if not self.sio.connected:
                try:
                    logger.info(f"Attempting to connect to server at {self.ws_uri} 🌐")
                    await self.sio.connect(self.ws_uri, transports=["websocket"])
                    await self._authenticate()
                    await self.sio.wait()
                except Exception as e:
                    logger.error(f"Failed to connect to server: {e}")
            await asyncio.sleep(retry_interval)

    async def start(self) -> None:
        """
        開始連接到 Socket.IO 伺服器。
        """
        if self.watchdog_task is None or self.watchdog_task.done():
            self.watchdog_task = asyncio.create_task(self._watchdog())
            logger.info("Watchdog task started.")
        else:
            logger.warning("Watchdog task is already running.")

    async def stop(self) -> None:
        """
        斷開與 Socket.IO 伺服器的連接。
        """
        if self.sio.connected:
            self.manual_disconnect = True
            await self.sio.disconnect()
            logger.info("Disconnected from server.")
        if self.watchdog_task:
            self.watchdog_task.cancel()
            try:
                await self.watchdog_task
            except asyncio.CancelledError:
                logger.info("Watchdog task cancelled.")
            self.watchdog_task = None

    async def _authenticate(self) -> None:
        """
        發送 JWT Token 進行認證。
        """
        await self.sio.emit("AUTHENTICATE", {"token": self.token})
        logger.info("Authenticating with server... 🔒")

        # 等待認證回應
        try:
            event, data = await self._wait_for_event("authenticated", "unauthorized")
            if event == "authenticated":
                logger.info("✅ Authentication successful.")
            else:
                logger.error("❌ Authentication failed.")
        except asyncio.TimeoutError:
            logger.error("❌ Authentication timed out.")
            await self.sio.disconnect()

    async def _wait_for_event(self, *event_names):
        """
        等待特定事件的回應。

        參數：
        - event_names: 需要等待的事件名稱。

        返回：
        - 如果事件名稱不是 'message'，返回 (event_name, data)。
        - 如果事件名稱是 'message'，僅返回 data。
        """
        future = asyncio.get_event_loop().create_future()

        async def handler(event, data):
            if not future.done():
                if event != "message":
                    future.set_result((event, data))
                else:
                    future.set_result(data)
                # 移除所有相關的事件處理器
                for e in event_names:
                    self.sio.handlers["/"].pop(e, None)

        # 使用 partial 綁定事件名稱到處理器
        partial_handlers = {}
        for event in event_names:
            partial_handlers[event] = partial(handler, event)
            self.sio.on(event, partial_handlers[event])

        try:
            result = await asyncio.wait_for(future, timeout=10)
            return result
        finally:
            # 確保無論成功還是失敗都移除事件處理器
            for event in event_names:
                self.sio.handlers["/"].pop(event, None)

    def send_event(self, event_name: str, payload: dict) -> None:
        """
        發送事件到伺服器。

        參數：
        - event_name: 事件名稱。
        - payload: 事件負載。
        """
        if self.sio.connected:
            asyncio.create_task(self._send_event_async(event_name, payload))
        else:
            logger.warning("Socket.IO is not connected. Cannot send event.")

    async def _send_event_async(self, event_name: str, payload: dict) -> None:
        try:
            await self.sio.emit(event_name, payload)
            logger.info(f"Sent event: {event_name} with payload: {json.dumps(payload)}")
        except Exception as e:
            logger.error(f"Failed to send event: {e}")
