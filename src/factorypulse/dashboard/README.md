# Dashboard FactoryPulse

## Vue atelier : deux caméras

La page d'accueil présente les postes « Contrôle d'entrée » et « Identification
du pays ». La navigation reprend l'organisation des maquettes IBC : menu latéral
clair, onglets supérieurs et cartes compactes. Seuls les onglets **Caméras** et
**Réglages** sont affichés. Le replay pédagogique, les indicateurs moteur/cycle,
les résultats de détection et l'historique sont retirés de l'interface.
Les fixtures et les fonctions de lecture existantes restent dans le dépôt,
mais cette application ne les charge pas.

Ouvrir l'onglet **Réglages**, renseigner les adresses HTTP(S) directes
des flux **MJPEG**, puis cliquer sur **Appliquer les sources**. Une adresse vide
débranche le lecteur correspondant. Les adresses sont conservées dans la session
du navigateur, pas dans le dépôt. Chaque lecteur gère séparément la connexion,
l'absence d'image (délai de 10 secondes) et la reprise manuelle. Le bouton
**Suspendre les aperçus** coupe seulement les connexions vidéo de cette page.
Quitter l'onglet Caméras libère également les lecteurs. Les sources appliquées
et la suspension restent mémorisées pendant la navigation.

Les aperçus adaptent leur hauteur à la fenêtre, pour conserver une vue compacte
sur ordinateur. Aucun `overflow: hidden` global ne masque du contenu : sur mobile
ou à fort zoom, les éléments restent accessibles par défilement si nécessaire.
Les onglets ont été vérifiés dans Chromium à 100 % de zoom, avec des fenêtres
de 1280 × 720, 1366 × 768, 1440 × 900 et 1920 × 1080 : aucun défilement de page
avec le contenu actuel. Les deux lecteurs ont
aussi été vérifiés avec des flux MJPEG synthétiques ; les caméras physiques
restent à raccorder et à valider sur le poste.

Le navigateur reçoit les images directement : le dashboard ne charge aucun
modèle, n'ouvre aucune webcam et ne lance aucun calcul de vision. Les deux flux
doivent être produits par le poste vision, idéalement à partir des images déjà
capturées/annotées. Ce producteur n'est pas encore implémenté dans le dashboard.
Les index USB, URL RTSP et pages WebRTC ne sont pas acceptés comme flux MJPEG.

Depuis un autre ordinateur, utiliser l'adresse réseau du PC vision et non
`localhost` (qui désigne alors l'ordinateur du visiteur). Une page HTTPS exige
un flux HTTPS ; les restrictions réseau du navigateur restent applicables.

**Image reçue** signifie seulement qu'une image a pu être affichée : ce lecteur
ne dispose ni d'horodatage de trame ni de preuve de fraîcheur du flux. Un MJPEG
figé peut rester visible. Les décisions, scores, cycles et états du Raspberry
ne sont pas affichés. Une commande logicielle ne prouve pas un mouvement réel :
un éventuel suivi moteur devra distinguer les consignes des mesures physiques.
Aucune commande moteur n'est disponible. Le contrat FP-LAB-1.1 reste inchangé.

Vérifications ciblées :

```bash
python -m pytest tests/dashboard
python scripts/validate_contract.py
```

## Lancement

Depuis la racine du dépôt, installer l'option du module puis lancer :

```powershell
python -m pip install -e ".[dashboard,dev]"
python -m streamlit run src/factorypulse/dashboard/app.py
```
