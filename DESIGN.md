# fitmap design

## Purpose

`fitmap` is a command-line utility for visualising collections of Garmin FIT
activities on one interactive map. Its main job is exploration: finding where
activities happened, overlaying related rides, and producing a local HTML file
that can be opened without a server.

It is not a training analysis package and does not try to replace Garmin
Connect, Strava, or Golden Cheetah.

## Initial goals

The first implementation supports:

* direct FIT parsing with `fitdecode`
* file, glob, and directory inputs
* optional recursive directory traversal
* date filtering with `--after` and `--before`
* geographic filtering with `--bbox` or individual min/max coordinates
* one coloured Leaflet layer per activity
* automatic map bounds
* popup metadata for filename, date, distance, and elapsed time
* robust handling of bad or GPS-less FIT files

The default output is `map.html`.

## Architecture

The package is split by responsibility:

* `fitmap.activity` contains dataclasses for `Activity`, `TrackPoint`, and
  `Bounds`.
* `fitmap.fit` reads FIT files and returns the model objects. It has no map or
  CLI knowledge.
* `fitmap.filters` contains pure filtering functions. It does no I/O.
* `fitmap.palette` assigns stable colours to activity indexes.
* `fitmap.render` turns activities into a Folium HTML map. It has no FIT
  decoding knowledge.
* `fitmap.util` resolves CLI input paths, directories, and glob patterns.
* `fitmap.cli` wires the pieces together with Click.

This keeps future additions such as GeoJSON export, GPX export, heatmaps, and
caching from becoming entangled with FIT parsing or command-line handling.

## Data model

`TrackPoint` stores timestamp, latitude, longitude, and optional sensor data
when present in the FIT record message:

* elevation
* heart rate
* cadence
* power
* speed
* cumulative distance

`Activity` stores the source path, points, optional start time, optional total
distance, and optional elapsed time. If FIT session totals are missing, display
distance and elapsed time can be derived from record data.

`Bounds` stores min/max latitude and longitude and provides helpers for point
containment, activity intersection, union, and Leaflet ordering.

## FIT parsing choices

Only `record` and `session` messages are read initially. Record messages provide
GPS points and optional point-level sensor data. Session messages provide
summary metadata for popup display.

FIT coordinates are commonly stored as semicircles, so coordinates outside the
normal decimal-degree range are converted to WGS84 decimal degrees.

Files without usable GPS points are rejected for mapping, but the CLI logs a
warning and continues.

## Filtering semantics

Date filtering uses a half-open interval:

* `--after 2026-05-01` includes activities starting at or after midnight on
  2026-05-01.
* `--before 2026-06-01` excludes activities starting at or after midnight on
  2026-06-01.

Bounding-box filtering includes an activity if any point intersects the box.
The `--bbox` option uses the common GIS order:

```text
min-lon,min-lat,max-lon,max-lat
```

## Performance

The first implementation keeps the algorithm linear in the number of input
points. It does not do pairwise activity comparisons and does not require a GIS
stack.

For around 1000 normal activities this should be dominated by FIT decoding and
browser rendering time. Very large datasets will eventually need track
simplification and caching.

## Future functionality

Likely next features:

* `--heatmap` using all GPS points
* colour modes such as year, month, speed, elevation, or activity type
* start and finish markers
* richer popup metadata: average speed, moving time, elevation gain, calories,
  temperature, and bike name
* summary sidebar with total activities, distance, and time
* filename or activity-name search
* GPX export for selected activities
* GeoJSON export
* additional basemaps
* Douglas-Peucker track simplification for browser performance
* parsed FIT cache keyed by path, size, and modification time
* static raster output for reports

Long term, the boundaries between parsing, filtering, and rendering make it
possible to add plugins or alternate renderers without rewriting the core.

