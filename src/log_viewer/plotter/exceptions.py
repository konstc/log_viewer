""" Plotter exceptions module """

from typing import Optional

class PlotterError(Exception):
    """
    Base class for the plotter module related exceptions
    """

    def __init__(
        self,
        message: str = "",
        error_code: Optional[int] = None,
    ) -> None:
        self._error_code = error_code
        super().__init__(
            message if error_code is None else
            f"{message} [Error Code {error_code}]"
        )

class PlotterInvalidData(PlotterError):
    """
    Indicates that the plot data is invalid
    """

class PlotterInitError(PlotterError):
    """
    Indicates that the init of plotter is failed
    """

class PlotterPlotError(PlotterError):
    """
    Indicates that the plot try is failed
    """
