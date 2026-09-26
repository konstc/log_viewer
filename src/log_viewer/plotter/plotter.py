""" Plotter main module """

from abc import ABC, abstractmethod
import enum
import os
import tempfile

import can
import cantools
import numpy
import pandas as pd

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

    def _get_series(self, var: str) -> pd.DataFrame:
        """
        Returns a DataFrame with timestamp and 'var' columns without NaN values
        of 'var'
        """
        return self._df.filter([self._timestamp, var]).dropna(subset=var)

    # pylint: disable-next=too-many-locals,too-many-arguments,too-many-positional-arguments
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
                    df = self._get_series(var)
                    sig_len = df[self._timestamp].size
                    fft_df["freqs"] = numpy.fft.rfftfreq(sig_len)
                    fft_df[var] = numpy.fft.rfft(df[var].values)
                    fft_df[var] = fft_df[var].apply(numpy.abs)
                    plots.append(fft_df)
            else:
                for var in pvars:
                    plots.append(self._get_series(var))
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

_INT_DTYPES = [numpy.dtype(x) for x in ("int8", "uint8", "int16", "uint16",
                                        "int32", "uint32", "int64", "uint64")]

def _signal_dtype(signal) -> numpy.dtype:
    """
    Returns the smallest dtype which holds all decoded values of the given
    cantools 'signal'. Multiplexed signals may be absent in a message, so they
    always get a float dtype to be able to store NaN.
    """
    scale, offset = signal.scale, signal.offset
    if signal.is_float:
        if signal.length == 32 and scale == 1 and offset == 0:
            return numpy.dtype(numpy.float32)
        return numpy.dtype(numpy.float64)

    if signal.is_signed:
        raw_min = -(1 << (signal.length - 1))
        raw_max = (1 << (signal.length - 1)) - 1
    else:
        raw_min, raw_max = 0, (1 << signal.length) - 1
    val_min, val_max = sorted((raw_min * scale + offset,
                               raw_max * scale + offset))

    if (signal.multiplexer_ids is None and float(scale).is_integer()
            and float(offset).is_integer()):
        for dtype in _INT_DTYPES:
            info = numpy.iinfo(dtype)
            if info.min <= val_min and val_max <= info.max:
                return dtype

    # float32 keeps every step of the signal distinguishable if the number of
    # steps from zero fits into its 24-bit mantissa
    if scale and max(abs(val_min), abs(val_max)) / abs(scale) < (1 << 24):
        return numpy.dtype(numpy.float32)
    return numpy.dtype(numpy.float64)

class _MessageStore:
    """
    Temporary on-disk storage of decoded rows of one J1939 message instance.
    Rows are collected in a fixed-size buffer and appended to a raw binary
    file when the buffer is full.
    """

    def __init__(self, path: str, signals: list, buffer_rows: int) -> None:
        """
        :param signals: list of cantools signals of the message
        """
        self._path = path
        self.signals = [sig.name for sig in signals]
        # Field 0 is a timestamp, the rest are signals in the DBC order
        self._dtype = numpy.dtype(
            [("f0", numpy.float64)] +
            [(f"f{idx + 1}", _signal_dtype(sig))
             for idx, sig in enumerate(signals)]
        )
        self._buffer = numpy.empty(buffer_rows, dtype=self._dtype)
        self._count = 0

    def append(self, timestamp: float, values: dict) -> None:
        """
        Appends a row with the given 'timestamp' and decoded signal 'values'.
        Signals absent in 'values' (e.g. multiplexed ones) are stored as NaN.
        """
        self._buffer[self._count] = (timestamp, *(
            values.get(sig, numpy.nan) for sig in self.signals
        ))
        self._count += 1
        if self._count == len(self._buffer):
            self.flush()

    def flush(self) -> None:
        """
        Appends buffered rows to the file
        """
        if self._count:
            with open(self._path, "ab") as file:
                self._buffer[:self._count].tofile(file)
            self._count = 0

    def load(self, timestamp: str) -> pd.DataFrame:
        """
        Returns all stored rows as a DataFrame with 'timestamp' column and
        signal columns. Signals which have no values are dropped.
        """
        self.flush()
        data = numpy.fromfile(self._path, dtype=self._dtype)
        df = pd.DataFrame({
            name: data[field] for name, field
            in zip([timestamp] + self.signals, self._dtype.names)
        })
        return df.dropna(axis="columns", how="all")

