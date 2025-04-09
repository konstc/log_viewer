""" Log viewer's main application module """

import argparse
import json
import locale
import logging
import sys
import os
import platform

import jsonschema
import matplotlib
from PyQt6 import QtGui
from PyQt6.QtWidgets import QApplication, QMessageBox

from exceptions import LogViewerInvalidConfig
from main_window import MainWindow
from version import __version__

locale.setlocale(locale.LC_ALL, "")
matplotlib.use("qtagg")

APP_LOG_PATH = "debug.log"

basedir = os.path.dirname(__file__)

cur_platform = platform.system()
if cur_platform == "Windows":
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("KonstC.LogViewer")
    except ImportError:
        pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        filename=APP_LOG_PATH,
                        filemode="w",
                        format="%(asctime)s %(levelname)s %(message)s")

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
        window.show()
        sys.exit(app.exec())
    except (LogViewerInvalidConfig,
            json.decoder.JSONDecodeError,
            jsonschema.ValidationError) as err:
        logging.error(err, exc_info=True)
        QMessageBox.critical(None, "Critical error", str(err))
        sys.exit(0)
