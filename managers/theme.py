import math
import random
import pygame

PINK = (255, 64, 160)
PINK_LIGHT = (255, 130, 200)
PINK_SOFT = (255, 205, 235)
BORDER = (255, 70, 170)
TEXT = (255, 240, 250)
MUTED = (235, 170, 210)
DIM = (150, 70, 120)
PANEL_FILL = (62, 10, 56, 205)
PANEL_DARK = (28, 5, 30, 230)

_fonts = {}


def font(size, bold=False):
    key = ("ui", size, bold)

    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("Arial", size, bold=bold)

    return _fonts[key]


def title_font(size):
    key = ("title", size)

    if key not in _fonts:
        path = pygame.font.match_font("arialblack")

        if path:
            _fonts[key] = pygame.font.Font(path, size)
        else:
            _fonts[key] = pygame.font.SysFont(
                "verdana,dejavusans,arial", size, bold=True
            )

    return _fonts[key]


def text(screen, string, fnt, color, pos, anchor="topleft"):
    surface = fnt.render(str(string), True, color)
    rect = surface.get_rect(**{anchor: pos})
    screen.blit(surface, rect)
    return rect


_outline_cache = {}


def _outlined(string, fnt, color, outline, t):
    key = (string, id(fnt), color, outline, t)
    surf = _outline_cache.get(key)

    if surf is None:
        main = fnt.render(string, True, color)
        edge = fnt.render(string, True, outline)
        w, h = main.get_size()
        pad = t + 2

        surf = pygame.Surface(
            (w + pad * 2, h + pad * 2 + t + 3), pygame.SRCALPHA
        )

        surf.blit(edge, (pad, pad + t + 3))

        for dx in range(-t, t + 1):
            for dy in range(-t, t + 1):
                if (dx or dy) and dx * dx + dy * dy <= t * t + 1:
                    surf.blit(edge, (pad + dx, pad + dy))

        surf.blit(main, (pad, pad))
        _outline_cache[key] = surf

    return surf


def heading(
    screen, string, fnt, color, pos, anchor="center",
    outline=(110, 8, 76), t=2
):
    string = str(string)
    base = fnt.render(string, True, color).get_rect(**{anchor: pos})
    surf = _outlined(string, fnt, color, outline, t)
    pad = t + 2
    screen.blit(surf, (base.x - pad, base.y - pad))
    return base


def heading_with_icon(screen, icon, string, cy, w, size=34):
    fnt = title_font(size)
    tw = fnt.size(string)[0]
    x0 = w // 2 - (44 + tw) // 2

    draw_icon(screen, icon, x0 + 16, cy, PINK_LIGHT, 1.8)
    heading(screen, string, fnt, TEXT, (x0 + 46, cy), "midleft")


_backdrops = {}

CRATERS = [
    (-0.35, -0.25, 0.12),
    (0.25, -0.45, 0.08),
    (0.40, 0.20, 0.15),
    (-0.15, 0.35, 0.09),
    (-0.50, 0.15, 0.06),
]


