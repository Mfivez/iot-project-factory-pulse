"""Point d'entrée de l'équipe 2 : inventaire des six images à réaliser."""

from __future__ import annotations
import argparse
import csv
from pathlib import Path
from factorypulse.vision.detection_euro import detect_euro
from factorypulse.vision.detection_pays_2euros import detect_country_coins


def inspect_manifest(manifest: Path, images: Path) -> list[dict[str, str | bool]]:
    with manifest.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [
        {
            "file": row["file"],
            "scene": row["scene"],
            "present": (images / row["file"]).is_file(),
        }
        for row in rows
    ]


def main() -> None:
    detect_euro()
    detect_country_coins()
    
    


if __name__ == "__main__":
    main()
