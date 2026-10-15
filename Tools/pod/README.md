# Nacelle ventrale de l'ALSR « Vador » et dérives ventrales

`alsr_pod.py` construit, dans Blender, la nacelle ventrale de l'ALSR (carénage « canoë » à fond plat, mince à
l'avant, profond sous la cabine, dont l'extrémité arrière loge la boule optronique rétractable, caméra rentrée)
et les deux dérives ventrales inclinées du 350 sous le fuselage de `Models/KingAir.ac`, puis les exporte en AC3D ;
`splice_ac.py` insère (ou remplace) les objets exportés dans `Models/KingAir.ac`.

```
blender --background --python Tools/pod/alsr_pod.py -- --out /tmp/alsr-pod.ac
python Tools/pod/splice_ac.py /tmp/alsr-pod.ac
```

Blender 4.1 ou plus récent avec l'addon AC3D (`io_scene_ac3d`) activé. Si la scène ne contient pas d'objet
`Fuselage`, `Models/KingAir.ac` est importé d'abord (axes `-Z` avant / `Y` haut : les axes de Blender sont alors
ceux du modèle FlightGear, x vers l'arrière, y vers la droite, z vers le haut). Le script peut aussi être collé
dans l'éditeur de texte de Blender ou envoyé par le serveur MCP de Blender ; un dictionnaire global `PARAMS`
remplace alors les paramètres de `P`, et `OUT` le fichier de sortie.

## Forme et cotes

D'après les photographies du prototype F-WTAO (vues de dessous et de trois-quarts, 2018) et du F-RACH, le dessin
constructeur de la modification et le profil relevé par l'auteur du projet ; les positions sont en mètres dans le repère du modèle (x vers l'arrière, 0 au centre du modèle ; nez à −7,05).

| Élément | Cote |
|---|---|
| Partie avant | pointe à x −4,42, juste derrière le logement du train avant ; demi-ellipse de 0,40 × 0,36 en plan ; bord avant en quart de rond (r 0,14) ; plaque plate de 0,14 à 0,16 m de profondeur jusqu'à x −3,75 (pas de tourelle avant sur cet appareil) |
| Rampe | de x −3,75 (0,16) à x −3,05 (0,56), en S : pente d'environ 30° au milieu, raccords arrondis aux deux extrémités |
| Corps | demi-largeur 0,40 (largeur 0,8 m), profondeur 0,56 de x −2,8 à −0,5 |
| Extrémité arrière | de x −0,5 à +0,6 (derrière le bord de fuite) : demi-ellipse en plan, profil elliptique qui remonte jusqu'au ventre |
| Disque de la caméra arrière rentrée | Ø 0,44 centré à x −0,72 dans le fond plat, dépasse de 8 mm (objet `AlsrSensorCover`, gris) |
| Dérives ventrales (delta) | objet `DeltaFins`, une pièce pour les deux (photo de profil du F-RACG) : longues et basses, corde 1,85 m à l'emplanture (x 3,10 → 4,95, de la cocarde à l'approche de la queue), bords d'attaque et de fuite en flèche arrière (saumon de x 3,50 à 4,80), hauteur 0,42 m hors fuselage, inclinées de 35° vers l'extérieur, emplanture à y ±0,25 sur le dessous du cône arrière (enfoncée de 12 cm), épaisseur 4 cm amincie vers le saumon |
| Section | fond plat, bouchains arrondis (r 0,08 à l'avant, 0,10 sur le corps), flancs verticaux ; une seule surface lissée de l'avant à la pointe (interpolation cubique monotone des stations) |
| Haut | les parois remontent de 12 cm à l'intérieur du fuselage (aucun jour visible, invisible de la cabine) |

Le ventre est sondé par lancer de rayons sur le maillage `Fuselage` : la nacelle suit la courbure longitudinale
du fuselage (le fond remonte vers l'arrière avec le ventre).

## Texture

Aucune livrée n'est retouchée : les UV de la nacelle réutilisent le bas du flanc droit du fuselage de la texture
(u = 0,4836 + 0,0681 x, v de 0,972 au niveau de la quille à 0,927 en haut des parois : zone blanche dans toutes
les livrées, avec les légères salissures de ventre de la livrée ALSR) ; la plaque de la caméra pointe sur le gris
uniforme du train (u 0,917, v 0,30). Les trois objets sont dans la liste de l'effet `KingAir-350-combShaders` et
dans le groupe `bodyWork` de `Models/KingAir.xml` (la liste d'objets auxquels l'animation de livrée applique la
texture) : ils suivent la livrée comme le reste du fuselage. Ils ne sont pas dans la liste `BODYWORK` de
`Tools/livery/maps.py` : ils n'ont pas de texels en propre.

## Affichage

`Models/KingAir.xml` : animation `select` sur `sim/model/livery/alsr-pod` pour `AlsrPod` et `AlsrSensorCover`, `true`
dans `Models/Liveries/ALSR.xml` et `false` dans les autres livrées (même mécanisme que `window-plug-l1`). `DeltaFins`
n'est pas conditionné : ce sont les dérives de série du 350.
