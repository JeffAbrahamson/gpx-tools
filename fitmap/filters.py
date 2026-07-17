"""Pure filtering helpers for activities."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, time

from .activity import Activity, Bounds


def filter_activities(
    activities: Iterable[Activity],
    *,
    after: date | datetime | None = None,
    before: date | datetime | None = None,
    bounds: Bounds | None = None,
) -> list[Activity]:
    """Return activities matching all supplied filters."""

    return [
        activity
        for activity in activities
        if matches_date_range(activity, after=after, before=before)
        and matches_bounds(activity, bounds)
    ]


def matches_date_range(
    activity: Activity,
    *,
    after: date | datetime | None = None,
    before: date | datetime | None = None,
) -> bool:
    """Return true if activity starts within the requested half-open range."""

    if after is None and before is None:
        return True
    if activity.start_time is None:
        return False

    start = activity.start_time
    if after is not None and start < _as_datetime(after, end_of_day=False):
        return False
    if before is not None and start >= _as_datetime(before, end_of_day=False):
        return False
    return True


def matches_bounds(activity: Activity, bounds: Bounds | None) -> bool:
    """Return true if any activity point intersects bounds."""

    if bounds is None:
        return True
    return bounds.intersects_activity(activity)


def parse_bbox(value: str) -> Bounds:
    """Parse min-lon,min-lat,max-lon,max-lat into Bounds."""

    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        raise ValueError("--bbox must be min-lon,min-lat,max-lon,max-lat")
    try:
        min_lon, min_lat, max_lon, max_lat = (float(part) for part in parts)
    except ValueError as exc:
        raise ValueError("--bbox values must be numbers") from exc
    return Bounds(min_lat=min_lat, min_lon=min_lon, max_lat=max_lat, max_lon=max_lon)


def build_bounds(
    *,
    bbox: str | None = None,
    min_lat: float | None = None,
    max_lat: float | None = None,
    min_lon: float | None = None,
    max_lon: float | None = None,
) -> Bounds | None:
    """Build Bounds from either --bbox or individual coordinate limits."""

    if bbox and any(
        value is not None for value in (min_lat, max_lat, min_lon, max_lon)
    ):
        raise ValueError("use either --bbox or individual min/max coordinate options")
    if bbox:
        return parse_bbox(bbox)
    values = (min_lat, max_lat, min_lon, max_lon)
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise ValueError(
            "min-lat, max-lat, min-lon, and max-lon must be supplied together"
        )
    assert min_lat is not None
    assert max_lat is not None
    assert min_lon is not None
    assert max_lon is not None
    return Bounds(min_lat=min_lat, min_lon=min_lon, max_lat=max_lat, max_lon=max_lon)


def _as_datetime(value: date | datetime, *, end_of_day: bool) -> datetime:
    if isinstance(value, datetime):
        return value
    if end_of_day:
        return datetime.combine(value, time.max)
    return datetime.combine(value, time.min)
