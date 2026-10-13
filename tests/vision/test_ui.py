from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

from factorypulse.vision import ui


def test_direct_entrypoint_starts_streamlit_when_not_in_app_context(monkeypatch):
    calls = []
    monkeypatch.setattr(ui, "get_script_run_ctx", lambda **kwargs: None)
    monkeypatch.setattr(ui, "launch_ui", lambda: calls.append("server"))
    monkeypatch.setattr(ui, "main", lambda: calls.append("app"))

    ui._run_entrypoint()

    assert calls == ["server"]


def test_streamlit_entrypoint_runs_app_inside_streamlit_context(monkeypatch):
    calls = []
    monkeypatch.setattr(ui, "get_script_run_ctx", lambda **kwargs: object())
    monkeypatch.setattr(ui, "launch_ui", lambda: calls.append("server"))
    monkeypatch.setattr(ui, "main", lambda: calls.append("app"))

    ui._run_entrypoint()

    assert calls == ["app"]


def test_webrtc_frame_is_annotated_and_tracked_without_index_mapping(monkeypatch):
    image = object()
    annotated = object()
    detections = [{"object_type": "bottle", "confidence": 0.9}]
    model = object()
    face_detector = object()
    source = "camera:browser:test-session"
    analysis_calls = []
    tracking_calls = []

    class FakeVideoFrame:
        def to_ndarray(self, *, format):
            assert format == "bgr24"
            return image

        @classmethod
        def from_ndarray(cls, frame_data, *, format):
            assert frame_data is annotated
            assert format == "bgr24"
            return "rendered-video-frame"

    monkeypatch.setattr(
        ui,
        "analyze_frame",
        lambda frame, yolo, haar: (
            analysis_calls.append((frame, yolo, haar)) or (annotated, detections)
        ),
    )
    monkeypatch.setattr(
        ui,
        "track_camera_frame",
        lambda frame, found, camera_source: tracking_calls.append(
            (frame, found, camera_source)
        ),
    )

    result = ui.process_webrtc_frame(
        FakeVideoFrame(), model, face_detector, source
    )

    assert result == "rendered-video-frame"
    assert analysis_calls == [(image, model, face_detector)]
    assert tracking_calls == [(annotated, detections, source)]


def test_camera_uses_browser_webrtc_device_selector_without_periodic_fragment(monkeypatch):
    call_arguments = {}
    streamlit_webrtc = ModuleType("streamlit_webrtc")
    streamlit_webrtc.WebRtcMode = SimpleNamespace(SENDRECV="sendrecv")

    def webrtc_streamer(**kwargs):
        call_arguments.update(kwargs)
        return SimpleNamespace(state=SimpleNamespace(playing=False))

    streamlit_webrtc.webrtc_streamer = webrtc_streamer
    monkeypatch.setitem(__import__("sys").modules, "streamlit_webrtc", streamlit_webrtc)
    monkeypatch.setattr(ui, "load_models", lambda: (object(), object()))
    monkeypatch.setattr(
        ui,
        "st",
        SimpleNamespace(
            session_state={},
            caption=Mock(),
        ),
    )

    ui._camera_controls()

    assert call_arguments["key"] == "factorypulse-camera"
    assert call_arguments["media_stream_constraints"]["video"]["frameRate"] == {
        "ideal": 10,
        "max": 15,
    }
    assert "run_every" not in call_arguments
