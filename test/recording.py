import asyncio
from recording_sys import RecordingSys


async def test(recording_sys: RecordingSys) -> None:
    print("測試錄製系統...")
    await asyncio.sleep(5)
    # 開始錄製
    recording_sys.start_recording()
    await recording_sys.handle_disable_stage(
        {"stage_name": "ImageBinarizationStage", "source": 0}
    )
    await asyncio.sleep(5)
    recording_sys.stop_recording()
    print("錄製已停止。")
