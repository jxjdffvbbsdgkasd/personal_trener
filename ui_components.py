import pygame

COLOR_INACTIVE = pygame.Color("lightskyblue3")
COLOR_ACTIVE = pygame.Color("dodgerblue2")
COLOR_TEXT = (255, 255, 255)
COLOR_BUTTON_DEF = (70, 70, 80)
COLOR_BUTTON_HOVER = (100, 100, 110)


class InputBox:
    def __init__(self, x, y, w, h, font, text="", is_password=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.font = font
        self.txt_surface = self.font.render(text, True, COLOR_TEXT)
        self.active = False
        self.is_password = is_password

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Jeśli kliknięto w prostokąt
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return self.text  # Zwraca tekst po wciśnięciu Enter
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode

                # Renderowanie tekstu (gwiazdki jeśli hasło)
                display_text = "*" * len(self.text) if self.is_password else self.text
                self.txt_surface = self.font.render(display_text, True, COLOR_TEXT)
        return None

    def draw(self, screen):
        # Rysowanie tekstu
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 10))
        # Rysowanie ramki
        pygame.draw.rect(screen, self.color, self.rect, 2)

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
