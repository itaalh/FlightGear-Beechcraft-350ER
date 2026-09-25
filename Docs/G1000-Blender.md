# King Air 350ER « G1000 » — intégration des écrans dans le cockpit 3D (Blender)

La variante `KingAir-350ER-G1000` fonctionne **sans retoucher le 3D** : les deux afficheurs Garmin GDU 1044B
du FG1000 (livrés avec FlightGear dans `$FG_ROOT/Aircraft/Instruments-3d/FG1000/GDU104X/`) sont posés
**en applique**, 3,7 cm devant la face du tableau de bord, et les instruments qu'ils recouvrent sont masqués
(`sim/model/g1000/enabled`, animation *select* ajoutée en fin de `Models/flightdeck.xml`). Le travail Blender
décrit ici sert à obtenir un montage **affleurant** et propre : découpe du tableau de bord, suppression des
cadrans peints sous les écrans, éventuellement un cadre encastré.

## 1. Repères et coordonnées

Le cockpit est `Models/flightdeck.ac` (source : `Sources/Models/flightdeck.blend`, inclus dans le dépôt d'origine).

| Repère | x | y | z |
|---|---|---|---|
| Modèle FlightGear (fichiers XML, `<offsets>`) | vers l'arrière (+x = queue) | vers la droite | vers le haut |
| Fichier AC3D `flightdeck.ac` | identique | = z modèle (haut) | = −y modèle (gauche) |
| Blender (import AC3D, « Y up » converti en « Z up ») | identique | = y modèle | = z modèle |

Vérification rapide dans Blender : l'aiguille `Torque.needle` doit être vers x ≈ −4,65, y ≈ −0,22, z ≈ 0,22.
Si les y sont inversés, votre importateur n'a pas fait la conversion : remplacez y par −y dans les valeurs ci-dessous.

**Face du tableau de bord** : x = −4,647 m (objets `Panel.005` et `Panel`, qui portent aussi les textures des cadrans).
Les instruments occupent z ∈ [0,04 ; 0,34] ; les boutons du panneau FGC (rangée `HDG.btn`… ) sont à z 0,29–0,32,
les voyants FD à z 0,33, les poignées incendie à z 0,35.

## 2. Emplacement des deux écrans (voir `G1000-panel-layout.png`)

| Écran | Modèle FG1000 | Centre (y, z) | Encombrement bezel (approx.) | Zone écran |
|---|---|---|---|---|
| PFD (pilote) | `GDU-1044B.1.xml` | y = −0,425 m, z = 0,165 m | 277 × 203 mm (10,9 × 8,0 in) | 211 × 158 mm (10,4", 4:3) |
| MFD (centre) | `GDU-1044B.2.xml` | y = +0,010 m, z = 0,165 m | 277 × 203 mm | 211 × 158 mm |

Le PFD est centré sur la colonne EADI/EHSI du pilote (les deux tubes EFIS-84 sont à y −0,425) ; le MFD recouvre
la pile COM1/NAV1/ADF1, l'alerteur d'altitude et le KLN-90B. La colonne des jauges moteur (y −0,23 … −0,13) reste
visible entre les deux, ainsi que COM2/NAV2/transpondeur à droite, le panneau audio au-dessus et le panneau FGC.

Les dimensions du bezel sont celles du GDU 1040/1044 réel ; **mesurez le modèle FG1000** pour être exact :
importez `$FG_ROOT/Aircraft/Instruments-3d/FG1000/GDU104X/GDU-1044B.ac` dans Blender (il donne aussi la position
de l'origine du modèle, qui fixe le point placé par `<offsets>` dans `Models/KingAir-G1000.xml`).

Deux gabarits de découpe sont fournis, aux positions ci-dessus, profondeur 8 cm (x de −4,70 à −4,62) :
`G1000-cutters.obj` (import direct dans Blender, repère modèle) et `G1000-cutters.ac` (repère AC3D).

## 3. Procédure Blender

1. Ouvrir `Sources/Models/flightdeck.blend` (ou importer `Models/flightdeck.ac` avec l'add-on AC3D de FlightGear).
   Faire une copie de sauvegarde.
2. `File › Import › Wavefront (.obj)` → `Docs/G1000-cutters.obj` (Forward −Y? Non : laissez *Forward = -Z, Up = Y*
   désactivés, c.-à-d. « Y Forward / Z Up » pour garder les coordonnées telles quelles ; vérifiez que les boîtes
   tombent bien sur la colonne EFIS et sur les radios). Ajuster ± quelques mm si nécessaire.
3. Sur `Panel.005` (face avec les cadrans) puis sur `Panel` (fond) : modificateur **Boolean › Difference** avec
   chaque gabarit, appliquer. Vous obtenez deux ouvertures dans lesquelles les bezels GDU viendront s'encastrer.
   Variante plus simple si le booléen abîme les UV : sélectionner les faces sous chaque gabarit en édition (vue
   de face, sélection rectangulaire) et les supprimer, puis refermer le pourtour.
4. Supprimer (ou déplacer hors du cockpit) les objets recouverts, dont les noms sont listés dans l'animation
   *select* de `Models/flightdeck.xml` (`ASI1.needle`, `ALTneedle1`, `VSI1.needle`, `RMI1.*`, `eadi1.off`,
   `ehsi1.off`, `COMM1.*`, `NAV1.*`, `ADF1.*`, `alerter.*`, `altalert.*`, `KLN90B.*`, `gps*.btn`, `gyro-face`…).
   Ne renommez pas les objets conservés : les animations et les zones cliquables de `flightdeck.xml` les
   référencent par nom.
5. Facultatif : modéliser un cadre de 8–10 mm autour de chaque ouverture (extrusion vers −x) pour le rendu
   « encastré », ou reprendre la texture `instruments.png` pour effacer les cadrans peints restants
   (altimètre, VSI et anémomètre du pilote dépassent de ~1–2 cm de part et d'autre du PFD).
6. Exporter en AC3D vers `Models/flightdeck.ac` (mêmes options que l'original : textures relatives, pas de
   transformation d'axes supplémentaire), en écrasant l'ancien fichier. Le nom des objets et des textures doit
   rester identique.
7. Dans FlightGear, lancer `KingAir-350ER-G1000`, ouvrir le navigateur de propriétés et régler
   `sim/model/g1000/pfd/dx-m` (et `mfd`) pour reculer les bezels dans les ouvertures (typiquement dx ≈ −0,035
   pour revenir à la face x = −4,647, dy/dz pour centrer). Reporter ensuite les valeurs dans les `<offsets>` de
   `Models/KingAir-G1000.xml` et remettre les propriétés à 0.

## 4. Si vous préférez vos propres écrans (sans les bezels FG1000)

Le FG1000 peut aussi dessiner sur une surface quelconque : créez deux objets plans (par exemple
`G1000.PFD.screen` et `G1000.MFD.screen`) au format 4:3, UV de (0,0) à (1,1) couvrant toute la face, normales
vers le pilote, puis dans `Nasal/fg1000-kingair.nas` remplacez `addPFD(1)` / `addMFD(2)` par un appel avec
placement — vérifiez la signature dans `$FG_ROOT/Aircraft/Instruments-3d/FG1000/Nasal/FG1000.nas`
(`addPFD(index, placement)`, placement = `{"node": "G1000.PFD.screen"}` sur les versions récentes). Les touches
programmables et les boutons doivent alors être modélisés et reliés aux commandes du FG1000 (`fg1000-multikey.xml`
donne la liste des commandes clavier correspondantes).

## 5. Limites connues de la variante

- Le bandeau moteur (EIS) du FG1000 est conçu pour un monomoteur à pistons : il affiche le moteur 1 avec les
  libellés RPM / MAN (= couple %) / FF / huile / EGT (= ITT). Les jauges analogiques des deux moteurs restent
  dans le tableau de bord.
- Le pilote automatique reste celui de l'avion (panneau FGC ou dialogue F11) ; le GFC 700 du FG1000 n'est pas chargé
  pour ne pas entrer en conflit avec les boucles JSBSim.
- La page carburant du FG1000 lit les deux premiers réservoirs (`tank[0]`, `tank[1]`).
- Nécessite FlightGear 2018.3 ou plus récent (présence du dossier FG1000) ; sinon la variante démarre avec les
  instruments d'origine et affiche un message.
