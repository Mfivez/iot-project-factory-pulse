from fastapi import APIRouter, HTTPException


from devices.servo2 import tourner_droite

router = APIRouter(prefix="/servo2", tags=["SERVO"])



@router.post("/activer")
def recevoir_resultat():
    try:
        tourner_droite()
    except:
        raise HTTPException(status_code=400, detail="Erreur")
    return {"status": "ok"}


