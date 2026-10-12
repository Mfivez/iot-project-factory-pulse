"""Interface minimale de replay. Les équipes enrichissent graphes et alertes."""
import json
from factorypulse.dashboard.readers import load_fixture
from factorypulse.shared.paths import project_root


def main():
    try:
        import streamlit as st
        import pandas as pd
    except ImportError as exc:
        raise SystemExit('Installer les dépendances : pip install -e ".[dashboard,dev]"') from exc

    config = json.loads((project_root()/"config/factorypulse.json").read_text(encoding="utf-8"))
    st.set_page_config(page_title="FactoryPulse | Labo", page_icon="🏭", layout="wide")
    st.title("🏭 FactoryPulse")
    st.info("REPLAY SYNTHÉTIQUE : les données affichées ne proviennent pas des capteurs en direct.")
    st.caption("Horloge de replay : " + config["replay"]["as_of_utc"])

    telemetry = load_fixture("m01.jsonl")
    inspections = load_fixture("q01.jsonl")
    col1, col2, col3 = st.columns(3)
    col1.metric("Mesures M01", len(telemetry))
    col2.metric("Inspections uniques Q01", len(inspections))
    col3.metric("Pièces PASS", sum(e["payload"]["verdict"] == "PASS" for e in inspections))
    if telemetry:
        df = pd.DataFrame([
            {"UTC": e["timestamp_utc"], "Température (°C)": e["payload"]["temperature_c"],
             "Vibration RMS (g)": e["payload"]["vibration_rms_g"]}
            for e in telemetry
        ]).set_index("UTC")
        st.subheader("Mesures machine M01")
        st.line_chart(df)
    st.subheader("Inspections Q01")
    st.dataframe(pd.DataFrame([e["payload"] for e in inspections]), use_container_width=True)
    st.caption("À développer : curseur de replay, état du noeud, journal d'alertes, intégration agent.")


if __name__ == "__main__":
    main()
