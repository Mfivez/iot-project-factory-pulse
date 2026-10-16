"""Point d'entrée de l'API de tri des pièces."""
from fastapi import FastAPI
from gpiozero import AngularServo


from routes.servo import router as servo_router
from routes.moteur import router as moteur_router
from routes.servo2 import router as servo2_router
# Création du serveur API
app = FastAPI()
app.include_router(servo_router)
app.include_router(moteur_router)
app.include_router(servo2_router)

# Initialisation du servo2 (en attente d'intégration).


def main():
    pass

# Ce garde empêche le programme de démarrer lors d'un import comme module.
if __name__ == "__main__":
    # L'appel lance l'essai choisi en exécution directe.
    main()
