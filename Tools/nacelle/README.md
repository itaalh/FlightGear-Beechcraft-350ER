# Nacelles moteur et bords d'attaque

`nacelle_details.py` reconstruit, dans Blender, les entrées d'air, les échappements et les ouïes des deux PT6A-60A,
referme les cônes d'hélice et le bord d'attaque manquant de l'aile intérieure et refait les bandes noires de
dégivrage sur toute l'envergure, puis exporte les objets en AC3D ; `Tools/pod/splice_ac.py` les insère dans `Models/KingAir.ac` (un objet
remplacé garde le matériau et les faces double face de l'original).

```
blender --background --python Tools/nacelle/nacelle_details.py -- --out /tmp/nacelle.ac
python Tools/pod/splice_ac.py /tmp/nacelle.ac --set-mat Exhaust=2 --remove DeicebootsInner --remove PropCone
```

Le script repart toujours de la géométrie d'origine des objets qu'il modifie (`FrontCowls`, `FrontEngineCowls`,
`DeicebootsWings`, `Wings`, `PropConeLeft`, `PropConeRight`), conservée dans `original_objects.ac` (extraite de `Models/KingAir.ac` avant la première
application) : le résultat ne dépend pas de ce que contient déjà le modèle, et deux exécutions de suite donnent le
même résultat. Il peut aussi être collé dans l'éditeur de texte de
Blender ou envoyé par le serveur MCP de Blender (`PARAMS`, `OUT`). `--remove DeicebootsInner` retire l'objet d'une
version précédente du script ; `--remove PropCone` retire un disque fermé de 0,21 m resté sur le flanc extérieur du
capot droit dans le modèle d'origine (non animé, malgré son nom), que cachait la base de l'ancien échappement.

## Références

