import cv2
import numpy as np
import threading
import mediapipe as mp
import speech_recognition as sr
import time
import difflib


GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)

# wymiary kamer
w,h = 960,720

local_idx = 0
ip_url = "http://192.168.33.8:8080/video"  # ip kamerki telefon

exercises = ["biceps","barki"]
state = ["start","stop"]