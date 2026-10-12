"""Interface Streamlit de consultation du replay synthétique FactoryPulse.

L'interface affiche des données de démonstration, et non des mesures en direct.
La logique de lecture et de préparation des événements se trouve dans
``readers.py`` afin de pouvoir être testée sans exécuter Streamlit.
"""
import json
from datetime import timedelta

from factorypulse.dashboard.readers import (
    build_incidents,
    events_at,
    load_dashboard_events,
    machine_status,
    station_health,
)
from factorypulse.shared.contracts import parse_utc
from factorypulse.shared.paths import project_root


def main() -> None:
    """Charge les données puis affiche les indicateurs du replay sélectionné."""
    try:
        import streamlit as st
        import pandas as pd
    except ImportError as exc:
        raise SystemExit('Installer les dépendances : pip install -e ".[dashboard,dev]"') from exc

    st.set_page_config(page_title="FactoryPulse | Labo", page_icon="🏭", layout="wide")
    st.title("🏭 FactoryPulse")
    st.info(
        "REPLAY SYNTHÉTIQUE — ces données ne proviennent pas de capteurs en direct. "
        "Les horodatages sont ceux du replay, jamais ceux de l'ordinateur."
    )

    # Une erreur de configuration ou de lecture doit être visible plutôt que
    # de présenter un dashboard partiel comme si son contenu était complet.
    try:
        root = project_root()
        config = json.loads(
            (root / "config" / "factorypulse.json").read_text(encoding="utf-8")
        )
        all_events = load_dashboard_events()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        st.error(f"Impossible de charger la configuration ou les fixtures : {exc}")
        st.stop()

    # Le curseur parcourt l'intervalle déclaré dans la configuration. Toutes
    # les sections suivantes utilisent la même position de replay.
    replay_start = parse_utc(config["replay"]["start_utc"])
    replay_end = parse_utc(config["replay"]["as_of_utc"])
    replay_duration_s = int((replay_end - replay_start).total_seconds())
    offset_s = st.slider(
        "Position dans le replay",
        min_value=0,
        max_value=replay_duration_s,
        value=replay_duration_s,
        format="%d s",
        help="Déplacez le curseur pour rejouer l'état connu à cet instant.",
    )
    as_of = replay_start + timedelta(seconds=offset_s)
    as_of_text = as_of.strftime("%Y-%m-%dT%H:%M:%SZ")
    replay_events = events_at(all_events, as_of)
    stale_after_s = config["thresholds"]["heartbeat_stale_after_s"]

    st.caption(
        f"Horloge du replay : **{as_of_text}** · "
        f"{len(replay_events):,} événements connus à cet instant"
    )

    telemetry = [
        event for event in replay_events
        if event["station_id"] == "M01" and event["event_type"] == "telemetry"
    ]
    inspections = [
        event for event in replay_events
        if event["station_id"] == "Q01" and event["event_type"] == "inspection"
    ]
    # Le jeu contient déjà des inspections dédupliquées par event_id : chaque
    # pièce représente donc une inspection unique, pas une ligne de transport.
    latest_telemetry = max(
        telemetry,
        key=lambda event: parse_utc(event["timestamp_utc"]),
        default=None,
    )
    machine = machine_status(replay_events)
    nodes = station_health(replay_events, as_of, stale_after_s)
    pass_count = sum(event["payload"]["verdict"] == "PASS" for event in inspections)

    st.subheader("Vue d'ensemble")
    metrics = st.columns(4)
    metrics[0].metric("Mesures M01", f"{len(telemetry):,}")
    metrics[1].metric("État machine", machine["machine_state"])
    metrics[2].metric("État capteur", machine["sensor_state"])
    metrics[3].metric("Inspections Q01 uniques", f"{len(inspections):,}")
    if latest_telemetry:
        st.caption(f"Dernière mesure M01 : {latest_telemetry['timestamp_utc']}")
    else:
        st.caption("Aucune mesure M01 n'a encore été rejouée.")
    st.caption(
        f"État machine et état du capteur proviennent de la dernière télémétrie. "
        f"Un signe de vie est périmé après {stale_after_s} s."
    )

    st.subheader("Disponibilité des nœuds")
    node_columns = st.columns(3)
    for column, station in zip(node_columns, ("M01", "Q01", "SERVER")):
        node = nodes[station]
        column.metric(f"{station} · nœud", node["state"])
        last_seen = node["last_seen_utc"] or "Aucun signe de vie"
        column.caption(f"Dernier signe de vie : {last_seen}")

    st.subheader("Télémétrie M01")
    if telemetry:
        # Pandas conserve les valeurs nulles comme manquantes; on ne les
        # remplace pas par zéro, car cela fausserait les courbes.
        telemetry_frame = pd.DataFrame([
            {
                "UTC": parse_utc(event["timestamp_utc"]),
                "Température (°C)": event["payload"]["temperature_c"],
                "Vibration RMS (g)": event["payload"]["vibration_rms_g"],
            }
            for event in telemetry
        ]).set_index("UTC")
        temperature, vibration = st.columns(2)
        temperature.markdown("**Température (°C)**")
        temperature.line_chart(telemetry_frame[["Température (°C)"]])
        temperature.caption(
            f"Seuil d'alerte pédagogique : > {config['thresholds']['temperature_c_gt']} °C"
        )
        vibration.markdown("**Vibration RMS (g)**")
        vibration.line_chart(telemetry_frame[["Vibration RMS (g)"]])
        vibration.caption(
            f"Seuil d'alerte pédagogique : > "
            f"{config['thresholds']['vibration_rms_g_gt']} g"
        )
        st.caption("Les valeurs manquantes restent absentes dans les séries.")
    else:
        st.info("Aucune télémétrie disponible à cette position du replay.")

    st.subheader("Inspections Q01")
    verdict_counts = {
        verdict: sum(event["payload"]["verdict"] == verdict for event in inspections)
        for verdict in ("PASS", "REJECT", "UNKNOWN")
    }
    verdict_columns = st.columns(3)
    verdict_columns[0].metric("PASS", verdict_counts["PASS"])
    verdict_columns[1].metric("REJECT", verdict_counts["REJECT"])
    verdict_columns[2].metric("UNKNOWN", verdict_counts["UNKNOWN"])
    st.caption(f"Pièces conformes : {pass_count} / {len(inspections)} inspections uniques.")
    verdict_filter = st.selectbox(
        "Filtrer les inspections",
        ("Toutes", "PASS", "REJECT", "UNKNOWN"),
    )
    # Le filtre affecte le tableau détaillé uniquement; les compteurs ci-dessus
    # restent ceux de l'ensemble des inspections visibles dans le replay.
    visible_inspections = [
        event for event in inspections
        if verdict_filter == "Toutes" or event["payload"]["verdict"] == verdict_filter
    ]
    inspection_rows = [
        {
            "UTC": event["timestamp_utc"],
            "event_id": event["event_id"],
            "Pièce": event["payload"]["part_id"],
            "Objet": event["payload"]["object_class"],
            "Confiance": event["payload"]["confidence"],
            "Repère": event["payload"]["marker_color"],
            "Verdict": event["payload"]["verdict"],
            "Algorithme": event["payload"]["algorithm"],
        }
        for event in visible_inspections
    ]
    if inspection_rows:
        st.dataframe(pd.DataFrame(inspection_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Aucune inspection ne correspond à ce filtre à cet instant du replay.")

    st.subheader("Incidents et alertes")
    incidents = build_incidents(replay_events, as_of, stale_after_s)
    if incidents:
        # Les identifiants affichés permettent de retrouver les événements
        # bruts qui justifient chaque incident.
        incident_rows = [
            {
                "Station": incident["station_id"],
                "Niveau": incident["level"],
                "Détail": incident["detail"],
                "Début UTC": incident["first_seen_utc"],
                "Dernier événement UTC": incident["last_seen_utc"],
                "Occurrences": incident["occurrences"],
                "event_id sources": ", ".join(incident["evidence_event_ids"]),
            }
            for incident in incidents
        ]
        st.dataframe(pd.DataFrame(incident_rows), use_container_width=True, hide_index=True)
    else:
        st.success("Aucun incident ni avertissement enregistré jusqu'à cet instant.")

    st.caption(
        "Les lignes affichées sont des événements synthétiques dédupliqués par event_id. "
        "Les données brutes des fixtures ne sont pas modifiées."
    )


if __name__ == "__main__":
    main()
