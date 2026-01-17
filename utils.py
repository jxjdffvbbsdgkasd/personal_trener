from settings import *

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
    # Zamieniamy osie (height,width,3) -> (width,height,3) bez obracania/odbicia
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
    # lewa
    left_center_x = WIN_W // 4
    # prawa
    right_center_x = (WIN_W // 4) * 3

    box_width = 320
    box_height = DASH_H - 40

    left_box_x = left_center_x - (box_width // 2)
    right_box_x = right_center_x - (box_width // 2)
    box_y = y_start + 20

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

        # info po skonczeniu wszystkich
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

    # Box na Feedback
    if trainer.feedback:
        for i, msg in enumerate(trainer.feedback[:3]):
            draw_text_centered(
                screen, msg, font_small, COLOR_RED, center_x, y_start + 140 + (i * 25)
            )
    else:
        draw_text_centered(
            screen,
            "Technika Prawidłowa",
            font_small,
            (100, 100, 100),
            center_x,
            y_start + 150,
        )
    if angles is None:
        return

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


def detect_and_draw(frame, model, draw_color=(0, 255, 0)):
    """
    Wykrywa pozę i rysuje szkielet w zadanym kolorze.
    draw_color: krotka (B, G, R) - domyślnie Zielony (0, 255, 0).
    """
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
    """Return dict of landmark index -> (x_norm, y_norm)."""
    if not results or not results.pose_landmarks:
        return {}
    lm = results.pose_landmarks.landmark
    return {i: (lm[i].x, lm[i].y) for i in range(len(lm))}


def _triangulate_point(x1, y1, x2, y2, focal=1.0, baseline=0.6):
    """Approximate 3D point from two normalized image coords.

    Assumptions:
    - both images are normalized coords from 0..1
    - cameras are symmetric around Z axis at +/-45 degrees yaw
    - focal length is arbitrary scale (focal=1 gives reasonable relative distances)
    - baseline is distance between cameras along X axis
    Returns 3D np.array (x, y, z) in arbitrary units.
    """
    # image plane coords centered at 0
    x_im1 = x1 - 0.5
    y_im1 = 0.5 - y1
    x_im2 = x2 - 0.5
    y_im2 = 0.5 - y2

    d1 = np.array([x_im1, y_im1, focal], dtype=float)
    d2 = np.array([x_im2, y_im2, focal], dtype=float)
    d1 = d1 / np.linalg.norm(d1)
    d2 = d2 / np.linalg.norm(d2)

    # Camera positions: left (-b/2,0,0), right (+b/2,0,0)
    o1 = np.array([-baseline / 2.0, 0.0, 0.0])
    o2 = np.array([baseline / 2.0, 0.0, 0.0])

    # Rotate directions by yaw: left camera looks +45deg, right camera -45deg
    th = np.deg2rad(45.0)
    R_left = np.array(
        [[np.cos(th), 0.0, np.sin(th)], [0.0, 1.0, 0.0], [-np.sin(th), 0.0, np.cos(th)]]
    )
    R_right = np.array(
        [
            [np.cos(-th), 0.0, np.sin(-th)],
            [0.0, 1.0, 0.0],
            [-np.sin(-th), 0.0, np.cos(-th)],
        ]
    )

    v1 = R_left.dot(d1)
    v2 = R_right.dot(d2)

    # Triangulate by finding closest points on two rays o1+s*v1 and o2+t*v2
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
    """Reconstruct 3D points for landmarks present in both results.
    Returns dict index -> (x,y,z)
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
    """Return angle at point b formed by points a-b-c in degrees."""
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

    # Swing (Czy łokieć ucieka od ciała w przód/tył/bok - ruch ramienia)
    angles["left_shoulder_swing"] = get_ang(
        pose.LEFT_HIP, pose.LEFT_SHOULDER, pose.LEFT_ELBOW
    )
    angles["right_shoulder_swing"] = get_ang(
        pose.RIGHT_HIP, pose.RIGHT_SHOULDER, pose.RIGHT_ELBOW
    )

    # --- NOWOŚĆ: WYKRYWANIE "KÓŁEK" (FLARE) ---
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
    Liczy kąty pod wyciskanie na barki (Overhead Press).
    Kluczowy jest kąt: Biodro-Bark-Łokieć (jak wysoko jest ramię).
    """
    pts3d = reconstruct_3d(results_left, results_right, focal=focal, baseline=baseline)
    angles = {}

    # Enumy MediaPipe
    Pose = mp.solutions.pose.PoseLandmark

    # Funkcja pomocnicza do bezpiecznego liczenia
    def get_ang(p1, p2, p3):
        if p1.value in pts3d and p2.value in pts3d and p3.value in pts3d:
            return angle_between_3d(pts3d[p1.value], pts3d[p2.value], pts3d[p3.value])
        return None

    # 1. KĄT WZNOSU RAMIENIA (Biodro -> Bark -> Łokieć)
    # To nam mówi, czy ręka jest na górze (ok 170-180) czy na dole (ok 90)
    angles["left_shoulder_lift"] = get_ang(
        Pose.LEFT_HIP, Pose.LEFT_SHOULDER, Pose.LEFT_ELBOW
    )
    angles["right_shoulder_lift"] = get_ang(
        Pose.RIGHT_HIP, Pose.RIGHT_SHOULDER, Pose.RIGHT_ELBOW
    )

    # 2. KĄT WYPROSTU W ŁOKCIU (Bark -> Łokieć -> Nadgarstek)
    # To nam mówi, czy "dopchnęliśmy" ruch (wyprost > 160)
    angles["left_elbow"] = get_ang(Pose.LEFT_SHOULDER, Pose.LEFT_ELBOW, Pose.LEFT_WRIST)
    angles["right_elbow"] = get_ang(
        Pose.RIGHT_SHOULDER, Pose.RIGHT_ELBOW, Pose.RIGHT_WRIST
    )

    return angles


def draw_angles_on_frames(frame_left, frame_right, results_left, results_right, angles):
    """Draw angle text near elbow landmarks on both frames."""
    # Draw both left and right angles on both frames using each frame's landmark positions
    h1, w1 = frame_left.shape[:2]
    h2, w2 = frame_right.shape[:2]

    COLOR_ELBOW = (0, 255, 255)  # zolty
    COLOR_SWING = (0, 140, 255)  # pomarancz
    COLOR_HIP = (255, 0, 255)  # fiolet

    def draw_styled_text(img, text, x, y, color):
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.7
        thickness = 2

        # czarny outline
        cv2.putText(img, text, (x, y), font, scale, (0, 0, 0), thickness + 3)
        # wartosci katow
        cv2.putText(img, text, (x, y), font, scale, color, thickness)

    # pomocnicza do pokazania katow
    def _draw_if(
        frame, lm_list, landmark_idx, x_scale, y_scale, val, prefix, color, y_offset=0
    ):
        if lm_list is None:
            return
        if landmark_idx is None or landmark_idx >= len(lm_list):
            return
        # pobranie punktu
        x = int(lm_list[landmark_idx].x * x_scale)
        y = int(lm_list[landmark_idx].y * y_scale)
        if val is not None:
            text = f"{prefix}:{int(val)}"
            draw_styled_text(frame, text, x - 30, y + y_offset, color)

    # lewa kamerka (laptop)
    if results_left and results_left.pose_landmarks:
        lm_l = results_left.pose_landmarks.landmark

        # barki
        _draw_if(
            frame_left,
            lm_l,
            mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value,
            w1,
            h1,
            angles.get("left_shoulder_swing"),
            "Lsw",
            COLOR_SWING,
            y_offset=-40,
        )
        _draw_if(
            frame_left,
            lm_l,
            mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value,
            w1,
            h1,
            angles.get("right_shoulder_swing"),
            "Rsw",
            COLOR_SWING,
            y_offset=-40,
        )

        # lokcie
        _draw_if(
            frame_left,
            lm_l,
            mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value,
            w1,
            h1,
            angles.get("left_elbow"),
            "Lel",
            COLOR_ELBOW,
            y_offset=10,
        )
        _draw_if(
            frame_left,
            lm_l,
            mp.solutions.pose.PoseLandmark.RIGHT_ELBOW.value,
            w1,
            h1,
            angles.get("right_elbow"),
            "Rel",
            COLOR_ELBOW,
            y_offset=10,
        )

        # biodra
        _draw_if(
            frame_left,
            lm_l,
            mp.solutions.pose.PoseLandmark.LEFT_HIP.value,
            w1,
            h1,
            angles.get("left_hip_angle"),
            "Lhip",
            COLOR_HIP,
            y_offset=50,
        )
        _draw_if(
            frame_left,
            lm_l,
            mp.solutions.pose.PoseLandmark.RIGHT_HIP.value,
            w1,
            h1,
            angles.get("right_hip_angle"),
            "Rhip",
            COLOR_HIP,
            y_offset=50,
        )

    # prawa kamerka (telefon)
    if results_right and results_right.pose_landmarks:
        lm_r = results_right.pose_landmarks.landmark

        # barki
        _draw_if(
            frame_right,
            lm_r,
            mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value,
            w2,
            h2,
            angles.get("left_shoulder_swing"),
            "Lsw",
            COLOR_SWING,
            y_offset=-40,
        )
        _draw_if(
            frame_right,
            lm_r,
            mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value,
            w2,
            h2,
            angles.get("right_shoulder_swing"),
            "Rsw",
            COLOR_SWING,
            y_offset=-40,
        )

        # łokcie
        _draw_if(
            frame_right,
            lm_r,
            mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value,
            w2,
            h2,
            angles.get("left_elbow"),
            "Lel",
            COLOR_ELBOW,
            y_offset=10,
        )
        _draw_if(
            frame_right,
            lm_r,
            mp.solutions.pose.PoseLandmark.RIGHT_ELBOW.value,
            w2,
            h2,
            angles.get("right_elbow"),
            "Rel",
            COLOR_ELBOW,
            y_offset=10,
        )

        # biodra
        _draw_if(
            frame_right,
            lm_r,
            mp.solutions.pose.PoseLandmark.LEFT_HIP.value,
            w2,
            h2,
            angles.get("left_hip_angle"),
            "Lhip",
            COLOR_HIP,
            y_offset=50,
        )
        _draw_if(
            frame_right,
            lm_r,
            mp.solutions.pose.PoseLandmark.RIGHT_HIP.value,
            w2,
            h2,
            angles.get("right_hip_angle"),
            "Rhip",
            COLOR_HIP,
            y_offset=50,
        )


def select_exercise_via_voice(timeout=10, phrase_time_limit=4):
    r = sr.Recognizer()
    mic = sr.Microphone(device_index=1, sample_rate=48000)
    try:
        with mic as source:
            print("Listening for exercise name (say 'barki' or 'biceps')...")
            audio = r.listen(
                source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
        text = r.recognize_google(audio, show_all=False, language="pl-PL")
        if not text:
            return None
        text = text.lower()
        if "barki" in text:
            return "barki"
        if "biceps" in text:
            return "biceps"
    except Exception as e:
        pass
    return None


def process_command(voice_control, exercise_type, workout_manager, trainer):
    cmd = voice_control.last_command

    trainer.clear_system_message()

    if not cmd or cmd == "COMMAND_NONE":
        return exercise_type

    # obsluga start stop
    if cmd == "start":
        if exercise_type == "none":
            print(" Wybierz ćwiczenie najpierw!")
            trainer.system_message.append("Najpierw wybierz ćwiczenie!")
        else:
            voice_control.started = True

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

            print(f" [BLOKADA] Ukończ serie dla '{exercise_type}'!")
            trainer.system_message.append(f"Dokończ serie dla '{exercise_type}'!")
        else:
            exercise_type = cmd
            print(f" Zmieniono ćwiczenie na: {cmd}")

    # resetowanie
    elif cmd == "reset":
        reset_status = workout_manager.reset_targets(cmd, exercise_type)
        if reset_status is True:
            trainer.system_message.append(
                f"Liczniki dla '{exercise_type}' zresetowane!"
            )
        elif reset_status is False:
            trainer.system_message.append("Dokończ serie, zanim zresetujesz!")
            trainer.system_message.append("Dasz radę!")

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
