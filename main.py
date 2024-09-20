# main.py

import asyncio
from capture.capture_module import AudioSource, VideoSource
from recording_sys import RecordingSys
from controller import ControllerModule
from pipeline.stages import PersonDetectionStage, ImageCroppingStage, DeblurringStage
from storage.storage_module import StorageModule


async def main() -> None:
    ws_uri: str = "ws://server_address"
    controller_module = ControllerModule(ws_uri)
    audo_sources = [
        # AudioSource(source=0, samplerate=44100, channels=1),
        # AudioSource(source=2, samplerate=44100, channels=1),
    ]
    viedo_sources = [
        VideoSource(
            source=0,
            pipelines=[
                PersonDetectionStage(),
                ImageCroppingStage(),
                DeblurringStage(),
            ],
        )
    ]

    recording_sys = RecordingSys(
        controller_module, viedo_sources, audo_sources
    )

    # Start the controller module (WebSocket listener)
    await controller_module.start()

    # Now you can control the recording system directly
    await test(recording_sys)

    # Keep the main program running
    while True:
        await asyncio.sleep(1)


async def test(recording_sys: RecordingSys) -> None:
    print("Testing recording system...")
    recording_sys.start_recording()
    await asyncio.sleep(10)  # Record for 10 seconds
    recording_sys.stop_recording()
    print("Recording stopped.")
    # You can also call event handlers directly if needed
    # await recording_sys.handle_enable_stage({"stage_name": "Deblurring"})
    # await recording_sys.handle_disable_stage({"stage_name": "PersonDetection"})


if __name__ == "__main__":
    asyncio.run(main())
