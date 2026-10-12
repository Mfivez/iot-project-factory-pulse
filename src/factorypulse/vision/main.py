"""Point d'entrée de l'équipe 2 : inventaire des six images à réaliser."""

from __future__ import annotations
import argparse
import csv
from pathlib import Path
from factorypulse.shared.paths import project_root


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
    parser = argparse.ArgumentParser(description="Equipe 2 : photos du labo et démonstrations webcam.")
    parser.add_argument("--manifest", type=Path, default=project_root()/"data/inputs/prises_de_vue.csv")
    parser.add_argument("--images", type=Path, default=project_root()/"data/images")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--webcam", action="store_true", help="Lancer YOLO et la webcam (extra vision requis).")
    mode.add_argument("--colors", action="store_true", help="Lancer la détection de couleurs par webcam.")
    args = parser.parse_args()

    # Les bibliothèques et le matériel ne sont nécessaires qu'aux démonstrations.
    if args.webcam:
        from factorypulse.vision.detector import detect_objects
        detect_objects()
    elif args.colors:
        from factorypulse.vision.color_check import detect_marker_color
        detect_marker_color()
    else:
        inventory = inspect_manifest(args.manifest, args.images)
        for item in inventory:
            print(("OK   " if item["present"] else "A FAIRE ")+str(item["file"]))
        print("À développer par l'équipe 2 : décisions d'inspection et JSONL Q01.")


if __name__ == "__main__":
    main()
