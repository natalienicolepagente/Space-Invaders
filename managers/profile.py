import pygame

from db import get_player_stats, update_profile
from managers import theme, cosmetics
from managers.sound_manager import sound
from managers.ui import TextInput

ACHIEVEMENTS = [
    ("Play your first game", lambda s: s["games_played"] >= 1),
    ("Score 500 in one game", lambda s: s["highest_score"] >= 500),
    ("Reach level 5", lambda s: s["highest_wave"] >= 5),
    ("Play 10 games", lambda s: s["games_played"] >= 10),
    ("Earn 5,000 total score", lambda s: s["total_score"] >= 5000),
    ("Reach level 10", lambda s: s["highest_wave"] >= 10),
]


class Profile:
    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player if isinstance(player, dict) else {}
        self.action = None

        self.username = self.player.get("username", "PLAYER")
        self.ship = cosmetics.clamp_id(
            self.player.get("ship", 1), cosmetics.SHIP_COUNT
        )
        self.avatar = cosmetics.clamp_id(
            self.player.get("avatar", 1), cosmetics.AVATAR_COUNT
        )

        self.stats = {
            "total_score": 0,
            "games_played": 0,
            "highest_score": 0,
            "highest_wave": 0,
        }

        if "player_id" in self.player:
            self.stats = get_player_stats(self.player["player_id"])

        self.panel = pygame.Rect(70, 85, 660, 480)

        self.name_box = TextInput(
            pygame.Rect(210, 105, 390, 40), "Player Name", "user",
            max_len=20
        )
        self.name_box.text = self.username

        self.ship_panel = pygame.Rect(90, 262, 300, 124)
        self.avatar_panel = pygame.Rect(410, 262, 300, 124)

        self.ship_cells = [
            pygame.Rect(
                self.ship_panel.x + 20 + i * 68, self.ship_panel.y + 30,
                56, 56
            )
            for i in range(cosmetics.SHIP_COUNT)
        ]
        self.avatar_cells = [
            pygame.Rect(
                self.avatar_panel.x + 20 + i * 68, self.avatar_panel.y + 30,
                56, 56
            )
            for i in range(cosmetics.AVATAR_COUNT)
        ]

        self.hex_centers = [(280 + i * 58, 425) for i in range(6)]

        self.save_btn = pygame.Rect(w // 2 - 110, 500, 220, 44)

        self.message = ""
        self.message_ok = False
        self.message_timer = 0

    def set_message(self, text, ok=False):
        self.message = text
        self.message_ok = ok
        self.message_timer = 180

    def save(self):
        name = self.name_box.text.strip()

        if len(name) < 3:
            self.set_message("NAME MUST BE AT LEAST 3 CHARACTERS")
            return

        if "player_id" not in self.player:
            self.set_message("NO PLAYER LOGGED IN")
            return

        ok, msg = update_profile(
            self.player["player_id"], name, self.ship, self.avatar
        )

        if ok:
            self.player["username"] = name
            self.player["ship"] = self.ship
            self.player["avatar"] = self.avatar
            self.username = name
            self.name_box.text = name
            self.name_box.active = False

        self.set_message(msg, ok)

    def draw_top(self):
        cosmetics.draw_avatar_id(self.screen, 140, 162, 46, self.avatar)

        self.name_box.draw(self.screen)
        cosmetics.draw_icon(
            self.screen, "pencil", self.name_box.rect.right - 24,
            self.name_box.rect.centery, theme.MUTED, 0.9
        )

        for x, icon, label, value in (
            (210, "trophy", "Total Score",
             f"{self.stats['total_score']:,}"),
            (430, "star", "Highest Level", str(self.stats["highest_wave"])),
        ):
            color = (255, 200, 90) if icon == "star" else theme.PINK_LIGHT
            cosmetics.draw_icon(self.screen, icon, x + 16, 197, color, 1.3)
            theme.text(
                self.screen, label, theme.font(12), theme.MUTED,
                (x + 42, 177)
            )
            theme.text(
                self.screen, value, theme.font(22, True), theme.TEXT,
                (x + 42, 192)
            )

        level, current, needed = theme.level_info(
            self.stats["total_score"]
        )

        theme.text(
            self.screen, f"Lv. {level}   {current} / {needed}",
            theme.font(12), theme.MUTED, (600, 222), "topright"
        )
        theme.draw_progress(
            self.screen, pygame.Rect(210, 240, 390, 8), current / needed
        )

    def draw_choice_panel(self, panel, title, cells, selected, draw_item):
        theme.draw_panel(
            self.screen, panel, fill=(40, 8, 40, 220), radius=12,
            border=(170, 50, 130), width=1
        )
        theme.text(
            self.screen, title, theme.font(14, True), theme.TEXT,
            (panel.x + 20, panel.y + 8)
        )

        mouse = pygame.mouse.get_pos()

        for i, rect in enumerate(cells, start=1):
            chosen = i == selected
            hover = rect.collidepoint(mouse)

            theme.draw_panel(
                self.screen, rect,
                fill=(120, 24, 96, 235) if (chosen or hover)
                else (28, 5, 30, 235),
                radius=10,
                border=theme.PINK_SOFT if chosen else (170, 50, 130),
                width=2 if chosen else 1
            )
            draw_item(i, rect)
            theme.text(
                self.screen, str(i), theme.font(12),
                theme.PINK_SOFT if chosen else theme.MUTED,
                (rect.centerx, rect.bottom + 4), "midtop"
            )

    def draw_achievements(self):
        theme.text(
            self.screen, "Achievements", theme.font(14, True), theme.TEXT,
            (90, 425), "midleft"
        )

        mouse = pygame.mouse.get_pos()
        hover_text = ""

        for (cx, cy), (desc, check) in zip(self.hex_centers, ACHIEVEMENTS):
            if check(self.stats):
                theme.draw_hex(
                    self.screen, cx, cy, 18, (120, 24, 96), theme.PINK_SOFT
                )
                theme.draw_icon(
                    self.screen, "star", cx, cy, (255, 200, 90), 1.0
                )
            else:
                theme.draw_hex(
                    self.screen, cx, cy, 18, (40, 8, 40), (110, 40, 90)
                )
                theme.draw_icon(
                    self.screen, "lock", cx, cy, (130, 60, 105), 0.8
                )

            if (mouse[0] - cx) ** 2 + (mouse[1] - cy) ** 2 <= 18 ** 2:
                hover_text = desc

        if hover_text:
            theme.text(
                self.screen, hover_text, theme.font(12), theme.MUTED,
                (self.w // 2, 456), "center"
            )

    def draw(self):
        theme.draw_backdrop(self.screen, self.w, self.h, "menu")
        theme.draw_back_button(self.screen)

        theme.heading(
            self.screen, "PLAYER PROFILE", theme.title_font(30),
            theme.TEXT, (self.w // 2, 46), "center"
        )

        theme.draw_panel(
            self.screen, self.panel, fill=theme.PANEL_DARK, width=1
        )

        self.draw_top()

        self.draw_choice_panel(
            self.ship_panel, "CHOOSE YOUR SHIP", self.ship_cells, self.ship,
            lambda i, r: self.screen.blit(
                cosmetics.ship_image(i, 44),
                cosmetics.ship_image(i, 44).get_rect(center=r.center)
            )
        )
        self.draw_choice_panel(
            self.avatar_panel, "CHANGE AVATAR", self.avatar_cells,
            self.avatar,
            lambda i, r: cosmetics.draw_avatar_id(
                self.screen, r.centerx, r.centery, 22, i, border=False
            )
        )

        self.draw_achievements()

        if self.message_timer > 0:
            self.message_timer -= 1
            theme.text(
                self.screen, self.message, theme.font(13, True),
                theme.PINK_SOFT if self.message_ok else (255, 120, 150),
                (self.w // 2, 478), "center"
            )

        cosmetics.button(
            self.screen, self.save_btn, "SAVE", theme.font(19, True),
            self.save_btn.collidepoint(pygame.mouse.get_pos()),
            primary=True, icon="save"
        )

    def handle_events(self, events):
        self.action = None

        for event in events:
            self.name_box.handle_event(event)

            if event.type == pygame.KEYDOWN:
                if (
                    event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
                    and self.name_box.active
                ):
                    self.save()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if theme.BACK_RECT.collidepoint(event.pos):
                    sound.play_click()
                    self.action = "back"
                    return

                if self.save_btn.collidepoint(event.pos):
                    sound.play_click()
                    self.save()
                    continue

                for i, rect in enumerate(self.ship_cells, start=1):
                    if rect.collidepoint(event.pos):
                        sound.play_click()
                        self.ship = i

                for i, rect in enumerate(self.avatar_cells, start=1):
                    if rect.collidepoint(event.pos):
                        sound.play_click()
                        self.avatar = i