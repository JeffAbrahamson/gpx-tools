# gpx-tools

Small local tools for activity data.

## fitmap

`fitmap` generates an interactive HTML map from Garmin FIT activity files.

Install the package in editable mode:

```bash
python -m pip install -e ".[dev]"
```

Then run:

```bash
fitmap rides/*.fit
```

or:

```bash
fitmap rides --recursive --output rides.html
```

Useful filters:

```bash
fitmap rides \
  --recursive \
  --after 2026-05-01 \
  --before 2026-06-01 \
  --bbox 6,45,10,48 \
  --output may-switzerland.html
```

The output HTML can be opened directly in a browser. Map tiles are loaded from
OpenStreetMap while viewing.

### Options

* `--recursive` traverses directory inputs recursively.
* `--after YYYY-MM-DD` includes activities starting on or after the date.
* `--before YYYY-MM-DD` includes activities before the date.
* `--bbox min-lon,min-lat,max-lon,max-lat` filters by geographic intersection.
* `--min-lat`, `--max-lat`, `--min-lon`, `--max-lon` are an alternative to
  `--bbox`.
* `--opacity` controls track opacity.
* `--weight` controls track width.
* `--verbose` shows parsing progress and warnings.

## Development

Run tests with:

```bash
python -m pytest
```
