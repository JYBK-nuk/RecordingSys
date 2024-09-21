import asyncio
from capture.capture_module import AudioSource, VideoSource
from logger import logger
from recording_sys import RecordingSys
from controller import ControllerModule
from pipeline.stages import (
    PersonDetectionStage,
    ImageCroppingStage,
    DeblurringStage,
    ImageBinarizationStage,
)
from storage.storage_module import StorageModule

is_running = True


async def main() -> None:
    global is_running  # 如果你希望修改這個變量
    ws_uri: str = "ws://server_address"
    controller_module = ControllerModule(ws_uri)
    audio_sources = [
        AudioSource(source=0, samplerate=44100, channels=1),
        AudioSource(source=2, samplerate=44100, channels=1),
    ]
    video_sources = [
        VideoSource(
            source=0,
            pipelines=[
                PersonDetectionStage(),
                ImageCroppingStage(),
                DeblurringStage(),
                ImageBinarizationStage(),
            ],
        ),
        VideoSource(
            source=1,
            pipelines=[ImageBinarizationStage()],
        ),
    ]

    recording_sys = RecordingSys(controller_module, video_sources, audio_sources)

    # Start the controller module (WebSocket listener)
    await controller_module.start()

    # Now you can control the recording system directly
    await test(recording_sys)

    # Keep the main program running
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        is_running = False
        logger.warning("Shutting down...")
        recording_sys.shutdown()


async def test(recording_sys: RecordingSys) -> None:
    print("Testing recording system...")
    recording_sys.start_recording()
    await asyncio.sleep(5)
    await recording_sys.handle_disable_stage({"stage_name": "ImageBinarizationStage", "source": 0})
    await asyncio.sleep(5)
    recording_sys.stop_recording()
    print("Recording stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Exiting...")
