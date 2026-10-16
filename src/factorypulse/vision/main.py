"""Point d'entrée vision : deux caméras, deux modèles en parallèle, résultats envoyés au Raspberry Pi.

- caméra euro : modèle detect_euro      -> POST /servo/resultat1 {"result": "euro"|"piece"|"objet"}
- caméra pays : modèle pays_2euros      -> POST /servo/resultat2 {"result": "<pays>"}

Chaque caméra tourne dans son propre processus (voir camera_worker.py) ; ce processus-ci ne fait
que recevoir les détections et les envoyer en HTTP. Ctrl+C ou q dans une fenêtre pour arrêter.

Les paramètres se règlent dans les constantes ci-dessous.

Usage :
    python -m factorypulse.vision.main
"""

from __future__ import annotations

import csv
import multiprocessing as mp
import queue
from pathlib import Path

# ---- Paramètres ----
CAM_EURO = 1                    # index de la caméra du modèle euro
CAM_PAYS = 0                    # index de la caméra du modèle pays
RASPBERRYPI_IP = "192.168.50.2"
RASPBERRYPI_PORT = 8000
CONF = 0.85                     # confiance minimale pour envoyer un résultat
SHOW_WINDOWS = True             # False : pas de fenêtre vidéo


def inspect_manifest(manifest: Path, images: Path) -> list[dict[str, str | bool]]:
    with manifest.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [
        {
            "file": row["file"],
            "scene": row["scene"],
            "present": (images / row["file"]).is_file(),
        }
        for row in rows
    ]


def build_request(base_url: str, detection) -> tuple[str, dict]:
    """URL et JSON à envoyer au Pi pour une détection."""
    from factorypulse.vision.camera_worker import ROUTES

    return base_url + ROUTES[detection.kind], {"result": detection.label}


def send(session, base_url: str, detection) -> bool:
    import requests

    url, payload = build_request(base_url, detection)
    try:
        r = session.post(url, json=payload, timeout=3)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Échec d'envoi vers {url} ({e}) — résultat perdu : {payload}", flush=True)
        return False
    print(f"Envoyé {url} : {payload} (confiance {detection.conf:.0%})", flush=True)
    return True


def main() -> None:
    import requests

    from factorypulse.vision.camera_worker import run_camera

    base_url = f"http://{RASPBERRYPI_IP}:{RASPBERRYPI_PORT}/servo"
    cameras = {"euro": CAM_EURO, "pays": CAM_PAYS}

    ctx = mp.get_context("spawn")  # comportement identique sous Windows et Linux
    results = ctx.Queue()
    stop = ctx.Event()

    def start(kind):
        proc = ctx.Process(
            target=run_camera, name=f"camera-{kind}",
            args=(kind, cameras[kind], results, stop, SHOW_WINDOWS, CONF),
            daemon=True,
        )
        proc.start()
        return proc

    procs = {kind: start(kind) for kind in cameras}
    session = requests.Session()
    print(f"Envoi vers {base_url} — Ctrl+C ou q pour arrêter.", flush=True)
    try:
        while not stop.is_set():
            try:
                detection = results.get(timeout=0.5)
            except queue.Empty:
                pass
            else:
                send(session, base_url, detection)
            for kind, proc in procs.items():  # un processus caméra planté est relancé
                if not proc.is_alive() and not stop.is_set():
                    print(f"[{kind}] processus arrêté (code {proc.exitcode}), redémarrage", flush=True)
                    procs[kind] = start(kind)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        for proc in procs.values():
            proc.join(timeout=5)
            if proc.is_alive():
                proc.terminate()
        print("Arrêt.", flush=True)


if __name__ == "__main__":
    main()
