# Matériel disponible, à vérifier avant câblage

Inventaire communiqué : environ 10 Raspberry Pi 3B, 2 Raspberry Pi 4B, PC, kit HUSKYLENS, détecteur infrarouge de mouvement, moteur, ventilateur, capteurs de température, accéléromètre, rack et diverses résistances.

## Vérifications obligatoires
- Référence exacte de l'accéléromètre et du/des thermomètres (brochages différents selon module).
- Déterminer si le détecteur infrarouge est un **PIR de mouvement** ou une **barrière infrarouge de passage**. Un PIR ne compte pas de façon fiable des pièces.
- Confirmer HUSKYLENS présent, son modèle et son câble de données.
- Vérifier alimentations de Pi 3B (micro-USB) et Pi 4B (USB-C), et cartes SD.
- Vérifier les niveaux électriques des modules avant GPIO : logique Pi en 3,3 V.
- Alimenter séparément le moteur/ventilateur, avec protection mécanique et électrique ; ne jamais le brancher aux GPIO.

## Organisation future
- Equipe 1 : adapter `sensors.py` aux capteurs identifiés, recalibrer les seuils sur mesures réelles.
- Equipe 2 : adapter `huskylens.py` et `detector.py` à la caméra et aux modèles réellement testés.
- Equipe 3 : lire le stockage/MQTT une fois la collecte validée.

**Ce dépôt ne contient volontairement aucun plan de câblage imposé pour les modules non identifiés.** Les premiers essais sont réalisés sur les données synthétiques.
