import cv2, torch
from ultralytics import YOLO

print(torch.cuda.is_available())
model = YOLO("trained_26l_v1.pt")
model.to('cuda')

camera = cv2.VideoCapture(0)

while camera.isOpened():
    ret, frame = camera.read()
    if not ret:
        break
    
    detections = model(frame)[0]
    print(detections)
    
    annotated_frame = detections.plot()
    cv2.imshow('pee', annotated_frame)
    
    if cv2.waitKey(1) & 0xFF == ord('1'):
        break