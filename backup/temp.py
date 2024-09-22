from ultralytics import YOLOWorld
import cv2
import numpy as np
import supervision as sv
from main1 import binarization
VIDEO = 'IMG_0427.MOV'
video_info = sv.VideoInfo.from_video_path(VIDEO)
frames_generator = sv.get_video_frames_generator(VIDEO)

# Load a model
model = YOLOWorld('yolov8s-world.pt')
classes = ["person", "blackboard"]
model.set_classes(classes)

def find_closest_blackboard(detection, frame_center):
    closest_box = None
    min_distance = float('inf')

    for box, class_id in zip(detection.xyxy, detection.class_id):
        if class_id == 1:  # Class ID for blackboard
            x1, y1, x2, y2 = map(int, box)
            box_center = ((x1 + x2) // 2, (y1 + y2) // 2)
            distance = np.sqrt((box_center[0] - frame_center[0]) ** 2 + (box_center[1] - frame_center[1]) ** 2)
            if distance < min_distance:
                min_distance = distance
                closest_box = [x1, y1, x2, y2, class_id]
    
    return closest_box

first_frame = next(frames_generator)
results = model.predict(first_frame, conf=0.5)
detection = sv.Detections.from_ultralytics(results[0])
frame_center = (first_frame.shape[1] // 2, first_frame.shape[0] // 2)
closest_blackboard = find_closest_blackboard(detection, frame_center)
count=1
padding = 30
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output.mp4', fourcc, 30.0, (abs(closest_blackboard[0]-closest_blackboard[2]), abs(closest_blackboard[1]-closest_blackboard[3]) * 2))
with sv.VideoSink(target_path='target.mp4', video_info=video_info) as sink:
    for frame in frames_generator:
        if count == 1:
            blank_canvas = np.zeros_like(frame)
            count += 1
             
        results = model.predict(frame, conf=0.5)
        detection = sv.Detections.from_ultralytics(results[0])
        bounding_box_annotator = sv.BoundingBoxAnnotator()
        annotated_frame2 = bounding_box_annotator.annotate(
            scene=frame.copy(),
            detections=detection
        )
        
        combined_boxes = []
        if closest_blackboard:
            combined_boxes.append(closest_blackboard)
        
        people_boxes = []
        for i, (box, class_id) in enumerate(zip(detection.xyxy, detection.class_id)):
            if class_id == 0:  # Person class
                people_boxes.append(box)
            elif class_id != 1:  # Exclude blackboard
                x1, y1, x2, y2 = map(int, box)
                combined_boxes.append([x1, y1, x2, y2, class_id])

        annotated_frame = frame.copy()
        for box in combined_boxes:
            x1, y1, x2, y2, class_id = box
            color = (0, 255, 0) if class_id == 0 else (255, 0, 0)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            label = classes[class_id]
            cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Create a mask for people inside the blackboard area
        blackboard_mask = np.zeros_like(frame[:, :, 0])
        if closest_blackboard:
            x1, y1, x2, y2, _ = closest_blackboard
            blackboard_area = frame[y1:y2, x1:x2].copy()
            for box in people_boxes:
                px1, py1, px2, py2 = map(int, box)
                # Ensure the people box is within the blackboard area
                if px1 < x2 and px2 > x1 and py1 < y2 and py2 > y1:
                    bx1 = max(px1 - padding, x1) - x1
                    by1 = max(py1 - padding, y1) - y1
                    bx2 = min(px2 + padding, x2) - x1
                    by2 = min(py2 + padding, y2) - y1
                    blackboard_area[by1:by2, bx1:bx2] = 0  # Remove the person area from the blackboard

            # Create a blank canvas and overlay the modified blackboard area only for non-zero values
            non_zero_indices = np.where(blackboard_area != 0)
            blank_canvas[y1:y2, x1:x2][non_zero_indices] = blackboard_area[non_zero_indices]
            

        mask_frame = np.zeros_like(frame[:, :, 0])
        for box in combined_boxes:
            x1, y1, x2, y2, class_id = box
            if class_id == 0:
                mask_frame[y1:y2, x1:x2] = 255

        blank_canvas_crop=blank_canvas[y1:y2, x1:x2]
        final_canvas=binarization(blank_canvas_crop)
        origin_crop=frame[y1:y2, x1:x2]
        frame_preview=cv2.vconcat([final_canvas,origin_crop])
        out.write(frame_preview)
        cv2.imshow('Annotated Frame', frame_preview)
        if closest_blackboard:
            cv2.imshow('Blank Canvas with Modified Blackboard', blank_canvas)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
out.release()
