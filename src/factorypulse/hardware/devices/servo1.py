"""Commande PWM du servo 1 avec l'API RPi.GPIO."""

import threading
import time

import RPi.GPIO as GPIO

from config import (
    SERVO1_GPIO,
    SERVO1_ANGLE_GAUCHE,
    SERVO1_ANGLE_DROITE,
    SERVO1_ZERO,
    SERVO1_TEMPS_MOUVEMENT,
    SERVO1_PAUSE,
)

_FREQUENCE_PWM_HZ = 50
_ANGLE_MIN = -90
_ANGLE_MAX = 90
_RAPPORT_CYCLIQUE_MIN = 2.0
_RAPPORT_CYCLIQUE_MAX = 12.0

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO1_GPIO, GPIO.OUT)
servo1 = GPIO.PWM(SERVO1_GPIO, _FREQUENCE_PWM_HZ)
servo1.start(0)

# Ce verrou sérialise les mouvements : une requête qui arrive pendant un
# mouvement en cours attend simplement que le verrou se libère.
_verrou_servo1 = threading.Lock()


def _angle_vers_rapport_cyclique(angle: float) -> float:
    """Convertit un angle de -90° à 90° en rapport cyclique de 2 % à 12 %."""
    if not _ANGLE_MIN <= angle <= _ANGLE_MAX:
        raise ValueError(f"Angle hors limites : {angle} (attendu entre -90 et 90)")

    amplitude_angle = _ANGLE_MAX - _ANGLE_MIN
    amplitude_rapport = _RAPPORT_CYCLIQUE_MAX - _RAPPORT_CYCLIQUE_MIN
    return _RAPPORT_CYCLIQUE_MIN + (
        (angle - _ANGLE_MIN) * amplitude_rapport / amplitude_angle
    )


def _positionner(angle: float, duree: float) -> None:
    """Alimente le servo le temps du mouvement, puis coupe le signal PWM."""
    try:
        servo1.ChangeDutyCycle(_angle_vers_rapport_cyclique(angle))
        time.sleep(duree)
    finally:
        # Comme dans l'exemple « No Jitter » de la vidéo, un rapport nul évite
        # de maintenir inutilement le servo sous commande entre deux positions.
        servo1.ChangeDutyCycle(0)


def _bouger(angle_cible: float) -> None:
    with _verrou_servo1:
        _positionner(angle_cible, SERVO1_TEMPS_MOUVEMENT)
        _positionner(SERVO1_ZERO, SERVO1_PAUSE)


def tourner_gauche():
    """Trie une pièce reconnue comme un euro."""
    _bouger(SERVO1_ANGLE_GAUCHE)


def tourner_droite():
    """Écarte un objet qui n'est pas un euro."""
    _bouger(SERVO1_ANGLE_DROITE)
