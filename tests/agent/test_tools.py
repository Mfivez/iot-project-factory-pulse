import json

import pytest

from factorypulse.agent import tools


REPLAY_END = "2026-10-12T09:05:59Z"


def _event(
    event_id: str,
    timestamp: str,
    station_id: str,
    event_type: str,
    payload: dict,
) -> dict:
    return {
        "event_id": event_id,
        "timestamp_utc": timestamp,
        "station_id": station_id,
        "event_type": event_type,
        "source": "simulated",
        "payload": payload,
    }


def _telemetry(event_id: str, timestamp: str, state: str = "RUNNING") -> dict:
    return _event(
        event_id,
        timestamp,
        "M01",
        "telemetry",
        {
            "temperature_c": 40.0,
            "vibration_rms_g": 0.1,
            "machine_state": state,
            "data_quality": "OK",
            "alert_level": "OK",
            "alert_reason": None,
        },
    )


def test_get_status_returns_latest_original_events_and_separate_states():
    result = tools.get_status("M01", "2026-10-12T09:04:59Z")

    assert set(result) == {"as_of_utc", "events", "warnings", "summary"}
    assert {event["event_type"] for event in result["events"]} == {
        "telemetry", "health"
    }
    assert all("event_id" in event for event in result["events"])
    assert result["summary"] == {
        "node_state": "RUNNING",
        "machine_state": "STOPPED",
        "data_age_s": 0.0,
    }
    assert result["warnings"] == []
    json.dumps(result)


def test_get_status_caps_future_cursor_and_warns_when_data_is_stale():
    result = tools.get_status("M01", "2026-10-12T09:07:00Z")

    assert result["as_of_utc"] == REPLAY_END
    assert result["summary"]["node_state"] == "OFFLINE"
    assert result["summary"]["data_age_s"] == 60.0
    assert any("limitée à la fin du replay" in warning for warning in result["warnings"])
    assert any("périmée" in warning for warning in result["warnings"])


def test_get_status_reports_missing_station_telemetry_without_guessing_state():
    result = tools.get_status("Q01", "2026-10-12T09:00:00Z")

    assert result["summary"] == {
        "node_state": "RUNNING",
        "machine_state": "UNKNOWN",
        "data_age_s": None,
    }
    assert any("Aucune télémétrie" in warning for warning in result["warnings"])
    assert all(event["event_type"] == "health" for event in result["events"])


def test_get_status_warns_when_latest_telemetry_has_missing_sensor_data(monkeypatch):
    telemetry = _telemetry("telemetry", "2026-10-12T09:00:00Z")
    telemetry["payload"]["temperature_c"] = None
    telemetry["payload"]["data_quality"] = "TEMPERATURE_MISSING"
    telemetry["payload"]["alert_level"] = "DATA_ISSUE"
    telemetry["payload"]["alert_reason"] = "TEMPERATURE_MISSING"
    monkeypatch.setattr(tools, "_load_events", lambda: [telemetry])

    result = tools.get_status("M01", "2026-10-12T09:00:01Z")

    assert result["summary"]["machine_state"] == "RUNNING"
    assert any("TEMPERATURE_MISSING" in warning for warning in result["warnings"])
    assert result["events"][0]["event_id"] == "telemetry"


def test_get_history_uses_inclusive_bounds_and_caps_the_replay_end(monkeypatch):
    events = [
        _telemetry("before", "2026-10-12T09:00:00Z"),
        _telemetry("start", "2026-10-12T09:00:01Z"),
        _telemetry("end", "2026-10-12T09:00:02Z"),
        _telemetry("after", "2026-10-12T09:00:03Z"),
    ]
    monkeypatch.setattr(tools, "_load_events", lambda: events)

    result = tools.get_history(
        "M01",
        "2026-10-12T09:00:01Z",
        "2026-10-12T09:07:00Z",
    )

    assert result["as_of_utc"] == REPLAY_END
    assert [event["event_id"] for event in result["events"]] == ["start", "end", "after"]
    assert all(event["event_type"] == "telemetry" for event in result["events"])
    assert any("limitée à la fin du replay" in warning for warning in result["warnings"])


def test_get_history_limits_results_and_reports_truncation(monkeypatch):
    timestamp = "2026-10-12T09:01:00Z"
    monkeypatch.setattr(
        tools,
        "_load_events",
        lambda: [_telemetry(f"event-{number}", timestamp) for number in range(501)],
    )

    result = tools.get_history("M01", timestamp, timestamp)

    assert len(result["events"]) == 500
    assert result["events"][0]["event_id"] == "event-0"
    assert any("tronqués à 500" in warning for warning in result["warnings"])


