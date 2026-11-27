""" Unit-tests for main_window.py module entities """

from types import SimpleNamespace

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import QAbstractItemView, QListWidget

# modules under test
from main_window import MainWindow, PlotItemList
from toolbar import PlotMode

SIGNALS = ["CAN0.SA0.PDU2.GE0.EEC1.EngineSpeed",
           "CAN0.SA0.PDU2.GE0.EEC1.EngineTorque",
           "CAN0.SA0.PDU2.GE0.ET1.CoolantTemp",
           "CAN0.SA3.PDU2.GE0.EEC1.EngineSpeed",
           "CAN0.SA3.PDU1.DA0.TSC1.RequestedSpeed"]
EEC1 = [name for name in SIGNALS if ".EEC1." in name]
ET1 = [name for name in SIGNALS if ".ET1." in name]
TSC1 = [name for name in SIGNALS if ".TSC1." in name]

def make_plot_item_list(items: list[str]) -> PlotItemList:
    """
    Instantiates a PlotItemList with 'items' in a new multi selection list
    """
    listw = QListWidget()
    listw.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
    return PlotItemList(items, listw)

def shown_items(pil: PlotItemList) -> list[str]:
    """
    Gets the names of items shown in the list widget of 'pil'
    """
    # pylint: disable-next=protected-access
    return [name for name, item in pil._items.items() if not item.isHidden()]

# pylint: disable-next=unused-argument
def test_plot_item_list(setup_plot_item_list, qtbot):
    """
    Unit-tests for PlotItemList methods

    Step 0: Prepare QListWidget parent object
    Step 1: Instantiate a PlotItemList with setup_plot_item_list fixture
    Step 2: Check that selected_plots() method returns [[]] for all modes
    Step 3: Call select_all() method
    Step 4: Check that selected_plots() method returns lists corresponding to
        setup_plot_item_list fixture
    Step 5: Call assign_selected() method
    Step 6: Check that selected_plots(PlotMode.PLOTMODE_MANUAL) method returns
        returns list corresponding to setup_plot_item_list fixture
    Step 7: Call clear_plot_assignment() method
    Step 8: Check that selected_plots(PlotMode.PLOTMODE_MANUAL) method returns
        [[]]
    Step 9: Call select_clear() method
    Step 10: Check that selected_plots() method returns [[]] for all modes
    Step 11: Add test item by calling add_items() method
    Step 12: Call select_all() method
    Step 13: Check that selected_plots() method returns lists corresponding to
        setup_plot_item_list fixture with an added test item
    Step 14: Call clear() method
    Step 15: Check that selected_plots() method returns [[]] for all modes
    """
    listw = QListWidget()
    listw.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

    pil = PlotItemList(setup_plot_item_list, listw)

    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == [[]]
    assert pil.selected_plots(PlotMode.PLOTMODE_SEPARATED) == [[]]
    assert pil.selected_plots(PlotMode.PLOTMODE_MANUAL) == [[]]

    merged_all = [setup_plot_item_list]
    separated_all = [[plot] for plot in setup_plot_item_list]

    pil.select_all()
    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == merged_all
    assert pil.selected_plots(PlotMode.PLOTMODE_SEPARATED) == separated_all
    assert pil.selected_plots(PlotMode.PLOTMODE_MANUAL) == [[]]

    pil.assign_selected()
    assert pil.selected_plots(PlotMode.PLOTMODE_MANUAL) == merged_all

    pil.clear_plot_assignment()
    assert pil.selected_plots(PlotMode.PLOTMODE_MANUAL) == [[]]

    pil.select_clear()
    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == [[]]
    assert pil.selected_plots(PlotMode.PLOTMODE_SEPARATED) == [[]]
    assert pil.selected_plots(PlotMode.PLOTMODE_MANUAL) == [[]]

    pil.add_items(["added_sig"])
    merged_all = [setup_plot_item_list + ["added_sig"]]
    separated_all = [[plot] for plot in setup_plot_item_list + ["added_sig"]]
    pil.select_all()
    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == merged_all
    assert pil.selected_plots(PlotMode.PLOTMODE_SEPARATED) == separated_all
    assert pil.selected_plots(PlotMode.PLOTMODE_MANUAL) == [[]]

    pil.clear()
    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == [[]]
    assert pil.selected_plots(PlotMode.PLOTMODE_SEPARATED) == [[]]
    assert pil.selected_plots(PlotMode.PLOTMODE_MANUAL) == [[]]

# pylint: disable-next=unused-argument
def test_main_window(qtbot):
    """
    Unit-tests for MainWindow methods

    Step 0: Instantiate a MainWindow object
    Step 1: Check that there is no opened plot windows
    Step 2: Check that there is no instantiated plotter
    """
    window = MainWindow()

    # pylint: disable=protected-access
    assert window._ready is False
    assert window._file == ""
    assert not window._plot_windows
    assert not window._plot_windows_actions
    assert window._plotter is None

