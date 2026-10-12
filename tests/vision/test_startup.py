"""Le socle peut lire les photos attendues sans dépendances ni caméra."""
import subprocess
import sys
import runpy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from factorypulse.vision import main as vision_main


def test_inventory_runs_without_importing_optional_vision_dependencies():
    source = Path(vision_main.__file__).resolve().parents[2]
    script = """
import importlib.abc
import runpy
import sys

class NoVisionDependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'cv2', 'numpy', 'ultralytics'}:
            raise AssertionError(f'Dépendance optionnelle chargée : {fullname}')

sys.meta_path.insert(0, NoVisionDependencies())
sys.path.insert(0, sys.argv.pop())
runpy.run_module('factorypulse.vision.main', run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(source)],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("A FAIRE ") + result.stdout.count("OK   ") == 6


@pytest.mark.parametrize(
    ("flag", "module", "function"),
    [
        ("--webcam", "detector", "detect_objects"),
        ("--colors", "color_check", "detect_marker_color"),
    ],
)
def test_camera_demos_require_an_explicit_option(monkeypatch, flag, module, function):
    calls = []
    fake_module = SimpleNamespace(**{function: lambda: calls.append(flag)})
    monkeypatch.setitem(sys.modules, f"factorypulse.vision.{module}", fake_module)
    monkeypatch.setattr(sys, "argv", ["vision", flag])

    vision_main.main()

    assert calls == [flag]


@pytest.mark.parametrize("camera_opens", [False, True])
def test_detector_import_is_passive_and_failed_capture_is_released(monkeypatch, camera_opens):
    camera = Mock()
    camera.isOpened.return_value = camera_opens
    camera.read.return_value = (False, None)
    cv2 = SimpleNamespace(VideoCapture=Mock(return_value=camera), destroyAllWindows=Mock())
    yolo = Mock()
    modules = {
        "cv2": cv2,
        "cv2.typing": SimpleNamespace(MatLike=object),
        "numpy": SimpleNamespace(),
        "numpy.typing": SimpleNamespace(NDArray=object),
        "ultralytics": SimpleNamespace(YOLO=yolo),
        "ultralytics.engine.results": SimpleNamespace(Results=object),
    }
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)

    detector = runpy.run_path(str(Path(vision_main.__file__).with_name("detector.py")))
    yolo.assert_not_called()
    cv2.VideoCapture.assert_not_called()

    with pytest.raises(RuntimeError, match="webcam"):
        detector["detect_objects"]()

    yolo.assert_called_once_with("yolo26n-seg.pt")
    cv2.VideoCapture.assert_called_once_with(0)
    camera.release.assert_called_once_with()
    cv2.destroyAllWindows.assert_called_once_with()
