import pygame

pygame.init()
pygame.key.set_repeat(400, 35)

from db import setup_database
from managers.login import LoginManager
from managers.game_manager import GameManager
from managers.home import Home
from managers.mode_select import ModeSelect
from managers.profile import Profile
from managers.leader import Leader
from managers.settings import Settings
from managers.settings_manager import load_settings
from managers.sound_manager import sound

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders by Pagente, Natalie Nicole")

setup_database()

login = LoginManager(screen, SCREEN_WIDTH, SCREEN_HEIGHT)
game = GameManager(screen, SCREEN_WIDTH, SCREEN_HEIGHT)

home = None
mode_select = None
profile = None
leader = None
settings = None
current_screen = "login"

settings_return = "home"
leader_return = "home"

sound.play_music()

clock = pygame.time.Clock()
running = True


def new_home():
    return Home(
        screen, SCREEN_WIDTH, SCREEN_HEIGHT, login.logged_in_player
    )


while running:

    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            running = False

    if current_screen == "login":

        login.handle_events(events)
        login.draw()

        if login.logged_in_player is not None:
            home = new_home()
            current_screen = "home"

    elif current_screen == "home":

        home.handle_events(events)
        home.draw()

        action = home.action
        home.action = None

        if action == "play":
            mode_select = ModeSelect(screen, SCREEN_WIDTH, SCREEN_HEIGHT)
            current_screen = "mode"

        elif action == "profile":
            profile = Profile(
                screen, SCREEN_WIDTH, SCREEN_HEIGHT,
                login.logged_in_player
            )
            current_screen = "profile"

        elif action == "leaderboard":
            leader_return = "home"
            leader = Leader(
                screen, SCREEN_WIDTH, SCREEN_HEIGHT,
                login.logged_in_player
            )
            current_screen = "leader"

        elif action == "settings":
            settings_return = "home"
            settings = Settings(
                screen, SCREEN_WIDTH, SCREEN_HEIGHT,
                login.logged_in_player
            )
            current_screen = "settings"

        elif action == "logout":
            login.logged_in_player = None
            login.switch_view("login")
            home = None
            current_screen = "login"

    elif current_screen == "mode":

        mode_select.handle_events(events)
        mode_select.draw()

        action = mode_select.action
        mode_select.action = None

        if action == "back":
            home = new_home()
            current_screen = "home"

        elif action in ("classic", "survival", "timeattack"):
            game.current_player_id = login.logged_in_player["player_id"]
            game.player_name = login.logged_in_player["username"]
            game.ship_id = login.logged_in_player.get("ship", 1)
            game.start_again(action)
            current_screen = "game"

    elif current_screen == "profile":

        profile.handle_events(events)
        profile.draw()

        if profile.action == "back":
            profile.action = None
            home = new_home()
            current_screen = "home"

    elif current_screen == "leader":

        leader.handle_events(events)
        leader.draw()

        if leader.action == "back":
            leader.action = None

            if leader_return == "game":
                game.game_state = "game_over"
                current_screen = "game"
            else:
                home = new_home()
                current_screen = "home"

    elif current_screen == "settings":

        settings.handle_events(events)
        settings.draw()

        if settings.action == "back":
            settings.action = None

            if settings_return == "game":
                game.settings = load_settings()
                game.mobile.reset()
                game.game_state = "paused"
                current_screen = "game"
            else:
                home = new_home()
                current_screen = "home"

    elif current_screen == "game":

        game.update(events)
        game.draw()

        if game.game_state == "back_home":
            game.game_state = "playing"
            home = new_home()
            current_screen = "home"

        elif game.game_state == "open_settings":
            settings_return = "game"
            settings = Settings(
                screen, SCREEN_WIDTH, SCREEN_HEIGHT,
                login.logged_in_player
            )
            current_screen = "settings"

        elif game.game_state == "open_leader":
            leader_return = "game"
            leader = Leader(
                screen, SCREEN_WIDTH, SCREEN_HEIGHT,
                login.logged_in_player
            )
            current_screen = "leader"

    pygame.display.update()
    clock.tick(60)

pygame.quit()