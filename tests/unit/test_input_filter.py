"""Screening of /match inputs, before anything is embedded."""

import pytest

from app.services.matching.input_filter import screen_inputs

_LONG = "Machine learning algorithms for quantum computing simulations"


def _screen(ids, texts, min_length=25):
    return screen_inputs(ids, texts, min_input_length=min_length)


def test_accepts_a_long_enough_text():
    screened = _screen(["d1"], [_LONG])

    assert screened.ids == ["d1"]
    assert screened.texts == [_LONG]
    assert screened.skipped_ids == []


def test_skips_a_text_below_the_minimum_length():
    screened = _screen(["d1"], ["Quantum"])

    assert screened.ids == []
    assert screened.skipped_ids == ["d1"]


def test_length_is_measured_on_the_stripped_text():
    """Padding must not make a short input look long enough to match."""
    screened = _screen(["d1"], ["Quantum" + " " * 50])

    assert screened.skipped_ids == ["d1"]


def test_screening_is_per_input_and_preserves_order():
    screened = _screen(
        ["keep-1", "short", "keep-2"],
        [_LONG, "tiny", _LONG],
    )

    assert screened.ids == ["keep-1", "keep-2"]
    assert screened.texts == [_LONG, _LONG]
    assert screened.skipped_ids == ["short"]


@pytest.mark.parametrize("min_length", [0, 1])
def test_a_zero_or_one_minimum_keeps_any_non_empty_text(min_length):
    """Disabling the length rule must not accidentally drop valid short inputs."""
    screened = _screen(["d1"], ["AI"], min_length=min_length)

    assert screened.ids == ["d1"]
