""" Unit-tests for plotter.py entities """

import base64

import pandas as pd
import pytest

# modules under test
from plotter import BasePlotter, SimpleCsvPlotter, J1939DumpPlotter, \
                    LogOpenProgress, PlotWindow, PlotterInitError, \
                    PlotterPlotError

def test_base_plotter_init():
    """
    Unit-test for BasePlotter.__init__ function

    Check that an attempt to instantiate a BasePlotter leads to an TypeError
    exception
    """
    with pytest.raises(TypeError):
        # pylint: disable-next=abstract-class-instantiated
        BasePlotter("")

# pylint: disable-next=unused-argument
def test_simple_csv_plotter(setup_simple_csv_file, qtbot):
    """
    Unit-tests for SimpleCsvPlotter methods

    Step 0-2: Check that an attempt to instantiate a SimpleCsvPlotter with an
        empty filename/delimeter/timestamp leads to a PlotterInitError 
        exception
    Step 3: Check that attempt to instantiate a SimpleCsvPlotter with a
        non-existent filename leads to a PlotterInitError exception
    Step 4: Instantiate a SimpleCsvPlotter with setup_simple_csv_file fixture
    Step 5: Check that is_opened property is False
    Step 6: Check that plot_vars property is []
    Step 7: Check that attempt to call plot() method in unopened state leads to
        PlotterPlotError exception
    Step 8: Call open() method and check that it returns
        LogOpenProgress.OPEN_COMPLETED
    Step 9: Check that is_opened property is True
    Step 10: Check that plot_vars property contains expected signals
    Step 11: Call plot() method with expected signals
    Step 12: Check that the returned object has a PlotWindow type
    """
    with pytest.raises(PlotterInitError):
        SimpleCsvPlotter("", ";", "timestamp", {})

    with pytest.raises(PlotterInitError):
        SimpleCsvPlotter(setup_simple_csv_file, "", "timestamp", {})

    with pytest.raises(PlotterInitError):
        SimpleCsvPlotter(setup_simple_csv_file, ";", "", {})

    with pytest.raises(PlotterInitError):
        SimpleCsvPlotter("Path", ";", "timestamp", {})

    plotter = SimpleCsvPlotter(setup_simple_csv_file, ";", "timestamp", {})

    assert not plotter.is_opened
    assert not plotter.plot_vars
    with pytest.raises(PlotterPlotError):
        plotter.plot(["sig1"], False, False)

    assert plotter.open() == LogOpenProgress.OPEN_COMPLETED
    assert plotter.is_opened
    assert plotter.plot_vars == ["sig1"]

    pwin = plotter.plot([["sig1"]], False)
    assert isinstance(pwin, PlotWindow)
    pwin.close()
    qtbot.wait(10)

