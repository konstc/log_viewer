""" Log viewer's main window module """

import json
import logging

from jsonschema import validate
from PyQt6.QtCore import pyqtSlot, Qt, QRectF, QSize
from PyQt6.QtGui import QAction, QColor, QIcon, QPixmap, QTextDocument
from PyQt6.QtWidgets import QDialog, QFileDialog, QLabel, QListWidget, \
                            QListWidgetItem, QMainWindow, QMessageBox, \
                            QStyledItemDelegate, QStyle, QStyleOptionViewItem

from about_dialog import AboutDialog
from generated_ui import Ui_MainWindow
from import_dialog import ImportDialog
from plotter import SimpleCsvPlotter, J1939DumpPlotter, PlotterInitError, \
                    PlotterPlotError
from settings_schema import APP_SETTINGS_SCHEMA
from settings_dialog import CursorSettings, AppearanceSettings, SettingsData, \
                            SettingsDialog, SimpleCsvSettings, J1939DumpSettings
from toolbar import PlotMode
from utils import get_icons_path, get_settings_path

class PlotItemList:
    """
    A list of items to plot
    """

    item_template = "<table width=\"100%\">" \
                        "<tr>" \
                            "<td align=\"left\">{item}</td>" \
                            "<td align=\"right\"><i>{plot}</i></td>" \
                        "</tr>" \
                    "</table>"

    def __init__(self, items: list[str], list_widget: QListWidget) -> None:
        """
        Constructs a list of items to plot using 'list' names and external
        QListWidget 'list_widget'
        """
        self._items = {}
        self._plots = []
        self._lw = list_widget
        self.add_items(items)

    def __get_selected_items(self) -> list[str]:
        """
        Returns a list of the selected items names
        """
        return [item_name for item_name, item in self._items.items()
                if item.isSelected()]

    def __mark_item(self, item: str, plot: int) -> None:
        """
        Assigns item with name 'item' to 'plot' plot
        """
        self._items[item].setText(
            self.item_template.format(item=item,
                                      plot="[PLOT" + str(plot) + "]")
        )
        flags = self._items[item].flags()
        self._items[item].setFlags(flags & ~(Qt.ItemFlag.ItemIsSelectable))
        self._items[item].setBackground(Qt.GlobalColor.lightGray)
        self._items[item].setSelected(False)

    def __unmark_item(self, item: str) -> None:
        """
        Clears the plot assignment for item with name 'item'
        """
        self._items[item].setText(
            self.item_template.format(item=item, plot="")
        )
        flags = self._items[item].flags()
        self._items[item].setFlags(flags | Qt.ItemFlag.ItemIsSelectable)
        self._items[item].setBackground(Qt.GlobalColor.transparent)

    def selected_plots(self, mode: PlotMode) -> list[list[str]]:
        """
        Returns the list of selected item names grouped by separate plots
        """
        if mode == PlotMode.PLOTMODE_MERGED:
            sel_items = self.__get_selected_items()
            if sel_items:
                return [[plot for plot in sel_items]]
        elif mode == PlotMode.PLOTMODE_SEPARATED:
            sel_items = self.__get_selected_items()
            if sel_items:
                return [[plot] for plot in sel_items]
        else:
            if self._plots:
                return self._plots
        return [[]]

    def add_items(self, items: list[str]) -> None:
        """
        Adds the list 'list' with item names
        """
        for item in items:
            self._items[item] = QListWidgetItem(
                self.item_template.format(item=item, plot="")
            )
            self._lw.addItem(self._items[item])
        self._lw.sortItems(order=Qt.SortOrder.AscendingOrder)

    def clear_plot_assignment(self) -> None:
        """
        Clears the plot assignment for all items
        """
        for item_name in self._items:
            self.__unmark_item(item_name)
        self._plots.clear()

    def assign_selected(self) -> None:
        """
        Assigns currently selected items to the next vacant plot
        """
        items = self.__get_selected_items()
        if items:
            for item in items:
                self.__mark_item(item, len(self._plots))
            self._plots.append(items)

    def select_all(self) -> None:
        """
        Sets all items selected
        """
        for _, item in self._items.items():
            item.setSelected(True)

    def select_clear(self) -> None:
        """
        Resets selection for all items
        """
        for _, item in self._items.items():
            item.setSelected(False)

    def clear(self) -> None:
        """
        Deletes all items from the list
        """
        self._lw.clear()
        self._items.clear()
        self._plots.clear()

