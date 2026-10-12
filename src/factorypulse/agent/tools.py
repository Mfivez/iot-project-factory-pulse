"""Fonctions locales de consultation des événements FactoryPulse.

Les outils ne prennent aucun chemin fourni par l'appelant et n'effectuent que
des lectures des quatre fixtures autorisées. Ils renvoient les événements
originaux afin que leurs ``event_id`` restent disponibles comme preuves.
"""
from __future__ import annotations

import json
from datetime import datetime
from collections.abc import Callable
from typing import Any

from factorypulse.shared.contracts import ContractError, STATIONS, parse_utc
from factorypulse.shared.jsonl import dedupe_events, read_jsonl
from factorypulse.shared.paths import fixture_path, project_root


_FIXTURE_NAMES = ("m01.jsonl", "q01.jsonl", "systeme.jsonl", "logs.jsonl")
_HISTORY_LIMIT = 500
_LOG_LIMIT = 100
_INSPECTION_LIMIT = 100


def _load_config() -> dict[str, Any]:
    """Charge la configuration locale qui fixe le curseur maximal du replay."""
    config_path = project_root() / "config" / "factorypulse.json"
    with config_path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def _load_events() -> list[dict[str, Any]]:
    """Charge, valide, déduplique et trie les fixtures autorisées."""
    events = [
        event
        for name in _FIXTURE_NAMES
        for event in read_jsonl(fixture_path(name), validate=True)
    ]
    # Dédupliquer après lecture de toutes les sources détecte aussi les
    # collisions d'identifiants entre deux fixtures distinctes.
    return sorted(
        dedupe_events(events),
        key=lambda event: (
            parse_utc(event["timestamp_utc"]),
            event["event_id"],
        ),
    )


def _validate_station(station_id: str) -> None:
    """Refuse toute station qui n'est pas prévue par le contrat partagé."""
    if not isinstance(station_id, str) or station_id not in STATIONS:
        raise ValueError(f"station_id non autorisé : {station_id!r}")


def _format_utc(value: datetime) -> str:
    """Formate une date UTC avec le suffixe Z exigé par les réponses."""
    return value.isoformat().replace("+00:00", "Z")


def _replay_limit(config: dict[str, Any]) -> datetime:
    """Renvoie la borne haute de replay définie par la configuration."""
    return parse_utc(config["replay"]["as_of_utc"])


def _cap_to_replay(
    requested_end: datetime,
    replay_end: datetime,
) -> tuple[datetime, list[str]]:
    """Plafonne une date future au curseur de replay et explique la limite."""
    if requested_end <= replay_end:
        return requested_end, []
    return replay_end, [
        f"La borne supérieure a été limitée à la fin du replay "
        f"({_format_utc(replay_end)})."
    ]


