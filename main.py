import IPStream
import cv2
import numpy as np


# Konfiguracja
local_idx = 0
ip_url = "http://192.168.254.101:8080/video"


cap_local = cv2.VideoCapture(local_idx)
cam_ip = IPStream(ip_url) # nie laguje, prawie zerowy delay

while True:
    ret1, frame1 = cap_local.read()
    ret2, frame2 = cam_ip.read()

    if not ret1: frame1 = np.zeros((480, 640, 3), np.uint8)
    
    # Skalowanie
    frame1 = cv2.resize(frame1, (640, 480))
    frame2 = cv2.resize(frame2, (640, 480))

    cv2.imshow('Dual Camera', np.hstack((frame1, frame2)))

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap_local.release()
cam_ip.release()
cv2.destroyAllWindows()