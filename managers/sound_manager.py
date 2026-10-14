import os
import pygame

from managers.settings_manager import load_settings

MUSIC_FILE = "assets/sounds/nicmusic.mp3"
CLICK_FILE = "assets/sounds/nicbutton.mp3"
SHOOT_FILE = "assets/sounds/nicllet.mp3"


class SoundManager:
    def __init__(self):
        self.available = True
        self.music_loaded = False

        try:
            pygame.mixer.init()
        except pygame.error as e:
            print(f"Audio Error: {e}")
            self.available = False

        self.click_sound = self._load(CLICK_FILE)
        self.shoot_sound = self._load(SHOOT_FILE)

        self.settings = load_settings()
        self.apply(self.settings)

    def _load(self, path):
        if not self.available:
            return None

        if not os.path.exists(path):
            print(f"Sound file not found: {path}")
            return None

        try:
            return pygame.mixer.Sound(path)
        except pygame.error as e:
            print(f"Sound Error ({path}): {e}")
            return None

    @staticmethod
    def _volume(value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = 70

        return max(0, min(100, value)) / 100

    def _music_level(self):
        if not self.settings.get("music_on", True):
            return 0.0

        return self._volume(self.settings.get("volume", 70))

    def _sfx_level(self):
        if not self.settings.get("sound_on", True):
            return 0.0

        return self._volume(self.settings.get("volume", 70))

    def apply(self, settings=None):
        if settings is not None:
            self.settings = settings

        if not self.available:
            return

        pygame.mixer.music.set_volume(self._music_level())

        sfx = self._sfx_level()

        for s in (self.click_sound, self.shoot_sound):
            if s:
                s.set_volume(sfx)

        self.play_music()

    def play_music(self):
        if not self.available or self.music_loaded:
            return

        if not os.path.exists(MUSIC_FILE):
            print(f"Sound file not found: {MUSIC_FILE}")
            return

        try:
            pygame.mixer.music.load(MUSIC_FILE)
            pygame.mixer.music.set_volume(self._music_level())
            pygame.mixer.music.play(-1)
            self.music_loaded = True
        except pygame.error as e:
            print(f"Music Error: {e}")

    def play_click(self):
        if self.click_sound:
            self.click_sound.play()

    def play_shoot(self):
        if self.shoot_sound:
            self.shoot_sound.play()


sound = SoundManager()