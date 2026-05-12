import cv2
from ultralytics import YOLO
import numpy as np

yolo_model = YOLO("yolov8n.pt") 
class_names = yolo_model.names

print("1 - Веб-камера\n2 - Видеофайл")
choice = input("Выбор: ")
source = 0 if choice == '1' else input("Путь к файлу: ").replace('"', '')

cap = cv2.VideoCapture(source)

skip_frames = 2  
frame_count = 0
prev_centers = {} 

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    frame_count += 1
    if frame_count % skip_frames != 0:
        continue 


    results = yolo_model.track(frame, persist=True, verbose=False, conf=0.3, imgsz=480)
    
    if results[0].boxes and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        ids = results[0].boxes.id.cpu().numpy()
        clss = results[0].boxes.cls.cpu().numpy()
        
        for box, track_id, cls_id in zip(boxes, ids, clss):
            x1, y1, x2, y2 = map(int, box)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            obj_name = class_names[int(cls_id)].lower()

            movement = 0
            if track_id in prev_centers:
                px, py = prev_centers[track_id]
                movement = np.sqrt((cx - px)**2 + (cy - py)**2)
            
            prev_centers[track_id] = (cx, cy)

            status = ""
            if obj_name == "person":
                status = "Walking" if movement > 2.0 else "Standing"
                if (x2 - x1) > (y2 - y1) * 1.1: status = "Lying"
            
            elif obj_name in ["car", "bus", "truck", "motorcycle"]:
                status = "Driving" if movement > 3.0 else "Parked"

            color = (255, 150, 0) if "ing" in status or "ing" in status else (100, 100, 100)
            if status == "Lying": color = (0, 0, 255)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{obj_name.capitalize()} #{int(track_id)} {status}"
            cv2.putText(frame, label, (x1, y1 - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    cv2.imshow("Fast AI Monitor", frame)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()