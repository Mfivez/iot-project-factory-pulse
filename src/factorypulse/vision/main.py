"""Point d'entrée de l'équipe 2 : inventaire des six images à réaliser."""

from __future__ import annotations
import argparse
import csv
from pathlib import Path


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
    parser = argparse.ArgumentParser(
        description="Equipe 2 : détection sur caméra ou image fixe."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--webcam", action="store_true", help="Démarrer directement la webcam.")
    mode.add_argument("--colors", action="store_true", help="Démarrer le contrôle couleur webcam.")
    args = parser.parse_args()

    if args.webcam:
        from factorypulse.vision.detector import detect_objects
        detect_objects()
    elif args.colors:
        from factorypulse.vision.color_check import detect_marker_color
        detect_marker_color()
    else:
        from factorypulse.vision.ui import launch_ui
        launch_ui()


if __name__ == "__main__":
    main()
