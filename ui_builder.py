from ui_components import Button, InputBox
from settings import WIN_W


# przygotowuje elementy interfejsu i zwraca je w slowniku.
# porzadek w main zostaje
def build_ui(center_x, center_y, font_big, font_med, font_small):
    ui = {}

    # ekran logowania
    ui["input_login"] = InputBox(center_x - 100, center_y - 80, 200, 40, font_med)
    ui["input_pass"] = InputBox(
        center_x - 100, center_y - 20, 200, 40, font_med, is_password=True
    )
    ui["btn_login"] = Button(
        center_x - 100, center_y + 50, 200, 50, "Zaloguj", font_med, "LOGIN"
    )
    ui["btn_register"] = Button(
        center_x - 100, center_y + 110, 200, 50, "Rejestracja", font_med, "REGISTER"
    )

    # menu glowne
    ui["btn_start"] = Button(
        center_x - 150,
        center_y - 50,
        300,
        60,
        "Rozpocznij Trening",
        font_med,
        "GOTO_TRAIN",
    )
    ui["btn_settings"] = Button(
        center_x - 150,
        center_y + 110,
        300,
        60,
        "Dostosuj Trening",
        font_med,
        "GOTO_SETTINGS",
    )
    ui["btn_hist"] = Button(
        center_x - 150,
        center_y + 30,
        300,
        60,
        "Historia Treningów",
        font_med,
        "GOTO_HIST",
    )
    ui["btn_logout"] = Button(WIN_W - 120, 20, 100, 40, "Wyloguj", font_small, "LOGOUT")

    # menu dostosowyania treningu
    # biceps
    ui["btn_bic_m"] = Button(
        center_x - 150, center_y - 60, 60, 60, "-", font_big, "BIC_MINUS"
    )
    ui["btn_bic_p"] = Button(
        center_x + 90, center_y - 60, 60, 60, "+", font_big, "BIC_PLUS"
    )
    # pole tekstowe coby nie klikac +/-
    ui["inp_bic"] = InputBox(
        center_x - 30,
        center_y - 55,
        60,
        50,
        font_big,
        text="3",
        centered=True,
        max_chars=2,
    )

    # barki
    ui["btn_bar_m"] = Button(
        center_x - 150, center_y + 60, 60, 60, "-", font_big, "BAR_MINUS"
    )
    ui["btn_bar_p"] = Button(
        center_x + 90, center_y + 60, 60, 60, "+", font_big, "BAR_PLUS"
    )
    # tu tez pole tekstowe jak wyzej -..-
    ui["inp_bar"] = InputBox(
        center_x - 30,
        center_y + 65,
        60,
        50,
        font_big,
        text="3",
        centered=True,
        max_chars=2,
    )

    # przycisk powrotu
    ui["btn_back"] = Button(20, 20, 100, 40, "Powrót", font_small, "BACK")

    return ui