def _events_in_range(
    events: list[dict[str, Any]],
    start: datetime,
    end: datetime,
    predicate: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    """Filtre inclusivement sur l'horodatage et un type/station d'événement."""
    return [
        event for event in events
        if start <= parse_utc(event["timestamp_utc"]) <= end
        and predicate(event)
    ]


def _limited_response(
    as_of: datetime,
    events: list[dict[str, Any]],
    limit: int,
    warnings: list[str],
) -> dict[str, Any]:
    """Construit la réponse commune et avertit quand la limite est dépassée."""
    if len(events) > limit:
        warnings.append(
            f"Résultats tronqués à {limit} événements sur {len(events)}."
        )
    return {
        "as_of_utc": _format_utc(as_of),
        "events": events[:limit],
        "warnings": warnings,
    }


def get_status(station_id: str, at_utc: str) -> dict[str, Any]:
    """Retourne la dernière télémétrie et le dernier signe de vie d'une station.

    ``data_age_s`` est l'âge de la dernière télémétrie à la date effective du
    replay. Il vaut ``None`` pour les stations sans télémétrie, conformément au
    contrat où seule M01 publie ce type d'événement. L'état du nœud est calculé
    avec le dernier événement health et le seuil de fraîcheur configuré.

    Args:
        station_id: M01, Q01 ou SERVER.
        at_utc: Date ISO 8601 UTC terminée par Z.

    Returns:
        Un objet JSON sérialisable contenant la date effective, les événements
        bruts, les avertissements et un résumé des états.

    Raises:
        ValueError: Si la station ou la date n'est pas autorisée/valide.
    """
    _validate_station(station_id)
    requested_at = parse_utc(at_utc)
    config = _load_config()
    as_of, warnings = _cap_to_replay(requested_at, _replay_limit(config))

    station_events = [
        event for event in _load_events()
        if event["station_id"] == station_id
        and parse_utc(event["timestamp_utc"]) <= as_of
    ]
    telemetry = [
        event for event in station_events if event["event_type"] == "telemetry"
    ]
    health = [event for event in station_events if event["event_type"] == "health"]
    latest_telemetry = telemetry[-1] if telemetry else None
    latest_health = health[-1] if health else None

    if latest_telemetry is None:
        warnings.append(f"Aucune télémétrie disponible pour {station_id}.")
        data_age_s = None
        machine_state = "UNKNOWN"
    else:
        telemetry_at = parse_utc(latest_telemetry["timestamp_utc"])
        data_age_s = (as_of - telemetry_at).total_seconds()
        machine_state = latest_telemetry["payload"]["machine_state"]
        data_quality = latest_telemetry["payload"]["data_quality"]
        if data_quality != "OK":
            warnings.append(
                f"La dernière télémétrie de {station_id} signale "
                f"une qualité de données {data_quality}."
            )
        if data_age_s > config["thresholds"]["heartbeat_stale_after_s"]:
            warnings.append(
                f"La dernière télémétrie de {station_id} est périmée "
                f"({data_age_s:g} s)."
            )

    if latest_health is None:
        node_state = "UNKNOWN"
        warnings.append(f"Aucun signe de vie disponible pour {station_id}.")
    else:
        health_at = parse_utc(latest_health["timestamp_utc"])
        health_age_s = (as_of - health_at).total_seconds()
        if health_age_s > config["thresholds"]["heartbeat_stale_after_s"]:
            node_state = "OFFLINE"
            warnings.append(
                f"Le dernier signe de vie de {station_id} est périmé "
                f"({health_age_s:g} s)."
            )
        else:
            # service_state décrit le service qui publie le heartbeat; ce champ
            # n'est jamais utilisé comme substitut de machine_state.
            node_state = latest_health["payload"]["service_state"]

    status_events = [
        event for event in (latest_telemetry, latest_health)
        if event is not None
    ]
    status_events.sort(
        key=lambda event: (
            parse_utc(event["timestamp_utc"]),
            event["event_id"],
        )
    )
    return {
        "as_of_utc": _format_utc(as_of),
        "events": status_events,
        "warnings": warnings,
        "summary": {
            "node_state": node_state,
            "machine_state": machine_state,
            "data_age_s": data_age_s,
        },
    }


def get_history(station_id: str, from_utc: str, to_utc: str) -> dict[str, Any]:
    """Retourne jusqu'à 500 télémétries de la station, bornes comprises."""
    _validate_station(station_id)
    start = parse_utc(from_utc)
    requested_end = parse_utc(to_utc)
    if start > requested_end:
        raise ValueError("from_utc doit être antérieur ou égal à to_utc")

    config = _load_config()
    end, warnings = _cap_to_replay(requested_end, _replay_limit(config))
    if start > end:
        warnings.append("L'intervalle commence après la fin du replay; aucun événement retourné.")
        selected: list[dict[str, Any]] = []
    else:
        selected = _events_in_range(
            _load_events(),
            start,
            end,
            lambda event: (
                event["station_id"] == station_id
                and event["event_type"] == "telemetry"
            ),
        )
        if not selected:
            warnings.append(f"Aucune télémétrie trouvée pour {station_id} dans cet intervalle.")
        else:
            incomplete_count = sum(
                event["payload"]["data_quality"] != "OK"
                for event in selected
            )
            if incomplete_count:
                warnings.append(
                    f"{incomplete_count} télémétrie(s) signalent des données absentes "
                    "ou de qualité dégradée."
                )
    return _limited_response(end, selected, _HISTORY_LIMIT, warnings)


def get_logs(station_id: str, from_utc: str, to_utc: str) -> dict[str, Any]:
    """Retourne jusqu'à 100 logs de station ou du SERVER qui la ciblent."""
    _validate_station(station_id)
    start = parse_utc(from_utc)
    requested_end = parse_utc(to_utc)
    if start > requested_end:
        raise ValueError("from_utc doit être antérieur ou égal à to_utc")

    config = _load_config()
    end, warnings = _cap_to_replay(requested_end, _replay_limit(config))
    if start > end:
        warnings.append("L'intervalle commence après la fin du replay; aucun événement retourné.")
        selected: list[dict[str, Any]] = []
    else:
        selected = _events_in_range(
            _load_events(),
            start,
            end,
            lambda event: (
                event["event_type"] == "log"
                and (
                    event["station_id"] == station_id
                    or (
                        event["station_id"] == "SERVER"
                        and event["payload"].get("target_station") == station_id
                    )
                )
            ),
        )
        if not selected:
            warnings.append(f"Aucun log trouvé pour {station_id} dans cet intervalle.")
    return _limited_response(end, selected, _LOG_LIMIT, warnings)


def get_inspections(from_utc: str, to_utc: str) -> dict[str, Any]:
    """Retourne jusqu'à 100 inspections Q01 uniques, bornes comprises."""
    start = parse_utc(from_utc)
    requested_end = parse_utc(to_utc)
    if start > requested_end:
        raise ValueError("from_utc doit être antérieur ou égal à to_utc")

    config = _load_config()
    end, warnings = _cap_to_replay(requested_end, _replay_limit(config))
    if start > end:
        warnings.append("L'intervalle commence après la fin du replay; aucun événement retourné.")
        selected: list[dict[str, Any]] = []
    else:
        # _load_events déduplique globalement par event_id; les événements
        # renvoyés restent néanmoins les objets d'origine avec leur preuve.
        selected = _events_in_range(
            _load_events(),
            start,
            end,
            lambda event: (
                event["station_id"] == "Q01"
                and event["event_type"] == "inspection"
            ),
        )
        if not selected:
            warnings.append(f"Aucune inspection Q01 trouvée dans cet intervalle.")
    return _limited_response(end, selected, _INSPECTION_LIMIT, warnings)
