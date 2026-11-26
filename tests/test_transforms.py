"""Tests for diot.transforms: behaviour and the remembering of results."""

import keyword

import pytest

from diot import transforms
from diot.transforms import (
    safe_transform,
    camel_case,
    snake_case,
    upper_case,
    lower_case,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("a,b", "a_b"),
        ("a_,_b", "a__b"),
        ("in", "_in"),
        ("for", "_for"),
        ("", ""),
        ("___", "___"),
        ("a.b.c", "a_b_c"),
        ("...", "_"),
        (".a.", "_a_"),
        ("a..b", "a_b"),
        ("0abc", "_0abc"),
        ("9", "_9"),
        ("123", "_123"),
        ("_x", "_x"),
        ("x_", "x_"),
        ("X_Y", "X_Y"),
        ("MixedCase", "MixedCase"),
        ("with space", "with_space"),
        ("  pad  ", "_pad_"),
        ("a-b", "a_b"),
        ("a/b", "a_b"),
        ("a@b", "a_b"),
        ("name_1", "name_1"),
    ],
)
def test_safe_transform_values(value, expected):
    assert safe_transform(value) == expected


def test_safe_transform_bytes_is_decoded():
    assert safe_transform(b"a,b") == "a_b"
    assert safe_transform(b"in") == "_in"


def test_safe_transform_non_string_is_stringified():
    assert safe_transform(1) == "_1"
    assert safe_transform(2.5) == "_2_5"
    assert safe_transform(None) == "_None"


def test_safe_transform_remembers_but_keeps_types_apart():
    """True == 1 and hash(True) == hash(1), so a bare value key would collide."""
    assert safe_transform(True) == "_True"
    assert safe_transform(1) == "_1"
    # call again to exercise the remembered path for both
    assert safe_transform(True) == "_True"
    assert safe_transform(1) == "_1"
    # bool is not str/bytes, so it is recomputed rather than remembered
    assert safe_transform(True) == "_True"


def test_safe_transform_distinguishes_str_from_bytes():
    assert safe_transform("a,b") == "a_b"
    assert safe_transform(b"a,b") == "a_b"
    # same text, different types: both are correct and must not cross over
    assert safe_transform("in") == "_in"
    assert safe_transform(b"in") == "_in"


def test_safe_transform_repeated_calls_are_stable():
    for _ in range(5):
        assert safe_transform("name_1") == "name_1"
        assert safe_transform("port_2") == "port_2"


def test_safe_transform_cache_flushes_when_full(monkeypatch):
    """A full cache is cleared instead of growing without bound."""
    monkeypatch.setattr(transforms, "_SAFE_CACHE_MAX", 4)
    transforms._SAFE_CACHE.clear()

    for i in range(4):
        assert safe_transform(f"key_{i}") == f"key_{i}"
    assert len(transforms._SAFE_CACHE) == 4

    # the next new key overflows the cache and triggers the flush
    assert safe_transform("key_99") == "key_99"
    assert len(transforms._SAFE_CACHE) == 1

    # everything still works after the flush
    assert safe_transform("key_0") == "key_0"


def test_safe_transform_matches_direct_regex_implementation():
    """The remembered path must agree with a plain recomputation."""
    for value in ["a,b", "in", "0abc", "with space", "name_1", "...", "a..b"]:
        transforms._SAFE_CACHE.clear()
        fresh = transforms._safe_transform(value)
        remembered = safe_transform(value)
        again = safe_transform(value)
        assert fresh == remembered == again


def test_keyword_list_is_honoured():
    for word in keyword.kwlist:
        assert safe_transform(word) == "_" + word


def test_other_transforms_build_on_safe_transform():
    assert camel_case("one_two") == "oneTwo"
    assert camel_case("_one") == "_one"
    assert snake_case("oneTwo") == "one_two"
    assert upper_case("oneTwo") == "ONETWO"
    assert lower_case("ONETWO") == "onetwo"
