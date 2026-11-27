""" Unit-tests for signal_filter.py module entities """

import pytest

# modules under test
from signal_filter import compile_filter, match_filter

NAME = "CAN0.SA0.PDU2.GE0.EEC1.EngineSpeed"
NAME_NO_CAN = "SA0.PDU2.GE0.EEC1.EngineSpeed"

@pytest.mark.parametrize("query", ["", " ", "  \t "])
def test_empty_query(query):
    """
    Unit-tests for an empty query: any name matches
    """
    assert match_filter(NAME, query)
    assert match_filter("", query)

@pytest.mark.parametrize("query, expected", [
    ("EngineSpeed", True),
    ("gineSp", True),
    ("CAN0", True),
    ("EngineTorque", False),
    ("EEC2", False),
])
def test_substring(query, expected):
    """
    Unit-tests for a single word: a substring of the name
    """
    assert match_filter(NAME, query) is expected

@pytest.mark.parametrize("query", ["enginespeed", "ENGINESPEED", "eNgInEsPeEd",
                                   "eec1", "can0.sa0"])
def test_case_insensitive(query):
    """
    Unit-tests for case insensitivity of both the query and the name
    """
    assert match_filter(NAME, query)
    assert match_filter(NAME.lower(), query)

@pytest.mark.parametrize("query, expected", [
    ("eec1 speed", True),
    ("speed eec1", True),
    ("  eec1 \t speed  ", True),
    ("sa0 pdu2 ge0 eec1 speed", True),
    ("eec1 torque", False),
    ("torque eec1", False),
])
def test_several_words(query, expected):
    """
    Unit-tests for several words: all of them must match, in any order
    """
    assert match_filter(NAME, query) is expected

@pytest.mark.parametrize("name, query, expected", [
    # the mask covers the whole name
    (NAME_NO_CAN, "SA0.*.EEC1.*", True),
    (NAME, "SA0.*.EEC1.*", False),
    (NAME, "*SA0.*.EEC1.*", True),
    (NAME, "*.eec1.*", True),
    (NAME, "*.EEC1", False),
    (NAME, "*speed", True),
    (NAME, "*", True),
    # '?' is exactly one character
    (NAME, "can?.sa0.*", True),
    (NAME, "can?.sa?.*", True),
    (NAME, "can??.*", False),
    # a mask is combined with the other words
    (NAME, "*.eec1.* speed", True),
    (NAME, "*.eec1.* torque", False),
    (NAME, "can0.* *.et1.*", False),
])
def test_glob(name, query, expected):
    """
    Unit-tests for words with '*' or '?': a glob mask over the whole name
    """
    assert match_filter(name, query) is expected

@pytest.mark.parametrize("name, query, expected", [
    # a dot in a word is a dot, not "any character"
    (NAME, "sa0.pdu2", True),
    (NAME, "ge0.eec1.", True),
    ("CAN0xSA0", "can0.sa0", False),
    ("CAN0xSA0xPDU2", "can0.sa0*", False),
    ("CAN0.SA0.PDU2", "can0.sa0*", True),
    # other characters special for regular expressions
    ("Msg.Sig(1)+[2]", "sig(1)+[2]", True),
    ("Msg.Sig$^|1", "sig$^|1", True),
    ("Msg.Sig1", "sig(1)", False),
])
def test_special_characters(name, query, expected):
    """
    Unit-tests for characters special for regular expressions in the name
    and in the query
    """
    assert match_filter(name, query) is expected

def test_compile_filter():
    """
    Unit-tests for compile_filter(): the predicate is reused for many names
    """
    names = [NAME,
             "CAN0.SA0.PDU2.GE0.EEC1.EngineTorque",
             "CAN0.SA3.PDU2.GE0.EEC1.EngineSpeed",
             "CAN0.SA0.PDU2.GE0.ET1.CoolantTemp"]
    matches = compile_filter("*.sa0.* eec1")
    assert [name for name in names if matches(name)] == names[:2]
    assert [name for name in names if compile_filter("")(name)] == names
