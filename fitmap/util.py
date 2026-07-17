"""Utility helpers for CLI input resolution."""

from __future__ import annotations

from glob import glob
from pathlib import Path


def resolve_inputs(inputs: tuple[str, ...], *, recursive: bool) -> list[Path]:
    """Resolve files, directories, and shell-style glob patterns to FIT files."""

    paths: list[Path] = []
    for raw in inputs:
        matches = [Path(match) for match in glob(raw, recursive=True)]
        if matches:
            for match in matches:
                paths.extend(_expand_path(match, recursive=recursive))
            continue
        paths.extend(_expand_path(Path(raw), recursive=recursive))

    unique: dict[Path, None] = {}
    for path in paths:
        if path.suffix.lower() == ".fit":
            unique[path.resolve()] = None
    return sorted(unique)


def _expand_path(path: Path, *, recursive: bool) -> list[Path]:
    if path.is_dir():
        pattern = "**/*.fit" if recursive else "*.fit"
        return list(path.glob(pattern))
    if path.is_file():
        return [path]
    return []
