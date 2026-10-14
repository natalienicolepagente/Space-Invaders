import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "volume": 70,
    "sound_on": True,
    "music_on": True,
    "controls": "keyboard",
}

VALID_CONTROLS = ("keyboard", "mobile")


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as file:
            json.dump(settings, file, indent=4)
    except IOError as e:
        print(f"Settings Save Error: {e}")


def _clean(settings):
    if settings.get("controls") == "mouse":
        settings["controls"] = "mobile"

    if settings.get("controls") not in VALID_CONTROLS:
        settings["controls"] = "keyboard"

    try:
        settings["volume"] = max(0, min(100, int(settings["volume"])))
    except (TypeError, ValueError):
        settings["volume"] = DEFAULT_SETTINGS["volume"]

    settings["sound_on"] = bool(settings.get("sound_on", True))
    settings["music_on"] = bool(settings.get("music_on", True))

    return settings


def load_settings():
    settings = dict(DEFAULT_SETTINGS)

    if not os.path.exists(SETTINGS_FILE):
        save_settings(settings)
        return settings

    try:
        with open(SETTINGS_FILE, "r") as file:
            data = json.load(file)

        if isinstance(data, dict):
            for key in DEFAULT_SETTINGS:
                if key in data:
                    settings[key] = data[key]

            if "volume" not in data and "music_volume" in data:
                settings["volume"] = data["music_volume"]

    except (json.JSONDecodeError, IOError):
        pass

    return _clean(settings)