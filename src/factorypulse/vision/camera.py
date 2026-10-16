"""Ouverture d'une webcam robuste, utilisable par plusieurs caméras en même temps.

Sous Windows, le backend par défaut (Media Foundation) gère mal deux webcams USB ouvertes
simultanément : on utilise DirectShow. Le format MJPG divise par ~10 le débit USB par rapport
au flux brut (YUY2) ; sans lui, deux caméras 1280x720 sur le même contrôleur USB saturent la
bande passante et l'une des deux ne renvoie plus d'image.
"""
import sys

import cv2

# sans cela, OpenCV affiche un avertissement à chaque tentative sur une caméra débranchée
cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)


def open_camera(index: int, width: int = 1280, height: int = 720):
    """Ouvre la webcam `index` ; renvoie None si elle est absente ou ne donne pas d'image.

    Sous Windows, DirectShow d'abord (vraies webcams USB), puis Media Foundation en secours :
    certaines caméras virtuelles (DroidCam) ne fonctionnent qu'avec ce dernier.
    """
    if sys.platform == "win32":
        cap = _try_open(index, cv2.CAP_DSHOW, width, height, configure=True)
        if cap is None:
            cap = _try_open(index, cv2.CAP_MSMF, width, height, configure=False)
        return cap
    return _try_open(index, cv2.CAP_ANY, width, height, configure=True)


def _try_open(index, backend, width, height, configure, warmup=10):
    try:
        cap = cv2.VideoCapture(index, backend)
    except cv2.error:
        return None
    if not cap.isOpened():
        cap.release()
        return None
    if configure:
        # l'ordre compte : le format avant la résolution
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # toujours l'image la plus récente
    for _ in range(warmup):
        ok, _ = cap.read()
        if ok:
            return cap
    cap.release()
    return None
