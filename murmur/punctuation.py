"""
Converts spoken punctuation words into their characters.
Applied after transcription, before AI cleanup.
Longer phrases are matched first to avoid partial clobbers.
"""
import re

# (spoken phrase, replacement) — order: longest first
_MAP = [
    ("new paragraph",     "\n\n"),
    ("new line",          "\n"),
    ("open quote",        "\u201c"),
    ("close quote",       "\u201d"),
    ("open parenthesis",  "("),
    ("close parenthesis", ")"),
    ("left parenthesis",  "("),
    ("right parenthesis", ")"),
    ("open paren",        "("),
    ("close paren",       ")"),
    ("open bracket",      "["),
    ("close bracket",     "]"),
    ("open brace",        "{"),
    ("close brace",       "}"),
    ("exclamation point", "!"),
    ("question mark",     "?"),
    ("ellipsis",          "\u2026"),
    ("semicolon",         ";"),
    ("colon",             ":"),
    ("comma",             ","),
    ("period",            "."),
    ("em dash",           "\u2014"),
    ("dash",              "\u2014"),
    ("hyphen",            "-"),
    ("at symbol",         "@"),
    ("at sign",           "@"),
    ("hashtag",           "#"),
    ("percent",           "%"),
    ("ampersand",         "&"),
    ("asterisk",          "*"),
    ("slash",             "/"),
    ("backslash",         "\\"),
    ("equals",            "="),
    ("plus",              "+"),
    ("tilde",             "~"),
    ("caret",             "^"),
]

_COMPILED = [
    (re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE), char)
    for phrase, char in _MAP
]


def apply(text: str) -> str:
    for pattern, char in _COMPILED:
        text = pattern.sub(lambda m: char, text)
    return text
