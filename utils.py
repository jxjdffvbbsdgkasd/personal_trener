from settings import *

font_big = None
font_med = None
font_small = None

def init_fonts():
    global font_big, font_med, font_small
    font_big = pygame.font.SysFont("arial", 60, bold=True)
    font_med = pygame.font.SysFont("arial", 30, bold=True)
    font_small = pygame.font.SysFont("consolas", 20)

def cv2_to_pygame(frame, width, height):
    frame = cv2.resize(frame, (width, height))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)
    return pygame.surfarray.make_surface(frame)

def draw_text_centered(surface, text, font, color, center_x, center_y):
    if font is None: return
    render = font.render(text, True, color)
    rect = render.get_rect(center=(center_x, center_y))
    surface.blit(render, rect)


def draw_dashboard(screen, exercise_name, is_running, trainer, angles):
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

    draw_text_centered(screen, f"Ćwiczenie: {exercise_name.upper()}", font_med, COLOR_ACCENT, center_x, y_start + 30)

    status_msg = "Seria trwa" if is_running else "Oczekiwanie"
    status_col = COLOR_GREEN if is_running else COLOR_RED

    # Ramka statusu
    pygame.draw.rect(screen, status_col, (center_x - 150, y_start + 60, 300, 40), border_radius=10)
    draw_text_centered(screen, status_msg, font_small, (0, 0, 0), center_x, y_start + 80)

    # Box na Feedback
    if trainer.feedback:
        for i, msg in enumerate(trainer.feedback[:3]):
            draw_text_centered(screen, msg, font_small, COLOR_RED, center_x, y_start + 140 + (i * 25))
    else:
        draw_text_centered(screen, "Technika Prawidłowa", font_small, (100, 100, 100), center_x, y_start + 150)

    # lewa
    pygame.draw.rect(screen, COLOR_PANEL, (left_box_x, box_y, box_width, box_height), border_radius=15)
    draw_text_centered(screen, "Lewa ręka", font_med, COLOR_TEXT, left_center_x, y_start + 50)
    draw_text_centered(screen, str(trainer.reps_left), font_big, COLOR_ACCENT, left_center_x, y_start + 110)
    draw_text_centered(screen, "powtórzeń", font_small, (150,150,150), left_center_x, y_start + 150)
    ang_l = angles.get("left_elbow")
    val_l = f"{int(ang_l)}°" if ang_l else "--"
    draw_text_centered(screen, f"Kąt: {val_l}", font_small, COLOR_TEXT, left_center_x, y_start + 190)

    # prawa
    pygame.draw.rect(screen, COLOR_PANEL, (right_box_x, box_y, box_width, box_height), border_radius=15)
    draw_text_centered(screen, "Prawa Ręka", font_med, COLOR_TEXT, right_center_x, y_start + 50)
    draw_text_centered(screen, str(trainer.reps_right), font_big, COLOR_ACCENT, right_center_x, y_start + 110)
    draw_text_centered(screen, "powtórzeń", font_small, (150, 150, 150), right_center_x, y_start + 150)
    ang_r = angles.get("right_elbow")
    val_r = f"{int(ang_r)}°" if ang_r else "--"
    draw_text_centered(screen, f"Kąt: {val_r}", font_small, COLOR_TEXT, right_center_x, y_start + 190)

