"""Commande du servo2 : Pousse la pièce tout en bas de la pile des pièces de 2€"""

import threading
import time

from gpiozero import AngularServo

from config import (
    SERVO2_GPIO,
    SERVO2_ANGLE_DROITE,
    SERVO2_ZERO,
    SERVO2_TEMPS_MOUVEMENT,
    SERVO2_PAUSE,
)

servo2 = AngularServo(SERVO2_GPIO, 
                    min_angle=-90, 
                    max_angle=90,
                    min_pulse_width=0.001,
                    max_pulse_width=0.002,
                    frame_width=0.010,)
# Ce verrou sérialise les mouvements : une requête qui arrive pendant un
# mouvement en cours attend simplement que le verrou se libère.
_verrou_servo2 = threading.Lock()


def _bouger(angle_cible):
    with _verrou_servo2:
        servo2.angle = angle_cible
        time.sleep(SERVO2_TEMPS_MOUVEMENT)
        servo2.angle = SERVO2_ZERO
        time.sleep(SERVO2_PAUSE)



def tourner_droite():
    """Écarte un objet qui n'est pas un euro."""
    _bouger(SERVO2_ANGLE_DROITE)
