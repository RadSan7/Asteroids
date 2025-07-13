import pygame
import random
from circleshape import CircleShape
from constants import *
from AsteroidField import *

class Asteroid(CircleShape):
    def __init__(self, x, y, radius):
        super().__init__(x, y, radius)
        self.rotation = 0

    def draw(self, screen):
        pygame.draw.circle(screen, "white", ((self.position.x), (self.position.y)), self.radius, 2)

    def update(self, dt):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        self.position += self.velocity * dt

    def split(self):
        self.kill()
        if self.radius <= ASTEROID_MIN_RADIUS:
            return
        self.angle = random.uniform(20, 50)
        self.new_radius = self.radius - ASTEROID_MIN_RADIUS
        v1 = self.velocity.rotate(self.angle)
        v2 = self.velocity.rotate(-self.angle)
        new_asteroid1 = Asteroid(self.position.x, self.position.y, self.new_radius)
        new_asteroid1.velocity = v1
        new_asteroid2 = Asteroid(self.position.x, self.position.y, self.new_radius * -1)
        new_asteroid2.velocity = v2
        