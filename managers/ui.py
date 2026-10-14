import pygame

from managers import theme
from managers.sound_manager import sound


class TextInput:
    def __init__(self, rect, placeholder, icon, password=False, max_len=30):
        self.rect = rect
        self.placeholder = placeholder
        self.icon = icon
        self.password = password
        self.max_len = max_len

        self.text = ""
        self.active = False
        self.show = False

        self.eye_rect = pygame.Rect(rect.right - 40, rect.y, 40, rect.h)

    def clear(self):
        self.text = ""
        self.active = False
        self.show = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.password and self.eye_rect.collidepoint(event.pos):
                sound.play_click()
                self.show = not self.show
                self.active = True
            else:
                self.active = self.rect.collidepoint(event.pos)

        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]

            elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                pass

            elif (
                event.unicode
                and event.unicode.isprintable()
                and len(self.text) < self.max_len
            ):
                self.text += event.unicode

    def draw(self, screen):
        border = theme.PINK_SOFT if self.active else (170, 50, 130)

        theme.draw_panel(
            screen, self.rect, fill=(40, 8, 40, 210),
            radius=8, border=border, width=2
        )

        theme.draw_icon(
            screen, self.icon,
            self.rect.x + 26, self.rect.centery, theme.MUTED, 1.0
        )

        fnt = theme.font(17)
        max_width = self.rect.w - 26 - 30 - (40 if self.password else 14)

        if self.text:
            shown = (
                self.text
                if (not self.password or self.show)
                else "\u2022" * len(self.text)
            )
            color = theme.TEXT
        else:
            shown = self.placeholder
            color = theme.DIM

        while fnt.size(shown)[0] > max_width and len(shown) > 1:
            shown = shown[1:]

        rect = theme.text(
            screen, shown, fnt, color,
            (self.rect.x + 52, self.rect.centery), "midleft"
        )

        if self.active and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = rect.right + 2 if self.text else self.rect.x + 52
            pygame.draw.line(
                screen, theme.TEXT,
                (cx, self.rect.centery - 9), (cx, self.rect.centery + 9), 2
            )

        if self.password:
            theme.draw_icon(
                screen,
                "eye" if self.show else "eye_off",
                self.eye_rect.centerx, self.eye_rect.centery,
                theme.MUTED, 1.0,
            )