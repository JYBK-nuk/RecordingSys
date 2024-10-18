import asyncio
import json
from capture.capture_module import AudioSource, VideoSource
from logger import logger
from controller import ControllerModule
import os
from pipeline.stages import (
    ImageCroppingStage,
    DeblurringStage,
    ImageBinarizationStage,
    PersonRemovingStage,
    ObjectDetectionStage,
)
from recording_sys import RecordingSys


# Sources
audio_sources = [
    AudioSource(source=0, samplerate=44100, channels=1),
    AudioSource(source=2, samplerate=44100, channels=1),
]
video_sources = [
    # VideoSource(
    #     source=0,
    #     pipelines=[
    #         ObjectDetectionStage(),
    #         PersonRemovingStage(),
    #         ImageCroppingStage(),
    #         # DeblurringStage(),
    #         # ImageBinarizationStage(),
    #     ],
    # ),
    VideoSource(
        source=0,
        pipelines=[],
    ),
]



async def main() -> None:
    config = load_config()
    ws_uri: str = config["ws_uri"]
    controller_module = ControllerModule(ws_uri, token=config["token"])

    recording_sys = RecordingSys(
        controller_module=controller_module,
        video_sources=video_sources,
        audio_sources=audio_sources,
        preview_mode=config["preview"],
    )

    try:
        # 啟動 controller module (WebSocket listener)
        controller_module.start()

        # 保持主程式運行，直到收到中斷信號
        while True:
            await asyncio.sleep(1)

    except asyncio.CancelledError:
        logger.warning("Program cancelled.")
    except Exception as e:
        logger.error(f"Some error occurred: {e}")
    finally:
        logger.warning("Shutting down the program...")
        await recording_sys.shutdown()
        await controller_module.stop()
        logger.info("Program exited.")

def load_config():
    config_path = "config.json"
    default_config = {
        "ws_uri": "ws://127.0.0.1:3001",
        "token": "your_token_here",
        "preview": True,
    }
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)

    config = json.load(open(config_path))
    return config

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt (Ctrl+C) detected.")
    except Exception as e:
        logger.error(f"Some error occurred: {e}")
    finally:
        logger.info("Program exited.")
