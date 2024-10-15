# pipeline/stages/__init__.py

from .image_cropping_stage import ImageCroppingStage
from .deblurring_stage import DeblurringStage
from .image_binarization_stage import ImageBinarizationStage
from .obj_detection_stage import ObjectDetectionStage
from .person_removing_stage import PersonRemovingStage

__all__ = [
    "ImageCroppingStage",
    "DeblurringStage",
    "ImageBinarizationStage",
    "ObjectDetectionStage",
    "PersonRemovingStage",
]