def draw_planet(surf, x, y, r):
    size = (r + 22) * 2
    glow = pygame.Surface((size, size), pygame.SRCALPHA)

    for extra, alpha in ((20, 25), (13, 40), (6, 60)):
        pygame.draw.circle(
            glow, (255, 60, 160, alpha), (size // 2, size // 2), r + extra
        )

    surf.blit(glow, (x - size // 2, y - size // 2))

    pygame.draw.circle(surf, (150, 24, 112), (x, y), r)

    for cx, cy, cr in CRATERS:
        pos = (int(x + cx * r), int(y + cy * r))
        rad = max(2, int(cr * r))
        pygame.draw.circle(surf, (105, 14, 80), pos, rad)
        pygame.draw.circle(surf, (205, 55, 150), pos, rad, 1)

    pygame.draw.circle(surf, (255, 90, 180), (x, y), r, 3)


BG_DIRS = ("assets/images", "assets")
BG_FILES = {"login": "nicback.png", "home": "nicmenu.png"}


def _load_bg(name, w, h):
    for folder in BG_DIRS:
        try:
            img = pygame.image.load(f"{folder}/{name}").convert()
        except Exception:
            continue

        iw, ih = img.get_size()
        scale = max(w / iw, h / ih)
        size = (max(w, int(iw * scale)), max(h, int(ih * scale)))
        img = pygame.transform.smoothscale(img, size)

        out = pygame.Surface((w, h))
        out.blit(img, ((w - size[0]) // 2, (h - size[1]) // 2))
        return out

    return None


def _build_backdrop(w, h, decor):
    if decor in BG_FILES:
        img = _load_bg(BG_FILES[decor], w, h)

        if img:
            return img

        decor = "menu"

    surf = pygame.Surface((w, h))

    top = (40, 6, 38)
    bottom = (16, 2, 18)

    for y in range(h):
        t = y / h
        color = tuple(
            int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)
        )
        pygame.draw.line(surf, color, (0, y), (w, y))

    if decor != "game":
        for i in range(110):
            x = (i * 137) % w
            y = (i * 83) % h
            size = 1 if i % 4 else 2
            pygame.draw.circle(surf, (255, 150, 205), (x, y), size)

    if decor == "menu":
        planets = [
            (30, h - 10, 115),
            (w - 20, h + 5, 120),
            (45, 80, 24),
            (w - 30, 115, 38),
        ]
    else:
        planets = [(60, h - 90, 38)]

    for x, y, r in planets:
        draw_planet(surf, x, y, r)

    return surf


def draw_backdrop(screen, w, h, decor="menu"):
    key = (w, h, decor)

    if key not in _backdrops:
        _backdrops[key] = _build_backdrop(w, h, decor)

    screen.blit(_backdrops[key], (0, 0))


_live = {"layers": None, "shooting": []}

STAR_LAYERS = (
    (0.4, 1, 60, (150, 70, 120)),
    (1.0, 1, 40, (255, 150, 205)),
    (2.2, 2, 18, (255, 215, 238)),
)


def _init_live(w, h):
    rng = random.Random(7)
    _live["layers"] = [
        {
            "speed": speed,
            "size": size,
            "color": color,
            "pts": [
                [rng.uniform(0, w), rng.uniform(0, h)]
                for _ in range(count)
            ],
        }
        for speed, size, count, color in STAR_LAYERS
    ]


def draw_live_backdrop(screen, w, h, boost=1.0):
    draw_backdrop(screen, w, h, "game")

    if _live["layers"] is None:
        _init_live(w, h)

    tick = pygame.time.get_ticks() // 220

    for li, layer in enumerate(_live["layers"]):
        for i, pt in enumerate(layer["pts"]):
            pt[1] += layer["speed"] * boost

            if pt[1] > h:
                pt[1] -= h + 4
                pt[0] = random.uniform(0, w)

            if li >= 1 and (tick + i) % 7 == 0:
                continue

            s = layer["size"]
            pygame.draw.rect(
                screen, layer["color"], (int(pt[0]), int(pt[1]), s, s)
            )

    if boost > 0 and random.random() < 0.006:
        _live["shooting"].append(
            [random.uniform(w * 0.3, w), -10.0]
        )

    alive = []

    for star in _live["shooting"]:
        star[0] -= 7 * boost
        star[1] += 9 * boost

        if star[1] < h + 20 and star[0] > -30:
            alive.append(star)

            x, y = int(star[0]), int(star[1])
            pygame.draw.line(
                screen, (255, 120, 190), (x + 28, y - 36), (x, y), 1
            )
            pygame.draw.line(
                screen, PINK_SOFT, (x + 12, y - 16), (x, y), 2
            )

    _live["shooting"] = alive


_menu_fx = {"stars": None, "sparks": None, "comets": []}


def _init_menu_fx(w, h):
    rng = random.Random(11)

    _menu_fx["stars"] = [
        (
            rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0, 6.28),
            rng.uniform(1.5, 3.5), rng.choice((1, 2, 2, 3)),
        )
        for _ in range(80)
    ]

    _menu_fx["sparks"] = [
        [
            rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.2, 0.7),
            rng.uniform(0, 6.28),
        ]
        for _ in range(34)
    ]


def draw_menu_fx(screen, w, h):
    if _menu_fx["stars"] is None:
        _init_menu_fx(w, h)

    t = pygame.time.get_ticks() / 1000

    for x, y, phase, speed, size in _menu_fx["stars"]:
        a = 0.5 + 0.5 * math.sin(t * speed + phase)

        if a < 0.25:
            continue

        color = (int(150 + 105 * a), int(80 + 120 * a), int(150 + 90 * a))
        pygame.draw.rect(screen, color, (int(x), int(y), size, size))

        if size == 3 and a > 0.85:
            cx, cy = int(x) + 1, int(y) + 1
            pygame.draw.line(screen, color, (cx - 5, cy), (cx + 5, cy), 1)
            pygame.draw.line(screen, color, (cx, cy - 5), (cx, cy + 5), 1)

    for sp in _menu_fx["sparks"]:
        sp[1] -= sp[2]

        if sp[1] < -6:
            sp[1] = h + 6
            sp[0] = random.uniform(0, w)

        x = sp[0] + math.sin(t + sp[3]) * 8
        pygame.draw.circle(screen, (255, 170, 220), (int(x), int(sp[1])), 1)

    if random.random() < 0.012:
        _menu_fx["comets"].append([random.uniform(w * 0.3, w), -10.0])

    alive = []

    for c in _menu_fx["comets"]:
        c[0] -= 6
        c[1] += 7

        if c[1] < h + 20 and c[0] > -30:
            alive.append(c)

            x, y = int(c[0]), int(c[1])
            pygame.draw.line(
                screen, (255, 120, 190), (x + 34, y - 40), (x, y), 1
            )
            pygame.draw.line(screen, PINK_SOFT, (x + 14, y - 17), (x, y), 2)

    _menu_fx["comets"] = alive


def draw_live_menu(screen, w, h, decor="menu"):
    draw_backdrop(screen, w, h, decor)
    draw_menu_fx(screen, w, h)


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


INVADER_B = [
    "..#.....#..",
    "#..#...#..#",
    "#.#######.#",
    "###.###.###",
    "###########",
    ".#########.",
    "..#.....#..",
    ".#.......#.",
]


def _draw_pattern(screen, pattern, cx, cy, px, color):
    width = len(pattern[0]) * px
    height = len(pattern) * px
    x0 = int(cx - width // 2)
    y0 = int(cy - height // 2)

    for row, line in enumerate(pattern):
        for col, ch in enumerate(line):
            if ch == "#":
                pygame.draw.rect(
                    screen,
                    color,
                    (x0 + col * px, y0 + row * px, px, px),
                )


def draw_invader(screen, cx, cy, px=4, color=PINK_LIGHT):
    _draw_pattern(screen, INVADER, cx, cy, px, color)


def draw_floating_invader(
    screen, cx, cy, px=4, color=PINK_LIGHT, phase=0.0
):
    t = pygame.time.get_ticks() / 1000
    x = cx + math.sin(t * 0.9 + phase) * 7
    y = cy + math.sin(t * 1.6 + phase) * 10
    frame = INVADER if int(t * 2 + phase) % 2 == 0 else INVADER_B

    _draw_pattern(screen, frame, x, y, px, color)


def draw_title(screen, cx, y, size=52):
    f = title_font(size)
    cursor = y

    for string, color, outline in (
        ("SPACE", PINK_LIGHT, (120, 8, 80)),
        ("INVADERS", (255, 250, 253), (170, 16, 110)),
    ):
        rect = heading(
            screen, string, f, color, (cx, cursor), "midtop",
            outline=outline, t=3
        )
        cursor += int(rect.height * 0.9)

    return cursor


SHIP_PATHS = ("assets/images/nicship.png", "assets/nicship.png")

_ship_src = {"loaded": False, "image": None}
_ship_scaled = {}


def _ship_image(size):
    if not _ship_src["loaded"]:
        _ship_src["loaded"] = True

        for path in SHIP_PATHS:
            try:
                _ship_src["image"] = pygame.image.load(path).convert_alpha()
                break
            except Exception:
                continue

    src = _ship_src["image"]

    if src is None:
        return None

    if size not in _ship_scaled:
        _ship_scaled[size] = pygame.transform.smoothscale(
            src, (size, size)
        )

    return _ship_scaled[size]


def draw_ship(screen, cx, y, size=56):
    img = _ship_image(size)

    pygame.draw.line(screen, (255, 90, 190), (cx, y - 38), (cx, y), 2)

    if img:
        screen.blit(img, img.get_rect(midtop=(cx, y)))
    else:
        pts = [
            (cx, y),
            (cx - 8, y + 24),
            (cx - 24, y + 40),
            (cx - 8, y + 36),
            (cx, y + 46),
            (cx + 8, y + 36),
            (cx + 24, y + 40),
            (cx + 8, y + 24),
        ]
        pygame.draw.polygon(screen, (90, 14, 70), pts)
        pygame.draw.polygon(screen, PINK_SOFT, pts, 2)


_glow_cache = {}


def _glow_surface(w, h, radius, pad, color):
    key = (w, h, radius, pad, color)
    surf = _glow_cache.get(key)

    if surf is None:
        surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)

        for i in range(pad, 0, -1):
            alpha = int(50 * ((pad - i + 1) / pad) ** 2)
            ring = pygame.Rect(pad - i, pad - i, w + i * 2, h + i * 2)
            pygame.draw.rect(
                surf, (*color, alpha), ring, 2, border_radius=radius + i
            )

        _glow_cache[key] = surf

    return surf


def _pulse(speed=2.0, low=190, high=255):
    t = pygame.time.get_ticks() / 1000
    return int(low + (high - low) * (0.5 + 0.5 * math.sin(t * speed)))


def draw_panel(
    screen, rect, fill=PANEL_FILL, radius=14, border=BORDER, width=2,
    glow=True
):
    big = min(rect.w, rect.h) >= 80

    if glow:
        pad = 5 if big else 3
        g = _glow_surface(rect.w, rect.h, radius, pad, tuple(border[:3]))
        g.set_alpha(_pulse(1.8))
        screen.blit(g, (rect.x - pad, rect.y - pad))

    surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(surf, fill, surf.get_rect(), border_radius=radius)

    if min(rect.w, rect.h) >= 50:
        pygame.draw.rect(
            surf, (255, 150, 215, 60), surf.get_rect().inflate(-8, -8), 1,
            border_radius=max(2, radius - 3)
        )

    screen.blit(surf, rect.topleft)
    pygame.draw.rect(screen, border, rect, width, border_radius=radius)


def draw_dim(screen, w, h, alpha=170):
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((14, 2, 16, alpha))
    screen.blit(overlay, (0, 0))


def draw_button(
    screen, rect, label, fnt, hover=False, primary=False,
    icon=None, radius=10
):
    if primary:
        bg = (255, 95, 190) if hover else (255, 50, 160)
        border = (255, 200, 235)

        g = _glow_surface(rect.w, rect.h, radius, 4, (255, 70, 170))
        g.set_alpha(_pulse(3.0, 160, 255))
        screen.blit(g, (rect.x - 4, rect.y - 4))
    else:
        bg = (112, 22, 90) if hover else (74, 12, 64)
        border = PINK_SOFT if hover else PINK

    pygame.draw.rect(screen, bg, rect, border_radius=radius)

    if primary:
        shine = pygame.Rect(rect.x + 6, rect.y + 3, rect.w - 12, 3)
        pygame.draw.rect(screen, (255, 170, 220), shine, border_radius=2)

    pygame.draw.rect(screen, border, rect, 2, border_radius=radius)

    if icon:
        draw_icon(screen, icon, rect.x + 34, rect.centery, TEXT, 1.2)

    text(screen, label, fnt, TEXT, rect.center, "center")


def draw_progress(screen, rect, ratio):
    pygame.draw.rect(screen, (40, 6, 38), rect, border_radius=rect.h // 2)

    ratio = max(0.0, min(1.0, ratio))
    fill = pygame.Rect(rect.x, rect.y, int(rect.w * ratio), rect.h)

    if fill.w > 0:
        pygame.draw.rect(screen, PINK, fill, border_radius=rect.h // 2)

    pygame.draw.rect(
        screen, PINK_LIGHT, rect, 1, border_radius=rect.h // 2
    )


def level_info(total_score):
    total_score = int(total_score or 0)
    return total_score // 1000 + 1, total_score % 1000, 1000


def draw_avatar(screen, cx, cy, r):
    pygame.draw.circle(screen, (110, 20, 90), (cx, cy), r)

    img = _ship_image(max(8, int(r * 1.4)))

    if img:
        screen.blit(img, img.get_rect(center=(cx, cy)))
    else:
        draw_invader(screen, cx, cy, max(1, int(r * 1.3 / 11)), PINK_SOFT)

    pygame.draw.circle(screen, PINK, (cx, cy), r, 3)


BACK_RECT = pygame.Rect(24, 24, 40, 40)


def draw_back_button(screen, rect=BACK_RECT):
    hover = rect.collidepoint(pygame.mouse.get_pos())
    draw_button(screen, rect, "", font(14), hover, radius=8)
    draw_icon(screen, "back", rect.centerx, rect.centery, TEXT, 1.0)


def draw_hex(screen, cx, cy, r, fill, border):
    pts = [
        (
            cx + r * math.cos(math.radians(60 * i - 90)),
            cy + r * math.sin(math.radians(60 * i - 90)),
        )
        for i in range(6)
    ]
    pygame.draw.polygon(screen, fill, pts)
    pygame.draw.polygon(screen, border, pts, 3)


def draw_icon(screen, name, cx, cy, color=TEXT, s=1.0):
    def p(dx, dy):
        return (cx + dx * s, cy + dy * s)

    lw = max(2, int(2 * s))

    if name == "user":
        pygame.draw.circle(screen, color, p(0, -5), max(3, int(5 * s)), lw)
        pygame.draw.arc(
            screen, color,
            (cx - 9 * s, cy + 1 * s, 18 * s, 14 * s),
            math.pi, 2 * math.pi, lw,
        )

    elif name == "lock":
        pygame.draw.rect(
            screen, color,
            (cx - 7 * s, cy - 1 * s, 14 * s, 10 * s),
            border_radius=2,
        )
        pygame.draw.arc(
            screen, color,
            (cx - 5 * s, cy - 9 * s, 10 * s, 14 * s),
            0, math.pi, lw,
        )

    elif name in ("eye", "eye_off"):
        pygame.draw.ellipse(
            screen, color,
            (cx - 10 * s, cy - 6 * s, 20 * s, 12 * s), lw,
        )
        pygame.draw.circle(screen, color, p(0, 0), max(2, int(3 * s)))

        if name == "eye_off":
            pygame.draw.line(screen, color, p(-9, 8), p(9, -8), lw)

    elif name == "play":
        pygame.draw.polygon(
            screen, color, [p(-6, -9), p(-6, 9), p(9, 0)]
        )

    elif name == "trophy":
        pygame.draw.polygon(
            screen, color, [p(-8, -9), p(8, -9), p(5, 2), p(-5, 2)], lw
        )
        pygame.draw.line(screen, color, p(0, 2), p(0, 8), lw)
        pygame.draw.line(screen, color, p(-5, 9), p(5, 9), lw)
        pygame.draw.arc(
            screen, color,
            (cx - 13 * s, cy - 8 * s, 8 * s, 8 * s),
            math.pi / 2, 3 * math.pi / 2, lw,
        )
        pygame.draw.arc(
            screen, color,
            (cx + 5 * s, cy - 8 * s, 8 * s, 8 * s),
            -math.pi / 2, math.pi / 2, lw,
        )

    elif name == "gear":
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(
                screen, color,
                p(math.cos(a) * 6, math.sin(a) * 6),
                p(math.cos(a) * 10, math.sin(a) * 10),
                lw + 1,
            )

        pygame.draw.circle(screen, color, p(0, 0), max(4, int(7 * s)), lw)
        pygame.draw.circle(screen, color, p(0, 0), max(1, int(2 * s)))

    elif name == "logout":
        pygame.draw.line(screen, color, p(-9, -9), p(-2, -9), lw)
        pygame.draw.line(screen, color, p(-9, -9), p(-9, 9), lw)
        pygame.draw.line(screen, color, p(-9, 9), p(-2, 9), lw)
        pygame.draw.line(screen, color, p(-3, 0), p(9, 0), lw)
        pygame.draw.line(screen, color, p(4, -5), p(9, 0), lw)
        pygame.draw.line(screen, color, p(4, 5), p(9, 0), lw)

    elif name == "back":
        pygame.draw.line(screen, color, p(8, 0), p(-8, 0), 3)
        pygame.draw.line(screen, color, p(-8, 0), p(-1, -7), 3)
        pygame.draw.line(screen, color, p(-8, 0), p(-1, 7), 3)

    elif name == "music":
        pygame.draw.circle(screen, color, p(-4, 6), max(3, int(4 * s)))
        pygame.draw.line(screen, color, p(0, 6), p(0, -8), lw)
        pygame.draw.line(screen, color, p(0, -8), p(8, -5), lw)

    elif name == "speaker":
        pygame.draw.polygon(
            screen, color,
            [p(-8, -3), p(-3, -3), p(3, -8), p(3, 8), p(-3, 3), p(-8, 3)],
        )
        pygame.draw.arc(
            screen, color,
            (cx + 4 * s, cy - 5 * s, 8 * s, 10 * s),
            -math.pi / 2, math.pi / 2, lw,
        )

    elif name == "controller":
        pygame.draw.rect(
            screen, color,
            (cx - 11 * s, cy - 6 * s, 22 * s, 13 * s),
            lw, border_radius=6,
        )
        pygame.draw.line(screen, color, p(-6, 0), p(-2, 0), lw)
        pygame.draw.line(screen, color, p(-4, -2), p(-4, 2), lw)
        pygame.draw.circle(screen, color, p(5, -1), max(1, int(1.5 * s)))
        pygame.draw.circle(screen, color, p(7, 2), max(1, int(1.5 * s)))

    elif name == "power":
        pygame.draw.arc(
            screen, color,
            (cx - 9 * s, cy - 9 * s, 18 * s, 18 * s),
            math.pi / 2 + 0.7, math.pi / 2 - 0.7 + 2 * math.pi, lw + 1,
        )
        pygame.draw.line(screen, color, p(0, -11), p(0, -2), lw + 1)

    elif name == "star":
        pts = []

        for i in range(10):
            radius = 10 if i % 2 == 0 else 4.5
            a = math.radians(-90 + i * 36)
            pts.append(p(math.cos(a) * radius, math.sin(a) * radius))

        pygame.draw.polygon(screen, color, pts)