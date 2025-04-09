""" Unit-tests for plotter_utils.py entities """

import numpy as np
import pandas as pd

# modules under test
from plotter import prepare_merged_plot, get_plot_minmax, get_plot_rms

def test_prepare_merged_plot(setup_plot_list):
    """
    Unit-test for prepare_merged_plot() function

    Step 0: call test_prepare_merged_plot with setup_plot_list fixture
    Step 1: check that returned Dataframe has expected size & columns
    Step 2: check that data in "timestamp" column is sorted
    Step 3: check that NaN values are interpolated
    Step 4: check that return Dataframe is empty on empty input
    """
    merged_df = prepare_merged_plot(setup_plot_list)

    # Check merged_df size
    assert len(merged_df.columns) == 3
    assert len(merged_df.index) == 6
    assert merged_df.columns[0] == "timestamp"
    assert merged_df.columns[1] == "sig1"
    assert merged_df.columns[2] == "sig2"

    # Check "timestamp" for monotonic
    for i in range(1, 6):
        assert merged_df.iloc[i, 0] > merged_df.iloc[i - 1, 0]

    # Check "sig1" for interpolation
    assert merged_df.iloc[1, 1] == 1
    assert merged_df.iloc[3, 1] == 3

    # Check "sig2" for interpolation
    assert np.isnan(merged_df.iloc[0, 2])
    assert merged_df.iloc[2, 2] == 1
    assert merged_df.iloc[4, 2] == 3

    # Check for empty input
    assert prepare_merged_plot([]).empty

def test_get_plot_minmax(setup_plot_df):
    """
    Unit-test for get_plot_minmax() function

    Step 0: check that returned min, max are as expected for column "sig1" of
        setup_plot_df fixture
    Step 1: check that returned min, max are "N/A" for column "sig2" of
        setup_plot_df fixture
    Step 2: check that returned min, max are "N/A" for some empty input
        Dataframe
    """
    pmax, pmin = get_plot_minmax(setup_plot_df, "sig1")
    assert pmax == "2"
    assert pmin == "-2"

    pmax, pmin = get_plot_minmax(setup_plot_df, "sig2")
    assert pmax == "N/A"
    assert pmin == "N/A"

    pmax, pmin = get_plot_minmax(pd.DataFrame({}), "sig1")
    assert pmax == "N/A"
    assert pmin == "N/A"

def test_get_plot_rms(setup_plot_df):
    """
    Unit test for get_plot_rms() function

    Step 0: check that rms is as expected for column "sig1" of setup_plot_df
        fixture
    Step 1: check that rms is "N/A" for column "sig2" of setup_plot_df fixture
    Step 2: check that rms is "N/A" for some empty input Dataframe
    """
    rms = get_plot_rms(setup_plot_df, "sig1")
    assert rms == str(np.sqrt(1.5))

    rms = get_plot_rms(setup_plot_df, "sig2")
    assert rms == "N/A"

    rms = get_plot_rms(pd.DataFrame({}), "sig1")
    assert rms == "N/A"
