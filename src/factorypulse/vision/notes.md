# YOLO

# Résumé

Famille de modèles IA qui permet d'analyser une image ou vbidéo pour reconnaiter des objets, les localiser, et, pour certains modèles, d'identifier certaines actions.

Peut détecter des objets en temps réel et dessiner un rectangle autour de chaque objet détecté.

# Fonctionnement

1. Image ou vidéo
   Webcam, caméra IP, fichier vidéo ou photo

2. Modèle YOLO
   Analyse l'image et calcule les prédictions

3. Détections
   Classe, position, score de confiance

4. Application
   Affichage, comptage, alerte, automatisation ou stockage

## Trois informations essentiells d'une détection

1. La classe (**class**) : Ce que le modèle pense avoir reconnu - une personne, une couleur, etc...

2. Position (**bouding box**) : Rectangle défini par les coordonnées qui indiquent où se trouve l'objet dans l'image

3. Score de confiance (**confidence**)

## Suppression de redondance

NMS (Non Maximum Suppression) : Mecanisme de suppression des détections redondantes, pour éviter de conserver plusieurs rectangles qui correspondent au même objet.

# Utilisations

1. Détection d'objet : Identifier et localiser plusieurs objets dans une image.

2. Segmentation : Délimiter précisément la forme de chaque objet, au lieu d'un rectangle

3. Estimation de pose : Récupérer les points d'un corps pour déterminer les mouvements

4. Suivi d'objets: Suivre les objets entre lezs images successives d'une vidéo.

5. Classification : Déterminer la catégorie d'une image (ex: Ceci n'est pas une pipe).

6. Boites orientées - OBB (oriented bouding box) : Détecter des objets avec des rectangles inclinés, notamment pour les images aériennes ou les objets disposés en diagonale.

## Plusieurs modèles

Plusieurs modèles +/- grands, on peut aussi en personnaliser

## Comment l'utiliser

Option A — Analyser des images

-> Tu fournis une photo et YOLO retourne les objets détectés. C'est le plus simple pour une première démonstration.

Option B — Analyser une vidéo ou une webcam

-> YOLO traite les images successives. Tu peux afficher les rectangles, compter les objets ou déclencher des alertes.

Option C — Entraîner ton propre modèle

-> Tu lui apprends à reconnaître des classes spécifiques en utilisant des images annotées. C'est généralement l'option la plus intéressante pour démontrer le travail réalisé dans un projet étudiant.

## Exemple de code

Installation package

```
pip install ultralytics
```

Analyser simple image:

```
from ultralytics import YOLO

# Charger un modèle préentraîné
model = YOLO("yolo26n.pt")

# Analyser une image
results = model.predict(
    source="image.jpg",
    conf=0.25, # seuil minimal
    save=True
)
```

Analyser depuis Webcam:

```
from ultralytics import YOLO

model = YOLO("yolo26n.pt")

model.predict(
    source=0,       # Webcam par défaut
    conf=0.4,
    show=True
)
```

Afficher les résultats de détection:

```
for result in results:
    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        name = result.names[class_id]

        print(
            f"{name} : "
            f"{confidence:.2%}"
        )

```

## Reconnaitre objets personnalisés

C'est une partie importante si tu veux aller au-delà d'une simple démonstration.
Imaginons que tu veuilles créer une application qui reconnaît des canettes, des bouteilles et des cartons pour trier des déchets.

Étape 1 — **Collecter des images**
Prends des photos variées : objets isolés, objets superposés, éclairage différent, arrière-plans différents.

Étape 2 — **Annoter les images**
Dessine un rectangle autour de chaque objet et attribue-lui la bonne classe. Des outils comme CVAT ou Label Studio peuvent aider.

Étape 3 — **Organiser le dataset**
Sépare les images en ensembles d'entraînement, de validation et de test.

Étape 4 — **Entraîner le modèle**
Pars d'un modèle préentraîné et ajuste-le avec tes propres images : c'est le fine-tuning.

Étape 5 — **Évaluer les résultats**
Teste le modèle sur des images qu'il n'a jamais vues pendant l'entraînement et mesure sa précision.

### Code

Fichier de config `data.yaml`

```
path: ./dataset

train: images/train # folder image
val: images/val
test: images/test

names:
  0: canette
  1: bouteille
  2: carton
```

```
from ultralytics import YOLO

model = YOLO("yolo26n.pt")

model.train(
    data="data.yaml", # on spécifie le path de la config
    epochs=50,
    imgsz=640,
    batch=16
)
```

# Avantages et limites

Les avantages et les limites de YOLO
Avantages

- Détection rapide, adaptée à de nombreuses vidéos en temps réel.
- Détection de plusieurs objets simultanément.
- Modèles préentraînés faciles à tester.
- Possibilité de personnaliser les classes.
- Écosystème d'outils pour entraîner, évaluer et exporter les modèles.
- Intégration possible dans une application.

Limites

- Peut manquer les objets petits, cachés ou flous.
- Peut se tromper si les images diffèrent trop des données d'entraînement.
- L'entraînement demande des images annotées de qualité.
- Les modèles plus lourds nécessitent davantage de ressources.
- Une détection correcte ne garantit pas une décision correcte.
- Le suivi peut perdre un objet ou changer son identifiant.

# Comment l'intégrer ?

```
Caméra
Image ou flux vidéo
       |
       v
Service d'inférence YOLO
Python + modèle entraîné
       |
       v
API et logique métier
Résultats JSON, règles, historique, alertes
       |
       v
Interface utilisateur
React, tableau de bord, statistiques et vidéo annotée
```

# Licenses

YOLO offre deux types de licenses:

- AGPL 3.0: Pour étudiants et passionnés, ISO

- Enterprise license: Pour developpement et production business, nécessaire pour intégrer dans leur suite logicielle

## Installation

### pip

```
pip install -U ultralytics
```

### docker

```
sudo docker pull ultralytics/ultralytics:latest
sudo docker run -it --ipc=host --device nvidia.com/gpu=all ultralytics/ultralytics:latest
```

## Usage with CLI

```
yolo predict model=yolo26n.pt
```

-> Utilise le modèle pré-entrainé
