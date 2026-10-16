"""Le dashboard distingue images reçues, sources configurées et données absentes."""
from pathlib import Path

import pytest

from factorypulse.dashboard.cameras import validate_stream_url


@pytest.mark.parametrize("url", ["", "http://192.168.1.20:8080/camera1.mjpg",
                                "https://vision.example/cam?view=2", "http://[::1]:8080/cam"])
def test_stream_addresses_allow_local_network_and_disconnected_sources(url):
    assert validate_stream_url(f" {url} ") == url


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///etc/passwd", "rtsp://camera/live",
                                "http://", "http://camera:invalid/live", "http://camera:99999/live",
                                "http://user:secret@camera/live", 'http://camera/" onerror="alert(1)',
                                "http://camera/with space", "http://camera/\nimage", "http://camera/#x"])
def test_invalid_sources_are_rejected_before_render(url):
    with pytest.raises(ValueError):
        validate_stream_url(url)


def dashboard(initial_state=None):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    path = Path(__file__).resolve().parents[2] / "src/factorypulse/dashboard/app.py"
    app = AppTest.from_file(str(path), default_timeout=15)
    for key, value in (initial_state or {}).items():
        app.session_state[key] = value
    return app.run()


def test_workshop_starts_without_inference_or_simulated_results():
    app = dashboard()
    assert not app.exception
    assert app.title[0].value == "Flux caméras"
    assert not app.metric
    assert len(app.radio) == 1
    assert app.radio[0].options == ["Caméras", "Réglages"]
    assert len(app.get("component_instance")) == 2
    assert app.session_state["camera_stream_urls"] == ("", "")
    assert not app.slider  # Pas d'horloge de replay mélangée à la vue atelier.


def test_sources_apply_together_and_invalid_input_preserves_previous_configuration():
    app = dashboard()
    app.radio(key="workshop_tab").set_value("Réglages").run()
    app.text_input[0].set_value("http://pc-vision:8080/cam1.mjpg")
    app.text_input[1].set_value("http://pc-vision:8080/cam2.mjpg")
    app.button[0].click().run()
    assert not app.exception
    previous = app.session_state["camera_stream_urls"]
    app.text_input[1].set_value("javascript:alert(1)")
    app.button[0].click().run()
    assert app.error
    assert app.session_state["camera_stream_urls"] == previous
    app.radio(key="workshop_tab").set_value("Caméras").run()
    assert not app.metric  # Les sources vidéo n'apportent aucune mesure moteur.
    assert len(app.get("component_instance")) == 2
    app.radio(key="workshop_tab").set_value("Réglages").run()
    assert [field.value for field in app.text_input] == list(previous)


def test_tabs_isolate_content_and_preserve_pause_without_starting_hidden_players():
    app = dashboard()
    app.toggle[0].set_value(True).run()
    app.radio(key="workshop_tab").set_value("Réglages").run()
    assert not app.exception
    assert not app.get("component_instance")
    assert app.session_state["camera_previews_paused"] is True
    app.radio(key="workshop_tab").set_value("Caméras").run()
    assert app.toggle[0].value is True
    assert len(app.get("component_instance")) == 2


@pytest.mark.parametrize("removed_tab", ["Cycle & équipements", "Historique"])
def test_previous_session_returns_to_cameras_without_loading_replay(monkeypatch, removed_tab):
    from factorypulse.dashboard import readers

    def unexpected_fixture_read():
        pytest.fail("La vue caméra ne doit pas charger les fixtures du replay.")

    monkeypatch.setattr(readers, "load_dashboard_events", unexpected_fixture_read)
    app = dashboard({"workspace": "Replay pédagogique", "workshop_tab": removed_tab})
    assert not app.exception
    assert app.radio(key="workshop_tab").value == "Caméras"
    assert len(app.get("component_instance")) == 2
    assert not app.slider
    assert not app.metric
