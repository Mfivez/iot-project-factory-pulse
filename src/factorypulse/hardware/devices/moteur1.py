"""Commande du moteur pas-à-pas 1 : rotation continue démarrable/arrêtable via l'API."""
import threading
import time

from gpiozero import OutputDevice

from config import STEPPER_1_GPIOS, DELAI_MOTEUR_1

# Les huit états commandent les bobines en mode demi-pas (même séquence que old/devices.py).
_SEQUENCE_DEMI_PAS = (
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
    (1, 0, 0, 1),
)

_sorties = [OutputDevice(gpio, initial_value=False) for gpio in STEPPER_1_GPIOS]
_en_marche = threading.Event()
_verrou_demarrage = threading.Lock()
_thread = None


def _tourner_en_continu():
    index_phase = 0
    while _en_marche.is_set():
        index_phase = (index_phase - 1) % len(_SEQUENCE_DEMI_PAS)
        phase = _SEQUENCE_DEMI_PAS[index_phase]
        for sortie, active in zip(_sorties, phase):
            sortie.value = bool(active)
        time.sleep(DELAI_MOTEUR_1)
    for sortie in _sorties:
        sortie.off()


def demarrer():
    """Lance la rotation continue dans un thread dédié, sans bloquer l'API."""
    global _thread
    with _verrou_demarrage:
        if _en_marche.is_set():
            return
        _en_marche.set()
        _thread = threading.Thread(target=_tourner_en_continu, daemon=True)
        _thread.start()


def arreter():
    """Arrête la rotation et coupe les bobines."""
    _en_marche.clear()
