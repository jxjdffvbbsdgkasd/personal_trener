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
ip_url = "http://192.168.254.101:4747/video"
#ip_url = "http://192.168.0.102:4747/video"
#ip_url = "http://192.168.1.115:4747/video"

COLOR_BG = (20, 20, 25)
COLOR_PANEL = (40, 40, 45)
COLOR_TEXT = (220, 220, 220)
COLOR_ACCENT = (0, 200, 255)
COLOR_GREEN = (50, 205, 50)
COLOR_RED = (220, 60, 60)

exercises = ["biceps", "barki"]
state = ["start", "stop"]

# kolory ui
COLOR_INACTIVE = pygame.Color("lightskyblue3")
COLOR_ACTIVE = pygame.Color("dodgerblue2")
COLOR_BUTTON_TEXT = (255, 255, 255)
COLOR_BUTTON_DEF = (70, 70, 80)
COLOR_BUTTON_HOVER = (100, 100, 110)

# konfiguracja ui
CENTER_X = WIN_W // 2
CENTER_Y = WIN_H // 2
