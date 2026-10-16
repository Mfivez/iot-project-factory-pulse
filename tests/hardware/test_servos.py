"""Tests des servomoteurs sans accéder aux GPIO de la machine de test."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


RACINE = Path(__file__).parents[2]
DOSSIER_DEVICES = RACINE / "src" / "factorypulse" / "hardware" / "devices"


class FauxPWM:
    def __init__(self, gpio: int, frequence: int) -> None:
        self.gpio = gpio
        self.frequence = frequence
        self.demarrages: list[float] = []
        self.rapports_cycliques: list[float] = []

    def start(self, rapport_cyclique: float) -> None:
        self.demarrages.append(rapport_cyclique)

    def ChangeDutyCycle(self, rapport_cyclique: float) -> None:
        self.rapports_cycliques.append(rapport_cyclique)


class FauxGPIO(ModuleType):
    BCM = "BCM"
    OUT = "OUT"

    def __init__(self) -> None:
        super().__init__("RPi.GPIO")
        self.modes: list[str] = []
        self.configurations: list[tuple[int, str]] = []
        self.pwm_crees: list[FauxPWM] = []

    def setmode(self, mode: str) -> None:
        self.modes.append(mode)

    def setup(self, gpio: int, mode: str) -> None:
        self.configurations.append((gpio, mode))

    def PWM(self, gpio: int, frequence: int) -> FauxPWM:
        pwm = FauxPWM(gpio, frequence)
        self.pwm_crees.append(pwm)
        return pwm


def _charger_servo(monkeypatch: pytest.MonkeyPatch, nom_module: str):
    faux_gpio = FauxGPIO()
    paquet_rpi = ModuleType("RPi")
    paquet_rpi.GPIO = faux_gpio

    configuration = ModuleType("config")
    configuration.SERVO1_GPIO = 12
    configuration.SERVO1_ANGLE_GAUCHE = -90
    configuration.SERVO1_ANGLE_DROITE = 90
    configuration.SERVO1_ZERO = 0
    configuration.SERVO1_TEMPS_MOUVEMENT = 1.5
    configuration.SERVO1_PAUSE = 1.0
    configuration.SERVO2_GPIO = 13
    configuration.SERVO2_ANGLE_DROITE = 90
    configuration.SERVO2_ZERO = 0
    configuration.SERVO2_TEMPS_MOUVEMENT = 1.5
    configuration.SERVO2_PAUSE = 2.0

    monkeypatch.setitem(sys.modules, "RPi", paquet_rpi)
    monkeypatch.setitem(sys.modules, "RPi.GPIO", faux_gpio)
    monkeypatch.setitem(sys.modules, "config", configuration)

    chemin = DOSSIER_DEVICES / f"{nom_module}.py"
    specification = importlib.util.spec_from_file_location(
        f"test_{nom_module}", chemin
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module, faux_gpio


@pytest.mark.parametrize(
    ("nom_module", "action", "gpio", "rapports_attendus", "pauses_attendues"),
    [
        ("servo1", "tourner_gauche", 12, [2.0, 0, 7.0, 0], [1.5, 1.0]),
        ("servo1", "tourner_droite", 12, [12.0, 0, 7.0, 0], [1.5, 1.0]),
        ("servo2", "tourner_droite", 13, [12.0, 0, 7.0, 0], [1.5, 2.0]),
    ],
)
def test_mouvement_pwm_coupe_le_signal_entre_les_positions(
    monkeypatch: pytest.MonkeyPatch,
    nom_module: str,
    action: str,
    gpio: int,
    rapports_attendus: list[float],
    pauses_attendues: list[float],
) -> None:
    module, faux_gpio = _charger_servo(monkeypatch, nom_module)
    pauses: list[float] = []
    monkeypatch.setattr(module.time, "sleep", pauses.append)

    getattr(module, action)()

    assert faux_gpio.modes == [faux_gpio.BCM]
    assert faux_gpio.configurations == [(gpio, faux_gpio.OUT)]
    assert len(faux_gpio.pwm_crees) == 1
    pwm = faux_gpio.pwm_crees[0]
    assert (pwm.gpio, pwm.frequence) == (gpio, 50)
    assert pwm.demarrages == [0]
    assert pwm.rapports_cycliques == rapports_attendus
    assert pauses == pauses_attendues


@pytest.mark.parametrize("angle", [-91, 91])
def test_angle_hors_limites_refuse(
    monkeypatch: pytest.MonkeyPatch, angle: float
) -> None:
    module, _ = _charger_servo(monkeypatch, "servo1")

    with pytest.raises(ValueError, match="Angle hors limites"):
        module._angle_vers_rapport_cyclique(angle)
