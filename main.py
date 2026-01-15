from settings import *
from classes import *
from utils import *
import utils
from db_manager import DBManager
from ui_components import *

pygame.init()
init_fonts()

# czcionki z utilsow
font_big = utils.font_big
font_med = utils.font_med
font_small = utils.font_small

screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("Cyber Trener - System Analizy Ruchu")
clock = pygame.time.Clock()

app_state = "LOGIN"  # LOGIN, MENU, TRAINING, HISTORY
current_user_id = None
current_user_name = ""
login_message = ""  # do bledow np zle haslo

mp_pose = mp.solutions.pose
pose_local = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
pose_ip = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap_local = cv2.VideoCapture(local_idx)
# cam_ip = IPStream(ip_url)
cam_ip = None

print("Wybierz ćwiczenie (biceps albo barki)")
exercise_type = "none"
voice_control = VoiceThread(model_path="vosk-model")

trainer = Trainer()
workout_manager = WorkoutManager()
selected_session_id = None  # przegladana aktualnie sesja w historii
session_buttons = []  # lista przyciskow z datami treningow
db = DBManager()
# current_user_id = 1  # narazie na sztywno bo nie ma logowania
current_user_id = None
angles = None
running = True

# konfiguracja ui
center_x = WIN_W // 2
center_y = WIN_H // 2

# ekran logowania
input_login = InputBox(center_x - 100, center_y - 80, 200, 40, font_med)
input_pass = InputBox(
    center_x - 100, center_y - 20, 200, 40, font_med, is_password=True
)
button_login = Button(
    center_x - 100, center_y + 50, 200, 50, "Zaloguj", font_med, "LOGIN"
)
button_register = Button(
    center_x - 100, center_y + 110, 200, 50, "Rejestracja", font_med, "REGISTER"
)

# menu glowne
button_start_train = Button(
    center_x - 150, center_y - 50, 300, 60, "Rozpocznij Trening", font_med, "GOTO_TRAIN"
)
button_settings = Button(
    center_x - 150,
    center_y + 110,
    300,
    60,
    "Dostosuj Trening",
    font_med,
    "GOTO_SETTINGS",
)
button_show_hist = Button(
    center_x - 150, center_y + 30, 300, 60, "Historia Treningów", font_med, "GOTO_HIST"
)
button_logout = Button(WIN_W - 120, 20, 100, 40, "Wyloguj", font_small, "LOGOUT")

# menu dostosowyania treningu
# biceps
btn_bic_minus = Button(
    center_x - 150, center_y - 60, 60, 60, "-", font_big, "BIC_MINUS"
)
btn_bic_plus = Button(center_x + 90, center_y - 60, 60, 60, "+", font_big, "BIC_PLUS")
# pole tekstowe coby nie klikac +/-
input_bic_sets = InputBox(
    center_x - 30, center_y - 55, 60, 50, font_big, text="3", centered=True, max_chars=2
)
# barki
btn_bar_minus = Button(
    center_x - 150, center_y + 60, 60, 60, "-", font_big, "BAR_MINUS"
)
btn_bar_plus = Button(center_x + 90, center_y + 60, 60, 60, "+", font_big, "BAR_PLUS")
# tu tez pole tekstowe jak wyzej -..-
input_bar_sets = InputBox(
    center_x - 30, center_y + 65, 60, 50, font_big, text="3", centered=True, max_chars=2
)
# przycisk powrotu
button_back = Button(20, 20, 100, 40, "Powrót", font_small, "BACK")

