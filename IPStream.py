import cv2
import numpy as np
import threading

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