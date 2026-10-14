import pygame

from db import login_player, register_player
from managers import theme
from managers.sound_manager import sound
from managers.ui import TextInput


class LoginManager:
    def __init__(self, screen, w, h):
        self.screen = screen
        self.w = w
        self.h = h

        self.logged_in_player = None
        self.view = "login"
        self.message = ""
        self.message_ok = False

        pw = 420
        px = w // 2 - pw // 2
        fx = px + 30
        fw = pw - 60

        self.login_panel = pygame.Rect(px, 185, pw, 262)
        self.create_panel = pygame.Rect(px, 172, pw, 314)

        L = self.login_panel
        C = self.create_panel

        self.login_inputs = [
            TextInput(pygame.Rect(fx, L.y + 56, fw, 42),
                      "Username", "user"),
            TextInput(pygame.Rect(fx, L.y + 106, fw, 42),
                      "Password", "lock", password=True),
        ]
        self.login_btn = pygame.Rect(fx, L.y + 174, fw, 44)
        self.login_msg_y = L.y + 153

        self.create_inputs = [
            TextInput(pygame.Rect(fx, C.y + 56, fw, 42),
                      "Player Name", "user"),
            TextInput(pygame.Rect(fx, C.y + 106, fw, 42),
                      "Password", "lock", password=True),
            TextInput(pygame.Rect(fx, C.y + 156, fw, 42),
                      "Confirm Password", "lock", password=True),
        ]
        self.create_btn = pygame.Rect(fx, C.y + 228, fw, 44)
        self.create_msg_y = C.y + 203

        self.link_rect = pygame.Rect(0, 0, 0, 0)

    def inputs(self):
        return (
            self.login_inputs
            if self.view == "login"
            else self.create_inputs
        )

    def set_message(self, text, ok=False):
        self.message = text
        self.message_ok = ok

    def switch_view(self, view, message="", ok=False):
        self.view = view

        for box in self.login_inputs + self.create_inputs:
            box.clear()

        self.set_message(message, ok)

    def cycle_focus(self):
        boxes = self.inputs()
        current = -1

        for i, box in enumerate(boxes):
            if box.active:
                current = i

        for box in boxes:
            box.active = False

        boxes[(current + 1) % len(boxes)].active = True

    def submit_login(self):
        username = self.login_inputs[0].text.strip()
        password = self.login_inputs[1].text

        if not username or not password:
            self.set_message("FILL IN ALL FIELDS")
            return

        player = login_player(username, password)

        if player is None:
            self.set_message("INVALID USERNAME OR PASSWORD")
            return

        self.set_message("")
        self.logged_in_player = player

        for box in self.login_inputs:
            box.clear()

    def submit_create(self):
        username = self.create_inputs[0].text.strip()
        password = self.create_inputs[1].text
        confirm = self.create_inputs[2].text

        if not username or not password or not confirm:
            self.set_message("FILL IN ALL FIELDS")
            return

        if len(username) < 3:
            self.set_message("NAME MUST BE AT LEAST 3 CHARACTERS")
            return

        if len(password) < 4:
            self.set_message("PASSWORD MUST BE AT LEAST 4 CHARACTERS")
            return

        if password != confirm:
            self.set_message("PASSWORDS DO NOT MATCH")
            return

        ok, msg = register_player(username, password)

        if ok:
            self.switch_view("login", "ACCOUNT CREATED! PLEASE LOGIN", True)
        else:
            self.set_message(msg)

    def submit(self):
        if self.view == "login":
            self.submit_login()
        else:
            self.submit_create()

    def handle_events(self, events):
        for event in events:
            for box in self.inputs():
                box.handle_event(event)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.cycle_focus()

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.submit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                btn = (
                    self.login_btn
                    if self.view == "login"
                    else self.create_btn
                )

                if btn.collidepoint(event.pos):
                    sound.play_click()
                    self.submit()

                elif self.link_rect.collidepoint(event.pos):
                    sound.play_click()

                    if self.view == "login":
                        self.switch_view("create")
                    else:
                        self.switch_view("login")

    def draw_link_line(self, y, prefix, link):
        f = theme.font(14)
        fb = theme.font(14, True)

        a = f.render(prefix + " ", True, theme.TEXT)
        b = fb.render(link, True, theme.PINK_LIGHT)

        total = a.get_width() + b.get_width()
        x = self.w // 2 - total // 2

        self.screen.blit(a, (x, y))
        self.screen.blit(b, (x + a.get_width(), y))

        self.link_rect = pygame.Rect(
            x + a.get_width(), y - 4, b.get_width(), b.get_height() + 8
        )

        pygame.draw.line(
            self.screen, theme.PINK_LIGHT,
            (self.link_rect.x, y + b.get_height() + 1),
            (self.link_rect.right, y + b.get_height() + 1), 1
        )

    def draw(self):
        theme.draw_backdrop(self.screen, self.w, self.h, "login")

        theme.draw_invader(self.screen, 100, 120, 5)
        theme.draw_invader(self.screen, self.w - 100, 120, 5)

        theme.draw_title(self.screen, self.w // 2, 20, 52)

        mouse = pygame.mouse.get_pos()

        if self.view == "login":
            panel = self.login_panel
            heading = "LOGIN"
            btn = self.login_btn
            btn_text = "Login"
            msg_y = self.login_msg_y
            link_y = panel.y + 230
        else:
            panel = self.create_panel
            heading = "CREATE ACCOUNT"
            btn = self.create_btn
            btn_text = "Sign Up"
            msg_y = self.create_msg_y
            link_y = panel.y + 284

        theme.draw_panel(self.screen, panel)

        theme.text(
            self.screen, heading, theme.font(22, True), theme.TEXT,
            (panel.centerx, panel.y + 28), "center"
        )

        for box in self.inputs():
            box.draw(self.screen)

        if self.message:
            color = theme.PINK_SOFT if self.message_ok else (255, 120, 150)
            theme.text(
                self.screen, self.message, theme.font(13, True), color,
                (panel.centerx, msg_y + 9), "center"
            )

        theme.draw_button(
            self.screen, btn, btn_text, theme.font(19, True),
            btn.collidepoint(mouse), primary=True
        )

        if self.view == "login":
            self.draw_link_line(
                link_y, "Don't have an account?", "Create Account"
            )
        else:
            self.draw_link_line(
                link_y, "Already have an account?", "Login"
            )

        theme.draw_ship(self.screen, self.w // 2, 528)