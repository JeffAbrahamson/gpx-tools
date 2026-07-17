from datetime import datetime
from pathlib import Path

import pytest

from fitmap.activity import Activity, Bounds, TrackPoint
from fitmap.filters import build_bounds, filter_activities, parse_bbox


def activity(start_time=None, points=None):
    return Activity(
        path=Path("ride.fit"),
        points=points or [TrackPoint(None, 47.0, 7.0)],
        start_time=start_time,
    )


def test_bbox_uses_lon_lat_order():
    assert parse_bbox("6,45,10,48") == Bounds(
        min_lat=45.0,
        min_lon=6.0,
        max_lat=48.0,
        max_lon=10.0,
    )


def test_build_bounds_requires_complete_coordinate_set():
    with pytest.raises(ValueError):
        build_bounds(min_lon=6.0, max_lon=10.0)


def test_filter_activities_matches_half_open_date_range():
    activities = [
        activity(datetime(2026, 4, 30, 23, 59)),
        activity(datetime(2026, 5, 1, 0, 0)),
        activity(datetime(2026, 6, 1, 0, 0)),
    ]

    selected = filter_activities(
        activities,
        after=datetime(2026, 5, 1),
        before=datetime(2026, 6, 1),
    )

    assert selected == [activities[1]]


def test_filter_activities_includes_any_point_in_bounds():
    outside_then_inside = activity(
        points=[
            TrackPoint(None, 44.0, 4.0),
            TrackPoint(None, 46.0, 7.0),
        ]
    )

    selected = filter_activities(
        [outside_then_inside],
        bounds=Bounds(min_lat=45.0, min_lon=6.0, max_lat=48.0, max_lon=10.0),
    )

    assert selected == [outside_then_inside]
