# recording_sys.py

from typing import Any
from capture.capture_module import AudioSource, CaptureModule, VideoSource
from event_decorators import event_handler
import sounddevice as sd
from logger import logger
from storage.storage_module import StorageModule
from controller import ControllerModule


class RecordingSys:
    def __init__(
        self,
        controller_module: ControllerModule,
        video_sources: list[VideoSource],
        audio_sources: list[AudioSource],
    ) -> None:
        self.controller_module: ControllerModule = controller_module
        self.recording: bool = False

        self.video_sources: list[VideoSource] = video_sources
        self.audio_sources: list[AudioSource] = audio_sources

        self.capture_module: CaptureModule = None
        self._print_startup_message()
        self._initialize_capture()
        self._register_event_handlers()

    def _print_startup_message(self) -> None:
        startup_message = "👉 Starting up the system..."
        print(startup_message)

    def _initialize_capture(self) -> None:
        logger.info("🎈 Initializing capture module...")
        self.capture_module = CaptureModule(
            video_sources=self.video_sources,
            audio_sources=self.audio_sources,
        )
        logger.info("🎈 Capture module initialized.")

    def _register_event_handlers(self) -> None:
        logger.info("🎈 Registering event handlers...")
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, "_event_name"):
                event_name = getattr(attr, "_event_name")
                self.controller_module.register_event_handler(event_name, attr)
        logger.debug(
            "Event handlers registered: {}",
            ", ".join(self.controller_module.event_handlers.keys()),
        )
        logger.info("🎈 Event handlers registered.")

    def start_recording(self) -> None:
        if not self.recording:
            self.recording = True
            self.capture_module.start_recording()
            logger.info("Recording started. 📹")
        else:
            logger.warning("Recording is already in progress.")

    def stop_recording(self) -> None:
        if self.recording:
            self.recording = False
            self.capture_module.stop_recording()
            logger.info("Recording stopped. 🛑")
        else:
            logger.warning("Recording is not currently in progress.")

    def shutdown(self) -> None:
        self.capture_module.stop_all_captures()
        logger.info("👋 Shutting down the system...")

    @event_handler("START")
    async def handle_start(self, data: dict) -> None:
        self.start_recording()

    @event_handler("STOP")
    async def handle_stop(self, data: dict) -> None:
        self.stop_recording()

    @event_handler("ENABLE_STAGE")
    async def handle_enable_stage(self, data: dict) -> None:
        stage_name: str = data.get("stage_name")
        source: int = data.get("source")
        for vc in self.capture_module.video_captures:
            if vc.source == source:
                vc.processing_pipeline.set_stage_enabled(stage_name, True)
                break

    @event_handler("DISABLE_STAGE")
    async def handle_disable_stage(self, data: dict) -> None:
        stage_name: str = data.get("stage_name")
        source: int = data.get("source")
        for vc in self.capture_module.video_captures:
            if vc.source == source:
                vc.processing_pipeline.set_stage_enabled(stage_name, False)
                break

    @event_handler("SET_PARAMETER")
    async def handle_set_parameter(self, data: dict) -> None:
        stage_name: str = data.get("stage_name")
        param_name: str = data.get("param_name")
        value: Any = data.get("value")
        source: int = data.get("source")
        for vc in self.capture_module.video_captures:
            if vc.source == source:
                vc.processing_pipeline.set_stage_parameter(
                    stage_name, param_name, value
                )
                break
