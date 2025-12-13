import cv2
import numpy as np
import threading
import mediapipe as mp

class IPStream:
    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        self.frame = np.zeros((480, 640, 3), np.uint8)
        self.running = True
        threading.Thread(target=self.update, daemon=True).start()
    def update(self):
        while self.running:
            ret, img = self.cap.read()
            if ret: self.frame = img
    def read(self):
        return True, self.frame
    def release(self):
        self.running = False
        self.cap.release()

def detect_and_draw(frame, model):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_rgb.flags.writeable = False
    
    results = model.process(frame_rgb)
    
    if results.pose_landmarks:
        mp.solutions.drawing_utils.draw_landmarks(
            frame, 
            results.pose_landmarks, 
            mp.solutions.pose.POSE_CONNECTIONS
        )
    
    return frame, results