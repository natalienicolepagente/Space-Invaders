import pygame

from db import get_player_stats
from managers import theme, cosmetics
from managers.sound_manager import sound


class Home:
    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player
        self.action = None
        self.confirm_logout = False

        self.username = "PLAYER"
        self.ship = 1
        self.avatar = 1
        self.stats = {"total_score": 0}

        if isinstance(self.player, dict):
            self.username = self.player.get("username", "PLAYER")
            self.ship = self.player.get("ship", 1)
            self.avatar = self.player.get("avatar", 1)

            if "player_id" in self.player:
                self.stats = get_player_stats(self.player["player_id"])

        bw = 300
        bx = w // 2 - bw // 2

        self.buttons = [
            ("START GAME", "play", "play", pygame.Rect(bx, 170, bw, 58), True),
            ("LEADERBOARD", "leaderboard", "trophy",
             pygame.Rect(bx, 240, bw, 46), False),
            ("SETTINGS", "settings", "gear",
             pygame.Rect(bx, 296, bw, 46), False),
            ("PROFILE", "profile", "user",
             pygame.Rect(bx, 352, bw, 46), False),
            ("LOGOUT", "logout", "logout",
             pygame.Rect(bx, 408, bw, 46), False),
        ]

        self.chip = pygame.Rect(w - 205, 16, 190, 58)

        dlg_w, dlg_h = 340, 230
        self.dialog = pygame.Rect(
            w // 2 - dlg_w // 2, h // 2 - dlg_h // 2, dlg_w, dlg_h
        )
        self.yes_btn = pygame.Rect(
            self.dialog.x + 30, self.dialog.y + 128, dlg_w - 60, 40
        )
        self.cancel_btn = pygame.Rect(
            self.dialog.x + 30, self.dialog.y + 176, dlg_w - 60, 36
        )

    def draw_chip(self):
        theme.draw_panel(self.screen, self.chip, radius=12)
        cosmetics.draw_avatar_id(
            self.screen, self.chip.x + 28, self.chip.centery, 18,
            self.avatar
        )

        level, current, needed = theme.level_info(
            self.stats.get("total_score", 0)
        )

        theme.text(
            self.screen, self.username, theme.font(14, True), theme.TEXT,
            (self.chip.x + 54, self.chip.y + 8)
        )
        theme.text(
            self.screen, f"Lv. {level}", theme.font(12), theme.MUTED,
            (self.chip.x + 54, self.chip.y + 26)
        )
        theme.draw_progress(
            self.screen,
            pygame.Rect(self.chip.x + 54, self.chip.y + 44, 120, 6),
            current / needed
        )

    def draw_dialog(self):
        theme.draw_dim(self.screen, self.w, self.h, 190)
        theme.draw_panel(
            self.screen, self.dialog, fill=theme.PANEL_DARK, radius=14
        )

        theme.draw_icon(
            self.screen, "power",
            self.dialog.centerx, self.dialog.y + 34, theme.PINK_LIGHT, 1.6
        )
        theme.text(
            self.screen, "LOGOUT", theme.font(22, True), theme.TEXT,
            (self.dialog.centerx, self.dialog.y + 74), "center"
        )
        theme.text(
            self.screen, "Are you sure you want to log out?",
            theme.font(14), theme.MUTED,
            (self.dialog.centerx, self.dialog.y + 102), "center"
        )

        mouse = pygame.mouse.get_pos()

        theme.draw_button(
            self.screen, self.yes_btn, "Yes, Logout", theme.font(16, True),
            self.yes_btn.collidepoint(mouse), primary=True, radius=6
        )
        theme.draw_button(
            self.screen, self.cancel_btn, "Cancel", theme.font(16),
            self.cancel_btn.collidepoint(mouse), radius=6
        )

    def draw(self):
        theme.draw_live_menu(self.screen, self.w, self.h, "home")

        theme.draw_floating_invader(self.screen, 110, 330, 6, phase=0.0)
        theme.draw_floating_invader(
            self.screen, self.w - 110, 270, 6, phase=1.7
        )
        theme.draw_floating_invader(
            self.screen, self.w - 110, 400, 6, phase=3.1
        )
        theme.draw_floating_invader(self.screen, 110, 220, 4, phase=4.6)

        theme.draw_title(self.screen, self.w // 2 - 0, 12, 50)
        self.draw_chip()

        mouse = pygame.mouse.get_pos()

        for label, _, icon, rect, primary in self.buttons:
            theme.draw_button(
                self.screen, rect, label,
                theme.font(20 if primary else 17, True),
                rect.collidepoint(mouse) and not self.confirm_logout,
                primary=primary, icon=icon
            )

        cosmetics.draw_menu_ship(self.screen, self.w // 2, 520, self.ship)

        if self.confirm_logout:
            self.draw_dialog()

    def handle_events(self, events):
        self.action = None

        for event in events:
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            if self.confirm_logout:
                if self.yes_btn.collidepoint(event.pos):
                    sound.play_click()
                    self.confirm_logout = False
                    self.action = "logout"
                elif self.cancel_btn.collidepoint(event.pos):
                    sound.play_click()
                    self.confirm_logout = False
                continue

            for _, action, _, rect, _ in self.buttons:
                if rect.collidepoint(event.pos):
                    sound.play_click()

                    if action == "logout":
                        self.confirm_logout = True
                    else:
                        self.action = action
                    break