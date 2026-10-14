import pygame

PINK = (255, 105, 180)
PINK_DARK = (78, 20, 56)
PINK_HOT = (255, 60, 150)
WHITE = (255, 236, 246)
FLAME = (255, 210, 90)


class MobileButtons:

    def __init__(self, w=800, h=600):
        self.w = w
        self.h = h

        self.left = pygame.Rect(20, 526, 56, 52)
        self.right = pygame.Rect(86, 526, 56, 52)
        self.fire = pygame.Rect(724, 526, 56, 52)

        self.fingers = {}

    def reset(self):
        self.fingers.clear()

    def _points(self, events):
        for event in events:
            if event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION):
                self.fingers[event.finger_id] = (
                    event.x * self.w, event.y * self.h
                )
            elif event.type == pygame.FINGERUP:
                self.fingers.pop(event.finger_id, None)

        points = list(self.fingers.values())

        if pygame.mouse.get_pressed()[0]:
            points.append(pygame.mouse.get_pos())

        return points

    def _draw_base(self, screen, rect, pressed, fire=False):
        bg = PINK_HOT if (pressed and fire) else (
            PINK if pressed else PINK_DARK
        )

        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            surf, (*bg, 175), surf.get_rect(), border_radius=12
        )
        pygame.draw.rect(
            surf, (*PINK, 240), surf.get_rect(), 2, border_radius=12
        )
        screen.blit(surf, rect.topleft)

    def _draw_arrow(self, screen, rect, direction):
        cx, cy = rect.center

        pygame.draw.polygon(
            screen,
            WHITE,
            [
                (cx + 10 * direction, cy),
                (cx - 7 * direction, cy - 11),
                (cx - 7 * direction, cy + 11),
            ],
        )

    def _draw_fire_icon(self, screen, rect):
        cx, cy = rect.center

        pygame.draw.polygon(
            screen, FLAME,
            [(cx - 4, cy + 9), (cx + 4, cy + 9), (cx, cy + 18)]
        )
        pygame.draw.polygon(
            screen, WHITE,
            [(cx - 6, cy + 2), (cx - 12, cy + 11), (cx - 6, cy + 9)]
        )
        pygame.draw.polygon(
            screen, WHITE,
            [(cx + 6, cy + 2), (cx + 12, cy + 11), (cx + 6, cy + 9)]
        )
        pygame.draw.rect(
            screen, WHITE, (cx - 6, cy - 6, 12, 16), border_radius=3
        )
        pygame.draw.polygon(
            screen, WHITE,
            [(cx, cy - 18), (cx - 6, cy - 5), (cx + 6, cy - 5)]
        )
        pygame.draw.circle(screen, PINK_HOT, (cx, cy), 3)

    def draw(self, screen):
        points = list(self.fingers.values())

        if pygame.mouse.get_pressed()[0]:
            points.append(pygame.mouse.get_pos())

        def pressed(rect):
            return any(rect.collidepoint(p) for p in points)

        for rect, direction in ((self.left, -1), (self.right, 1)):
            self._draw_base(screen, rect, pressed(rect))
            self._draw_arrow(screen, rect, direction)

        self._draw_base(screen, self.fire, pressed(self.fire), fire=True)
        self._draw_fire_icon(screen, self.fire)

    def handle_mouse(self, player, events):
        fire = False

        for p in self._points(events):
            if self.left.collidepoint(p):
                player.move_left()

            if self.right.collidepoint(p):
                player.move_right()

            if self.fire.collidepoint(p):
                fire = True

        return fire