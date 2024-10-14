# pipeline/stages/image_cropping_stage.py

from typing import Any, Tuple
from pipeline import PipelineStage
from models import FrameDataModel
import numpy as np
import supervision as sv
import cv2


class ImageCroppingStage(PipelineStage):
    def __init__(self, crop_size: Tuple[int, int] = (100, 100)):
        """
        初始化圖像裁剪階段

        參數：
        - crop_size: 裁剪尺寸（寬，高）
        """

        self.crop_size: Tuple[int, int] = crop_size

    def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
        """
        執行圖像裁剪

        參數：
        - frame: 當前影片幀
        - data: 當前幀的數據模型

        返回：
        - frame: 處理後的影片幀
        - data: 更新後的數據模型
        """
        # 創建與當前幀相同大小的空白畫布
        blank_canvas = np.zeros_like(frame)

        # 找到黑板的中央最大區域，並存儲在數據模型中
        data.closest_blackboard = self.find_center_axis(frame, data.model)

        # 如果找到黑板，則進行後續處理
        if data.closest_blackboard is not None:
            x1, y1, x2, y2, _ = (
                data.closest_blackboard
            )  # 黑板的座標 (x1, y1) - (x2, y2)
            self.combined_boxes.append(
                data.closest_blackboard
            )  # 將黑板框加入到已偵測的框中

            # 去除黑板區域中的人遮擋的地方 如果有做人的偵測的話
            if data.person_detection_stage_finish:
                blank_canvas = self.process_blackboard_area(  # 處理黑板區域中人的部分
                    frame=frame, data=data, blank_canvas=blank_canvas, padding=31
                )

            # 從空白畫布中裁剪出黑板區域
            cropped_blackboard_canvas = blank_canvas[y1:y2, x1:x2]

            # 從原影片幀中裁剪出黑板區域
            cropped_blackboard_original = frame[y1:y2, x1:x2]

            # 合併裁剪出的黑板區域和原圖進行預覽
            frame_preview = cv2.vconcat(
                [cropped_blackboard_canvas, cropped_blackboard_original]
            )

            # 更新處理後的幀為黑板裁剪部分
            frame = cropped_blackboard_canvas

            # 標記圖像裁剪階段已完成
            data.image_cropping_stage_finish = True

            return frame, data
        else:
            # 如果未找到黑板，則返回原始幀和數據模型
            return frame, data

    def find_closest_blackboard(self, detection, frame_center):
        closest_box = None
        min_distance = float("inf")

        for box, class_id in zip(detection.xyxy, detection.class_id):
            if class_id == 1:  # Class ID for blackboard
                x1, y1, x2, y2 = map(int, box)
                box_center = ((x1 + x2) // 2, (y1 + y2) // 2)
                distance = np.sqrt(
                    (box_center[0] - frame_center[0]) ** 2
                    + (box_center[1] - frame_center[1]) ** 2
                )
                if distance < min_distance:
                    min_distance = distance
                    closest_box = [x1, y1, x2, y2, class_id]

        return closest_box

    def find_center_axis(self, frame, model):
        first_frame = frame
        results = model.predict(first_frame, conf=0.5)
        detection = sv.Detections.from_ultralytics(results[0])
        frame_center = (first_frame.shape[1] // 2, first_frame.shape[0] // 2)
        closest_blackboard = self.find_closest_blackboard(detection, frame_center)
        return closest_blackboard

    # step4
    # 把畫面中的人加入=>人列表
    def annotate_people(self, detection):
        for i, (box, class_id) in enumerate(zip(detection.xyxy, detection.class_id)):
            if class_id == 0:  # Person class
                self.people_boxes.append(box)
            elif class_id != 1:  # Exclude blackboard
                x1, y1, x2, y2 = map(int, box)
                self.combined_boxes.append([x1, y1, x2, y2, class_id])

    # step5
    def process_blackboard_area(
        self, frame, data: FrameDataModel, blank_canvas, padding=30
    ):
        if data.closest_blackboard is not None:
            x1, y1, x2, y2, _ = data.closest_blackboard
            blackboard_area = frame[y1:y2, x1:x2].copy()
            for box in data.people_boxes:
                px1, py1, px2, py2 = map(int, box)
                # Ensure the people box is within the blackboard area
                if px1 < x2 and px2 > x1 and py1 < y2 and py2 > y1:
                    bx1 = max(px1 - padding, x1) - x1
                    by1 = max(py1 - padding, y1) - y1
                    bx2 = min(px2 + padding, x2) - x1
                    by2 = min(py2 + padding, y2) - y1
                    blackboard_area[by1:by2, bx1:bx2] = (
                        0  # Remove the person area from the blackboard
                    )

            # Overlay the modified blackboard area only for non-zero values
            non_zero_indices = np.where(blackboard_area != 0)
            blank_canvas[y1:y2, x1:x2][non_zero_indices] = blackboard_area[
                non_zero_indices
            ]

        return blank_canvas
