import cv2
import numpy as np
import pygame
import threading
import mediapipe as mp
import speech_recognition as sr
import time
import difflib
import os
import json
import queue
from vosk import Model, KaldiRecognizer
import pyaudio

CAM_W = 640  # Szerokość jednej kamerki
CAM_H = 480  # Wysokość kamerki
DASH_H = 250  # Wysokość panelu dolnego

FPS = 45

WIN_W = CAM_W * 2  # Całkowita szerokość (1200)
WIN_H = CAM_H + DASH_H  # Całkowita wysokość (700)

local_idx = 0
# ip_url = "http://192.168.33.10:8080/video"
# ip_url = "http://192.168.254.101:8080/video"
ip_url = "http://192.168.0.102:4747/video"

COLOR_BG = (20, 20, 25)
COLOR_PANEL = (40, 40, 45)
COLOR_TEXT = (220, 220, 220)
COLOR_ACCENT = (0, 200, 255)
COLOR_GREEN = (50, 205, 50)
COLOR_RED = (220, 60, 60)

exercises = ["biceps", "barki"]
state = ["start", "stop"]
