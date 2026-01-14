from settings import *
from classes import *
from utils import *
from db_manager import DBManager

pygame.init()
init_fonts()
screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("Cyber Trener - System Analizy Ruchu")
clock = pygame.time.Clock()

mp_pose = mp.solutions.pose
pose_local = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
pose_ip = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap_local = cv2.VideoCapture(local_idx)
cam_ip = IPStream(ip_url)

print("Wybierz ćwiczenie (biceps albo barki)")
exercise_type = "none"
voice_control = VoiceThread(model_path="vosk-model")

trainer = Trainer()
db = DBManager()
current_user_id = 1  # narazie na sztywno bo nie ma logowania
angles = None
running = True
while running:

    # obhsluga zapisu skonczonej serii do bazy (po powiedzeniu "STOP")
    if voice_control.last_command == "stop" and voice_control.started:
        if exercise_type != "none":
            acc = trainer.get_accuracy()
            print(f"[ZAPIS] Koniec serii. Zapisuję do bazy.. Poprawność: {acc:.1f}%")

            db.save_workout(
                current_user_id,
                exercise_type,
                trainer.reps_left,
                trainer.reps_right,
                acc,
            )

            # reset licznikow
            trainer.reset()

    exercise_type = process_command(voice_control, exercise_type)
    if exercise_type == "reset":
        trainer.reset()
        exercise_type = "none"

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
            if event.key == pygame.K_r:
                trainer.reset()  # Reset klawiszem R

    ret1, frame1 = cap_local.read()
    ret2, frame2 = cam_ip.read()

    # Obsługa błędów kamer (pusta klatka)
    if not ret1:
        frame1 = np.zeros((CAM_H, CAM_W, 3), np.uint8)
    if not ret2:
        frame2 = np.zeros((CAM_H, CAM_W, 3), np.uint8)

    frame1 = cv2.resize(frame1, (CAM_W, CAM_H))
    frame2 = cv2.resize(frame2, (CAM_W, CAM_H))

    # 1. Ustalamy kolor na podstawie flag błędu (cheat)
    skeleton_color = (0, 255, 0)  # Domyślnie ZIELONY
    if trainer.cheat_left or trainer.cheat_right:
        skeleton_color = (0, 0, 255)  # Jeśli błąd -> CZERWONY

    # 2. Przekazujemy kolor do funkcji rysującej (draw_color)
    frame1, results1 = detect_and_draw(frame1, pose_local, draw_color=skeleton_color)
    frame2, results2 = detect_and_draw(frame2, pose_ip, draw_color=skeleton_color)

    angles = {}

    if voice_control.started:
        if exercise_type == "biceps":
            angles = compute_angles_3d_biceps(
                results1, results2, focal=1.0, baseline=0.6
            )
            trainer.process_biceps(angles)
        elif exercise_type == "barki":
            angles = compute_angles_3d_shoulders(
                results1, results2, focal=1.0, baseline=0.6
            )
            trainer.process_shoulders(angles)

    screen.fill(COLOR_BG)

    pg_frame1 = cv2_to_pygame(frame1, CAM_W, CAM_H)
    pg_frame2 = cv2_to_pygame(frame2, CAM_W, CAM_H)

    screen.blit(pg_frame1, (0, 0))
    screen.blit(pg_frame2, (CAM_W, 0))

    draw_dashboard(screen, exercise_type, voice_control.started, trainer, angles)

    pygame.display.flip()
    clock.tick(FPS)

voice_control.stop()
cap_local.release()
cam_ip.release()
db.close()
pygame.quit()
