# main.py

import asyncio
from recording_sys import RecordingSys
from controller import ControllerModule
from storage.storage_module import StorageModule


async def main() -> None:
    ws_uri: str = "ws://server_address"
    controller_module = ControllerModule(ws_uri)
    storage_module = StorageModule({
        "file_path": "recordings",
        "file_name_format": "{timestamp}.h5"
    })
    recording_sys = RecordingSys(controller_module, storage_module)

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