Photographies du prototype F-WTAO, du F-RACH et du F-RACG (gros plans des nacelles, vues de profil et de dessous),
plan trois vues du Super King Air 350 (forme en plan de l'aile, position des échappements), descriptions du PT6A-60A
du King Air 350 (Twin & Turbine, King Air Magazine : lèvre d'entrée d'air chauffée par les gaz d'échappement).

## Objets et cotes

Repère du modèle : x vers l'arrière, y vers la droite, z vers le haut, en mètres. Axes des moteurs : ceux des
hélices de `Models/KingAir.xml`, y −2,749 et +2,796 (le moteur droit est 4,7 cm plus à l'extérieur que le gauche).

| Objet | Description |
|---|---|
| `EngineInlets` (nouveau) | Entrée d'air : bouche en ovale aplati de 0,34 × 0,10 m centrée à z −0,624, lèvre tubulaire en métal (extérieur 0,43 × 0,19 m) dans le plan x −5,26, en avant du capot comme un museau, conduit sombre de 12 cm. Ouïes : deux ouvertures sombres de 25 × 11,5 cm sous chaque capot, de part et d'autre de l'axe, entre x −4,97 et −4,72. |
| `FrontCowls` (modifié) | Sous l'anneau qui entoure le cône, l'avant du capot d'origine était un cadre arrondi autour d'une ouverture en D de 0,54 × 0,25 m, prolongée par un tunnel (on voyait l'intérieur de la nacelle). Le cadre et le tunnel sont retirés (sous z −0,25 pour les joues latérales) et remplacés dans l'objet même par un menton qui porte la lèvre : courbes qui partent du bord extérieur de la lèvre vers l'arrière et rejoignent le bord arrière de l'anneau, au-dessus de la bouche, et le bord avant de `FrontEngineCowls`, qu'elles abordent dans le prolongement du capot (sans arête). De chaque côté de l'anneau, l'étroite bande entre l'anneau et le bord du capot, de z −0,25 à −0,43, est remplie à plat comme la joue au-dessus. Le menton partage les sommets de l'anneau, des joues et la position de ceux du bord de `FrontEngineCowls` : pas de jour, pas de recouvrement. |
| `Exhaust` (remplacé) | Un échappement court en coude de chaque côté de chaque nacelle, à hauteur de l'axe du cône (x −5,02, z −0,16), d'après les photos de face, de dos et de trois-quarts : il sort du flanc juste derrière l'anneau avant par un congé de raccordement (tangent au capot et au tuyau, 2,5 cm de large), vers l'extérieur et 10° vers le haut, tourne de 64° et finit par une courte partie droite dont l'axe pointe vers l'arrière, 25° vers l'extérieur et 6° vers le haut ; la sortie dépasse le capot de 0,23 m, vers x −4,90. Section ronde de 14 cm qui s'évase à 18 × 17 cm, bout coupé en biais (20°) pour que la sortie regarde surtout vers l'arrière. Découpe sombre sous le tuyau. Matériau blanc (index 2) au lieu du gris très foncé de l'objet d'origine (`--set-mat Exhaust=2`). |
| `FrontEngineCowls` (modifié) | Les faces de l'ancienne douille d'échappement sont retirées et le trou est rebouché dans l'objet même : le contour du trou (ouvert sur le bord avant du capot) est refermé le long de ce bord, puis maillé finement (triangulation de Delaunay contrainte, vue de côté, du contour et d'une grille de points espacés de 2,5 cm), chaque nouveau sommet posé sur la surface du capot, relevée par rayons et interpolée au-dessus du trou. UV du capot environnant. |
| `Wings` (modifié) | Entre le fuselage et les nacelles (\|y\| 0,83 à 1,88), l'aile d'origine n'a pas de faces de bord d'attaque : le nez était ouvert et le bord d'attaque semblait reculé de 11 cm. Les six faces manquantes de chaque côté sont recréées entre les deux sections existantes (bord d'attaque droit, comme sur le plan trois vues), avec les UV de leurs voisines. |
| `DeicebootsWings` (refait) | Bandes noires qui enveloppent le bord d'attaque, du fuselage à la nacelle et de la nacelle au saumon, extrémités fermées, calées sur la position réelle du flanc de nacelle. Le long du nez fermé (aile intérieure, raccord de la nacelle), section relevée par un éventail de rayons centré 16 cm derrière le bord d'attaque. Sur l'aile extérieure (\|y\| 3,97 à 8,76), l'aile n'a pas de nez (les peaux s'arrêtent environ 15 cm derrière le bord d'attaque, l'ancienne bande formait ce nez) : section en D, le long des deux peaux puis autour du nez par la ligne de bord d'attaque de l'ancienne bande. L'ancienne bande n'avait que deux petits tronçons blancs à l'intérieur, rien entre la nacelle et \|y\| 3,97, et à l'extérieur une coque de longs triangles qui ne suivait pas le raccord courbe (un morceau pendait sous l'aile). |
| `PropConeLeft`, `PropConeRight` (refaits) | Les cônes d'origine avaient trois ouvertures de pales à 120° pour une hélice à quatre pales : une seule pale passait dans une ouverture. Ils sont refermés : surface de révolution autour de l'axe de rotation de `Models/KingAir.xml` (48 segments, profil relevé sur les anneaux du cône d'origine), pointe fermée, base ouverte contre `PropConeDisks` comme avant. La texture du cône est une projection vue de face, avec les trois ouvertures peintes : le cône fermé est plaqué sur un secteur propre de ±12° de cette projection, choisi automatiquement là où la texture s'écarte le moins de son profil radial médian, au même rayon (aspect métal poli conservé, aucune livrée retouchée). Les animations ne changent pas. |

## Texture

Aucune livrée n'est retouchée. Lèvre et échappements : gris moyen de la zone du cône d'hélice (u 0,670, v 0,240),
identique dans toutes les livrées ; conduit, interstices et ouïes : gris foncé de la bande de bord d'attaque
(u 0,16, v 0,033), sombre dans toutes les livrées sauf LN-LTI ; menton et rebouchage : UV du capot le plus
proche ; bandes : noir des bandes de bord d'attaque (u 0,556 → 0,600, v 0,024). La zone échappement de la
texture (u 0,112 → 0,180, v 0,573) n'est plus utilisée ; `Tools/livery/alsr.py` ne la peint plus (`EXHAUST = []`).
`EngineInlets` est dans l'effet `KingAir-350-combShaders` et dans le groupe `bodyWork` de `Models/KingAir.xml`.
