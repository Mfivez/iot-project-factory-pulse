"""Interface Streamlit consacrée aux deux flux vidéo du poste vision."""
from pathlib import Path

from factorypulse.dashboard.cameras import render_workshop


def main() -> None:
    """Affiche les caméras et leurs réglages, sans charger le replay."""
    try:
        import streamlit as st
    except ImportError as exc:
        raise SystemExit('Installer les dépendances : pip install -e ".[dashboard,dev]"') from exc

    st.set_page_config(page_title="FactoryPulse | Caméras", page_icon="🏭", layout="wide")
    st.markdown(
        "<style>" + Path(__file__).with_name("style.css").read_text(encoding="utf-8") + "</style>",
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.markdown('<div class="fp-brand"><b>f</b><div>Factory<span>Pulse</span>'
                    '<small>Le tri, simplement.</small></div></div>', unsafe_allow_html=True)
        st.caption("VUE CAMÉRAS")
        st.divider()
        st.markdown('<div class="fp-sidebar-note">LES DEUX POSTES<br><strong>01</strong> Contrôle d’entrée<br>'
                    '<strong>02</strong> Pays d’émission</div>'
                    '<div class="fp-sidebar-bottom"><b>Poste vision</b><br>'
                    'Deux flux vidéo</div>', unsafe_allow_html=True)
    st.markdown('<div class="fp-topbar"><span>FactoryPulse / Caméras</span>'
                '<span class="fp-chip">VISION</span></div>', unsafe_allow_html=True)
    render_workshop(st)


if __name__ == "__main__":
    main()
