import pytest

from fitmap.palette import color_for_index


def test_color_for_index_cycles():
    colors = ["red", "green"]

    assert color_for_index(0, colors) == "red"
    assert color_for_index(1, colors) == "green"
    assert color_for_index(2, colors) == "red"


def test_color_for_index_rejects_empty_palette():
    with pytest.raises(ValueError):
        color_for_index(0, [])
