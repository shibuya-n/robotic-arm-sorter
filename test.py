from ultralytics import YOLO

model = YOLO("yolo26n.pt")
model(0, show = True)