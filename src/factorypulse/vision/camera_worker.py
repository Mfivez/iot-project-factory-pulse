"""Une caméra = un processus qui détecte en continu et envoie ses résultats dans une file.

La caméra est ouverte une seule fois et reste ouverte : elle n'est plus libérée puis rouverte
à chaque pièce. Si elle est débranchée (ou absente au démarrage), le processus réessaie
régulièrement sans planter ; l'autre caméra continue de tourner.

Chaque pièce n'est envoyée qu'une fois : après un envoi, la caméra se réarme seulement quand
l'image est restée vide pendant quelques images (la pièce est partie).
"""
from __future__ import annotations

from dataclasses import dataclass

# routes du Raspberry Pi pour chaque modèle
ROUTES = {"euro": "/resultat1", "pays": "/resultat2"}
WINDOWS = {"euro": "Detection euro", "pays": "Pays 2 euros"}


@dataclass
class Detection:
    """Message envoyé par un processus caméra au processus principal."""
    kind: str      # "euro" ou "pays"
    label: str     # classe du modèle (euro / piece / objet, ou nom du pays)
    conf: float


class CoinTrigger:
    """Décide quand une pièce doit être envoyée : une seule fois tant qu'elle reste visible."""

    def __init__(self, conf: float = 0.85, rearm_frames: int = 15):
        self.conf = conf
        self.rearm_frames = rearm_frames
        self.armed = True
        self.empty = 0  # images consécutives sans pièce

    def update(self, coins):
        """Renvoie la pièce à envoyer, ou None."""
        if not coins:
            self.empty += 1
            if self.empty >= self.rearm_frames:
                self.armed = True
            return None
        self.empty = 0
        if not self.armed:
            return None
        sure = [c for c in coins if c.sure and c.conf >= self.conf]
        if not sure:
            return None
        self.armed = False
        return max(sure, key=lambda c: c.conf)


def log(message):
    print(message, flush=True)  # flush : sinon les messages d'un sous-processus restent en mémoire tampon


def _make_detector(kind):
    """Détecteur et fonction d'affichage du modèle `kind` (imports dans le processus caméra)."""
    if kind == "euro":
        from factorypulse.vision import detection_euro as m
        detector = m.EuroDetector()
        return detector, m.draw
    if kind == "pays":
        from factorypulse.vision import detection_pays_2euros as m
        detector = m.Pays2EurosDetector()
        return detector, lambda frame, coins: m.draw(frame, coins, detector.model.names)
    raise ValueError(f"Modèle inconnu : {kind}")


def run_camera(kind, camera, results, stop, show=True, conf=0.85, retry_delay=2.0):
    """Boucle d'un processus caméra : à lancer avec multiprocessing.Process."""
    import cv2

    from factorypulse.vision.camera import open_camera

    detector, draw = _make_detector(kind)
    trigger = CoinTrigger(conf)
    window = f"{WINDOWS[kind]} (camera {camera})"
    cap = None
    warned = False  # message "indisponible" affiché une seule fois par coupure
    try:
        while not stop.is_set():
            if cap is None:
                cap = open_camera(camera)
                if cap is None:
                    if not warned:
                        log(f"[{kind}] caméra {camera} indisponible, nouvel essai toutes les {retry_delay:.0f} s")
                        warned = True
                    stop.wait(retry_delay)
                    continue
                log(f"[{kind}] caméra {camera} ouverte")
                warned = False

            ok, frame = cap.read()
            if not ok:  # caméra débranchée en cours de route
                log(f"[{kind}] caméra {camera} perdue, reconnexion...")
                cap.release()
                cap = None
                continue

            coins = detector.detect(frame)
            coin = trigger.update(coins)
            if coin is not None:
                results.put(Detection(kind, str(coin.label), round(coin.conf, 4)))

            if show:
                out = draw(frame.copy(), coins)
                status = "pret" if trigger.armed else "envoye, retirer la piece"
                cv2.putText(out, status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
                cv2.putText(out, status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.imshow(window, out)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    stop.set()  # q dans une fenêtre arrête tout le programme
    except KeyboardInterrupt:
        pass  # Ctrl+C est géré par le processus principal
    finally:
        if cap is not None:
            cap.release()
        if show:
            cv2.destroyAllWindows()
