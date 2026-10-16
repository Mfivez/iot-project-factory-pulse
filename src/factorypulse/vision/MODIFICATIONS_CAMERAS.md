# Deux caméras en parallèle : problèmes trouvés et corrections

Objectif : deux webcams branchées au PC, chacune avec son modèle, qui tournent **en même temps**
et envoient leurs résultats au Raspberry Pi 3 en HTTP (Ethernet).

| Caméra | Index par défaut | Modèle | Route sur le Pi | JSON envoyé |
|---|---|---|---|---|
| euro | 1 | `modeles/detect_euro.onnx` | `POST /servo/resultat1` | `{"result": "euro"}` / `"piece"` / `"objet"` |
| pays | 0 | `modeles/pays_2euros.onnx` | `POST /servo/resultat2` | `{"result": "<pays>"}` |

## Lancer

```bash
python -m factorypulse.vision.main
```

Les paramètres sont codés en dur en haut de `main.py` :

```python
CAM_EURO = 1                    # index de la caméra du modèle euro
CAM_PAYS = 0                    # index de la caméra du modèle pays
RASPBERRYPI_IP = "192.168.50.2"
RASPBERRYPI_PORT = 8000
CONF = 0.85                     # confiance minimale pour envoyer un résultat
SHOW_WINDOWS = True             # False : pas de fenêtre vidéo
```

Arrêt : `Ctrl+C` dans la console, ou `q` dans une des fenêtres vidéo.

## Problèmes trouvés dans l'ancien code

### Pourquoi les caméras plantaient

1. **La caméra était fermée puis rouverte à chaque pièce.** `detect_euro()` / `detect_country_coins()`
   faisaient `cap.release()` et `return` dès la première pièce à 85 %. Il fallait donc relancer
   la fonction, rouvrir la webcam et recharger le modèle ONNX pour chaque pièce. Rouvrir une
   webcam sous Windows prend plusieurs secondes et échoue souvent quand l'autre caméra est active.
2. **Les deux caméras pouvaient s'ouvrir plusieurs fois.** Dans la version avec `ProcessPoolExecutor`,
   `pool.submit(...)` était appelé à chaque tour de boucle. Or `future.result(timeout=5)` n'arrête
   **pas** la tâche en cours quand le délai expire. Les tâches s'empilaient et plusieurs processus
   essayaient d'ouvrir la même caméra.
3. **Backend Windows par défaut (Media Foundation).** Il gère mal deux webcams USB ouvertes en même
   temps. Correction : backend DirectShow (`CAP_DSHOW`).
4. **Bande passante USB.** Deux flux bruts 1280x720 (YUY2) saturent souvent un même contrôleur USB,
   et l'une des caméras ne renvoie plus d'image (`cap.read()` → `False`, puis `break`). Correction :
   format **MJPG** (flux compressé, beaucoup plus léger).
5. **Aucune reprise d'erreur.** Une caméra absente provoquait `SystemExit`, et une image ratée
   arrêtait la boucle. Avec une seule caméra branchée, tout le programme tombait.

### Bugs dans l'envoi au Raspberry Pi

6. `{"result": f_euro}` envoyait l'**objet `Future`** au lieu du label. Il n'est pas sérialisable en
   JSON : `TypeError`, qui n'était pas rattrapé par `except requests.RequestException`, donc crash.
7. Après la première détection, `resultat(f_euro)` relisait **le même `Future` terminé** à chaque tour :
   le même résultat aurait été envoyé au Pi en boucle, sans pause.
8. L'URL était concaténée : avec les deux modèles actifs, on aurait obtenu
   `/servo/resultat1/resultat2`.
9. `f"{url}{"/resultat1"}"` (guillemets imbriqués) est une **erreur de syntaxe en Python 3.11**,
   alors que le projet annonce Python >= 3.11 (accepté seulement à partir de 3.12).
10. Dans les fichiers de détection, `p.parse_args(["--camera", ...])` ignorait les options de la
    ligne de commande, et il n'y avait pas de bloc `if __name__ == "__main__"`. Les commandes
    `python detection_euro.py --camera 1` indiquées dans la doc ne faisaient donc rien.

## Nouvelle architecture

```
            processus "camera-euro"                    processus "camera-pays"
   caméra 1 -> EuroDetector -> CoinTrigger     caméra 0 -> Pays2EurosDetector -> CoinTrigger
                       \                                          /
                        +------> multiprocessing.Queue <---------+
                                         |
                              processus principal (main.py)
                                         |
                       POST http://192.168.50.2:8000/servo/resultat1|2
```

