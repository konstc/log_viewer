""" Toolbar cursor tool module """

import numpy as np
import pandas as pd

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.cbook import Stack

from PyQt6.QtCore import pyqtSignal

from .base_tool import PlotterBaseTool

# pylint: disable-next=too-many-instance-attributes
class PlotterToolbarCursor(PlotterBaseTool):
    """
    Toolbar cursor tool
    """

    cursor_placed = pyqtSignal(bool)
    cursor_moved = pyqtSignal(float)

    # pylint: disable-next=too-many-arguments,too-many-positional-arguments
    def __init__(self,
                 canvas: FigureCanvasQTAgg,
                 nav_stack: Stack,
                 plot_points: pd.DataFrame,
                 linestyle: str = "dashed",
                 lw: float = 0.8,
                 color: str = "r"):

        super().__init__(canvas, nav_stack)

        self._plot_points = plot_points
        self._visible = False
        self._placed = False
        self._resized = False

        self._canvas_infos = {
            ax.figure.canvas: {"cids": [], "background": None} \
                for ax in self._axes
        }

        xmin, xmax = self._axes[-1].get_xlim()
        xmid = 0.5 * (xmin + xmax)
        self._cursor_pos = xmid
        self._cursor_idx = 0
        self._vlines = [ax.axvline(xmid,
                                   visible=self._visible,
                                   linestyle=linestyle,
                                   lw=lw,
                                   color=color,
                                   animated=True) for ax in self._axes]

        self.connect()
        self.cursor_placed.emit(self._placed)
        self._canvas.draw_idle()

    @property
    def pos(self) -> float:
        """
        Returns current cursor position
        """
        if self._placed:
            return self._cursor_pos
        return 0.0

    @property
    def placed(self) -> bool:
        """
        Returns placed state of the cursor (True of the cursor is placed)
        """
        return self._placed

    def connect(self):
        for canvas, info in self._canvas_infos.items():
            info["cids"] = [
                canvas.mpl_connect("button_press_event",
                                   self._button_press_handler),
                canvas.mpl_connect("button_release_event",
                                   self._button_release_handler),
                canvas.mpl_connect("motion_notify_event", self._move_handler),
                canvas.mpl_connect("draw_event", self._draw_handler),
                canvas.mpl_connect("resize_event", self._resize_handler),
                canvas.mpl_connect("key_press_event", self._key_handler)
            ]

    def disconnect(self):
        self._clear()
        for canvas, info in self._canvas_infos.items():
            for cid in info["cids"]:
                canvas.mpl_disconnect(cid)
            info["cids"].clear()

    def zoom_plus(self):
        """
        Zooms in the current view along the current cursor position
        """
        if self._placed:
            if self._nav_stack() is None:
                self.push_view()
            xmin, xmax = self._axes[-1].get_xlim()
            lenx = (xmax - xmin) / 4.0
            left = self._cursor_pos - lenx
            right = self._cursor_pos + lenx
            for ax in self._axes:
                ax.set_xlim((left, right))
            self._resized = True
            self._canvas.draw_idle()
            self.push_view()

    def zoom_minus(self):
        """
        Zooms out the current view along the current cursor position
        """
        if self._placed:
            if self._nav_stack() is None:
                self.push_view()
            xmin, xmax = self._axes[-1].get_xlim()
            lenx = xmax - xmin
            left = self._cursor_pos - lenx
            right = self._cursor_pos + lenx
            for ax in self._axes:
                ax.set_xlim((left, right))
            self._resized = True
            self._canvas.draw_idle()
            self.push_view()

    def zoom_auto(self):
        """
        Autozooms the current view along the Y axis
        """
        if self._placed:
            if self._nav_stack() is None:
                self.push_view()
            for ax in self._axes:
                autozoomy_ax(ax)
            self._resized = True
            self._canvas.draw_idle()
            self.push_view()

    def move_forward(self):
        """
        Moves the cursor forward
        """
        if self._placed:
            if self._cursor_idx < len(self._plot_points) - 1:
                self._cursor_idx += 1
                xdata = self._plot_points.iloc[self._cursor_idx, 0]
                for line in self._vlines:
                    line.set_xdata((xdata, xdata))
                self._cursor_pos = xdata
                self.cursor_moved.emit(xdata)
                l, r = self._axes[-1].get_xlim()
                if xdata > r:
                    if self._nav_stack() is None:
                        self.push_view()
                    rem = xdata - r
                    l += rem + rem * 1.1
                    r += rem + rem * 1.1
                    for ax in self._axes:
                        ax.set_xlim(left = l, right = r)
                    self._resized = True
                    self._canvas.draw_idle()
                    self.push_view()
                else:
                    self.__update()

    def move_back(self):
        """
        Moves the cursor backward
        """
        if self._placed:
            if self._cursor_idx > 0:
                self._cursor_idx -= 1
                xdata = self._plot_points.iloc[self._cursor_idx, 0]
                for line in self._vlines:
                    line.set_xdata((xdata, xdata))
                self._cursor_pos = xdata
                self.cursor_moved.emit(xdata)
                l, r = self._axes[-1].get_xlim()
                if xdata < l:
                    if self._nav_stack() is None:
                        self.push_view()
                    rem = l - xdata
                    l -= rem + rem * 1.1
                    r -= rem + rem * 1.1
                    for ax in self._axes:
                        ax.set_xlim(left = l, right = r)
                    self._resized = True
                    self._canvas.draw_idle()
                    self.push_view()
                else:
                    self.__update()

    def _move(self, xdata):
        """
        Moves the cursor to the new place
        """
        # Correct xdata to the nearest plot_points
        idx_col = self._plot_points.columns[0]
        idx = (self._plot_points[idx_col] - xdata).abs().idxmin()
        nearest = self._plot_points.iloc[idx, 0]
        for line in self._vlines:
            line.set_xdata((nearest, nearest))
        self._cursor_pos = nearest
        self._cursor_idx = idx
        self.__update()

    def _clear(self):
        """
        Clears the current cursor position
        """
        self._visible = False
        self._placed = False
        self.cursor_placed.emit(self._placed)
        self.cursor_moved.emit(np.nan)
        for line in self._vlines:
            line.set_visible(self._visible)
        self.__update()

    def _button_press_handler(self, event):
        if (self.ignore(event) or
            event.inaxes not in self._axes or
            not event.canvas.widgetlock.available(self)):
            return
        self._visible = True
        self._placed = False
        self.cursor_placed.emit(self._placed)
        self.cursor_moved.emit(np.nan)
        self._move(event.xdata)

    def _button_release_handler(self, event):
        if self.ignore(event):
            return
        self._placed = True
        self.cursor_placed.emit(self._placed)
        self.cursor_moved.emit(self._cursor_pos)

    def _move_handler(self, event):
        if (self.ignore(event) or
            event.inaxes not in self._axes or
            not event.canvas.widgetlock.available(self)):
            return
        if not self._placed:
            self._move(event.xdata)

    def _draw_handler(self, event):
        if self.ignore(event):
            return
        for canvas, info in self._canvas_infos.items():
            if canvas is not canvas.figure.canvas:
                continue
            info["background"] = canvas.copy_from_bbox(canvas.figure.bbox)
        if self._resized:
            if self._placed:
                self.__draw_cursor()
            self._resized = False

    def _resize_handler(self, event):
        """
        Handler for 'resize_event' event
        """
        if self.ignore(event):
            return
        self._resized = True

    def _key_handler(self, event):
        """
        Handler for 'key_press_event' event
        """
        if self.ignore(event):
            return
        if event.key == "right":
            self.move_forward()
        elif event.key == "left":
            self.move_back()

    def __update(self):
        """
        Updates the current cursor view
        """
        for canvas, info in self._canvas_infos.items():
            if info["background"]:
                canvas.restore_region(info["background"])
        self.__draw_cursor()
        for canvas in self._canvas_infos:
            canvas.blit()

    def __draw_cursor(self):
        """
        Draws the cursor tool
        """
        for ax, line in zip(self._axes, self._vlines):
            line.set_visible(self._visible)
            ax.draw_artist(line)

def autozoomy_ax(ax, margin: float = 0.05):
    """
    https://stackoverflow.com/questions/29461608/fixing-x-axis-scale-and-autoscale-y-axis
    """
    lines = ax.get_lines()
    bot, top = np.inf, -np.inf

    def get_bottom_top(line):
        xd = line.get_xdata()
        yd = line.get_ydata()
        l, h = ax.get_xlim()
        y_dis = yd[((xd > l) & (xd < h))]
        t = np.max(y_dis) - np.min(y_dis)
        bot = np.min(y_dis) - margin * t
        top = np.max(y_dis) + margin * t
        return bot, top

    for line in lines:
        # pylint: disable-next=protected-access
        if line._animated:
            continue
        new_bot, new_top = get_bottom_top(line)
        if new_bot < bot:
            bot = new_bot
        if new_top > top:
            top = new_top

    if bot != top:
        ax.set_ylim(bot, top)
