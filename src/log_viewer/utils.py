""" Log viewer's extra utilites module """

from pathlib import Path

APP_RESOURCE_PATH = "resource"
APP_SETTINGS_PATH = "cfg"

def get_settings_path() -> Path:
    """
    Gets path to 'app.json' file
    """
    return Path(APP_SETTINGS_PATH).resolve() / "app.json"

def get_resource_path() -> Path:
    """
    Gets path to 'resource' folder
    """
    return Path(APP_RESOURCE_PATH).resolve()

def get_icons_path() -> Path:
    """
    Gets path to 'icons' folder
    """
    return get_resource_path() / "icons"
