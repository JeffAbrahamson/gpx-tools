"""Colour palette helpers."""

from __future__ import annotations

from collections.abc import Iterator

DEFAULT_COLORS = [
    "#2563eb",
    "#dc2626",
    "#16a34a",
    "#ca8a04",
    "#9333ea",
    "#0891b2",
    "#ea580c",
    "#4f46e5",
    "#be123c",
    "#0f766e",
    "#65a30d",
    "#c026d3",
]


def color_for_index(index: int, colors: list[str] | None = None) -> str:
    """Return a stable colour for index, cycling through the palette."""

    palette = DEFAULT_COLORS if colors is None else colors
    if not palette:
        raise ValueError("palette must contain at least one colour")
    return palette[index % len(palette)]


def color_cycle(colors: list[str] | None = None) -> Iterator[str]:
    """Yield colours forever."""

    index = 0
    while True:
        yield color_for_index(index, colors)
        index += 1
