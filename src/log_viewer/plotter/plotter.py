""" Plotter main module """

from abc import ABC, abstractmethod
import enum
import os

import can
import cantools
import numpy
import pandas as pd
from scipy import fft

from .exceptions import PlotterInitError, PlotterPlotError
from .plot_window import PlotWindow

class LogOpenProgress(enum.Enum):
    """
    Open progress states
    """
    OPEN_NOT_STARTED = enum.auto()
    OPEN_COMPLETED = enum.auto()
    OPEN_IN_PROGRESS = enum.auto()
    OPEN_FAILED = enum.auto()

class BasePlotter(ABC):
    """
    Abstract base plotter
    """

    TIMESTAMP_DEFAULT = "timestamp"

    def __init__(self,
                 filename: os.PathLike[str]) -> None:

        if not os.path.isfile(filename):
            raise PlotterInitError

        self._filename = filename
        self._opened = False
        self._df = pd.DataFrame()
        self._timestamp = self.TIMESTAMP_DEFAULT

    @property
    def plot_vars(self) -> list[str]:
        """
        Returns a list of plot vars labels
        """
        if self._opened:
            pvars = list(self._df)
            if self._timestamp in pvars:
                pvars.remove(self._timestamp)
            return pvars
        return []

    @property
    def is_opened(self) -> bool:
        """
        Returns the plotter open state (True if successfully opened)
        """
        return self._opened

    @abstractmethod
    def open(self) -> LogOpenProgress:
        """
        Performs an opening process. Should be overriden by the child classes.
        """
        return LogOpenProgress.OPEN_FAILED

    # pylint: disable-next=too-many-locals,too-many-arguments
    def plot(self,
             vars_set: list[list[str]],
             spectrum: bool,
             plotstyle: str = "default",
             linestyle: str = "solid",
             linewidth: float = 1.0,
             marker: str = "none",
             use_mpl_toolbar: bool = False,
             cursor_style: str = "dashed",
             cursor_width: float = 0.5,
             cursor_color: str = "red") -> PlotWindow:
        """
        Performs plotting
        """
        if not self._opened:
            raise PlotterPlotError

        plot_set = []
        for pvars in vars_set:
            if not any(x in self.plot_vars for x in pvars):
                raise PlotterPlotError
            plots = []
            if spectrum:
                for var in pvars:
                    fft_df = pd.DataFrame()
                    df = self._df.dropna(subset=var)
                    sig_len = df[self._timestamp].size
                    fft_df["freqs"] = fft.rfftfreq(sig_len)
                    fft_df[var] = fft.rfft(df[var].values)
                    fft_df[var] = fft_df[var].apply(numpy.abs)
                    plots.append(fft_df)
            else:
                for var in pvars:
                    plots.append(
                        self._df.filter([self._timestamp, var]).dropna(
                            subset=var
                        )
                    )
            if plots:
                plot_set.append(plots)

        return PlotWindow(
            plot_set=plot_set,
            title="Plot: " + str(vars_set),
            use_mpl_toolbar=use_mpl_toolbar,
            cursor_style=cursor_style,
            cursor_width=cursor_width,
            cursor_color=cursor_color,
            plotstyle=plotstyle,
            linestyle=linestyle,
            linewidth=linewidth,
            marker=marker
        )

class SimpleCsvPlotter(BasePlotter):
    """
    Plotter to plot CSV data
    """

    def __init__(self,
                 filename: os.PathLike[str],
                 delimiter: str,
                 timestamp: str,
                 scales: dict[str, float]) -> None:
        super().__init__(filename)

        if not delimiter or not timestamp:
            raise PlotterInitError

        self._timestamp = timestamp
        self._delimiter = delimiter
        self._scales = scales

    def open(self) -> LogOpenProgress:
        """
        Performs an opening process
        """
        self._df = pd.read_csv(self._filename, delimiter=self._delimiter)
        columns = list(self._df.columns)
        if self._timestamp in columns:
            self._df = self._df.sort_values(by=[self._timestamp])
        else:
            self._df[self._timestamp] = range(0, len(self._df))

        # Apply scales
        for var, scale in self._scales.items():
            if var in columns:
                # pylint: disable-next=cell-var-from-loop
                self._df[var] = self._df[var].apply(lambda x: x * scale)

        self._opened = True
        return LogOpenProgress.OPEN_COMPLETED

