#!/usr/bin/env python3
"""Generate manifests pairing processed outputs with enhancement files."""
import csv
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from difflib import SequenceMatcher


# --- Repo & I/O ---
REPO = Path.cwd()
MAIN_DIR = REPO / "results" / "new_output"
ENH_DIR = REPO / "output"
OUT_DIR = REPO / "manifests"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Matching config ---
SIM_THRESHOLD = 0.72  # fuzzy name similarity floor
SIZE_TOLERANCE = 0.08  # ±8% size tolerance considered "close"
PREF_EXT = {
    # prefer matching these extension pairs
    ".png": [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr"],
    ".jpg": [".jpg", ".jpeg", ".png", ".tif", ".tiff"],
    ".jpeg": [".jpeg", ".jpg", ".png", ".tif", ".tiff"],
    ".tif": [".tif", ".tiff", ".png", ".jpg", ".jpeg"],
    ".tiff": [".tiff", ".tif", ".png", ".jpg", ".jpeg"],
    ".exr": [".exr", ".tif", ".tiff", ".png"],
}
# Common noise tokens to strip from stems when normalizing
NOISE_PAT = re.compile(
    r"(?:_processed\\b|_denoise\\b|_sharpen\\b|_v\\d+\\b|_[0-9]{3,4}p\\b|_[0-9]{2,4}(?:bit|b)?\\b|"
    r"_[0-9]{1,3}fps\\b|_[0-9]+x[0-9]+\\b|_[0-9]{4}-[0-9]{2}-[0-9]{2}\\b|_[0-9]{6,}\\b|_pass\\d+\\b|"
    r"_final\\b|_draft\\b)",
    re.IGNORECASE,
)


def norm_stem(name: str) -> str:
    stem = Path(name).stem
    stem = NOISE_PAT.sub("", stem)
    stem = re.sub(r"[_\-\s]+", "_", stem).strip("_").lower()
    return stem


def seq_sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def list_files(base: Path, name_filter=None) -> List[Path]:
    if not base.exists():
        return []
    out = []
    for p in base.rglob("*"):
        if p.is_file() and (name_filter(p) if name_filter else True):
            out.append(p)
    return out


def file_record(stage: str, repo: Path, p: Path) -> Dict:
    st = p.stat()
    return {
        "stage": stage,
        "relative_path": p.relative_to(repo).as_posix(),
        "filename": p.name,
        "bytes": st.st_size,
        "modified_iso": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        "ext": p.suffix.lower(),
        "stem": Path(p.name).stem,
        "norm_stem": norm_stem(p.name),
    }


def write_csv(path: Path, rows: List[Dict], fields: List[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def readable_size(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n / 1024:.1f} {unit}"
        n /= 1024
    return f"{n:.0f} B"


def choose_best_match(main: Dict, candidates: List[Dict]) -> Tuple[Optional[Dict], Dict[str, float]]:
    """Return best enhance candidate + scoring breakdown."""
    nm = main["norm_stem"]
    main_ext = main["ext"]
    main_bytes = max(int(main["bytes"]), 1)

    best: Optional[Dict] = None
    best_score = -1.0
    best_breakdown: Dict[str, float] = {}

    for candidate in candidates:
        sim = seq_sim(nm, candidate["norm_stem"])
        # Extension preference
        ext_ok = candidate["ext"] in PREF_EXT.get(main_ext, [main_ext])
        ext_bonus = 0.06 if ext_ok else 0.0

        # Size proximity (not required, but rewarded)
        candidate_bytes = max(int(candidate["bytes"]), 1)
        size_ratio = candidate_bytes / main_bytes
        size_delta = abs(1 - size_ratio)
        size_ok = size_delta <= SIZE_TOLERANCE
        size_bonus = 0.05 if size_ok else 0.0

        # Overall score: name similarity weighted highest
        score = (sim * 0.89) + ext_bonus + size_bonus

        if score > best_score:
            best = candidate
            best_score = score
            best_breakdown = {
                "name_sim": sim,
                "ext_bonus": ext_bonus,
                "size_bonus": size_bonus,
                "size_ratio": size_ratio,
                "score": score,
            }

    if best and best_breakdown.get("name_sim", 0.0) >= SIM_THRESHOLD:
        return best, best_breakdown
    return None, {
        "name_sim": 0.0,
        "score": 0.0,
        "size_ratio": 0.0,
        "ext_bonus": 0.0,
        "size_bonus": 0.0,
    }


def classify_status(main: Dict, match: Optional[Dict], metrics: Dict[str, float]) -> str:
    if not match:
        return "ORPHAN_MAIN"  # no enhance counterpart found
    similarity = metrics.get("name_sim", 0.0)
    if similarity >= 0.9:
        return "MATCH_STRONG"
    if similarity >= 0.8:
        return "MATCH_GOOD"
    return "MATCH_WEAK"


def main() -> int:
    # Collect files
    main_files = [
        file_record("main", REPO, path)
        for path in list_files(MAIN_DIR, lambda q: "_processed" in q.stem)
    ]
    enhance_files = [
        file_record("enhance", REPO, path) for path in list_files(ENH_DIR)
    ]

    # Write full manifest CSV
    manifest_rows = main_files + enhance_files
    write_csv(
        OUT_DIR / "processed_manifest.csv",
        manifest_rows,
        [
            "stage",
            "relative_path",
            "filename",
            "bytes",
            "modified_iso",
            "ext",
            "stem",
            "norm_stem",
        ],
    )

    # Cross-reference by normalized stems (fast lookup buckets)
    bucket: Dict[str, List[Dict]] = {}
    for enhance in enhance_files:
        bucket.setdefault(enhance["norm_stem"], []).append(enhance)

    # Build candidate lists by proximity of normalized names (same or close)
    pairs = []
    for main_file in main_files:
        # Start with exact normalized stem bucket
        candidates = bucket.get(main_file["norm_stem"], [])
        # If empty, broaden search: take top-N by fuzzy similarity against all enhance files (cheap scan)
        if not candidates:
            scored: List[Tuple[float, Dict]] = []
            normalized = main_file["norm_stem"]
            for enhance in enhance_files:
                similarity = seq_sim(normalized, enhance["norm_stem"])
                if similarity >= (SIM_THRESHOLD - 0.08):  # consider near-threshold for review
                    scored.append((similarity, enhance))
            scored.sort(key=lambda x: x[0], reverse=True)
            candidates = [enhance for _, enhance in scored[:12]]  # cap to 12 nearest to keep scoring quick

        match, metrics = choose_best_match(main_file, candidates)
        status = classify_status(main_file, match, metrics)
        row = {
            "main_path": main_file["relative_path"],
            "main_file": main_file["filename"],
            "main_ext": main_file["ext"],
            "main_bytes": main_file["bytes"],
            "main_size_readable": readable_size(int(main_file["bytes"])),
            "enh_path": match["relative_path"] if match else "",
            "enh_file": match["filename"] if match else "",
            "enh_ext": match["ext"] if match else "",
            "enh_bytes": match["bytes"] if match else "",
            "enh_size_readable": readable_size(int(match["bytes"])) if match else "",
            "name_similarity": f"{metrics.get('name_sim', 0.0):.3f}",
            "size_ratio": f"{metrics.get('size_ratio', 0.0):.3f}",
            "score": f"{metrics.get('score', 0.0):.3f}",
            "status": status,
        }
        pairs.append(row)

    # Write pairs CSV
    write_csv(
        OUT_DIR / "pairs.csv",
        pairs,
        [
            "status",
            "score",
            "main_file",
            "main_ext",
            "main_size_readable",
            "main_bytes",
            "main_path",
            "enh_file",
            "enh_ext",
            "enh_size_readable",
            "enh_bytes",
            "enh_path",
            "name_similarity",
            "size_ratio",
        ],
    )

    # Markdown summaries
    orphan_main = sum(1 for pair in pairs if pair["status"] == "ORPHAN_MAIN")
    strong = sum(1 for pair in pairs if pair["status"] == "MATCH_STRONG")
    good = sum(1 for pair in pairs if pair["status"] == "MATCH_GOOD")
    weak = sum(1 for pair in pairs if pair["status"] == "MATCH_WEAK")

    md = []
    md.append("# Processed Outputs — Manifest & Pairing\n")
    md.append(f"- Generated: {datetime.now().isoformat(timespec='seconds')}")
    md.append("- Main pipeline dir: `results/new_output/` (expects `*_processed.*`)")
    md.append("- Enhancement dir: `output/`\n")
    md.append("## Pairing Summary\n")
    md.append(
        f"- **MATCH_STRONG**: {strong}\n- **MATCH_GOOD**: {good}\n- **MATCH_WEAK**: {weak}\n- **ORPHAN_MAIN**: {orphan_main}\n"
    )
    md.append("### Sample (up to 40 rows)\n")
    md.append("| status | score | main → enhance |\n|---|---:|---|\n")
    for row in pairs[:40]:
        lhs = f"`{row['main_file']}`"
        rhs = f"`{row['enh_file']}`" if row["enh_file"] else "—"
        md.append(f"| {row['status']} | {row['score']} | {lhs} → {rhs} |\n")

    (OUT_DIR / "pairs.md").write_text("\n".join(md), encoding="utf-8")

    # Full listings MD
    md2 = []
    md2.append("# Processed Outputs Manifest\n")
    md2.append(f"- Generated: {datetime.now().isoformat(timespec='seconds')}")
    md2.append("- Main pipeline dir: `results/new_output/`")
    md2.append("- Enhancement dir: `output/`\n")
    md2.append("## Main pipeline (`*_processed.*`)\n| path | size | modified |\n|---|---:|---|\n")
    for record in sorted(
        [row for row in manifest_rows if row["stage"] == "main"],
        key=lambda x: x["relative_path"],
    ):
        md2.append(
            f"| `{record['relative_path']}` | {readable_size(int(record['bytes']))} | {record['modified_iso']} |\n"
        )
    md2.append("\n## Enhancement outputs (`output/`)\n| path | size | modified |\n|---|---:|---|\n")
    for record in sorted(
        [row for row in manifest_rows if row["stage"] == "enhance"],
        key=lambda x: x["relative_path"],
    ):
        md2.append(
            f"| `{record['relative_path']}` | {readable_size(int(record['bytes']))} | {record['modified_iso']} |\n"
        )
    (OUT_DIR / "processed_manifest.md").write_text("\n".join(md2), encoding="utf-8")

    print("Wrote:")
    print(f"  - {OUT_DIR / 'processed_manifest.csv'}")
    print(f"  - {OUT_DIR / 'processed_manifest.md'}")
    print(f"  - {OUT_DIR / 'pairs.csv'}")
    print(f"  - {OUT_DIR / 'pairs.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
