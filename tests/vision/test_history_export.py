import json

import numpy as np

from factorypulse.vision.history import DetectionHistoryExporter, StableDetectionTracker


def test_history_exporter_writes_jsonl_and_capture(tmp_path):
    exporter = DetectionHistoryExporter(base_dir=tmp_path)
    frame = np.zeros((120, 160, 3), dtype=np.uint8)

    event = exporter.export_event(
        frame=frame,
        object_type="bottle",
        color="red",
        confidence=0.95,
        source="webcam_0",
    )

    assert event["id"] == 1
    assert event["object_type"] == "bottle"
    assert event["image_path"].startswith("data/images/captures/")
    assert event["anomaly"] is None
    assert event["source"] == "webcam_0"
    assert event["confidence"] == 0.95
    assert (tmp_path / event["image_path"]).exists()

    written = (tmp_path / "data" /
               "history.jsonl").read_text(encoding="utf-8").strip()
    payload = json.loads(written)
    assert payload == event


def test_stable_tracker_emits_one_event_per_second_for_same_object(tmp_path):
    exporter = DetectionHistoryExporter(base_dir=tmp_path)
    tracker = StableDetectionTracker(exporter)
    frame = np.zeros((120, 160, 3), dtype=np.uint8)

    tracker.track(
        frame=frame,
        detections=[{"object_type": "bottle",
                     "color": "red", "confidence": 0.95}],
        source="webcam_0",
        now=0.0,
    )
    tracker.track(
        frame=frame,
        detections=[{"object_type": "bottle",
                     "color": "red", "confidence": 0.95}],
        source="webcam_0",
        now=0.5,
    )
    tracker.track(
        frame=frame,
        detections=[{"object_type": "bottle",
                     "color": "red", "confidence": 0.95}],
        source="webcam_0",
        now=1.2,
    )

    events = (tmp_path / "data" /
              "history.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(events) == 1
    payload = json.loads(events[0])
    assert payload["object_type"] == "bottle"
    assert payload["source"] == "webcam_0"

    tracker.track(
        frame=frame,
        detections=[],
        source="webcam_0",
        now=2.2,
    )
    tracker.track(
        frame=frame,
        detections=[{"object_type": "bottle",
                     "color": "red", "confidence": 0.95}],
        source="webcam_0",
        now=6.0,
    )
    tracker.track(
        frame=frame,
        detections=[{"object_type": "bottle",
                     "color": "red", "confidence": 0.95}],
        source="webcam_0",
        now=7.0,
    )

    events = (tmp_path / "data" /
              "history.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(events) == 2


def test_image_result_exports_one_jpeg_and_one_jsonl_event(tmp_path):
    exporter = DetectionHistoryExporter(base_dir=tmp_path)
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    input_path = tmp_path / "input" / "source photo.png"
    input_path.parent.mkdir()
    input_path.write_bytes(b"source image")

    event = exporter.export_image_result(
        frame=frame,
        detections=[
            {"object_type": "bottle", "color": "red", "confidence": 0.95},
            {"object_type": "cup", "color": "blue", "confidence": 0.81},
        ],
        input_image_path=input_path,
    )

    history_lines = (tmp_path / "data" / "history.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()
    captures = list((tmp_path / "data" / "images" / "captures").glob("*.jpg"))
    assert len(history_lines) == 1
    assert len(captures) == 1
    assert json.loads(history_lines[0]) == event
    assert event["source"] == "image_upload"
    assert event["input_image_path"] == str(input_path.resolve())
    assert event["object_type"] == "multiple"
    assert len(event["detections"]) == 2
