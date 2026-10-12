# Dashboard FactoryPulse

Le dashboard Streamlit explore les fixtures synthétiques FP-LAB-1.1. Il présente
la télémétrie M01, les états distincts de la machine, du capteur et des nœuds,
les inspections Q01 uniques et les incidents avec leurs `event_id` de preuve.

Depuis la racine du dépôt, installer l'option du module puis lancer :

```powershell
python -m pip install -e ".[dashboard,dev]"
python -m streamlit run src/factorypulse/dashboard/app.py
```

Le curseur rejoue les événements jusqu'à une date UTC issue de
`config/factorypulse.json`. L'horloge système n'est pas utilisée pour interpréter
la fraîcheur. Les mesures manquantes restent absentes et les fixtures ne sont
jamais modifiées. Ces données ne représentent pas des capteurs en direct.
