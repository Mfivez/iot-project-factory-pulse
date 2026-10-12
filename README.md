# FactoryPulse 🏭

**Monorepo pédagogique Industrie 4.0** : trois équipes développent en parallèle la surveillance machine, la vision et le dashboard. Un module transversal prépare le diagnostic IA en lecture seule.

> **Statut : modules en cours d'intégration.** Le dashboard de replay et les quatre outils de consultation de l'agent sont implémentés. La vision propose des démonstrations webcam YOLO/OpenCV, encore sans export d'inspections JSONL. Les mesures et inspections fournies dans `data/` sont **synthétiques** ; les règles M01, le diagnostic IA, MCP, MQTT et l'acquisition physique restent à développer.

## 1. Qui développe quoi ?

| Partie | Équipe | Mission |
|---|---|---|
| `src/factorypulse/monitoring/` | 1 | Température, vibrations, anomalies, futur Raspberry M01 |
| `src/factorypulse/vision/` | 2 | YOLO, OpenCV, futur HUSKYLENS, inspection Q01 |
| `src/factorypulse/dashboard/` | 3 | Streamlit, événements, indicateurs et alertes |
| `src/factorypulse/agent/` | Transversal | Outils de lecture et futur diagnostic/MCP |
| `src/factorypulse/shared/` | Commun | Contrat JSONL et utilitaires validés |
| `src/factorypulse/transport/` | Intégration | MQTT ultérieurement |

Chaque dossier contient un **`AGENTS.md`** ; lire celui de la racine puis celui du module pour travailler avec Codex.

## 2. Installation

Python **3.11+** et Git. Sur Windows :

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Sur Linux / macOS :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Ajouter seulement les dépendances nécessaires, sur les **PC** :

```bash
python -m pip install -e ".[vision,dev]"       # equipe 2
python -m pip install -e ".[dashboard,dev]"    # equipe 3
```

Les dépendances YOLO peuvent être lourdes et ne sont pas requises sur les Raspberry Pi 3. Le module `agent` et MQTT ne sont pas obligatoires pour le labo initial.

## 3. Vérifier que le dépôt fonctionne

```bash
python scripts/validate_contract.py
python -m pytest
python -m factorypulse.monitoring.main
python -m factorypulse.vision.main
```

Ces deux dernières commandes inspectent les **entrées existantes**, elles ne réalisent pas encore l'analyse métier.

Pour les démonstrations vision, avec l'extra `vision` installé et une webcam disponible :

```bash
python -m factorypulse.vision.main --webcam   # YOLO : objets et couleurs
python -m factorypulse.vision.main --colors   # OpenCV : rouge et vert
```

La caméra démarre uniquement avec l'une de ces options. YOLO peut télécharger
ses poids au premier lancement. Ces démonstrations ne produisent pas encore
les décisions `PASS`/`REJECT`/`UNKNOWN` ni le fichier `data/outputs/q01.jsonl`.

Pour le dashboard (si les dépendances ont été installées) :

```bash
python -m streamlit run src/factorypulse/dashboard/app.py
```

Le dashboard montre **les fixtures de replay**, pas des capteurs en direct. Ne jamais comparer les horodatages du replay à l'heure courante.

## 4. Données de départ

- `data/inputs/machine.csv` : 300 mesures synthétiques M01, dont des données manquantes.
- `data/inputs/acceleration_xyz.csv` : exercice facultatif de calcul RMS à partir des axes.
- `data/inputs/prises_de_vue.csv` : les **six photos à réaliser** par l'équipe 2 ; aucune image fournie.
- `data/fixtures/m01.jsonl` : exemple de traitement machine.
- `data/fixtures/q01.jsonl` : 6 inspections uniques + 1 doublon exact volontaire.
- `data/fixtures/systeme.jsonl` et `logs.jsonl` : santé système et logs simulés.
- `config/factorypulse.json` : seuils pédagogiques et paramètres du replay.

**Sources de vérité :** `docs/DATA_CONTRACT.md` et `config/factorypulse.json`. Les sorties locales vont dans `data/outputs/` (ignorées par Git).

## 5. Collaboration Git

- Une branche par fonctionnalité : `feat/monitoring-rules`, `feat/vision-yolo`, `feat/dashboard-metrics`.
- Une Pull Request par fonctionnalité, revue par au moins une autre personne.
- Ne pas casser `shared/` sans accord collectif ; toutes les équipes en dépendent.
- Ajouter des tests et un README pour tout changement de module.
- Ne jamais pousser `.env`, données personnelles, poids de modèles ou gros fichiers générés.

Voir `docs/DEVELOPMENT.md` et `docs/MISSIONS.md`.

## 6. Premier push GitHub

Depuis le dossier `factorypulse-monorepo` :

```bash
git init -b main
git add .
git commit -m "chore: initialize FactoryPulse monorepo"
git remote add origin https://github.com/TON-COMPTE/TON-DEPOT.git
git push -u origin main
```

Créer le dépôt vide sur GitHub avant de lancer ces commandes et remplacer l'URL. Choisir et ajouter une licence `LICENSE` si vous souhaitez publier le code comme open source. Le dépôt est fourni **sans historique `.git`** : c'est vous qui choisissez le propriétaire et les accès.

## Sécurité

Aucun GPIO moteur n'est commandé par ce socle. Le futur agent IA n'aura que des outils de **consultation**, pas d'exécution de commandes arbitraires. Ne pas connecter directement un moteur aux GPIO. Consulter `docs/HARDWARE.md`.
