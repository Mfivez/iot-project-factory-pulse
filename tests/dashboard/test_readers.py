from datetime import datetime, timezone

from factorypulse.dashboard.readers import (
    build_incidents,
    events_at,
    load_dashboard_events,
    machine_status,
    station_health,
)
from factorypulse.shared.contracts import parse_utc


def _event(
    event_id: str,
    timestamp: str,
    station: str,
    event_type: str,
    payload: dict,
) -> dict:
    return {
        "event_id": event_id,
        "timestamp_utc": timestamp,
        "station_id": station,
        "event_type": event_type,
        "source": "simulated",
        "payload": payload,
    }


def test_dashboard_loads_all_fixture_types_and_deduplicates_ids():
    events = load_dashboard_events()

    assert {event["event_type"] for event in events} == {
        "telemetry", "inspection", "health", "log"
    }
    assert len({event["event_id"] for event in events}) == len(events)
    assert sum(event["event_type"] == "inspection" for event in events) == 6


def test_events_at_includes_events_on_the_cursor_and_excludes_future_events():
    events = [
        _event("before", "2026-10-12T09:00:00Z", "M01", "health", {}),
        _event("at", "2026-10-12T09:00:05Z", "M01", "health", {}),
        _event("after", "2026-10-12T09:00:06Z", "M01", "health", {}),
    ]

    visible = events_at(events, parse_utc("2026-10-12T09:00:05Z"))

    assert [event["event_id"] for event in visible] == ["before", "at"]


def test_machine_sensor_and_node_statuses_remain_distinct():
    events = [
        _event(
            "health-1",
            "2026-10-12T09:00:00Z",
            "M01",
            "health",
            {
                "service_state": "RUNNING",
                "cpu_pct": 10,
                "ram_pct": 20,
                "mqtt_connected": True,
                "uptime_s": 10,
            },
        ),
        _event(
            "telemetry-1",
            "2026-10-12T09:00:01Z",
            "M01",
            "telemetry",
            {
                "temperature_c": None,
                "vibration_rms_g": 0.1,
                "machine_state": "STOPPED",
                "data_quality": "TEMPERATURE_MISSING",
                "alert_level": "DATA_ISSUE",
                "alert_reason": "TEMPERATURE_MISSING",
            },
        ),
    ]
    as_of = datetime(2026, 10, 12, 9, 1, tzinfo=timezone.utc)

    status = machine_status(events)
    nodes = station_health(events, as_of, stale_after_s=15)

    assert status["machine_state"] == "STOPPED"
    assert status["sensor_state"] == "DATA_ISSUE"
    assert nodes["M01"]["state"] == "OFFLINE"
    assert nodes["Q01"]["state"] == "UNKNOWN"
    assert nodes["SERVER"]["state"] == "UNKNOWN"


def test_incidents_keep_event_evidence_and_group_repeated_alerts():
    events = [
        _event(
            "alert-1",
            "2026-10-12T09:00:00Z",
            "M01",
            "telemetry",
            {
                "temperature_c": None,
                "vibration_rms_g": 0.1,
                "machine_state": "RUNNING",
                "data_quality": "TEMPERATURE_MISSING",
                "alert_level": "DATA_ISSUE",
                "alert_reason": "TEMPERATURE_MISSING",
            },
        ),
        _event(
            "alert-2",
            "2026-10-12T09:00:01Z",
            "M01",
            "telemetry",
            {
                "temperature_c": None,
                "vibration_rms_g": 0.1,
                "machine_state": "RUNNING",
                "data_quality": "TEMPERATURE_MISSING",
                "alert_level": "DATA_ISSUE",
                "alert_reason": "TEMPERATURE_MISSING",
            },
        ),
    ]
    incidents = build_incidents(
        events,
        parse_utc("2026-10-12T09:00:01Z"),
        stale_after_s=15,
    )

    assert len(incidents) == 1
    assert incidents[0]["occurrences"] == 2
    assert incidents[0]["evidence_event_ids"] == ["alert-1", "alert-2"]