class PlotItemDelegate(QStyledItemDelegate):
    """
    A HTML-based list widget item
    """

    def paint(self, painter, option, index):
        """
        Overrided paint() from QStyledItemDelegate
        """
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        painter.save()

        doc = QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(options.rect.width())

        options.text = ""
        options.widget.style().drawControl(
            QStyle.ControlElement.CE_ItemViewItem, options, painter
        )

        painter.translate(options.rect.left(), options.rect.top())
        clip = QRectF(0, 0, options.rect.width(), options.rect.height())
        doc.drawContents(painter, clip)

        painter.restore()

    def sizeHint(self, option, index): # pylint: disable=invalid-name
        """
        Overrided sizeHint() from QStyledItemDelegate
        """
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        doc = QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(doc.idealWidth())

        return QSize(doc.idealWidth(), doc.size().height())

class MainWindow(QMainWindow): # pylint: disable=too-many-instance-attributes
    """
    LogViewer's main window
    """

    def __init__(self) -> None:
        """
        Constructs a main window of the LogViewer
        """
        super().__init__()

        self._ready = False
        self._file = ""
        self._plot_windows = {}
        self._plot_windows_actions = {}
        self._plotter = None

        with open(str(get_settings_path()), "r",
                  encoding="utf-8") as settings_file:
            self._settings = json.load(settings_file)
        validate(self._settings, APP_SETTINGS_SCHEMA)

        # Setup the UI from Qt Designer
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)
        delegate = PlotItemDelegate(self._ui.listWidget)
        self._ui.listWidget.setItemDelegate(delegate)
        self._plot_items = PlotItemList([], self._ui.listWidget)

        # Setup action icons
        self._ui.actionPlot.setIcon(self.__icon("plot.png"))
        self._ui.actionSpectrum.setIcon(self.__icon("spectrum.png"))
        self._ui.actionAssign.setIcon(self.__icon("plus.png"))
        self._ui.actionClear.setIcon(self.__icon("delete.png"))
        self._ui.actionSelectAll.setIcon(self.__icon("select_all.png"))
        self._ui.actionSelectClear.setIcon(self.__icon("select_clear.png"))

        # Status bar setup
        self._status_mode = QLabel()
        self._ui.statusbar.addPermanentWidget(self._status_mode)
        self.__update()

        # Tool bar setup
        self._ui.toolBar.addActions([self._ui.actionPlot,
                                    self._ui.actionSpectrum,
                                    self._ui.actionSelectAll,
                                    self._ui.actionSelectClear,
                                    self._ui.actionAssign,
                                    self._ui.actionClear])

        # Slots configuration
        self._ui.actionAssign.triggered.connect(self.assign_plot)
        self._ui.actionClear.triggered.connect(self.clear_assignment)
        self._ui.actionClose.triggered.connect(self.file_close)
        self._ui.actionCloseAll.triggered.connect(self.close_all_plot_window)
        self._ui.actionPlot.triggered.connect(self.plot)
        self._ui.actionOpen.triggered.connect(self.file_open)
        self._ui.actionRefresh.triggered.connect(self.file_refresh)
        self._ui.actionAbout.triggered.connect(self.about_dialog_open)
        self._ui.actionSettings.triggered.connect(self.settings_dialog_open)
        self._ui.actionSelectAll.triggered.connect(self.select_all)
        self._ui.actionSelectClear.triggered.connect(self.select_clear)
        self._ui.toolBar.plot_mode_updated.connect(self.plot_mode_updated)

        logging.info("Successfully started")

    def __icon(self, name: str) -> QIcon:
        """
        Gets QIcon for a given 'name' filename
        """
        filename = get_icons_path() / name

        pmap = QPixmap(str(filename))
        pmap.setDevicePixelRatio(self.devicePixelRatioF() or 1)
        if self.palette().color(self.backgroundRole()).value() < 128:
            icon_color = self.palette().color(self.foregroundRole())
            mask = pmap.createMaskFromColor(
                QColor("black"),
                Qt.MaskMode.MaskOutColor
            )
            pmap.fill(icon_color)
            pmap.setMask(mask)
        return QIcon(pmap)

    def __update_actions(self) -> None:
        """
        Updates all QActions according to current application state
        """
        self._ui.actionOpen.setEnabled(not self._ready)
        self._ui.actionRefresh.setEnabled(self._ready)
        self._ui.actionClose.setEnabled(self._ready)
        self._ui.actionPlot.setEnabled(self._ready)
        self._ui.actionSpectrum.setEnabled(self._ready)
        self._ui.actionSelectAll.setEnabled(self._ready)
        self._ui.actionSelectClear.setEnabled(self._ready)

        if (self._ready and self._ui.toolBar.plot_mode ==
                                                     PlotMode.PLOTMODE_MANUAL):
            self._ui.actionAssign.setEnabled(True)
            self._ui.actionClear.setEnabled(True)
        else:
            self._ui.actionAssign.setEnabled(False)
            self._ui.actionClear.setEnabled(False)

    def __update(self) -> None:
        """
        Updates application widgets according to current application mode
        """
        # Update statusbar
        if self._settings["mode"] == "simple_csv":
            self._status_mode.setText("Mode: Simple CSV reader")
        elif self._settings["mode"] == "j1939_dump":
            self._status_mode.setText("Mode: J1939 dump decoder")
        else:
            self._status_mode.setText("Mode: unknown")

        # Update plot items
        self._plot_items.clear()
        if self._ready:
            self._plot_items.add_items(self._plotter.plot_vars)

        # Update toolbar
        self._ui.toolBar.plot_mode_box.setEnabled(self._ready)
        self._ui.toolBar.plot_mode_changed(
            self._ui.toolBar.plot_mode_box.currentIndex()
        )

        self.__update_actions()

    def __import(self) -> None:
        """
        Performs import from opened self._file according to current application
        mode
        """
        if self._file:
            if self._settings["mode"] == "simple_csv":
                try:
                    self._plotter = SimpleCsvPlotter(
                        self._file,
                        self._settings["simple_csv"]["delimiter"],
                        self._settings["simple_csv"]["timestamp"],
                        self._settings["simple_csv"]["scales"]
                    )
                    self._plotter.open()
                    self._ready = True
                    logging.info("Successfully opened: %s", self._file)
                except PlotterInitError as err:
                    logging.error(err, exc_info=True)
                    QMessageBox.critical(None, "Critical error", str(err))
            elif self._settings["mode"] == "j1939_dump":
                try:
                    self._plotter = J1939DumpPlotter(
                            self._file,
                            self._settings["j1939_dump"]["db"],
                            self._settings["j1939_dump"]["asc_base"],
                            self._settings["j1939_dump"]["asc_rel_timestamp"]
                        )
                    dialog = ImportDialog(self._plotter)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        self._ready = True
                        logging.info("Successfully opened: %s", self._file)
                    else:
                        logging.warning("Failed to open: %s", self._file)
                except PlotterInitError as err:
                    logging.error(err, exc_info=True)
                    QMessageBox.critical(None, "Critical error", str(err))

    def __save_settings(self) -> None:
        """
        Performs saving current application settings to a json
        """
        with open(str(get_settings_path()), "w",
                  encoding="utf-8") as settings_file:
            json.dump(self._settings, settings_file, indent=4)
            logging.info("Changed application configuration")

    @pyqtSlot()
    def file_open(self) -> None:
        """
        Performs select and open file according to current application mode
        """
        if self._settings["mode"] == "simple_csv":
            self._file, _ = QFileDialog.getOpenFileName(
                None,
                "Open log-file",
                "./",
                "CSV (*.csv)"
            )
        elif self._settings["mode"] == "j1939_dump":
            if self._settings["j1939_dump"]["db"]:
                self._file, _ = QFileDialog.getOpenFileName(
                    None,
                    "Open log-file",
                    "./",
                    "J1939-CAN dump file (*.asc *.blf *.csv *.log)"
                )
            else:
                self._file = ""
                QMessageBox.warning(
                    self,
                    "Warning",
                    "No database configured. File opening is cancelled. " 
                    "Please add .dbc files in "
                    "Application -> Settings -> "
                    "J1939 dump decoder -> Database setup.",
                    QMessageBox.StandardButton.Ok
                )
        else:
            self._file = ""
        self.__import()
        self.__update()

    @pyqtSlot()
    def file_refresh(self) -> None:
        """
        Repeats import from previously opened self._file
        """
        self.__import()
        self.__update()

    @pyqtSlot()
    def file_close(self) -> None:
        """
        Closes previously opened self._file
        """
        logging.info("Closed: %s", self._file)
        self._file = ""
        self._plotter = None
        self._ready = False
        self.__update()

    @pyqtSlot()
    def about_dialog_open(self) -> None:
        """
        Opens "About" window
        """
        dialog = AboutDialog()
        dialog.exec()

    @pyqtSlot()
    def settings_dialog_open(self) -> None:
        """
        Opens application settings dialog
        """
        dialog = SettingsDialog(
            SettingsData(
                self._settings["mode"],
                AppearanceSettings(
                    CursorSettings(
                        self._settings["plot"]["cursor"]["style"],
                        self._settings["plot"]["cursor"]["width"],
                        self._settings["plot"]["cursor"]["color"]
                    ),
                    self._settings["plot"]["style"],
                    self._settings["plot"]["linestyle"],
                    self._settings["plot"]["linewidth"],
                    self._settings["plot"]["marker"],
                    self._settings["plot"]["use_mpl_toolbar"]
                ),
                SimpleCsvSettings(
                    self._settings["simple_csv"]["delimiter"],
                    self._settings["simple_csv"]["timestamp"],
                    self._settings["simple_csv"]["scales"]
                ),
                J1939DumpSettings(
                    self._settings["j1939_dump"]["asc_base"],
                    self._settings["j1939_dump"]["asc_rel_timestamp"],
                    self._settings["j1939_dump"]["db"]
                )
            )
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            ret = dialog.get_settings()
            mode_changed = self._settings["mode"] != ret.mode
            self._settings["mode"] = ret.mode
            self._settings["plot"]["style"] = ret.appearance.plotstyle
            self._settings["plot"]["linestyle"] = ret.appearance.linestyle
            self._settings["plot"]["linewidth"] = ret.appearance.linewidth
            self._settings["plot"]["marker"] = ret.appearance.marker
            self._settings["plot"]["use_mpl_toolbar"] = \
                                                 ret.appearance.use_mpl_toolbar
            self._settings["plot"]["cursor"]["style"] = \
                                                    ret.appearance.cursor.style
            self._settings["plot"]["cursor"]["width"] = \
                                                    ret.appearance.cursor.width
            self._settings["plot"]["cursor"]["color"] = \
                                                    ret.appearance.cursor.color
            self._settings["simple_csv"]["delimiter"] = \
                                                       ret.simple_csv.delimiter
            self._settings["simple_csv"]["timestamp"] = \
                                                       ret.simple_csv.timestamp
            self._settings["simple_csv"]["scales"] = ret.simple_csv.scales
            self._settings["j1939_dump"]["asc_base"] = ret.j1939_dump.asc_base
            self._settings["j1939_dump"]["asc_rel_timestamp"] = \
                                                   ret.j1939_dump.rel_timestamp
            self._settings["j1939_dump"]["db"] = ret.j1939_dump.databases
            self.__save_settings()
            if mode_changed and self._ready:
                self.file_close()
            else:
                self.__update()

    @pyqtSlot()
    def plot(self) -> None:
        """
        Plots selected items
        """
        vars_set = self._plot_items.selected_plots(self._ui.toolBar.plot_mode)
        spectrum = self._ui.actionSpectrum.isChecked()
        logging.info("Trying to plot: %s", str(vars_set))
        marker = "x" if self._settings["plot"]["marker"] else "none"

        if vars_set:
            try:
                pwin = self._plotter.plot(
                    vars_set,
                    spectrum,
                    self._settings["plot"]["style"],
                    self._settings["plot"]["linestyle"],
                    self._settings["plot"]["linewidth"],
                    marker,
                    self._settings["plot"]["use_mpl_toolbar"],
                    self._settings["plot"]["cursor"]["style"],
                    self._settings["plot"]["cursor"]["width"],
                    self._settings["plot"]["cursor"]["color"]
                )
                title = pwin.windowTitle()

                # Close the same plot window if it already exists
                if title in self._plot_windows:
                    self._plot_windows[title].close()
                self._plot_windows[title] = pwin
                self._plot_windows[title].closed.connect(
                    self.del_plot_window
                )

                # Add action to Window menu
                if not title in self._plot_windows_actions:
                    self._plot_windows_actions[title] = QAction(self)
                    self._plot_windows_actions[title].setText(title)
                    self._plot_windows_actions[title].triggered.connect(
                        lambda: self.activate_plot_window(title)
                    )
                    self._ui.menuWindow.addAction(
                        self._plot_windows_actions[title]
                    )
                self._ui.actionCloseAll.setEnabled(True)
            except PlotterPlotError:
                pass

    @pyqtSlot(str)
    def del_plot_window(self, title: str) -> None:
        """
        Actions after closing plot window with "title" title
        """
        if title in self._plot_windows:
            self._ui.menuWindow.removeAction(self._plot_windows_actions[title])
            del self._plot_windows_actions[title]
            del self._plot_windows[title]
        if len(self._plot_windows) == 0:
            self._ui.actionCloseAll.setEnabled(False)

    @pyqtSlot(str)
    def activate_plot_window(self, title: str) -> None:
        """
        Sets focus to plot window with "title" title
        """
        if title in self._plot_windows:
            self._plot_windows[title].activateWindow()

    @pyqtSlot()
    def close_all_plot_window(self) -> None:
        """
        Sends close() to all opened plot windows
        """
        for pwin in list(self._plot_windows.values()):
            pwin.close()

    @pyqtSlot()
    def assign_plot(self) -> None:
        """
        Assigns selected items to a single plot
        """
        self._plot_items.assign_selected()

    @pyqtSlot()
    def clear_assignment(self) -> None:
        """
        Clears plot assignment for all items
        """
        self._plot_items.clear_plot_assignment()

    @pyqtSlot()
    def plot_mode_updated(self) -> None:
        """
        Handles current plot mode update event
        """
        if self._ui.toolBar.plot_mode != PlotMode.PLOTMODE_MANUAL:
            self._plot_items.clear_plot_assignment()
        self.__update_actions()

    @pyqtSlot()
    def select_all(self) -> None:
        """
        Selects all items in the current plot list
        """
        self._plot_items.select_all()

    @pyqtSlot()
    def select_clear(self) -> None:
        """
        Clear selection in the current plot list
        """
        self._plot_items.select_clear()