# pylint: disable-next=unused-argument
def test_j1939_dump_plotter(setup_j1939_dump_file, qtbot):
    """
    Unit-tests for J1939DumpPlotter methods

    Step 0-1: Check that an attempt to instantiate a J1939DumpPlotter with an
        empty filename/dbc_files leads to a PlotterInitError exception
    Step 2: Check that an attempt to instantiate a J1939DumpPlotter with a
        non-existent dbc file leads to a PlotterInitError exception
    Step 3: Instantiate a J1939DumpPlotter with setup_j1939_dump_file fixture
    Step 4: Check that is_opened property is False
    Step 5: Check that plot_vars property is []
    Step 6: Perform opening process with checking that processed property is
        always increments
    Step 7: Check that final call returns LogOpenProgress.OPEN_COMPLETED
    Step 8: Check that plot_vars property contains expected signals
    Step 9: Call plot() method with expected signals
    Step 10: Check that the returned object has a PlotWindow type
    """
    with pytest.raises(PlotterInitError):
        J1939DumpPlotter("", ["dbc/example_db.dbc"])

    with pytest.raises(PlotterInitError):
        J1939DumpPlotter(setup_j1939_dump_file, [""])

    with pytest.raises(PlotterInitError):
        J1939DumpPlotter(setup_j1939_dump_file, ["dbc/example_db.dbc1"])

    plotter = J1939DumpPlotter(setup_j1939_dump_file, ["dbc/example_db.dbc"])

    assert not plotter.is_opened
    assert not plotter.plot_vars

    processed = plotter.processed
    while True:
        progress = plotter.open()
        if progress == LogOpenProgress.OPEN_IN_PROGRESS:
            assert plotter.processed > processed
            processed = plotter.processed
        else:
            break

    assert plotter.open() == LogOpenProgress.OPEN_COMPLETED
    assert any(sig in ["SA100.PDU2.GE0.ExampleMessageRx.RxSignal1",
                       "SA100.PDU2.GE0.ExampleMessageRx.RxSignal2",
                       "SA249.PDU1.DA100.ExampleMessageTx.TxSignal1",
                       "SA249.PDU1.DA100.ExampleMessageTx.TxSignal2"]
                    for sig in plotter.plot_vars)

    pwin = plotter.plot([["SA100.PDU2.GE0.ExampleMessageRx.RxSignal1"]], False)
    assert isinstance(pwin, PlotWindow)
    pwin.close()
    qtbot.wait(10)

# pylint: disable-next=unused-argument
def test_j1939_dump_plotter_instances(tmp_path, qtbot):
    """
    Unit-test for J1939DumpPlotter storage of message instances

    Step 0: Generate a dump with ExampleMessageRx from two source addresses
        (more rows than J1939DumpPlotter.BUFFER_ROWS for each of them)
    Step 1: Open the dump
    Step 2: Check that plot_vars contains signals of both instances only
    Step 3: Check that decoded values and timestamps of each instance are
        stored in the original order without NaN values
    Step 4: Check that temporary files are removed
    """
    rows = J1939DumpPlotter.BUFFER_ROWS * 2 + 10
    records = []
    for idx in range(rows):
        for src in (100, 101):
            value = idx % 256
            data = base64.b64encode(bytes([value, (idx + src) % 4])).decode()
            records.append({
                "timestamp": idx + src / 1000,
                "arbitration_id": hex(0x0df00000 | src),
                "extended": 1, "remote": 0, "error": 0, "dlc": 2,
                "data": data
            })
    path = str(tmp_path / "dump.csv")
    pd.DataFrame(records).to_csv(path, index=False)

    plotter = J1939DumpPlotter(path, ["dbc/example_db.dbc"])
    while plotter.open() == LogOpenProgress.OPEN_IN_PROGRESS:
        pass
    assert plotter.is_opened
    assert plotter.processed == rows * 2

    assert sorted(plotter.plot_vars) == [
        "SA100.PDU2.GE0.ExampleMessageRx.RxSignal1",
        "SA100.PDU2.GE0.ExampleMessageRx.RxSignal2",
        "SA101.PDU2.GE0.ExampleMessageRx.RxSignal1",
        "SA101.PDU2.GE0.ExampleMessageRx.RxSignal2",
    ]

    for src in (100, 101):
        prefix = f"SA{src}.PDU2.GE0.ExampleMessageRx."
        sig1 = plotter._get_series(prefix + "RxSignal1")
        sig2 = plotter._get_series(prefix + "RxSignal2")
        assert len(sig1) == rows and len(sig2) == rows
        assert list(sig1["timestamp"]) == [i + src / 1000 for i in range(rows)]
        # RxSignal1 is a signed 8-bit signal
        assert list(sig1[prefix + "RxSignal1"]) == [
            (i % 256) - 256 if i % 256 > 127 else i % 256 for i in range(rows)
        ]
        assert list(sig2[prefix + "RxSignal2"]) == [
            (i + src) % 4 for i in range(rows)
        ]

    # pylint: disable-next=protected-access
    assert plotter._temp_dir is None
