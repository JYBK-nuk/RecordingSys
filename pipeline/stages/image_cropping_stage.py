# pipeline/stages/image_cropping_stage.py

from typing import Any, Tuple, List, Optional
from pipeline import PipelineStage
from models import FrameDataModel
import numpy as np
import cv2


class ImageCroppingStage(PipelineStage):
    def __init__(self, crop_size: Tuple[int, int] = (100, 100)):
        """
        Initialize the Image Cropping Stage.

        Parameters:
        - crop_size: Desired crop size (width, height). (Currently unused but can be utilized for resizing if needed)
        """
        self.crop_size: Tuple[int, int] = crop_size

    def process(self, frame: Any, data: FrameDataModel) -> Tuple[Any, FrameDataModel]:
        """
        Execute image cropping by merging blackboard boxes and cropping the largest one.

        Parameters:
        - frame: Current video frame.
        - data: Data model for the current frame.

        Returns:
        - frame: Processed video frame.
        - data: Updated data model.
        """
        # Ensure there are blackboard boxes to process
        if not data.blackboard_boxes:
            return frame, data

        # Merge all blackboard boxes to find the largest bounding box
        largest_box = self.get_largest_box(data.blackboard_boxes)

        if largest_box:
            x1, y1, x2, y2 = largest_box

            # Ensure coordinates are within frame boundaries
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

            # Crop the frame to the largest blackboard area
            cropped_frame = frame[y1:y2, x1:x2]
            cropped_frame = cv2.resize(cropped_frame, self.crop_size)

            # Update the frame and data model
            frame = cropped_frame
            return frame, data

        # If no valid box is found, return the original frame and data
        return frame, data

    def get_largest_box(self, boxes: List[Any]) -> Optional[List[int]]:
        """
        Identify the largest box based on area from a list of boxes.

        Parameters:
        - boxes: List of bounding boxes, each defined by [x1, y1, x2, y2].

        Returns:
        - The largest box as a list [x1, y1, x2, y2] or None if no boxes are provided.
        """
        if not boxes:
            return None

        # Calculate area for each box and identify the largest one
        largest_box = max(boxes, key=lambda box: (box[2] - box[0]) * (box[3] - box[1]))
        return [int(coord) for coord in largest_box[:4]]