def detect_and_draw(frame, model):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_rgb.flags.writeable = False

    results = model.process(frame_rgb)

    if results.pose_landmarks:
        mp.solutions.drawing_utils.draw_landmarks(
            frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS
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


def compute_angles_3d(results_left, results_right, focal=1.0, baseline=0.6):
    """
    obliczanie katow w stawach w 3d. zwraca slowmiki:
    right/left_elbow (zgiecie reki katy od 0 do 180)
    oraz
    right/left_shoulder_swing (wychylenie lokcia od tulowia)

    """
    pts3d = reconstruct_3d(results_left, results_right, focal=focal, baseline=baseline)
    angles = {}
    # Use MediaPipe landmark indices
    L_SHOULDER = mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value
    L_ELBOW = mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value
    L_WRIST = mp.solutions.pose.PoseLandmark.LEFT_WRIST.value
    R_SHOULDER = mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value
    R_ELBOW = mp.solutions.pose.PoseLandmark.RIGHT_ELBOW.value
    R_WRIST = mp.solutions.pose.PoseLandmark.RIGHT_WRIST.value
    L_HIP = mp.solutions.pose.PoseLandmark.LEFT_HIP.value
    R_HIP = mp.solutions.pose.PoseLandmark.RIGHT_HIP.value
    # TEST na bujanie biodrami przod tyl
    L_KNEE = mp.solutions.pose.PoseLandmark.LEFT_KNEE.value
    R_KNEE = mp.solutions.pose.PoseLandmark.RIGHT_KNEE.value

    # katy w łokciu (shoulder - elbow - wrist)
    if L_SHOULDER in pts3d and L_ELBOW in pts3d and L_WRIST in pts3d:
        angles["left_elbow"] = angle_between_3d(
            pts3d[L_SHOULDER], pts3d[L_ELBOW], pts3d[L_WRIST]
        )
    else:
        angles["left_elbow"] = None

    if R_SHOULDER in pts3d and R_ELBOW in pts3d and R_WRIST in pts3d:
        angles["right_elbow"] = angle_between_3d(
            pts3d[R_SHOULDER], pts3d[R_ELBOW], pts3d[R_WRIST]
        )
    else:
        angles["right_elbow"] = None

    # ----- nowe
    # jak bardzo ramie odchyla sie od pionu tulowia
    # kat barkowy (kat miedzy biodrem, barkiem a lokciem)
    if L_HIP in pts3d and L_SHOULDER in pts3d and L_ELBOW in pts3d:
        angles["left_shoulder_swing"] = angle_between_3d(
            pts3d[L_HIP], pts3d[L_SHOULDER], pts3d[L_ELBOW]
        )
    else:
        angles["left_shoulder_swing"] = None

    if R_HIP in pts3d and R_SHOULDER in pts3d and R_ELBOW in pts3d:
        angles["right_shoulder_swing"] = angle_between_3d(
            pts3d[R_HIP], pts3d[R_SHOULDER], pts3d[R_ELBOW]
        )
    else:
        angles["right_shoulder_swing"] = None

    # kat biodrowy (wykrywanie bujania sie przod tyl)
    # (bark biodro kolano)
    # prosto 180 stopni
    # pochylenie to mniej niz 180
    if L_SHOULDER in pts3d and L_HIP in pts3d and L_KNEE in pts3d:
        angles["left_hip_angle"] = angle_between_3d(
            pts3d[L_SHOULDER], pts3d[L_HIP], pts3d[L_KNEE]
        )
    else:
        angles["left_hip_angle"] = None

    if R_SHOULDER in pts3d and R_HIP in pts3d and R_KNEE in pts3d:
        angles["right_hip_angle"] = angle_between_3d(
            pts3d[R_SHOULDER], pts3d[R_HIP], pts3d[R_KNEE]
        )
    else:
        angles["right_hip_angle"] = None

    # ------ nowe

    # # (szyja, bark, lokiec)
    # # jak daleko jest lokiec od szyi
    # # nw czy nadal to uzywane bedzie, zostawiam zeby nie krzyczalo przy wyswietlaniu
    # # najwyzej sie usunie xd
    # # narazie komentuje to!

    # angles["left_shoulder"] = None
    # angles["right_shoulder"] = None

    # neck = None
    # if L_SHOULDER in pts3d and R_SHOULDER in pts3d:
    #     neck = (pts3d[L_SHOULDER] + pts3d[R_SHOULDER]) / 2.0

    # # Left shoulder angle: neck(or left hip) - left_shoulder - left_elbow
    # if L_SHOULDER in pts3d and L_ELBOW in pts3d:
    #     ref = None
    #     if neck is not None:
    #         ref = neck
    #     elif L_HIP in pts3d:
    #         ref = pts3d[L_HIP]
    #     if ref is not None:
    #         angles["left_shoulder"] = angle_between_3d(
    #             ref, pts3d[L_SHOULDER], pts3d[L_ELBOW]
    #         )

    # # Right shoulder angle: neck(or right hip) - right_shoulder - right_elbow
    # if R_SHOULDER in pts3d and R_ELBOW in pts3d:
    #     ref = None
    #     if neck is not None:
    #         ref = neck
    #     elif R_HIP in pts3d:
    #         ref = pts3d[R_HIP]
    #     if ref is not None:
    #         angles["right_shoulder"] = angle_between_3d(
    #             ref, pts3d[R_SHOULDER], pts3d[R_ELBOW]
    #         )

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
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        text = r.recognize_google(audio, show_all=False,language='pl-PL')
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
