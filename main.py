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


async def main() -> None:
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

    try:
        # 啟動 controller module (WebSocket listener)
        await controller_module.start()

        # 開始錄製
        recording_sys.start_recording()

        # 測試操作
        await test(recording_sys)

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


async def test(recording_sys: RecordingSys) -> None:
    print("測試錄製系統...")
    await asyncio.sleep(5)
    await recording_sys.handle_disable_stage(
        {"stage_name": "ImageBinarizationStage", "source": 0}
    )
    await asyncio.sleep(5)
    recording_sys.stop_recording()
    print("錄製已停止。")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt (Ctrl+C) detected.")
    except Exception as e:
        logger.error(f"Some error occurred: {e}")
    finally:
        logger.info("Program exited.")
