import pygame
import sys


WIDTH, HEIGHT = 800, 400
FPS = 60


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
CYAN = (0, 255, 255)
RED = (255, 0, 0)
GRAY = (100, 100, 100)
GREEN = (0, 255, 0)
PURPLE = (255, 0, 255)
ORANGE = (255, 165, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PINK = (255, 192, 203)
BROWN = (165, 42, 42)

class Player:
    def __init__(self, color):
        self.size = 30
        self.rect = pygame.Rect(100, HEIGHT - 80, self.size, self.size)
        self.vel_y = 0
        self.jump_power = -12
        self.gravity = 0.8
        self.on_ground = False
        self.color = color
        self.flying = False

    def jump(self):
        if self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False

    def update(self, platforms):
        if self.flying:
            self.vel_y += 0.2  
            self.rect.y += self.vel_y
           
        else:
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

class Portal:
    def __init__(self, x, y, radius=20):
        self.x = x
        self.y = y
        self.radius = radius

    def update(self, speed):
        self.x -= speed

    def draw(self, screen):
        pygame.draw.circle(screen, PURPLE, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius, 2)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

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
    portals = []
    plane_obstacles = []
    back_portal = None
    player = Player(player_color)

    skin_options = [CYAN, GREEN, PURPLE, ORANGE, BLUE, YELLOW, PINK, BROWN]
    skin_names = ["1-Cyan", "2-Green", "3-Purple", "4-Orange", "5-Blue", "6-Yellow", "7-Pink", "8-Brown"]

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
                        portals = [Portal(1200, HEIGHT-100)]
                        player = Player(player_color)
                        state = "GAME"
                    elif event.key == pygame.K_2:
                        level_speed = 8
                        obstacles = [Obstacle(600, HEIGHT-80, 30, 30, "spike"), Obstacle(1000, HEIGHT-150, 150, 20, "block")]
                        portals = [Portal(1300, HEIGHT-120)]
                        player = Player(player_color)
                        state = "GAME"
                    elif event.key == pygame.K_3:
                        state = "SKINS"
                    elif event.key == pygame.K_4:
                        level_speed = 5
                        obstacles = [Obstacle(600, HEIGHT-80, 30, 30, "spike"), Obstacle(800, HEIGHT-130, 100, 20, "block"), Obstacle(1000, HEIGHT-80, 30, 30, "spike"), Obstacle(1200, HEIGHT-150, 150, 20, "block"), Obstacle(1400, HEIGHT-80, 30, 30, "spike"), Obstacle(1600, HEIGHT-120, 80, 20, "block"), Obstacle(1800, HEIGHT-80, 30, 30, "spike")]
                        portals = [Portal(2000, HEIGHT-100)]
                        player = Player(player_color)
                        state = "GAME"

            elif state == "SKINS":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1: player_color = CYAN
                    elif event.key == pygame.K_2: player_color = GREEN
                    elif event.key == pygame.K_3: player_color = PURPLE
                    elif event.key == pygame.K_4: player_color = ORANGE
                    elif event.key == pygame.K_5: player_color = BLUE
                    elif event.key == pygame.K_6: player_color = YELLOW
                    elif event.key == pygame.K_7: player_color = PINK
                    elif event.key == pygame.K_8: player_color = BROWN
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_ESCAPE]:
                        state = "MENU"

            elif state == "GAME":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        player.jump()
                    if event.key == pygame.K_ESCAPE:
                        state = "MENU"

            elif state == "PLANE":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = "MENU"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    state = "MENU"

            elif state == "FINISH":
                if event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_ESCAPE]:
                    state = "MENU"

        if state == "MENU":
            draw_text(screen, "GEOMETRY WORLD", 64, WIDTH//2, HEIGHT//4, player_color)
            draw_text(screen, "4 - Stereo Madness", 30, WIDTH//2, HEIGHT//2 + 30)
            draw_text(screen, "2 - Складний рівень", 30, WIDTH//2, HEIGHT//2 + 30)
            draw_text(screen, "3 - Обрати СКІН", 30, WIDTH//2, HEIGHT//2 + 80, 'YELLOW')

        elif state == "SKINS":
            draw_text(screen, "Вибір КОЛЬОРУ", 50, WIDTH//2, 80, WHITE)
            for i, name in enumerate(skin_names):
                draw_text(screen, name, 35, WIDTH//2, 150 + (i * 45), skin_options[i])
            draw_text(screen, "Натиснути ESC щоб вийти ", 20, WIDTH//2, HEIGHT - 40, GRAY)

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

            for portal in portals:
                portal.update(level_speed)
                portal.draw(screen)
                if player.rect.colliderect(portal.get_rect()):
                    plane_obstacles = [Obstacle(800, 50, 30, 30, "spike"), Obstacle(1000, 200, 30, 30, "spike"), Obstacle(1200, 100, 30, 30, "spike"), Obstacle(1400, 300, 30, 30, "spike")]
                    back_portal = Portal(600, 200, 25)
                    player.flying = True
                    player.rect.x = 100
                    player.rect.y = HEIGHT // 2
                    player.vel_y = 0
                    state = "PLANE"

        elif state == "PLANE":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                player.vel_y = -5
            player.update([])
            player.draw(screen)
            draw_text(screen, "остерігайся шипів!", 20, WIDTH//2, 130, RED)

            if back_portal:
                back_portal.update(0)
                back_portal.draw(screen)

            if back_portal and player.rect.colliderect(back_portal.get_rect()):
                player.flying = False
                player.rect.x = 100
                player.rect.y = HEIGHT - 80
                player.vel_y = 0
                state = "FINISH"

            for obs in plane_obstacles:
                obs.update(6)
                obs.draw(screen)
                if obs.type == "spike" and player.rect.colliderect(obs.rect):
                    player.flying = False
                    state = "MENU"
                if obs.rect.right < 0:
                    obs.rect.x += 1200

        elif state == "FINISH":
            draw_text(screen, "STEREO MADNESS COMPLETE!", 40, WIDTH//2, HEIGHT//2 - 20, GREEN)
            draw_text(screen, "Press ENTER or ESC to return", 25, WIDTH//2, HEIGHT//2 + 40, WHITE)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()