# pylint: disable-next=unused-argument
def test_plot_item_list_filter(qtbot):
    """
    Unit-tests for hiding and showing items by PlotItemList.set_filter()

    Step 0: Instantiate a PlotItemList with J1939 signal names
    Step 1: Check that all items are shown
    Step 2: Set filters: substring, several words, glob, nothing matching
    Step 3: Check that only the matching items are shown, while all items are
        still in the list
    Step 4: Reset the filter and check that all items are shown again
    """
    pil = make_plot_item_list(SIGNALS)
    assert shown_items(pil) == SIGNALS
    assert (pil.shown_count, pil.total_count) == (5, 5)

    for query, expected in [("eec1", EEC1),
                            ("EEC1 speed", [SIGNALS[0], SIGNALS[3]]),
                            ("*.SA3.*", SIGNALS[3:]),
                            ("SA3.*", []),
                            ("not_found", [])]:
        pil.set_filter(query)
        assert shown_items(pil) == expected, query
        assert (pil.shown_count, pil.total_count) == (len(expected), 5)
        # pylint: disable-next=protected-access
        assert pil._lw.count() == 5

    pil.set_filter("")
    assert shown_items(pil) == SIGNALS
    assert (pil.shown_count, pil.total_count) == (5, 5)

# pylint: disable-next=unused-argument
def test_plot_item_list_filter_selection(qtbot):
    """
    Unit-tests for the selection of PlotItemList with an active filter

    Step 0: Instantiate a PlotItemList with J1939 signal names
    Step 1: Filter, call select_all() and check that only the shown items
        are selected
    Step 2: Change the filter, call select_all() again and check that the
        selection of the hidden items is kept and is returned by
        selected_plots()
    Step 3: Call select_clear() and check that the hidden items are
        deselected too
    """
    pil = make_plot_item_list(SIGNALS)

    pil.set_filter("eec1")
    pil.select_all()
    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == [EEC1]
    assert pil.selected_count == 3

    pil.set_filter("et1")
    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == [EEC1]
    pil.select_all()
    selected = [name for name in SIGNALS if name in EEC1 + ET1]
    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == [selected]
    assert pil.selected_plots(PlotMode.PLOTMODE_SEPARATED) == \
                                                [[name] for name in selected]
    assert pil.selected_plots(PlotMode.PLOTMODE_MANUAL) == [[]]
    assert (pil.shown_count, pil.selected_count) == (1, 4)

    pil.select_clear()
    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == [[]]
    assert pil.selected_count == 0
    pil.set_filter("")
    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == [[]]

# pylint: disable-next=unused-argument
def test_plot_item_list_filter_manual(qtbot):
    """
    Unit-tests for the manual plot assignment of PlotItemList with an active
    filter

    Step 0: Instantiate a PlotItemList with J1939 signal names
    Step 1: Filter, select all and assign the selection to a plot
    Step 2: Filter again, so that an assigned item is shown, select all and
        assign the selection to the next plot
    Step 3: Check that the assigned items are not selected again and both
        plots are kept after resetting the filter
    Step 4: Clear the assignment and check that no items become selected
    """
    pil = make_plot_item_list(SIGNALS)

    pil.set_filter("eec1")
    pil.select_all()
    pil.assign_selected()
    assert pil.selected_plots(PlotMode.PLOTMODE_MANUAL) == [EEC1]
    assert pil.selected_count == 0

    pil.set_filter("sa3")
    assert shown_items(pil) == SIGNALS[3:]
    pil.select_all()
    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == [TSC1]
    pil.assign_selected()
    assert pil.selected_plots(PlotMode.PLOTMODE_MANUAL) == [EEC1, TSC1]

    pil.set_filter("")
    assert pil.selected_plots(PlotMode.PLOTMODE_MANUAL) == [EEC1, TSC1]
    # pylint: disable=protected-access
    for name in EEC1:
        assert "[PLOT0]" in pil._items[name].text()
    assert "[PLOT1]" in pil._items[TSC1[0]].text()
    assert "[PLOT" not in pil._items[ET1[0]].text()
    # pylint: enable=protected-access

    pil.clear_plot_assignment()
    assert pil.selected_plots(PlotMode.PLOTMODE_MANUAL) == [[]]
    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == [[]]
    pil.select_all()
    assert pil.selected_plots(PlotMode.PLOTMODE_MERGED) == [SIGNALS]

