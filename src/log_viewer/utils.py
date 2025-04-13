""" Log viewer's extra utilites module """

import sys

from pathlib import Path

def _get_base_path() -> Path:
    """
    Gets base path to the current directory
    """
    try:
        base_path = Path(getattr(sys, "_MEIPASS"))
    except AttributeError:
        base_path = Path.cwd()
    return base_path

def get_settings_path() -> Path:
    """
    Gets path to 'app.json' file
    """
    return (_get_base_path() / "cfg").resolve() / "app.json"

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