while running:
    screen.fill(COLOR_BG)

    # obsluga zdarzen
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False

        # Obsługa wpisywania tekstu tylko w stanie LOGIN
        if app_state == "LOGIN":
            input_login.handle_event(event)
            input_pass.handle_event(event)

    # STAN LOGOWANIA
    if app_state == "LOGIN":
        draw_text_centered(
            screen, "CYBER TRENER - LOGOWANIE", font_big, COLOR_ACCENT, center_x, 100
        )

        input_login.draw(screen)
        input_pass.draw(screen)
        button_login.draw(screen)
        button_register.draw(screen)

        # Komunikaty błędów
        if login_message:
            draw_text_centered(
                screen, login_message, font_small, COLOR_RED, center_x, center_y + 180
            )

        # Logika Przycisków
        for event in events:
            if button_login.is_clicked(event):
                login = input_login.get_text()
                password = input_pass.get_text()
                user = db.login_user(login, password)
                if user:
                    current_user_id = user[0]
                    current_user_name = user[1]
                    app_state = "MENU"
                    login_message = ""
                    print(f"Zalogowano: {current_user_name}")
                else:
                    login_message = "Błędny login lub hasło!"

            if button_register.is_clicked(event):
                login = input_login.get_text()
                password = input_pass.get_text()
                if len(password) < 4:
                    login_message = "Hasło za krótkie (min 4 znaki)"
                else:
                    ok, msg = db.register_user(login, password)
                    login_message = msg
                    if ok:
                        # uzytkownik od razu zalogowany tym czym sie zarejestrowal
                        user = db.login_user(login, password)
                        if user:
                            current_user_id = user[0]
                            current_user_name = user[1]
                            app_state = "MENU"
                            login_message = ""
                            print(f"Zarejestrowano i zalogowano: {current_user_name}")

                            input_pass.text = ""
                            input_pass.txt_surface = font_med.render(
                                "", True, (255, 255, 255)
                            )

    # STAN MENU GLOWNEGO
    elif app_state == "MENU":
        draw_text_centered(
            screen, f"Witaj, {current_user_name}!", font_big, COLOR_TEXT, center_x, 150
        )

        button_start_train.draw(screen)
        button_show_hist.draw(screen)
        button_settings.draw(screen)
        button_logout.draw(screen)

        for event in events:
            if button_start_train.is_clicked(event):
                app_state = "TRAINING"
                trainer.reset()  # reset trenera przed startem

                if workout_manager.session_id is None:
                    workout_manager.start_new_training()

                # podczas "siedzenia" w menu kamerka sie wylacza, test czy to naprawi blad?
                if cam_ip is None:
                    print(" Nawiązywanie połączenia z kamerą IP..")
                    cam_ip = IPStream(ip_url)

            if button_show_hist.is_clicked(event):
                app_state = "HISTORY"

            if button_settings.is_clicked(event):
                app_state = "SETTINGS"

            if button_logout.is_clicked(event):
                app_state = "LOGIN"
                current_user_id = None
                current_user_name = ""
                input_pass.text = ""  # czyszczenie hasla
                input_pass.txt_surface = font_med.render("", True, (255, 255, 255))

    elif app_state == "TRAINING":
        # obhsluga zapisu skonczonej serii do bazy (po powiedzeniu "STOP")
        if voice_control.last_command == "stop" and voice_control.started:
            if exercise_type != "none":
                acc = trainer.get_accuracy()
                # pobieramy info potrzebne do zapisania serii
                session_id = workout_manager.session_id
                set_num = workout_manager.get_actual_set_number_for_db(exercise_type)
                print(f" Koniec serii. Zapisuję do bazy.. Poprawność: {acc:.1f}%")

                db.save_workout(
                    current_user_id,
                    session_id,
                    exercise_type,
                    set_num,
                    trainer.reps_left,
                    trainer.reps_right,
                    acc,
                )

                # zaliczamy serie w managerze workout'u
                workout_manager.mark_set_complete(exercise_type)

                # reset licznikow
                trainer.reset()

        exercise_type = process_command(voice_control, exercise_type)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    trainer.reset()  # Reset klawiszem R

            # przycisk powrotu
            if button_back.is_clicked(event):
                app_state = "MENU"
                # voice_control.stop()  # ubicie watku do komend glosowych, zakomentowane bo psuje xd
                exercise_type = "none"

                if cam_ip:
                    cam_ip.release()
                    cam_ip = None
                    print(" Rozlaczono z kamera IP")

        ret1, frame1 = cap_local.read()
        if cam_ip:
            ret2, frame2 = cam_ip.read()
        else:
            ret2, frame2 = False, None

        # Obsługa błędów kamer (pusta klatka)
        if not ret1:
            frame1 = np.zeros((CAM_H, CAM_W, 3), np.uint8)
        if not ret2:
            frame2 = np.zeros((CAM_H, CAM_W, 3), np.uint8)

        frame1 = cv2.resize(frame1, (CAM_W, CAM_H))
        frame2 = cv2.resize(frame2, (CAM_W, CAM_H))

        # kolor szkieletu na podstawie bledu
        skeleton_color = (0, 255, 0)  # Domyślnie ZIELONY
        if trainer.cheat_left or trainer.cheat_right:
            skeleton_color = (0, 0, 255)  # bledne: CZERWON

        # kolor do funkcji rysujacej
        frame1, results1 = detect_and_draw(
            frame1, pose_local, draw_color=skeleton_color
        )
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

        draw_dashboard(
            screen,
            exercise_type,
            voice_control.started,
            trainer,
            angles,
            workout_manager,
        )

        button_back.draw(screen)

    # STAN HISTORII
    elif app_state == "HISTORY":
        draw_text_centered(
            screen, "Wybierz Trening", font_big, COLOR_ACCENT, center_x, 50
        )
        if not session_buttons:
            raw_sessions = db.get_unique_sessions(current_user_id)
            start_y = 120
            for i, sess in enumerate(raw_sessions):
                s_id = sess[0]
                s_date = sess[1]
                label = f"Trening: {s_date[:-3]}"

                btn = Button(
                    center_x - 150, start_y + (i * 70), 300, 50, label, font_small, s_id
                )
                session_buttons.append(btn)

        if not session_buttons:
            draw_text_centered(
                screen,
                "Brak zapisanych treningów.",
                font_med,
                COLOR_TEXT,
                center_x,
                150,
            )
        else:
            for btn in session_buttons:
                btn.draw(screen)

        button_back.draw(screen)

        for event in events:
            if button_back.is_clicked(event):
                app_state = "MENU"
                session_buttons = []

            for btn in session_buttons:
                if btn.is_clicked(event):
                    selected_session_id = btn.action_code  # id sesji tu trzymamy
                    app_state = "HISTORY_DETAILS"  # idziemy do szczegolow

    # STAN SZCZEGOLY TRRNINGU
    elif app_state == "HISTORY_DETAILS":
        draw_text_centered(
            screen, "Szczegóły Treningu", font_big, COLOR_ACCENT, center_x, 50
        )

        # szczegoly dla wybanego id
        rows = db.get_session_details(selected_session_id)

        biceps_data = [r for r in rows if r[0] == "biceps"]
        barki_data = [r for r in rows if r[0] == "barki"]

        y_pos = 110

        # biceps
        if biceps_data:
            draw_text_centered(
                screen, "--- BICEPS ---", font_med, COLOR_ACCENT, center_x, y_pos
            )
            y_pos += 35
            # Nagłówek tabelki
            headers = f"{'Seria':<6} {'Lewa':<6} {'Prawa':<6} {'Poprawność'}"
            draw_text_centered(
                screen, headers, font_small, (150, 150, 150), center_x, y_pos
            )
            y_pos += 25

            for row in biceps_data:
                # row: (type, set_num, l, r, acc)
                line = f"Nr {row[1]:<5} {row[2]:<8} {row[3]:<8} {row[4]:.1f}%"
                draw_text_centered(
                    screen, line, font_small, COLOR_TEXT, center_x, y_pos
                )
                y_pos += 25

            y_pos += 20

        # barki
        if barki_data:
            draw_text_centered(
                screen, "--- BARKI ---", font_med, COLOR_ACCENT, center_x, y_pos
            )
            y_pos += 35
            headers = f"{'Seria':<6} {'Lewa':<6} {'Prawa':<6} {'Poprawność'}"
            draw_text_centered(
                screen, headers, font_small, (150, 150, 150), center_x, y_pos
            )
            y_pos += 25

            for row in barki_data:
                line = f"Nr {row[1]:<5} {row[2]:<8} {row[3]:<8} {row[4]:.1f}%"
                draw_text_centered(
                    screen, line, font_small, COLOR_TEXT, center_x, y_pos
                )
                y_pos += 25

        button_back.draw(screen)

        for event in events:
            if button_back.is_clicked(event):
                app_state = "HISTORY"

    # STAN USTAWIEN
    elif app_state == "SETTINGS":
        draw_text_centered(
            screen, "Konfiguracja Serii", font_big, COLOR_ACCENT, center_x, 50
        )

        # biceps
        y_biceps = center_y - 30
        draw_text_centered(
            screen, "BICEPS", font_med, COLOR_TEXT, center_x, y_biceps - 50
        )
        btn_bic_minus.draw(screen)
        btn_bic_plus.draw(screen)
        input_bic_sets.draw(screen)

        # # wyswietlona aktualna liczba serii
        # val_biceps = workout_manager.get_target_set("biceps")
        # draw_text_centered(
        #     screen, str(val_biceps), font_big, COLOR_TEXT, center_x, y_biceps
        # )

        # barki
        y_barki = center_y + 90
        draw_text_centered(
            screen, "BARKI", font_med, COLOR_TEXT, center_x, y_barki - 50
        )
        btn_bar_minus.draw(screen)
        btn_bar_plus.draw(screen)
        input_bar_sets.draw(screen)

        # val_barki = workout_manager.get_target_set("barki")
        # draw_text_centered(
        #     screen, str(val_barki), font_big, COLOR_TEXT, center_x, y_barki
        # )

        # powrot
        button_back.draw(screen)

        for event in events:
            if button_back.is_clicked(event):
                app_state = "MENU"

            # reczne wpisywanie ilosci serii
            input_bic_sets.handle_event(event)
            input_bar_sets.handle_event(event)
            # walidacja czt cyfra
            if input_bic_sets.text.isdigit() and int(input_bic_sets.text) > 0:
                workout_manager.target_sets["biceps"] = int(input_bic_sets.text)

            if input_bar_sets.text.isdigit() and int(input_bar_sets.text) > 0:
                workout_manager.target_sets["barki"] = int(input_bar_sets.text)

            # obsługa przyciskow +/-
            if btn_bic_minus.is_clicked(event):
                workout_manager.change_target("biceps", -1)
                input_bic_sets.text = str(
                    workout_manager.get_target_set("biceps")
                )  # synchro z textboxem
                input_bic_sets.txt_surface = font_big.render(
                    input_bic_sets.text, True, (255, 255, 255)
                )  # aktualizacja grafiki
            if btn_bic_plus.is_clicked(event):
                workout_manager.change_target("biceps", 1)
                input_bic_sets.text = str(
                    workout_manager.get_target_set("biceps")
                )  # synchro
                input_bic_sets.txt_surface = font_big.render(
                    input_bic_sets.text, True, (255, 255, 255)
                )  # refresh grafiki

            if btn_bar_minus.is_clicked(event):
                workout_manager.change_target("barki", -1)
                input_bar_sets.text = str(
                    workout_manager.get_target_set("barki")
                )  # synchro
                input_bar_sets.txt_surface = font_big.render(
                    input_bar_sets.text, True, (255, 255, 255)
                )  # odswiez
            if btn_bar_plus.is_clicked(event):
                workout_manager.change_target("barki", 1)
                input_bar_sets.text = str(
                    workout_manager.get_target_set("barki")
                )  # synchro
                input_bar_sets.txt_surface = font_big.render(
                    input_bar_sets.text, True, (255, 255, 255)
                )  # odswiez

    pygame.display.flip()
    clock.tick(FPS)

voice_control.stop()
cap_local.release()
cam_ip.release()
db.close()
pygame.quit()
