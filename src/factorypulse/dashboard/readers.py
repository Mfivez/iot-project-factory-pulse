"""Accès standard aux fixtures : pas de dépendance Streamlit ici."""
from factorypulse.shared.jsonl import read_jsonl, dedupe_events
from factorypulse.shared.paths import fixture_path


def load_fixture(name: str, deduplicate: bool = True) -> list[dict]:
    events = read_jsonl(fixture_path(name))
    return dedupe_events(events) if deduplicate else events
