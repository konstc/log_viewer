""" Log viewer's settings dialog window module """

from dataclasses import dataclass
import locale
from pathlib import Path

import matplotlib.pyplot as plt
from PyQt6.QtGui import QDoubleValidator, QRegularExpressionValidator
from PyQt6.QtCore import Qt, QRegularExpression, pyqtSlot
from PyQt6.QtWidgets import QDialog, QFileDialog, QLineEdit, QTableWidgetItem

from generated_ui import Ui_SettingsDialog

@dataclass
class CursorSettings:
    """ Cursor appearance settings """
    style: str = "dashed"
    width: float = 0.5
    color: str = "red"

@dataclass
class AppearanceSettings:
    """ Plot appearance settings """
    cursor: CursorSettings
    plotstyle: str = "default"
    linestyle: str = "solid"
    linewidth: float = 1.0
    marker: bool = False
    use_mpl_toolbar: bool = False

@dataclass
class SimpleCsvSettings:
    """ Simple CSV plotter settings """
    delimiter: str = ";"
    timestamp: str = "timestamp"
    scales: dict = None

@dataclass
class J1939DumpSettings:
    """ J1939 dump plotter settings """
    asc_base: str = "hex"
    rel_timestamp: bool = True
    databases: list = None

@dataclass
class SettingsData:
    """ All settings to save/export """
    mode: str
    appearance: AppearanceSettings
    simple_csv: SimpleCsvSettings
    j1939_dump: J1939DumpSettings

