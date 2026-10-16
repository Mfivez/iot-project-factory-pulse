from fastapi import APIRouter

from devices.moteur1 import demarrer, arreter

router = APIRouter(prefix="/moteur1", tags=["MOTEUR"])


@router.post("/demarrer")
def demarrer_moteur():
    demarrer()
    return {"status": "ok"}


@router.post("/arreter")
def arreter_moteur():
    arreter()
    return {"status": "ok"}