# pylint: disable-next=unused-argument
def test_plot_item_list_filter_add_items(qtbot):
    """
    Unit-tests for applying the filter of PlotItemList to added items

    Step 0: Instantiate a PlotItemList with J1939 signal names and filter it
    Step 1: Call clear() and check that the list is empty
    Step 2: Add the same items and check that the filter is applied again
    Step 3: Add items sorted before the present ones and check that the
        filter is applied to them and the shown items are still the same
    """
    pil = make_plot_item_list(SIGNALS)
    pil.set_filter("eec1")

    pil.clear()
    assert (pil.shown_count, pil.total_count, pil.selected_count) == (0, 0, 0)

    pil.add_items(SIGNALS)
    assert shown_items(pil) == EEC1
    assert (pil.shown_count, pil.total_count) == (3, 5)

    added = ["A0.SA0.PDU2.GE0.EEC1.ActualTorque", "A0.SA0.PDU2.GE0.ET1.FuelTemp"]
    pil.add_items(added)
    assert shown_items(pil) == EEC1 + added[:1]
    assert (pil.shown_count, pil.total_count) == (4, 7)

    pil.set_filter("")
    assert shown_items(pil) == SIGNALS + added

@pytest.fixture(name="opened_window")
def fixture_opened_window(qtbot):
    """
    MainWindow showing J1939 signal names as if a file was opened
    """
    window = MainWindow()
    qtbot.addWidget(window)
    # pylint: disable=protected-access
    window._ready = True
    window._plotter = SimpleNamespace(plot_vars=SIGNALS)
    window.file_refresh()
    return window

def count_text(window: MainWindow) -> str:
    """
    Gets the text of the counter of plot items
    """
    return window._ui.countLabel.text() # pylint: disable=protected-access

def test_main_window_filter(opened_window, qtbot):
    """
    Unit-tests for the signal filter of MainWindow

    Step 0: Instantiate a MainWindow and open a file in it
    Step 1: Type a filter and check the counter
    Step 2: Select all items and check that the counter is updated
    Step 3: Refresh the file and check that the filter is kept and applied
    Step 4: Press Escape and check that the filter is cleared
    Step 5: Close the file and check that the filter is cleared and disabled
    Step 6: Open the file again and check that all items are shown
    """
    window = opened_window
    filter_edit = window._ui.filterEdit # pylint: disable=protected-access
    assert filter_edit.isEnabled()
    assert filter_edit.isClearButtonEnabled()
    assert filter_edit.placeholderText() == "Filter signals…"
    assert count_text(window) == "Shown 5 of 5 · selected 0"

    qtbot.keyClicks(filter_edit, "eec1")
    assert count_text(window) == "Shown 3 of 5 · selected 0"

    window.select_all()
    qtbot.waitUntil(lambda: count_text(window) == "Shown 3 of 5 · selected 3")

    window.file_refresh()
    assert filter_edit.text() == "eec1"
    assert count_text(window) == "Shown 3 of 5 · selected 0"

    qtbot.keyClick(filter_edit, Qt.Key.Key_Escape)
    assert filter_edit.text() == ""
    assert count_text(window) == "Shown 5 of 5 · selected 0"

    qtbot.keyClicks(filter_edit, "sa3")
    window.file_close()
    assert filter_edit.text() == ""
    assert not filter_edit.isEnabled()
    assert count_text(window) == "Shown 0 of 0 · selected 0"

    # pylint: disable=protected-access
    window._ready = True
    window._plotter = SimpleNamespace(plot_vars=SIGNALS)
    window.file_refresh()
    assert filter_edit.isEnabled()
    assert count_text(window) == "Shown 5 of 5 · selected 0"

def test_main_window_filter_focus(opened_window, qtbot):
    """
    Unit-tests for moving the keyboard focus to and from the signal filter

    Step 0: Instantiate a MainWindow and open a file in it
    Step 1: Check that Ctrl+F shortcut moves the focus to the filter and
        selects its text
    Step 2: Press Down in the filter and check that the focus moves to the
        list and the first shown item becomes current without being selected
    """
    window = opened_window
    # pylint: disable=protected-access
    filter_edit = window._ui.filterEdit
    list_widget = window._ui.listWidget
    shortcut = window._filter_shortcut
    # pylint: enable=protected-access

    assert QKeySequence("Ctrl+F") in shortcut.keys()
    filter_edit.setText("sa3")
    shortcut.activated.emit()
    assert window.focusWidget() is filter_edit
    assert filter_edit.selectedText() == "sa3"

    qtbot.keyClick(filter_edit, Qt.Key.Key_Down)
    assert window.focusWidget() is list_widget
    current = list_widget.currentItem()
    assert current is not None and not current.isHidden()
    # the list is sorted by name: PDU1 goes before PDU2
    assert TSC1[0] in current.text()
    assert not list_widget.selectedItems()
