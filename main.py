from ui_builder import build_ui
from settings import *
from classes import *
from utils import *
from ui_components import *
from app_states import (
    handle_login_state,
    handle_menu_state,
    handle_training_state,
    handle_history_state,
    handle_history_details_state,
    handle_settings_state,
)

pygame.init()
font_big, font_med, font_small = init_fonts()


screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("Cyber Trener - System Analizy Ruchu")
clock = pygame.time.Clock()

# kamery
mp_pose = mp.solutions.pose
pose_local = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
pose_ip = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap_local = cv2.VideoCapture(local_idx)
cam_ip = None

print("Wybierz ćwiczenie (biceps albo barki)")
voice_control = VoiceThread(model_path="vosk-model")

game_state = GameState()
trainer = Trainer()
workout_manager = WorkoutManager()
db = DBManager()
angles = None

# budowa ui
ui = build_ui(CENTER_X, CENTER_Y, font_big, font_med, font_small)

while game_state.running:
    screen.fill(COLOR_BG)

    # obsluga zdarzen
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            game_state.running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                game_state.running = False

        # obsluga wpisywania tekstu w login i w settings
        if game_state.state == "LOGIN":
            ui["input_login"].handle_event(event)
            ui["input_pass"].handle_event(event)
        elif game_state.state == "SETTINGS":
            # reczne wpisywanie ilosci serii
            ui["inp_bic"].handle_event(event)
            ui["inp_bar"].handle_event(event)

            # walidacja wpisywania w ustawieniach
            if ui["inp_bic"].text.isdigit() and int(ui["inp_bic"].text) > 0:
                workout_manager.target_sets["biceps"] = int(ui["inp_bic"].text)
            if ui["inp_bar"].text.isdigit() and int(ui["inp_bar"].text) > 0:
                workout_manager.target_sets["barki"] = int(ui["inp_bar"].text)

    # STAN LOGOWANIA
    if game_state.state == "LOGIN":
        handle_login_state(
            screen,
            ui,
            events,
            game_state,
            db,
            workout_manager,
            font_big,
            font_med,
            font_small,
            CENTER_X,
            CENTER_Y,
        )

    # STAN MENU GLOWNEGO
    elif game_state.state == "MENU":
        cam_ip = handle_menu_state(
            screen,
            ui,
            events,
            game_state,
            trainer,
            workout_manager,
            cam_ip,
            font_big,
            font_med,
            CENTER_X,
        )

    # STAN TRENINGU
    elif game_state.state == "TRAINING":
        cam_ip, angles = handle_training_state(
            screen,
            ui,
            events,
            game_state,
            trainer,
            workout_manager,
            db,
            voice_control,
            cap_local,
            cam_ip,
            pose_local,
            pose_ip,
            font_big,
            font_med,
            font_small,
            CENTER_X,
            CENTER_Y,
        )

    # STAN HISTORII
    elif game_state.state == "HISTORY":
        handle_history_state(
            screen, ui, events, game_state, db, font_big, font_med, font_small, CENTER_X
        )

    # STAN SZCZEGOLY TRRNINGU
    elif game_state.state == "HISTORY_DETAILS":
        handle_history_details_state(
            screen, ui, events, game_state, db, font_big, font_med, font_small, CENTER_X
        )

    # STAN USTAWIEN
    elif game_state.state == "SETTINGS":
        handle_settings_state(
            screen, ui, events, game_state, db, workout_manager, font_big, font_med
        )

    pygame.display.flip()
    clock.tick(FPS)

voice_control.stop()
cap_local.release()
if cam_ip:
    cam_ip.release()
db.close()
pygame.quit()
