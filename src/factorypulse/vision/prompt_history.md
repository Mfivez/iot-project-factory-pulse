# Historique des détections : export JSONL + JPEG

# Objectif

Lorsqu'un objet est détecté de manière suffisamment stable, enregistrer un événement de détection comprenant :
- Une entrée dans un fichier JSONL.
- Une capture JPEG annotée correspondant à l'image réellement affichée à l'utilisateur.

L'implémentation doit être propre, modulaire et maintenable, sans modifier le projet `dashboard` pour le moment.

## 1. Conditions de déclenchement

- Une détection doit être maintenue pendant au moins **1 seconde** avant d'être considérée comme valide.
- Ignorer les détections trop brèves, intermittentes ou susceptibles d'être de faux positifs.
- Une fois la détection validée, générer **un événement par seconde** tant que l'objet reste détecté.
- Si l'objet disparaît, arrêter la génération des événements associés. Si l'objet est détecté à nouveau, appliquer de nouveau la période de validation d'une seconde.
- La détection des visages ne doit jamais déclencher la génération de données. Les autres classes d'objets détectées par YOLO restent éligibles.

Éviter de générer plusieurs événements par seconde pour une même détection logique. Si nécessaire, s'appuyer sur un suivi des objets existant dans le projet.

## 2. Export JSONL

Enregistrer les événements dans :

`data/history.jsonl`

Chaque événement doit occuper **une seule ligne au format JSONL**, sans tableau JSONL englobant l'ensemble des événements.

Structure d'un événement :

```json{"id": 1,"timestamp": "2026-10-13T09:30:00.000Z","object_type": "bottle","color": "red","image_path": "data/images/captures/capture_20261013T093000000Z.jpg","confidence": 0.95,"source": "webcam_0","anomaly": null}```

### Champs

| Champ | Type | Description |
|---|---|---|
| `id` | INTEGER | Identifiant unique de l'événement, équivalent à une clé primaire. |
| `timestamp` | TEXT | Date et heure UTC au format ISO 8601, avec suffixe `Z`. |
| `object_type` | TEXT | Classe YOLO détectée : `person`, `bottle`, etc. |
| `color` | TEXT ou null | Couleur estimée de l'objet, si disponible. |
| `image_path` | TEXT | Chemin relatif du JPEG annoté associé à l'événement. |
| `confidence` | REAL ou null | Score de confiance de la détection YOLO. |
| `source` | TEXT | Source de la détection : fichier JPEG ou identifiant de webcam, selon la source réelle. |
| `anomaly` | TEXT ou null | Champ réservé à une future détection d'anomalies. Toujours `null` pour le moment. |

### Contraintes

- Générer un identifiant unique et stable pour chaque événement, y compris après le redémarrage de l'application.
- Ajouter chaque événement à la fin du fichier, sans écraser les événements précédents.
- Garantir que chaque ligne soit un objet JSON valide et indépendant.
- Créer automatiquement le répertoire `data/` s'il n'existe pas.
- Écrire les données de manière sûre afin d'éviter les lignes incomplètes ou corrompues en cas d'interruption.


## 3. Export des images JPEG

Enregistrer les captures dans :

`data/images/captures/`

Convention de nommage :

`capture_<timestamp>.jpg`

Le timestamp utilisé dans le nom doit être unique, basé sur la date et l'heure UTC, afin d'éviter les collisions.

### Contenu de l'image

La capture doit représenter **exactement l'image visible par l'utilisateur au moment de l'enregistrement**, avec les annotations déjà appliquées :
- Bounding boxes colorées.
- Labels des classes détectées.
- Scores de confiance, s'ils sont affichés dans l'interface.
- Toute autre annotation visuelle déjà présente sur l'image affichée.

Ne pas enregistrer une image brute si l'interface affiche une version annotée.

Éviter de dupliquer inutilement le traitement d'image existant. Réutiliser de préférence l'image annotée déjà produite par le pipeline de détection.

Le champ `image_path` de l'événement JSONL doit référencer le JPEG correspondant.

## 4. Architecture et maintenabilité

Implémenter cette fonctionnalité dans une **fonction ou un module dédié**, distinct du code principal de détection et d'affichage.

Responsabilités à isoler autant que possible :
- Validation temporelle des détections.
- Gestion de la fréquence de génération des événements.
- Création et sauvegarde des JPEG annotés.
- Génération des événements JSONL.
- Gestion des identifiants et des chemins de fichiers.

Réutiliser les fonctions, structures de données et mécanismes de suivi déjà présents dans le projet vision lorsque c'est pertinent.

Éviter :
- La duplication de logique existante.
- Le mélange de la logique d'export avec le rendu de l'interface.
- Les variables globales inutiles.
- Les dépendances supplémentaires qui ne sont pas nécessaires.
- Les modifications qui risquent de perturber le fonctionnement actuel de la détection.

Respecter les conventions de code existantes et conserver une architecture simple, lisible et facile à faire évoluer.

## 5. Gestion des erreurs

- Créer automatiquement les répertoires de destination.
- Gérer les erreurs de lecture et d'écriture des fichiers.
- Ne pas ajouter au JSONL un événement qui référence une image dont la sauvegarde a échoué.
- Journaliser les erreurs de manière explicite sans interrompre inutilement la détection en cours.
- Éviter les accès concurrents dangereux au fichier d'historique.

## 6. Périmètre

Cette fonctionnalité prépare les données pour un futur système de visualisation et d'analyse via Streamlit dans le projet `dashboard`.

Pour le moment :
- Ne pas modifier le projet `dashboard`.
- Ne pas implémenter de graphiques ni d'analyse d'anomalies.
- Ne pas implémenter de base de données supplémentaire.
- Se concentrer uniquement sur la détection stable, l'export JSONL et la sauvegarde des images.

## 7. Consignes d'implémentation

Avant de modifier le code :
1. Examiner l'architecture actuelle du projet et identifier le pipeline de détection YOLO.
2. Identifier comment les images annotées sont produites et affichées.
3. Identifier comment les sources JPEG et webcam sont représentées.
4. Déterminer comment distinguer une détection persistante d'une nouvelle détection.

Ensuite, implémenter la fonctionnalité en réutilisant au maximum l'existant.

À la fin, fournir un résumé des modifications réalisées, des fichiers créés ou modifiés et des éventuelles décisions techniques importantes.


n'oublie pas, tout le code (hors exports) se trouve dans src/factorypulse/vision