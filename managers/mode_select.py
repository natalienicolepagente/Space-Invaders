import pygame

from managers import theme
from managers.sound_manager import sound


class ModeSelect:
    def __init__(self, screen, w, h):
        self.screen = screen
        self.w = w
        self.h = h
        self.action = None

        card_w, card_h, gap = 190, 270, 25
        start_x = w // 2 - (3 * card_w + 2 * gap) // 2

        self.modes = [
            ("CLASSIC", "classic", ["Survive", "as long", "as you can!"]),
            ("SURVIVAL", "survival", ["One life.", "How many levels", "can you last?"]),
            ("TIME ATTACK", "timeattack", ["60 seconds.", "Beat the clock!"]),
        ]

        self.cards = [
            pygame.Rect(start_x + i * (card_w + gap), 170, card_w, card_h)
            for i in range(3)
        ]

    def draw(self):
        theme.draw_backdrop(self.screen, self.w, self.h, "menu")
        theme.draw_back_button(self.screen)

        theme.heading(
            self.screen, "SELECT GAME MODE", theme.title_font(34),
            theme.PINK_LIGHT, (self.w // 2, 75), "center"
        )

        mouse = pygame.mouse.get_pos()

        for rect, (name, _, lines) in zip(self.cards, self.modes):
            hover = rect.collidepoint(mouse)

            theme.draw_panel(
                self.screen, rect,
                fill=(110, 22, 90, 230) if hover else theme.PANEL_FILL,
                border=theme.PINK_SOFT if hover else theme.BORDER,
                width=3
            )

            theme.draw_invader(
                self.screen, rect.centerx, rect.y + 70, 6,
                theme.PINK_SOFT if hover else theme.PINK_LIGHT
            )

            theme.text(
                self.screen, name, theme.font(20, True), theme.TEXT,
                (rect.centerx, rect.y + 135), "center"
            )

            for i, line in enumerate(lines):
                theme.text(
                    self.screen, line, theme.font(14), theme.MUTED,
                    (rect.centerx, rect.y + 175 + i * 20), "center"
                )

    def handle_events(self, events):
        self.action = None

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if theme.BACK_RECT.collidepoint(event.pos):
                    sound.play_click()
                    self.action = "back"
                    return

                for rect, (_, key, _) in zip(self.cards, self.modes):
                    if rect.collidepoint(event.pos):
                        sound.play_click()
                        self.action = key
                        return