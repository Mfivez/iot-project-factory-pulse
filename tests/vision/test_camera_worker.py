"""Deux caméras en parallèle : envoi unique par pièce, caméra absente sans plantage, requête vers le Pi."""
import queue
import threading
from types import SimpleNamespace

import pytest

from factorypulse.vision import camera_worker
from factorypulse.vision.camera_worker import CoinTrigger, Detection
from factorypulse.vision import main as vision_main
from factorypulse.vision.main import build_request


def coin(label="euro", conf=0.95, sure=True):
    return SimpleNamespace(label=label, conf=conf, sure=sure)


def test_coin_is_sent_once_while_it_stays_in_view():
    trigger = CoinTrigger(conf=0.85, rearm_frames=3)
    sent = [trigger.update([coin()]) for _ in range(10)]
    assert [c for c in sent if c is not None] == [sent[0]]


def test_trigger_rearms_after_coin_leaves():
    trigger = CoinTrigger(conf=0.85, rearm_frames=3)
    assert trigger.update([coin("euro")]) is not None
    for _ in range(2):
        trigger.update([])
    assert trigger.update([coin("piece")]) is None  # pas encore réarmé
    for _ in range(3):
        trigger.update([])
    assert trigger.update([coin("piece")]).label == "piece"


def test_uncertain_or_low_confidence_coin_is_not_sent():
    trigger = CoinTrigger(conf=0.85)
    assert trigger.update([coin(conf=0.70)]) is None
    assert trigger.update([coin(conf=0.95, sure=False)]) is None
    assert trigger.armed


def test_most_confident_coin_is_sent():
    trigger = CoinTrigger(conf=0.85)
    assert trigger.update([coin("piece", 0.86), coin("euro", 0.97)]).label == "euro"


@pytest.mark.parametrize(("kind", "route"), [("euro", "/resultat1"), ("pays", "/resultat2")])
def test_request_targets_the_route_of_each_model(kind, route):
    url, payload = build_request("http://192.168.50.2:8000/servo", Detection(kind, "Belgique", 0.9))
    assert url == f"http://192.168.50.2:8000/servo{route}"
    assert payload == {"result": "Belgique"}  # texte JSON, pas un objet Future


def test_default_cameras_match_the_bench():
    assert (vision_main.CAM_EURO, vision_main.CAM_PAYS) == (1, 0)


def test_missing_camera_retries_without_crashing(monkeypatch):
    attempts = []
    stop = threading.Event()

    def absent(index):
        attempts.append(index)
        if len(attempts) == 3:
            stop.set()
        return None

    monkeypatch.setattr("factorypulse.vision.camera.open_camera", absent)
    monkeypatch.setattr(camera_worker, "_make_detector", lambda kind: (None, None))
    camera_worker.run_camera("euro", 1, queue.Queue(), stop, show=False, retry_delay=0)
    assert attempts == [1, 1, 1]


def test_camera_loop_sends_detection_and_reconnects_after_lost_frame(monkeypatch):
    stop = threading.Event()
    results = queue.Queue()

    class FakeCap:
        def __init__(self):
            self.frames = [True, True, False]  # deux images puis débranchement
        def read(self):
            return (self.frames.pop(0) if self.frames else False), "frame"
        def release(self):
            pass

    opened = []

    def fake_open(index):
        opened.append(index)
        if len(opened) == 2:
            stop.set()
            return None
        return FakeCap()

    detector = SimpleNamespace(detect=lambda frame: [coin("objet", 0.9)])
    monkeypatch.setattr("factorypulse.vision.camera.open_camera", fake_open)
    monkeypatch.setattr(camera_worker, "_make_detector", lambda kind: (detector, None))
    camera_worker.run_camera("euro", 1, results, stop, show=False, retry_delay=0)

    assert opened == [1, 1]  # rouverte après la perte
    assert results.get_nowait() == Detection("euro", "objet", 0.9)
    assert results.empty()  # envoyée une seule fois


def test_importing_main_does_not_load_opencv():
    """Windows relance main.py dans chaque processus caméra : l'import doit rester léger."""
    import subprocess
    import sys

    code = "import sys, factorypulse.vision.main; assert 'cv2' not in sys.modules"
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0
