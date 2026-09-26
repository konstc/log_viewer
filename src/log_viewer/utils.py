""" Log viewer's extra utilites module """

import json
import os
import sys

from pathlib import Path

from exceptions import LogViewerInvalidConfig
from settings_schema import APP_SETTINGS_SCHEMA

def _get_base_path() -> Path:
    """
    Gets base path to the current directory
    """
    try:
        base_path = Path(getattr(sys, "_MEIPASS"))
    except AttributeError:
        base_path = Path.cwd()
    return base_path

def get_cache_path() -> Path:
    """
    Gets path to the per-user cache folder of the application
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or \
               Path.home() / "AppData" / "Local"
    else:
        base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "log_viewer"

def setup_matplotlib_cache() -> None:
    """
    Keeps matplotlib's font cache between runs of a PyInstaller bundle. The
    bundle's runtime hook points matplotlib to a new temporary folder on every
    start, so the cache was rebuilt on the first plot of every session. Must
    be called before matplotlib is imported.
    """
    if not getattr(sys, "frozen", False):
        return
    config_path = get_cache_path() / "matplotlib"
    try:
        config_path.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    os.environ["MPLCONFIGDIR"] = str(config_path)

def get_log_path() -> Path:
    """
    Gets path to 'debug.log' file: next to the executable if the application
    is run from a PyInstaller bundle, in the current directory otherwise
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "debug.log"
    return Path.cwd() / "debug.log"

def get_default_settings_path() -> Path:
    """
    Gets path to 'app.json' file with the default settings shipped with the
    application
    """
    return (_get_base_path() / "cfg").resolve() / "app.json"

def get_user_settings_path() -> Path:
    """
    Gets path to 'app.json' file with the settings of the current user
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or \
               Path.home() / "AppData" / "Roaming"
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(base) / "log_viewer" / "app.json"

def _merge_settings(defaults: dict, user: dict, schema: dict) -> dict:
    """
    Returns 'defaults' updated with 'user' values. Objects with properties
    defined by 'schema' are merged recursively, so settings added in newer
    versions get their default values. Other values (e.g. lists or objects
    with arbitrary keys) are taken from 'user' as a whole.
    """
    merged = dict(defaults)
    for key, value in user.items():
        sub_schema = schema.get("properties", {}).get(key, {})
        if "properties" in sub_schema and isinstance(value, dict) and \
                isinstance(merged.get(key), dict):
            merged[key] = _merge_settings(merged[key], value, sub_schema)
        else:
            merged[key] = value
    return merged

def load_settings() -> dict:
    """
    Loads the default settings updated with the settings of the current user
    """
    with open(get_default_settings_path(), "r",
              encoding="utf-8") as settings_file:
        settings = json.load(settings_file)

    user_path = get_user_settings_path()
    if user_path.is_file():
        try:
            with open(user_path, "r", encoding="utf-8") as settings_file:
                user_settings = json.load(settings_file)
        except json.JSONDecodeError as err:
            raise LogViewerInvalidConfig(f"{user_path}: {err}") from err
        settings = _merge_settings(settings, user_settings,
                                   APP_SETTINGS_SCHEMA)
    return settings

def save_settings(settings: dict) -> None:
    """
    Saves 'settings' as the settings of the current user
    """
    user_path = get_user_settings_path()
    user_path.parent.mkdir(parents=True, exist_ok=True)
    with open(user_path, "w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=4)

def get_resource_path() -> Path:
    """
    Gets path to 'resource' folder
    """
    return (_get_base_path() / "resource").resolve()

def get_icons_path() -> Path:
    """
    Gets path to 'icons' folder
    """
    return get_resource_path() / "icons"
