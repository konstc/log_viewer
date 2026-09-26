""" Log viewer's plotter package """

# pylint: disable=wrong-import-position
import matplotlib

# Backend must be selected before pyplot is imported by the modules below
matplotlib.use("qtagg")

from .exceptions import PlotterInvalidData, PlotterInitError, \
                        PlotterPlotError
from .plotter import BasePlotter, LogOpenProgress, SimpleCsvPlotter, \
                     J1939DumpPlotter
from .plotter_utils import prepare_merged_plot, get_plot_minmax, get_plot_rms
from .plot_window import PlotWindow, PlotProperty, PlotProperties, \
                         PlotPropertiesHeader
