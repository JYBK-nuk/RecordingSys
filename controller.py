# controller/ws_controller_module.py

import asyncio
import json
from typing import Dict, Callable
from websockets import connect, WebSocketClientProtocol
from websockets.exceptions import (
    ConnectionClosedError,
    ConnectionClosedOK,
    InvalidURI,
    InvalidHandshake,
)
from logger import logger


class ControllerModule:
    def __init__(self, ws_uri: str):
        self.ws_uri: str = ws_uri
        self.event_handlers: Dict[str, Callable] = {}
        self.ws_listener_task = None

    def register_event_handler(self, event_name: str, handler: Callable) -> None:
        self.event_handlers[event_name] = handler
        logger.info(f"Registered handler for event: {event_name}")

    async def start(self) -> None:
        self.ws_listener_task = asyncio.create_task(self._ws_listener_loop())

    async def _ws_listener_loop(self) -> None:
        while True:
            try:
                await self._connect_ws()
            except (OSError, InvalidURI, InvalidHandshake) as e:
                logger.error(f"Connection failed: {e}")
                logger.info("Retrying in 60 seconds... ⏳")
                await asyncio.sleep(60)

    async def _connect_ws(self) -> None:
        logger.info(f"Attempting to connect to WebSocket server at {self.ws_uri} 🌐")
        async with connect(self.ws_uri) as websocket:
            logger.success(f"Connected to WebSocket server at {self.ws_uri} 🎉")
            await self._listen_ws(websocket)

    async def _listen_ws(self, websocket: WebSocketClientProtocol) -> None:
        try:
            async for message in websocket:
                event_data = json.loads(message)
                event_name: str = event_data.get("event")
                payload: dict = event_data.get("data", {})
                handler = self.event_handlers.get(event_name)
                if handler:
                    logger.debug(f"Received event: {event_name} with data: {payload}")
                    await handler(payload)
                else:
                    logger.warning(f"Unhandled event: {event_name}")
        except (ConnectionClosedError, ConnectionClosedOK):
            logger.warning("Connection to WebSocket server has been closed.")
