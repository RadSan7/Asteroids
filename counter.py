import pygame
from constants import SCREEN_WIDTH

class Counter:
    def __init__(self):
        self.start_ticks = pygame.time.get_ticks()
        self.font = pygame.font.Font(None, 36)

    def reset(self):
        """Resetuje licznik do zera."""
        self.start_ticks = pygame.time.get_ticks()

    def get_time_text(self):
        """Zwraca aktualny czas w formacie 00:00 jako string."""
        elapsed_seconds = (pygame.time.get_ticks() - self.start_ticks) // 1000
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def draw(self, screen, width, height):
        timer_text = self.get_time_text()
        timer_surface = self.font.render(timer_text, True, (255, 255, 255))
        screen.blit(timer_surface, (width - timer_surface.get_width() - 10, 10))