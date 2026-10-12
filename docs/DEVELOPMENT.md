# Travail Git en équipe

## Workflow conseillé
1. Un mainteneur initialise `main` avec ce squelette.
2. Inviter les étudiants sur le dépôt GitHub ; configurer une protection de `main` si disponible.
3. Une branche par évolution : `feat/monitoring-rules`, `feat/vision-yolo`, `feat/dashboard-charts`.
4. Pull Request avec description, tests, exemple de sortie et captures si interface.
5. Revue par une personne extérieure au changement avant fusion.

## Nommage
- Modules en anglais, documentation en français.
- `M01` = surveillance machine, `Q01` = inspection, `SERVER` = collecte.
- Format d'événements imposé par `docs/DATA_CONTRACT.md`.
- Tests : `tests/<module>/test_*.py` ou `tests/test_*.py`.

## Dépendances
Pas de dépendances massives dans le noyau partagé. Déclarer les bibliothèques
propres à une équipe dans les `optional-dependencies` de `pyproject.toml`.
Ne pas installer PyTorch/YOLO sur les Pi 3 sans avoir mesuré la faisabilité.

## Integrité des données
`data/inputs` et `data/fixtures` sont des références synthétiques fournies.
`data/outputs` est ignoré par Git. Un changement de fixture doit être explicite
en PR, documenté et validé par les trois équipes.

## Relecture humaine obligatoire
Toute modification de contrat, sécurité, communication, câblage ou commande machine.
