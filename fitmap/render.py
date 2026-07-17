"""Render activities to an interactive HTML map."""

from __future__ import annotations

from html import escape
from pathlib import Path

from .activity import Activity, Bounds
from .palette import color_for_index


def render_map(
    activities: list[Activity],
    output: Path,
    *,
    opacity: float = 0.8,
    weight: int = 3,
    tiles: str = "OpenStreetMap",
) -> None:
    """Write a Folium/Leaflet HTML map for activities."""

    try:
        import folium
    except ImportError as exc:
        raise RuntimeError(
            "folium is required to render maps; install with `pip install folium`"
        ) from exc

    if not activities:
        raise ValueError("no activities to render")

    all_bounds = Bounds.union(
        [bounds for activity in activities if (bounds := activity.bounds) is not None]
    )
    center = _center(all_bounds) if all_bounds else [0.0, 0.0]
    fmap = folium.Map(location=center, zoom_start=12, tiles=tiles)

    for index, activity in enumerate(activities):
        color = color_for_index(index)
        coordinates = [[point.latitude, point.longitude] for point in activity.points]
        if len(coordinates) < 2:
            continue
        feature = folium.FeatureGroup(name=escape(activity.name), show=True)
        folium.PolyLine(
            coordinates,
            color=color,
            weight=weight,
            opacity=opacity,
            popup=folium.Popup(_popup_html(activity), max_width=340),
            tooltip=activity.name,
        ).add_to(feature)
        feature.add_to(fmap)

    if all_bounds is not None:
        fmap.fit_bounds(all_bounds.as_leaflet())
    folium.LayerControl(collapsed=False).add_to(fmap)
    output.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(output))


def _center(bounds: Bounds | None) -> list[float]:
    if bounds is None:
        return [0.0, 0.0]
    return [
        (bounds.min_lat + bounds.max_lat) / 2.0,
        (bounds.min_lon + bounds.max_lon) / 2.0,
    ]


def _popup_html(activity: Activity) -> str:
    rows = [("File", escape(activity.name))]
    if activity.start_time is not None:
        rows.append(
            ("Date", escape(activity.start_time.isoformat(sep=" ", timespec="seconds")))
        )
    distance = activity.display_distance_m()
    if distance is not None:
        rows.append(("Distance", escape(_format_distance(distance))))
    elapsed = activity.display_elapsed_seconds()
    if elapsed is not None:
        rows.append(("Elapsed", escape(_format_duration(elapsed))))

    table_rows = "\n".join(
        f"<tr><th>{escape(label)}</th><td>{value}</td></tr>" for label, value in rows
    )
    return f"<table>{table_rows}</table>"


def _format_distance(meters: float) -> str:
    if meters >= 1000.0:
        return f"{meters / 1000.0:.1f} km"
    return f"{meters:.0f} m"


def _format_duration(seconds: float) -> str:
    seconds_int = int(round(seconds))
    hours, remainder = divmod(seconds_int, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:d}:{secs:02d}"
