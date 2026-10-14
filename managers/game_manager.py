import random
import pygame

from db import save_score, get_player_stats
from managers import theme, cosmetics
from managers.settings_manager import load_settings
from managers.sound_manager import sound

from entities.player import Player
from entities.enemy import Enemy
from entities.bullet import Bullet
from entities.button import MobileButtons
from entities.boss import Boss

MODES = {
    "classic": {"lives": 3, "time": None, "drop": 70},
    "survival": {"lives": 1, "time": None, "drop": 55},
    "timeattack": {"lives": 3, "time": 60, "drop": 60},
}

BOSS_EVERY = 3


class GameManager:
    def __init__(self, screen, w, h):
        self.screen = screen
        self.w = w
        self.h = h

        self.current_player_id = None
        self.player_name = "PLAYER"
        self.ship_id = 1
        self.mode = "classic"

        self.mobile = MobileButtons(w, h)

        self.again_btn = pygame.Rect(w // 2 - 150, 350, 300, 46)
        self.home_btn = pygame.Rect(w // 2 - 150, 404, 300, 46)
        self.board_btn = pygame.Rect(w // 2 - 150, 458, 300, 46)

        self.pause_btn = pygame.Rect(12, 6, 28, 28)
        self.pause_panel = pygame.Rect(w // 2 - 160, 160, 320, 270)
        self.resume_btn = pygame.Rect(w // 2 - 130, 250, 260, 44)
        self.pause_settings_btn = pygame.Rect(w // 2 - 130, 304, 260, 44)
        self.pause_home_btn = pygame.Rect(w // 2 - 130, 358, 260, 44)

        self.game_state = "playing"
        self.start_again()

    def start_again(self, mode=None):
        if mode in MODES:
            self.mode = mode

        cfg = MODES[self.mode]
        self.cfg = cfg
        self.settings = load_settings()

        self.player = Player(self.w, self.h, self.ship_id)
        self.life_icon = pygame.transform.smoothscale(
            self.player.image, (18, 18)
        )

        self.bullets = []
        self.enemies = []
        self.boss = None
        self.boss_bullets = []

        self.score = 0
        self.lives = cfg["lives"]
        self.level = 1
        self.time_left = (
            cfg["time"] * 60 if cfg["time"] else None
        )

        self.shoot_cooldown = 0
        self.drop_timer = 60
        self.blink_frames = 0
        self.score_saved = False
        self.best_level = 1

        self.banner_text = ""
        self.banner_timer = 0

        self.mobile.reset()

        self.game_state = "playing"
        self.spawn_level()

    def is_boss_level(self):
        return self.level % BOSS_EVERY == 0

    def spawn_level(self):
        self.boss_bullets = []

        if self.is_boss_level():
            self.enemies = []
            self.boss = Boss(self.w, self.level // BOSS_EVERY)
            self.banner_text = (
                f"LEVEL {self.level}  -  BOSS: {self.boss.name}"
            )
        else:
            self.boss = None
            count = min(4 + self.level, 8)
            self.enemies = [
                Enemy(i, count, self.w) for i in range(count)
            ]
            self.banner_text = f"LEVEL {self.level}"

        self.banner_timer = 130
        self.drop_timer = 60

    def fire(self):
        x = self.player.x + self.player.width // 2 - 16
        self.bullets.append(Bullet(x, self.player.y))
        self.shoot_cooldown = 15
        sound.play_shoot()

    def end_game(self):
        self.game_state = "game_over"

        self.best_level = self.level

        if not self.score_saved and self.current_player_id is not None:
            save_score(self.current_player_id, self.score, self.level)

            stats = get_player_stats(self.current_player_id)
            self.best_level = max(stats["highest_wave"], self.level)

        self.score_saved = True

    def hurt_player(self):
        self.lives -= 1

        self.player.is_blinking = True
        self.player.blink_timer = 0
        self.blink_frames = 0

        if self.lives <= 0:
            self.end_game()

    def update(self, events):
        if self.game_state == "game_over":
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.again_btn.collidepoint(event.pos):
                        sound.play_click()
                        self.start_again()
                        return

                    if self.home_btn.collidepoint(event.pos):
                        sound.play_click()
                        self.game_state = "back_home"
                        return

                    if self.board_btn.collidepoint(event.pos):
                        sound.play_click()
                        self.game_state = "open_leader"
                        return
            return

        if self.game_state == "paused":
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.resume_btn.collidepoint(event.pos):
                        sound.play_click()
                        self.game_state = "playing"
                        self.mobile.reset()
                        return

                    if self.pause_settings_btn.collidepoint(event.pos):
                        sound.play_click()
                        self.game_state = "open_settings"
                        return

                    if self.pause_home_btn.collidepoint(event.pos):
                        sound.play_click()
                        self.game_state = "back_home"
                        return

                elif event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE, pygame.K_p
                ):
                    self.game_state = "playing"
                    self.mobile.reset()
                    return
            return

        if self.game_state != "playing":
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.pause_btn.collidepoint(event.pos):
                    sound.play_click()
                    self.game_state = "paused"
                    return

            elif event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE, pygame.K_p
            ):
                self.game_state = "paused"
                return

        fire = False

        if pygame.key.get_pressed()[pygame.K_SPACE]:
            fire = True

        if self.settings.get("controls") == "mobile":
            if self.mobile.handle_mouse(self.player, events):
                fire = True

        self.player.update()

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if fire and self.shoot_cooldown <= 0:
            self.fire()

        if self.banner_timer > 0:
            self.banner_timer -= 1

        if self.time_left is not None:
            self.time_left -= 1

            if self.time_left <= 0:
                self.time_left = 0
                self.end_game()
                return

        self.drop_timer -= 1

        if self.drop_timer <= 0:
            waiting = [
                e for e in self.enemies
                if e.active and e.state == "waiting"
            ]

            if waiting:
                enemy = random.choice(waiting)
                enemy.start_drop(
                    self.player.x + self.player.width // 2,
                    self.player.y + self.player.height // 2,
                )

            self.drop_timer = max(20, self.cfg["drop"] - self.level * 5)

        for enemy in self.enemies:
            enemy.update()

        if self.boss:
            self.boss_bullets.extend(
                self.boss.update(self.player, self.level)
            )

        for eb in self.boss_bullets:
            eb.update()

        for bullet in self.bullets:
            bullet.update()

        for bullet in self.bullets:
            if not bullet.is_active:
                continue

            for enemy in self.enemies:
                if not enemy.active:
                    continue

                if bullet.get_rect().colliderect(enemy.get_rect()):
                    bullet.is_active = False
                    enemy.active = False
                    self.score += 10
                    break

        if self.boss and self.boss.vulnerable:
            for bullet in self.bullets:
                if not bullet.is_active:
                    continue

                if bullet.get_rect().colliderect(self.boss.get_rect()):
                    bullet.is_active = False
                    self.score += 5

                    if self.boss.hit(1):
                        self.score += 200 + 100 * (self.level // BOSS_EVERY)
                        self.boss = None
                        self.boss_bullets = []
                        break

        if not self.player.is_blinking:
            hit = False

            for enemy in self.enemies:
                if (
                    enemy.active
                    and enemy.state == "dropping"
                    and enemy.get_rect().colliderect(
                        self.player.get_rect()
                    )
                ):
                    enemy.active = False
                    hit = True
                    break

            if not hit:
                body = self.player.get_rect().inflate(-30, -30)

                for eb in self.boss_bullets:
                    if eb.active and eb.get_rect().colliderect(body):
                        eb.active = False
                        hit = True
                        break

            if hit:
                self.hurt_player()
        else:
            self.blink_frames += 1

            if self.blink_frames >= 90:
                self.player.is_blinking = False
                self.player.visible = True
                self.blink_frames = 0

        self.bullets = [b for b in self.bullets if b.is_active]
        self.boss_bullets = [b for b in self.boss_bullets if b.active]

        if (
            self.game_state == "playing"
            and self.boss is None
            and not any(e.active for e in self.enemies)
        ):
            self.level += 1
            self.spawn_level()

    def draw_hud(self):
        f = theme.font(14, True)

        theme.text(
            self.screen, f"SCORE: {self.score:06d}", f, theme.TEXT, (50, 12)
        )
        theme.text(
            self.screen, f"LEVEL: {self.level:02d}", f, theme.TEXT,
            (self.w - 14, 12), "topright"
        )

        for i in range(max(self.lives, 0)):
            self.screen.blit(
                self.life_icon, (self.w - 14 - 22 * (i + 1), 32)
            )

        if self.time_left is not None:
            seconds = (self.time_left + 59) // 60
            theme.text(
                self.screen, f"TIME: {seconds:02d}", f, theme.PINK_LIGHT,
                (self.w // 2, 12), "midtop"
            )

        if self.boss:
            theme.text(
                self.screen, self.boss.name, theme.font(11, True),
                theme.PINK_LIGHT, (self.w // 2, 29), "midtop"
            )

            bar = pygame.Rect(self.w // 2 - 100, 43, 200, 7)
            ratio = max(0.0, self.boss.hp / self.boss.max_hp)
            fill = pygame.Rect(bar.x, bar.y, int(bar.w * ratio), bar.h)

            pygame.draw.rect(self.screen, (40, 6, 38), bar, border_radius=4)

            if fill.w > 0:
                pygame.draw.rect(
                    self.screen, (255, 60, 90), fill, border_radius=4
                )

            pygame.draw.rect(
                self.screen, theme.PINK_LIGHT, bar, 1, border_radius=4
            )

    def draw_banner(self):
        if self.banner_timer <= 0:
            return

        theme.heading(
            self.screen, self.banner_text, theme.title_font(15),
            theme.TEXT, (self.w // 2, 300), "center", t=1
        )

    def draw_pause_button(self):
        hover = self.pause_btn.collidepoint(pygame.mouse.get_pos())

        theme.draw_button(
            self.screen, self.pause_btn, "", theme.font(12), hover,
            radius=8
        )

        cx, cy = self.pause_btn.center
        pygame.draw.rect(self.screen, theme.TEXT, (cx - 6, cy - 7, 4, 14))
        pygame.draw.rect(self.screen, theme.TEXT, (cx + 2, cy - 7, 4, 14))

    def draw_paused(self):
        theme.draw_dim(self.screen, self.w, self.h, 190)
        theme.draw_panel(
            self.screen, self.pause_panel, fill=theme.PANEL_DARK
        )

        theme.heading(
            self.screen, "PAUSED", theme.title_font(28), theme.PINK_LIGHT,
            (self.w // 2, 205), "center"
        )

        mouse = pygame.mouse.get_pos()

        cosmetics.button(
            self.screen, self.resume_btn, "RESUME", theme.font(18, True),
            self.resume_btn.collidepoint(mouse), primary=True, icon="play"
        )
        cosmetics.button(
            self.screen, self.pause_settings_btn, "SETTINGS",
            theme.font(18, True),
            self.pause_settings_btn.collidepoint(mouse), icon="gear"
        )
        cosmetics.button(
            self.screen, self.pause_home_btn, "MENU", theme.font(18, True),
            self.pause_home_btn.collidepoint(mouse), icon="home"
        )

    def draw_game_over(self):
        theme.draw_dim(self.screen, self.w, self.h, 190)

        panel = pygame.Rect(self.w // 2 - 190, 110, 380, 410)
        theme.draw_panel(self.screen, panel, fill=theme.PANEL_DARK)

        theme.heading(
            self.screen, "GAME OVER", theme.title_font(38),
            theme.PINK_LIGHT, (self.w // 2, 158), "center"
        )
        theme.text(
            self.screen, "YOUR SCORE", theme.font(14), theme.MUTED,
            (self.w // 2, 210), "center"
        )
        theme.text(
            self.screen, f"{self.score:,}", theme.font(36, True),
            theme.TEXT, (self.w // 2, 245), "center"
        )
        theme.text(
            self.screen, f"LEVEL REACHED: {self.level}", theme.font(15),
            theme.MUTED, (self.w // 2, 284), "center"
        )

        label = f"HIGHEST LEVEL: {self.best_level}"
        f = theme.font(16, True)
        tw = f.size(label)[0]

        cosmetics.draw_icon(
            self.screen, "star", self.w // 2 - tw // 2 - 14, 314,
            (255, 200, 90), 1.1
        )
        theme.text(
            self.screen, label, f, theme.TEXT,
            (self.w // 2 + 8, 314), "center"
        )

        mouse = pygame.mouse.get_pos()

        cosmetics.button(
            self.screen, self.again_btn, "PLAY AGAIN", theme.font(18, True),
            self.again_btn.collidepoint(mouse), primary=True, icon="play"
        )
        cosmetics.button(
            self.screen, self.home_btn, "MENU", theme.font(18, True),
            self.home_btn.collidepoint(mouse), icon="home"
        )
        cosmetics.button(
            self.screen, self.board_btn, "LEADERBOARD", theme.font(18, True),
            self.board_btn.collidepoint(mouse), icon="trophy"
        )

    def draw(self):
        theme.draw_live_backdrop(
            self.screen, self.w, self.h,
            0 if self.game_state in ("paused", "open_settings")
            else (2.2 if self.boss else 1.0)
        )

        for enemy in self.enemies:
            enemy.draw(self.screen)

        if self.boss:
            self.boss.draw(self.screen)

        for eb in self.boss_bullets:
            eb.draw(self.screen)

        for bullet in self.bullets:
            bullet.draw(self.screen)

        self.player.draw(self.screen)
        self.draw_hud()
        self.draw_banner()

        if self.settings.get("controls") == "mobile":
            self.mobile.draw(self.screen)

        self.draw_pause_button()

        if self.game_state in ("game_over", "open_leader"):
            self.draw_game_over()
        elif self.game_state in ("paused", "open_settings"):
            self.draw_paused()