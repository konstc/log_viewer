""" Common fixtures for all types of tests """

import os

import pytest
import pandas as pd

@pytest.fixture
def setup_plot_item_list():
    """
    Generate list with some signal names
    """
    return ["sig1", "sig2", "sig3"]

@pytest.fixture
def setup_j1939_dump_file(tmp_path):
    """
    Generate temporary .csv file with some J1939 dump data
    """
    path = str(tmp_path / "test_j1939_dump.csv")
    pd.DataFrame({
        "timestamp":      list(range(0, 20000)),
        "arbitration_id": ["0xdf00064", "0x55064f9"] * 10000,
        "extended":       [1] * 20000,
        "remote":         [0] * 20000,
        "error":          [0] * 20000,
        "dlc":            [2] * 20000,
        "data":           ["AAAAAAAAAAA="] * 20000
    }).to_csv(path, index=False)
    yield path
    os.remove(path)
