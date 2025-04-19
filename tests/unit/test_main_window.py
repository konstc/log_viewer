""" Unit-tests for main_window.py module entities """

from PyQt6.QtWidgets import QAbstractItemView, QListWidget

# modules under test
from main_window import MainWindow, PlotItemList
from toolbar import PlotMode

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
