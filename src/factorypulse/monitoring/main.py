"""Point d'entrée de l'équipe 1. Prévisualisation CSV, traitement métier à réaliser."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
from factorypulse.shared.paths import project_root


def preview_csv(path: Path) -> dict[str, int]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return {
        "mesures": len(rows),
        "temperatures_manquantes": sum(not r["temperature_c"].strip() for r in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Equipe 1 : vérifier le jeu de données d'entrée M01.")
    parser.add_argument("--input", type=Path, default=project_root()/"data/inputs/machine.csv")
    args = parser.parse_args()
    summary = preview_csv(args.input)
    print(f"Source synthétique : {args.input}")
    print(f"Mesures : {summary['mesures']}; température absente : {summary['temperatures_manquantes']}")
    print("À développer par l'équipe 1 : règles + génération de data/outputs/m01.jsonl")


if __name__ == "__main__":
    main()
