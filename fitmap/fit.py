"""FIT parsing."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .activity import Activity, TrackPoint

LOG = logging.getLogger(__name__)
SEMICIRCLES_TO_DEGREES = 180.0 / 2**31


class FitParseError(RuntimeError):
    """Raised when a FIT file cannot be parsed into an activity."""


def parse_fit_file(path: Path) -> Activity:
    """Parse one FIT file and return an Activity.

    Only record and session messages are read. Files without GPS points raise
    FitParseError so callers can warn and continue.
    """

    try:
        import fitdecode
    except ImportError as exc:
        raise FitParseError(
            "fitdecode is required to read FIT files; install with `pip install fitdecode`"
        ) from exc

    points: list[TrackPoint] = []
    start_time: datetime | None = None
    distance: float | None = None
    elapsed_time: float | None = None

    try:
        with fitdecode.FitReader(path) as fit:
            for frame in fit:
                if not isinstance(frame, fitdecode.FitDataMessage):
                    continue
                if frame.name == "record":
                    point = parse_record_message(frame)
                    if point is not None:
                        if start_time is None and point.timestamp is not None:
                            start_time = point.timestamp
                        points.append(point)
                elif frame.name == "session":
                    start_time = _coalesce(
                        _message_value(frame, "start_time"),
                        start_time,
                    )
                    distance = _coalesce(
                        _message_value(frame, "total_distance"),
                        distance,
                    )
                    elapsed_time = _coalesce(
                        _message_value(frame, "total_elapsed_time"),
                        elapsed_time,
                    )
    except Exception as exc:  # FIT files in the wild can fail in many ways.
        raise FitParseError(f"{path}: {exc}") from exc

    if not points:
        raise FitParseError(f"{path}: no GPS record points found")

    return Activity(
        path=path,
        points=points,
        start_time=start_time,
        distance=_as_float(distance),
        elapsed_time=_as_float(elapsed_time),
    )


def parse_record_message(message: Any) -> TrackPoint | None:
    """Parse a FIT record message into a TrackPoint, or None if GPS is absent."""

    raw_lat = _message_value(message, "position_lat")
    raw_lon = _message_value(message, "position_long")
    if raw_lat is None or raw_lon is None:
        return None

    return TrackPoint(
        timestamp=_message_value(message, "timestamp"),
        latitude=_coordinate_to_degrees(raw_lat),
        longitude=_coordinate_to_degrees(raw_lon),
        elevation=_as_float(_message_value(message, "enhanced_altitude", "altitude")),
        heart_rate=_as_int(_message_value(message, "heart_rate")),
        cadence=_as_int(_message_value(message, "cadence")),
        power=_as_int(_message_value(message, "power")),
        speed=_as_float(_message_value(message, "enhanced_speed", "speed")),
        distance=_as_float(_message_value(message, "distance")),
    )


def _message_value(message: Any, *names: str) -> Any:
    for name in names:
        try:
            value = message.get_value(name)
        except (AttributeError, KeyError, TypeError, ValueError):
            value = None
        if value is not None:
            return value
    return None


def _coordinate_to_degrees(value: Any) -> float:
    number = float(value)
    if -180.0 <= number <= 180.0:
        return number
    return number * SEMICIRCLES_TO_DEGREES


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coalesce(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None
