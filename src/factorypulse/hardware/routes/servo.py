from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from devices.servo1 import tourner_gauche, tourner_droite

router = APIRouter(prefix="/servo", tags=["SERVO"])


class ResultatDetection(BaseModel):
    result: str


@router.post("/resultat1")
def recevoir_resultat(donnee: ResultatDetection):
    if donnee.result == "euro":
        tourner_gauche()
        print("doit tourner à gauche")
    elif donnee.result == "paseuro":
        tourner_droite()
        print("doit tourner à gauche")
    else:
        raise HTTPException(status_code=400, detail="Valeur de result inconnue")
    return {"status": "ok"}


