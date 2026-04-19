import pygame
import sys

# Настройки окна
WIDTH, HEIGHT = 800, 400
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CYAN = (0, 255, 255)
RED = (255, 0, 0)
GRAY = (100, 100, 100)
GREEN = (0, 255, 0)
PURPLE = (255, 0, 255)
ORANGE = (255, 165, 0)

class Player:
    def __init__(self, color):
        self.size = 30
        self.rect = pygame.Rect(100, HEIGHT - 80, self.size, self.size)
        self.vel_y = 0
        self.jump_power = -12
        self.gravity = 0.8
        self.on_ground = False
        self.color = color

    def jump(self):
        if self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False

    def update(self, platforms):
        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        if self.rect.bottom > HEIGHT - 50:
            self.rect.bottom = HEIGHT - 50
            self.vel_y = 0
            self.on_ground = True

        for plat in platforms:
            if self.rect.colliderect(plat):
                if self.vel_y > 0 and self.rect.bottom <= plat.bottom + 10:
                    self.rect.bottom = plat.top
                    self.vel_y = 0
                    self.on_ground = True

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)

class Obstacle:
    def __init__(self, x, y, width, height, type="block"):
        self.rect = pygame.Rect(x, y, width, height)
        self.type = type

    def update(self, speed):
        self.rect.x -= speed

    def draw(self, screen):
        if self.type == "block":
            pygame.draw.rect(screen, GRAY, self.rect)
            pygame.draw.rect(screen, WHITE, self.rect, 1)
        elif self.type == "spike":
            points = [(self.rect.left, self.rect.bottom), (self.rect.right, self.rect.bottom), (self.rect.centerx, self.rect.top)]
            pygame.draw.polygon(screen, RED, points)

def draw_text(screen, text, size, x, y, color=WHITE):
    font = pygame.font.SysFont("Arial", size, bold=True)
    img = font.render(text, True, color)
    rect = img.get_rect(center=(x, y))
    screen.blit(img, rect)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Geometry World")
    clock = pygame.time.Clock()

    state = "MENU"
    player_color = CYAN
    level_speed = 5
    obstacles = []
    player = Player(player_color)

    # Список доступных цветов для скинов
    skin_options = [CYAN, GREEN, PURPLE, ORANGE]
    skin_names = ["1-Cyan", "2-Green", "3-Purple", "4-Orange"]

    while True:
        screen.fill(BLACK)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if state == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        level_speed = 5
                        obstacles = [Obstacle(600, HEIGHT-80, 30, 30, "spike"), Obstacle(900, HEIGHT-130, 100, 20, "block")]
                        player = Player(player_color)
                        state = "GAME"
                    elif event.key == pygame.K_2:
                        level_speed = 8
                        obstacles = [Obstacle(600, HEIGHT-80, 30, 30, "spike"), Obstacle(1000, HEIGHT-150, 150, 20, "block")]
                        player = Player(player_color)
                        state = "GAME"
                    elif event.key == pygame.K_3:
                        state = "SKINS"

            elif state == "SKINS":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1: player_color = CYAN
                    if event.key == pygame.K_2: player_color = GREEN
                    if event.key == pygame.K_3: player_color = PURPLE
                    if event.key == pygame.K_4: player_color = ORANGE
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_ESCAPE]:
                        state = "MENU"

            elif state == "GAME":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        player.jump()
                    if event.key == pygame.K_ESCAPE:
                        state = "MENU"

        if state == "MENU":
            draw_text(screen, "GEOMETRY WORLD", 64, WIDTH//2, HEIGHT//4, player_color)
            draw_text(screen, "1 - Легкий уровень", 30, WIDTH//2, HEIGHT//2 - 20)
            draw_text(screen, "2 - Сложный уровень", 30, WIDTH//2, HEIGHT//2 + 30)
            draw_text(screen, "3 - Выбрать СКИН", 30, WIDTH//2, HEIGHT//2 + 80, 'YELLOW')

        elif state == "SKINS":
            draw_text(screen, "ВЫБЕРИ ЦВЕТ", 50, WIDTH//2, 80, WHITE)
            for i, name in enumerate(skin_names):
                draw_text(screen, name, 35, WIDTH//2, 150 + (i * 45), skin_options[i])
            draw_text(screen, "Нажми цифру или ESC для выхода", 20, WIDTH//2, HEIGHT - 40, GRAY)

        elif state == "GAME":
            pygame.draw.line(screen, WHITE, (0, HEIGHT - 50), (WIDTH, HEIGHT - 50), 2)
            platforms = [o.rect for o in obstacles if o.type == "block"]
            player.update(platforms)
            player.draw(screen)

            for obs in obstacles:
                obs.update(level_speed)
                obs.draw(screen)
                if obs.type == "spike" and player.rect.colliderect(obs.rect):
                    state = "MENU"
                if obs.rect.right < 0:
                    obs.rect.x += 1000 

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()