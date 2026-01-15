import pygame

COLOR_INACTIVE = pygame.Color("lightskyblue3")
COLOR_ACTIVE = pygame.Color("dodgerblue2")
COLOR_TEXT = (255, 255, 255)
COLOR_BUTTON_DEF = (70, 70, 80)
COLOR_BUTTON_HOVER = (100, 100, 110)


class InputBox:
    def __init__(
        self,
        x,
        y,
        w,
        h,
        font,
        text="",
        is_password=False,
        centered=False,
        max_chars=None,
    ):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.font = font
        self.txt_surface = self.font.render(text, True, COLOR_TEXT)
        self.active = False
        self.is_password = is_password
        self.centered = centered
        self.max_chars = max_chars
        self.overwrite_mode = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # kliknieto w prostokąt
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
                # pole klikniete wiec nadpisz wartosc w nim nowowpisana
                if self.active:
                    self.overwrite_mode = True
            else:
                self.active = False
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                    self.color = COLOR_INACTIVE
                    return self.text

                elif event.key == pygame.K_BACKSPACE:
                    # kasowanie wszystkiego jak klikniemy okienko i backspace
                    if self.overwrite_mode:
                        self.text = ""
                        self.overwrite_mode = False
                    else:
                        self.text = self.text[:-1]

                else:
                    # wpisywanie znakow

                    # tryb zaznacz wszystko
                    if self.overwrite_mode:
                        self.text = (
                            event.unicode
                        )  # nowa cyfra zastepuje wszystko co bylo
                        self.overwrite_mode = (
                            False  # wylaczamy tryb po nadpisaniu juz jedna cyfra
                        )

                    # limit znaku == 2
                    elif self.max_chars and len(self.text) >= self.max_chars:
                        # limit osiagniety? ignoruj
                        return

                    # zwykle wpisuywanie
                    else:
                        self.text += event.unicode

                display_text = "*" * len(self.text) if self.is_password else self.text
                self.txt_surface = self.font.render(display_text, True, COLOR_TEXT)
        return None

    def draw(self, screen):
        # ramka
        pygame.draw.rect(screen, self.color, self.rect, 2)

        if self.centered:
            # srodek prostokata
            text_rect = self.txt_surface.get_rect(center=self.rect.center)
            screen.blit(self.txt_surface, text_rect)
        else:
            # od lewej standardowo chcemy
            screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 10))

    def get_text(self):
        return self.text


class Button:
    def __init__(self, x, y, w, h, text, font, action_code):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.action_code = action_code  # Kod akcji np. "LOGIN", "START", "HISTORY"
        self.color = COLOR_BUTTON_DEF

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        # Efekt po najechaniu myszką
        if self.rect.collidepoint(mouse_pos):
            self.color = COLOR_BUTTON_HOVER
        else:
            self.color = COLOR_BUTTON_DEF

        pygame.draw.rect(screen, self.color, self.rect, border_radius=10)

        text_surf = self.font.render(self.text, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Lewy przycisk
                if self.rect.collidepoint(event.pos):
                    return True
        return False
