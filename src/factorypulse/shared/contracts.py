"""Validation structurelle des événements FP-LAB-1.1 (sans dépendance externe)."""
from __future__ import annotations

from datetime import datetime, timedelta
from numbers import Real
from math import isfinite
from typing import Any

REQUIRED_KEYS = frozenset({
    "event_id", "timestamp_utc", "station_id", "event_type", "source", "payload"
})
STATIONS = {"M01", "Q01", "SERVER"}
SOURCES = {"simulated", "physical_sensor", "camera_analysis"}
EVENT_TYPES = {"telemetry", "inspection", "health", "log"}


class ContractError(ValueError):
    """Une entrée ne respecte pas le contrat de données partagé."""


def parse_utc(value: str) -> datetime:
    """Accepte un horodatage ISO 8601 en UTC terminé par Z."""
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ContractError("timestamp_utc doit être une date ISO 8601 UTC se terminant par Z")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ContractError("timestamp_utc non valide") from exc
    if dt.utcoffset() != timedelta(0):
        raise ContractError("timestamp_utc doit être en UTC")
    return dt


def _is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def _numeric_or_none(value: Any, key: str, low: float | None = None, high: float | None = None) -> None:
    if value is None:
        return
    if not _is_number(value) or not isfinite(value):
        raise ContractError(f"{key} doit être un nombre fini ou null")
    if low is not None and value < low:
        raise ContractError(f"{key} est inférieur au minimum {low}")
    if high is not None and value > high:
        raise ContractError(f"{key} est supérieur au maximum {high}")


def validate_event(event: dict[str, Any]) -> dict[str, Any]:
    """Valide un événement et le renvoie inchangé.

    Les règles métier de persistance, de fraîcheur et de comptage
    relèvent des modules des équipes, pas de ce validateur structurel.
    """
    if not isinstance(event, dict):
        raise ContractError("Un événement doit être un objet JSON")
    if set(event) != REQUIRED_KEYS:
        missing = sorted(REQUIRED_KEYS - set(event))
        extra = sorted(set(event) - REQUIRED_KEYS)
        raise ContractError(f"Clés invalides, manquantes={missing}, supplémentaires={extra}")
    if not isinstance(event["event_id"], str) or not event["event_id"].strip():
        raise ContractError("event_id doit être une chaîne non vide")
    parse_utc(event["timestamp_utc"])
    if not isinstance(event["station_id"], str) or event["station_id"] not in STATIONS:
        raise ContractError("station_id non autorisé")
    if not isinstance(event["event_type"], str) or event["event_type"] not in EVENT_TYPES:
        raise ContractError("event_type non autorisé")
    if not isinstance(event["source"], str) or event["source"] not in SOURCES:
        raise ContractError("source non autorisée")
    payload = event["payload"]
    if not isinstance(payload, dict):
        raise ContractError("payload doit être un objet JSON")

    typ = event["event_type"]
    if typ == "telemetry":
        if event["station_id"] != "M01":
            raise ContractError("telemetry doit venir de M01 dans ce labo")
        required = {"temperature_c", "vibration_rms_g", "machine_state", "data_quality", "alert_level", "alert_reason"}
        if not required.issubset(payload):
            raise ContractError(f"telemetry manque {sorted(required - set(payload))}")
        _numeric_or_none(payload["temperature_c"], "temperature_c")
        _numeric_or_none(payload["vibration_rms_g"], "vibration_rms_g", low=0)
        for key, allowed in {
            "machine_state": {"RUNNING", "STOPPED", "UNKNOWN"},
            "data_quality": {"OK", "TEMPERATURE_MISSING", "VIBRATION_MISSING", "MISSING"},
            "alert_level": {"OK", "WARNING", "DATA_ISSUE"},
        }.items():
            if payload[key] not in allowed:
                raise ContractError(f"{key} non reconnu")
        if payload["alert_reason"] is not None and not isinstance(payload["alert_reason"], str):
            raise ContractError("alert_reason doit être du texte ou null")
    elif typ == "inspection":
        if event["station_id"] != "Q01":
            raise ContractError("inspection doit venir de Q01 dans ce labo")
        required = {"part_id", "object_class", "confidence", "bbox_xyxy", "marker_color", "verdict", "image_path", "image_size_px", "algorithm"}
        if not required.issubset(payload):
            raise ContractError(f"inspection manque {sorted(required - set(payload))}")
        if not isinstance(payload["part_id"], str) or not payload["part_id"]:
            raise ContractError("part_id doit être du texte non vide")
        if payload["object_class"] not in {"bottle", "cup", "unknown"}:
            raise ContractError("object_class non reconnue")
        _numeric_or_none(payload["confidence"], "confidence", low=0, high=1)
        if payload["marker_color"] not in {"green", "red", "unknown"}:
            raise ContractError("marker_color non reconnue")
        if payload["verdict"] not in {"PASS", "REJECT", "UNKNOWN"}:
            raise ContractError("verdict non reconnu")
        bbox = payload["bbox_xyxy"]
        if bbox is not None and (not isinstance(bbox, list) or len(bbox) != 4 or not all(_is_number(n) for n in bbox)):
            raise ContractError("bbox_xyxy doit avoir 4 coordonnées numériques ou null")
        size = payload["image_size_px"]
        if not isinstance(size, list) or len(size) != 2 or not all(_is_number(n) and n > 0 for n in size):
            raise ContractError("image_size_px doit contenir largeur et hauteur positives")
    elif typ == "health":
        required = {"service_state", "cpu_pct", "ram_pct", "mqtt_connected", "uptime_s"}
        if not required.issubset(payload):
            raise ContractError(f"health manque {sorted(required - set(payload))}")
        if payload["service_state"] not in {"RUNNING", "STOPPED", "UNKNOWN"}:
            raise ContractError("service_state non reconnu")
        for key in ("cpu_pct", "ram_pct"):
            _numeric_or_none(payload[key], key, low=0, high=100)
        if payload["mqtt_connected"] is not None and not isinstance(payload["mqtt_connected"], bool):
            raise ContractError("mqtt_connected doit être booléen ou null")
        _numeric_or_none(payload["uptime_s"], "uptime_s", low=0)
    elif typ == "log":
        required = {"service", "level", "code", "message"}
        if not required.issubset(payload):
            raise ContractError(f"log manque {sorted(required - set(payload))}")
        if payload["level"] not in {"INFO", "WARNING", "ERROR"}:
            raise ContractError("level de log non reconnu")
        for key in ("service", "code", "message"):
            if not isinstance(payload[key], str):
                raise ContractError(f"{key} doit être du texte")
    return event
