import pygame
import random
from asteroid import Asteroid
from constants import *


class AsteroidField(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height):
        # Properly inherit and support containers if set
        if hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.spawn_timer = 0.0
        self.edges = [
            [pygame.Vector2(1, 0), lambda y: pygame.Vector2(-ASTEROID_MAX_RADIUS, y * self.screen_height)],
            [pygame.Vector2(-1, 0), lambda y: pygame.Vector2(self.screen_width + ASTEROID_MAX_RADIUS, y * self.screen_height)],
            [pygame.Vector2(0, 1), lambda x: pygame.Vector2(x * self.screen_width, -ASTEROID_MAX_RADIUS)],
            [pygame.Vector2(0, -1), lambda x: pygame.Vector2(x * self.screen_width, self.screen_height + ASTEROID_MAX_RADIUS)],
        ]

    def spawn(self, radius, position, velocity):
        asteroid = Asteroid(x=position.x, y=position.y, radius=radius)
        asteroid.velocity = velocity
        if hasattr(Asteroid, "containers"):
            for group in Asteroid.containers:
                group.add(asteroid)

    def update(self, dt):
        # Update screen dimensions from the current display
        display_info = pygame.display.get_surface()
        if display_info:
            self.screen_width = display_info.get_width()
            self.screen_height = display_info.get_height()

        self.spawn_timer += dt
        if self.spawn_timer > ASTEROID_SPAWN_RATE:
            self.spawn_timer = 0
            # Use up-to-date screen dimensions for edge functions
            self.edges = [
                [pygame.Vector2(1, 0), lambda y: pygame.Vector2(-ASTEROID_MAX_RADIUS, y * self.screen_height)],
                [pygame.Vector2(-1, 0), lambda y: pygame.Vector2(self.screen_width + ASTEROID_MAX_RADIUS, y * self.screen_height)],
                [pygame.Vector2(0, 1), lambda x: pygame.Vector2(x * self.screen_width, -ASTEROID_MAX_RADIUS)],
                [pygame.Vector2(0, -1), lambda x: pygame.Vector2(x * self.screen_width, self.screen_height + ASTEROID_MAX_RADIUS)],
            ]
            # Spawn multiple asteroids at once
            for _ in range(3):  # Spawn 3 asteroids at once
                edge = random.choice(self.edges)
                speed = random.randint(40, 100)
                velocity = edge[0] * speed
                velocity = velocity.rotate(random.randint(-30, 30))
                position = edge[1](random.uniform(0, 1))
                kind = random.randint(1, ASTEROID_KINDS)
                self.spawn(ASTEROID_MIN_RADIUS * kind, position, velocity)