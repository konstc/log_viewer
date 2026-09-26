""" Log viewer's main application module """

import argparse
import json
import locale
import logging
import sys
import os
from pathlib import Path
import platform
import tempfile

import jsonschema
from PyQt6 import QtGui
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget

from exceptions import LogViewerInvalidConfig
from main_window import MainWindow
from utils import get_log_path, setup_matplotlib_cache
from version import __version__

locale.setlocale(locale.LC_ALL, "")

basedir = os.path.dirname(__file__)

cur_platform = platform.system()
if cur_platform == "Windows":
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("KonstC.LogViewer")
    except ImportError:
        pass

def setup_logging() -> None:
    """
    Configures logging into 'debug.log'. Falls back to the temporary directory
    if the default location is not writable.
    """
    log_format = "%(asctime)s %(levelname)s %(message)s"
    try:
        logging.basicConfig(level=logging.INFO, filename=get_log_path(),
                            filemode="w", format=log_format)
    except OSError:
        logging.basicConfig(level=logging.INFO,
                            filename=Path(tempfile.gettempdir()) / "debug.log",
                            filemode="w", format=log_format)

def show_instead_of_splash(widget: QWidget) -> None:
    """
    Shows 'widget' and closes the splash screen shown by the PyInstaller
    bootloader (if the application is run from a PyInstaller bundle)
    """
    widget.show()
    # Activate the widget while the splash screen still holds the foreground,
    # otherwise Windows opens it behind other windows
    widget.raise_()
    widget.activateWindow()
    try:
        import pyi_splash # pylint: disable=import-outside-toplevel
        pyi_splash.close()
    except ImportError:
        pass

if __name__ == "__main__":
    setup_logging()
    setup_matplotlib_cache()

    parser = argparse.ArgumentParser(
        description="GUI tool for viewing various types of logs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--version",
                        action="version",
                        version=__version__,
                        help="Print version information and exit")

    args = parser.parse_args()

    app = QApplication([])
    app.setWindowIcon(
        QtGui.QIcon(os.path.join(basedir, "icon.ico"))
    )

    try:
        window = MainWindow()
        show_instead_of_splash(window)
        sys.exit(app.exec())
    except (LogViewerInvalidConfig,
            json.decoder.JSONDecodeError,
            jsonschema.ValidationError) as err:
        logging.error(err, exc_info=True)
        msg_box = QMessageBox(QMessageBox.Icon.Critical, "Critical error",
                              str(err))
        show_instead_of_splash(msg_box)
        msg_box.exec()
        sys.exit(0)
