from utils import *
import cv2
import numpy as np
import mediapipe as mp


# Konfiguracja
local_idx = 0
ip_url = "http://192.168.254.101:8080/video"

mp_pose = mp.solutions.pose
 
pose_local = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
pose_ip = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap_local = cv2.VideoCapture(local_idx)
cam_ip = IPStream(ip_url) # nie laguje, prawie zerowy delay



while True:
    ret1, frame1 = cap_local.read()
    ret2, frame2 = cam_ip.read()

    if not ret1: frame1 = np.zeros((480, 640, 3), np.uint8)
    
    # Skalowanie
    frame1 = cv2.resize(frame1, (640, 480))
    frame2 = cv2.resize(frame2, (640, 480))

    frame1, results1 = detect_and_draw(frame1, pose_local)
    frame2, results2 = detect_and_draw(frame2, pose_ip)


    # Compute 3D angles from stereo views (assumes cameras at +/-45deg)
    angles = compute_angles_3d(results1, results2, focal=1.0, baseline=0.6)
    draw_angles_on_frames(frame1, frame2, results1, results2, angles)

    cv2.imshow('Dual Camera', np.hstack((frame1, frame2)))

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap_local.release()
cam_ip.release()
cv2.destroyAllWindows()