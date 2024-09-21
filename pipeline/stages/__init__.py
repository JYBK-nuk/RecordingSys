# pipeline/stages/__init__.py

from .person_detection_stage import PersonDetectionStage
from .image_cropping_stage import ImageCroppingStage
from .deblurring_stage import DeblurringStage
from .image_binarization_stage import ImageBinarizationStage

__all__ = [
    "PersonDetectionStage",
    "ImageCroppingStage",
    "DeblurringStage",
    "ImageBinarizationStage",
]
