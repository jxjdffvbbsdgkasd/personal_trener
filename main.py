import pygame
import cv2
import numpy as np
import mediapipe as mp
import difflib
from settings import *
from classes import *
from utils import *

# KONFIGURACJA UI
UI_WIDTH = 400
SCREEN_WIDTH = (w * 2) + UI_WIDTH
SCREEN_HEIGHT = h

# Kolory UI
BG_COLOR = (30, 30, 30)
PANEL_COLOR = (50, 50, 55)
TEXT_WHITE = (240, 240, 240)
ACCENT_CYAN = (0, 255, 255)
ACCENT_GREEN = (50, 205, 50)
ACCENT_RED = (255, 69, 0)

# INICJALIZACJA MEDIAPIPE
mp_pose = mp.solutions.pose
pose_local = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
pose_ip = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# INICJALIZACJA PYGAME
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cyber Trener - System Analizy Ruchu")
clock = pygame.time.Clock()

# Fonty
font_huge = pygame.font.SysFont("arial", 80, bold=True)
font_large = pygame.font.SysFont("arial", 40, bold=True)
font_med = pygame.font.SysFont("arial", 28)
font_small = pygame.font.SysFont("consolas", 20)


# FUNKCJE UI

def draw_text_centered(surface, text, font, color, center_x, center_y):
    render = font.render(text, True, color)
    rect = render.get_rect(center=(center_x, center_y))
    surface.blit(render, rect)

# Konwersja obrazu opencv na pygame surface
def cv2_to_pygame(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)
    frame = pygame.surfarray.make_surface(frame)
    return frame

# Rysuje panel boczny ze statystykami
def draw_dashboard(surface, exercise_name, is_running, reps, feedback_list, current_angle):
    # Tlo panelu
    panel_rect = pygame.Rect(w * 2, 0, UI_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(surface, BG_COLOR, panel_rect)
    pygame.draw.line(surface, ACCENT_CYAN, (w * 2, 0), (w * 2, SCREEN_HEIGHT), 3)

    center_x = (w * 2) + (UI_WIDTH // 2)

    pygame.draw.rect(surface, PANEL_COLOR, (w * 2 + 10, 20, UI_WIDTH - 20, 80), border_radius=10)
    draw_text_centered(surface, "ĆWICZENIE:", font_small, (180, 180, 180), center_x, 40)
    draw_text_centered(surface, exercise_name.upper(), font_large, ACCENT_CYAN, center_x, 75)

    status_text = "SERIA TRWA" if is_running else "OCZEKIWANIE"
    status_color = ACCENT_GREEN if is_running else ACCENT_RED

    pygame.draw.rect(surface, status_color, (w * 2 + 10, 120, UI_WIDTH - 20, 60), border_radius=10)
    draw_text_centered(surface, status_text, font_large, (0, 0, 0), center_x, 150)

    y_reps = 280
    draw_text_centered(surface, "POWTÓRZENIA", font_med, TEXT_WHITE, center_x, y_reps - 50)
    pygame.draw.circle(surface, PANEL_COLOR, (center_x, y_reps + 20), 70)
    pygame.draw.circle(surface, ACCENT_CYAN, (center_x, y_reps + 20), 70, 3)
    draw_text_centered(surface, str(reps), font_huge, TEXT_WHITE, center_x, y_reps + 22)

    y_angle = 450
    pygame.draw.rect(surface, (40, 40, 40), (w * 2 + 20, y_angle, UI_WIDTH - 40, 40))
    angle_val = f"{int(current_angle)}°" if current_angle is not None else "--"
    draw_text_centered(surface, f"Kąt (łokieć): {angle_val}", font_med, (200, 200, 200), center_x, y_angle + 20)

    y_feed = 530
    draw_text_centered(surface, "KOREKTA TRENERA:", font_med, ACCENT_RED, center_x, y_feed)
    pygame.draw.rect(surface, (20, 20, 20), (w * 2 + 20, y_feed + 25, UI_WIDTH - 40, 150), border_radius=5)

    current_y = y_feed + 50
    if not feedback_list:
        draw_text_centered(surface, "Technika OK", font_small, ACCENT_GREEN, center_x, current_y + 10)
    else:
        # Tylko unikalne komunikaty
        unique_feedback = list(set(feedback_list))
        for msg in unique_feedback[-3:]:
            draw_text_centered(surface, f"• {msg}", font_small, TEXT_WHITE, center_x, current_y)
            current_y += 30

cap_local = cv2.VideoCapture(local_idx)
cam_ip = IPStream(ip_url)

# Wybór ćwiczenia (Głosowy) - Skrócony na potrzeby testu UI, ale działający
print("Powiedz 'biceps' lub 'barki' do mikrofonu...")
exercise_type = None

# Petla wyboru cwiczenia
# Zeby napewno dzialalo ustawiam tu na sztywno ale docelowo bedzie select_exercise_via_voice()
try:
    # exercise_type = select_exercise_via_voice()
    if exercise_type is None:
        exercise_type = "biceps"
except:
    exercise_type = "biceps"

print(f"Wybrano tryb: {exercise_type}")

voice_control = VoiceThread()

# Zmienne do cwiczen
reps_counter = 0
stage = "down"  # down / up
feedback_log = []
last_valid_angle = 0

running = True
while running:
    # Obsługa zdarzen pygame
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
            # Opcjonalny reset licznika
            if event.key == pygame.K_r:
                reps_counter = 0

    ret1, frame1 = cap_local.read()
    ret2, frame2 = cam_ip.read()

    if not ret1: frame1 = np.zeros((h, w, 3), np.uint8)
    if not ret2: frame2 = np.zeros((h, w, 3), np.uint8)

    # Skalowanie
    frame1 = cv2.resize(frame1, (w, h))
    frame2 = cv2.resize(frame2, (w, h))

    frame1, results1 = detect_and_draw(frame1, pose_local)
    frame2, results2 = detect_and_draw(frame2, pose_ip)

    # Obliczenia 3D
    angles = compute_angles_3d(results1, results2, focal=1.0, baseline=0.6)
    draw_angles_on_frames(frame1, frame2, results1, results2, angles)

    # Logika Trenera
    curr_angle = angles.get("right_elbow")  # Domyslnie prawy
    if curr_angle is None:
        curr_angle = angles.get("left_elbow")

    swing_angle = angles.get("left_shoulder_swing")

    feedback_log = []

    if voice_control.started:
        if curr_angle is not None:
            last_valid_angle = curr_angle

            # Logika liczenia dla bicepsow
            if exercise_type == "biceps":
                if curr_angle > 160:
                    stage = "down"
                if curr_angle < 40 and stage == "down":
                    stage = "up"
                    reps_counter += 1
                    print("REP!")

            # Detekcja bledow (odchylanie lokcia)
            if swing_angle is not None and swing_angle > 25:
                feedback_log.append("Łokieć przy ciele!")

            # Tu logika dla barkow

    # Rysowanie w Pygame
    screen.fill(BG_COLOR)

    # Konwersja i kamery
    pg_frame1 = cv2_to_pygame(frame1)
    pg_frame2 = cv2_to_pygame(frame2)

    screen.blit(pg_frame1, (0, 0))
    screen.blit(pg_frame2, (w, 0))

    # Rysowanie Panelu Bocznego
    draw_dashboard(
        surface=screen,
        exercise_name=exercise_type,
        is_running=voice_control.started,
        reps=reps_counter,
        feedback_list=feedback_log,
        current_angle=last_valid_angle
    )

    pygame.display.flip()

    clock.tick(30)


voice_control.stop()
cap_local.release()
cam_ip.release()
pygame.quit()