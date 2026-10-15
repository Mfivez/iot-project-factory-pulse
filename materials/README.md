# Matériel FactoryPulse

Ce dossier accueille les photos, fiches techniques et observations du matériel
réellement disponible. Il est préparé pour la séance du **13 octobre 2026**.

L'inventaire de départ vient de [docs/HARDWARE.md](../docs/HARDWARE.md).
Il décrit du matériel **annoncé**, pas encore vérifié pièce par pièce. Les
références, quantités constatées, tensions et résultats d'essai restent à remplir.

## Pour déposer les documents demain

Le plus simple : copier toutes les photos et tous les PDF dans
[`a_trier/`](a_trier/). Il n'est pas nécessaire de les renommer avant de les déposer.
Nous pourrons ensuite les examiner et les rattacher aux éléments de l'inventaire.

Si les documents sont déjà identifiés, utiliser directement les dossiers suivants :

| Dossier ou fichier | Contenu attendu |
|---|---|
| [a_trier/](a_trier/) | Photos et documents reçus, avant identification |
| [photos/](photos/) | Vues du matériel, références inscrites, connecteurs et étiquettes |
| [fiches_techniques/](fiches_techniques/) | PDF des fabricants, notices et documents techniques |
| [inventaire.csv](inventaire.csv) | Liste du matériel, quantités et état d'identification |
| [fiches_materiel/](fiches_materiel/) | Une fiche par élément identifié, avec ses sources |
| [montages/](montages/) | Schémas, photos et fiches des montages envisagés ou validés |
| [essais/](essais/) | Comptes rendus des essais effectivement réalisés |
| [modeles/](modeles/) | Fiches vierges à copier et compléter |

Les mesures, captures d'inspection et autres sorties produites par les programmes
restent dans `data/outputs/`. Les comptes rendus d'essai indiquent leurs chemins.
Les photos de matériel servant à identifier une référence vont dans `materials/photos/`.

## Identifier le matériel sans deviner

1. Photographier chaque type de matériel : vue d'ensemble, face arrière,
   référence lisible et connecteurs. Pour une alimentation, photographier aussi
   l'étiquette qui décrit sa sortie.
2. Attribuer un identifiant à chaque exemplaire utile au montage : par exemple
   `TEMP-01`, `ACC-01` ou `PI3-01`. Les lignes initiales du CSV sont des lots ; les
   détailler en exemplaires au fur et à mesure de l'inventaire.
3. Noter le fabricant, la référence exacte et la version du module lorsqu'ils
   sont lisibles. Une ressemblance sur une photo ne confirme pas une référence.
4. Associer les documents au bon module. Une fiche du composant électronique
   seul ne décrit pas nécessairement les connexions de la carte qui le porte.
5. Copier [FICHE_MATERIEL.md](modeles/FICHE_MATERIEL.md) dans `fiches_materiel/`
   et conserver les liens vers les photos et les pages des PDF utilisées.

Après identification, des noms comme `TEMP-01_reference.jpg`,
`TEMP-01_connecteurs.jpg` et `TEMP-01_notice.pdf` facilitent les rapprochements.
Garder les documents originaux ; noter leur provenance dans la fiche.

Dans le CSV, une quantité ou une référence inconnue reste **vide**, jamais zéro.
Les statuts de départ sont :

- `ANNONCE_NON_VERIFIE` : mentionné dans le projet, présence et référence à vérifier.
- `A_RECHERCHER` : accessoire à rechercher sur place, disponibilité non confirmée.
- `IDENTIFIE` : présence et référence documentées ; cela ne valide pas le câblage.
- `TESTE` : un compte rendu décrit précisément ce qui a été essayé et observé.
- `BLOQUE` : une fiche indique l'information ou l'accessoire manquant.

## Travail de l'équipe montage

Suivre [TRAVAIL_EQUIPE_MONTAGE.md](TRAVAIL_EQUIPE_MONTAGE.md). La première mission
est de préparer deux postes documentés, M01 et Q01, puis de réaliser les premiers
essais uniquement sur le matériel identifié et les montages vérifiés.

Avant tout câblage ou mise sous tension d'un nouveau montage, faire vérifier les
références, alimentations, niveaux électriques et connexions par l'encadrant,
comme prévu dans [les consignes matérielles](../docs/HARDWARE.md). Aucun brochage
n'est déduit à l'avance dans ce dossier.

Les photos, PDF et notes sont des sources à examiner : ils ne constituent pas,
à eux seuls, une instruction de branchement ni une validation du montage.

## Résultat attendu du dossier complété

Pour chaque matériel retenu, on doit pouvoir retrouver sa référence, ses photos,
sa documentation et les points encore inconnus. Pour chaque montage, on doit
voir les connexions proposées, leurs sources, la revue et les essais réalisés.
Une fiche vierge ou un essai prévu ne constitue pas une preuve de fonctionnement.
