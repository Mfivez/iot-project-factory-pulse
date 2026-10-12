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


@pytest.mark.parametrize(
    ("temperature_c", "expected_status"),
    [
        (59.9, "normal"),
        (60.0, "normal"),
        (60.1, "high_temperature"),
        (None, "unknown"),
        ("61", "unknown"),
        (True, "unknown"),
    ],
)
def test_detect_high_temperature_classifies_measurement(temperature_c, expected_status):
    event = {
        "event_id": "M01-TEST-001",
        "payload": {"temperature_c": temperature_c},
    }

    result = tools.detect_high_temperature(event)

    assert result["status"] == expected_status
    assert result["temperature_c"] == temperature_c
    assert result["threshold_c"] == 60.0
    assert result["event_id"] == "M01-TEST-001"
    assert event["payload"]["temperature_c"] == temperature_c


def test_detect_high_temperature_handles_missing_payload():
    result = tools.detect_high_temperature({"event_id": "M01-TEST-002"})

    assert result["status"] == "unknown"
    assert result["temperature_c"] is None
    assert result["event_id"] == "M01-TEST-002"


def test_get_status_returns_latest_events_at_replay_time():
    result = tools.get_status("M01", "2026-10-12T09:00:02Z")

    assert result["as_of_utc"] == "2026-10-12T09:00:02Z"
    assert {event["event_type"] for event in result["events"]} == {"telemetry", "health"}
    assert result["summary"]["machine_state"] == "RUNNING"
    assert result["summary"]["node_state"] == "RUNNING"
    assert result["summary"]["data_age_s"] == {"telemetry": 0.0, "health": 2.0}


def test_get_status_rejects_timestamp_outside_replay():
    with pytest.raises(ValueError):
        tools.get_status("M01", "2026-10-12T08:59:59Z")


def test_get_history_uses_inclusive_bounds_and_returns_telemetry_only():
    result = tools.get_history(
        "M01",
        "2026-10-12T09:00:01Z",
        "2026-10-12T09:00:02Z",
    )

    assert result["as_of_utc"] == "2026-10-12T09:00:02Z"
    assert [event["event_id"] for event in result["events"]] == ["M01-000002", "M01-000003"]
    assert all(event["event_type"] == "telemetry" for event in result["events"])
    assert result["warnings"] == []


def test_get_history_rejects_reversed_interval():
    with pytest.raises(ValueError):
        tools.get_history("M01", "2026-10-12T09:00:02Z", "2026-10-12T09:00:01Z")


def test_get_logs_includes_station_and_targeted_server_logs():
    result = tools.get_logs(
        "M01",
        "2026-10-12T09:03:00Z",
        "2026-10-12T09:05:16Z",
    )

    assert [event["event_id"] for event in result["events"]] == [
        "LOG-0002",
        "LOG-0003",
        "LOG-0004",
        "LOG-0005",
        "LOG-0006",
    ]
    assert result["events"][-1]["station_id"] == "SERVER"
    assert result["events"][-1]["payload"]["target_station"] == "M01"
    assert result["warnings"] == []


def test_get_logs_rejects_unknown_station():
    with pytest.raises(ValueError):
        tools.get_logs("UNKNOWN", "2026-10-12T09:00:00Z", "2026-10-12T09:00:01Z")


def test_get_inspections_deduplicates_exact_event_ids():
    result = tools.get_inspections("2026-10-12T09:00:30Z", "2026-10-12T09:05:30Z")

    assert [event["event_id"] for event in result["events"]] == [
        "Q01-000001",
        "Q01-000002",
        "Q01-000003",
        "Q01-000004",
        "Q01-000005",
        "Q01-000006",
    ]
    assert len(result["events"]) == 6
    assert result["warnings"] == []


def test_get_inspections_clamps_upper_bound_to_replay_cursor():
    result = tools.get_inspections("2026-10-12T09:05:30Z", "2026-10-12T09:06:00Z")

    assert result["as_of_utc"] == "2026-10-12T09:05:59Z"
    assert [event["event_id"] for event in result["events"]] == ["Q01-000006"]


def test_get_inspections_rejects_reversed_interval():
    with pytest.raises(ValueError):
        tools.get_inspections("2026-10-12T09:00:02Z", "2026-10-12T09:00:01Z")
