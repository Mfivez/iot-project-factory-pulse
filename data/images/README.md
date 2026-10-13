# Images de test de l'équipe 2

Six images photoréalistes synthétiques ont été générées avec l'outil intégré
`imagegen` le 13 octobre 2026 et partagées dans ce dossier. Elles
reprennent les noms et les scènes de `../inputs/prises_de_vue.csv`.
Ce ne sont pas des photos du matériel réel.

| Fichier | Scène | Verdict attendu |
| --- | --- | --- |
| `01_bouteille_verte.jpg` | Bouteille avec pastille verte | PASS |
| `02_tasse_verte.jpg` | Tasse avec pastille verte | PASS |
| `03_bouteille_rouge.jpg` | Bouteille avec pastille rouge | REJECT |
| `04_tasse_rouge.jpg` | Tasse avec pastille rouge | REJECT |
| `05_bouteille_sans_repere.jpg` | Bouteille sans pastille | UNKNOWN |
| `06_scene_vide.jpg` | Fond vide | UNKNOWN |

Les verdicts ci-dessus sont des objectifs du manifeste, pas des résultats
mesurés. Ces images servent à préparer l'analyse ; elles ne remplacent pas
les prises de vues et la validation sur le matériel réel. Aucun résultat
YOLO ni événement Q01 n'est fourni avec ce lot.

Les prompts exacts et la provenance sont enregistrés dans
[`generation_prompts.json`](generation_prompts.json). Les originaux PNG ont
été convertis en JPEG sans recadrage ni redimensionnement.

Le point d'entrée vérifie seulement la présence des six fichiers :

```bash
python -m factorypulse.vision.main
```

Ces six images synthétiques et leur fichier de provenance sont versionnés
pour permettre à l'équipe de tester sans appareil photo ni webcam. Les noms
des PNG d'origine sont conservés comme identifiants de génération ; seuls
les JPEG sont fournis dans le dépôt.

Les autres fichiers ajoutés dans ce dossier restent ignorés par Git pour
éviter de publier involontairement des photos privées. Les fixtures de replay
dans `data/fixtures/` restent inchangées.
