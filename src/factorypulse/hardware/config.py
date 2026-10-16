"""Réglages faciles à adapter après les premiers essais sur le mécanisme."""

# Numéros GPIO en mode BCM, pas les numéros physiques du connecteur.
  # Le signal du servo utilise le GPIO23.
STEPPER_1_GPIOS = (17, 18, 27, 22)  # Ces GPIO pilotent le premier module ULN2003.
STEPPER_2_GPIOS = (5, 6, 13, 19)  # Ces GPIO pilotent le second module ULN2003.

# ==== CONFIG SERVO 1 & 2 ==== 
# Positions relatives du servo, de -1 à +1.
SERVO1_GPIO = 12
SERVO2_GPIO = 13
 # !!!! à changer

SERVO1_TEMPS_MOUVEMENT = 1.5  # Cette durée laisse le servo atteindre sa position.
SERVO1_PAUSE = 1  # Cette durée sépare les mouvements du servo.
SERVO1_ZERO = 0
SERVO1_ANGLE_DROITE = 90
SERVO1_ANGLE_GAUCHE = -90

SERVO2_TEMPS_MOUVEMENT = 1.5
SERVO2_PAUSE = 2
SERVO2_ZERO = 0
SERVO2_ANGLE_DROITE = -90




# ===== MOTEUR 1 ======
# Les angles signés des deux moteurs sont exprimés en degrés.
# Le premier moteur fait 10° dans le sens inverse choisi, puis revient de 5°.
MOTEUR_1_MOUVEMENT_PAIRE_DEGRES = (-10.0, 5.0)
# Chaque paire fait avancer le moteur de 5° nets dans le sens inverse.
MOTEUR_1_NOMBRE_DE_PAIRES = 72*2
# Soixante-douze paires donnent un tour complet net de 360°.
MOTEUR_1_MOUVEMENTS_DEGRES = MOTEUR_1_MOUVEMENT_PAIRE_DEGRES * MOTEUR_1_NOMBRE_DE_PAIRES
MOTEUR_2_MOUVEMENTS_DEGRES = (180.0,)  # Le deuxième moteur fait un demi-tour par cycle.

# Valeur nominale approximative en demi-pas pour un tour de sortie du 28BYJ-48.
DEMI_PAS_PAR_TOUR = 4096  # Cette valeur sert de base de conversion degrés-vers-pas.
DELAI_ENTRE_DEMI_PAS = 0.003  # Cette durée règle la vitesse des moteurs.
DELAI_MOTEUR_1 = 0.001  # Ce délai plus court accélère les pas du premier moteur.
PAUSE_ENTRE_MOUVEMENTS = 0.01  # Cette pause courte accélère l'enchaînement des mouvements.
