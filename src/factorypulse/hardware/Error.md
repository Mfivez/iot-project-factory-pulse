maxime@RaspMax:~/Coin_sorter $ uv run fastapi run main.py --host 0.0.0.0 --port 8000

 ⚡️ Starting FastAPI in production mode
/home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/gpiozero/devices.py:300: PinFactoryFallback: Falling back from lgpio: No module named 'lgpio'
  warnings.warn(
/home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/gpiozero/devices.py:300: PinFactoryFallback: Falling back from rpigpio: No module named 'RPi'
  warnings.warn(
/home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/gpiozero/devices.py:300: PinFactoryFallback: Falling back from pigpio: No module named 'pigpio'
  warnings.warn(
/home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/gpiozero/devices.py:297: NativePinFactoryFallback: Falling back to the experimental pin factory NativeFactory because no other pin factory could be loaded. For best results, install RPi.GPIO or pigpio. See https://gpiozero.readthedocs.io/en/stable/api_pins.html for more information.
  warnings.warn(NativePinFactoryFallback(native_fallback_message))

╭─────────────────────── Traceback (most recent call last) ───────────────────────╮
│ /home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/fastapi_cli/cli.py: │
│ 521 in run                                                                      │
│                                                                                 │
│   518 │                                                                         │
│   519 │   Otherwise, it uses the first [bold]FastAPI[/bold] app found in the    │
│       imported module or package.                                               │
│   520 │   """                                                                   │
│ ❱ 521 │   _run(                                                                 │
│   522 │   │   path=path,                                                        │
│   523 │   │   host=host,                                                        │
│   524 │   │   port=port,                                                        │
│                                                                                 │
│ /home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/fastapi_cli/cli.py: │
│ 182 in _run                                                                     │
│                                                                                 │
│   179 │   │   try:                                                              │
│   180 │   │   │   # Resolve import data with priority: CLI path/app > config    │
│       entrypoint > auto-discovery                                               │
│   181 │   │   │   if path or app:                                               │
│ ❱ 182 │   │   │   │   import_data = get_import_data(path=path, app_name=app)    │
│   183 │   │   │   elif config.entrypoint:                                       │
│   184 │   │   │   │   import_data = get_import_data_from_import_string(         │
│   185 │   │   │   │   │   config.entrypoint, config.from_pyproject              │
│                                                                                 │
│ /home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/fastapi_cli/discove │
│ r.py:143 in get_import_data                                                     │
│                                                                                 │
│   140 │   │   raise FastAPICLIException(f"Path does not exist {path}")          │
│   141 │   mod_data = get_module_data_from_path(path)                            │
│   142 │   sys.path.insert(0, str(mod_data.extra_sys_path))                      │
│ ❱ 143 │   use_app_name = get_app_name(mod_data=mod_data, app_name=app_name)     │
│   144 │                                                                         │
│   145 │   import_string = f"{mod_data.module_import_str}:{use_app_name}"        │
│   146                                                                           │
│                                                                                 │
│ /home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/fastapi_cli/discove │
│ r.py:70 in get_app_name                                                         │
│                                                                                 │
│    67                                                                           │
│    68 def get_app_name(*, mod_data: ModuleData, app_name: str | None = None) -> │
│       str:                                                                      │
│    69 │   try:                                                                  │
│ ❱  70 │   │   mod = importlib.import_module(mod_data.module_import_str)         │
│    71 │   except (ImportError, ValueError) as e:                                │
│    72 │   │   logger.error(f"Import error: {e}")                                │
│    73 │   │   logger.warning(                                                   │
│                                                                                 │
│ /usr/lib/python3.13/importlib/__init__.py:88 in import_module                   │
│                                                                                 │
│    85 │   │   │   if character != '.':                                          │
│    86 │   │   │   │   break                                                     │
│    87 │   │   │   level += 1                                                    │
│ ❱  88 │   return _bootstrap._gcd_import(name[level:], package, level)           │
│    89                                                                           │
│    90                                                                           │
│    91 _RELOADING = {}                                                           │
│ in _gcd_import:1387                                                             │
│ in _find_and_load:1360                                                          │
│ in _find_and_load_unlocked:1331                                                 │
│ in _load_unlocked:935                                                           │
│ in exec_module:1026                                                             │
│ in _call_with_frames_removed:488                                                │
│                                                                                 │
│ /home/maxime/Coin_sorter/main.py:6 in <module>                                  │
│                                                                                 │
│    3 from gpiozero import AngularServo                                          │
│    4                                                                            │
│    5 from config import SERVO2_GPIO                                             │
│ ❱  6 from routes.servo import router as servo_router                            │
│    7                                                                            │
│    8 # Création du serveur API                                                  │
│    9 app = FastAPI()                                                            │
│                                                                                 │
│ /home/maxime/Coin_sorter/routes/servo.py:4 in <module>                          │
│                                                                                 │
│    1 from fastapi import APIRouter, HTTPException                               │
│    2 from pydantic import BaseModel                                             │
│    3                                                                            │
│ ❱  4 from devices.servo1 import tourner_gauche, tourner_droite                  │
│    5                                                                            │
│    6 router = APIRouter(prefix="/servo", tags=["SERVO"])                        │
│    7                                                                            │
│                                                                                 │
│ /home/maxime/Coin_sorter/devices/servo1.py:16 in <module>                       │
│                                                                                 │
│   13 │   SERVO1_PAUSE,                                                          │
│   14 )                                                                          │
│   15                                                                            │
│ ❱ 16 servo1 = AngularServo(SERVO1_GPIO, min_angle=-90, max_angle=90)            │
│   17 # Ce verrou sérialise les mouvements : une requête qui arrive pendant un   │
│   18 # mouvement en cours attend simplement que le verrou se libère.            │
│   19 _verrou_servo1 = threading.Lock()                                          │
│                                                                                 │
│ /home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/gpiozero/devices.py │
│ :108 in __call__                                                                │
│                                                                                 │
│   105 │   │   │   │   cls._instances[key] = weakref.ref(self)                   │
│   106 │   │   else:                                                             │
│   107 │   │   │   # Construct the instance as normal                            │
│ ❱ 108 │   │   │   self = super().__call__(*args, **kwargs)                      │
│   109 │   │   # At this point __new__ and __init__ have all been run. We now    │
│       fix the                                                                   │
│   110 │   │   # set of attributes on the class by dir'ing the instance and      │
│       creating a                                                                │
│   111 │   │   # frozenset of the result called __attrs__ (which is queried by   │
│                                                                                 │
│ /home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/gpiozero/output_dev │
│ ices.py:1719 in __init__                                                        │
│                                                                                 │
│   1716 │   │   │   raise OutputDeviceBadValue(                                  │
│   1717 │   │   │   │   f"AngularServo angle must be between {min_angle} and "   │
│   1718 │   │   │   │   f"{max_angle}, or None")                                 │
│ ❱ 1719 │   │   super().__init__(pin, initial_value=initial_value,               │
│   1720 │   │   │   │   │   │    min_pulse_width=min_pulse_width,                │
│   1721 │   │   │   │   │   │    max_pulse_width=max_pulse_width,                │
│   1722 │   │   │   │   │   │    frame_width=frame_width,                        │
│        pin_factory=pin_factory)                                                 │
│                                                                                 │
│ /home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/gpiozero/output_dev │
│ ices.py:1497 in __init__                                                        │
│                                                                                 │
│   1494 │   │   self._min_value = -1                                             │
│   1495 │   │   self._value_range = 2                                            │
│   1496 │   │   super().__init__(                                                │
│ ❱ 1497 │   │   │   pwm_device=PWMOutputDevice(                                  │
│   1498 │   │   │   │   pin, frequency=int(1 / frame_width),                     │
│        pin_factory=pin_factory),                                                │
│   1499 │   │   │   pin_factory=pin_factory                                      │
│   1500 │   │   )                                                                │
│                                                                                 │
│ /home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/gpiozero/devices.py │
│ :108 in __call__                                                                │
│                                                                                 │
│   105 │   │   │   │   cls._instances[key] = weakref.ref(self)                   │
│   106 │   │   else:                                                             │
│   107 │   │   │   # Construct the instance as normal                            │
│ ❱ 108 │   │   │   self = super().__call__(*args, **kwargs)                      │
│   109 │   │   # At this point __new__ and __init__ have all been run. We now    │
│       fix the                                                                   │
│   110 │   │   # set of attributes on the class by dir'ing the instance and      │
│       creating a                                                                │
│   111 │   │   # frozenset of the result called __attrs__ (which is queried by   │
│                                                                                 │
│ /home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/gpiozero/output_dev │
│ ices.py:396 in __init__                                                         │
│                                                                                 │
│    393 │   │   │   │   │   │    pin_factory=pin_factory)                        │
│    394 │   │   try:                                                             │
│    395 │   │   │   # XXX need a way of setting these together                   │
│ ❱  396 │   │   │   self.pin.frequency = frequency                               │
│    397 │   │   │   self.value = initial_value                                   │
│    398 │   │   except:                                                          │
│    399 │   │   │   self.close()                                                 │
│                                                                                 │
│ /home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/gpiozero/pins/__ini │
│ t__.py:379 in <lambda>                                                          │
│                                                                                 │
│    376 │                                                                        │
│    377 │   frequency = property(                                                │
│    378 │   │   lambda self: self._get_frequency(),                              │
│ ❱  379 │   │   lambda self, value: self._set_frequency(value),                  │
│    380 │   │   doc="""\                                                         │
│    381 │   │   The frequency (in Hz) for the pin's PWM implementation, or       │
│        :data:`None`                                                             │
│    382 │   │   if PWM is not currently in use. This value always defaults to    │
│                                                                                 │
│ /home/maxime/Coin_sorter/.venv/lib/python3.13/site-packages/gpiozero/pins/__ini │
│ t__.py:374 in _set_frequency                                                    │
│                                                                                 │
│    371 │                                                                        │
│    372 │   def _set_frequency(self, value):                                     │
│    373 │   │   if value is not None:                                            │
│ ❱  374 │   │   │   raise PinPWMUnsupported(  # pragma: no cover                 │
│    375 │   │   │   │   f"PWM is not supported on pin {self!r}")                 │
│    376 │                                                                        │
│    377 │   frequency = property(                                                │
╰─────────────────────────────────────────────────────────────────────────────────╯
PinPWMUnsupported: PWM is not supported on pin GPIO12