""" Toolbar base tool module """

from weakref import WeakKeyDictionary

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.cbook import Stack
from matplotlib.widgets import Widget

from PyQt6.QtCore import QObject, pyqtSignal

class PlotterBaseTool(Widget, QObject):
    """
    Toolbar base tool
    """

    nav_updated = pyqtSignal()

    def __init__(self,
                 canvas: FigureCanvasQTAgg,
                 nav_stack: Stack) -> None:
        QObject.__init__(self)

        self._canvas = canvas
        self._axes = self._canvas.figure.get_axes()
        self._nav_stack = nav_stack

        self.destroyed.connect(self.disconnect)

    def push_view(self):
        """
        Push current view into navigation stack
        """
        self._nav_stack.push(
            WeakKeyDictionary(
                # pylint: disable-next=protected-access
                {ax: (ax._get_view(),
                      (ax.get_position(True).frozen(),
                       ax.get_position().frozen()))
                 for ax in self._canvas.figure.axes}
            )
        )
        self.nav_updated.emit()

    def connect(self):
        """
        Connect mpl events to the handlers. Should be implemented in the child
        classes.
        """
        raise NotImplementedError

    def disconnect(self):
        """
        Disconnect mpl events from the handlers. Should be implemented in the
        child classes.
        """
        raise NotImplementedError

    def _button_press_handler(self, event):
        """
        Handler for 'button_press_event' event. Should be implemented in the
        child classes.
        """
        raise NotImplementedError

    def _button_release_handler(self, event):
        """
        Handler for 'button_release_event' event. Should be implemented in the
        child classes.
        """
        raise NotImplementedError

    def _move_handler(self, event):
        """
        Handler for 'motion_notify_event' event. Should be implemented in the
        child classes.
        """
        raise NotImplementedError

    def _draw_handler(self, event):
        """
        Handler for 'draw_event' event. Should be implemented in the child
        classes.
        """
        raise NotImplementedError
