from datetime import datetime, timezone

import pytest

from factorypulse.agent.tools import get_status
from factorypulse.dashboard.readers import load_dashboard_events, machine_status, station_health
from factorypulse.shared.contracts import parse_utc
from factorypulse.shared.status import summarize_station


def _event(
    event_id: str,
    timestamp: str,
    event_type: str,
    payload: dict,
    station_id: str = "M01",
) -> dict:
    return {
        "event_id": event_id,
        "timestamp_utc": timestamp,
        "station_id": station_id,
        "event_type": event_type,
        "source": "simulated",
        "payload": payload,
    }


def test_summarize_station_keeps_machine_sensor_and_node_states_separate():
    events = [
        _event(
            "health",
            "2026-10-12T09:00:00Z",
            "health",
            {"service_state": "RUNNING"},
        ),
        _event(
            "telemetry",
            "2026-10-12T09:00:01Z",
            "telemetry",
            {
                "machine_state": "STOPPED",
                "data_quality": "TEMPERATURE_MISSING",
            },
        ),
    ]

    summary = summarize_station(
        events,
        "M01",
        datetime(2026, 10, 12, 9, 0, 10, tzinfo=timezone.utc),
        stale_after_s=15,
    )

    assert summary["node_state"] == "RUNNING"
    assert summary["machine_state"] == "STOPPED"
    assert summary["sensor_state"] == "DATA_ISSUE"
    assert summary["data_age_s"] == 9
    assert summary["health_age_s"] == 10
    assert summary["telemetry_event"]["event_id"] == "telemetry"
    assert summary["health_event"]["event_id"] == "health"


def test_summarize_station_ignores_future_events_and_marks_old_node_offline():
    events = [
        _event(
            "old-health",
            "2026-10-12T09:00:00Z",
            "health",
            {"service_state": "RUNNING"},
        ),
        _event(
            "future-health",
            "2026-10-12T09:00:20Z",
            "health",
            {"service_state": "RUNNING"},
        ),
    ]

    summary = summarize_station(
        events,
        "M01",
        datetime(2026, 10, 12, 9, 0, 16, tzinfo=timezone.utc),
        stale_after_s=15,
    )

    assert summary["node_state"] == "OFFLINE"
    assert summary["health_event"]["event_id"] == "old-health"
    assert summary["health_age_s"] == 16
    assert summary["machine_state"] == "UNKNOWN"
    assert summary["sensor_state"] == "UNKNOWN"
    assert summary["data_age_s"] is None


def test_summarize_station_does_not_mark_node_offline_at_exact_stale_threshold():
    events = [
        _event(
            "health",
            "2026-10-12T09:00:00Z",
            "health",
            {"service_state": "RUNNING"},
        ),
    ]

    summary = summarize_station(
        events,
        "M01",
        datetime(2026, 10, 12, 9, 0, 15, tzinfo=timezone.utc),
        stale_after_s=15,
    )

    assert summary["node_state"] == "RUNNING"


def test_summarize_station_rejects_unknown_station_and_naive_clock():
    as_of = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="non autorisé"):
        summarize_station([], "M02", as_of, stale_after_s=15)
    with pytest.raises(ValueError, match="fuseau horaire"):
        summarize_station([], "M01", datetime(2026, 10, 12, 9, 0), stale_after_s=15)


def test_dashboard_and_agent_status_use_the_same_shared_calculation():
    events = load_dashboard_events()
    as_of_text = "2026-10-12T09:05:59Z"
    as_of = parse_utc(as_of_text)
    shared = summarize_station(events, "M01", as_of, stale_after_s=15)
    dashboard_machine = machine_status(events, as_of, stale_after_s=15)
    dashboard_nodes = station_health(events, as_of, stale_after_s=15)
    agent_status = get_status("M01", as_of_text)

    assert dashboard_machine["machine_state"] == shared["machine_state"]
    assert dashboard_machine["sensor_state"] == shared["sensor_state"]
    assert dashboard_nodes["M01"]["state"] == shared["node_state"]
    assert agent_status["summary"] == {
        "node_state": shared["node_state"],
        "machine_state": shared["machine_state"],
        "data_age_s": shared["data_age_s"],
    }
