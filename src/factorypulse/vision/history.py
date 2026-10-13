"""Historique des détections YOLO : JSONL + JPEG annotés."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import cv2

from factorypulse.shared.paths import project_root

LOGGER = logging.getLogger(__name__)


class DetectionHistoryExporter:
    """Écrit les événements d'historique dans data/history.jsonl et les captures annotées."""

    def __init__(
        self,
        base_dir: str | Path | None = None,
        history_path: str | Path | None = None,
        capture_dir: str | Path | None = None,
    ) -> None:
        self.root_dir = Path(base_dir).resolve(
        ) if base_dir is not None else project_root()
        self.history_path = (
            Path(history_path)
            if history_path is not None
            else self.root_dir / "data" / "history.jsonl"
        )
        self.capture_dir = (
            Path(capture_dir)
            if capture_dir is not None
            else self.root_dir / "data" / "images" / "captures"
        )
        self._lock = threading.Lock()
        self._next_id = self._read_next_id()

    def _read_next_id(self) -> int:
        if not self.history_path.exists():
            return 1

        max_id = 0
        try:
            with self.history_path.open("r", encoding="utf-8") as file_obj:
                for raw_line in file_obj:
                    if not raw_line.strip():
                        continue
                    try:
                        event = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue
                    candidate = event.get("id")
                    if isinstance(candidate, int):
                        max_id = max(max_id, candidate)
        except OSError as exc:
            LOGGER.warning(
                "Impossible de lire l'historique pour calculer l'ID suivant : %s", exc)
        return max_id + 1

    def _serialise_event(self, event: dict[str, Any]) -> str:
        return (
            json.dumps(event, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False)
            + "\n"
        )

    def export_event(
        self,
        *,
        frame,
        object_type: str,
        color: str | None,
        confidence: float | None,
        source: str,
    ) -> dict[str, Any] | None:
        """Sauvegarde le JPEG annoté et ajoute l'événement JSONL correspondant."""
        object_type = str(object_type).strip()
        if not object_type:
            return None

        timestamp_dt = datetime.now(timezone.utc)
        timestamp_iso = timestamp_dt.strftime(
            "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        file_timestamp = timestamp_dt.strftime("%Y%m%dT%H%M%S%f")[:-3] + "Z"

        self.capture_dir.mkdir(parents=True, exist_ok=True)
        capture_name = f"capture_{file_timestamp}_{uuid4().hex[:8]}.jpg"
        capture_path = self.capture_dir / capture_name
        relative_image_path = "data/images/captures/" + capture_name

        if not cv2.imwrite(str(capture_path), frame):
            LOGGER.warning(
                "Impossible d'écrire la capture %s pour l'objet %s.", capture_path, object_type)
            return None

        event: dict[str, Any] = {
            "timestamp": timestamp_iso,
            "object_type": object_type,
            "color": color,
            "image_path": relative_image_path,
            "confidence": None if confidence is None else float(confidence),
            "source": source,
            "anomaly": None,
        }

        with self._lock:
            event["id"] = self._next_id
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            with self.history_path.open("a", encoding="utf-8") as file_obj:
                file_obj.write(self._serialise_event(event))
                file_obj.flush()
                os.fsync(file_obj.fileno())
            self._next_id += 1

        return event

    def export_image_result(
        self,
        *,
        frame,
        detections: list[dict[str, Any]],
        input_image_path: str | Path,
    ) -> dict[str, Any] | None:
        """Exporte une image fixe en un JPEG annoté et une seule ligne JSONL."""
        timestamp_dt = datetime.now(timezone.utc)
        timestamp_iso = timestamp_dt.strftime(
            "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        file_timestamp = timestamp_dt.strftime("%Y%m%dT%H%M%S%f")[:-3] + "Z"

        self.capture_dir.mkdir(parents=True, exist_ok=True)
        capture_name = f"capture_{file_timestamp}_{uuid4().hex[:8]}.jpg"
        capture_path = self.capture_dir / capture_name
        relative_image_path = "data/images/captures/" + capture_name
        if not cv2.imwrite(str(capture_path), frame):
            LOGGER.warning("Impossible d'écrire la capture %s.", capture_path)
            return None

        copied_detections = [
            {
                "object_type": str(item.get("object_type", "")),
                "color": item.get("color"),
                "confidence": (
                    None if item.get("confidence") is None
                    else float(item["confidence"])
                ),
            }
            for item in detections
        ]
        first_detection = copied_detections[0] if len(copied_detections) == 1 else {}
        event: dict[str, Any] = {
            "timestamp": timestamp_iso,
            "object_type": first_detection.get("object_type", "multiple" if copied_detections else None),
            "color": first_detection.get("color"),
            "image_path": relative_image_path,
            "input_image_path": str(input_image_path),
            "confidence": first_detection.get("confidence"),
            "source": "image_upload",
            "detections": copied_detections,
            "anomaly": None,
        }

        with self._lock:
            event["id"] = self._next_id
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            with self.history_path.open("a", encoding="utf-8") as file_obj:
                file_obj.write(self._serialise_event(event))
                file_obj.flush()
                os.fsync(file_obj.fileno())
            self._next_id += 1
        return event


class StableDetectionTracker:
    """Regroupe les détections YOLO brèves et ne valide que les objets stables pendant au moins 1 seconde."""

    def __init__(self, exporter: DetectionHistoryExporter) -> None:
        self.exporter = exporter
        self._active: dict[tuple[str, str], dict[str, Any]] = {}

    def track(
        self,
        *,
        frame,
        detections: list[dict[str, Any]],
        source: str,
        now: float | None = None,
    ) -> None:
        current_time = time.monotonic() if now is None else float(now)
        seen_keys: set[tuple[str, str]] = set()

        for detection in detections:
            object_type = str(detection.get("object_type") or "").strip()
            if not object_type or object_type in {"person", "face"}:
                continue
            key = (source, object_type)
            seen_keys.add(key)

            current = self._active.get(key)
            if current is None:
                current = {
                    "first_seen": current_time,
                    "confirmed": False,
                    "last_emitted": None,
                    "color": detection.get("color"),
                    "confidence": detection.get("confidence"),
                }
                self._active[key] = current

            current["color"] = detection.get("color") or current.get("color")
            confidence = detection.get("confidence")
            if confidence is not None:
                current["confidence"] = max(
                    float(confidence), float(current.get("confidence") or 0.0))

            if not current["confirmed"] and current_time - float(current["first_seen"]) >= 1.0:
                current["confirmed"] = True

            if current["confirmed"] and (
                current["last_emitted"] is None
                or current_time - float(current["last_emitted"]) >= 1.0
            ):
                event = self.exporter.export_event(
                    frame=frame,
                    object_type=object_type,
                    color=current.get("color"),
                    confidence=current.get("confidence"),
                    source=source,
                )
                if event is not None:
                    current["last_emitted"] = current_time

        for key in list(self._active):
            if key not in seen_keys:
                del self._active[key]
