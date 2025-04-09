""" Log viewer's about dialog window module """

from PyQt6.QtWidgets import QDialog

from generated_ui import Ui_AboutDialog
from version import __version__

class AboutDialog(QDialog):
    """
    About window with a common info
    """

    def __init__(self) -> None:
        super().__init__()

        self._ui = Ui_AboutDialog()
        self._ui.setupUi(self)
        about = self._ui.versionLabel.text()
        self._ui.versionLabel.setText(about + __version__)
