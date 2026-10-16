"""Point d'entrée de l'équipe 2 : inventaire des six images à réaliser."""

from __future__ import annotations
import argparse
import csv
from pathlib import Path
import requests
import serial
import time
from factorypulse.vision.detection_euro import detect_euro
from factorypulse.vision.detection_pays_2euros import detect_country_coins
from concurrent.futures import ProcessPoolExecutor


def inspect_manifest(manifest: Path, images: Path) -> list[dict[str, str | bool]]:
    with manifest.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [
        {
            "file": row["file"],
            "scene": row["scene"],
            "present": (images / row["file"]).is_file(),
        }
        for row in rows
    ]

def resultat(future, nom):
    try:
        return future.result(timeout=5)
    except Exception as e:
        print(f"Détection {nom} en échec : {e!r}")
        return None


def main() -> None:
    
    RASPBERRYPI_PORT = 8000
    RASPBERRYPI_IP = "192.168.50.2"    
 
    url = f"http://{RASPBERRYPI_IP}:{RASPBERRYPI_PORT}/servo"
    session = requests.Session()

    with ProcessPoolExecutor(max_workers=2) as pool:

        
        print("Ctrl+C pour arrêter.")
        
        while True:
            
            url = f"http://{RASPBERRYPI_IP}:{RASPBERRYPI_PORT}/servo"
                      
            
            f_euro = pool.submit(detect_euro, 1)
            f_pays = pool.submit(detect_country_coins, 0)
            
            type_euro = resultat(f_euro, "type")
            type_pays = resultat(f_pays, "pays")
            
            if type_euro is None and type_pays is None:
                continue
            
            try:
                            
                envoye =None
            
                if type_euro is not None:
                    print("hello poto j'ai détecté un euro")
                    playload_euro = {"result": f_euro}
                    envoye = playload_euro
                    url = f"{url}{"/resultat1"}"
                    
                    r = session.post(url, json=playload_euro, timeout=3)
                    r.raise_for_status()
                    
                if type_pays is not None:
                    playload_pays = {"result": f_pays}
                    envoye = playload_pays
                   
                    url = f"{url}{"/resultat2"}"                   
                    r = session.post(url, json=playload_pays, timeout=3)
                    r.raise_for_status()
                  
                print(f"Envoyé : {envoye}")
            except requests.RequestException as e:
                print(f"Échec d'envoi ({e}) — ligne perdue : ")
                time.sleep(1) 

if __name__ == "__main__":
    main()
