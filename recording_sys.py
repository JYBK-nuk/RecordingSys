# recording_sys.py

from typing import Any
from capture.capture_module import AudioSource, CaptureModule, VideoSource
from event_decorators import event_handler
import sounddevice as sd
from logger import logger
from storage.storage_module import StorageModule
from controller import ControllerModule
from pipeline.stages import PersonDetectionStage, ImageCroppingStage, DeblurringStage


class RecordingSys:
    def __init__(
        self, controller_module: ControllerModule, storage_module: StorageModule
    ) -> None:
        self.controller_module: ControllerModule = controller_module
        self.storage_module: StorageModule = storage_module
        self.recording: bool = False

        self.capture_module: CaptureModule = None
        self._print_startup_message()
        self._initialize_capture()
        self._register_event_handlers()

    def _print_startup_message(self) -> None:
        startup_message = "👉 Starting up the system..."
        print(startup_message)

    def _initialize_capture(self) -> None:
        logger.info("🎈 Initializing capture module...")
        print(sd.query_devices())
        self.capture_module = CaptureModule(
            storage_module=self.storage_module,
            video_sources=[
                VideoSource(
                    source=0,
                    pipelines=[
                        PersonDetectionStage(),
                        ImageCroppingStage(),
                        DeblurringStage(),
                    ],
                )
            ],
            audio_sources=[
                AudioSource(source=0, samplerate=44100, channels=1),
                AudioSource(source=2, samplerate=44100, channels=1),
            ],
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
            self.capture_module.start_capture()
            logger.info("Recording started. 📹")
        else:
            logger.warning("Recording is already in progress.")

    def stop_recording(self) -> None:
        if self.recording:
            self.recording = False
            self.capture_module.stop_capture()
            logger.info("Recording stopped. 🛑")
        else:
            logger.warning("Recording is not currently in progress.")

    @event_handler("START")
    async def handle_start(self, data: dict) -> None:
        self.start_recording()

    @event_handler("STOP")
    async def handle_stop(self, data: dict) -> None:
        self.stop_recording()

    @event_handler("ENABLE_STAGE")
    async def handle_enable_stage(self, data: dict) -> None:
        stage_name: str = data.get("stage_name")
        self.processing_pipeline.set_stage_enabled(stage_name, True)

    @event_handler("DISABLE_STAGE")
    async def handle_disable_stage(self, data: dict) -> None:
        stage_name: str = data.get("stage_name")
        self.processing_pipeline.set_stage_enabled(stage_name, False)

    @event_handler("SET_PARAMETER")
    async def handle_set_parameter(self, data: dict) -> None:
        stage_name: str = data.get("stage_name")
        param_name: str = data.get("param_name")
        value: Any = data.get("value")
        self.processing_pipeline.set_stage_parameter(stage_name, param_name, value)
