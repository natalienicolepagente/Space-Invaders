import math
import random
import pygame

BOSS_STYLES = [
    {"name": "MOTHERSHIP", "pattern": "spread", "color": (255, 110, 190)},
    {"name": "HUNTER", "pattern": "aimed", "color": (255, 160, 90)},
    {"name": "VORTEX", "pattern": "spiral", "color": (180, 140, 255)},
    {"name": "INVADER KING", "pattern": "rain", "color": (255, 90, 120)},
]

TINTS = [
    (255, 255, 255),
    (255, 190, 140),
    (190, 160, 255),
    (255, 110, 110),
]

INVADER = [
    "..#.....#..",
    "...#...#...",
    "..#######..",
    ".##.###.##.",
    "###########",
    "#.#######.#",
    "#.#.....#.#",
    "...##.##...",
]

SCREEN_H = 600

BOSS_BULLET_RADIUS = 10


class BossBullet:
    def __init__(self, x, y, vx, vy, color, radius=BOSS_BULLET_RADIUS):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = radius
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy

        if (
            self.y > SCREEN_H + 40
            or self.y < -60
            or self.x < -60
            or self.x > 860
        ):
            self.active = False

    def get_rect(self):
        r = self.radius
        return pygame.Rect(int(self.x - r), int(self.y - r), r * 2, r * 2)

    def draw(self, screen):
        if not self.active:
            return

        pos = (int(self.x), int(self.y))
        pygame.draw.circle(screen, self.color, pos, self.radius + 3, 2)
        pygame.draw.circle(screen, self.color, pos, self.radius)
        pygame.draw.circle(screen, (255, 255, 255), pos, self.radius // 2)


class Boss:
    def __init__(self, screen_width, boss_no):
        self.screen_width = screen_width
        self.boss_no = boss_no

        self.style_index = (boss_no - 1) % len(BOSS_STYLES)
        style = BOSS_STYLES[self.style_index]
        self.name = style["name"]
        self.pattern = style["pattern"]
        self.color = style["color"]

        self.width = 150
        self.height = 110

        self.image = self._load_enemy_image()

        if self.image is None:
            self.image = self._build_image()

        self.x = screen_width / 2 - self.width / 2
        self.y = -self.height - 20
        self.target_y = 85

        self.max_hp = 30 + 15 * (boss_no - 1)
        self.hp = self.max_hp

        self.state = "entering"
        self.dir = random.choice((-1, 1))
        self.timer = 0
        self.angle = 0.0
        self.flash = 0

        base = {"spread": 1.6, "aimed": 2.6, "spiral": 1.1, "rain": 3.2}
        self.speed = base[self.pattern] * (1 + 0.06 * (boss_no - 1))

    @property
    def vulnerable(self):
        return self.state == "fighting"

    def _load_enemy_image(self):
        try:
            img = pygame.image.load(
                "assets/images/nicmy.png"
            ).convert_alpha()
        except Exception:
            return None

        self.width = 130
        self.height = 130

        img = pygame.transform.smoothscale(img, (self.width, self.height))
        img.fill(
            (*TINTS[self.style_index], 255),
            special_flags=pygame.BLEND_RGBA_MULT
        )
        return img

    def _build_image(self):
        w, h = self.width, self.height
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        c = self.color
        dark = (60, 8, 52)

        if self.pattern == "spread":
            pygame.draw.ellipse(s, (120, 30, 100), (35, 6, 80, 62))
            pygame.draw.ellipse(s, c, (35, 6, 80, 62), 3)
            pygame.draw.ellipse(s, dark, (0, 40, w, 62))
            pygame.draw.ellipse(s, c, (0, 40, w, 62), 4)
            pygame.draw.circle(s, (255, 255, 255), (75, 30), 13)
            pygame.draw.circle(s, (255, 50, 90), (75, 30), 7)

            for i in range(5):
                pygame.draw.circle(
                    s, (255, 240, 160), (22 + i * 27, 72), 5
                )

        elif self.pattern == "aimed":
            pts = [
                (w / 2, h - 4), (6, 22), (w * 0.28, 6),
                (w * 0.72, 6), (w - 6, 22),
            ]
            pygame.draw.polygon(s, dark, pts)
            pygame.draw.polygon(s, c, pts, 4)
            pygame.draw.line(s, c, (w * 0.28, 6), (w / 2, 60), 3)
            pygame.draw.line(s, c, (w * 0.72, 6), (w / 2, 60), 3)
            pygame.draw.rect(s, c, (12, 24, 14, 26), border_radius=3)
            pygame.draw.rect(s, c, (w - 26, 24, 14, 26), border_radius=3)
            pygame.draw.ellipse(s, (255, 60, 80), (w / 2 - 20, 28, 40, 24))
            pygame.draw.circle(s, (255, 255, 255), (w // 2, 40), 6)

        elif self.pattern == "spiral":
            cx, cy = w // 2, h // 2

            pygame.draw.circle(s, dark, (cx, cy), 52)
            pygame.draw.circle(s, c, (cx, cy), 52, 4)

            for i in range(8):
                a = i * math.pi / 4

                pygame.draw.line(
                    s, c,
                    (cx + math.cos(a) * 20, cy + math.sin(a) * 20),
                    (cx + math.cos(a) * 48, cy + math.sin(a) * 48), 3
                )

            pygame.draw.circle(s, (255, 255, 255), (cx, cy), 15)
            pygame.draw.circle(s, c, (cx, cy), 8)

        else:
            px = 13
            x0 = (w - len(INVADER[0]) * px) // 2
            y0 = (h - len(INVADER) * px) // 2

            for row, line in enumerate(INVADER):
                for col, ch in enumerate(line):
                    if ch == "#":
                        pygame.draw.rect(
                            s, c,
                            (x0 + col * px, y0 + row * px, px, px)
                        )

            for col in (3, 7):
                pygame.draw.rect(
                    s, dark, (x0 + col * px, y0 + 4 * px, px, px)
                )
                pygame.draw.rect(
                    s, (255, 255, 255),
                    (x0 + col * px + 3, y0 + 4 * px + 3, px - 6, px - 6)
                )

        return s

    def get_rect(self):
        return pygame.Rect(
            int(self.x) + 10, int(self.y) + 10,
            self.width - 20, self.height - 20
        )

    def hit(self, damage=1):
        self.hp -= damage
        self.flash = 3
        return self.hp <= 0

    def _shot(self, x, y, angle, speed, radius=BOSS_BULLET_RADIUS):
        speed *= 1 + 0.05 * (self.boss_no - 1)
        rad = math.radians(angle)

        return BossBullet(
            x, y, math.cos(rad) * speed, math.sin(rad) * speed,
            self.color, radius
        )

    def update(self, player, level=1):
        if self.flash > 0:
            self.flash -= 1

        if self.state == "entering":
            self.y += 2

            if self.y >= self.target_y:
                self.y = self.target_y
                self.state = "fighting"
                self.timer = 0

            return []

        self.timer += 1
        self._move()
        return self._attack(player)

    def _move(self):
        self.x += self.dir * self.speed

        if self.x <= 10:
            self.x = 10
            self.dir = 1
        elif self.x + self.width >= self.screen_width - 10:
            self.x = self.screen_width - 10 - self.width
            self.dir = -1

        if self.pattern == "aimed" and random.random() < 0.006:
            self.dir *= -1

        if self.pattern != "rain":
            self.y = self.target_y + math.sin(self.timer / 30) * 12

    def _attack(self, player):
        out = []

        cx = self.x + self.width / 2
        cy = self.y + self.height - 10
        px = player.x + player.width / 2
        py = player.y + player.height / 2

        k = max(0.55, 1 - 0.08 * (self.boss_no - 1))

        if self.pattern == "spread":
            gap = max(30, int(75 * k))

            if self.timer % gap == 0:
                out.append(self._shot(cx, cy, 90, 3.8))

        elif self.pattern == "aimed":
            gap = max(25, int(50 * k))

            if self.timer % gap == 0:
                base = math.degrees(math.atan2(py - cy, px - cx))
                out.append(self._shot(cx, cy, base, 5.2))

        elif self.pattern == "spiral":
            gap = max(4, int(8 * k))

            if self.timer % gap == 0:
                self.angle += 23

                out.append(self._shot(cx, cy, self.angle, 3.2))

        else:
            gap = max(10, int(22 * k))

            if self.timer % gap == 0:
                out.append(BossBullet(
                    px, self.y + self.height, 0,
                    4.5 * (1 + 0.05 * (self.boss_no - 1)), self.color
                ))

        return out

    def draw(self, screen):
        img = self.image

        if self.flash > 0:
            img = img.copy()
            img.fill((90, 90, 90, 0), special_flags=pygame.BLEND_RGB_ADD)

        screen.blit(img, (int(self.x), int(self.y)))