import pygame
from constants import *
from player import Player
from AsteroidField import *
from circleshape import CircleShape
from shot import Shot
from counter import Counter

def show_controls(screen, width, height):
    from player import Player
    try:
        font = pygame.font.SysFont("starwars", 100)
    except:
        font = pygame.font.Font(None, 74)
    small_font = pygame.font.Font(None, 36)

    back_button_width = 200
    back_button_height = 50
    back_button = pygame.Rect(width // 2 - back_button_width // 2, height - 120, back_button_width, back_button_height)

    menu_player = Player(width // 2 - 300, height // 2)
    menu_player.scale = 3
    menu_player.rotation = 160
    menu_asteroids = [
        Asteroid(width // 2 + 370, height // 2 - 50, 60),
        Asteroid(width // 2 + 450, height // 2, 80),
        Asteroid(width // 2 + 370, height // 2 + 50, 50)
    ]

    controls_lines = [
        "W - move forward",
        "S - move backward",
        "A - rotate left",
        "D - rotate right",
        "SPACE - shoot",
        "ESC - return to menu"
    ]

    blur_color = (50, 50, 50, 150)
    blur_surface = pygame.Surface((back_button_width + 20, back_button_height + 20), pygame.SRCALPHA)
    blur_surface.fill(blur_color)

    def draw_gradient_background(screen, top_color, bottom_color):
        width = screen.get_width()
        height = screen.get_height()
        for y in range(height):
            ratio = y / height
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (width, y))

    running = True
    while running:
        draw_gradient_background(screen, (0, 0, 30), (70, 130, 180))

        # Draw static ship and asteroids
        menu_player.draw(screen)
        for ast in menu_asteroids:
            ast.draw(screen)

        # Draw controls text
        box_width = 400
        box_height = 40 * len(controls_lines) + 40
        box_x = width // 2 - box_width // 2
        box_y = 150 - 20
        # Draw semi-transparent box
        controls_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        controls_box.fill((40, 40, 40, 180))
        screen.blit(controls_box, (box_x, box_y))
        for i, line in enumerate(controls_lines):
            text_surf = small_font.render(line, True, (255, 255, 255))
            screen.blit(text_surf, (width // 2 - text_surf.get_width() // 2, 150 + i * 40))

        # Draw back button
        screen.blit(blur_surface, (back_button.x - 10, back_button.y - 10))
        pygame.draw.rect(screen, (200, 200, 200), back_button)
        back_text = small_font.render("WSTECZ", True, (0, 0, 0))
        back_text_rect = back_text.get_rect(center=back_button.center)
        screen.blit(back_text, back_text_rect)

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            elif event.type == pygame.VIDEORESIZE:
                    width, height = event.w, event.h
                    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    running = False

def draw_gradient_background(screen, top_color, bottom_color):
    width = screen.get_width()
    height = screen.get_height()
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (width, y))

def load_high_score():
    try:
        with open('high_score.txt', 'r') as f:
            return int(f.read())
    except:
        return 0

def save_high_score(score):
    try:
        with open('high_score.txt', 'w') as f:
            f.write(str(score))
    except:
        pass

def format_time(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"

def show_menu(screen, width, height):
    try:
        font = pygame.font.SysFont("starwars", 100)
    except:
        font = pygame.font.Font(None, 74)
    small_font = pygame.font.Font(None, 50)
    title = font.render("ASTEROIDS", True, (255, 215, 0))
    
    # Load and display high score
    high_score = load_high_score()
    high_score_text = small_font.render("NAJLEPSZY CZAS", True, (255, 215, 0))
    high_score_value = small_font.render(format_time(high_score), True, (255, 255, 255))

    new_game_text = small_font.render("Nowa Gra", True, (0, 0, 0))
    controls_text = small_font.render("STEROWANIE", True, (0, 0, 0))
    exit_text = small_font.render("Wyjdź", True, (0, 0, 0))

    button_width = 250
    button_height = 60
    button_spacing = 80  # vertical spacing between buttons
    total_height = 3 * button_height + 2 * button_spacing
    start_y = height // 2 - total_height // 2

    new_game_button = pygame.Rect(width // 2 - button_width // 2, start_y, button_width, button_height)
    controls_button = pygame.Rect(width // 2 - button_width // 2, start_y + button_height + button_spacing, button_width, button_height)
    exit_button = pygame.Rect(width // 2 - button_width // 2, start_y + 2 * (button_height + button_spacing), button_width, button_height)

    blur_color = (50, 50, 50, 150)
    blur_surface = pygame.Surface((button_width + 20, button_height + 20), pygame.SRCALPHA)
    blur_surface.fill(blur_color)

    menu_player = Player(width // 2 - 300, height // 2)
    menu_player.scale = 3
    menu_player.rotation = 160
    menu_asteroids = [
        Asteroid(width // 2 + 370, height // 2 - 50, 60),
        Asteroid(width // 2 + 450, height // 2, 80),
        Asteroid(width // 2 + 370, height // 2 + 50, 50)
    ]


    while True:
        draw_gradient_background(screen, (0, 0, 30), (70, 130, 180))
        screen.blit(title, (width // 2 - title.get_width() // 2, 100))

        # Draw high score box
        score_box_width = 300
        score_box_height = 120
        score_box_x = width // 4 - score_box_width // 2
        score_box_y = height // 2 - score_box_height // 2
        
        # Draw semi-transparent box for high score
        score_box = pygame.Surface((score_box_width, score_box_height), pygame.SRCALPHA)
        score_box.fill((40, 40, 40, 180))
        screen.blit(score_box, (score_box_x, score_box_y))
        
        # Draw high score text
        screen.blit(high_score_text, (score_box_x + score_box_width//2 - high_score_text.get_width()//2, 
                                    score_box_y + 20))
        screen.blit(high_score_value, (score_box_x + score_box_width//2 - high_score_value.get_width()//2, 
                                     score_box_y + 70))

        # Recalculate button positions for horizontal centering
        new_game_button.x = width // 2 - new_game_button.width // 2
        controls_button.x = width // 2 - controls_button.width // 2
        exit_button.x = width // 2 - exit_button.width // 2

        screen.blit(blur_surface, (new_game_button.x - 10, new_game_button.y - 10))
        screen.blit(blur_surface, (controls_button.x - 10, controls_button.y - 10))
        screen.blit(blur_surface, (exit_button.x - 10, exit_button.y - 10))

        pygame.draw.rect(screen, (200, 200, 200), new_game_button)
        pygame.draw.rect(screen, (200, 200, 200), controls_button)
        pygame.draw.rect(screen, (200, 200, 200), exit_button)

        # Text
        screen.blit(new_game_text, new_game_text.get_rect(center=new_game_button.center))
        screen.blit(controls_text, controls_text.get_rect(center=controls_button.center))
        screen.blit(exit_text, exit_text.get_rect(center=exit_button.center))

        menu_player.draw(screen)
        for ast in menu_asteroids:
            ast.draw(screen)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            elif event.type == pygame.VIDEORESIZE:
                width, height = event.w, event.h
                screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if new_game_button.collidepoint(event.pos):
                    return "new_game"
                if controls_button.collidepoint(event.pos):
                    show_controls(screen, width, height)
                if exit_button.collidepoint(event.pos):
                    pygame.quit()
                    return "quit"

def main(width=SCREEN_WIDTH, height=SCREEN_HEIGHT):
    pygame.init()
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    while True:
        choice = show_menu(screen, width, height)
        if choice == "quit":
            return

        updatable = pygame.sprite.Group()
        drawable = pygame.sprite.Group()
        asteroids = pygame.sprite.Group()
        shots = pygame.sprite.Group()
        
        Shot.containers = (shots, updatable, drawable)
        AsteroidField.containers = (updatable,)
        Player.containers = (drawable, updatable)
        Asteroid.containers = (asteroids, drawable, updatable)

        # Ensure new instance of Player for each new game
        player = Player(width / 2, height / 2)
        counter = Counter()
        asteroid_field = AsteroidField(width, height)
        dt = 0

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.VIDEORESIZE:
                    width, height = event.w, event.h
                    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Save high score when exiting with ESC
                        current_time = (pygame.time.get_ticks() - counter.start_ticks) // 1000
                        high_score = load_high_score()
                        if current_time > high_score:
                            save_high_score(current_time)
                        running = False
                        break
            if not running:
                break
            updatable.update(dt)
            for asteroid in asteroids:
                if CircleShape.collide(player, asteroid):
                    # Get current time and update high score if needed
                    current_time = (pygame.time.get_ticks() - counter.start_ticks) // 1000
                    high_score = load_high_score()
                    if current_time > high_score:
                        save_high_score(current_time)
                    print("Game Over")
                    running = False
                    main(width, height)  # zachowuje aktualny rozmiar okna
                for shot in shots:
                    if CircleShape.collide(shot, asteroid):
                        shot.kill()
                        asteroid.split()

            draw_gradient_background(screen, (0, 0, 30), (70, 130, 180))
            counter.draw(screen, width, height)
            for obj in drawable:
                obj.draw(screen)

            pygame.display.flip()
            dt = clock.tick(60)/1000

if __name__ == "__main__":
    main()