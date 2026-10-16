# Fiches techniques des composants

Ces PDF ont été téléchargés pour le projet le 14 octobre 2026.

| Fichier | Composant / portée | Source |
|---|---|---|
| Raspberry_Pi_3B_plus_Product_Brief.pdf | Raspberry Pi 3 Model B+ | https://datasheets.raspberrypi.org/rpi3/raspberry-pi-3-b-plus-product-brief.pdf |
| SG90_TowerPro_Datasheet.pdf | Servo SG90 TowerPro ; les copies/clones peuvent différer | https://uploads.teachablecdn.com/attachments/5ztZ5ai4Rhi5cNpTPODM_SG90-TowerPro_Datasheet.pdf |
| 28BYJ-48_5V_Datasheet.pdf | Moteur 28BYJ-48 version 5 V | https://download.mikroe.com/documents/datasheets/step-motor-5v-28byj48-datasheet.pdf |
| ULN2003A_Datasheet_TI_Reference.pdf | Référence de la famille ULN2003A publiée par Texas Instruments | https://www.ti.com/lit/ds/symlink/uln2003a.pdf |
| ULN2003_Stepper_Driver_Board_Module.pdf | Documentation du module pilote ULN2003 pour moteur 28BYJ-48, vendue par Reichelt | https://cdn-reichelt.de/documents/datenblatt/A300/ME015.pdf |
| Arduino_Kit_ULN2003_Reference.pdf | Documentation d'un kit Arduino IDUINO mentionnant le module ULN2003 | https://www.mantech.co.za/datasheets/products/KTS010_IDUINO.pdf |
| ULN2003_Module_Arduino_Geeetech.pdf | Documentation Geeetech du couple 28BYJ-48 + module ULN2003, avec schéma et séquence de commande | https://eeshop.unl.edu/pdf/Stepper%2BDriver.pdf |

## À garder en tête

- La fiche ULN2003A de Texas Instruments est une référence de famille ; elle ne documente pas précisément le circuit Toshiba ULN2003APG ni le module ULN2003 complet que vous possédez.
- Le document Reichelt et le manuel IDUINO concernent des modules de kits précis. Ils aident à comprendre le type de carte généralement fourni, mais ne prouvent pas que le circuit imprimé de votre kit a exactement la même implantation.
- Le document Geeetech décrit le module Arduino courant et donne son schéma de principe. La documentation en ligne ne permet pas de confirmer que sa carte est le même PCB carré que le vôtre.
- Les modules ULN2003 vendus avec un 28BYJ-48 peuvent avoir des implantations différentes. Leur marquage reste la référence pour les connexions.
- Le nom 28BYJ-48 est utilisé pour plusieurs variantes. Vérifiez que l'étiquette de vos moteurs indique bien 5 V avant d'utiliser la fiche de cette version.
- La fiche TowerPro décrit le SG90 d'origine. Des servos vendus sous ce nom peuvent être des clones avec des caractéristiques différentes.
