import pygame
import sys
import math
import random

WIDTH, HEIGHT = 800, 450
FPS = 60
GROUND_Y = HEIGHT - 60

WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0)
CYAN    = (0,   255, 255)
RED     = (255, 0,   0)
GRAY    = (100, 100, 100)
GREEN   = (0,   220, 80)
PURPLE  = (180, 0,   255)
ORANGE  = (255, 140, 0)
BLUE    = (50,  120, 255)
YELLOW  = (255, 230, 0)
PINK    = (255, 100, 180)
BROWN   = (160, 80,  40)
DARK    = (15,  10,  30)
NEON_G  = (0,   255, 150)

SKIN_COLORS = [CYAN, GREEN, PURPLE, ORANGE, BLUE, YELLOW, PINK, BROWN]
SKIN_NAMES  = ["Cyan","Green","Purple","Orange","Blue","Yellow","Pink","Brown"]

# ── helpers ───────────────────────────────────────────────────────────────────

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def draw_text(screen, text, size, x, y, color=WHITE, center=True):
    font = pygame.font.SysFont("Arial", size, bold=True)
    img  = font.render(text, True, color)
    rect = img.get_rect(center=(x, y)) if center else img.get_rect(topleft=(x, y))
    screen.blit(img, rect)

def glow_circle(surf, color, pos, radius, alpha=80):
    tmp = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    pygame.draw.circle(tmp, (*color, alpha), (radius, radius), radius)
    surf.blit(tmp, (pos[0]-radius, pos[1]-radius))

# ── Player ────────────────────────────────────────────────────────────────────

