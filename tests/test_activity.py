from datetime import datetime, timedelta
from pathlib import Path

from fitmap.activity import Activity, Bounds, TrackPoint


def test_bounds_from_points_and_leaflet_order():
    points = [
        TrackPoint(None, 47.0, 6.0),
        TrackPoint(None, 46.0, 10.0),
    ]

    bounds = Bounds.from_points(points)

    assert bounds == Bounds(min_lat=46.0, min_lon=6.0, max_lat=47.0, max_lon=10.0)
    assert bounds.as_leaflet() == [[46.0, 6.0], [47.0, 10.0]]


def test_activity_elapsed_time_from_points():
    start = datetime(2026, 5, 1, 10, 0)
    activity = Activity(
        path=Path("ride.fit"),
        points=[
            TrackPoint(start, 47.0, 6.0),
            TrackPoint(start + timedelta(minutes=5), 47.1, 6.1),
        ],
    )

    assert activity.display_elapsed_seconds() == 300.0
