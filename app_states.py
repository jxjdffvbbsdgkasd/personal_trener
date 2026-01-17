from settings import *
from classes import IPStream
from ui_components import Button
from utils import *


def handle_login_state(
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
):
    draw_text_centered(
        screen, "CYBER TRENER", font_big, COLOR_ACCENT, CENTER_X, CENTER_Y - 245
    )
    draw_text_centered(
        screen, "PANEL LOGOWANIA", font_small, COLOR_TEXT, CENTER_X, CENTER_Y - 195
    )

    draw_text_centered(screen, "LOGIN UŻYTKOWNIKA", font_small, (150, 150, 150), CENTER_X, CENTER_Y - 90)
    ui["input_login"].draw(screen)

    draw_text_centered(screen, "HASŁO", font_small, (150, 150, 150), CENTER_X, CENTER_Y + 30)
    ui["input_pass"].draw(screen)

    # Przyciski
    ui["btn_login"].draw(screen)
    ui["btn_register"].draw(screen)

    if game_state.login_msg:
        draw_text_centered(
            screen,
            game_state.login_msg,
            font_small,
            COLOR_RED,
            CENTER_X,
            CENTER_Y + 130
        )

    for event in events:
        # obsluga wpisywania tekstu w login i w settings
        if ui["btn_login"].is_clicked(event):
            game_state.login_msg = ""
            login = ui["input_login"].get_text()
            pwd = ui["input_pass"].get_text()
            user = db.login_user(login, pwd)
            if user:
                game_state.user_id, game_state.user_name = user
                settings = db.get_user_settings(game_state.user_id)
                if settings:
                    workout_manager.target_sets = settings
                    print(f"Wczytano ustawienia dla {game_state.user_name}.")
                else:
                    workout_manager.target_sets = {"biceps": 3, "barki": 3}

                game_state.state = "MENU"
                game_state.login_msg = ""
                print(f"Zalogowano: {game_state.user_name}")
            else:
                game_state.login_msg = "Błędny login lub hasło!"

        if ui["btn_register"].is_clicked(event):
            login = ui["input_login"].get_text()
            pwd = ui["input_pass"].get_text()
            if len(pwd) < 4:
                game_state.login_msg = "Hasło za krótkie (min 4 znaki)"
            else:
                ok, msg = db.register_user(login, pwd)
                game_state.login_msg = msg
                if ok:
                    user = db.login_user(login, pwd)
                    if user:
                        game_state.user_id, game_state.user_name = user
                        workout_manager.target_sets = {"biceps": 3, "barki": 3}
                        game_state.state = "MENU"
                        game_state.login_msg = ""
                        ui["input_pass"].text = ""
                        ui["input_pass"].txt_surface = font_med.render(
                            "", True, (255, 255, 255)
                        )


def handle_menu_state(
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
):
    draw_text_centered(
        screen,
        f"Witaj, {game_state.user_name}!",
        font_big,
        COLOR_TEXT,
        CENTER_X,
        150,
    )
    ui["btn_start"].draw(screen)
    ui["btn_hist"].draw(screen)
    ui["btn_settings"].draw(screen)
    ui["btn_logout"].draw(screen)

    for event in events:
        if ui["btn_start"].is_clicked(event):
            game_state.state = "TRAINING"
            trainer.reset()

            if workout_manager.session_id is None:
                workout_manager.start_new_training()

            if cam_ip is None:
                print(" Nawiązywanie połączenia z kamerą IP..")
                cam_ip = IPStream(ip_url)
                ng.notif.add_notification("Wybierz ćwiczenie (biceps albo barki)",duration_seconds=5.0,outline_thickness=2,)

        if ui["btn_hist"].is_clicked(event):
            game_state.state = "HISTORY"

        if ui["btn_settings"].is_clicked(event):
            game_state.state = "SETTINGS"
            biceps_text = str(workout_manager.get_target_set("biceps"))
            update_settings_input(ui["inp_bic"], font_big, biceps_text)
            barki_text = str(workout_manager.get_target_set("barki"))
            update_settings_input(ui["inp_bar"], font_big, barki_text)

        if ui["btn_logout"].is_clicked(event):
            game_state.state = "LOGIN"
            game_state.user_id = None
            workout_manager.target_sets = {"biceps": 3, "barki": 3}
            ui["input_pass"].text = ""
            ui["input_pass"].txt_surface = font_med.render("", True, (255, 255, 255))

    return cam_ip