class Player:
    MODES = ["cube", "ship", "ball", "wave", "ufo"]

    def __init__(self, color=CYAN):
        self.color   = color
        self.size    = 28
        self.rect    = pygame.Rect(120, GROUND_Y - self.size, self.size, self.size)
        self.vel_y   = 0
        self.vel_x   = 0       # horizontal velocity
        self.on_ground = False
        self.angle   = 0
        self.mode    = "cube"   # cube / ship / ball / wave / ufo
        self.gravity = 1
        self.alive   = True
        self.trail   = []
        # ship / ufo boost
        self._holding = False
        self._moving_left = False   # track left/right input
        self._moving_right = False

    # ── input ──────────────────────────────────────────────────────────────────
    def press(self):
        if not self.alive: return
        if self.mode == "cube":
            if self.on_ground:
                self.vel_y = -14
                self.on_ground = False
        elif self.mode == "ball":
            self.gravity *= -1
            self.vel_y = -6 * self.gravity
        elif self.mode == "ufo":
            self.vel_y = -7
        elif self.mode in ("ship", "wave"):
            self._holding = True

    def release(self):
        self._holding = False

    def move_left(self, enable=True):
        self._moving_left = enable

    def move_right(self, enable=True):
        self._moving_right = enable

    # ── update ─────────────────────────────────────────────────────────────────
    def update(self, platforms, slope_rects):
        if not self.alive: return

        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 18:
            self.trail.pop(0)

        # ---- horizontal movement --------------------------------------------------
        acceleration = 0.8
        max_speed = 7
        if self._moving_left:
            self.vel_x = max(-max_speed, self.vel_x - acceleration)
        elif self._moving_right:
            self.vel_x = min(max_speed, self.vel_x + acceleration)
        else:
            # friction when no input
            if abs(self.vel_x) > 0.1:
                self.vel_x *= 0.85
            else:
                self.vel_x = 0
        
        self.rect.x += int(self.vel_x)
        # keep player in bounds
        self.rect.x = max(20, min(WIDTH - 40, self.rect.x))

        g = 0.75 * self.gravity

        if self.mode == "cube":
            self.vel_y += g
            self.angle -= 6 if not self.on_ground else 0
        elif self.mode == "ship":
            if self._holding: self.vel_y -= 0.9
            else:             self.vel_y += 0.6
            self.vel_y = max(-9, min(9, self.vel_y))
            self.angle = -self.vel_y * 3
        elif self.mode == "ball":
            self.vel_y += g
            self.angle -= 8
        elif self.mode == "wave":
            self.vel_y = -8 if self._holding else 8
            self.angle = -45 if self._holding else 45
        elif self.mode == "ufo":
            self.vel_y += 0.5
            self.vel_y = max(-8, min(8, self.vel_y))

        self.rect.y += int(self.vel_y)

        # ---- ground / ceiling ------------------------------------------------
        top_limit = 0
        bot_limit = GROUND_Y - self.size

        if self.mode == "ball" and self.gravity < 0:
            # inverted gravity → ceiling is floor
            if self.rect.top < top_limit:
                self.rect.top = top_limit
                self.vel_y = 0
                self.on_ground = True
        else:
            if self.rect.bottom >= GROUND_Y:
                self.rect.bottom = GROUND_Y
                self.vel_y = 0
                self.on_ground = True
            else:
                self.on_ground = False
            if self.rect.top < top_limit:
                self.rect.top = top_limit
                self.vel_y = 2

        # ---- platforms -------------------------------------------------------
        for plat in platforms:
            if self.rect.colliderect(plat):
                if self.vel_y > 0 and self.rect.bottom - self.vel_y <= plat.top + 4:
                    self.rect.bottom = plat.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0 and self.rect.top - self.vel_y >= plat.bottom - 4:
                    self.rect.top = plat.bottom
                    self.vel_y = 2

    # ── draw ───────────────────────────────────────────────────────────────────
    def draw(self, screen):
        # trail
        for i, pos in enumerate(self.trail):
            alpha = int(200 * i / len(self.trail))
            r = max(2, int(self.size * 0.35 * i / len(self.trail)))
            glow_circle(screen, self.color, pos, r, alpha)

        # body (rotated)
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        if self.mode == "cube":
            pygame.draw.rect(surf, self.color, (0, 0, self.size, self.size), border_radius=4)
            pygame.draw.rect(surf, WHITE,      (0, 0, self.size, self.size), 2, border_radius=4)
            # inner cross
            pygame.draw.line(surf, WHITE, (4,4), (self.size-4, self.size-4), 1)
            pygame.draw.line(surf, WHITE, (self.size-4,4), (4, self.size-4), 1)
        elif self.mode == "ship":
            pts = [(0, self.size//2),(self.size, 6),(self.size, self.size-6)]
            pygame.draw.polygon(surf, self.color, pts)
            pygame.draw.polygon(surf, WHITE, pts, 2)
        elif self.mode == "ball":
            pygame.draw.circle(surf, self.color, (self.size//2, self.size//2), self.size//2-1)
            pygame.draw.circle(surf, WHITE,      (self.size//2, self.size//2), self.size//2-1, 2)
            pygame.draw.circle(surf, WHITE,      (self.size//2, self.size//2), self.size//4)
        elif self.mode == "wave":
            pts = [(0, self.size),(self.size//2, 0),(self.size, self.size//2)]
            pygame.draw.polygon(surf, self.color, pts)
            pygame.draw.polygon(surf, WHITE, pts, 2)
        elif self.mode == "ufo":
            pygame.draw.ellipse(surf, self.color, (0, self.size//3, self.size, self.size//2))
            pygame.draw.ellipse(surf, WHITE,      (0, self.size//3, self.size, self.size//2), 2)
            pygame.draw.ellipse(surf, WHITE, (self.size//4, 2, self.size//2, self.size//3))

        rot_surf = pygame.transform.rotate(surf, self.angle % 360)
        rot_rect = rot_surf.get_rect(center=self.rect.center)
        screen.blit(rot_surf, rot_rect)

# ── Obstacle ──────────────────────────────────────────────────────────────────

class Obstacle:
    def __init__(self, x, y, w, h, otype="block", color=None):
        self.rect  = pygame.Rect(x, y, w, h)
        self.otype = otype
        self.color = color

    def update(self, spd):
        self.rect.x -= spd

    def draw(self, screen):
        c = self.color
        if self.otype == "block":
            col = c or (80, 80, 120)
            pygame.draw.rect(screen, col, self.rect, border_radius=3)
            pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=3)
        elif self.otype == "spike":
            col = c or RED
            pts = [(self.rect.left,  self.rect.bottom),
                   (self.rect.right, self.rect.bottom),
                   (self.rect.centerx, self.rect.top)]
            pygame.draw.polygon(screen, col, pts)
            pygame.draw.polygon(screen, WHITE, pts, 1)
        elif self.otype == "spike_ceil":
            col = c or RED
            pts = [(self.rect.left,  self.rect.top),
                   (self.rect.right, self.rect.top),
                   (self.rect.centerx, self.rect.bottom)]
            pygame.draw.polygon(screen, col, pts)
            pygame.draw.polygon(screen, WHITE, pts, 1)
        elif self.otype == "orb":
            col = c or YELLOW
            cx, cy = self.rect.center
            r = self.rect.width // 2
            pygame.draw.circle(screen, col, (cx, cy), r)
            pygame.draw.circle(screen, WHITE, (cx, cy), r, 2)
        elif self.otype == "pad":
            col = c or NEON_G
            pygame.draw.rect(screen, col, self.rect, border_radius=4)
            pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=4)
        elif self.otype == "portal":
            col1 = c or PURPLE
            col2 = (255, 80, 0) if col1 == PURPLE else WHITE
            cx, cy = self.rect.center
            r = self.rect.width // 2
            pygame.draw.circle(screen, col1, (cx, cy), r)
            pygame.draw.circle(screen, col2, (cx, cy), r, 3)
            draw_text(screen, self.tag if hasattr(self, 'tag') else "?", 10, cx, cy, WHITE)

    def collide_kill(self):
        return self.otype in ("spike", "spike_ceil", "block")

    def is_platform(self):
        return self.otype in ("block", "pad")

# ── Coin ──────────────────────────────────────────────────────────────────────

class Coin:
    def __init__(self, x, y):
        self.rect      = pygame.Rect(x, y, 18, 18)
        self.collected = False
        self.angle     = random.uniform(0, 360)

    def update(self, spd):
        self.rect.x -= spd
        self.angle  += 3

    def draw(self, screen):
        if self.collected: return
        cx, cy = self.rect.center
        r = 9
        glow_circle(screen, YELLOW, (cx, cy), r+4, 60)
        pygame.draw.circle(screen, YELLOW, (cx, cy), r)
        pygame.draw.circle(screen, WHITE,  (cx, cy), r, 2)
        # $ sign
        draw_text(screen, "*", 12, cx, cy, WHITE)

# ── Background ────────────────────────────────────────────────────────────────

class Background:
    def __init__(self, col1=(15,10,30), col2=(30,0,60)):
        self.col1   = col1
        self.col2   = col2
        self.stars  = [(random.randint(0,WIDTH), random.randint(0,HEIGHT-60),
                        random.uniform(0.5,1.5), random.uniform(0.3,1.0)) for _ in range(80)]
        self.offset = 0
        self.pulse  = 0
        self.lines  = []   # scrolling bg lines

    def set_colors(self, c1, c2):
        self.col1 = c1
        self.col2 = c2

    def update(self, spd, beat=False):
        self.offset += spd * 0.3
        if beat:
            self.pulse = 1.0
        if self.pulse > 0:
            self.pulse -= 0.05

    def draw(self, screen):
        # gradient sky
        for y in range(HEIGHT - 60):
            t = y / (HEIGHT - 60)
            p = self.pulse * 0.25
            c = lerp_color(
                tuple(min(255, int(self.col1[i] + self.col1[i]*p)) for i in range(3)),
                tuple(min(255, int(self.col2[i] + self.col2[i]*p)) for i in range(3)),
                t)
            pygame.draw.line(screen, c, (0, y), (WIDTH, y))

        # stars
        for sx, sy, br, sp in self.stars:
            rx = (sx - self.offset * sp * 0.15) % WIDTH
            a  = int(180 + 60 * math.sin(self.offset * 0.02 + sx))
            r  = max(1, int(br * 1.5))
            glow_circle(screen, WHITE, (int(rx), int(sy)), r, a)

        # ground
        pygame.draw.rect(screen, (25, 15, 50), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(screen, CYAN, (0, GROUND_Y), (WIDTH, GROUND_Y), 2)

# ── Level builder ─────────────────────────────────────────────────────────────
#
# Each entry: (x_from_start, Obstacle/Coin/dict)
# "portal" objects carry extra keys: mode, bg_cols

def make_level_stereo():
    """Stereo Madness — medium difficulty, all mechanics introduced."""
    spd = 6
    objs = []
    coins= []

    def b(x,y,w,h,c=None): return Obstacle(x,y,w,h,"block",c)
    def sp(x,y):            return Obstacle(x, GROUND_Y-30, 30,30,"spike")
    def sc(x,y):            return Obstacle(x,y,30,30,"spike_ceil")
    def orb(x,y,c=YELLOW):  return Obstacle(x,y,24,24,"orb",c)
    def pad(x,y):           return Obstacle(x, GROUND_Y-8, 60,8,"pad")
    def portal(x, mode, bg1=(15,10,30), bg2=(30,0,60)):
        o = Obstacle(x, GROUND_Y-80, 30,80,"portal")
        o.tag  = mode[0].upper()
        o.mode = mode
        o.bg   = (bg1, bg2)
        return o
    def coin(x,y): return ("coin", x, y)

    # ── Cube section ──────────────────────────────────────────────────────────
    objs += [sp(600,0), sp(700,0), b(800, GROUND_Y-40, 40,40), sp(900,0)]
    objs += [sp(1000,0), b(1100,GROUND_Y-40,40,40), b(1140,GROUND_Y-80,40,40)]
    objs += [sp(1250,0), sp(1310,0)]
    objs += [orb(1420, GROUND_Y-120)]          # yellow orb → double jump
    objs += [b(1500, GROUND_Y-40,40,40), sp(1600,0)]
    coins+= [coin(650, GROUND_Y-60), coin(1420, GROUND_Y-150)]

    # ── Ship portal ───────────────────────────────────────────────────────────
    objs += [portal(1750,"ship", (5,5,25),(20,0,60))]
    objs += [b(1900,20,WIDTH,20), b(1900,GROUND_Y-20,WIDTH,20)]  # ceiling/floor tunnel
    objs += [b(2050, 80,20,140), b(2150,GROUND_Y-160,20,120)]
    objs += [b(2300, 60,20,180), b(2400,GROUND_Y-140,20,100)]
    coins+= [coin(2100, HEIGHT//2 - 10)]

    # ── Ball portal ───────────────────────────────────────────────────────────
    objs += [portal(2600,"ball", (5,20,10),(0,40,20))]
    objs += [sp(2750,0), orb(2850,GROUND_Y-100,(255,80,200))]  # pink orb → reverse grav
    objs += [sp(2980,0), sp(3060,0), b(3150,GROUND_Y-50,50,50)]
    coins+= [coin(2980, GROUND_Y-60)]

    # ── Wave portal ───────────────────────────────────────────────────────────
    objs += [portal(3350,"wave",(25,5,5),(60,0,0))]
    # narrow wave corridor
    objs += [b(3500,0,WIDTH,70), b(3500,GROUND_Y-70,WIDTH,70)]  # tight tunnel
    objs += [b(3700,70,20,80), b(3800,GROUND_Y-150,20,80)]
    objs += [b(3950,70,20,100),b(4050,GROUND_Y-170,20,100)]

    # ── UFO portal ────────────────────────────────────────────────────────────
    objs += [portal(4200,"ufo",(5,10,30),(0,20,70))]
    objs += [sp(4400,0),orb(4500,GROUND_Y-130,CYAN),sp(4650,0)]
    objs += [b(4800,GROUND_Y-60,60,60),sp(4920,0),sp(4980,0)]
    coins+= [coin(4500, GROUND_Y-160)]

    # ── Cube portal (back) ────────────────────────────────────────────────────
    objs += [portal(5100,"cube",(15,10,30),(30,0,60))]
    objs += [sp(5300,0),sp(5380,0),b(5480,GROUND_Y-50,50,50)]
    objs += [sp(5600,0),orb(5700,GROUND_Y-120),sp(5850,0)]
    objs += [sp(5950,0),sp(6030,0),b(6130,GROUND_Y-40,40,40)]
    coins+= [coin(5700, GROUND_Y-150)]

    # ── Final sprint ──────────────────────────────────────────────────────────
    for i in range(6):
        objs += [sp(6400 + i*120, 0)]
    objs += [b(7200, GROUND_Y-40,40,40), sp(7300,0)]

    return spd, objs, coins


def make_level_back_on_track():
    """Back on Track — easier, longer pure-cube level."""
    spd = 5
    objs = []
    coins= []

    def b(x,y,w,h): return Obstacle(x,y,w,h,"block")
    def sp(x,y=0):  return Obstacle(x, GROUND_Y-30, 30,30,"spike")
    def orb(x,y):   return Obstacle(x,y,24,24,"orb",YELLOW)
    def coin(x,y):  return ("coin",x,y)

    # gentle intro
    objs += [sp(500), sp(650), b(780,GROUND_Y-40,40,40), sp(870)]
    objs += [sp(1000), b(1100,GROUND_Y-40,80,40), sp(1230), sp(1310)]
    objs += [orb(1450, GROUND_Y-110), b(1540,GROUND_Y-40,40,40)]
    objs += [sp(1680), sp(1760), sp(1840)]
    coins+= [coin(650, GROUND_Y-55), coin(1450, GROUND_Y-140)]

    objs += [b(2000,GROUND_Y-80,40,80), b(2040,GROUND_Y-40,40,40)]
    objs += [sp(2150), orb(2300,GROUND_Y-120), sp(2450), sp(2530)]
    objs += [b(2650,GROUND_Y-60,60,60), sp(2770), sp(2850)]
    coins+= [coin(2300, GROUND_Y-150)]

    objs += [sp(3000),sp(3080),sp(3160)]
    objs += [b(3300,GROUND_Y-40,40,40),b(3340,GROUND_Y-80,40,40)]
    objs += [orb(3500,GROUND_Y-120),sp(3650),sp(3730)]
    coins+= [coin(3500, GROUND_Y-150)]

    for i in range(5):
        objs += [sp(4000+i*100)]
    objs += [b(4600,GROUND_Y-40,40,40),sp(4700),sp(4780)]

    return spd, objs, coins


def make_level_dry_out():
    """Dry Out — medium, introduces ship heavily."""
    spd = 7
    objs = []
    coins= []

    def b(x,y,w,h,c=None): return Obstacle(x,y,w,h,"block",c)
    def sp(x):  return Obstacle(x, GROUND_Y-30,30,30,"spike")
    def sc(x,y):return Obstacle(x,y,30,30,"spike_ceil")
    def orb(x,y,c=YELLOW): return Obstacle(x,y,24,24,"orb",c)
    def portal(x,mode,bg1=(15,10,30),bg2=(30,0,60)):
        o=Obstacle(x,GROUND_Y-80,30,80,"portal"); o.tag=mode[0].upper(); o.mode=mode; o.bg=(bg1,bg2); return o
    def coin(x,y): return ("coin",x,y)

    objs+=[sp(500),sp(600),b(700,GROUND_Y-40,40,40),sp(800)]
    objs+=[portal(1000,"ship",(5,15,5),(0,40,10))]
    objs+=[b(1150,0,20,120),b(1150,GROUND_Y-120,20,120)]
    objs+=[b(1350,0,20,160),b(1350,GROUND_Y-100,20,100)]
    objs+=[b(1550,0,20,100),b(1550,GROUND_Y-170,20,170)]
    coins+=[coin(1250,HEIGHT//2-10)]

    objs+=[portal(1800,"cube",(5,5,20),(20,0,50))]
    objs+=[sp(1950),sp(2050),orb(2200,GROUND_Y-120),sp(2350)]
    objs+=[b(2500,GROUND_Y-60,60,60),sp(2620),sp(2700)]
    coins+=[coin(2200,GROUND_Y-150)]

    objs+=[portal(2900,"ship",(5,15,5),(0,40,10))]
    objs+=[b(3050,0,20,80),b(3050,GROUND_Y-80,20,80)]
    objs+=[b(3250,0,20,120),b(3250,GROUND_Y-110,20,110)]
    objs+=[b(3450,0,20,60),b(3450,GROUND_Y-140,20,140)]
    coins+=[coin(3150,HEIGHT//2-10)]

    objs+=[portal(3700,"cube",(5,5,20),(20,0,50))]
    for i in range(7):
        objs+=[sp(3900+i*90)]
    objs+=[b(4600,GROUND_Y-40,40,40),sp(4700)]

    return spd, objs, coins


LEVELS = [
    {"name": "Stereo Madness", "desc": "All modes · Medium", "fn": make_level_stereo,      "color": CYAN},
    {"name": "Back on Track",  "desc": "Cube only · Easy",   "fn": make_level_back_on_track,"color": GREEN},
    {"name": "Dry Out",        "desc": "Ship focus · Hard",  "fn": make_level_dry_out,      "color": ORANGE},
]

LEVEL_END_X = 7500   # x-pos of finish flag (same for all levels for simplicity)

# ── Game ──────────────────────────────────────────────────────────────────────

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Geometry World")
        self.clock  = pygame.time.Clock()
        self.state  = "MENU"
        self.skin   = CYAN
        self.attempts= 0
        self.best_pct= [0.0] * len(LEVELS)
        self.sel_lvl = 0
        self.bg      = Background()
        self.tick    = 0
        self._reset_game(0)

    def _reset_game(self, lvl_idx):
        self.lvl_idx = lvl_idx
        spd, objs, coins_raw = LEVELS[lvl_idx]["fn"]()
        self.base_speed = spd
        self.speed      = spd
        self.obstacles  = objs
        self.coins      = [Coin(cx, cy) for (_, cx, cy) in coins_raw]
        self.coins_got  = 0
        self.player     = Player(self.skin)
        self.cam_x      = 0
        self.bg.set_colors((15,10,30),(30,0,60))
        self.attempts  += 1
        self.practice   = False
        self.checkpoints= []
        self.cp_player  = None
        self.finished   = False
        self.death_anim = 0

    def _build_platforms(self):
        return [o.rect.move(-self.cam_x, 0) for o in self.obstacles if o.is_platform()]

    def run(self):
        while True:
            self.tick += 1
            self._events()
            self._update()
            self._draw()
            self.clock.tick(FPS)

    # ── events ────────────────────────────────────────────────────────────────
    def _events(self):
        press = release = False
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if   ev.key == pygame.K_ESCAPE: self._on_escape()
                elif ev.key == pygame.K_SPACE:  press = True
                elif ev.key == pygame.K_UP:     press = True
                elif ev.key == pygame.K_LEFT and self.state == "GAME":
                    self.player.move_left(True)
                elif ev.key == pygame.K_RIGHT and self.state == "GAME":
                    self.player.move_right(True)
                elif ev.key == pygame.K_r and self.state=="GAME":
                    self._reset_game(self.lvl_idx)
                elif ev.key == pygame.K_p and self.state=="GAME":
                    self.practice = not self.practice
                elif ev.key == pygame.K_c and self.practice and self.state=="GAME":
                    self._save_checkpoint()
                elif self.state == "MENU":
                    self._menu_key(ev.key)
                elif self.state == "SKINS":
                    self._skin_key(ev.key)
                elif self.state in ("WIN","DEAD"):
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = "MENU"
            if ev.type == pygame.KEYUP:
                if ev.key in (pygame.K_SPACE, pygame.K_UP): release = True
                elif ev.key == pygame.K_LEFT:
                    self.player.move_left(False)
                elif ev.key == pygame.K_RIGHT:
                    self.player.move_right(False)
            if ev.type == pygame.MOUSEBUTTONDOWN:
                press = True
            if ev.type == pygame.MOUSEBUTTONUP:
                release = True

        if self.state == "GAME":
            if press:   self.player.press()
            if release: self.player.release()

    def _on_escape(self):
        if   self.state == "GAME":   self.state = "MENU"
        elif self.state == "SKINS":  self.state = "MENU"
        elif self.state in ("WIN","DEAD"): self.state = "MENU"

    def _menu_key(self, key):
        if key == pygame.K_DOWN:
            self.sel_lvl = (self.sel_lvl + 1) % len(LEVELS)
        elif key == pygame.K_UP:
            self.sel_lvl = (self.sel_lvl - 1) % len(LEVELS)
        elif key == pygame.K_RETURN:
            self._reset_game(self.sel_lvl)
            self.state = "GAME"
        elif key == pygame.K_s:
            self.state = "SKINS"

    def _skin_key(self, key):
        for i, k in enumerate([pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4,
                                pygame.K_5,pygame.K_6,pygame.K_7,pygame.K_8]):
            if key == k:
                self.skin = SKIN_COLORS[i]
                self.player.color = self.skin
        if key == pygame.K_ESCAPE:
            self.state = "MENU"

    def _save_checkpoint(self):
        import copy
        self.cp_player = copy.deepcopy(self.player)
        self.cp_cam    = self.cam_x
        self.checkpoints.append(self.cam_x)

    def _load_checkpoint(self):
        if self.cp_player:
            import copy
            self.player = copy.deepcopy(self.cp_player)
            self.cam_x  = self.cp_cam

    # ── update ────────────────────────────────────────────────────────────────
    def _update(self):
        if self.state != "GAME": 
            self.bg.update(1)
            return

        beat = (self.tick % (FPS // 2)) == 0
        self.bg.update(self.speed, beat)

        if not self.player.alive:
            self.death_anim += 1
            if self.death_anim > 60:
                if self.practice:
                    self._load_checkpoint()
                    self.player.alive = True
                    self.death_anim = 0
                else:
                    self.state = "DEAD"
            return

        # camera tracks player
        target_cam = self.player.rect.x - 150
        self.cam_x += (target_cam - self.cam_x) * 0.2

        # platforms in world coords, shifted to screen
        platforms_screen = [pygame.Rect(o.rect.x - self.cam_x, o.rect.y,
                                        o.rect.width, o.rect.height)
                            for o in self.obstacles if o.is_platform()]
        self.player.update(platforms_screen, [])

        # update obstacles & portals in world space
        for o in self.obstacles:
            pass  # static world, cam moves

        for c in self.coins:
            c.update(0)  # world-relative, drawn with cam offset

        # check collisions (world → screen offset)
        px = self.player.rect
        for o in self.obstacles:
            sr = pygame.Rect(o.rect.x - self.cam_x, o.rect.y, o.rect.width, o.rect.height)
            if px.colliderect(sr):
                if o.otype in ("spike","spike_ceil"):
                    self.player.alive = False
                    self.death_anim = 0
                    pct = self.cam_x / LEVEL_END_X
                    if pct > self.best_pct[self.lvl_idx]:
                        self.best_pct[self.lvl_idx] = pct
                    break
                elif o.otype == "block" and o.color and o.color != (80,80,120):
                    # coloured wall → kill
                    if px.right > sr.left+4 and px.left < sr.right-4:
                        if not (px.bottom <= sr.top+6 or px.top >= sr.bottom-6):
                            self.player.alive = False
                            self.death_anim = 0
                            break
                elif o.otype == "orb":
                    # auto-activate on press
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
                        if o.color == YELLOW:
                            self.player.vel_y = -14
                            self.player.on_ground = False
                        elif o.color == (255,80,200):   # pink → reverse gravity
                            self.player.gravity *= -1
                            self.player.vel_y = -8 * self.player.gravity
                        elif o.color == CYAN:
                            self.player.vel_y = -18
                elif o.otype == "pad":
                    self.player.vel_y = -16
                elif o.otype == "portal":
                    self.player.mode    = o.mode
                    self.player.gravity = 1   # reset gravity on mode change
                    self.bg.set_colors(*o.bg)

        # coins
        for c in self.coins:
            if not c.collected:
                cr = pygame.Rect(c.rect.x - self.cam_x, c.rect.y, c.rect.width, c.rect.height)
                if px.colliderect(cr):
                    c.collected = True
                    self.coins_got += 1

        # finish
        if self.cam_x >= LEVEL_END_X:
            pct = 1.0
            self.best_pct[self.lvl_idx] = pct
            self.finished = True
            self.state = "WIN"

    # ── draw ──────────────────────────────────────────────────────────────────
    def _draw(self):
        self.bg.draw(self.screen)

        if self.state == "MENU":
            self._draw_menu()
        elif self.state == "SKINS":
            self._draw_skins()
        elif self.state == "GAME":
            self._draw_game()
        elif self.state == "WIN":
            self._draw_win()
        elif self.state == "DEAD":
            self._draw_dead()

        pygame.display.flip()

    def _draw_menu(self):
        # title
        t  = self.tick * 0.04
        cx = WIDTH//2 + int(math.sin(t)*3)
        draw_text(self.screen,"GEOMETRY WORLD",58,cx,80,
                  lerp_color(CYAN,PURPLE,(math.sin(t)+1)/2))
        draw_text(self.screen,"↑ ↓  Navigate   ENTER  Play   S  Skins",22,WIDTH//2,130,GRAY)

        # level cards
        for i, lvl in enumerate(LEVELS):
            y   = 200 + i * 72
            sel = (i == self.sel_lvl)
            col = lvl["color"]
            bw  = 420; bh = 58
            bx  = WIDTH//2 - bw//2
            br  = pygame.Rect(bx, y - bh//2, bw, bh)
            if sel:
                pygame.draw.rect(self.screen, col,  br, border_radius=10)
                pygame.draw.rect(self.screen, WHITE,br, 2, border_radius=10)
            else:
                s = pygame.Surface((bw, bh), pygame.SRCALPHA)
                s.fill((*col[:3], 50))
                self.screen.blit(s, (bx, y - bh//2))
                pygame.draw.rect(self.screen, col, br, 2, border_radius=10)
            tc = BLACK if sel else col
            draw_text(self.screen, lvl["name"],  22, WIDTH//2, y-10, tc)
            draw_text(self.screen, lvl["desc"],  15, WIDTH//2, y+12, tc)
            pct = self.best_pct[i]
            bar_w = int(bw * 0.8 * pct)
            if bar_w:
                pygame.draw.rect(self.screen, NEON_G,
                    (bx + bw//10, y+bh//2-8, bar_w, 4), border_radius=2)
            draw_text(self.screen, f"{int(pct*100)}%", 13,
                      bx+bw//10 + bar_w + 16, y+bh//2-5, NEON_G)

        draw_text(self.screen, f"Skin:", 18, WIDTH//2 - 60, HEIGHT-28, GRAY)
        pygame.draw.rect(self.screen, self.skin,
                         (WIDTH//2-10, HEIGHT-42, 26, 26), border_radius=4)

    def _draw_skins(self):
        draw_text(self.screen,"Choose Skin",46,WIDTH//2,60,WHITE)
        draw_text(self.screen,"Press 1-8 to select, ESC to go back",18,WIDTH//2,100,GRAY)
        cols = 4
        for i,(c,n) in enumerate(zip(SKIN_COLORS, SKIN_NAMES)):
            col = i % cols
            row = i // cols
            x   = WIDTH//2 - 160 + col*100
            y   = 170 + row*110
            sel = (c == self.skin)
            r   = pygame.Rect(x-30, y-30, 60, 60)
            pygame.draw.rect(self.screen, c, r, border_radius=8)
            if sel:
                pygame.draw.rect(self.screen, WHITE, r, 3, border_radius=8)
                glow_circle(self.screen, c, (x, y), 35, 80)
            draw_text(self.screen, f"{i+1} {n}", 16, x, y+38, c)

    def _draw_game(self):
        cam = self.cam_x

        # obstacles
        for o in self.obstacles:
            sr = pygame.Rect(o.rect.x - cam, o.rect.y, o.rect.width, o.rect.height)
            if -60 < sr.x < WIDTH + 60:
                # draw adjusted
                tmp = o.otype; tmp_rect = o.rect
                o.rect = sr
                o.draw(self.screen)
                o.rect = tmp_rect

        # coins
        for c in self.coins:
            if not c.collected:
                sr = pygame.Rect(c.rect.x - cam, c.rect.y, c.rect.width, c.rect.height)
                if -30 < sr.x < WIDTH+30:
                    c.rect.x -= cam
                    c.draw(self.screen)
                    c.rect.x += cam

        # player (fixed on screen)
        self.player.draw(self.screen)

        # death particles
        if not self.player.alive and self.death_anim > 0:
            for i in range(12):
                a  = i * 30 + self.death_anim * 5
                r  = self.death_anim * 2
                px = self.player.rect.centerx + int(math.cos(math.radians(a)) * r)
                py = self.player.rect.centery + int(math.sin(math.radians(a)) * r)
                s  = max(0, 8 - self.death_anim//5)
                if s > 0:
                    pygame.draw.rect(self.screen, self.player.color,
                                     (px-s//2, py-s//2, s, s))

        # HUD
        self._draw_hud()

    def _draw_hud(self):
        # progress bar
        pct   = min(1.0, self.cam_x / LEVEL_END_X)
        bar_x = 20; bar_y = 12; bar_w = WIDTH-40; bar_h = 8
        pygame.draw.rect(self.screen, GRAY,   (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        pygame.draw.rect(self.screen, NEON_G, (bar_x, bar_y, int(bar_w*pct), bar_h), border_radius=4)
        pygame.draw.rect(self.screen, WHITE,  (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
        draw_text(self.screen, f"{int(pct*100)}%", 14, bar_x+bar_w+24, bar_y+4, WHITE)

        # mode icon
        mode_col = {
            "cube":CYAN,"ship":YELLOW,"ball":PINK,"wave":RED,"ufo":PURPLE
        }.get(self.player.mode, WHITE)
        draw_text(self.screen, self.player.mode.upper(), 16, 60, 34, mode_col)

        # attempts & coins
        draw_text(self.screen, f"Attempt {self.attempts}", 16, WIDTH-70, 34, GRAY)
        draw_text(self.screen, f"★ {self.coins_got}", 16, WIDTH//2, 34, YELLOW)

        # practice mode badge
        if self.practice:
            draw_text(self.screen, "PRACTICE  [C]=Checkpoint", 14, WIDTH//2, HEIGHT-20, YELLOW)

        # controls hint (first 3 sec)
        if self.tick < FPS*4:
            draw_text(self.screen,"SPACE / Click  =  Jump / Fly",18,WIDTH//2,HEIGHT//2+80,
                      (*WHITE, 180))

    def _draw_win(self):
        col = LEVELS[self.lvl_idx]["color"]
        draw_text(self.screen, "LEVEL COMPLETE!", 52, WIDTH//2, HEIGHT//2-60,
                  lerp_color(col, WHITE, (math.sin(self.tick*0.08)+1)/2))
        draw_text(self.screen, LEVELS[self.lvl_idx]["name"], 28, WIDTH//2, HEIGHT//2-10, col)
        draw_text(self.screen, f"Coins: {self.coins_got} / {len(self.coins)}", 24,
                  WIDTH//2, HEIGHT//2+30, YELLOW)
        draw_text(self.screen, "ENTER / SPACE  to return", 20, WIDTH//2, HEIGHT//2+80, GRAY)

    def _draw_dead(self):
        draw_text(self.screen, "YOU DIED", 60, WIDTH//2, HEIGHT//2-50, RED)
        draw_text(self.screen, f"Reached {int(self.best_pct[self.lvl_idx]*100)}%",
                  28, WIDTH//2, HEIGHT//2+10, WHITE)
        draw_text(self.screen, "ENTER / SPACE  to return", 20, WIDTH//2, HEIGHT//2+60, GRAY)


# ── entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()