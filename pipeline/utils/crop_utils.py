from ultralytics import YOLOWorld
import cv2
import numpy as np
import supervision as sv


# 人物偵測拆走
# ----------------------------------------------------------------影像處理的部分 模糊....
def adjust_contrast(image: np.ndarray, factor: float) -> np.ndarray:
    mean = np.mean(image)
    return np.clip((1 - factor) * mean + factor * image, 0, 255).astype(np.uint8)


def process_image(image: np.ndarray) -> np.ndarray:
    from skimage import img_as_ubyte
    from skimage.filters import threshold_sauvola

    # 调整对比度
    low_contrast_image = adjust_contrast(image, factor=1.7)

    # Sauvola 二值化处理
    window_size = 3  # Sauvola 方法的窗口大小，需根据图像大小调整
    sauvola_thresh = threshold_sauvola(low_contrast_image, window_size=window_size)
    binary_image = low_contrast_image > sauvola_thresh
    binary_image = img_as_ubyte(binary_image)  # 将布尔图像转换为 uint8 类型

    # 負片效果
    binary_image = 255 - binary_image
    return binary_image


def draw_contours(image: np.ndarray, contours: list) -> np.ndarray:
    output = image.copy()
    cv2.drawContours(output, contours, -1, (0, 255, 0), 2)
    return output


def binarization(image: np.ndarray) -> np.ndarray:
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    source_image = image.copy()
    image = process_image(image)
    # 使用形態學操作來加強文字區域
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask = cv2.dilate(image.copy(), kernel, iterations=3)

    # BINARIZATION
    _, binary = cv2.threshold(source_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # and operation mask and binary image
    image = cv2.bitwise_and(binary, mask)
    # convert to rgb color
    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image


# ----------------------------------------------------------------切黑板
# 模擬過程
def all_process(self, frame, model):

    blank_canvas = np.zeros_like(frame)

    closest_blackboard = find_center_axis(self, frame, model)
    x1, y1, x2, y2, _ = closest_blackboard
    self.combined_boxes.append(closest_blackboard)

    detections = get_detections(self, frame, model)  # 取得偵測物件(人/黑板)
    annotate_people(self, detections)  # 偵測到的人加入people-list列表

    blank_canvas = process_blackboard_area(  # 處理黑板區域中人的部分
        self, frame, closest_blackboard, blank_canvas
    )
    blank_canvas_crop = blank_canvas[y1:y2, x1:x2]
    final_canvas = binarization(blank_canvas_crop)
    origin_crop = frame[y1:y2, x1:x2]
    frame_preview = cv2.vconcat([final_canvas, origin_crop])
    pass


# step2
def find_closest_blackboard(detection, frame_center):
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


# step1
def find_center_axis(self, frame, model):
    first_frame = frame
    results = model.predict(first_frame, conf=0.5)
    detection = sv.Detections.from_ultralytics(results[0])
    frame_center = (first_frame.shape[1] // 2, first_frame.shape[0] // 2)
    closest_blackboard = find_closest_blackboard(detection, frame_center)
    return closest_blackboard


# step3  移動到person_detection_stage.py
def get_detections(self, frame, model):
    results = model.predict(frame, conf=0.5)
    detection = sv.Detections.from_ultralytics(results[0])
    return detection


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
def process_blackboard_area(self, frame, closest_blackboard, blank_canvas, padding=30):
    if closest_blackboard:
        x1, y1, x2, y2, _ = closest_blackboard
        blackboard_area = frame[y1:y2, x1:x2].copy()
        for box in self.people_boxes:
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
        blank_canvas[y1:y2, x1:x2][non_zero_indices] = blackboard_area[non_zero_indices]

    return blank_canvas