def handle_training_state(
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
):
    # handle voice STOP
    if voice_control.last_command == "stop" and voice_control.started:
        if game_state.exercise_type != "none":
            acc = trainer.get_accuracy()
            session_id = workout_manager.session_id
            set_num = workout_manager.get_actual_set_number_for_db(
                game_state.exercise_type
            )
            print(f" Koniec serii. Zapisuję do bazy.. Poprawność: {acc:.1f}%")

            db.save_workout(
                game_state.user_id,
                session_id,
                game_state.exercise_type,
                set_num,
                trainer.reps_left,
                trainer.reps_right,
                acc,
            )

            workout_manager.mark_set_complete(game_state.exercise_type)
            trainer.reset()

    game_state.exercise_type = process_command(voice_control, game_state.exercise_type, workout_manager, trainer)
    voice_control.last_command = workout_manager.reset_targets(voice_control.last_command, voice_control.started, game_state.exercise_type)

    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                trainer.reset()

        if ui["btn_back"].is_clicked(event):
            game_state.state = "MENU"
            game_state.exercise_type = "none"

            if cam_ip is not None:
                cam_ip.release()
                cam_ip = None
                print(" Rozlaczono z kamera IP")

    ret1, frame1 = cap_local.read()
    if cam_ip:
        ret2, frame2 = cam_ip.read()
    else:
        ret2, frame2 = False, None

    if not ret1:
        frame1 = np.zeros((CAM_H, CAM_W, 3), np.uint8)
    if not ret2:
        frame2 = np.zeros((CAM_H, CAM_W, 3), np.uint8)

    frame1 = cv2.resize(frame1, (CAM_W, CAM_H))
    frame2 = cv2.resize(frame2, (CAM_W, CAM_H))

    skeleton_color = (0, 255, 0)
    if trainer.cheat_left or trainer.cheat_right:
        skeleton_color = (0, 0, 255)

    frame1, results1 = detect_and_draw(frame1, pose_local, draw_color=skeleton_color)
    frame2, results2 = detect_and_draw(frame2, pose_ip, draw_color=skeleton_color)

    angles = {}

    if voice_control.started:
        if game_state.exercise_type == "biceps":
            angles = compute_angles_3d_biceps(
                results1, results2, focal=1.0, baseline=0.6
            )
            trainer.process_biceps(angles)
        elif game_state.exercise_type == "barki":
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
        game_state.exercise_type,
        voice_control.started,
        trainer,
        angles,
        workout_manager,
    )

    ui["btn_back"].draw(screen)

    return cam_ip, angles


def handle_history_state(
    screen, ui, events, game_state, db, font_big, font_med, font_small, CENTER_X
):
    draw_text_centered(screen, "Wybierz Trening", font_big, COLOR_ACCENT, CENTER_X, 50)
    if not game_state.session_buttons:
        raw_sessions = db.get_unique_sessions(game_state.user_id)
        start_y = 120
        for i, sess in enumerate(raw_sessions):
            session_id, session_date = sess
            label = f"Trening: {session_date[:-3]}"

            btn = Button(
                CENTER_X - 150,
                start_y + (i * 70),
                300,
                50,
                label,
                font_small,
                session_id,
            )
            game_state.session_buttons.append(btn)

    if not game_state.session_buttons:
        draw_text_centered(
            screen,
            "Brak zapisanych treningów.",
            font_med,
            COLOR_TEXT,
            CENTER_X,
            150,
        )
    else:
        for btn in game_state.session_buttons:
            btn.draw(screen)

    ui["btn_back"].draw(screen)

    for event in events:
        if ui["btn_back"].is_clicked(event):
            game_state.state = "MENU"
            game_state.session_buttons = []

        for btn in game_state.session_buttons:
            if btn.is_clicked(event):
                game_state.selected_session_id = btn.action_code
                game_state.state = "HISTORY_DETAILS"


