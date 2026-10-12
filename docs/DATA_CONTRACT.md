# Contrat commun FP-LAB-1.1
Cette édition conserve les six clés de l'atelier précédent et précise les valeurs manquantes, la santé informatique et les logs. Ne pas utiliser l'ancien validateur, limité aux deux premiers types.

## Formats
CSV d'entrée : UTF-8, séparateur virgule, point décimal, en-tête présent. Cellule vide de température = donnée manquante.
JSONL de sortie : UTF-8, UN objet JSON par ligne, pas de tableau autour des lignes. Configuration et références : JSON classique. Photos : JPG/PNG. Documentation : Markdown (.md).
Chaque événement contient `event_id`, `timestamp_utc`, `station_id`, `event_type`, `source`, `payload`.
Date ISO 8601 UTC avec Z. Station M01, Q01 ou SERVER. Identifiant d'événement unique ; réimporter le même identifiant ne crée pas une nouvelle pièce. Une réémission conserve le même identifiant. Tous les exemples du kit portent source=simulated. Réserver physical_sensor aux mesures réelles et camera_analysis à une analyse réellement exécutée.

## M01 / telemetry
Payload : temperature_c (nombre ou null), vibration_rms_g (nombre >=0 ou null), machine_state (RUNNING/STOPPED/UNKNOWN), data_quality (OK/TEMPERATURE_MISSING/VIBRATION_MISSING/MISSING), alert_level (OK/WARNING/DATA_ISSUE), alert_reason (chaîne ou null).
Température en °C. Vibration RMS dynamique en g, non accélération absolue gravité comprise. Pour cet exercice, la valeur RMS est déjà fournie ; le CSV XYZ sert à une extension.
Règles : température >60 ou vibration >0.20 pendant 3 mesures consécutives espacées au plus de 1.5s -> WARNING. Une condition peut en remplacer une autre si elle persiste à son tour. Retour OK après 3 mesures valides sous les deux seuils. Une donnée manquante -> DATA_ISSUE immédiatement et remise à zéro des compteurs. L'arrêt ne masque pas une donnée manquante.
Aucune télémétrie n'est produite pour M01 après 09:04:59Z. Ne pas fabriquer des valeurs de capteur pour remplir ce trou.

## Q01 / inspection
Payload : part_id, object_class (bottle/cup/unknown), confidence (nombre 0..1 ou null), bbox_xyxy ([x1,y1,x2,y2] en pixels ou null), marker_color (green/red/unknown), verdict (PASS/REJECT/UNKNOWN), image_path (chemin relatif ou null), image_size_px ([largeur,hauteur]), algorithm.
Un seul objet cible et une seule décision par photographie dans le premier labo. Object_class inconnue, score <0.5, repère absent ou ambigu, plusieurs objets : UNKNOWN. Sinon vert = PASS, rouge = REJECT. Ne pas inventer un score si l'algorithme n'en fournit pas.
Le compteur mesure des inspections uniques. Le comptage de passages physiques demandera un déclencheur et un part_id correctement associé au banc réel.

## health et log
Health : service_state (RUNNING/STOPPED/UNKNOWN), cpu_pct, ram_pct, mqtt_connected, uptime_s. Son timestamp est le signe de vie ; mqtt_connected représente une observation à cet instant, pas une vérité permanente.
Log : service, level (INFO/WARNING/ERROR), code, message ; target_station facultatif pour le collecteur central.
Déclarer les données périmées quand as_of_utc moins dernier timestamp est >15s. Ne pas comparer ce replay à l'heure réelle du PC. Ne pas assimiler absence de données à arrêt de machine.

## Diagnostic à produire
JSON avec station_id, as_of_utc, summary, facts, hypotheses, checks et limitations. Chaque fait contient un texte et une liste evidence_event_ids. Les hypothèses restent conditionnelles. Aucun score de confiance inventé. La réponse est consultative, sans action de commande.
