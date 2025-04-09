""" Log viewer's toolbar module """

import enum

from PyQt6.QtWidgets import QComboBox, QToolBar
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

class PlotMode(enum.Enum):
    """
    Available plot modes list
    """
    PLOTMODE_MERGED = 0
    PLOTMODE_SEPARATED = 1
    PLOTMODE_MANUAL = 2

class LogViewerToolbar(QToolBar):
    """
    Log viewer's main toolbar
    """

    plot_mode_updated = pyqtSignal()

    @property
    def plot_mode(self) -> PlotMode:
        """
        Gets selected plot mode
        """
        return self._plot_mode

    @property
    def plot_mode_box(self) -> QComboBox:
        """
        Gets QComboBox object representing plot mode
        """
        return self._plot_mode_box

    def __init__(self, parent = None) -> None:
        super().__init__(parent)

        self._plot_mode = PlotMode.PLOTMODE_MERGED

        self._plot_mode_box = QComboBox(parent=self)
        self._plot_mode_box.setEnabled(False)
        self._plot_mode_box.addItems(["Merged plot",
                                      "Separated plots",
                                      "Manual assignment"])
        self._plot_mode_box.activated.connect(self.plot_mode_changed)
        self.addWidget(self._plot_mode_box)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)

    @pyqtSlot(int)
    def plot_mode_changed(self, mode_idx: int) -> None:
        """
        Updates internal states and emits signals while self._plot_mode updated
        """
        self._plot_mode = PlotMode(mode_idx)
        self.plot_mode_updated.emit()
