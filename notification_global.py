from settings import *

notif = None

def render_text_with_outline(text, font, text_color=(255, 255, 255), outline_color=(0, 0, 0), outline_thickness=1, antialias=True):
    """
    Tworzy powierzchnię (Surface) z tekstem i obrysem.
    Można używać jako funkcję pomocniczą niezależnie od powiadomień.
    """
    text_surf = font.render(text, antialias, text_color)
    
    # Jeśli brak obrysu, zwracamy sam tekst
    if outline_thickness <= 0 or outline_color is None:
        return text_surf

    # Renderujemy obrys
    outline_surf = font.render(text, antialias, outline_color)
    
    # Obliczamy wymiary nowej powierzchni
    final_width = text_surf.get_width() + 2 * outline_thickness
    final_height = text_surf.get_height() + 2 * outline_thickness
    
    final_surface = pygame.Surface((final_width, final_height), pygame.SRCALPHA)
    
    # Rysujemy obrys przesunięty w każdym kierunku (prosta i skuteczna metoda)
    for dx in range(-outline_thickness, outline_thickness + 1):
        for dy in range(-outline_thickness, outline_thickness + 1):
            if dx == 0 and dy == 0: continue # Nie rysuj pod samym tekstem (opcjonalne)
            final_surface.blit(outline_surf, (outline_thickness + dx, outline_thickness + dy))
            
    # Na końcu nakładamy właściwy tekst na środek
    final_surface.blit(text_surf, (outline_thickness, outline_thickness))
    
    return final_surface

class NotificationManager:
    def __init__(self, screen_width, screen_height, default_font=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.active_notifications = []
        
        # zabezpieczenie jakby ktos nie podal czcionki
        if default_font is None:
            self.default_font = pygame.font.SysFont("Arial", 24)
        else:
            self.default_font = default_font

    def add_notification(self, message, duration_seconds=2.0, 
                         text_color=(255, 255, 255), bg_color=None,
                         position_topleft=None, position_center=None, pos_y_diff=0, 
                         font=None, outline_color=(0, 0, 0), outline_thickness=1):
        
        #czcionka
        use_font = font if font else self.default_font

        # 1. generowanie tekstu z obrysem
        text_surface = render_text_with_outline(
            message, use_font, text_color, outline_color, outline_thickness
        )

        # 2. tlo
        padding = 10
        if bg_color:
            bg_width = text_surface.get_width() + 2 * padding
            bg_height = text_surface.get_height() + 2 * padding
            final_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
            final_surface.fill(bg_color)
            
            text_rect = text_surface.get_rect(center=(bg_width // 2, bg_height // 2))
            final_surface.blit(text_surface, text_rect)
        else:
            # jak nie ma tla, to sam tekst
            final_surface = text_surface

        # 3. pozycjonowanie
        final_rect = final_surface.get_rect()
        
        if position_topleft:
            final_rect.topleft = position_topleft
        elif position_center:
            final_rect.center = position_center
        else:
            # srodek +- offset
            default_top_y = 100 + pos_y_diff
            final_rect.centerx = self.screen_width // 2
            final_rect.top = default_top_y

        # 4. czas trwania
        end_time = pygame.time.get_ticks() + (duration_seconds * 1000)

        # 5. lista notyfikacji
        self.active_notifications.append({
            "surface": final_surface,
            "rect": final_rect,
            "end_time": end_time
        })

    def update_and_draw(self, screen):
        """
        Tę funkcję wywołuj w głównej pętli rysowania (np. po narysowaniu tła).
        Usuwa przeterminowane powiadomienia i rysuje aktywne.
        """
        current_time = pygame.time.get_ticks()
        
        # Filtrujemy listę: zostawiamy tylko te, których czas jeszcze nie minął
        # [:] tworzy kopię, żebyśmy mogli bezpiecznie iterować, ale tutaj robimy list comprehension
        self.active_notifications = [n for n in self.active_notifications if n["end_time"] > current_time]

        # Rysowanie
        for note in self.active_notifications:
            screen.blit(note["surface"], note["rect"])
