"""Interface Streamlit de sélection de caméra ou d'image pour la vision."""

from __future__ import annotations

import sys
import threading
from uuid import uuid4
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
from factorypulse.vision.detector import (
    MODEL_PATH,
    YOLO,
    analyze_frame,
    load_face_detector,
    process_image_frame,
    track_camera_frame,
)
from factorypulse.shared.paths import project_root

_INFERENCE_LOCK = threading.Lock()


@st.cache_resource(show_spinner="Chargement des modèles YOLO et Haar…")
def load_models() -> tuple[YOLO, cv2.CascadeClassifier]:
    """Charge une seule fois les modèles lourds pour la session Streamlit."""
    model = YOLO(str(project_root() / MODEL_PATH))
    return model, load_face_detector()


def _show_image_result(frame: Any) -> None:
    st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), caption="Image annotée")
    st.success("Une image JPEG annotée et une ligne JSONL ont été enregistrées.")


def process_webrtc_frame(
    frame: Any,
    model: YOLO,
    face_detector: cv2.CascadeClassifier,
    source: str,
) -> Any:
    """Analyse une frame WebRTC sans déclencher de rerun Streamlit."""
    image = frame.to_ndarray(format="bgr24")
    with _INFERENCE_LOCK:
        output, detections = analyze_frame(image, model, face_detector)
        track_camera_frame(output, detections, source)
    return type(frame).from_ndarray(output, format="bgr24")


def _camera_controls() -> None:
    """Utilise WebRTC pour un flux continu et la sélection native des appareils."""
    try:
        from streamlit_webrtc import WebRtcMode, webrtc_streamer
    except ImportError:
        st.error(
            "Le flux sans rafraîchissement nécessite streamlit-webrtc. "
            "Mets à jour l'environnement avec uv sync --all-extras."
        )
        return

    model, face_detector = load_models()
    source = st.session_state.setdefault(
        "camera_source", f"camera:browser:{uuid4().hex}"
    )

    def video_frame_callback(frame: Any) -> Any:
        return process_webrtc_frame(frame, model, face_detector, source)

    st.caption("Sélectionne la caméra dans le lecteur, puis autorise son accès.")
    context = webrtc_streamer(
        key="factorypulse-camera",
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={
            "video": {
                "frameRate": {"ideal": 10, "max": 15},
            },
            "audio": False,
        },
        async_processing=True,
        media_toggle_controls=False,
    )
    if context.state.playing:
        st.caption("Caméra active — le flux ne relance pas la page.")


def main() -> None:
    """Affiche les deux choix d'entrée et leurs contrôles spécifiques."""
    st.set_page_config(page_title="FactoryPulse — Vision", layout="wide")
    st.title("FactoryPulse — Vision")
    st.caption("Choisissez une caméra ou une image à analyser.")
    st.session_state.setdefault("input_mode", None)
    st.session_state.setdefault("camera", None)

    camera_column, image_column = st.columns(2)
    if camera_column.button("Caméra", use_container_width=True):
        st.session_state.input_mode = "camera"
    if image_column.button("Image", use_container_width=True):
        if st.session_state.get("camera") is not None:
            st.session_state.camera.release()
            st.session_state.camera = None
        st.session_state.input_mode = "image"
        st.session_state.pop("image_result", None)

    if st.session_state.input_mode == "camera":
        st.subheader("Entrée caméra")
        _camera_controls()

    elif st.session_state.input_mode == "image":
        st.subheader("Entrée image")
        uploaded_image = st.file_uploader(
            "Choisir une image", type=["jpg", "jpeg", "png", "bmp", "webp"]
        )
        if uploaded_image is not None:
            if st.button("Analyser l'image", type="primary"):
                try:
                    model, face_detector = load_models()
                    image_bytes = np.frombuffer(uploaded_image.getvalue(), dtype=np.uint8)
                    frame = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
                    if frame is None:
                        raise ValueError("Le fichier choisi n'est pas une image lisible.")
                    output = process_image_frame(
                        frame,
                        model,
                        face_detector,
                        input_image_path=uploaded_image.name,
                    )
                    st.session_state.image_result = output
                except Exception as exc:
                    st.error(f"Échec de l'analyse : {exc}")
        if st.session_state.get("image_result") is not None:
            _show_image_result(st.session_state.image_result)


def launch_ui() -> None:
    """Démarre le serveur Streamlit pour la page de choix vision."""
    import streamlit.web.cli as stcli

    ui_path = Path(__file__).resolve()
    sys.argv = ["streamlit", "run", str(ui_path)]
    stcli.main()


def _run_entrypoint() -> None:
    """Lance Streamlit hors runner, ou exécute l'app dans son contexte web."""
    if get_script_run_ctx(suppress_warning=True) is None:
        launch_ui()
    else:
        main()


if __name__ == "__main__":
    _run_entrypoint()
