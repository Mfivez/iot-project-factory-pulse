"""Chargement et préparation des événements affichés par le dashboard.

Ce module ne dépend pas de Streamlit : ses fonctions restent ainsi faciles à
tester séparément de l'interface graphique.
"""
from datetime import datetime
from typing import Any

from factorypulse.shared.contracts import parse_utc
from factorypulse.shared.jsonl import read_jsonl, dedupe_events
from factorypulse.shared.paths import fixture_path


# Charger les quatre fichiers donne au dashboard une vue cohérente du replay :
# télémétrie, inspections, signes de vie des nœuds et logs.
FIXTURE_NAMES = ("m01.jsonl", "q01.jsonl", "systeme.jsonl", "logs.jsonl")


def load_fixture(name: str, deduplicate: bool = True) -> list[dict[str, Any]]:
    """Lit une fixture autorisée et, par défaut, supprime ses doublons exacts.

    Args:
        name: Nom d'un fichier de fixture autorisé par ``fixture_path``.
        deduplicate: Si vrai, ignore les répétitions exactes et refuse les
            collisions où un même ``event_id`` désigne deux contenus différents.

    Returns:
        Les événements lus, dans leur ordre d'origine.
    """
    events = read_jsonl(fixture_path(name))
    return dedupe_events(events) if deduplicate else events


def load_dashboard_events() -> list[dict[str, Any]]:
    """Charge et trie chronologiquement tous les événements des fixtures.

    La déduplication est faite après la lecture de toutes les sources afin de
    détecter aussi une collision d'``event_id`` entre deux fichiers distincts.
    Une répétition identique ne compte qu'une fois. Les collisions
    contradictoires sont signalées par le validateur partagé, jamais masquées.
    """
    events = [
        event
        for name in FIXTURE_NAMES
        for event in load_fixture(name, deduplicate=False)
    ]
    # Le second critère rend l'ordre stable lorsque deux événements partagent
    # le même horodatage.
    return sorted(dedupe_events(events), key=lambda event: (
        parse_utc(event["timestamp_utc"]),
        event["event_id"],
    ))


def events_at(
    events: list[dict[str, Any]], as_of: datetime
) -> list[dict[str, Any]]:
    """Retourne les événements déjà survenus à la position du replay.

    La comparaison est inclusive : un événement horodaté exactement à ``as_of``
    est visible. L'horloge courante de l'ordinateur n'intervient pas.
    """
    return [
        event for event in events
        if parse_utc(event["timestamp_utc"]) <= as_of
    ]


def station_health(
    events: list[dict[str, Any]], as_of: datetime, stale_after_s: int
) -> dict[str, dict[str, Any]]:
    """Détermine l'état des trois nœuds à partir de leurs signes de vie.

    Seuls les événements ``health`` antérieurs ou égaux à ``as_of`` sont pris
    en compte. Si aucun signe de vie n'existe, l'état est ``UNKNOWN``. Sinon,
    le nœud est ``OFFLINE`` quand son dernier signe de vie est plus ancien que
    ``stale_after_s`` secondes dans le replay; cette règle ne dépend pas de
    l'heure réelle de l'ordinateur.

    Le signe de vie décrit le nœud, pas la machine ni la qualité de ses
    capteurs. Le dictionnaire renvoyé conserve l'événement source pour garder
    sa provenance.
    """
    stations = ("M01", "Q01", "SERVER")
    health_by_station = {
        station: [
            event for event in events
            if event["station_id"] == station
            and event["event_type"] == "health"
            and parse_utc(event["timestamp_utc"]) <= as_of
        ]
        for station in stations
    }
    result = {}
    for station, health_events in health_by_station.items():
        if not health_events:
            result[station] = {
                "state": "UNKNOWN",
                "last_seen_utc": None,
                "event_id": None,
            }
            continue
        latest = max(health_events, key=lambda event: parse_utc(event["timestamp_utc"]))
        last_seen = parse_utc(latest["timestamp_utc"])
        # La fraîcheur est évaluée par rapport au curseur de replay, pas à
        # datetime.now(), ce qui rend le résultat rejouable et déterministe.
        stale = (as_of - last_seen).total_seconds() > stale_after_s
        result[station] = {
            "state": "OFFLINE" if stale else latest["payload"]["service_state"],
            "last_seen_utc": latest["timestamp_utc"],
            "event_id": latest["event_id"],
            "event": latest,
        }
    return result


