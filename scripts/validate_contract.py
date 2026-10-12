#!/usr/bin/env python3
"""Valide tous les exemples du labo et compte les doublons exacts."""
from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from factorypulse.shared.jsonl import read_jsonl, dedupe_events


def main() -> int:
    root = ROOT / "data" / "fixtures"
    names = ("m01.jsonl", "q01.jsonl", "systeme.jsonl", "logs.jsonl")
    try:
        all_events = []
        for name in names:
            events = read_jsonl(root / name)
            unique = dedupe_events(events)
            all_events.extend(unique)
            print(f"OK {name:16} {len(events):4} événements, {len(events)-len(unique)} doublon(s) exact(s)")
        dedupe_events(all_events)
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERREUR {exc}", file=sys.stderr)
        return 1
    print("OK : contrat FP-LAB-1.1 ; aucune acquisition physique/YOLO prouvée par ces tests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
