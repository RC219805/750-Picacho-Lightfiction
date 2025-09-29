"""
Main pipeline for processing architectural renderings.
Iterates through images in the input directory, applies processing,
and saves results to the output directory.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

# Add src directory to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__)))

from processing import process_image
from config import INPUT_DIR, OUTPUT_DIR, DCI_4K_RESOLUTION


def get_image_files(directory):
    """
    Get list of image files from the specified directory.
    
    Args:
        directory (str): Directory path to scan for images
        
    Returns:
        list: List of image file paths
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    image_files = []
    
    if not os.path.exists(directory):
        print(f"Input directory '{directory}' does not exist.")
        return image_files
    
    for file in os.listdir(directory):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(os.path.join(directory, file))

    return sorted(image_files)


def _parse_mired_value(value) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        clean = value.strip().lower()
        if clean.endswith("_mireds"):
            clean = clean[: -len("_mireds")]
        try:
            return float(clean)
        except ValueError:
            return None

    return None


def _parse_crop(entry: Dict) -> Optional[Tuple[int, int, int, int]]:
    crop = entry.get("crop") or entry.get("crop_box")
    if crop is None:
        return None

    if isinstance(crop, dict):
        keys = ["left", "top", "right", "bottom"]
        if all(k in crop for k in keys):
            return tuple(int(crop[k]) for k in keys)
        return None

    if isinstance(crop, (list, tuple)) and len(crop) == 4:
        return tuple(int(v) for v in crop)

    return None


def _extract_grading(entry: Dict) -> Dict[str, float]:
    grading = {}
    source = {}
    if isinstance(entry.get("grading"), dict):
        source.update(entry["grading"])
    source.update({k: entry[k] for k in entry if k not in {"file", "input", "output", "crop", "crop_box", "grading"}})

    temp_value = source.get("temperature_shift") or source.get("warm_shift")
    temp_shift = _parse_mired_value(temp_value)
    if temp_shift is not None and temp_shift != 0:
        grading["temperature_shift"] = temp_shift

    for key in ("shadow_lift", "highlight_lift", "micro_contrast", "local_contrast"):
        value = source.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        grading[key] = numeric

    return grading


def load_manifest(manifest_path: Path) -> List[Dict]:
    if not manifest_path or not manifest_path.exists():
        return []

    with manifest_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, dict):
        images = data.get("images", [])
    elif isinstance(data, list):
        images = data
    else:
        images = []

    valid_entries = []
    for entry in images:
        if not isinstance(entry, dict):
            continue
        if any(k in entry for k in ("file", "input")):
            valid_entries.append(entry)

    return valid_entries


def build_jobs(
    input_dir: Path,
    output_dir: Path,
    target_size: Tuple[int, int],
    manifest_entries: Iterable[Dict],
):
    input_files = get_image_files(str(input_dir))
    manifest_map: Dict[str, Dict] = {}

    for entry in manifest_entries:
        key = entry.get("file") or entry.get("input")
        if key:
            manifest_map[os.path.basename(key)] = entry

    jobs = []

    for filepath in input_files:
        filename = os.path.basename(filepath)
        entry = manifest_map.get(filename, {})

        output_name = entry.get("output")
        if not output_name:
            stem, ext = os.path.splitext(filename)
            output_name = f"{stem}_processed{ext}"

        crop_box = _parse_crop(entry)
        grading = _extract_grading(entry)

        jobs.append(
            {
                "input": filepath,
                "output": str(output_dir / output_name),
                "crop_box": crop_box,
                "grading": grading if grading else None,
                "target_size": target_size,
            }
        )

    return jobs


def run_pipeline(
    input_dir: Path = Path(INPUT_DIR),
    output_dir: Path = Path(OUTPUT_DIR),
    target_size: Tuple[int, int] = DCI_4K_RESOLUTION,
    manifest_path: Optional[Path] = None,
):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path) if manifest_path else input_dir / "manifest.json"

    manifest_entries = load_manifest(manifest_path)
    jobs = build_jobs(input_dir, output_dir, target_size, manifest_entries)

    os.makedirs(output_dir, exist_ok=True)

    processed = []
    failed = []

    for job in jobs:
        success = process_image(
            job["input"],
            job["output"],
            target_size=job["target_size"],
            crop_box=job["crop_box"],
            grading=job["grading"],
        )
        if success:
            processed.append(job["output"])
        else:
            failed.append(job)

    return {
        "processed": processed,
        "failed": failed,
        "jobs": jobs,
    }


def main():
    """
    Main pipeline execution.
    Processes all images in the input directory and saves them to the output directory.
    """
    print("Starting rendering pipeline...")
    print(f"Target resolution: {DCI_4K_RESOLUTION[0]}x{DCI_4K_RESOLUTION[1]} (4K DCI)")
    
    # Get all image files from input directory
    input_files = get_image_files(INPUT_DIR)

    if not input_files:
        print(f"No image files found in '{INPUT_DIR}' directory.")
        print("Please add some images to process.")
        return
    
    print(f"Found {len(input_files)} image(s) to process:")
    for file in input_files:
        print(f"  - {os.path.basename(file)}")
    
    results = run_pipeline(
        input_dir=Path(INPUT_DIR),
        output_dir=Path(OUTPUT_DIR),
        target_size=DCI_4K_RESOLUTION,
    )

    processed_count = len(results["processed"])
    failed_count = len(results["failed"])

    for output_path in results["processed"]:
        print(f"  ✓ Saved to: {os.path.basename(output_path)}")

    for job in results["failed"]:
        print(f"  ✗ Failed to process: {os.path.basename(job['input'])}")

    print(f"\nPipeline completed!")
    print(f"Successfully processed: {processed_count} images")
    if failed_count > 0:
        print(f"Failed to process: {failed_count} images")

    if processed_count:
        print(f"Results saved in '{OUTPUT_DIR}' directory.")


if __name__ == "__main__":
    main()