import pygame

from db import (
    get_player_rank,
    get_player_scores,
    get_player_stats,
    load_leaderboard,
)
from managers import theme
from managers.sound_manager import sound


class Leader:
    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player
        self.action = None

        self.player_id = None
        self.username = "PLAYER"

        if isinstance(player, dict):
            self.player_id = player.get("player_id")
            self.username = player.get("username", "PLAYER")

        self.tab = "global"
        self.tab_global = pygame.Rect(w // 2 - 130, 98, 120, 30)
        self.tab_mine = pygame.Rect(w // 2 + 10, 98, 120, 30)

        self.global_rows = []
        self.my_rows = []
        self.my_best = 0
        self.my_wave = 0
        self.my_rank = None

        self.load_data()

    def load_data(self):
        self.global_rows = load_leaderboard(8)

        if self.player_id is not None:
            self.my_rows = get_player_scores(self.player_id, 8)
            stats = get_player_stats(self.player_id)
            self.my_best = stats["highest_score"]
            self.my_wave = stats["highest_wave"]
            self.my_rank = get_player_rank(self.player_id)

    def draw_tabs(self):
        mouse = pygame.mouse.get_pos()

        for rect, label, key in (
            (self.tab_global, "Global", "global"),
            (self.tab_mine, "Your Score", "mine"),
        ):
            selected = self.tab == key
            theme.draw_button(
                self.screen, rect, label, theme.font(14, True),
                hover=rect.collidepoint(mouse), primary=selected,
                radius=15
            )

    def draw_row(self, y, cells, highlight=False, header=False):
        rect = pygame.Rect(50, y, 700, 34)

        if highlight:
            pygame.draw.rect(self.screen, theme.PINK, rect, border_radius=6)
        elif not header:
            pygame.draw.rect(
                self.screen, (50, 8, 46), rect, border_radius=6
            )

        fnt = theme.font(15, True if (header or highlight) else False)
        color = theme.PINK_LIGHT if header else theme.TEXT

        xs = (75, 150, 470, 610)

        for x, value in zip(xs, cells):
            theme.text(
                self.screen, value, fnt, color,
                (x, rect.centery), "midleft"
            )

    def draw_table(self):
        panel = pygame.Rect(40, 140, 720, 420)
        theme.draw_panel(self.screen, panel, fill=theme.PANEL_DARK)

        if self.tab == "global":
            self.draw_row(150, ["#", "Player", "Score", "Level"], header=True)

            if not self.global_rows:
                theme.text(
                    self.screen, "NO SCORES YET", theme.font(17),
                    theme.MUTED, (self.w // 2, 300), "center"
                )

            for i, row in enumerate(self.global_rows, start=1):
                self.draw_row(
                    190 + (i - 1) * 40,
                    [
                        str(i),
                        str(row.get("username", "PLAYER")),
                        f"{int(row.get('score', 0)):,}",
                        str(row.get("wave", 1)),
                    ],
                )

            rank = f"{self.my_rank}" if self.my_rank else "-"
            self.draw_row(
                190 + 8 * 40 + 10,
                [
                    "You",
                    f"{self.username}   (Rank {rank})",
                    f"{self.my_best:,}",
                    str(self.my_wave),
                ],
                highlight=True,
            )

        else:
            self.draw_row(150, ["#", "Date", "Score", "Level"], header=True)

            if not self.my_rows:
                theme.text(
                    self.screen, "NO GAMES YET", theme.font(17),
                    theme.MUTED, (self.w // 2, 300), "center"
                )

            for i, row in enumerate(self.my_rows, start=1):
                date_value = row.get("date_added")

                try:
                    date_text = date_value.strftime("%d/%m/%Y %I:%M %p")
                except Exception:
                    date_text = str(date_value) if date_value else "N/A"

                self.draw_row(
                    190 + (i - 1) * 40,
                    [
                        str(i),
                        date_text,
                        f"{int(row.get('score', 0)):,}",
                        str(row.get("wave", 1)),
                    ],
                )

    def draw(self):
        theme.draw_backdrop(self.screen, self.w, self.h, "menu")
        theme.draw_back_button(self.screen)

        theme.heading_with_icon(
            self.screen, "trophy", "LEADERBOARD", 52, self.w, 32
        )

        self.draw_tabs()
        self.draw_table()

    def handle_events(self, events):
        self.action = None

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if theme.BACK_RECT.collidepoint(event.pos):
                    sound.play_click()
                    self.action = "back"
                elif self.tab_global.collidepoint(event.pos):
                    sound.play_click()
                    self.tab = "global"
                elif self.tab_mine.collidepoint(event.pos):
                    sound.play_click()
                    self.tab = "mine"