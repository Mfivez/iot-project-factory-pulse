"""Shared status calculations for dashboard and read-only agent tools."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from factorypulse.shared.contracts import STATIONS, parse_utc


def summarize_station(
    events: Iterable[dict[str, Any]],
    station_id: str,
    as_of: datetime,
    stale_after_s: int,
) -> dict[str, Any]:
    """Summarize machine, sensor, and node states from events up to ``as_of``.

    ``machine_state`` and ``sensor_state`` come from the latest telemetry,
    while ``node_state`` comes independently from the latest health heartbeat.
    Missing telemetry or heartbeat yields ``UNKNOWN``; an old heartbeat yields
    ``OFFLINE`` according to the replay clock, never the system clock.

    The source events and their ages are included so callers can retain event
    provenance and produce their own presentation or response format.
    """
    if not isinstance(station_id, str) or station_id not in STATIONS:
        raise ValueError(f"station_id non autorisé : {station_id!r}")
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of doit inclure un fuseau horaire")
    if stale_after_s < 0:
        raise ValueError("stale_after_s doit être positif ou nul")

    latest_telemetry = None
    latest_health = None
    for event in events:
        if event["station_id"] != station_id:
            continue
        event_at = parse_utc(event["timestamp_utc"])
        if event_at > as_of:
            continue
        if event["event_type"] == "telemetry":
            if (
                latest_telemetry is None
                or event_at > parse_utc(latest_telemetry["timestamp_utc"])
            ):
                latest_telemetry = event
        elif event["event_type"] == "health":
            if latest_health is None or event_at > parse_utc(
                latest_health["timestamp_utc"]
            ):
                latest_health = event

    telemetry_age_s = None
    if latest_telemetry is None:
        machine_state = "UNKNOWN"
        sensor_state = "UNKNOWN"
    else:
        telemetry_age_s = (
            as_of - parse_utc(latest_telemetry["timestamp_utc"])
        ).total_seconds()
        machine_state = latest_telemetry["payload"]["machine_state"]
        sensor_state = (
            "OK"
            if latest_telemetry["payload"]["data_quality"] == "OK"
            else "DATA_ISSUE"
        )

    health_age_s = None
    if latest_health is None:
        node_state = "UNKNOWN"
    else:
        health_age_s = (as_of - parse_utc(latest_health["timestamp_utc"])).total_seconds()
        if health_age_s > stale_after_s:
            node_state = "OFFLINE"
        else:
            node_state = latest_health["payload"]["service_state"]

    return {
        "node_state": node_state,
        "machine_state": machine_state,
        "sensor_state": sensor_state,
        "data_age_s": telemetry_age_s,
        "health_age_s": health_age_s,
        "telemetry_event": latest_telemetry,
        "health_event": latest_health,
    }