def test_get_logs_includes_station_and_targeted_server_logs(monkeypatch):
    events = [
        _event("direct", "2026-10-12T09:00:01Z", "M01", "log", {
            "service": "acquisition",
            "level": "ERROR",
            "code": "READ_FAILED",
            "message": "Lecture indisponible.",
        }),
        _event("targeted", "2026-10-12T09:00:02Z", "SERVER", "log", {
            "service": "collector",
            "level": "WARNING",
            "code": "HEARTBEAT_STALE",
            "target_station": "M01",
            "message": "Signe de vie périmé.",
        }),
        _event("other-target", "2026-10-12T09:00:03Z", "SERVER", "log", {
            "service": "collector",
            "level": "WARNING",
            "code": "HEARTBEAT_STALE",
            "target_station": "Q01",
            "message": "Autre station.",
        }),
    ]
    monkeypatch.setattr(tools, "_load_events", lambda: events)

    result = tools.get_logs("M01", "2026-10-12T09:00:01Z", "2026-10-12T09:00:03Z")

    assert [event["event_id"] for event in result["events"]] == ["direct", "targeted"]
    assert all(event["event_type"] == "log" for event in result["events"])
    json.dumps(result)


def test_get_logs_limits_results_and_reports_truncation(monkeypatch):
    timestamp = "2026-10-12T09:01:00Z"
    events = [
        _event(f"log-{number}", timestamp, "M01", "log", {
            "service": "acquisition",
            "level": "INFO",
            "code": "HEARTBEAT",
            "message": "Heartbeat.",
        })
        for number in range(101)
    ]
    monkeypatch.setattr(tools, "_load_events", lambda: events)

    result = tools.get_logs("M01", timestamp, timestamp)

    assert len(result["events"]) == 100
    assert any("tronqués à 100" in warning for warning in result["warnings"])


def test_get_inspections_are_unique_and_keep_original_event_ids():
    result = tools.get_inspections(
        "2026-10-12T09:00:00Z",
        "2026-10-12T09:07:00Z",
    )

    assert result["as_of_utc"] == REPLAY_END
    assert len(result["events"]) == 6
    assert len({event["event_id"] for event in result["events"]}) == 6
    assert all(
        event["station_id"] == "Q01" and event["event_type"] == "inspection"
        for event in result["events"]
    )


def test_get_inspections_limits_results_and_reports_truncation(monkeypatch):
    timestamp = "2026-10-12T09:01:00Z"
    inspections = [
        _event(f"inspection-{number}", timestamp, "Q01", "inspection", {
            "part_id": f"part-{number}",
            "object_class": "bottle",
            "confidence": 0.9,
            "bbox_xyxy": [1, 2, 3, 4],
            "marker_color": "green",
            "verdict": "PASS",
            "image_path": None,
            "image_size_px": [640, 480],
            "algorithm": "test",
        })
        for number in range(101)
    ]
    monkeypatch.setattr(tools, "_load_events", lambda: inspections)

    result = tools.get_inspections(timestamp, timestamp)

    assert len(result["events"]) == 100
    assert any("tronqués à 100" in warning for warning in result["warnings"])


@pytest.mark.parametrize(
    ("station_id", "at_utc"),
    [
        ("M02", "2026-10-12T09:00:00Z"),
        (None, "2026-10-12T09:00:00Z"),
        ("M01", "2026-10-12T09:00:00"),
    ],
)
def test_get_status_rejects_unauthorized_station_and_invalid_timestamp(
    station_id: str | None,
    at_utc: str,
):
    with pytest.raises(ValueError):
        tools.get_status(station_id, at_utc)


def test_range_tools_reject_invalid_or_reversed_ranges():
    with pytest.raises(ValueError):
        tools.get_history("M01", "2026-10-12T09:00:02Z", "2026-10-12T09:00:01Z")
    with pytest.raises(ValueError):
        tools.get_logs("M02", "2026-10-12T09:00:00Z", "2026-10-12T09:00:01Z")
    with pytest.raises(ValueError):
        tools.get_inspections("2026-10-12T09:00:00", "2026-10-12T09:00:01Z")


@pytest.mark.parametrize("tool_name", ["get_history", "get_logs", "get_inspections"])
def test_range_tools_reject_start_before_authorized_replay(tool_name):
    args = [] if tool_name == "get_inspections" else ["M01"]
    with pytest.raises(ValueError, match="début du replay"):
        getattr(tools, tool_name)(
            *args, "2026-10-12T08:59:59Z", "2026-10-12T09:00:01Z"
        )
