""" Fixtures for unit-tests """

import os

import pytest
import pandas as pd

@pytest.fixture
def setup_plot_list():
    """
    Setup plot set of 3 Dataframes (with one empty)
    """
    return [
        [],
        [pd.DataFrame({
            "timestamp": [0, 2, 4],
            "sig1":      [0, 2, 4]
        })],
        [pd.DataFrame({
            "timestamp": [1, 5, 3],
            "sig2":      [0, 4, 2]
        })]
    ]

@pytest.fixture
def setup_plot_df():
    """
    Setup Dataframe with some 1 signal
    """
    return pd.DataFrame({
        "timestamp": [0,  1,  2,  3,  4,  5,  6,  7],
        "sig1":      [0,  1,  2,  1,  0, -1, -2, -1]
    })

@pytest.fixture
def setup_simple_csv_file(tmp_path):
    """
    Generate temporary .csv file with some signal data
    """
    path = str(tmp_path / "test_simple_csv.csv")
    pd.DataFrame({
        "timestamp": [0,  1,  2,  3,  4,  5,  6,  7],
        "sig1":      [0,  1,  2,  1,  0, -1, -2, -1]
    }).to_csv(path, sep=";", index=False)
    yield path
    os.remove(path)
