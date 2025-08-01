import pygame
from constants import *
from player import Player
from AsteroidField import *
from circleshape import CircleShape
from shot import Shot

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    
    Shot.containers = (shots, updatable, drawable)
    AsteroidField.containers = (updatable,)
    Player.containers = (drawable, updatable)
    Asteroid.containers = (asteroids, drawable, updatable)

    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

    asteroid_field = AsteroidField()
    dt = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            
        updatable.update(dt)
        for asteroid in asteroids:
            if CircleShape.collide(player, asteroid) == True:
                pygame.quit()
                print("Game Over")
                main()
            for shot in shots:
                if CircleShape.collide(shot, asteroid):
                    shot.kill()
                    asteroid.split()

        screen.fill((0, 0, 0))

        for obj in drawable:
            obj.draw(screen)

        pygame.display.flip()
        dt = clock.tick(60)/1000

if __name__ == "__main__":
    main()