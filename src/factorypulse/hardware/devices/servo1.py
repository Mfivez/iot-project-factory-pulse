"""Commande du servo1 : trie une pièce à gauche ou un objet non reconnu à droite."""
import threading
import time

from gpiozero import AngularServo

from config import (
    SERVO1_GPIO,
    SERVO1_ANGLE_GAUCHE,
    SERVO1_ANGLE_DROITE,
    SERVO1_ZERO,
    SERVO1_TEMPS_MOUVEMENT,
    SERVO1_PAUSE,
)

servo1 = AngularServo(SERVO1_GPIO,
                    min_angle=-90,
                    max_angle=90,
                    #min_pulse_width=0.001,
                    #max_pulse_width=0.002,
                    #frame_width=0.010,)
# Ce verrou sérialise les mouvements : une requête qui arrive pendant un
# mouvement en cours attend simplement que le verrou se libère.
_verrou_servo1 = threading.Lock()


def _bouger(angle_cible):
    with _verrou_servo1:
        servo1.angle = angle_cible
        time.sleep(SERVO1_TEMPS_MOUVEMENT)
        servo1.angle = SERVO1_ZERO
        time.sleep(SERVO1_PAUSE)


def tourner_gauche():
    """Trie une pièce reconnue comme un euro."""
    _bouger(SERVO1_ANGLE_GAUCHE)


def tourner_droite():
    """Écarte un objet qui n'est pas un euro."""
    _bouger(SERVO1_ANGLE_DROITE)
