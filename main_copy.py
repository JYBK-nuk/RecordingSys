from pipeline.processing_pipeline import ProcessingPipeline
from pipeline.stages.deblurring_stage import DeblurringStage
from pipeline.stages.image_cropping_stage import ImageCroppingStage
from pipeline.stages.person_detection_stage import PersonDetectionStage
import time
import cv2

cap = cv2.VideoCapture(0)
processing_pipeline = ProcessingPipeline(source=cap)
pipelines = [
    PersonDetectionStage(),
    ImageCroppingStage(),
    DeblurringStage(),
]
for stage in pipelines:
    processing_pipeline.add_stage(stage.__class__.__name__, stage)
while cap.isOpened():
    ret, frame = cap.read()

    timestamp = time.time()

    # Process the frame using the pipeline
    frame, data, timestamp = processing_pipeline.process(frame, timestamp)
    cv2.imshow("test", frame)
    cv2.waitKey(0)
