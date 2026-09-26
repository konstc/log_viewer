""" Integration tests for import_dialog.py module """

import pandas as pd
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QDialog

# modules under test
from import_dialog import ImportDialog, ImportWorker
from plotter import J1939DumpPlotter

def test_import_dialog_accepted(setup_j1939_dump_file, qtbot):
    """
    Integration test for successful j1939 dump file opening

    Step 0: Prepare J1939DumpPlotter by using setup_j1939_dump_file fixture
    Step 1: Instantiate a ImportDialog object
    Step 2: Call exec() of ImportDialog's object and check that it returns
        Accepted return code
    Step 3: Check that plotter is successfully opened and temporary files
        are removed
    """

    plotter = J1939DumpPlotter(setup_j1939_dump_file, ["dbc/example_db.dbc"])
    dialog = ImportDialog(plotter)
    qtbot.addWidget(dialog)

    assert dialog.exec() == QDialog.DialogCode.Accepted
    assert plotter.is_opened
    assert plotter._temp_dir is None # pylint: disable=protected-access

def test_import_dialog_rejected(setup_j1939_dump_file, qtbot):
    """
    Integration test for aborted j1939 dump file opening

    Step 0: Prepare J1939DumpPlotter by using setup_j1939_dump_file fixture
    Step 1: Instantiate a ImportDialog object
    Step 2: Prepare emulation of _ui.cancelButton click by using QTimer's
        handler
    Step 3: Call exec() of ImportDialog's object and check that it returns
        Rejected return code
    Step 4: Check that plotter is not successfully opened and temporary files
        are removed
    """

    plotter = J1939DumpPlotter(setup_j1939_dump_file, ["dbc/example_db.dbc"])
    dialog = ImportDialog(plotter)
    qtbot.addWidget(dialog)

    def to_handler():
        # pylint: disable=protected-access
        qtbot.mouseClick(dialog._ui.cancelButton, Qt.MouseButton.LeftButton)

    QTimer.singleShot(0, to_handler)
    assert dialog.exec() == QDialog.DialogCode.Rejected
    assert not plotter.is_opened
    assert plotter._temp_dir is None # pylint: disable=protected-access

def test_import_worker_failed(tmp_path, qtbot):
    """
    Integration test for failed j1939 dump file opening

    Step 0: Generate a dump with a malformed message after valid ones
    Step 1: Run ImportWorker with a J1939DumpPlotter for this dump
    Step 2: Check that failed signal is emitted, plotter is not opened and
        temporary files are removed
    """
    path = str(tmp_path / "broken_dump.csv")
    pd.DataFrame({
        "timestamp":      [0, 1, 2],
        "arbitration_id": ["0xdf00064"] * 3,
        "extended":       [1] * 3,
        "remote":         [0] * 3,
        "error":          [0] * 3,
        "dlc":            [2] * 3,
        "data":           ["AAA=", "AAA=", "!"]
    }).to_csv(path, index=False)

    plotter = J1939DumpPlotter(path, ["dbc/example_db.dbc"])
    worker = ImportWorker(plotter)
    with qtbot.waitSignal(worker.failed, timeout=5000):
        worker.run()
    assert not plotter.is_opened
    assert plotter._temp_dir is None # pylint: disable=protected-access
