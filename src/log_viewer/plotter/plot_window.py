""" Plot window module """

import enum

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, \
                                               NavigationToolbar2QT
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from PyQt6.QtCore import QPoint, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QHeaderView, QMenu, QSplitter, QTreeWidget, \
                            QTreeWidgetItem, QVBoxLayout, QWidget

from .exceptions import PlotterInvalidData
from .plotter_utils import prepare_merged_plot, get_plot_minmax, get_plot_rms
from .toolbar import PlotterToolbar

class PlotProperty(enum.Enum):
    """
    Set of properties of the each signal (table columns)
    """
    Signal = 0      # pylint: disable=invalid-name
    Value = 1       # pylint: disable=invalid-name
    Max = 2         # pylint: disable=invalid-name
    Min = 3         # pylint: disable=invalid-name
    RMS = 4         # pylint: disable=invalid-name

    def __str__(self):
        return f"{self.name}"

class PlotPropertiesHeader(QHeaderView):
    """
    Property table header class with context menu for enable/disable some
    properties
    """

    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)

        self.setDefaultSectionSize(125)

        self._max = QAction(str(PlotProperty.Max), self)
        self._max.setCheckable(True)
        self._max.setChecked(False)
        self._max.triggered.connect(self.max_changed)

        self._min = QAction(str(PlotProperty.Min), self)
        self._min.setCheckable(True)
        self._min.setChecked(False)
        self._min.triggered.connect(self.min_changed)

        self._rms = QAction(str(PlotProperty.RMS), self)
        self._rms.setCheckable(True)
        self._rms.setChecked(False)
        self._rms.triggered.connect(self.rms_changed)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

    @pyqtSlot(bool)
    def max_changed(self, state: bool) -> None:
        """
        Change visibility of PlotProperty.Max property section

        Slot for processing "triggered" signal from self._max
        """
        if state:
            self.showSection(PlotProperty.Max.value)
        else:
            self.hideSection(PlotProperty.Max.value)

    @pyqtSlot(bool)
    def min_changed(self, state: bool) -> None:
        """
        Change visibility of PlotProperty.Min property section

        Slot for processing "triggered" signal from self._min
        """
        if state:
            self.showSection(PlotProperty.Min.value)
        else:
            self.hideSection(PlotProperty.Min.value)

    @pyqtSlot(bool)
    def rms_changed(self, state: bool) -> None:
        """
        Change visibility of PlotProperty.RMS property section

        Slot for processing "triggered" signal from self._max
        """
        if state:
            self.showSection(PlotProperty.RMS.value)
        else:
            self.hideSection(PlotProperty.RMS.value)

    @pyqtSlot(QPoint)
    def context_menu(self, point: QPoint) -> None:
        """
        Create and show context menu

        Slot for processing "customContextMenuRequested" signal from self
        """
        menu = QMenu(self)
        # pylint: disable-next=attribute-defined-outside-init
        self.current_section = self.logicalIndexAt(point)
        menu.addAction(self._max)
        menu.addAction(self._min)
        menu.addAction(self._rms)
        menu.exec(self.mapToGlobal(point))

class PlotProperties(QTreeWidget):
    """
    Signals properties table class
    """

    def __init__(self, signals: list[str], parent=None) -> None:
        """
        :param signals: list of signal names
        """
        super().__init__(parent)

        self._signals = ["Cursor position"] + signals

        self.setHeader(PlotPropertiesHeader(self))
        self.setColumnCount(len(PlotProperty))
        self.setHeaderLabels([str(k) for k in PlotProperty])

        # Fill columns by default
        self.addTopLevelItem(QTreeWidgetItem(["Cursor position", "N/A"]))
        for signal in self._signals[1:]:
            self.addTopLevelItem(
                QTreeWidgetItem([signal] + ["N/A"] * (len(PlotProperty) - 1))
            )

        # Hide below columns by default
        self.setColumnHidden(PlotProperty.Max.value, True)
        self.setColumnHidden(PlotProperty.Min.value, True)
        self.setColumnHidden(PlotProperty.RMS.value, True)

    def set_property(self,
                     signal: str,
                     prop: PlotProperty,
                     value: str) -> None:
        """
        Set current value 'value' of property 'prop' for signal with name
        'signal'
        """
        if signal in self._signals:
            self.topLevelItem(self._signals.index(signal)).setText(
                prop.value, value
            )