def machine_status(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Résume la dernière télémétrie sans confondre trois états différents.

    ``machine_state`` décrit si la machine est RUNNING ou STOPPED.
    ``sensor_state`` indique DATA_ISSUE si la qualité de la dernière mesure
    n'est pas OK. L'état du nœud, basé sur les événements ``health``, est
    calculé séparément par :func:`station_health`.

    L'événement utilisé est inclus dans le résultat afin de garder accès à sa
    preuve et à son horodatage. En l'absence de télémétrie, les états sont
    ``UNKNOWN`` plutôt que supposés.
    """
    telemetry = [
        event for event in events
        if event["station_id"] == "M01" and event["event_type"] == "telemetry"
    ]
    if not telemetry:
        return {"machine_state": "UNKNOWN", "sensor_state": "UNKNOWN", "event": None}
    latest = max(telemetry, key=lambda event: parse_utc(event["timestamp_utc"]))
    quality = latest["payload"]["data_quality"]
    return {
        "machine_state": latest["payload"]["machine_state"],
        # Une valeur de capteur manquante est un problème de données, pas une
        # mesure égale à zéro ni une indication que la machine est arrêtée.
        "sensor_state": "DATA_ISSUE" if quality != "OK" else "OK",
        "event": latest,
    }


def build_incidents(
    events: list[dict[str, Any]],
    as_of: datetime,
    stale_after_s: int,
) -> list[dict[str, Any]]:
    """Construit une liste d'incidents et conserve leurs événements de preuve.

    Les télémétries signalant autre chose que OK, les logs WARNING/ERROR et les
    services déclarés STOPPED deviennent des incidents. Les événements ayant
    la même station, le même niveau et le même détail sont regroupés : leur
    nombre, leur premier/dernier horodatage et tous leurs ``event_id`` sont
    conservés.

    Les nœuds dont le signe de vie est périmé à ``as_of`` reçoivent aussi un
    incident OFFLINE. Chaque ligne produite peut ainsi être reliée aux données
    JSONL d'origine; aucun diagnostic matériel supplémentaire n'est inventé.
    """
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for event in events:
        payload = event["payload"]
        if event["event_type"] == "telemetry" and payload["alert_level"] != "OK":
            level = payload["alert_level"]
            detail = payload["alert_reason"] or level
        elif event["event_type"] == "log" and payload["level"] in {"WARNING", "ERROR"}:
            level = payload["level"]
            detail = f'{payload["code"]} — {payload["message"]}'
        elif event["event_type"] == "health" and payload["service_state"] == "STOPPED":
            level = "STOPPED"
            detail = "Service déclaré arrêté"
        else:
            continue

        # Cette clé rassemble les répétitions du même problème sans fusionner
        # des incidents de stations ou de causes différentes.
        key = (event["station_id"], level, detail)
        incident = grouped.get(key)
        if incident is None:
            grouped[key] = {
                "station_id": event["station_id"],
                "level": level,
                "detail": detail,
                "first_seen_utc": event["timestamp_utc"],
                "last_seen_utc": event["timestamp_utc"],
                "occurrences": 1,
                "evidence_event_ids": [event["event_id"]],
            }
            continue
        incident["last_seen_utc"] = event["timestamp_utc"]
        incident["occurrences"] += 1
        incident["evidence_event_ids"].append(event["event_id"])

    # L'incident OFFLINE cite comme preuve le dernier signe de vie connu :
    # c'est son ancienneté dans le replay qui permet de le qualifier de périmé.
    for station, health in station_health(events, as_of, stale_after_s).items():
        if health["state"] == "OFFLINE":
            grouped[(station, "OFFLINE", "Signe de vie périmé")] = {
                "station_id": station,
                "level": "OFFLINE",
                "detail": "Signe de vie périmé",
                "first_seen_utc": health["last_seen_utc"],
                "last_seen_utc": health["last_seen_utc"],
                "occurrences": 1,
                "evidence_event_ids": [health["event_id"]],
            }

    return sorted(
        grouped.values(),
        key=lambda incident: (incident["last_seen_utc"], incident["station_id"]),
        reverse=True,
    )
