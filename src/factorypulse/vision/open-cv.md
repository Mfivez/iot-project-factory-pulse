# OPENCV

## Qu'est-ce que c'est ?

### Voici la réponse de mon cousin Claude :

OpenCV (Open Source Computer Vision Library) est une bibliothèque, utilisable surtout en Python et en C++, qui sert de « boîte à outils » pour manipuler des images et des vidéos. On s'en sert pour :

- lire et écrire des images, ou capter le flux d'une webcam ou d'une caméra IP ;
- faire du prétraitement : redimensionner, convertir en niveaux de gris, flouter, seuiller, détecter des contours ;
- dessiner sur l'image (rectangles, texte) pour afficher des résultats ;
- appliquer de la vision « classique », sans deep learning : détection de visages par Haar cascades, suivi de mouvement, calibration de caméra.

## Installation

Installation :
 
```
# avec pip
pip install opencv-python
```
```
# avec uv
uv add opencv-python
```
## Introduction de pythonia

### Première étape : lire et afficher une image

```
import cv2

# on lit notre image et on la stocke dans une variable
image = cv2.imread('coco.jpg', cv2.IMREAD_COLOR)


# pour afficher l'image on écrit :
cv2.imshow('image exemple', image)
```

cv2.IMREAD_COLOR est un exemple de flag. Celui-ci n'est pas obligatoire (c'est le flag par défaut). Voici les 3 flags les plus utilisés :

- cv2.IMREAD_COLOR : charge l'image sur 3 canaux BGR, mais sans la transparence
- cv2.IMREAD_GRAYSCALE : convertit et charge l'image en nuances de gris (1 seul canal)
- cv2.IMREAD_UNCHANGED : charge l'image telle quelle, en incluant le canal de transparence s'il existe

canal = une grille de valeurs (une par pixel) pour une seule composante de couleur (le bleu, le vert ou le rouge par exemple)

```
cv2.waitKey(0)
cv2.destroyAllWindows()
```

Ensuite, ces deux commandes précisent que l'image ne doit pas disparaître instantanément : waitKey(0) attend qu'on appuie sur une touche, et destroyAllWindows() sert à détruire les fenêtres.

### Sauvegarder une image

```
cv2.imwrite("manouvelleimage.jpg", image)
```

### Écrire sur une image

```
import cv2 

# on lit l'image et on la redimensionne
im = cv2.imread("faces_to_detect.jpg")
img = cv2.resize(im, (960, 540))
print('image lue')

# on enregistre une couleur dans un tuple
# attention : OpenCV range les couleurs en BGR (bleu, vert, rouge), pas en RGB !
rouge = (0, 0, 255)

# le premier argument de "cv2.rectangle" est l'image, ensuite le (300, 150) correspond aux
# coordonnées x et y du coin supérieur gauche, et (500, 400) à celles du coin inférieur droit
# 0,0 se situe tout en haut à gauche de l'image

image = cv2.rectangle(img, (300, 150), (500, 400), rouge, thickness=2)

# on met le nom de la nouvelle image ici dessin_rectangle.jpg
cv2.imwrite("dessin_rectangle.jpg", image)
print('image sauvegardée')
print('fin du script')
```

On peut aussi dessiner un rond : cv2.circle()
ou on peut aussi écrire sur notre image : cv2.putText()

### Utilisation d'une caméra

```
import cv2
webcam = cv2.VideoCapture(0)
# on crée une boucle
while(True):
    # on récupère frame par frame
    ret, frame = webcam.read()
    # on affiche le frame
    cv2.imshow('frame', frame)
    # on dit au logiciel d'attendre que la touche "q" soit pressée pour arrêter
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
webcam.release()
cv2.destroyAllWindows()
```

VideoCapture(0), vidéo capture, est une fonction de la librairie OpenCV, 0 identifie l'index de la caméra. S'il n'y a qu'une seule caméra branchée au PC, l'index est 0. S'il y a plusieurs caméras, il suffit de changer l'index (1, 2…).

### On peut donc écrire du texte sur notre webcam

```
import cv2
webcam = cv2.VideoCapture(0)


# Voici les arguments pour notre fonction d'écriture cv2.putText()
# style d'écriture
font_decriture = cv2.FONT_HERSHEY_SIMPLEX #nouvelle ligne

# position de ce qui est écrit sur la vidéo
position = (50, 50) #nouvelle ligne

# taille de l'écriture
taille = 1 #nouvelle ligne

# couleur bleue (en BGR, donc le bleu est en premier)
bleu = (255, 0, 0) #nouvelle ligne

# épaisseur de l'écriture, changer la valeur pour tester
thickness = 4 #nouvelle ligne


# on crée une boucle
while(True):
    # on récupère frame par frame
    ret, frame = webcam.read()
    # on écrit sur le frame
    frame_ecrit = cv2.putText(frame, "J'utilise OpenCV pour cette camera", 
        position, font_decriture, 
        taille, bleu, thickness, cv2.LINE_AA)
    # on affiche le frame
    cv2.imshow('frame', frame_ecrit)
    # on dit au logiciel d'attendre que la touche "q" soit pressée pour arrêter
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
webcam.release()
cv2.destroyAllWindows()
```
## Devenir un expert

