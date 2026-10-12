"""Point d'entrée de l'équipe 2 : inventaire des six images à réaliser."""

from __future__ import annotations
import argparse
import csv
from pathlib import Path
from factorypulse.shared.paths import project_root
from factorypulse.vision.color_check import detect_marker_color
from factorypulse.vision.detector import detect_objects


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
    detect_objects()

    # detect_marker_color()
    # p = argparse.ArgumentParser(description="Equipe 2 : vérifier les photos nécessaires au labo.")
    # p.add_argument("--manifest", type=Path, default=project_root()/"data/inputs/prises_de_vue.csv")
    # p.add_argument("--images", type=Path, default=project_root()/"data/images")
    # args = p.parse_args()
    # inventory = inspect_manifest(args.manifest, args.images)
    # for item in inventory:
    #     print(("OK   " if item["present"] else "A FAIRE ")+str(item["file"]))
    # print("À développer par l'équipe 2 : YOLO, contrôle de couleur et JSONL Q01.")


if __name__ == "__main__":
    main()