# pylint: disable-next=too-many-instance-attributes
class J1939DumpPlotter(BasePlotter):
    """
    Plotter to plot various J1939 dump data
    """

    MASK_WO_SA = 0xffffff00
    PDU1_TEMPLATE = "{can}SA{sa}.PDU1.DA{da}.{msg}"
    PDU2_TEMPLATE = "{can}SA{sa}.PDU2.GE{ge}.{msg}"

    def __init__(self,
                 filename: os.PathLike[str],
                 dbc_files: list[str],
                 asc_base: str = "hex",
                 asc_rel_timestamp: bool = True) -> None:
        super().__init__(filename)

        if not dbc_files:
            raise PlotterInitError

        if not any(os.path.isfile(x) for x in dbc_files):
            raise PlotterInitError

        self._db = cantools.db.Database(frame_id_mask=self.MASK_WO_SA)
        for dbc_file_path in dbc_files:
            self._db.add_dbc_file(dbc_file_path)
        for msg in self._db._messages:
            msg._frame_id &= self.MASK_WO_SA
        self._db.refresh()

        self._asc_base = asc_base
        self._asc_rel_timestamp = asc_rel_timestamp

        self._open_progress = LogOpenProgress.OPEN_NOT_STARTED
        self._processed = 0
        self._reader = None
        self._msg_iterator = None
        self._msg_list = []

    @property
    def processed(self) -> int:
        """
        Returns a number of currently processed messages while opening
        """
        return self._processed

    def __decode_message(self, msg: can.Message) -> tuple:
        """
        Returns a tuple of message name and message data for the given
        CAN message 'msg'
        """
        frame_id = msg.arbitration_id & self.MASK_WO_SA
        # pylint: disable-next=protected-access
        if frame_id in self._db._frame_id_to_message:
            _msg = self._db.get_message_by_frame_id(frame_id)
            return (_msg.name, _msg.decode(msg.data, decode_choices=False))
        return (None, None)

    def open(self) -> LogOpenProgress:
        """
        Performs an opening step
        """

        if self._open_progress == LogOpenProgress.OPEN_FAILED:
            self._open_progress = LogOpenProgress.OPEN_NOT_STARTED
        elif self._open_progress == LogOpenProgress.OPEN_COMPLETED:
            return self._open_progress

        if self._open_progress == LogOpenProgress.OPEN_NOT_STARTED:
            # Select the reader
            _, ext = os.path.splitext(self._filename)
            if ext == ".log":
                self._reader = can.CanutilsLogReader(self._filename)
            elif ext == ".asc":
                self._reader = can.ASCReader(self._filename,
                                             self._asc_base,
                                             self._asc_rel_timestamp)
            elif ext == ".blf":
                self._reader = can.BLFReader(self._filename)
            elif ext == ".csv":
                self._reader = can.CSVReader(self._filename)
            else:
                raise ImportError("Format is not supported",
                                  path=self._filename)

            # Generate an iterator
            self._msg_iterator = iter(self._reader)

            self._msg_list = []
            self._processed = 0
            self._open_progress = LogOpenProgress.OPEN_IN_PROGRESS

        try:
            msg = next(self._msg_iterator)
        except StopIteration as exc:
            self._df = pd.DataFrame.from_dict(self._msg_list)
            self._df.dropna(axis="columns", how="all", inplace=True)
            if self._timestamp in self._df.columns:
                self._opened = True
                self._open_progress = LogOpenProgress.OPEN_COMPLETED
            else:
                self._open_progress = LogOpenProgress.OPEN_FAILED
                raise ImportError("No data to plot in the given file",
                                  path=self._filename) from exc
            self._msg_list = []
        else:
            decoded = self.__decode_message(msg)
            if decoded[0]:
                if msg.channel:
                    if isinstance(msg.channel, str):
                        can_ch = msg.channel + "."
                    else:
                        can_ch = "CAN" + str(msg.channel) + "."
                else:
                    can_ch = ""
                frame_unp = cantools.j1939.frame_id_unpack(msg.arbitration_id)
                if cantools.j1939.is_pdu_format_1(frame_unp.pdu_format):
                    data_key = self.PDU1_TEMPLATE.format(
                        can=can_ch,
                        sa=str(frame_unp.source_address),
                        da=str(frame_unp.pdu_specific),
                        msg=decoded[0]
                    )
                else:
                    data_key = self.PDU2_TEMPLATE.format(
                        can=can_ch,
                        sa=str(frame_unp.source_address),
                        ge=str(frame_unp.pdu_specific),
                        msg=decoded[0]
                    )
                msg_data = {self._timestamp: msg.timestamp}
                for sig, value in decoded[1].items():
                    msg_data[data_key + "." + sig] = value
                self._msg_list.append(msg_data)
            self._processed += 1

        return self._open_progress