### La structure de notre image avec numpy

```
image.shape
```

Si image.shape affiche (480, 640, 3), cela signifie :
- 480 pixels de hauteur ;
- 640 pixels de largeur ;
- 3 canaux de couleur.

```
image[0, 0]
```

image[0, 0] correspond au coin supérieur gauche. Sa valeur ressemble à [B, G, R]
Attention la syntaxe n'est donc pas [R, G, B]

Et le type ?
```
image.dtype
```
uint8 : entier non signé codé sur 8 bits (donc des valeurs de 0 à 255)

### Modifier la couleur

```
image_grise = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
```
Ceci permet de convertir une image dans un autre espace de couleurs.
Elle prend en paramètres l'image et le code de conversion, ex : cv2.COLOR_BGR2GRAY
Pourquoi faire ça ? Certaines opérations de vision sont plus simples sur une image à un seul canal que sur une image couleur.

### Redimensionner une image (on l'a déjà vu, faut suivre)

```
cv2.resize(image, (largeur, hauteur))
```

Attention petit piège : image.shape donne la hauteur avant la largeur, mais cv2.resize() attend la largeur avant la hauteur.

### Recadrer une image

```
crop = image[100:300, 200:400]

## voici la syntaxe :

image[y_debut:y_fin, x_debut:x_fin]

```

### Flouter une image

Pourquoi faire ? Le flou sert notamment à réduire le bruit avant une détection de contours.

```
blurred = cv2.GaussianBlur(
    image,
    (5, 5),
    0
)
```

- Le (5, 5) correspond à la taille du noyau utilisé pour calculer les moyennes pondérées des pixels voisins (les deux valeurs doivent être impaires).
En gros, un noyau plus grand = un flou plus important

- Le 0 laisse OpenCV déterminer automatiquement l'écart-type gaussien à partir de la taille du noyau

## Devenir vraiment expert (avant c'était pour de faux)

### Détecter les contours avec Canny

C'est une opération très classique de la vision par ordinateur. Elle permet de mettre en évidence les contours, ce qui permet par la suite de rechercher des formes, des lignes et des objets.

```
import cv2

image = cv2.imread("image.jpg")

if image is None:
    raise FileNotFoundError("Image introuvable")

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

edges = cv2.Canny(
    blurred,
    threshold1=50,
    threshold2=150
)

cv2.imshow("Contours", edges)
cv2.waitKey(0)
cv2.destroyAllWindows()
```

On lit notre image, on la convertit en nuances de gris, ensuite on la floute et on la passe dans la fonction Canny(), puis on l'affiche.

Les deux paramètres de seuil servent à distinguer les contours suffisamment forts de ceux qui sont faibles.
Le bon réglage dépend de l'image et de son niveau de contraste, les valeurs sont donc juste des points de départ.


Canny nous donne des bords, mais pour OpenCV ce n’est qu’une image en noir et blanc. Pour qu’il comprenne « ça, c’est une forme », il faut lui demander de regrouper ces pixels en contours avec cv2.findContours()

ex : 
```
contours, hierarchy = cv2.findContours(
    edges,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)
```

findContours() prend trois paramètres :

- l’image en noir et blanc (le résultat de Canny ou d’un seuillage);
- cv2.RETR_EXTERNAL : on ne garde que les contours extérieurs. cv2.RETR_TREE garde aussi les contours à l’intérieur des autres ;
- cv2.CHAIN_APPROX_SIMPLE : on simplifie les contours. Pour une ligne droite, pas besoin de stocker les 300 points, le début et la fin suffisent.

La fonction renvoie deux éléments :

- contours : une liste où chaque contour est un tableau de points (x, y) ;
- hierarchy : qui est dans qui.

### Le seuillage : transformer une image en noir et blanc

Le seuillage (thresholding) consiste à classer chaque pixel en fonction de son intensité.

```
import cv2

image = cv2.imread("image.jpg")

if image is None:
    raise FileNotFoundError("Image introuvable")

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

_, binary = cv2.threshold(
    gray,
    127,
    255,
    cv2.THRESH_BINARY
)

cv2.imshow("Image binaire", binary)
cv2.waitKey(0)
cv2.destroyAllWindows()
```

On donne en paramètre notre image (gray), ensuite on définit la valeur seuil :
- intensité supérieure à 127 --> blanc
- intensité inférieure ou égale à 127 --> noir

et la valeur maximale attribuée à un pixel blanc (ici 255).
cv2.THRESH_BINARY précise que l'on doit appliquer cette règle à chaque pixel.

La fonction nous renvoie deux éléments :
- le seuil utilisé
- l'image transformée

ensuite on peut dessiner les contours :

```
cv2.drawContours(image, contours, -1, vert, 2)
```
le paramètre -1 inquique qu'on les dessine tous, si on en veut que 1 ou deux on peut metre 1,2,3,..

## Devenir vraiment vraiment expert (pour de vrai cette fois)

Maintenant, on détecte des objets avec YOLO

(erreur de sytaxe, faute d'orthographe et contenu du .md vérifié par mon cousin)