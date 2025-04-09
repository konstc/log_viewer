""" Toolbar zoomer tool module """

from collections import namedtuple

import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.cbook import Stack
from matplotlib.backend_bases import MouseButton

from .base_tool import PlotterBaseTool

class PlotterToolbarRectZoomer(PlotterBaseTool):
    """
    Toolbar zoomer tool
    """

    _ZoomInfo = namedtuple("_ZoomInfo", "direction start_xy axes cbar")

    def __init__(self,
                 canvas: FigureCanvasQTAgg,
                 nav_stack: Stack) -> None:

        super().__init__(canvas, nav_stack)

        self._zoom_info = None
        self._zoom_started = False
        self.connect()

    def _draw_rubberband(self,
                         x0: float,
                         y0: float,
                         x1: float,
                         y1: float) -> None:
        height = self._canvas.figure.bbox.height
        y1 = height - y1
        y0 = height - y0
        rect = [int(val) for val in (x0, y0, x1 - x0, y1 - y0)]
        self._canvas.drawRectangle(rect)

    def _remove_rubberband(self) -> None:
        self._canvas.drawRectangle(None)

    def connect(self) -> None:
        self._cid_press = self._canvas.mpl_connect(
            "button_press_event", self._button_press_handler
        )
        self._cid_release = self._canvas.mpl_connect(
            "button_release_event", self._button_release_handler
        )
        self._cid_move = self._canvas.mpl_connect(
            "motion_notify_event", self._move_handler
        )

    def disconnect(self) -> None:
        self._canvas.mpl_disconnect(self._cid_press)
        self._canvas.mpl_disconnect(self._cid_release)
        self._canvas.mpl_disconnect(self._cid_move)

    def _button_press_handler(self, event) -> None:
        if (event.button not in [MouseButton.LEFT, MouseButton.RIGHT] or
            event.x is None or
            event.y is None):
            return
        axes = [a for a in self._canvas.figure.get_axes()
                if a.in_axes(event) and a.get_navigate() and a.can_zoom()]
        if not axes:
            return
        if self._nav_stack() is None:
            self.push_view()
        self._zoom_started = True
        if hasattr(axes[0], "_colorbar"):
            # pylint: disable-next=protected-access
            cbar = axes[0]._colorbar.orientation
        else:
            cbar = None
        self._zoom_info = self._ZoomInfo(
            direction="in" if event.button == MouseButton.LEFT else "out",
            start_xy=(event.x, event.y),
            axes=axes,
            cbar=cbar
        )

    def _button_release_handler(self, event) -> None:
        if self._zoom_info is None:
            return

        self._zoom_started = False
        self._remove_rubberband()

        start_x, start_y = self._zoom_info.start_xy
        key = event.key
        if self._zoom_info.cbar == "horizontal":
            key = "x"
        elif self._zoom_info.cbar == "vertical":
            key = "y"

        # Ignore single clicks: 5 pixels is a threshold that allows the user to
        # "cancel" a zoom action by zooming by less than 5 pixels.
        if ((abs(event.x - start_x) < 5 and key != "y") or
            (abs(event.y - start_y) < 5 and key != "x")):
            self._canvas.draw_idle()
            self._zoom_info = None
            return

        for i, ax in enumerate(self._zoom_info.axes):
            # Detect whether this Axes is twinned with an earlier Axes in the
            # list of zoomed Axes, to avoid double zooming.
            twinx = any(ax.get_shared_x_axes().joined(ax, prev)
                        for prev in self._zoom_info.axes[:i])
            twiny = any(ax.get_shared_y_axes().joined(ax, prev)
                        for prev in self._zoom_info.axes[:i])
            # pylint: disable-next=protected-access
            ax._set_view_from_bbox(
                (start_x, start_y, event.x, event.y),
                self._zoom_info.direction, key, twinx, twiny)

        self._canvas.draw_idle()
        self._zoom_info = None
        self.push_view()

    def _move_handler(self, event) -> None:
        if self._zoom_started:
            start_xy = self._zoom_info.start_xy
            ax = self._zoom_info.axes[0]
            (x0, y0), (x1, y1) = np.clip(
                [start_xy, [event.x, event.y]], ax.bbox.min, ax.bbox.max
            )
            key = event.key
            if self._zoom_info.cbar == "horizontal":
                key = "x"
            elif self._zoom_info.cbar == "vertical":
                key = "y"
            if key == "x":
                y0, y1 = ax.bbox.intervaly
            elif key == "y":
                x0, x1 = ax.bbox.intervalx
            self._draw_rubberband(x0, y0, x1, y1)

    def _draw_handler(self, event) -> None:
        pass
