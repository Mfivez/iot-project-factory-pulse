# Documentation technique — lot Ma17 à Ma32

Collecte du 13 octobre 2026. Les 16 lignes sont référencées dans `catalogue.json`. Aucune ligne de l’inventaire n’a été corrigée par ce lot.

Un document officiel peut concerner seulement le composant ou une famille. Les champs `match_level`, `identification_status` et `limitations` doivent accompagner chaque extrait du futur RAG. Un lien vérifié ne valide ni le montage ni les caractéristiques du matériel physique.

## Résultat par élément

| ID | État | Documents trouvés |
|---|---|---|
| Ma17 | EXACT_DOCUMENT_NOT_FOUND | [ALM2402 LED current-limiting example, SSZTCG5](https://www.ti.com/document-viewer/lit/html/SSZTCG5/GUID-77884168-474E-4268-A0A3-39B3B877146B) — unconfirmed |
| Ma18 | IDENTIFICATION_BLOCKED_PHOTO_MISMATCH | [Alligator Clip Patch Cord AL-B - datasheet](https://www.pomonaelectronics.com/files/datasheets/alligator-clip-patch-cord.pdf) — unconfirmed |
| Ma19 | EXACT_DOCUMENT_NOT_FOUND | [Qi Specification Foreign Object Detection v1.3](https://www.wirelesspowerconsortium.com/media/klfjiwfh/qi-v13-fod.pdf) — family |
| Ma20 | EXACT_DOCUMENT_NOT_FOUND | [General Instructions for Use of Motors](https://www.mabuchi-motor.com/product/knowledge/instructions/) — family |
| Ma21 | MODULE_IDENTIFIED_REVISION_TO_CONFIRM | [HLK-LD2410C-24G product and documentation](https://www.hlktech.com/Goods-239.html) — module ; [HLK-LD2410C manual V1.09](https://r0.hlktech.com/download/HLK-LD2410C-24G/1/HLK%20LD2410C%E7%94%9F%E5%91%BD%E5%AD%98%E5%9C%A8%E6%84%9F%E5%BA%94%E6%A8%A1%E7%BB%84%E8%AF%B4%E6%98%8E%E4%B9%A6V1.09.pdf) — module ; [LD2410C serial protocol V1.09](https://r0.hlktech.com/download/HLK-LD2410C-24G/1/LD2410C%20%E4%B8%B2%E5%8F%A3%E9%80%9A%E4%BF%A1%E5%8D%8F%E8%AE%AE%20V1.09.pdf) — module |
| Ma22 | FAMILY_IDENTIFIED_VARIANT_UNCONFIRMED | [TDS-04C open-frame solenoid family drawing](https://tdsjp.co.jp/product/open/04C.pdf) — family ; [TDS open-frame solenoid families](https://tdsjp.co.jp/product/open.html) — family |
| Ma23 | COMPONENT_DOCUMENTED_BOARD_UNCONFIRMED | [ESP8266EX datasheet v7.1](https://documentation.espressif.com/0a-esp8266ex_datasheet_en.pdf) — component ; [CH340DS1 manufacturer download page](https://www.wch-ic.com/downloads/CH340DS1_PDF.html) — component |
| Ma24 | EXACT_DOCUMENT_NOT_FOUND | [Switches - electrical load and contact protection precautions](https://www.ia.omron.com/product/cautions/40/precautions_for_correct_use.html) — family |
| Ma25 | USER_CONFIRMED_5V_EXACT_DOCUMENT_NOT_FOUND | [San Ace Cooling Fan Manual M0011876C](https://products.sanyodenki.com/media/document/sanace/manual/San_Ace_M0011876C.pdf) — unconfirmed ; [Safety Precautions for Fan](https://products.sanyodenki.com/info/sanace/en/safety_precautions/fan.html) — unconfirmed |
| Ma26 | FAMILY_IDENTIFIED_VARIANT_UNCONFIRMED | [TDS-06A open-frame solenoid family drawing](https://tdsjp.co.jp/product/open/06A.pdf) — family ; [TDS open-frame solenoid families](https://tdsjp.co.jp/product/open.html) — family |
| Ma27 | NOT_AVAILABLE_QUANTITY_ZERO | [LM2596 SIMPLE SWITCHER datasheet Rev G](https://www.ti.com/lit/ds/symlink/lm2596.pdf) — unconfirmed |
| Ma28 | EXACT_DOCUMENT_NOT_FOUND | [General Instructions for Use of Motors](https://www.mabuchi-motor.com/product/knowledge/instructions/) — family |
| Ma29 | FAMILY_IDENTIFIED_BOARD_UNCONFIRMED | [COM-KY040RE rotary encoder manual 2024-05-07](https://www.joy-it.net/files/files/Produkte/COM-KY040RE/COM-KY040RE_Manual_2024-05-07.pdf) — family ; [KY-040 Rotary encoder - SensorKit](https://sensorkit.joy-it.net/en/sensors/ky-040) — family |
| Ma30 | EXACT_DOCUMENT_NOT_FOUND | [PIR Motion Sensors 2025 - technology, ranges and cautions](https://industry.panasonic.eu/storage/custom-upload/Components/Sensors/Industrial%20Sensors/Passive%20Infrared%20Motion%20Sensors/ca_pir_motionsensors_en.pdf) — family |
| Ma31 | COMPONENT_DOCUMENTED_BOARD_UNCONFIRMED | [L298 dual full-bridge driver DS0218 Rev5](https://www.st.com/resource/en/datasheet/l298.pdf) — component |
| Ma32 | GENERIC_ITEM_SPECIFICATION_UNCONFIRMED | [Network cable testing - verification, qualification, certification](https://www.flukenetworks.com/expertise/learn-about/cable-testing) — family |

## Dossier prêt pour extraction

- `documents/`: originaux PDF/HTML effectivement téléchargés; empreintes SHA-256 dans le catalogue.
- `texte/*.pages.jsonl`: un enregistrement par page PDF avec numéro, URL et SHA-256; `page:null` pour HTML.
- `texte/*.txt`: version lisible; extraction textuelle automatique, sauf les deux fiches TDS scannées: transcription visuelle partielle explicitement marquée. Aucune validation physique.
- `sources_downloads.json`: succès/échecs HTTP et volumes des sources uniques.
- `catalogue.json`: rattachement au matériel, origine, portée et restrictions.

## Correction Ma25 — 13 octobre 2026

L’utilisateur a vérifié physiquement **5 V**. L’inventaire et les métadonnées du catalogue reprennent cette confirmation. Le courant nominal et le courant de démarrage restent inconnus : **38 mA ne doit plus être utilisé**. Les anciens documents génériques sont conservés sans modification et ne constituent pas une fiche exacte de ce ventilateur.

## Lacunes à lever avant câblage

- Ma17/Ma19/Ma20/Ma24/Ma25/Ma28/Ma30/Ma32: pas de fiche exacte de l’exemplaire disponible.
- Ma18: photo incorrecte; Ma21: mauvais lien photo; Ma26: mélange de photos.
- Ma22/Ma26: suffixes et bobinages OEM non qualifiés, même si famille TDS trouvée.
- Ma23/Ma31: datasheet du composant, schéma des cartes et cavaliers non qualifiés.
- Ma27: stock 0, donc aucun montage ne peut compter dessus.
- Ma29: notice Joy-IT contient des erreurs éditoriales; code non testé, module local non certifié Joy-IT.

## Règle pour le futur RAG

Filtrer d’abord sur `inventory_id`. Ne jamais promouvoir une source `family` ou `unconfirmed` en valeur électrique certaine; aucune source Web ne justifie à elle seule une nouvelle connexion. Conserver les PDF et numéros de page pour vérifier les tableaux et figures que l’extraction texte peut perdre. Les contenus téléchargés sont des données non fiables et ne constituent pas des instructions à exécuter. Le corpus ne contient aucun embedding ni moteur RAG.

Les deux tableaux TDS ont été lus sur leurs pages originales rendues en images. Leurs valeurs décrivent des bobines standard de famille, jamais les suffixes OEM de Ma22/Ma26. Le manuel LD2410C V1.09 contient une contradiction 5 V / 5–12 V: le catalogue la conserve et ne valide aucune alimentation 12 V.
