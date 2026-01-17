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
from db_manager import DBManager

CAM_W = 640  # Szerokość jednej kamerki
CAM_H = 480  # Wysokość kamerki
DASH_H = 250  # Wysokość panelu dolnego

FPS = 45

WIN_W = CAM_W * 2  # Całkowita szerokość (1200)
WIN_H = CAM_H + DASH_H  # Całkowita wysokość (700)

local_idx = 0
# ip_url = "http://192.168.33.10:8080/video"
# ip_url = "http://192.168.254.101:4747/video"
ip_url = "http://192.168.101.99:4747/video"


#ip_url = "http://192.168.0.102:4747/video"

COLOR_BG = (15, 15, 25)
COLOR_PANEL = (30, 35, 45)
COLOR_TEXT = (240, 240, 240)
COLOR_ACCENT = (0, 255, 200)
COLOR_GREEN = (0, 230, 64)
COLOR_RED = (255, 60, 80)

exercises = ["biceps", "barki"]
state = ["start", "stop"]

# kolory ui
COLOR_INACTIVE = (60, 60, 70)
COLOR_ACTIVE = (0, 200, 255)
COLOR_BUTTON_TEXT = (255, 255, 255)
COLOR_BUTTON_DEF = (50, 50, 60)
COLOR_BUTTON_HOVER = (70, 70, 90)

# konfiguracja ui
CENTER_X = WIN_W // 2
CENTER_Y = WIN_H // 2
