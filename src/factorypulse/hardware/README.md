# Trieur de pièces — premiers essais

## Prérequis

- Raspberry Pi 3B+ avec Raspberry Pi OS et la bibliothèque Python gpiozero.
- Servo SG90 et moteurs alimentés par une source 5 V séparée.
- Un 28BYJ-48 et un module ULN2003 par moteur.
- Masse commune entre l'alimentation externe et le Raspberry Pi.

## Essais

Lancer un seul essai à la fois depuis le dossier du projet :

    python3 main.py servo
    python3 main.py moteur1
    python3 main.py moteur2
    python3 main.py cycle

Le deuxième moteur exige son propre module ULN2003.
Le mode cycle répète le mouvement du servo, puis celui du moteur 1, puis celui du moteur 2.
Arrêter le mode cycle avec Ctrl+C.

## Réglages

Modifier les angles, les positions du servo, les pauses et le délai entre demi-pas dans config.py.
Dans le mode cycle, le moteur 1 fait 10° puis revient de 5°, répété 72 fois pour un tour net de 360° ; le moteur 2 tourne de 180°.
Le délai entre les pas du moteur 1 et les pauses sont réglables dans config.py.
Les GPIO de la configuration utilisent la numérotation BCM.

Le code ne commande pas le solénoïde.
