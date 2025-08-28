import pygame
from circleshape import CircleShape
from constants import *
from shot import Shot

class Player(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_RADIUS)
        self.rotation = 0  # in degrees
        self.turbo_particle_timer = 0

    def triangle(self):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5
        a = self.position + forward * self.radius
        b = self.position - forward * self.radius - right
        c = self.position - forward * self.radius + right
        return [a, b, c]
    
    def draw(self, screen):
        pygame.draw.polygon(screen, "white", self.triangle(),2)

    def rotate(self, dt):
        self.rotation += PLAYER_TURN_SPEED * dt

    def move(self, dt, is_turbo=False):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        speed = PLAYER_SPEED * (PLAYER_TURBO_MULTIPLIER if is_turbo else 1)
        self.position += forward * speed * dt
        
        # Generate turbo particles
        if is_turbo:
            self.turbo_particle_timer += dt
            if self.turbo_particle_timer >= TURBO_PARTICLE_COOLDOWN:
                self.turbo_particle_timer = 0
                self.create_turbo_particles()

    def shoot(self):
        firing = Shot(self.position.x, self.position.y, SHOT_RADIUS, self.rotation)

    def create_turbo_particles(self):
        import random
        # Get triangle points
        points = self.triangle()
        base_center = (points[1] + points[2]) / 2  # Middle point of triangle base
        
        # Create multiple particles with random spread
        num_particles = random.randint(2, 4)  # Random number of particles per burst
        for _ in range(num_particles):
            # Random spread from the base of the triangle
            spread = random.uniform(-TURBO_PARTICLE_SPREAD, TURBO_PARTICLE_SPREAD)
            
            # Random offset from center of base
            offset = random.uniform(-self.radius/2, self.radius/2)
            offset_vector = pygame.Vector2(0, 1).rotate(self.rotation + 90) * offset
            spawn_pos = base_center + offset_vector
            
            # Create particle
            particle = Shot(spawn_pos.x, spawn_pos.y, SHOT_RADIUS/3, self.rotation + 180 + spread)
            
            # Random orange-red color variations
            r = random.randint(220, 255)
            g = random.randint(100, 165)
            b = random.randint(0, 50)
            particle.color = (r, g, b)
            
            # Set particle properties
            particle.speed = TURBO_PARTICLE_SPEED * random.uniform(0.8, 1.2)  # Random speed variation
            particle.lifetime = TURBO_PARTICLE_LIFETIME * random.uniform(0.8, 1.2)  # Random lifetime variation

    def update(self, dt):
        keys = pygame.key.get_pressed()
        is_turbo = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        if keys[pygame.K_w]:
            self.move(dt, is_turbo)
        
        if keys[pygame.K_s]:
            self.move(-dt, is_turbo)
    
        if keys[pygame.K_a]:
            self.rotate(-dt)
            
        if keys[pygame.K_d]:
            self.rotate(dt)

        if keys[pygame.K_SPACE]:
            self.shoot()
              