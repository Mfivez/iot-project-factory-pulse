"""Réception visuelle de deux flux MJPEG, sans acquisition ni inférence.

Les URL sont ouvertes par le navigateur. Aucune donnée de décision machine
n'est déduite de la réception d'une image.
"""
from pathlib import Path
from urllib.parse import urlsplit


def validate_stream_url(value: str) -> str:
    """Autorise une adresse HTTP(S) explicite, ou une source débranchée."""
    value = value.strip()
    if not value:
        return ""
    if any(char.isspace() or ord(char) < 32 for char in value):
        raise ValueError("L'adresse du flux ne doit pas contenir d'espace.")
    if any(char in value for char in '<>"\\'):
        raise ValueError("L'adresse du flux contient un caractère interdit.")
    try:
        parts = urlsplit(value)
        port = parts.port
        host = parts.hostname
    except ValueError as exc:
        raise ValueError("L'adresse ou le port du flux est invalide.") from exc
    if parts.scheme not in {"http", "https"} or not host:
        raise ValueError("Utilise une adresse complète commençant par http:// ou https://.")
    if parts.username is not None or parts.password is not None:
        raise ValueError("Ne place pas d'identifiants dans l'adresse du flux.")
    if parts.fragment or port == 0:
        raise ValueError("Utilise l'adresse directe du flux, sans fragment et avec un port valide.")
    return value


def render_preview(url: str, camera_id: str, paused: bool = False) -> None:
    """Un lecteur indépendant par caméra, avec état observé dans le navigateur."""
    import streamlit.components.v1 as components

    preview = components.declare_component(
        "factorypulse_camera_preview",
        path=str(Path(__file__).with_name("camera_preview")),
    )
    preview(url=validate_stream_url(url), camera_id=camera_id,
            paused=paused, key=f"preview_{camera_id}", default=None)


def _render_settings(st, urls) -> None:
    """Configuration à part : aucun formulaire n'allonge la vue des caméras."""
    st.session_state.setdefault("camera_url1_input", urls[0])
    st.session_state.setdefault("camera_url2_input", urls[1])
    with st.container(border=True):
        st.subheader("Sources vidéo")
        st.caption("Adresses HTTP(S) directes des flux MJPEG du poste vision, accessibles depuis ce navigateur.")
        with st.form("camera_sources", border=False):
            c1, c2 = st.columns(2)
            url1 = c1.text_input("Flux caméra 1 · plateau", key="camera_url1_input",
                                placeholder="http://pc-vision:8080/camera1.mjpg")
            url2 = c2.text_input("Flux caméra 2 · pays", key="camera_url2_input",
                                placeholder="http://pc-vision:8080/camera2.mjpg")
            submitted = st.form_submit_button("Appliquer les sources", type="primary")
        if submitted:
            try:
                urls = (validate_stream_url(url1), validate_stream_url(url2))
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state.camera_stream_urls = urls
                st.success("Sources mises à jour. La réception est indiquée dans chaque lecteur.")
        st.caption(
            "Laissez une adresse vide pour débrancher un aperçu. "
            "La configuration est conservée uniquement dans cette session."
        )
    with st.container(border=True):
        st.subheader("Pour raccorder le poste vision")
        st.markdown("1. Publier les images déjà capturées sous forme de deux flux MJPEG.\n"
                    "2. Utiliser l'adresse réseau du PC vision si vous consultez depuis un autre poste.\n"
                    "3. Vérifier chaque aperçu dans l'onglet **Caméras**.")
        st.caption("RTSP, pages WebRTC et index USB ne sont pas pris en charge ici. "
                   "Une page HTTPS exige des flux HTTPS. Aucun modèle n'est chargé par le dashboard.")


def _render_camera_tab(st, urls) -> None:
    # Valeur durable : le widget est démonté lors d'un changement d'onglet.
    st.session_state.setdefault("camera_previews_paused", False)
    st.session_state.setdefault("_camera_pause_widget", st.session_state.camera_previews_paused)
    paused = st.toggle("Suspendre les aperçus", key="_camera_pause_widget",
                       help="Ferme les flux dans cette page. Le traitement vision et la machine ne sont pas commandés ici.")
    st.session_state.camera_previews_paused = paused
    left, right = st.columns(2, gap="medium")
    for column, number, title, subtitle, url in (
        (left, "01", "Contrôle d'entrée", "Pièce ou objet", urls[0]),
        (right, "02", "Identification du pays", "Face nationale · pièce de 2 €", urls[1]),
    ):
        with column.container(border=True):
            st.markdown(f'<div class="fp-camera-heading"><span class="fp-camera-number">{number}</span>'
                        f'<div><strong>{title}</strong><small>{subtitle}</small></div>'
                        '<span class="fp-chip">CAMÉRA</span></div>', unsafe_allow_html=True)
            render_preview(url, number, paused)


def render_workshop(st) -> None:
    """Une seule section active ; les lecteurs sont libérés hors de Caméras."""
    st.title("Flux caméras")
    st.caption("Les deux vues du poste vision.")
    urls = st.session_state.setdefault("camera_stream_urls", ("", ""))
    if st.session_state.get("workshop_tab") not in ("Caméras", "Réglages"):
        st.session_state.workshop_tab = "Caméras"
    tab = st.radio("Sections de l'atelier", ("Caméras", "Réglages"),
                   horizontal=True, label_visibility="collapsed", key="workshop_tab")
    if tab == "Caméras":
        _render_camera_tab(st, urls)
    else:
        _render_settings(st, urls)
