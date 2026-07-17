"""Command-line interface for fitmap."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import click

from .filters import build_bounds, filter_activities
from .fit import FitParseError, parse_fit_file
from .render import render_map
from .util import resolve_inputs


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("inputs", nargs=-1, required=True)
@click.option(
    "-o", "--output", type=click.Path(path_type=Path), default=Path("map.html")
)
@click.option(
    "-r", "--recursive", is_flag=True, help="Traverse input directories recursively."
)
@click.option(
    "--after",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Include activities on or after this date.",
)
@click.option(
    "--before",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Include activities before this date.",
)
@click.option("--bbox", help="Bounding box as min-lon,min-lat,max-lon,max-lat.")
@click.option("--min-lat", type=float)
@click.option("--max-lat", type=float)
@click.option("--min-lon", type=float)
@click.option("--max-lon", type=float)
@click.option(
    "--opacity", type=click.FloatRange(0.0, 1.0), default=0.8, show_default=True
)
@click.option("--weight", type=click.IntRange(1, 20), default=3, show_default=True)
@click.option("--verbose", is_flag=True, help="Show parsing warnings and progress.")
def main(
    inputs: tuple[str, ...],
    output: Path,
    recursive: bool,
    after: date | None,
    before: date | None,
    bbox: str | None,
    min_lat: float | None,
    max_lat: float | None,
    min_lon: float | None,
    max_lon: float | None,
    opacity: float,
    weight: int,
    verbose: bool,
) -> None:
    """Generate an interactive HTML map from Garmin FIT files."""

    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    log = logging.getLogger(__name__)

    try:
        bounds = build_bounds(
            bbox=bbox,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    paths = resolve_inputs(inputs, recursive=recursive)
    if not paths:
        raise click.ClickException("no FIT files found")

    activities = []
    for path in paths:
        try:
            log.info("Reading %s", path)
            activities.append(parse_fit_file(path))
        except FitParseError as exc:
            log.warning("%s", exc)

    selected = filter_activities(activities, after=after, before=before, bounds=bounds)
    if not selected:
        raise click.ClickException("no activities matched the requested filters")

    try:
        render_map(selected, output, opacity=opacity, weight=weight)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Wrote {output} with {len(selected)} activities.")


if __name__ == "__main__":
    main()