class PlotWindow(QWidget):
    """
    Class of separate window with a plot
    """

    closed = pyqtSignal(str)

    # pylint: disable-next=too-many-locals,too-many-arguments
    def __init__(self,
                 plot_set: list[list[pd.DataFrame]],
                 title: str,
                 use_mpl_toolbar: bool = False,
                 cursor_style: str = "dashed",
                 cursor_width: float = 0.5,
                 cursor_color: str = "red",
                 plotstyle: str = "default",
                 linestyle: str = "solid",
                 linewidth: float = 1.0,
                 marker: str = "none") -> None:
        """
        :param plot_set: Set of plot dataframes grouped by axes, e.g.
            [[df1, df2, df3]] - set of 3 dataframes on single axes,
            [[df1], [df2], [df3]] - set of 3 dataframes on separate axes,
            [[df1, df2], [df3]] - set of 3 dataframes, 2 on one axes, 1 on
            another one.
        :param title: Window title
        :param use_mpl_toolbar: Use NavigationToolbar2QT from matplotlib as
            toolbar (deprecated)
        :param cursor_style: Linestyle for cursor line
        :param cursor_width: Width of cursor line in px
        :param cursor_color: Color for cursor line
        :param plotstyle: Matplotlib style for current plot
        :param linestyle: Linestyle for plot lines
        :param linewidth: Width of plot lines
        :param marker: Marker style
        """

        super().__init__()

        plt.style.use(plotstyle)

        fig = Figure(layout="tight")
        fig_rows = len(plot_set)
        ax1 = fig.add_subplot(fig_rows, 1, 1)
        cursor_axes = [ax1]

        for plots_idx, plots in enumerate(plot_set):
            if plots_idx > 0:
                ax = fig.add_subplot(fig_rows, 1, plots_idx + 1, sharex=ax1)
                cursor_axes.append(ax)
            else:
                ax = ax1
            for plot in plots:
                if len(plot.columns) != 2:
                    raise PlotterInvalidData("Plot data is invalid")
                plot.plot(
                    plot.columns[0],
                    plot.columns[1],
                    ax=ax,
                    lw=linewidth,
                    linestyle=linestyle,
                    grid=True,
                    marker=marker
                )

        self.plot_points = prepare_merged_plot(plot_set)

        self.canvas = FigureCanvasQTAgg(fig)
        self.canvas.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.canvas.setFocus()

        self.plot_properties = PlotProperties(list(self.plot_points.columns[1:]))
        for col in self.plot_points.columns[1:]:
            max_str, min_str = get_plot_minmax(self.plot_points, col)
            self.plot_properties.set_property(col, PlotProperty.Min, min_str)
            self.plot_properties.set_property(col, PlotProperty.Max, max_str)
            rms_str = get_plot_rms(self.plot_points, col)
            self.plot_properties.set_property(col, PlotProperty.RMS, rms_str)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.canvas)
        self.splitter.addWidget(self.plot_properties)

        # pylint: disable-next=invalid-name
        self.verticalLayout = QVBoxLayout(self)
        if use_mpl_toolbar:
            self.toolbar = NavigationToolbar2QT(parent=self,
                                                canvas=self.canvas)
            self.verticalLayout.addWidget(self.toolbar)
            self.verticalLayout.addWidget(self.canvas)
        else:
            self.toolbar = PlotterToolbar(self.canvas,
                                          self.plot_points,
                                          cursor_style=cursor_style,
                                          cursor_width=cursor_width,
                                          cursor_color=cursor_color,
                                          parent=self)
            self.toolbar.tooldata_updated.connect(self.refresh_properties)
            self.verticalLayout.addWidget(self.toolbar)
            self.verticalLayout.addWidget(self.splitter)

        self.setWindowTitle(title)
        self.show()

    @pyqtSlot()
    def refresh_properties(self) -> None:
        """
        Refresh property table. Used only if use_mpl_toolbar = False.

        Slot for processing "tooldata_updated" signal from self.toolbar
        """
        tooldata = self.toolbar.tooldata
        ts_col = self.plot_points.columns[0]
        view_df = self.plot_points[
            (self.plot_points[ts_col] >= tooldata.view_xlim_left) &
            (self.plot_points[ts_col] <= tooldata.view_xlim_right)
        ]

        # Current position processing
        if np.isnan(tooldata.cursor_pos):
            cursor_pos_str = "N/A"
            for col in self.plot_points.columns[1:]:
                self.plot_properties.set_property(
                    col, PlotProperty.Value, cursor_pos_str
                )
        else:
            cursor_pos_str = str(tooldata.cursor_pos)
            cursor_df = self.plot_points.loc[
                self.plot_points[ts_col] == tooldata.cursor_pos
            ]
            for col_idx, col in enumerate(cursor_df.columns[1:]):
                cur_data = cursor_df.iloc[0, col_idx + 1]
                cur_data_str = "N/A" if np.isnan(cur_data) else str(cur_data)
                self.plot_properties.set_property(
                    col, PlotProperty.Value, cur_data_str
                )
        self.plot_properties.set_property(
            "Cursor position", PlotProperty.Value, cursor_pos_str
        )

        # Max/Min/RMS processing
        for col_idx, col in enumerate(view_df.columns[1:]):
            pmax, pmin = get_plot_minmax(view_df, col)
            prms = get_plot_rms(view_df, col)
            self.plot_properties.set_property(col, PlotProperty.Max, pmax)
            self.plot_properties.set_property(col, PlotProperty.Min, pmin)
            self.plot_properties.set_property(col, PlotProperty.RMS, prms)

    # pylint: disable-next=invalid-name
    def closeEvent(self, _) -> None:
        """
        Overriden closeEvent() from QWidget for emitting closed() signal
        with window title
        """
        self.closed.emit(self.windowTitle())
