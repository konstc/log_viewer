""" Filtering of signal names by a user query """

import re
from collections.abc import Callable
from fnmatch import translate

GLOB_CHARS = ("*", "?")

def compile_filter(query: str) -> Callable[[str], bool]:
    """
    Parses 'query' once and returns a predicate telling whether a signal name
    matches it. Matching is case-insensitive; the query is split by
    whitespace into words, and a name matches when it matches every word.
    A word containing '*' or '?' is a glob mask (fnmatch) over the whole
    name, any other word is a substring of the name. An empty query matches
    any name.
    """
    substrings = []
    globs = []
    for word in query.casefold().split():
        if any(char in word for char in GLOB_CHARS):
            globs.append(re.compile(translate(word)).match)
        else:
            substrings.append(word)

    def matches(name: str) -> bool:
        folded = name.casefold()
        return all(word in folded for word in substrings) and \
               all(glob(folded) for glob in globs)

    return matches

def match_filter(name: str, query: str) -> bool:
    """
    Returns True when signal name 'name' matches filter 'query'
    """
    return compile_filter(query)(name)
