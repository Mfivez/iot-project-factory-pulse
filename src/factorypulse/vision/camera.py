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
    """Ouvre la webcam `index` ; renvoie None si elle est absente ou ne donne pas d'image."""
    backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        cap.release()
        return None
    # l'ordre compte : le format avant la résolution
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # toujours l'image la plus récente
    ok, _ = cap.read()
    if not ok:
        cap.release()
        return None
    return cap
