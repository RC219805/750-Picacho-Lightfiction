"""Generate a JSON manifest for the legacy processing pipeline.

The script inspects an input directory, discovers image files and writes a
``manifest.json`` file compatible with :func:`src.main.load_manifest`.  It is
primarily intended to provide a quick starting point when working with the
legacy JSON workflow so that a basic manifest can be created without manual
editing.

Usage
-----

    python3 tools/generate_manifest.py --input-dir data/new_input

By default a ``manifest.json`` file will be written alongside the input
images.  Existing manifest entries are preserved unless ``--overwrite`` is
specified.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
DEFAULT_SUFFIX = "_processed"


def discover_images(input_dir: Path) -> List[Path]:
    """Return a sorted list of image files contained in ``input_dir``."""

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    files: List[Path] = [
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(files)


def load_existing_manifest(manifest_path: Path) -> List[Dict]:
    """Load manifest entries from ``manifest_path`` if it exists."""

    if not manifest_path.exists():
        return []

    try:
        with manifest_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Manifest at {manifest_path} is not valid JSON: {exc.msg}"
        ) from exc

    if isinstance(data, dict):
        entries = data.get("images", [])
    elif isinstance(data, list):
        entries = data
    else:
        raise ValueError(
            f"Unsupported manifest structure in {manifest_path}: {type(data).__name__}"
        )

    if not isinstance(entries, list):
        raise ValueError(
            f"Manifest at {manifest_path} must contain a list of entries."
        )

    return [entry for entry in entries if isinstance(entry, dict)]


def merge_entries(
    discovered: Iterable[Path],
    existing_entries: List[Dict],
    *,
    relative_to: Path,
    overwrite: bool,
) -> List[Dict]:
    """Combine ``discovered`` files with ``existing_entries``."""

    result: Dict[str, Dict] = {}

    for entry in existing_entries:
        key = entry.get("file") or entry.get("input")
        if not isinstance(key, str):
            continue
        result[key] = dict(entry)

    for path in discovered:
        rel_name = path.relative_to(relative_to).as_posix()
        default_output = f"{path.stem}{DEFAULT_SUFFIX}{path.suffix}"
        entry = {
            "file": rel_name,
            "output": default_output,
        }

        if overwrite or rel_name not in result:
            result[rel_name] = entry

    return [result[key] for key in sorted(result)]


def write_manifest(manifest_path: Path, entries: List[Dict]) -> None:
    """Persist ``entries`` to ``manifest_path`` as JSON."""

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump({"images": entries}, handle, indent=2)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/new_input"),
        help="Directory containing source renders that should be enumerated.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to the manifest file that should be generated. Defaults to"
        " <input-dir>/manifest.json.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing manifest entries instead of preserving them.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_dir = args.input_dir
    manifest_path = args.manifest or (input_dir / "manifest.json")

    try:
        discovered = discover_images(input_dir)
    except FileNotFoundError as exc:
        print(exc)
        return 1

    try:
        existing = load_existing_manifest(manifest_path)
    except ValueError as exc:
        print(exc)
        return 1

    entries = merge_entries(
        discovered,
        existing,
        relative_to=input_dir,
        overwrite=args.overwrite,
    )

    write_manifest(manifest_path, entries)

    if entries:
        print(
            f"Wrote {len(entries)} entr{'y' if len(entries) == 1 else 'ies'} "
            f"to {manifest_path}."
        )
    else:
        print(f"No images found in {input_dir}. Wrote an empty manifest to {manifest_path}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
