""" Unit-tests for utils.py entities """

import json
import os
import sys

import pytest

# modules under test
from exceptions import LogViewerInvalidConfig
from utils import get_cache_path, get_log_path, get_user_settings_path, \
                  load_settings, save_settings, setup_matplotlib_cache

DEFAULT_SETTINGS = {
    "mode": "simple_csv",
    "plot": {"style": "default", "linewidth": 1.0,
             "cursor": {"style": "dashed", "width": 0.75}},
    "simple_csv": {"delimiter": ";", "scales": {"default_scale": 2.0}},
    "j1939_dump": {"asc_base": "hex", "db": ["default.dbc"]}
}

@pytest.fixture
def default_settings(tmp_path, monkeypatch):
    """
    Setup a default settings file
    """
    path = tmp_path / "default_app.json"
    path.write_text(json.dumps(DEFAULT_SETTINGS), encoding="utf-8")
    monkeypatch.setattr("utils.get_default_settings_path", lambda: path)

def test_get_user_settings_path(tmp_path, monkeypatch):
    """
    Unit-test for get_user_settings_path function

    Step 0: Check that %APPDATA% is used on Windows
    Step 1: Check that $XDG_CONFIG_HOME is used on other platforms
    """
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    assert get_user_settings_path() == \
                                   tmp_path / "roaming" / "log_viewer" / "app.json"

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    assert get_user_settings_path() == \
                                    tmp_path / "config" / "log_viewer" / "app.json"

# pylint: disable-next=unused-argument,redefined-outer-name
def test_load_save_settings(default_settings):
    """
    Unit-tests for load_settings and save_settings functions

    Step 0: Check that the default settings are loaded if the user has no
        settings file
    Step 1: Save changed settings and check that they are written into the
        user settings file and loaded back
    Step 2: Check that settings missing in the user settings file get their
        default values, while lists and objects with arbitrary keys are taken
        from the user settings as a whole
    Step 3: Check that an invalid user settings file leads to a
        LogViewerInvalidConfig exception with its path in the message
    """
    assert load_settings() == DEFAULT_SETTINGS

    settings = load_settings()
    settings["plot"]["cursor"]["width"] = 0.5
    settings["simple_csv"]["scales"] = {"user_scale": 3.0}
    settings["j1939_dump"]["db"] = []
    save_settings(settings)
    assert get_user_settings_path().is_file()
    assert load_settings() == settings

    get_user_settings_path().write_text(json.dumps({
        "plot": {"cursor": {"width": 0.5}},
        "simple_csv": {"scales": {"user_scale": 3.0}}
    }), encoding="utf-8")
    loaded = load_settings()
    assert loaded["mode"] == "simple_csv"
    assert loaded["plot"] == {"style": "default", "linewidth": 1.0,
                              "cursor": {"style": "dashed", "width": 0.5}}
    assert loaded["simple_csv"] == {"delimiter": ";",
                                    "scales": {"user_scale": 3.0}}
    assert loaded["j1939_dump"] == DEFAULT_SETTINGS["j1939_dump"]

    get_user_settings_path().write_text("{ not json", encoding="utf-8")
    with pytest.raises(LogViewerInvalidConfig,
                       match=str(get_user_settings_path()).replace("\\", "\\\\")):
        load_settings()

def test_get_cache_path(tmp_path, monkeypatch):
    """
    Unit-test for get_cache_path function

    Step 0: Check that %LOCALAPPDATA% is used on Windows
    Step 1: Check that $XDG_CACHE_HOME is used on other platforms
    """
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    assert get_cache_path() == tmp_path / "local" / "log_viewer"

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    assert get_cache_path() == tmp_path / "cache" / "log_viewer"

def test_setup_matplotlib_cache(tmp_path, monkeypatch):
    """
    Unit-test for setup_matplotlib_cache function

    Step 0: Check that matplotlib's config folder is not changed when the
        application is run from sources
    Step 1: Check that the persistent cache folder is created and used when
        the application is run from a PyInstaller bundle
    """
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("MPLCONFIGDIR", "unchanged")

    setup_matplotlib_cache()
    assert os.environ["MPLCONFIGDIR"] == "unchanged"

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    setup_matplotlib_cache()
    config_path = tmp_path / "log_viewer" / "matplotlib"
    assert os.environ["MPLCONFIGDIR"] == str(config_path)
    assert config_path.is_dir()

def test_get_log_path(tmp_path, monkeypatch):
    """
    Unit-test for get_log_path function

    Step 0: Check that the log is placed in the current directory when the
        application is run from sources
    Step 1: Check that the log is placed next to the executable when the
        application is run from a PyInstaller bundle
    """
    monkeypatch.chdir(tmp_path)
    assert get_log_path() == tmp_path / "debug.log"

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "app" / "app.exe"))
    assert get_log_path() == tmp_path / "app" / "debug.log"
