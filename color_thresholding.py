import cv2, torch
from ultralytics import YOLO

print(torch.cuda.is_available())
model = YOLO("yolo26n.pt")
model.to('cuda')

camera = cv2.VideoCapture(0)


while camera.isOpened():
    ret, frame = camera.read()
    if not ret:
        break
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    #detects green
    # lower = (35, 50, 50) 
    # upper = (85, 255, 255)
    
    #detect red
    lower = (0, 120, 70)
    upper = (10, 255, 255)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    result = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow('mask result', result)  # you'll also want to actually display it

    if cv2.waitKey(1) & 0xFF == ord('1'):
        break

camera.release()
cv2.destroyAllWindows()