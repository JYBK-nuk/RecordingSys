# recording_sys.py

from typing import Any
from capture.capture_module import AudioSource, CaptureModule, VideoSource
from event_decorators import event_handler
import sounddevice as sd
from logger import logger
from controller import ControllerModule
import time
from typing import List



class RecordingSys:
    def __init__(
        self,
        controller_module: ControllerModule,
        video_sources: List[VideoSource],
        audio_sources: List[AudioSource],
        preview_mode: bool = False,
    ) -> None:
        self.controller_module: ControllerModule = controller_module
        self.recording: bool = False
        self.start_time: float = 0.0
        self.count_time: float = 0.0
        self.video_sources: List[VideoSource] = video_sources
        self.audio_sources: List[AudioSource] = audio_sources

        self.capture_module = CaptureModule(
            video_sources=self.video_sources,
            audio_sources=self.audio_sources,
            preview_mode=preview_mode,
            controller_module=self.controller_module,
        )
        self._print_startup_message()
        self._register_event_handlers()
        self.controller_module.on_initial = self.get_current_info

    def _print_startup_message(self) -> None:
        startup_message = "👉 Starting up the system..."
        print(startup_message)

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
            self.start_time = time.time()
            self.capture_module.start_recording()
            logger.info("Recording started. 📹")
        else:
            logger.warning("Recording is already in progress.")

    def stop_recording(self) -> None:
        if self.recording:
            self.recording = False
            self.capture_module.stop_recording()
            self.count_time = time.time() - self.start_time
            logger.info("Recording stopped. 🛑")
        else:
            logger.warning("Recording is not currently in progress.")

    def shutdown(self) -> None:
        self.capture_module.stop_all_captures()
        logger.info("👋 Shutting down the system...")

    def get_current_info(self) -> None:
        time: str = self.count_time
        recording: bool = self.recording
        stages_info = []
        for vc in self.capture_module.video_captures:
            stages_info += vc.processing_pipeline.get_stages()
        logger.info(f"stages_info: {stages_info}")

        self.controller_module.send_event(
            "DATA",
            {
                "current_info": {
                    "recording": recording,
                    "time": time,
                    "stages": stages_info,
                    "is_streaming": self.capture_module.is_streaming,
                }
            },
        )

    @event_handler("START")
    async def handle_start(self, data: dict) -> None:
        self.start_recording()
        logger.info(f"start recording {self.count_time}")
        self.controller_module.send_event(
            "DATA",
            {
                "current_info": {
                    "recording": self.recording,
                    "time": self.count_time,
                }
            },
        )

    @event_handler("STOP")
    async def handle_stop(self, data: dict) -> None:
        self.stop_recording()
        logger.info(f"stop recording {self.count_time}")

        self.controller_module.send_event(
            "DATA",
            {
                "current_info": {
                    "recording": self.recording,
                    "time": self.count_time,
                }
            },
        )

    @event_handler("ENABLE_STAGE")
    async def handle_enable_stage(self, data: dict) -> None:
        stage_name: str = data.get("stage_name")
        source: int = data.get("source")
        for vc in self.capture_module.video_captures:
            if vc.source == source:
                vc.processing_pipeline.set_stage_enabled(stage_name, True)
                self.get_current_info()
                break

    @event_handler("DISABLE_STAGE")
    async def handle_disable_stage(self, data: dict) -> None:
        stage_name: str = data.get("stage_name")
        source: int = data.get("source")
        for vc in self.capture_module.video_captures:
            if vc.source == source:
                vc.processing_pipeline.set_stage_enabled(stage_name, False)
                self.get_current_info()
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
                await self.handle_get_current_info(data)
                break

    @event_handler("GET_CURRENT_INFO")
    async def handle_get_current_info(self, data: dict) -> None:
        self.get_current_info()

    @event_handler("TOGGLE_PREVIEW")
    async def handle_toggle_preview(self, data: dict) -> None:
        self.capture_module.toggle_preview()
        self.get_current_info()
        logger.info(f"preview mode {self.capture_module.preview_mode}")
