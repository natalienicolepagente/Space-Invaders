import pygame

from managers import theme, cosmetics
from managers.settings_manager import load_settings, save_settings
from managers.sound_manager import sound


class Settings:
    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player
        self.action = None

        self.settings = load_settings()
        self.dragging = False

        self.panel = pygame.Rect(110, 120, 580, 340)

        keys = ("sound_on", "music_on", "controls", "volume")
        top = self.panel.y + 22

        self.rows = {
            key: pygame.Rect(
                self.panel.x + 10, top + i * 74, self.panel.w - 20, 68
            )
            for i, key in enumerate(keys)
        }

        self.toggles = {
            key: pygame.Rect(
                self.rows[key].right - 110,
                self.rows[key].centery - 16, 84, 32
            )
            for key in ("sound_on", "music_on", "controls")
        }

        vrow = self.rows["volume"]
        self.track = pygame.Rect(vrow.x + 200, vrow.centery - 4, 250, 8)

        self.back_btn = pygame.Rect(w // 2 - 90, 485, 180, 44)

    def is_on(self, key):
        if key == "controls":
            return self.settings.get("controls") == "mobile"

        return bool(self.settings.get(key, True))

    def apply_and_save(self):
        save_settings(self.settings)
        sound.apply(self.settings)

    def set_volume_from_x(self, x):
        ratio = max(0, min(1, (x - self.track.x) / self.track.w))
        self.settings["volume"] = int(round(ratio * 100))
        sound.apply(self.settings)

    def toggle(self, key):
        if key == "controls":
            self.settings["controls"] = (
                "keyboard" if self.is_on("controls") else "mobile"
            )
        else:
            self.settings[key] = not self.is_on(key)

        self.apply_and_save()

    def draw_toggle(self, rect, on):
        bg = (255, 50, 160) if on else (60, 18, 58)
        pygame.draw.rect(self.screen, bg, rect, border_radius=16)
        pygame.draw.rect(
            self.screen, theme.PINK_SOFT if on else theme.PINK, rect, 2,
            border_radius=16
        )

        knob_x = rect.right - 16 if on else rect.x + 16
        label_x = rect.x + 24 if on else rect.right - 24

        theme.text(
            self.screen, "ON" if on else "OFF", theme.font(12, True),
            theme.TEXT if on else theme.MUTED,
            (label_x, rect.centery), "center"
        )
        pygame.draw.circle(
            self.screen, theme.TEXT, (knob_x, rect.centery), 11
        )

    def draw_toggle_row(self, key, label, icon):
        row = self.rows[key]

        cosmetics.draw_icon(
            self.screen, icon, row.x + 40, row.centery, theme.PINK_LIGHT, 1.4
        )
        theme.text(
            self.screen, label, theme.font(19, True), theme.TEXT,
            (row.x + 75, row.centery), "midleft"
        )
        self.draw_toggle(self.toggles[key], self.is_on(key))

    def draw_volume(self):
        row = self.rows["volume"]
        track = self.track
        value = int(self.settings.get("volume", 70))
        knob = (track.x + int(track.w * value / 100), track.centery)

        cosmetics.draw_icon(
            self.screen, "speaker", row.x + 40, row.centery,
            theme.PINK_LIGHT, 1.4
        )
        theme.text(
            self.screen, "Volume", theme.font(19, True), theme.TEXT,
            (row.x + 75, row.centery), "midleft"
        )

        pygame.draw.rect(self.screen, (50, 10, 46), track, border_radius=4)
        pygame.draw.rect(
            self.screen, theme.PINK,
            (track.x, track.y, knob[0] - track.x, track.h),
            border_radius=4
        )
        pygame.draw.circle(self.screen, theme.TEXT, knob, 10)
        pygame.draw.circle(self.screen, theme.PINK, knob, 10, 2)

        theme.text(
            self.screen, f"{value}%", theme.font(15, True), theme.TEXT,
            (track.right + 30, track.centery), "midleft"
        )

    def draw(self):
        theme.draw_backdrop(self.screen, self.w, self.h, "menu")
        theme.draw_back_button(self.screen)

        theme.heading_with_icon(
            self.screen, "gear", "SETTINGS", 52, self.w, 32
        )

        theme.draw_panel(self.screen, self.panel, fill=theme.PANEL_DARK)

        for key in ("sound_on", "music_on", "controls"):
            y = self.rows[key].bottom + 3
            pygame.draw.line(
                self.screen, (120, 30, 95),
                (self.panel.x + 15, y), (self.panel.right - 15, y), 1
            )

        self.draw_toggle_row("sound_on", "Sound", "speaker")
        self.draw_toggle_row("music_on", "Music", "music")
        self.draw_toggle_row("controls", "Mobile Controls", "controller")
        self.draw_volume()

        cosmetics.button(
            self.screen, self.back_btn, "Back", theme.font(18, True),
            self.back_btn.collidepoint(pygame.mouse.get_pos()),
            primary=True, icon="back"
        )

    def handle_events(self, events):
        self.action = None

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if (
                    theme.BACK_RECT.collidepoint(event.pos)
                    or self.back_btn.collidepoint(event.pos)
                ):
                    sound.play_click()
                    self.action = "back"
                    return

                if self.track.inflate(24, 30).collidepoint(event.pos):
                    self.dragging = True
                    self.set_volume_from_x(event.pos[0])
                    continue

                for key, rect in self.toggles.items():
                    if rect.inflate(12, 12).collidepoint(event.pos):
                        self.toggle(key)
                        sound.play_click()
                        break

            elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.set_volume_from_x(event.pos[0])

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging:
                    self.dragging = False
                    self.apply_and_save()