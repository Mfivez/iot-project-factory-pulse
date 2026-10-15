# Stockage data

Sous forme de JSONL :

id	INTEGER PK	Identifiant unique de l'événement
timestamp	TEXT	Date et heure UTC au format ISO 8601
object_type	TEXT	Classe YOLO : person, bottle, etc.
color	TEXT NULL	Couleur estimée, si disponible
image_path	TEXT	Chemin relatif du JPEG annoté
confidence	REAL NULL	Confiance de la détection YOLO
source	TEXT jpg ou webcam ID
anomaly TEXT NULLABLE (pour plus tard)

# Ce qu'on va ajouter aujourd'hui

- Ajouter une UI
- Bouton pour sélectionner la source (jpeg or webcam)
- Output vers jsonl + générer un jpeg