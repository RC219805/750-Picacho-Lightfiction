"""CLI entry point that drives the rendering pipeline via a YAML manifest."""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List

import yaml

# Add src directory to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__)))

from config import (
    ASPECT_RATIO_PRESETS,
    DEFAULT_MANIFEST_PATH,
    INPUT_DIR,
    OUTPUT_DIR,
)
from processing import process_variant


def _coerce_path(path_str: str, base: Path) -> Path:
    """Return ``path_str`` as a :class:`~pathlib.Path` relative to ``base``."""

    path = Path(path_str)
    if not path.is_absolute():
        path = base / path
    return path


def load_manifest(manifest_path: Path) -> Dict:
    """Load and validate the YAML manifest located at ``manifest_path``."""

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    renders = data.get("renders")
    if not isinstance(renders, list) or not renders:
        raise ValueError("Manifest must define a non-empty 'renders' list.")

    return data


def iterate_tasks(
    manifest: Dict,
    input_dir: Path,
    output_dir: Path,
) -> Iterable[Dict]:
    """Yield processing tasks described by ``manifest``."""

    for render in manifest.get("renders", []):
        source = render.get("source")
        if not source:
            raise ValueError("Each render entry requires a 'source' value.")

        source_path = _coerce_path(source, input_dir)
        variants = render.get("variants") or []

        if not variants:
            raise ValueError(f"Render '{source}' defines no variants.")

        for variant in variants:
            filename = variant.get("filename") or variant.get("name")
            if not filename:
                raise ValueError(
                    f"Variant for '{source}' must include a 'filename'."
                )

            operations: List[Dict] = variant.get("operations") or []
            output_subdir = variant.get("directory")

            if output_subdir:
                target_dir = _coerce_path(output_subdir, output_dir)
            else:
                target_dir = output_dir

            yield {
                "source": source_path,
                "output": target_dir / filename,
                "operations": operations,
            }


def main(argv: List[str] | None = None) -> int:
    """Entry point used by both the CLI and tests."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Path to the YAML manifest that describes processing tasks.",
    )
    parser.add_argument(
        "--input-dir",
        default=str(INPUT_DIR),
        help="Base directory used to resolve relative source paths.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory where processed variants are written.",
    )

    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    try:
        manifest = load_manifest(manifest_path)
    except (OSError, ValueError) as exc:
        print(f"Error loading manifest: {exc}")
        return 1

    os.makedirs(output_dir, exist_ok=True)

    tasks = list(iterate_tasks(manifest, input_dir, output_dir))
    print(f"Loaded {len(tasks)} variant task(s) from {manifest_path}.")

    processed = 0
    failed = 0

    for task in tasks:
        source = task["source"]
        output_path = task["output"]
        operations = task["operations"]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Processing {source.name} -> {output_path.name}...")

        success = process_variant(
            str(source),
            str(output_path),
            operations,
            presets=ASPECT_RATIO_PRESETS,
        )

        if success:
            processed += 1
            print(f"  ✓ Saved to {output_path}")
        else:
            failed += 1
            print(f"  ✗ Failed to process {source}")

    print(
        f"Completed processing: {processed} succeeded, {failed} failed."
    )

    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
