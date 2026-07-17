"""Core data model for parsed activities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path


@dataclass(frozen=True)
class TrackPoint:
    """A single GPS point from an activity."""

    timestamp: datetime | None
    latitude: float
    longitude: float
    elevation: float | None = None
    heart_rate: int | None = None
    cadence: int | None = None
    power: int | None = None
    speed: float | None = None
    distance: float | None = None


@dataclass(frozen=True)
class Bounds:
    """Geographic bounds in decimal degrees."""

    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float

    def contains(self, point: TrackPoint) -> bool:
        """Return true if point lies inside this bounds object."""

        return (
            self.min_lat <= point.latitude <= self.max_lat
            and self.min_lon <= point.longitude <= self.max_lon
        )

    def intersects_activity(self, activity: "Activity") -> bool:
        """Return true if any activity point lies within these bounds."""

        return any(self.contains(point) for point in activity.points)

    def as_leaflet(self) -> list[list[float]]:
        """Return bounds in Leaflet's [[south, west], [north, east]] form."""

        return [[self.min_lat, self.min_lon], [self.max_lat, self.max_lon]]

    @classmethod
    def from_points(cls, points: list[TrackPoint]) -> "Bounds | None":
        """Build bounds for a non-empty point list."""

        if not points:
            return None
        return cls(
            min_lat=min(point.latitude for point in points),
            min_lon=min(point.longitude for point in points),
            max_lat=max(point.latitude for point in points),
            max_lon=max(point.longitude for point in points),
        )

    @classmethod
    def union(cls, bounds: list["Bounds"]) -> "Bounds | None":
        """Return the smallest bounds containing all provided bounds."""

        if not bounds:
            return None
        return cls(
            min_lat=min(bound.min_lat for bound in bounds),
            min_lon=min(bound.min_lon for bound in bounds),
            max_lat=max(bound.max_lat for bound in bounds),
            max_lon=max(bound.max_lon for bound in bounds),
        )


@dataclass(frozen=True)
class Activity:
    """A parsed FIT activity ready for filtering or rendering."""

    path: Path
    points: list[TrackPoint]
    start_time: datetime | None = None
    distance: float | None = None
    elapsed_time: float | None = None

    @property
    def name(self) -> str:
        """Return a user-facing activity name."""

        return self.path.name

    @property
    def bounds(self) -> Bounds | None:
        """Return geographic bounds for the activity."""

        return Bounds.from_points(self.points)

    def display_distance_m(self) -> float | None:
        """Return best available distance in meters."""

        if self.distance is not None:
            return self.distance
        point_distances = [
            point.distance for point in self.points if point.distance is not None
        ]
        if point_distances:
            return max(point_distances)
        if len(self.points) < 2:
            return None
        return sum(
            haversine_meters(
                prev.latitude, prev.longitude, point.latitude, point.longitude
            )
            for prev, point in zip(self.points, self.points[1:])
        )

    def display_elapsed_seconds(self) -> float | None:
        """Return best available elapsed duration in seconds."""

        if self.elapsed_time is not None:
            return self.elapsed_time
        timestamps = [point.timestamp for point in self.points if point.timestamp]
        if len(timestamps) < 2:
            return None
        return (max(timestamps) - min(timestamps)).total_seconds()


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance between two WGS84 coordinates."""

    earth_radius_m = 6_371_000.0
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)

    a = sin(delta_phi / 2.0) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2.0) ** 2
    c = 2.0 * atan2(sqrt(a), sqrt(1.0 - a))
    return earth_radius_m * c
