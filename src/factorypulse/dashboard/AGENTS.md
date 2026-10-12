# AGENTS - Equipe 3 / dashboard
Entrée initiale : les fichiers JSONL sous `data/fixtures/`.
Livrable : Streamlit, graphiques, incidents, inspections uniques et rejouabilité.

- Toujours dédupliquer par `event_id`, rejeter les collisions contradictoires.
- Distinguer machine STOPPED, capteur DATA_ISSUE et noeud OFFLINE.
- Les données du kit sont un replay terminé en 2026-10-12T09:05:59Z.
  L'horloge de référence est `config/factorypulse.json:replay.as_of_utc`, jamais now().
- Donner l'horodatage des dernières mesures, ne pas présenter des données simulées comme live.
- Conserver les preuves brutes pour le futur agent ; ne pas éditer les fixtures.
- Tests `tests/dashboard/` et revue pour tout changement de `shared/`.
