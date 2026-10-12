"""Lecture, écriture et déduplication déterministes des fichiers JSONL."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Any
from factorypulse.shared.contracts import validate_event, ContractError


def read_jsonl(path: str | Path, validate: bool = True) -> list[dict[str, Any]]:
    """Les doublons exacts sont conservés jusqu'à `dedupe_events`."""
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(file)
    events: list[dict[str, Any]] = []
    with file.open("r", encoding="utf-8") as f:
        for line_number, raw in enumerate(f, 1):
            if not raw.strip():
                continue
            try:
                event = json.loads(raw)
                if validate:
                    validate_event(event)
            except (json.JSONDecodeError, ContractError) as exc:
                raise ValueError(f"{file}:{line_number}: {exc}") from exc
            events.append(event)
    return events


def write_jsonl(events: Iterable[dict[str, Any]], path: str | Path, append: bool = False) -> None:
    """Écrit uniquement des événements valides, sans modifier les fixtures."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Validation préalable pour éviter une écriture partielle si une entrée est fausse.
    checked = [validate_event(event) for event in events]
    mode = "a" if append else "w"
    with dest.open(mode, encoding="utf-8") as f:
        for event in checked:
            f.write(json.dumps(event, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")


def dedupe_events(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ignore seulement des doublons exacts, rejette les collisions d'identifiants."""
    seen: dict[str, dict[str, Any]] = {}
    for event in events:
        validate_event(event)
        identifier = event["event_id"]
        if identifier in seen:
            if seen[identifier] != event:
                raise ContractError(f"Collision event_id avec contenu différent : {identifier}")
            continue
        seen[identifier] = event
    return list(seen.values())
