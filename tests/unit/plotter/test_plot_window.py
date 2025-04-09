""" Unit-tests for plot_window.py entities """

# modules under test
from plotter import PlotProperty, PlotProperties, PlotPropertiesHeader, \
                    PlotWindow

# pylint: disable-next=unused-argument
def test_plot_window(setup_plot_list, qtbot):
    """
    Unit-tests for PlotWindow methods with subobjects

    Step 0: Instantiate a PlotWindow with setup_plot_list fixture
    Step 1: Check that the header object of plot_properties has a
        PlotPropertiesHeader type
    Step 2: Check that the header has "_max", "_min" and "_rms" attributes
    Step 3: Check that all above attributes is not checked
    Step 4-6: Check that corresponding sections are hidden when corresponding
        signals are emitted
    Step 7: Check that the plot_properties attribute of the PlotWindow object
        has a PlotProperties type
    Step 8: Check that props._signals corresponds to setup_plot_list fixture
    Step 9: Check initial states of all properties
    Step 10-12: Check that set_property() method sets the corresponding
        signal's property
    """
    pwin = PlotWindow(setup_plot_list, "Test PlotWindow")

    # PlotPropertiesHeader tests

    props_head = pwin.plot_properties.header()
    assert isinstance(props_head, PlotPropertiesHeader)

    assert hasattr(props_head, "_max")
    assert hasattr(props_head, "_min")
    assert hasattr(props_head, "_rms")

    # pylint: disable=protected-access
    assert not props_head._max.isChecked()
    assert not props_head._min.isChecked()
    assert not props_head._rms.isChecked()

    props_head._max.triggered.emit(True)
    assert not props_head.isSectionHidden(PlotProperty.Max.value)
    props_head._max.triggered.emit(False)
    assert props_head.isSectionHidden(PlotProperty.Max.value)

    props_head._min.triggered.emit(True)
    assert not props_head.isSectionHidden(PlotProperty.Min.value)
    props_head._min.triggered.emit(False)
    assert props_head.isSectionHidden(PlotProperty.Min.value)

    props_head._rms.triggered.emit(True)
    assert not props_head.isSectionHidden(PlotProperty.RMS.value)
    props_head._rms.triggered.emit(False)
    assert props_head.isSectionHidden(PlotProperty.RMS.value)

    # PlotProperties tests

    props = pwin.plot_properties
    assert isinstance(props, PlotProperties)

    assert props._signals == ["Cursor position", "sig1", "sig2"]
    for idx, sig in enumerate(props._signals):
        assert props.topLevelItem(idx).text(PlotProperty.Signal.value) == sig
        assert props.topLevelItem(idx).text(PlotProperty.Value.value) == "N/A"
    for idx, sig in enumerate(props._signals[1:], start=1):
        assert props.topLevelItem(idx).text(PlotProperty.Max.value) != "N/A"
        assert props.topLevelItem(idx).text(PlotProperty.Min.value) != "N/A"
        assert props.topLevelItem(idx).text(PlotProperty.RMS.value) != "N/A"

    props.set_property("sig1", PlotProperty.Max, "10.0")
    assert props.topLevelItem(props._signals.index("sig1")).text(
        PlotProperty.Max.value
    ) == "10.0"

    props.set_property("sig1", PlotProperty.Min, "10.0")
    assert props.topLevelItem(props._signals.index("sig1")).text(
        PlotProperty.Min.value
    ) == "10.0"

    props.set_property("sig1", PlotProperty.RMS, "10.0")
    assert props.topLevelItem(props._signals.index("sig1")).text(
        PlotProperty.RMS.value
    ) == "10.0"
