# AGENTS - Equipe 2 / vision Q01
Entrée : `data/inputs/prises_de_vue.csv` (six JPG à photographier).
Sortie cible : `data/outputs/q01.jsonl`, plus images annotées dans `data/outputs/`.

- YOLO s'exécute sur PC avec `pip install -e ".[vision,dev]"`, pas automatiquement sur Pi 3.
- Contrôle pédagogique sur bouteille/tasse : vert=PASS, rouge=REJECT, incertain=UNKNOWN.
- Garder le score réel de YOLO ; ne jamais fabriquer une confidence pour HUSKYLENS.
- Une inspection unique par photo, avec event_id et part_id distincts.
- Les photos d'élèves ne doivent pas être ajoutées au Git sans consentement.
- `huskylens.py` reste un adaptateur futur ; ne pas traiter son USB-série comme une webcam.
- Tester images vides, ambiguës, plusieurs objets et confiance insuffisante.
- Pas de modification de `monitoring/` ni des formats communs sans revue.
