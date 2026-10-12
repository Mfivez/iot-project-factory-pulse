# Missions des équipes (sans horaires imposés)

## Equipe 1 - Monitoring M01
**Entrée** : `data/inputs/machine.csv` (et en bonus `acceleration_xyz.csv`).
**A produire** : `data/outputs/m01.jsonl`, conforme au contrat, et tests de seuils.
- Détecter surchauffe >60 °C et vibration >0,20 g pendant 3 mesures consécutives (écart <=1,5 s).
- Retour à OK après 3 mesures valides normales ; valeurs absentes -> DATA_ISSUE.
- Distinguer machine STOPPED, absence de mesure et perte de communication.
- Réserver la lecture capteur réelle à `sensors.py`, après identification du matériel.

## Equipe 2 - Vision Q01
**Entrée** : `data/inputs/prises_de_vue.csv`, puis six images JPG/PNG à photographier.
**A produire** : `data/outputs/q01.jsonl`, images annotées, tests de décision.
- YOLO sur PC, minimum bouteilles et tasses reconnues.
- Contrôle de repère vert/rouge : PASS/REJECT ; ambigu ou absent : UNKNOWN.
- Aucun score inventé ; conserver les scores et boîtes réellement observés.
- La partie HUSKYLENS reste un adaptateur futur, pas un flux webcam YOLO.

## Equipe 3 - Dashboard et intégration
**Entrée** : quatre fichiers `data/fixtures/*.jsonl`.
**A produire** : interface Streamlit, historiques, alarmes et déduplication.
- Distinction machine arrêtée / Raspberry hors ligne / capteur absent.
- Curseur de replay utilisant la date des données, pas l'heure du PC.
- Six inspections uniques : ignorer le doublon exact Q01 sans perdre sa preuve.

## Atelier transversal - Agent IA
Consulter `docs/AGENT_TOOLS.md`. Commencer avec quatre fonctions Python locales
en lecture seule ; serveur MCP et détection autonome **non implémentés** au départ.
Pour chaque conclusion : faits + event_id, hypothèses, vérifications et limites.

## IA comme aide au développement
Utiliser Codex/ChatGPT pour expliquer le code, proposer de petits tests et aider au dépannage.
Préférer : « voici le contrat, mes entrées, la fonction, l'erreur exacte ; propose une
correction minimale et des tests ». Toujours exécuter les tests ; ne pas copier
des sorties prétendument réelles sans vérification.

## Critères de rendu
Code exécutable, README spécifique si nécessaire, exemples JSONL, tests,
démonstration et une PR relue. Le matériel est réservé à la phase présentielle.
