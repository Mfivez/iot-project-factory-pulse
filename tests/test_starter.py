from factorypulse.monitoring.main import preview_csv
from factorypulse.vision.main import inspect_manifest
from factorypulse.shared.paths import project_root, fixture_path
from factorypulse.dashboard.readers import load_fixture
from factorypulse.agent import tools
import pytest


def test_csv_inputs_can_be_read():
    path = project_root() / "data/inputs/machine.csv"
    summary = preview_csv(path)
    assert summary["mesures"] == 300
    assert summary["temperatures_manquantes"] > 0


def test_vision_manifest_six_photos_specified():
    root = project_root()
    inventory = inspect_manifest(root/"data/inputs/prises_de_vue.csv", root/"data/images")
    assert len(inventory) == 6
    assert all(isinstance(row["present"], bool) for row in inventory)


def test_dashboard_deduplicates():
    assert len(load_fixture("q01.jsonl", deduplicate=True)) == 6
    assert len(load_fixture("q01.jsonl", deduplicate=False)) == 7


def test_fixture_path_whitelist():
    with pytest.raises(ValueError):
        fixture_path("../../secrets.env")


def test_agent_function_signatures_exist():
    assert all(callable(getattr(tools, name)) for name in ("get_status", "get_history", "get_logs", "get_inspections"))
