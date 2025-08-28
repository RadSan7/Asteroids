import pygame
from circleshape import CircleShape
from constants import *

class Shot(CircleShape):
    def __init__(self, x, y, radius, rotation):
        super().__init__(x, y, radius)
        self.rotation = rotation
        self.color = "white"
        self.creation_time = pygame.time.get_ticks() / 1000.0
        self.lifetime = None
        self.speed = PLAYER_SHOT_SPEED

    def draw(self, screen):
        if self.lifetime is not None:
            # Fade out the particle as it reaches end of life
            current_time = pygame.time.get_ticks() / 1000.0
            age = current_time - self.creation_time
            if age >= self.lifetime:
                self.kill()
                return
            # Make particle smaller and more transparent as it ages
            radius = self.radius * (1 - age/self.lifetime)
            pygame.draw.circle(screen, self.color, ((self.position.x), (self.position.y)), radius, 0)  # Filled circle for particles
        else:
            pygame.draw.circle(screen, self.color, ((self.position.x), (self.position.y)), self.radius, 2)  # Normal shots

    def update(self, dt):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        self.position += forward * self.speed * dt

    
        