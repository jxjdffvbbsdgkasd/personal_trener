from settings import *
import numpy as np
import pygame
import notification_global as ng

# --- INICJALIZACJA CZCIONEK ---
font_big = None
font_med = None
font_small = None


def init_fonts():
    global font_big, font_med, font_small
    font_big = pygame.font.SysFont("arial", 60, bold=True)
    font_med = pygame.font.SysFont("arial", 30, bold=True)
    font_small = pygame.font.SysFont("consolas", 20)
    return font_big, font_med, font_small


def cv2_to_pygame(frame, width, height):
    frame = cv2.resize(frame, (width, height))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    frame = np.transpose(frame, (1, 0, 2))
    return pygame.surfarray.make_surface(frame)


def draw_text_centered(surface, text, font, color, center_x, center_y):
    if font is None:
        return
    render = font.render(text, True, color)
    rect = render.get_rect(center=(center_x, center_y))
    surface.blit(render, rect)


def draw_dashboard(
        screen, exercise_name, is_running, trainer, angles, workout_manager=None
):
    y_start = CAM_H

    pygame.draw.rect(screen, COLOR_BG, (0, y_start, WIN_W, DASH_H))
    pygame.draw.line(screen, (80, 80, 80), (0, y_start), (WIN_W, y_start), 2)

    center_x = WIN_W // 2
    margin = 30
    box_width = 350
    box_height = DASH_H - 40
    box_y = y_start + 20

    left_box_x = margin
    left_center_x = left_box_x + (box_width // 2)

    right_box_x = WIN_W - box_width - margin
    right_center_x = right_box_x + (box_width // 2)

    draw_text_centered(
        screen,
        f"Ćwiczenie: {exercise_name.upper()}",
        font_med,
        COLOR_ACCENT,
        center_x,
        y_start + 30,
    )

    # WYSWIETLANIE SERII
    if workout_manager and exercise_name in ["biceps", "barki"]:
        current_set = workout_manager.get_display_set_number(exercise_name)
        target_set = workout_manager.get_target_set(exercise_name)

        # kolor tekstu w trakcie bialy, po zakonczeniu zielony
        set_color = (200, 200, 200)
        set_text = f"Seria: {current_set} / {target_set}"

        # informacja po skonczeniu wszystkich
        if workout_manager.is_workout_complete(exercise_name):
            set_text += " (UKOŃCZONO)"
            set_color = COLOR_GREEN

        draw_text_centered(
            screen, set_text, font_small, set_color, center_x, y_start + 55
        )

    status_msg = "Seria trwa" if is_running else "Oczekiwanie"
    status_col = COLOR_GREEN if is_running else COLOR_RED

    # Ramka statusu
    pygame.draw.rect(
        screen, status_col, (center_x - 150, y_start + 75, 300, 40), border_radius=10
    )
    draw_text_centered(
        screen, status_msg, font_small, (0, 0, 0), center_x, y_start + 95
    )

    if angles is not None:
        # lewa
        pygame.draw.rect(
            screen,
            COLOR_PANEL,
            (left_box_x, box_y, box_width, box_height),
            border_radius=15,
        )
        draw_text_centered(
            screen, "Lewa ręka", font_med, COLOR_TEXT, left_center_x, y_start + 50
        )
        draw_text_centered(
            screen,
            str(trainer.reps_left),
            font_big,
            COLOR_ACCENT,
            left_center_x,
            y_start + 110,
        )
        draw_text_centered(
            screen, "powtórzeń", font_small, (150, 150, 150), left_center_x, y_start + 150
        )
        ang_l = angles.get("left_elbow")
        val_l = f"{int(ang_l)}°" if ang_l else "--"
        draw_text_centered(
            screen, f"Kąt: {val_l}", font_small, COLOR_TEXT, left_center_x, y_start + 190
        )

        # prawa
        pygame.draw.rect(
            screen,
            COLOR_PANEL,
            (right_box_x, box_y, box_width, box_height),
            border_radius=15,
        )
        draw_text_centered(
            screen, "Prawa Ręka", font_med, COLOR_TEXT, right_center_x, y_start + 50
        )
        draw_text_centered(
            screen,
            str(trainer.reps_right),
            font_big,
            COLOR_ACCENT,
            right_center_x,
            y_start + 110,
        )
        draw_text_centered(
            screen, "powtórzeń", font_small, (150, 150, 150), right_center_x, y_start + 150
        )
        ang_r = angles.get("right_elbow")
        val_r = f"{int(ang_r)}°" if ang_r else "--"
        draw_text_centered(
            screen, f"Kąt: {val_r}", font_small, COLOR_TEXT, right_center_x, y_start + 190
        )

    # Box na Feedback
    if trainer.feedback:
        for i, msg in enumerate(trainer.feedback[:2]):
            txt_surf = font_med.render(msg.upper(), True, COLOR_RED)

            fixed_w = 650
            fixed_h = 48

            box_rect = pygame.Rect(0, 0, fixed_w, fixed_h)
            box_rect.center = (center_x, y_start + 155 + (i * 60))

            pygame.draw.rect(screen, (0, 0, 0), box_rect, border_radius=8)
            pygame.draw.rect(screen, COLOR_RED, box_rect, width=3, border_radius=8)

            txt_rect = txt_surf.get_rect(center=box_rect.center)
            screen.blit(txt_surf, txt_rect)
    else:
        draw_text_centered(
            screen,
            "Technika Prawidłowa",
            font_small,
            (100, 100, 100),
            center_x,
            y_start + 160,
        )


# rysowanie kolorowego szkieletu (dobrze - zielony, zle - czerwony)
def detect_and_draw(frame, model, draw_color=(0, 255, 0)):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_rgb.flags.writeable = False
    results = model.process(frame_rgb)

    if results.pose_landmarks:
        # Definiujemy styl rysowania (kropki i linie w tym samym kolorze)
        # color=(B, G, R), thickness=grubość, circle_radius=promień kropki
        custom_style = mp.solutions.drawing_utils.DrawingSpec(
            color=draw_color, thickness=2, circle_radius=2
        )

        # Rysujemy
        mp.solutions.drawing_utils.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp.solutions.pose.POSE_CONNECTIONS,
            landmark_drawing_spec=custom_style,  # Styl kropek
            connection_drawing_spec=custom_style,  # Styl linii
        )

    return frame, results


def _landmark_dict(results):
    """Konwertuje wyniki z MediaPipe na słownik współrzędnych (x, y)."""
    if not results or not results.pose_landmarks:
        return {}
    lm = results.pose_landmarks.landmark
    return {i: (lm[i].x, lm[i].y) for i in range(len(lm))}

    # matematyka


def _triangulate_point(x1, y1, x2, y2, focal=1.0, baseline=0.6):
    """
    Oblicza pozycję punktu w 3D (gdzie on jest w przestrzeni).
    Bierze obraz z lewej i prawej kamery, żeby ustalić głębię.
    """

    # Przesuwamy punkt środka (żeby 0,0 było na środku obrazu, a nie w rogu)
    x_im1 = x1 - 0.5
    y_im1 = 0.5 - y1
    x_im2 = x2 - 0.5
    y_im2 = 0.5 - y2

    # Tworzymy wektory (linie patrzenia) dla obu kamer
    d1 = np.array([x_im1, y_im1, focal], dtype=float)
    d2 = np.array([x_im2, y_im2, focal], dtype=float)

    # Normalizacja (wyrównanie długości wektorów)
    d1 = d1 / np.linalg.norm(d1)
    d2 = d2 / np.linalg.norm(d2)

    # Ustawienie pozycji kamer (lewa i prawa są rozsunięte o 'baseline')
    o1 = np.array([-baseline / 2.0, 0.0, 0.0])
    o2 = np.array([baseline / 2.0, 0.0, 0.0])

    # Obracamy kamery o 45 stopni do środka (zbieżnie), żeby widziały ćwiczącego
    th = np.deg2rad(45.0)

    # Macierz obrotu dla lewej kamery
    R_left = np.array([
        [np.cos(th), 0.0, np.sin(th)],
        [0.0, 1.0, 0.0],
        [-np.sin(th), 0.0, np.cos(th)]
    ])

    # cierz obrotu dla prawej kamery
    R_right = np.array([
        [np.cos(-th), 0.0, np.sin(-th)],
        [0.0, 1.0, 0.0],
        [-np.sin(-th), 0.0, np.cos(-th)],
    ])

    v1 = R_left.dot(d1)
    v2 = R_right.dot(d2)

    # Matematyka szukająca przecięcia dwóch linii wzroku (najbliższy punkt)
    # To skomplikowane równanie, które wylicza punkt "S" i "T" na liniach
    a = np.dot(v1, v1)
    b = np.dot(v1, v2)
    c = np.dot(v2, v2)
    w0 = o1 - o2
    e = np.dot(v1, w0)
    f = np.dot(v2, w0)

    denom = a * c - b * b

    if abs(denom) < 1e-6:
        s = 0.0
        t = 0.0
    else:
        s = (b * f - c * e) / denom
        t = (a * f - b * e) / denom

    p1 = o1 + s * v1
    p2 = o2 + t * v2
    return (p1 + p2) / 2.0


def reconstruct_3d(results_left, results_right, focal=1.0, baseline=0.6):
    """
        Odtwarza punkty 3D dla punktów widocznych w obu kamerach.
        Zwraca słownik: index -> (x, y, z).
    """
    left = _landmark_dict(results_left)
    right = _landmark_dict(results_right)
    common = set(left.keys()) & set(right.keys())
    pts3d = {}
    for i in common:
        x1, y1 = left[i]
        x2, y2 = right[i]
        pts3d[i] = _triangulate_point(x1, y1, x2, y2, focal=focal, baseline=baseline)
    return pts3d


def angle_between_3d(a, b, c):
    """
        Liczy kąt w stopniach między trzema punktami.
        Np. Kąt w łokciu to kąt między: Ramieniem (A), Łokciem (B) i Nadgarstkiem (C).
    """
    ba = a - b
    bc = c - b

    na = np.linalg.norm(ba)
    nb = np.linalg.norm(bc)

    if na < 1e-6 or nb < 1e-6:
        return None

    cosang = np.dot(ba, bc) / (na * nb)
    cosang = np.clip(cosang, -1.0, 1.0)

    return float(np.degrees(np.arccos(cosang)))


def compute_angles_3d_biceps(results_left, results_right, focal=1.0, baseline=0.6):
    pts3d = reconstruct_3d(results_left, results_right, focal, baseline)
    angles = {}
    pose = mp.solutions.pose.PoseLandmark

    def get_ang(p1, p2, p3):
        if p1.value in pts3d and p2.value in pts3d and p3.value in pts3d:
            return angle_between_3d(pts3d[p1.value], pts3d[p2.value], pts3d[p3.value])
        return None

    # --- PODSTAWOWE KĄTY ---
    # Zgięcie w łokciu (Fleksja)
    angles["left_elbow"] = get_ang(pose.LEFT_SHOULDER, pose.LEFT_ELBOW, pose.LEFT_WRIST)
    angles["right_elbow"] = get_ang(
        pose.RIGHT_SHOULDER, pose.RIGHT_ELBOW, pose.RIGHT_WRIST
    )

    # Sprawdzenie techniki: czy łokieć jest stabilny (nie ucieka przód/tył).
    angles["left_shoulder_swing"] = get_ang(
        pose.LEFT_HIP, pose.LEFT_SHOULDER, pose.LEFT_ELBOW
    )
    angles["right_shoulder_swing"] = get_ang(
        pose.RIGHT_HIP, pose.RIGHT_SHOULDER, pose.RIGHT_ELBOW
    )

    # Detekcja błędu: Sprawdzenie, czy użytkownik nie odwodzi rąk na boki (tzw. flary)
    # Sprawdzamy kąt: PrawyBark -> LewyBark -> LewyNadgarstek.
    # Jeśli trzymasz ręce wąsko, kąt ~90 stopni.
    # Jeśli machasz na boki ("ręce na zewnątrz"), kąt rośnie > 110.

    angles["left_flare"] = get_ang(
        pose.RIGHT_SHOULDER, pose.LEFT_SHOULDER, pose.LEFT_WRIST
    )
    angles["right_flare"] = get_ang(
        pose.LEFT_SHOULDER, pose.RIGHT_SHOULDER, pose.RIGHT_WRIST
    )

    return angles


def compute_angles_3d_shoulders(results_left, results_right, focal=1.0, baseline=0.6):
    """
    Logika dla wyciskania na barki.
    Sprawdza dwa kluczowe kąty: czy ręka jest wysoko i czy jest wyprostowana.
    """
    pts3d = reconstruct_3d(results_left, results_right, focal=focal, baseline=baseline)
    angles = {}

    Pose = mp.solutions.pose.PoseLandmark

    def get_ang(p1, p2, p3):
        if p1.value in pts3d and p2.value in pts3d and p3.value in pts3d:
            return angle_between_3d(pts3d[p1.value], pts3d[p2.value], pts3d[p3.value])
        return None

    # 1. CZY RĘKA JEST W GÓRZE? (Kąt: Biodro -> Bark -> Łokieć)
    # Jak jest około 170-180 stopni -> ręka pionowo w górze.
    # Jak jest 90 stopni -> ręka w poziomie.
    angles["left_shoulder_lift"] = get_ang(
        Pose.LEFT_HIP, Pose.LEFT_SHOULDER, Pose.LEFT_ELBOW
    )
    angles["right_shoulder_lift"] = get_ang(
        Pose.RIGHT_HIP, Pose.RIGHT_SHOULDER, Pose.RIGHT_ELBOW
    )

    # 2. CZY ŁOKIEĆ JEST WYPROSTOWANY? (Bark -> Łokieć -> Nadgarstek)
    # Potrzebujemy pełnego wyprostu, czyli blisko 180 stopni.
    angles["left_elbow"] = get_ang(Pose.LEFT_SHOULDER, Pose.LEFT_ELBOW, Pose.LEFT_WRIST)
    angles["right_elbow"] = get_ang(
        Pose.RIGHT_SHOULDER, Pose.RIGHT_ELBOW, Pose.RIGHT_WRIST
    )

    return angles

    #handler dla komend glosowych
def process_command(voice_control, exercise_type, workout_manager, trainer, speaker):
    cmd = voice_control.last_command

    if not cmd:
        return exercise_type

    # obsluga start stop
    if cmd == "start":
        if exercise_type == "none":
            ng.notif.add_notification("Najpierw wybierz ćwiczenie!",duration_seconds=2.0,)
            if speaker:
                speaker.say("Najpierw wybierz ćwiczenie!")
        else:
            voice_control.started = True
            if speaker:
                speaker.say("Rozpoczynamy serię!")

    elif cmd == "stop":
        voice_control.started = False

    # zmiana cwiczenia obsluga
    elif cmd in exercises and not voice_control.started:
        # zakladana jest blokada na reset i zmiane cwiczenia jesli uzytkonik ukonczyl choc 1 serie
        sets_completed = workout_manager.sets_done.get(exercise_type, 0)

        if (
                exercise_type != "none"
                and sets_completed > 0
                and not workout_manager.is_workout_complete(exercise_type)
        ):

            ng.notif.add_notification(f"[BLOKADA] Ukończ serie dla '{exercise_type}'!",duration_seconds=2.0,)
            if speaker:
                speaker.say(f"Najpierw ukończ obecne ćwiczenie.")

        else:
            exercise_type = cmd
            ng.notif.add_notification(f" Zmieniono ćwiczenie na: {cmd}",duration_seconds=2.0,)
            if speaker:
                speaker.say(f"Wybrano: {cmd}.")

    # resetowanie w kolejnej funkcji wiec last_command czyscimy tam
    if cmd != "reset":
        voice_control.last_command = ""
    return exercise_type


# pomocnicza funkcje do obslugi przyciskow +/- aby pozbyc sie powtorzen
# pomocnicza do aktualizacji grafiki
def update_settings_input(ui_input, font, new_text):
    ui_input.text = new_text
    ui_input.txt_surface = font.render(new_text, True, COLOR_TEXT)


# pomocnicza do aktualizacji danych w workout managerze
def handle_settings_change(workout_manager, ui, font, exercise, delta):
    workout_manager.change_target(exercise, delta)

    new_text = str(workout_manager.get_target_set(exercise))

    input_box_key = f"inp_{exercise[:3]}"
    input_box = ui[input_box_key]

    update_settings_input(input_box, font, new_text)