def handle_history_details_state(
    screen, ui, events, game_state, db, font_big, font_med, font_small, CENTER_X
):
    draw_text_centered(
        screen, "Szczegóły Treningu", font_big, COLOR_ACCENT, CENTER_X, 50
    )

    rows = db.get_session_details(game_state.selected_session_id)

    biceps_data = [r for r in rows if r[0] == "biceps"]
    barki_data = [r for r in rows if r[0] == "barki"]

    y_pos = 110

    if biceps_data:
        draw_text_centered(
            screen, "--- BICEPS ---", font_med, COLOR_ACCENT, CENTER_X, y_pos
        )
        y_pos += 35
        headers = f"{'Seria':<6} {'Lewa':<6} {'Prawa':<6} {'Poprawność'}"
        draw_text_centered(
            screen, headers, font_small, (150, 150, 150), CENTER_X, y_pos
        )
        y_pos += 25

        for row in biceps_data:
            line = f"Nr {row[1]:<5} {row[2]:<8} {row[3]:<8} {row[4]:.1f}%"
            draw_text_centered(screen, line, font_small, COLOR_TEXT, CENTER_X, y_pos)
            y_pos += 25

        y_pos += 20

    if barki_data:
        draw_text_centered(
            screen, "--- BARKI ---", font_med, COLOR_ACCENT, CENTER_X, y_pos
        )
        y_pos += 35
        headers = f"{'Seria':<6} {'Lewa':<6} {'Prawa':<6} {'Poprawność'}"
        draw_text_centered(
            screen, headers, font_small, (150, 150, 150), CENTER_X, y_pos
        )
        y_pos += 25

        for row in barki_data:
            line = f"Nr {row[1]:<5} {row[2]:<8} {row[3]:<8} {row[4]:.1f}%"
            draw_text_centered(screen, line, font_small, COLOR_TEXT, CENTER_X, y_pos)
            y_pos += 25

    ui["btn_back"].draw(screen)

    for event in events:
        if ui["btn_back"].is_clicked(event):
            game_state.state = "HISTORY"


def handle_settings_state(
    screen, ui, events, game_state, db, workout_manager, font_big, font_med
):
    draw_text_centered(
        screen, "Konfiguracja Serii", font_big, COLOR_ACCENT, CENTER_X, 50
    )

    y_biceps = CENTER_Y - 30
    draw_text_centered(screen, "BICEPS", font_med, COLOR_TEXT, CENTER_X, y_biceps - 50)
    ui["btn_bic_m"].draw(screen)
    ui["btn_bic_p"].draw(screen)
    ui["inp_bic"].draw(screen)

    y_barki = CENTER_Y + 90
    draw_text_centered(screen, "BARKI", font_med, COLOR_TEXT, CENTER_X, y_barki - 50)
    ui["btn_bar_m"].draw(screen)
    ui["btn_bar_p"].draw(screen)
    ui["inp_bar"].draw(screen)

    ui["btn_back"].draw(screen)

    for event in events:
        if ui["btn_back"].is_clicked(event):
            db.save_user_settings(
                game_state.user_id,
                workout_manager.target_sets["biceps"],
                workout_manager.target_sets["barki"],
            )

            game_state.state = "MENU"

        if ui["btn_bic_m"].is_clicked(event):
            handle_settings_change(workout_manager, ui, font_big, "biceps", -1)

        if ui["btn_bic_p"].is_clicked(event):
            handle_settings_change(workout_manager, ui, font_big, "biceps", 1)

        if ui["btn_bar_m"].is_clicked(event):
            handle_settings_change(workout_manager, ui, font_big, "barki", -1)

        if ui["btn_bar_p"].is_clicked(event):
            handle_settings_change(workout_manager, ui, font_big, "barki", 1)