class SettingsDialog(QDialog):
    """
    Dialog window for edit Log Viewer settings
    """

    # pylint: disable-next=too-many-statements
    def __init__(self,
                 settings: SettingsData) -> None:

        super().__init__()

        self._settings = settings

        if self._settings.simple_csv.scales is None:
            self._settings.simple_csv.scales = {}

        if self._settings.j1939_dump.databases is None:
            self._settings.j1939_dump.databases = []

        self._ui = Ui_SettingsDialog()
        self._ui.setupUi(self)

        self._scale_name_edits = []
        self._scale_value_edits = []

        # General tab -------------------------------------

        if self._settings.mode == "simple_csv":
            self._ui.tabWidget.setTabEnabled(1, True)
            self._ui.tabWidget.setTabEnabled(2, False)
            self._ui.modeSelectorBox.setCurrentIndex(0)
        elif self._settings.mode == "j1939_dump":
            self._ui.tabWidget.setTabEnabled(1, False)
            self._ui.tabWidget.setTabEnabled(2, True)
            self._ui.modeSelectorBox.setCurrentIndex(1)
        else:
            self._ui.tabWidget.setTabEnabled(1, False)
            self._ui.tabWidget.setTabEnabled(2, False)

        style_list = ["default"] + plt.style.available
        self._ui.plotStyleSelectorBox.addItems(style_list)
        self._ui.plotStyleSelectorBox.setCurrentText(
            self._settings.appearance.plotstyle
        )

        self._ui.lineStyleSelectorBox.setCurrentText(
            self._settings.appearance.linestyle
        )

        self._ui.lineWidthSelectorBox.setCurrentText(
            str(self._settings.appearance.linewidth)
        )

        self._ui.enableMarkersBox.setChecked(
            self._settings.appearance.marker
        )

        self._ui.cursorStyleSelectorBox.setCurrentText(
            self._settings.appearance.cursor.style
        )
        self._ui.cursorStyleSelectorBox.setDisabled(
            self._settings.appearance.use_mpl_toolbar
        )

        self._ui.cursorWidthSelectorBox.setCurrentText(
            str(self._settings.appearance.cursor.width)
        )
        self._ui.cursorWidthSelectorBox.setDisabled(
            self._settings.appearance.use_mpl_toolbar
        )

        self._ui.cursorColorSelectorBox.setCurrentText(
            self._settings.appearance.cursor.color
        )
        self._ui.cursorColorSelectorBox.setDisabled(
            self._settings.appearance.use_mpl_toolbar
        )

        self._ui.enableMplToolbarBox.setChecked(
            self._settings.appearance.use_mpl_toolbar
        )

        # Simple CSV reader tab ---------------------------

        self._ui.simpleCsvAliasEdit.setText(
            self._settings.simple_csv.delimiter
        )
        self._ui.simpleCsvAliasEdit.setValidator(
            QRegularExpressionValidator(QRegularExpression("\\S+"))
        )
        self._ui.simpleCsvTimestampEdit.setText(
            self._settings.simple_csv.timestamp
        )
        self._ui.simpleCsvTimestampEdit.setValidator(
            QRegularExpressionValidator(QRegularExpression("\\S+"))
        )

        for name, value in self._settings.simple_csv.scales.items():
            name_edit = QLineEdit(name)
            value_edit = QLineEdit(locale.str(value))
            name_edit.setValidator(
                QRegularExpressionValidator(QRegularExpression("\\S+"))
            )
            value_edit.setValidator(QDoubleValidator())
            self._scale_name_edits.append(name_edit)
            self._scale_value_edits.append(value_edit)

        self._ui.scaleTable.setRowCount(len(self._scale_name_edits))

        for row, name_edit in enumerate(self._scale_name_edits):
            name_item = QTableWidgetItem()
            self._ui.scaleTable.setItem(row, 0, name_item)
            self._ui.scaleTable.setCellWidget(row, 0, name_edit)

        for row, value_edit in enumerate(self._scale_value_edits):
            value_item = QTableWidgetItem()
            self._ui.scaleTable.setItem(row, 1, value_item)
            self._ui.scaleTable.setCellWidget(row, 1, value_edit)

        # J1939 dump decoder tab --------------------------

        self._ui.ascBaseSelector.setCurrentText(
            self._settings.j1939_dump.asc_base
        )
        self._ui.relTimestampBox.setChecked(
            self._settings.j1939_dump.rel_timestamp
        )
        self._ui.databaseList.addItems(
            self._settings.j1939_dump.databases
        )

        # Slots configuration -----------------------------

        self._ui.modeSelectorBox.activated.connect(self.mode_changed)
        self._ui.addScaleButton.clicked.connect(self.add_scale)
        self._ui.removeScaleButton.clicked.connect(self.remove_scale)
        self._ui.clearScaleButton.clicked.connect(self.clear_scales)
        self._ui.addDatabaseButton.clicked.connect(self.add_db)
        self._ui.clearDatabaseButton.clicked.connect(self.clear_db)
        self._ui.buttonBox.accepted.connect(self.save_settings)
        self._ui.enableMplToolbarBox.stateChanged.connect(
            self.use_mpl_toolbar_changed
        )

    @pyqtSlot(int)
    def mode_changed(self, mode_index: int) -> None:
        """
        Enables/disables widgets due mode changing
        """
        if mode_index == 0:
            self._ui.tabWidget.setTabEnabled(1, True)
            self._ui.tabWidget.setTabEnabled(2, False)
        elif mode_index == 1:
            self._ui.tabWidget.setTabEnabled(1, False)
            self._ui.tabWidget.setTabEnabled(2, True)
        else:
            self._ui.tabWidget.setTabEnabled(1, False)
            self._ui.tabWidget.setTabEnabled(2, False)

    @pyqtSlot(int)
    def use_mpl_toolbar_changed(self, state: int) -> None:
        """
        Enables/disables widgets due 'Use matplotlib toolbar' checkbox changing
        """
        checked = state == Qt.CheckState.Checked.value
        self._ui.cursorStyleSelectorBox.setDisabled(checked)
        self._ui.cursorWidthSelectorBox.setDisabled(checked)
        self._ui.cursorColorSelectorBox.setDisabled(checked)

    @pyqtSlot()
    def add_scale(self) -> None:
        """
        Adds new scale row to self._ui.scaleTable
        """
        name_edit = QLineEdit("ValueName")
        value_edit = QLineEdit(locale.str(1.0))
        name_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression("\\S+"))
        )
        value_edit.setValidator(QDoubleValidator())
        self._scale_name_edits.append(name_edit)
        self._scale_value_edits.append(value_edit)

        self._ui.scaleTable.setRowCount(len(self._scale_name_edits))

        row = len(self._scale_name_edits) - 1
        name_item = QTableWidgetItem()
        self._ui.scaleTable.setItem(row, 0, name_item)
        self._ui.scaleTable.setCellWidget(row, 0, self._scale_name_edits[-1])
        value_item = QTableWidgetItem()
        self._ui.scaleTable.setItem(row, 1, value_item)
        self._ui.scaleTable.setCellWidget(row, 1, self._scale_value_edits[-1])

    @pyqtSlot()
    def remove_scale(self) -> None:
        """
        Removes selected scale row from self._ui.scaleTable
        """
        selected_row = self._ui.scaleTable.currentRow()
        if selected_row != -1:
            self._ui.scaleTable.takeItem(selected_row, 0)
            self._ui.scaleTable.takeItem(selected_row, 1)
            self._ui.scaleTable.removeRow(selected_row)
            del self._scale_name_edits[selected_row]
            del self._scale_value_edits[selected_row]

    @pyqtSlot()
    def clear_scales(self) -> None:
        """
        Clears self._ui.scaleTable
        """
        self._scale_name_edits.clear()
        self._scale_value_edits.clear()
        self._ui.scaleTable.clearContents()
        self._ui.scaleTable.setRowCount(0)

    @pyqtSlot()
    def add_db(self) -> None:
        """
        Adds new database row to self._ui.databaseList
        """
        files, _ = QFileDialog.getOpenFileNames(
            None,
            "Open database files",
            "./",
            "DBC (*.dbc)"
        )
        if files:
            paths = [str(Path(d)) for d in files]
            self._ui.databaseList.clear()
            self._ui.databaseList.addItems(paths)

    @pyqtSlot()
    def clear_db(self) -> None:
        """
        Clears self._ui.databaseList
        """
        self._ui.databaseList.clear()

    @pyqtSlot()
    def save_settings(self) -> None:
        """
        Saves current settings from widgets into self._settings
        """
        if self._ui.modeSelectorBox.currentIndex() == 0:
            self._settings.mode = "simple_csv"
        else:
            self._settings.mode = "j1939_dump"
        self._settings.appearance.plotstyle = \
                                    self._ui.plotStyleSelectorBox.currentText()
        self._settings.appearance.linestyle = \
                                    self._ui.lineStyleSelectorBox.currentText()
        self._settings.appearance.linewidth = float(
            self._ui.lineWidthSelectorBox.currentText()
        )
        self._settings.appearance.marker = \
                                          self._ui.enableMarkersBox.isChecked()
        self._settings.appearance.use_mpl_toolbar = \
                                       self._ui.enableMplToolbarBox.isChecked()
        self._settings.appearance.cursor.style = \
                                  self._ui.cursorStyleSelectorBox.currentText()
        self._settings.appearance.cursor.width = float(
            self._ui.cursorWidthSelectorBox.currentText()
        )
        self._settings.appearance.cursor.color = \
                                  self._ui.cursorColorSelectorBox.currentText()
        self._settings.simple_csv.delimiter = \
                                             self._ui.simpleCsvAliasEdit.text()
        self._settings.simple_csv.timestamp = \
                                         self._ui.simpleCsvTimestampEdit.text()
        self._settings.simple_csv.scales = {}
        for ind, val in enumerate(self._scale_name_edits):
            self._settings.simple_csv.scales[val.text()] = locale.atof(
                self._scale_value_edits[ind].text()
            )
        self._settings.j1939_dump.asc_base = \
                                         self._ui.ascBaseSelector.currentText()
        self._settings.j1939_dump.rel_timestamp = \
                                           self._ui.relTimestampBox.isChecked()
        self._settings.j1939_dump.databases = [
            self._ui.databaseList.item(d).text() for d in range(
                self._ui.databaseList.count()
            )
        ]

    def get_settings(self) -> SettingsData:
        """
        Returns current saved settings data
        """
        return self._settings