- **Un processus par caméra** (`camera_worker.run_camera`). Chacun ouvre sa caméra **une seule
  fois**, charge son modèle une seule fois et détecte en continu. Les deux caméras sont
  indépendantes et peuvent détecter au même moment.
  Pourquoi des processus et pas des threads : chaque processus a son propre cœur de calcul
  (Hough et ONNX en parallèle) et sa propre fenêtre OpenCV (`imshow` depuis plusieurs threads
  plante souvent sous Windows).
- **Envoi unique par pièce** (`CoinTrigger`) : quand une pièce est sûre (`sure` et confiance
  >= `CONF`), elle est envoyée **une fois**. La caméra se réarme quand l'image est restée vide
  pendant 15 images (la pièce est partie). La fenêtre affiche `pret` ou `envoye, retirer la piece`.
  Si plusieurs pièces sont visibles en même temps, seule la plus sûre est envoyée.
- **Caméra absente ou débranchée** : le processus réessaie toutes les 2 s sans planter (un seul
  message par coupure), et l'autre caméra continue de tourner. Une caméra débranchée en cours de
  route est reconnectée automatiquement.
- **Processus caméra planté** : `main.py` le relance.
- **Pi injoignable** : le message d'erreur est affiché, le résultat est perdu (pas de file
  d'attente), et les caméras continuent. Les envois se font dans le processus principal : un Pi
  lent ne bloque donc pas la détection.

## Fichiers modifiés / créés

| Fichier | Changement |
|---|---|
| `vision/camera.py` (nouveau) | `open_camera()` : DirectShow sous Windows, MJPG, 1280x720, tampon d'une image, renvoie `None` si la caméra est absente. Masque les avertissements OpenCV répétitifs. |
| `vision/camera_worker.py` (nouveau) | Boucle d'un processus caméra, `CoinTrigger` (envoi unique), message `Detection`, routes du Pi. |
| `vision/main.py` | Réécrit : lance les 2 processus, reçoit les détections, POST vers le Pi, paramètres en constantes en haut du fichier, arrêt propre. Imports supprimés : `serial` (inutilisé), `ProcessPoolExecutor`, `argparse`. Les imports lourds sont faits dans les fonctions, pour que chaque processus relancé sous Windows reste léger. |
| `vision/detection_euro.py`, `vision/detection_pays_2euros.py` | Utilisent `open_camera()` ; la ligne de commande est de nouveau prise en compte ; ajout du bloc `__main__`. Les modèles, le prétraitement et les seuils **n'ont pas changé**. |
| `tests/vision/test_camera_worker.py` (nouveau) | 11 tests : envoi unique, réarmement, pièce incertaine non envoyée, routes et JSON, caméra absente sans crash, reconnexion, import léger de `main`. |
| `tests/vision/test_startup.py`, `test_ui.py`, `test_history_export.py` | Supprimés à ta demande : ils visaient l'ancien `main.py` (UI Streamlit, `--webcam`, `--colors`), `ui.py` et `history.py`, qui ne font plus partie du flux principal. |

## Ce qui a été vérifié (16/10/2026)

- `python -m pytest` : 63 réussis, 1 ignoré (test MCP qui demande un serveur démarré).
- `python scripts/validate_contract.py` : OK.
- Lancement réel de `main.py` sans fenêtres pendant 20 s : les deux processus démarrent, chargent
  leur modèle et ouvrent leur caméra, sans crash. Avec des index inexistants (8 et 9), les deux
  processus réessaient en boucle sans planter.
- **Pas vérifié** : la détection réelle de pièces avec deux vraies webcams USB branchées en même
  temps, et l'envoi au Raspberry Pi (non connecté pendant les tests).

## Points d'attention

- **L'index 1 s'ouvre alors que la 2e webcam n'est pas branchée.** Windows propose donc une autre
  source vidéo sur l'index 1 (caméra infrarouge du portable, caméra virtuelle OBS/Teams…). Une fois
  les deux webcams branchées, vérifier quel index correspond à quelle caméra et ajuster
  `CAM_EURO` / `CAM_PAYS` dans `main.py`.
- Si une caméra ne donne toujours pas d'image avec les deux branchées : les mettre sur **deux ports
  USB différents** (idéalement deux contrôleurs, par exemple un port à l'avant et un à l'arrière),
  sans hub passif.
- Le Pi doit accepter `POST /servo/resultat1` et `/servo/resultat2` avec `{"result": "..."}`. La
  confiance est affichée côté PC mais n'est pas envoyée.
- Le modèle pays répond toujours un pays, même si ce n'est pas une pièce de 2 € : c'est au montage
  (ou au Pi) de s'assurer que seule une pièce de 2 €, côté face, passe devant la caméra pays.
- `pyproject.toml` (non modifié) : `requests` n'est pas déclaré dans les dépendances (il est
  installé indirectement), et `serial>=0.0.97` n'est pas le bon paquet pour le port série (le bon
  est `pyserial`). À corriger après revue d'équipe, car ce fichier est commun.
