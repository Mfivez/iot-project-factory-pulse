# AGENTS - Equipe 1 / monitoring M01
Entrées : `data/inputs/machine.csv`, bonus `acceleration_xyz.csv`.
Sortie cible : `data/outputs/m01.jsonl`, format `docs/DATA_CONTRACT.md`.

- Développer dans `simulator.py`, `rules.py`, `sensors.py` et `main.py`.
- Surchauffe >60 °C, vibration >0,20 g : 3 mesures consécutives, espacées <=1,5 s.
- Retour OK après 3 mesures valides normales ; donnée manquante => DATA_ISSUE.
- Ne jamais remplacer une donnée absente par zéro.
- Calcul RMS sur accélérations **dynamiques**, après retrait de la gravité/composante statique.
- Séparer simulation et acquisition réelle ; ne jamais simuler une panne comme un relevé mesuré.
- Ne pas commander un moteur par GPIO ; matériel après identification et validation électrique.
- Ajouter tests `tests/monitoring/` ; éviter toute modification de `vision/` et `dashboard/`.
