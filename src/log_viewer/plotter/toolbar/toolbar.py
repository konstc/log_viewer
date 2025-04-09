""" Toolbar module """

from dataclasses import dataclass
from enum import Enum
import os

import numpy as np
import pandas as pd

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QToolBar
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

import matplotlib as mpl
from matplotlib.cbook import Stack
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from .cursor import PlotterToolbarCursor
from .zoomer import PlotterToolbarRectZoomer

class _PlotterToolbarMode(str, Enum):
    NONE = ""
    ZOOM_RECT = "zoom_rect"
    CURSOR = "cursor"

    def __str__(self):
        return self.value

@dataclass
class PlotterTooldata:
    """ General tool data """
    cursor_pos: float = np.nan
    view_xlim_left: float = 0.0
    view_xlim_right: float = 0.0
    view_ylim_top: float = 0.0
    view_ylim_bot: float = 0.0

# pylint: disable-next=too-many-instance-attributes
class PlotterToolbar(QToolBar):
    """
    Toolbar for the plot window
    """

    tooldata_updated = pyqtSignal()

    toolitems = (
        ("Home", "Reset original view", "_home"),
        ("Back", "Back to previous view", "_back"),
        ("Forward", "Forwared to next view", "_forward"),
        (None, None, None),
        ("Zoom Rect", "Zoom to rectangle\nx/y fixes axis", "_zoom_rect"),
        (None, None, None),
        ("Cursor", "Place cursor to the current view", "_cursor"),
        ("ZoomX+", "Zoom+ x2 on X axis around placed cursor",
         "_cursor_zoom_plus"),
        ("ZoomX-", "Zoom- x2 on X axis around placed cursor",
         "_cursor_zoom_minus"),
        ("ZoomY Auto", "Autozoom on Y axis around placed cursor",
         "_cursor_zoom_auto"),
        ("Move Forward", "Move cursor forward for one plot point",
         "_cursor_move_forward"),
        ("Move Back", "Move cursor back for one plot point",
         "_cursor_move_back"),
        (None, None, None),
        ("Save", "Save the plot into file", "_save_figure")
    )

    # pylint: disable-next=too-many-arguments
    def __init__(self,
                 canvas: FigureCanvasQTAgg,
                 plot_points: pd.DataFrame,
                 cursor_style: str = "dashed",
                 cursor_width: float = 0.5,
                 cursor_color: str = "red",
                 parent = None):

        super().__init__(parent)

        self.setAllowedAreas(
            Qt.ToolBarArea.TopToolBarArea | Qt.ToolBarArea.BottomToolBarArea
        )

        self._actions = {}
        for text, tooltip, callback in self.toolitems:
            if text is None:
                self.addSeparator()
            else:
                act = self.addAction(text, getattr(self, callback))
                self._actions[callback] = act
                if callback in ["_zoom_rect", "_cursor"]:
                    act.setCheckable(True)
                if tooltip:
                    act.setToolTip(tooltip)

        self._parent = parent
        self._canvas = canvas
        self._axes = canvas.figure.get_axes()
        self._nav_stack = Stack()
        self._zoom_rect_tool = None
        self._cursor_tool = None
        self._plot_points = plot_points
        self._subplot_dialog = None
        self._cursor_style = cursor_style
        self._cursor_width = cursor_width
        self._cursor_color = cursor_color
        self._tooldata = PlotterTooldata()

        self._mode = _PlotterToolbarMode.NONE

        self._update_history_buttons()
        self._update_cursor_buttons(False)
        self._update_view_lims()

    @property
    def tooldata(self) -> PlotterTooldata:
        """
        Returns current toolbar data
        """
        return self._tooldata

    # pylint: disable-next=unused-argument
    def _home(self, *args):
        self._switch_mode(_PlotterToolbarMode.NONE)
        self._nav_stack.home()
        self._update_history_buttons()
        self._update_checkable_buttons()
        self._update_view()
        self._update_view_lims()

    # pylint: disable-next=unused-argument
    def _back(self, *args):
        self._switch_mode(_PlotterToolbarMode.NONE)
        self._nav_stack.back()
        self._update_history_buttons()
        self._update_checkable_buttons()
        self._update_view()
        self._update_view_lims()

    # pylint: disable-next=unused-argument
    def _forward(self, *args):
        self._switch_mode(_PlotterToolbarMode.NONE)
        self._nav_stack.forward()
        self._update_history_buttons()
        self._update_checkable_buttons()
        self._update_view()
        self._update_view_lims()

    def _switch_mode(self, new_mode: _PlotterToolbarMode):
        if new_mode == _PlotterToolbarMode.NONE:
            if self._zoom_rect_tool:
                self._zoom_rect_tool.disconnect()
                self._zoom_rect_tool.nav_updated.disconnect()
                self._zoom_rect_tool = None
            if self._cursor_tool:
                self._cursor_tool.disconnect()
                self._cursor_tool.nav_updated.disconnect()
                self._cursor_tool.cursor_placed.disconnect()
                self._cursor_tool.cursor_moved.disconnect()
                self._cursor_tool = None
        elif new_mode == _PlotterToolbarMode.ZOOM_RECT:
            if self._cursor_tool:
                self._cursor_tool.disconnect()
                self._cursor_tool.nav_updated.disconnect()
                self._cursor_tool.cursor_placed.disconnect()
                self._cursor_tool.cursor_moved.disconnect()
                self._cursor_tool = None
            self._zoom_rect_tool = PlotterToolbarRectZoomer(self._canvas,
                                                            self._nav_stack)
            self._zoom_rect_tool.nav_updated.connect(
                self._update_history_buttons
            )
            self._zoom_rect_tool.nav_updated.connect(
                self._update_view_lims
            )
        elif new_mode == _PlotterToolbarMode.CURSOR:
            if self._zoom_rect_tool:
                self._zoom_rect_tool.disconnect()
                self._zoom_rect_tool.nav_updated.disconnect()
                self._zoom_rect_tool = None
            self._cursor_tool = PlotterToolbarCursor(self._canvas,
                                                     self._nav_stack,
                                                     self._plot_points,
                                                     linestyle=self._cursor_style,
                                                     lw=self._cursor_width,
                                                     color=self._cursor_color)
            self._cursor_tool.cursor_placed.connect(
                self._update_cursor_buttons
            )
            self._cursor_tool.cursor_moved.connect(
                self._update_cursor_pos
            )
            self._cursor_tool.nav_updated.connect(
                self._update_history_buttons
            )
            self._cursor_tool.nav_updated.connect(
                self._update_view_lims
            )
        self._mode = new_mode

    # pylint: disable-next=unused-argument
    def _zoom_rect(self, *args):
        if self._mode != _PlotterToolbarMode.ZOOM_RECT:
            self._switch_mode(_PlotterToolbarMode.ZOOM_RECT)
        else:
            self._switch_mode(_PlotterToolbarMode.NONE)
        self._update_checkable_buttons()

    # pylint: disable-next=unused-argument
    def _cursor(self, *args):
        if self._mode != _PlotterToolbarMode.CURSOR:
            self._switch_mode(_PlotterToolbarMode.CURSOR)
        else:
            self._switch_mode(_PlotterToolbarMode.NONE)
        self._update_checkable_buttons()

    # pylint: disable-next=unused-argument
    def _cursor_zoom_plus(self, *args):
        if self._cursor_tool:
            self._cursor_tool.zoom_plus()

    # pylint: disable-next=unused-argument
    def _cursor_zoom_minus(self, *args):
        if self._cursor_tool:
            self._cursor_tool.zoom_minus()

    # pylint: disable-next=unused-argument
    def _cursor_zoom_auto(self, *args):
        if self._cursor_tool:
            self._cursor_tool.zoom_auto()

    # pylint: disable-next=unused-argument
    def _cursor_move_forward(self, *args):
        if self._cursor_tool:
            self._cursor_tool.move_forward()

    # pylint: disable-next=unused-argument
    def _cursor_move_back(self, *args):
        if self._cursor_tool:
            self._cursor_tool.move_back()

    # pylint: disable-next=unused-argument
    def _save_figure(self, *args):
        filetypes = self._canvas.get_supported_filetypes_grouped()
        sorted_filetypes = sorted(filetypes.items())
        default_filetype = self._canvas.get_default_filetype()

        startpath = os.path.expanduser(mpl.rcParams['savefig.directory'])
        start = os.path.join(startpath, self._canvas.get_default_filename())
        filters = []
        selected_filter = None
        for name, exts in sorted_filetypes:
            exts_list = " ".join([f"*.{ext}" for ext in exts])
            filt = f"{name} ({exts_list})"
            if default_filetype in exts:
                selected_filter = filt
            filters.append(filt)
        filters = ';;'.join(filters)

        fname, filt = QFileDialog.getSaveFileName(
            self._canvas.parent(), "Choose a filename to save to", start,
            filters, selected_filter)
        if fname:
            # Save dir for next time, unless empty str (i.e., use cwd).
            if startpath != "":
                mpl.rcParams['savefig.directory'] = os.path.dirname(fname)
            try:
                self._canvas.figure.savefig(fname)
            # pylint: disable-next=broad-exception-caught
            except Exception as exc:
                QMessageBox.critical(
                    self, "Error saving file", str(exc),
                    QMessageBox.StandardButton.Ok,
                    QMessageBox.StandardButton.NoButton)

    def _update_view(self) -> None:
        """
        """
        nav_info = self._nav_stack()
        if nav_info:
            items = list(nav_info.items())
            for ax, (view, (pos_orig, pos_active)) in items:
                # pylint: disable=protected-access
                ax._set_view(view)
                ax._set_position(pos_orig, "original")
                ax._set_position(pos_active, "active")
                # pylint: enable=protected-access
            self._canvas.draw_idle()

    def _update_checkable_buttons(self):
        """
        """
        if "_zoom_rect" in self._actions:
            self._actions["_zoom_rect"].setChecked(
                self._mode == _PlotterToolbarMode.ZOOM_RECT
            )
        if "_cursor" in self._actions:
            self._actions["_cursor"].setChecked(
                self._mode == _PlotterToolbarMode.CURSOR
            )

    @pyqtSlot()
    def _update_history_buttons(self):
        """
        """
        # pylint: disable=protected-access
        can_back = self._nav_stack._pos > 0
        can_forw = self._nav_stack._pos < len(self._nav_stack._elements) - 1
        # pylint: enable=protected-access
        if "_back" in self._actions:
            self._actions["_back"].setEnabled(can_back)
        if "_forward" in self._actions:
            self._actions["_forward"].setEnabled(can_forw)

    @pyqtSlot(bool)
    def _update_cursor_buttons(self, cursor_placed: bool):
        """
        """
        if "_cursor_zoom_plus" in self._actions:
            self._actions["_cursor_zoom_plus"].setEnabled(cursor_placed)
        if "_cursor_zoom_minus" in self._actions:
            self._actions["_cursor_zoom_minus"].setEnabled(cursor_placed)
        if "_cursor_zoom_auto" in self._actions:
            self._actions["_cursor_zoom_auto"].setEnabled(cursor_placed)
        if "_cursor_move_forward" in self._actions:
            self._actions["_cursor_move_forward"].setEnabled(cursor_placed)
        if "_cursor_move_back" in self._actions:
            self._actions["_cursor_move_back"].setEnabled(cursor_placed)

    @pyqtSlot(float)
    def _update_cursor_pos(self, pos: float) -> None:
        """
        """
        self._tooldata.cursor_pos = pos
        self.tooldata_updated.emit()

    @pyqtSlot()
    def _update_view_lims(self) -> None:
        """
        """
        self._tooldata.view_xlim_left, self._tooldata.view_xlim_right = \
            self._axes[-1].get_xlim()
        self._tooldata.view_ylim_bot, self._tooldata.view_ylim_top = \
            self._axes[-1].get_ylim()
        self.tooldata_updated.emit()
