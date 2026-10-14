import colorsys
import math
import pygame

from managers import theme

SHIP_COUNT = 4
AVATAR_COUNT = 4

SHIP_COLORS = {
    1: (90, 160, 255),
    2: (255, 80, 90),
    3: (255, 130, 200),
    4: (170, 110, 255),
}

SHIP_HUES = {1: 0.60, 2: 0.0, 4: 0.76}

_ship = {"loaded": False, "src": None, "variants": {}, "hue": 0.9}
_ship_cache = {}
_avatar_cache = {}


def clamp_id(value, count):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 1

    return value if 1 <= value <= count else 1


def _load_source():
    for path in theme.SHIP_PATHS:
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, (160, 160))
        except Exception:
            continue

    return None


def _dominant_hue(src):
    w, h = src.get_size()
    sx = sy = 0.0
    n = 0

    for x in range(0, w, 2):
        for y in range(0, h, 2):
            r, g, b, a = src.get_at((x, y))

            if a < 200:
                continue

            hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

            if ss < 0.35 or vv < 0.3:
                continue

            sx += math.cos(hh * 2 * math.pi) * ss
            sy += math.sin(hh * 2 * math.pi) * ss
            n += 1

    if n == 0:
        return 0.9

    return (math.atan2(sy, sx) / (2 * math.pi)) % 1.0


def _recolor(src, ship_id):
    if ship_id not in SHIP_HUES:
        return src

    delta = SHIP_HUES[ship_id] - _ship["hue"]
    out = src.copy()
    w, h = out.get_size()

    for x in range(w):
        for y in range(h):
            r, g, b, a = out.get_at((x, y))

            if a == 0:
                continue

            hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

            if ss < 0.2:
                continue

            nr, ng, nb = colorsys.hsv_to_rgb((hh + delta) % 1.0, ss, vv)
            out.set_at((x, y), (int(nr * 255), int(ng * 255), int(nb * 255), a))

    return out


def _fallback_ship(size, color):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    k = size / 80

    pts = [
        (40 * k, 4 * k), (50 * k, 34 * k), (74 * k, 60 * k),
        (50 * k, 54 * k), (40 * k, 74 * k), (30 * k, 54 * k),
        (6 * k, 60 * k), (30 * k, 34 * k),
    ]

    pygame.draw.polygon(s, (60, 10, 52), pts)
    pygame.draw.polygon(s, color, pts, max(2, int(3 * k)))
    pygame.draw.circle(
        s, (255, 255, 255), (int(40 * k), int(34 * k)), max(2, int(6 * k))
    )
    return s


def ship_image(ship_id, size):
    ship_id = clamp_id(ship_id, SHIP_COUNT)
    key = (ship_id, size)

    if key in _ship_cache:
        return _ship_cache[key]

    if not _ship["loaded"]:
        _ship["loaded"] = True
        _ship["src"] = _load_source()

        if _ship["src"] is not None:
            _ship["hue"] = _dominant_hue(_ship["src"])

    src = _ship["src"]

    if src is None:
        surf = _fallback_ship(size, SHIP_COLORS[ship_id])
    else:
        if ship_id not in _ship["variants"]:
            _ship["variants"][ship_id] = _recolor(src, ship_id)

        surf = pygame.transform.smoothscale(
            _ship["variants"][ship_id], (size, size)
        )

    _ship_cache[key] = surf
    return surf


def draw_menu_ship(screen, cx, y, ship_id=1, size=56):
    t = pygame.time.get_ticks() / 1000
    cx = int(cx + math.sin(t * 0.8) * 12)
    y = int(y + math.sin(t * 2.2) * 5)

    beam = (255, 90, 190) if int(t * 4) % 2 == 0 else (255, 170, 225)
    pygame.draw.line(screen, beam, (cx, y - 38), (cx, y), 2)

    flick = 6 + int(5 * abs(math.sin(t * 25)))
    fy = y + size - 6

    pygame.draw.polygon(
        screen, (255, 140, 60),
        [(cx - 7, fy), (cx + 7, fy), (cx, fy + flick + 8)]
    )
    pygame.draw.polygon(
        screen, (255, 230, 140),
        [(cx - 3, fy), (cx + 3, fy), (cx, fy + flick)]
    )

    img = ship_image(ship_id, size)
    screen.blit(img, img.get_rect(midtop=(cx, y)))