# pylint: disable-next=too-many-instance-attributes
class J1939DumpPlotter(BasePlotter):
    """
    Plotter to plot various J1939 dump data
    """

    MASK_WO_SA = 0xffffff00
    PDU1_TEMPLATE = "{can}SA{sa}.PDU1.DA{da}.{msg}"
    PDU2_TEMPLATE = "{can}SA{sa}.PDU2.GE{ge}.{msg}"
    BUFFER_ROWS = 1024
    BATCH_FRAMES = 1000

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
        self._temp_dir = None
        self._stores: dict[str, _MessageStore] = {}
        # Message instance name -> DataFrame with timestamp and its signals
        self._frames: dict[str, pd.DataFrame] = {}
        # Plot var -> (message instance name, signal name)
        self._vars: dict[str, tuple[str, str]] = {}

    @property
    def processed(self) -> int:
        """
        Returns a number of currently processed messages while opening
        """
        return self._processed

    @property
    def plot_vars(self) -> list[str]:
        """
        Returns a list of plot vars labels
        """
        if self._opened:
            return list(self._vars)
        return []

    def _get_series(self, var: str) -> pd.DataFrame:
        key, sig = self._vars[var]
        # Signals are stored in compact dtypes, but plot utils (e.g. RMS)
        # expect float values to avoid integer overflows
        return self._frames[key][[self._timestamp, sig]].dropna(
            subset=sig
        ).astype({sig: numpy.float64}).rename(columns={sig: var})

    def close(self) -> None:
        """
        Removes temporary files of the opening process
        """
        self._stores = {}
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None

    def __decode_message(self, msg: can.Message) -> tuple:
        """
        Returns a tuple of cantools message and decoded message data for the
        given CAN message 'msg'
        """
        frame_id = msg.arbitration_id & self.MASK_WO_SA
        try:
            _msg = self._db.get_message_by_frame_id(frame_id)
        except KeyError:
            return (None, None)
        return (_msg, _msg.decode(msg.data, decode_choices=False))

    def __get_store(self, key: str, db_msg) -> _MessageStore:
        """
        Returns a store for the message instance 'key', creates it if needed
        """
        store = self._stores.get(key)
        if store is None:
            path = os.path.join(self._temp_dir.name,
                                str(len(self._stores)) + ".bin")
            store = _MessageStore(path, db_msg.signals, self.BUFFER_ROWS)
            self._stores[key] = store
        return store

    def __load_frames(self) -> None:
        """
        Loads all stored message instances to DataFrames
        """
        self._frames = {}
        self._vars = {}
        for key, store in self._stores.items():
            df = store.load(self._timestamp)
            self._frames[key] = df
            for sig in df.columns[1:]:
                self._vars[key + "." + sig] = (key, sig)

    def __store_message(self, msg: can.Message) -> None:
        """
        Decodes the given CAN message 'msg' and stores it to a store of its
        message instance. Messages absent in the database are skipped.
        """
        db_msg, decoded = self.__decode_message(msg)
        if not db_msg:
            return
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
                msg=db_msg.name
            )
        else:
            data_key = self.PDU2_TEMPLATE.format(
                can=can_ch,
                sa=str(frame_unp.source_address),
                ge=str(frame_unp.pdu_specific),
                msg=db_msg.name
            )
        self.__get_store(data_key, db_msg).append(msg.timestamp, decoded)

    # pylint: disable-next=too-many-branches
    def open(self) -> LogOpenProgress:
        """
        Performs an opening step: processes up to BATCH_FRAMES messages
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

            self._processed = 0
            self._open_progress = LogOpenProgress.OPEN_IN_PROGRESS
            self.close()
            self._temp_dir = tempfile.TemporaryDirectory()

        for _ in range(self.BATCH_FRAMES):
            try:
                msg = next(self._msg_iterator)
            except StopIteration as exc:
                try:
                    self.__load_frames()
                finally:
                    self.close()
                if self._vars:
                    self._opened = True
                    self._open_progress = LogOpenProgress.OPEN_COMPLETED
                else:
                    self._open_progress = LogOpenProgress.OPEN_FAILED
                    raise ImportError("No data to plot in the given file",
                                      path=self._filename) from exc
                break
            self.__store_message(msg)
            self._processed += 1

        return self._open_progress
