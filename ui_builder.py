from ui_components import Button, InputBox
from settings import WIN_W

def build_ui(center_x, center_y, font_big, font_med, font_small):
    ui = {}

    ui["input_login"] = InputBox(center_x - 125, center_y - 60, 250, 50, font_med, centered=True)

    ui["input_pass"] = InputBox(
        center_x - 125, center_y + 60, 250, 50, font_med, is_password=True, centered=True
    )

    ui["btn_login"] = Button(
        center_x - 125, center_y + 160, 250, 55, "Zaloguj się", font_med, "LOGIN"
    )

    ui["btn_register"] = Button(
        center_x - 125, center_y + 230, 250, 55, "Rejestracja", font_med, "REGISTER"
    )

    ui["btn_start"] = Button(
        center_x - 150, center_y - 50, 300, 60, "Rozpocznij trening", font_med, "GOTO_TRAIN",
    )
    ui["btn_settings"] = Button(
        center_x - 150, center_y + 110, 300, 60, "Konfiguracja Serii", font_med, "GOTO_SETTINGS",
    )
    ui["btn_hist"] = Button(
        center_x - 150, center_y + 30, 300, 60, "Twoje Wyniki", font_med, "GOTO_HIST",
    )
    ui["btn_logout"] = Button(WIN_W - 120, 20, 100, 40, "Wyloguj", font_small, "LOGOUT")

    # Konfiguracja
    ui["btn_bic_m"] = Button(center_x - 150, center_y - 60, 60, 60, "-", font_big, "BIC_MINUS")
    ui["btn_bic_p"] = Button(center_x + 90, center_y - 60, 60, 60, "+", font_big, "BIC_PLUS")
    ui["inp_bic"] = InputBox(center_x - 30, center_y - 55, 60, 50, font_big, text="3", centered=True, max_chars=2)
    ui["btn_bar_m"] = Button(center_x - 150, center_y + 60, 60, 60, "-", font_big, "BAR_MINUS")
    ui["btn_bar_p"] = Button(center_x + 90, center_y + 60, 60, 60, "+", font_big, "BAR_PLUS")
    ui["inp_bar"] = InputBox(center_x - 30, center_y + 65, 60, 50, font_big, text="3", centered=True, max_chars=2)
    ui["btn_back"] = Button(20, 20, 100, 40, "Powrót", font_small, "BACK")

    return ui
