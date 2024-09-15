## TODO
- [ ] 黑板處理 Pipeline stages
- [x] 多軌錄影
  - [x] 多路影像Pipeline處理
  - [x] 多路聲音採集
- [ ] 儲存系統
  - [x] 更多資訊儲存
  - [ ] 多路影像儲存
  - [x] 多路聲音儲存 (wav)
  - [ ] H.264 265 壓縮
  - [ ] Preview 串流輸出
...


## 項目結構

```
├── main.py                           # 程序入口
├── recording_sys.py                  # 主系統 RecordingSys
├── controller.py                     # 遠端控制模塊
├── event_decorators.py               # 事件裝飾器的定義，用於註冊事件處理函數
├── capture/                          # 影音相關模塊
│   ├── capture_module.py             # 影音錄製控制器
│   ├── video_capture.py              # 影像捕捉模塊 # TODO: 還是h.264 265好了，檔案賊大
│   ├── audio_capture.py              # 音訊捕捉模塊
├── pipeline/                         # 處理Pipeline模塊
│   ├── processing_pipeline.py        # 執行處理Pipeline
│   ├── pipeline_stage.py             # 處理階段的BaseClass
│   └── stages/                       # Pipeline 不同的處理階段
│       ├── person_detection_stage.py # Example
│       ├── image_cropping_stage.py   # Example
│       └── deblurring_stage.py       # Example
├── storage/                          # 數據存儲模塊
│   └── storage_module.py             # 負責保存處理後的數據
├── models/                           # 數據模型模塊
│   └── frame_data_model.py           # 幀數據的模型定義
├── requirements.txt                  # 項目依賴的第三方庫列表
│
│
├── recordings/                       # 錄影檔案資料夾
│   └── xxx.h5
└── RecordingReader/
    ├── storage_reader.py             # 錄影檔讀取
    └── client_app.py                 # 自訂撥放器

```

1. **運行程序**
   ```bash
   python main.py
   ```
   
  自訂格式撥放器
  ```bash
   python .\RecordingReader\client_app.py .\recordings\2024-09-15_22-44-08.h5
   ```


2. **與系統交互**

   通過 WebSocket 服務器，發送控制命令（如開始、停止錄製），或者調整處理管道的參數

   **示例命令：**

   - 開始錄製：

     ```json
     {
       "event": "START",
       "data": {}
     }
     ```

   - 停止錄製：

     ```json
     {
       "event": "STOP",
       "data": {}
     }
     ```

   - 啟用處理階段：

     ```json
     {
       "event": "ENABLE_STAGE",
       "data": {
         "stage_name": "PersonDetection"
       }
     }
     ```

   - 禁用處理階段：

     ```json
     {
       "event": "DISABLE_STAGE",
       "data": {
         "stage_name": "PersonDetection"
       }
     }
     ```

   - 設置處理階段參數：

     ```json
     {
       "event": "SET_PARAMETER",
       "data": {
         "stage_name": "PersonDetection",
         "param_name": "threshold",
         "value": 0.7
       }
     }
     ```

## 開發

### 新增事件處理函數

1. **在 `RecordingSys` 類中定義新的事件處理函數**

   使用 `@event_handler('EVENT_NAME')` 裝飾器註冊新事件

   ```python
   from event_decorators import event_handler

   class RecordingSys:
       # ...

       @event_handler('NEW_EVENT')
       async def handle_new_event(self, data: dict) -> None:
           """
           處理 'NEW_EVENT' 事件

           參數：
           - data: 事件傳遞的數據
           """
           # 在此處添加處理邏輯
           pass
   ```

2. **事件自動註冊**

   無需手動註冊，系統會在初始化時自動掃描並註冊所有使用 `@event_handler` 裝飾器的函數

### 新增處理階段

1. **創建新的處理階段文件**

   在 `pipeline/stages/` 目錄下創建新的文件，例如 `new_stage.py`

   ```python
   # pipeline/stages/new_stage.py

   from typing import Any, Tuple
   from pipeline import PipelineStage
   from models import FrameDataModel

   class NewStage(PipelineStage):
       def __init__(self, parameter: Any = None):
           """
           初始化新處理階段

           參數：
           - parameter: 自定義參數
           """
           self.parameter: Any = parameter

       def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
           """
           執行新處理階段的邏輯

           參數：
           - frame: 當前視頻幀
           - data: 當前幀的數據模型

           返回：
           - frame: 處理後的視頻幀
           - data: 更新後的數據模型
           """
           # 在此處添加處理邏輯
           return frame, data
   ```

2. **在 `__init__.py` 中導入新的處理階段**

   ```python
   # pipeline/stages/__init__.py

   from .person_detection_stage import PersonDetectionStage
   from .image_cropping_stage import ImageCroppingStage
   from .deblurring_stage import DeblurringStage
   from .new_stage import NewStage  # 新增的導入

   __all__ = ['PersonDetectionStage', 'ImageCroppingStage', 'DeblurringStage', 'NewStage']
   ```

3. **在 `RecordingSys` 中添加新的處理階段**

   ```python
   # recording_sys.py

   from pipeline.stages import NewStage

   class RecordingSys:
       # ...

       def _initialize_pipeline(self) -> None:
           self.processing_pipeline = ProcessingPipeline()
           self.processing_pipeline.add_stage('PersonDetection', PersonDetectionStage())
           self.processing_pipeline.add_stage('ImageCropping', ImageCroppingStage())
           self.processing_pipeline.add_stage('Deblurring', DeblurringStage())
           self.processing_pipeline.add_stage('NewStage', NewStage())  # 添加新的階段
   ```

### 修改數據模型

1. **在 `FrameDataModel` 中添加新的屬性**

   ```python
   # models/frame_data_model.py

   from pydantic import BaseModel
   from typing import List, Any

   class FrameDataModel(BaseModel):
       timestamp: float
       person_positions: List[Any] = []
       new_attribute: Any = None  # 新增的屬性
   ```

2. **在處理階段中使用新的屬性**

   ```python
   # pipeline/stages/new_stage.py

   class NewStage(PipelineStage):
       # ...

       def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
           # 使用新屬性
           data.new_attribute = 'some value'
           return frame, data
   ```
