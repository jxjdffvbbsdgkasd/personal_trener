import pygame
import cv2
import numpy as np
import mediapipe as mp
import difflib
from settings import *
from classes import *
from utils import *

pygame.init()
init_fonts()
screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("Cyber Trener - Dual Cam System")
clock = pygame.time.Clock()

mp_pose = mp.solutions.pose
pose_local = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
pose_ip = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap_local = cv2.VideoCapture(local_idx)
cam_ip = IPStream(ip_url)

print("Wybierz ćwiczenie (biceps albo barki)")
# exercise_type = select_exercise_via_voice() # Docelowo to narazie na sztywno jest biceps
exercise_type = "biceps"
print(f"-> Wybrano: {exercise_type}")

voice_control = VoiceThread()
trainer = Trainer()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q: running = False
            if event.key == pygame.K_r: trainer.reset()  # Reset klawiszem R

    ret1, frame1 = cap_local.read()
    ret2, frame2 = cam_ip.read()

    # Obsługa błędów kamer (pusta klatka)
    if not ret1: frame1 = np.zeros((CAM_H, CAM_W, 3), np.uint8)
    if not ret2: frame2 = np.zeros((CAM_H, CAM_W, 3), np.uint8)

    frame1 = cv2.resize(frame1, (CAM_W, CAM_H))
    frame2 = cv2.resize(frame2, (CAM_W, CAM_H))

    frame1, results1 = detect_and_draw(frame1, pose_local)
    frame2, results2 = detect_and_draw(frame2, pose_ip)

    angles = compute_angles_3d(results1, results2, focal=1.0, baseline=0.6)

    if voice_control.started:
        if exercise_type == "biceps":
            trainer.process_biceps(angles)
        # Tutaj elif do barkow

    screen.fill(COLOR_BG)

    pg_frame1 = cv2_to_pygame(frame1, CAM_W, CAM_H)
    pg_frame2 = cv2_to_pygame(frame2, CAM_W, CAM_H)

    screen.blit(pg_frame1, (0, 0))
    screen.blit(pg_frame2, (CAM_W, 0))

    draw_dashboard(screen, exercise_type, voice_control.started, trainer, angles)

    pygame.display.flip()
    clock.tick(30)

voice_control.stop()
cap_local.release()
cam_ip.release()
pygame.quit()