def _avatar_surface(avatar_id, r):
    d = r * 2
    c = r
    s = pygame.Surface((d, d), pygame.SRCALPHA)

    def P(x, y):
        return (int(c + x * r), int(c + y * r))

    def R(v):
        return max(1, int(v * r))

    def E(cx, cy, w, h):
        return pygame.Rect(
            int(c + (cx - w / 2) * r), int(c + (cy - h / 2) * r),
            max(1, int(w * r)), max(1, int(h * r))
        )

    def poly(color, pts):
        pygame.draw.polygon(s, color, [P(x, y) for x, y in pts])

    pygame.draw.circle(s, (110, 20, 90), (c, c), r)

    if avatar_id == 1:
        hair = (255, 120, 190)
        skin = (255, 226, 208)

        pygame.draw.circle(s, hair, P(0, -0.1), R(0.85))
        pygame.draw.ellipse(s, hair, E(0, 0.45, 1.7, 1.1))
        pygame.draw.ellipse(s, skin, E(0, 0.12, 1.15, 1.25))
        poly(hair, [
            (-0.62, -0.2), (-0.48, -0.66), (0, -0.82), (0.48, -0.66),
            (0.62, -0.2), (0.26, -0.32), (0, -0.04), (-0.26, -0.32),
        ])

        for sx in (-1, 1):
            pygame.draw.ellipse(s, (70, 24, 100), E(sx * 0.25, 0.2, 0.2, 0.3))
            pygame.draw.circle(
                s, (255, 255, 255), P(sx * 0.22, 0.13), R(0.045)
            )
            pygame.draw.circle(s, (255, 150, 170), P(sx * 0.4, 0.42), R(0.09))

        pygame.draw.arc(
            s, (200, 70, 100), E(0, 0.45, 0.26, 0.16),
            math.pi, 2 * math.pi, max(1, R(0.04))
        )

    elif avatar_id == 2:
        orange = (240, 130, 50)

        for sx in (-1, 1):
            poly(orange, [
                (sx * 0.78, -0.1), (sx * 0.7, -0.88), (sx * 0.2, -0.45)
            ])
            poly((255, 170, 190), [
                (sx * 0.62, -0.2), (sx * 0.6, -0.65), (sx * 0.32, -0.42)
            ])

        pygame.draw.ellipse(s, orange, E(0, 0.05, 1.55, 1.25))
        poly((255, 245, 235), [
            (-0.78, 0.12), (0, 0.9), (0.78, 0.12),
            (0.42, 0.02), (0, 0.2), (-0.42, 0.02),
        ])

        for sx in (-1, 1):
            pygame.draw.circle(s, (50, 20, 40), P(sx * 0.3, -0.02), R(0.08))

        pygame.draw.circle(s, (50, 20, 40), P(0, 0.5), R(0.1))

    elif avatar_id == 3:
        for sx in (-1, 1):
            pygame.draw.circle(s, (30, 20, 40), P(sx * 0.6, -0.62), R(0.28))

        pygame.draw.circle(s, (250, 248, 252), P(0, 0.05), R(0.8))

        for sx in (-1, 1):
            pygame.draw.ellipse(s, (30, 20, 40), E(sx * 0.3, 0.0, 0.3, 0.42))
            pygame.draw.circle(
                s, (255, 255, 255), P(sx * 0.3, -0.03), R(0.06)
            )

        pygame.draw.ellipse(s, (30, 20, 40), E(0, 0.3, 0.22, 0.14))
        pygame.draw.arc(
            s, (30, 20, 40), E(0, 0.45, 0.3, 0.16),
            math.pi, 2 * math.pi, max(1, R(0.035))
        )

    else:
        pygame.draw.circle(s, (232, 232, 245), P(0, 0), R(0.86))
        pygame.draw.ellipse(s, (40, 18, 90), E(0, 0.02, 1.2, 0.9))
        pygame.draw.ellipse(s, (130, 110, 255), E(-0.25, -0.15, 0.4, 0.22))
        pygame.draw.circle(s, (255, 130, 200), P(0.3, 0.15), R(0.07))
        pygame.draw.ellipse(s, (255, 130, 200), E(0, 0.02, 1.2, 0.9), max(1, R(0.04)))

    mask = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (c, c), r)
    s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

    return s


def draw_avatar_id(screen, cx, cy, r, avatar_id=1, border=True):
    avatar_id = clamp_id(avatar_id, AVATAR_COUNT)
    key = (avatar_id, r)

    if key not in _avatar_cache:
        _avatar_cache[key] = _avatar_surface(avatar_id, r)

    surf = _avatar_cache[key]
    screen.blit(surf, surf.get_rect(center=(cx, cy)))

    if border:
        pygame.draw.circle(
            screen, theme.PINK, (cx, cy), r, max(2, r // 12)
        )


def draw_icon(screen, name, cx, cy, color=theme.TEXT, s=1.0):
    def p(dx, dy):
        return (cx + dx * s, cy + dy * s)

    lw = max(2, int(2 * s))

    if name == "home":
        pygame.draw.polygon(
            screen, color, [p(-10, 0), p(0, -9), p(10, 0)], lw
        )
        pygame.draw.rect(
            screen, color, (cx - 7 * s, cy - 1 * s, 14 * s, 10 * s), lw
        )
        pygame.draw.rect(
            screen, color, (cx - 2 * s, cy + 3 * s, 4 * s, 6 * s)
        )

    elif name == "pencil":
        pygame.draw.line(screen, color, p(-7, 7), p(6, -6), lw + 2)
        pygame.draw.polygon(screen, color, [p(-10, 10), p(-10, 4), p(-4, 10)])

    elif name == "save":
        pygame.draw.rect(
            screen, color, (cx - 9 * s, cy - 9 * s, 18 * s, 18 * s),
            lw, border_radius=2
        )
        pygame.draw.rect(
            screen, color, (cx - 5 * s, cy - 9 * s, 10 * s, 6 * s)
        )
        pygame.draw.rect(
            screen, color, (cx - 5 * s, cy + 1 * s, 10 * s, 7 * s), lw
        )

    else:
        theme.draw_icon(screen, name, cx, cy, color, s)


def button(
    screen, rect, label, fnt, hover=False, primary=False,
    icon=None, radius=10
):
    theme.draw_button(
        screen, rect, label, fnt, hover, primary, None, radius
    )

    if icon:
        draw_icon(screen, icon, rect.x + 34, rect.centery, theme.TEXT, 1.2)