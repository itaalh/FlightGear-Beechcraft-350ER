# Cockpit Pro Line Fusion (variante 350ER G1000)

Le cockpit de `KingAir-350ER-G1000` reproduit celui d'un King Air 350ER / 360 équipé du Collins Pro Line Fusion,
d'après des photographies. Il est entièrement généré par les scripts Python de `Tools/fusion` : une seule
description des panneaux (`cockpit_spec.py`) produit les textures, la 3D et le fichier d'animation. Aucun document
du constructeur n'est inclus dans le dépôt.

La liste complète des commandes, panneau par panneau, avec leur propriété et leur bulle d'aide, est dans
[`Fusion-controls.md`](Fusion-controls.md) (générée).

## Utilisation à la souris

Toutes les commandes affichent une bulle d'aide avec leur état au survol.

| Commande | Action |
|---|---|
| Interrupteur | clic sur la moitié haute : cran vers le haut ; moitié basse : cran vers le bas ; molette aussi. Les positions momentanées (TEST, START, MANUAL…) reviennent au repos au relâchement. |
| Interrupteur gardé | clic sur le cache pour l'ouvrir ; fermer le cache remet l'interrupteur en position normale. |
| Bouton rotatif | molette ou glisser vertical ; Maj : pas rapide. Clic sur le centre : appui (SYNC, STD, PUSH…). |
| Molettes concentriques (FGP, boîtiers de curseur) | molette sur la couronne extérieure ou sur le bouton intérieur ; clic au centre : appui. |
| Poussoir | clic ; les touches de trim et d'alternat agissent tant que le bouton est tenu. |
| Disjoncteur | clic : tiré (le bouton sort) / réarmé. |
| Manettes de puissance, d'hélice, de condition | molette ou glisser vertical ; Maj : les deux manettes ensemble. Puissance : sous le ralenti, BETA puis REVERSE. Hélice : tout en arrière, FEATHER. Condition : FUEL CUTOFF, LOW IDLE, HIGH IDLE. |
| Levier de volets | molette ou glisser : UP, APPROACH, DOWN. |
| Roue de trim de profondeur | molette ou glisser (rouler vers l'avant : piqué) ; Maj : rapide. |
| Écrans | clic sur le libellé d'une touche programmable, en bas de l'écran (écran tactile). |
| Accoudoir intérieur des sièges | clic : baissé / relevé. Il est relevé au démarrage, pour laisser voir le pupitre. |

Les volants se masquent par le menu *King Air 350 › Yokes visible* (`sim/model/yokes-visible`). Ils portent la
déconnexion AP / YD, le trim électrique (deux boutons à tenir) et l'alternat.

## Les panneaux

**Auvent.** MASTER WARNING / MASTER CAUTION de chaque côté, incendie moteur (poussoirs de vanne coupe-feu et
d'extincteur, voyants DISCH), balises MKR et TAWS, voyant RADIO CALL (s'allume à un appel ATC).

**FGP (pilote automatique), au centre de l'auvent.** Boutons FD (un de chaque côté), VS, VNAV, FLC, NAV, HDG,
APPR, 1/2 BANK, ALT, YD, CPL, AP et YD/AP DISC ; molettes CRS1 et CRS2 (appui : route vers la station), HDG
(appui : cap actuel), SPEED (appui : vitesse actuelle), ALT (Maj : pas de 1 000 ft) et molette de tangage (cible
du mode VS, FLC ou PIT). L'écran de secours est au-dessus.

**Écrans.** PFD pilote, MFD, PFD copilote ; leur luminosité se règle au plafonnier.

**Bandeau sous les écrans.** Synchronisation des hélices, DG FREE et SLEW de chaque AHRS, réversion (PFD 1 OFF,
MFD OFF, PFD 2 OFF : l'écran s'éteint et le PFD du même côté passe sur l'écran central), sources AHS et ADS du PFD
pilote, inhibitions TOUCH / CURSOR de chaque écran, source statique de secours du pilote, EMER FREQ (COM 1 sur
121,500).

**Panneaux audio (pilote et copilote).** Sélecteur d'émission (XMT), volume général, récepteurs COMM, NAV, DME,
ADF, MKR, PA (clic : tiré / enfoncé, molette : volume), micro, sensibilité des balises, filtre NAV, mode EMER, et
molette BARO du PFD du même côté (appui : STD).

**Sous-panneau pilote.** Coupure générale (gardée), batterie, générateurs, avionique, écran de secours, essai du
délestage (BUS SENSE), couplage des générateurs, antigivrage des entrées d'air moteur et leurs actionneurs,
allumage et démarrage, autofeather (avec essai), essai du régulateur de survitesse hélice, allumage automatique.

**Éclairage et antigivrage.** Phares, taxi, givrage, navigation, reconnaissance ; antigivrage pare-brise, hélices
(AUTO / MANUAL), mise à l'air carburant, freins, dégivrage des surfaces (SINGLE / MANUAL), réchauffage de
l'avertisseur de décrochage et des pitots ; disjoncteur du relais de train.

**Train.** Levier de train (voyant rouge en transit), déverrouillage de secours, essai du levier et des voyants,
voyants de train sorti, feux anticollision (BEACON, STROBE), éclairage de la dérive.

**Centre.** Indicateurs de volets, de vario cabine et d'altitude / pression différentielle cabine.

**Conditionnement d'air.** Ventilateurs et consignes de température du poste et de la cabine, mode (OFF, AUTO,
MAN COOL, MAN HEAT, ELEC HEAT), réglage manuel, prélèvement d'air (général et par moteur).

**Sous-panneau copilote.** Désembuage des glaces latérales, essai des alarmes cabine, essais incendie (DET / EXT)
de chaque moteur, indicateur de température cabine, compteur horaire, manomètre d'oxygène.

**Frein de parc.** Poignée sous le panneau pilote (clic : serré / desserré).

**Pupitre.** Manettes et levier de volets, roue de trim de profondeur et son indicateur, trims d'aileron et de
direction, freins de manettes, deux boîtiers de curseur (voir plus bas), clavier alphanumérique, pressurisation
(altitude cabine, taux, TEST / PRESS / DUMP), rudder boost, trim électrique, essais de l'avertisseur de décrochage
et du klaxon de train, enregistreur de conversations (essai et effacement).

**Plafonnier.** MASTER PANEL LIGHTS, rétroéclairage des panneaux, luminosité des trois écrans (l'écran de secours
suit le PFD pilote), projecteurs d'ambiance (panneau, pupitre, plafonnier), intensité des voyants, essuie-glace,
consignes cabine (avec carillon), éclairage cabine ; indicateurs de charge des générateurs, courant batterie,
tension, courant du dégivrage hélices et température extérieure. Le compas de secours pend sous le montant
central du pare-brise.

**Carburant (paroi gauche).** Jauges gauche et droite (MAIN / AUXILIARY / TEST), intercommunication, pompes de
secours, transferts des réservoirs auxiliaires.

**Disjoncteurs (parois gauche et droite).** 88 disjoncteurs : chacun coupe son circuit dans les systèmes de
l'avion (radios, écrans, pilote automatique, éclairages, démarrage, pompes, trims, volets, train, chauffages,
conditionnement…).

## Boîtiers de curseur et clavier

Chaque boîtier du pupitre reproduit les touches du G1000 : grandes et petites molettes FMS, RANGE, D→, MENU, FPL,
PROC, CLR, ENT, et les molettes des radios NAV et COM. Le sélecteur DISPLAY choisit l'écran commandé (pilote : PFD 1
ou MFD ; copilote : MFD ou PFD 2). Le clavier envoie lettres et chiffres à l'écran du dernier boîtier utilisé.
L'inhibition CURSOR d'un écran désactive le boîtier sur cet écran ; l'inhibition TOUCH, ses touches tactiles.

## Propriétés utiles

| Propriété | Rôle |
|---|---|
| `sim/model/fusion/cockpit` | `true` dans `KingAir-350ER-G1000-set.xml` : masque l'ancien cockpit de `Models/flightdeck.xml` (sauf plancher et palonniers). |
| `sim/model/yokes-visible` | Affichage des volants. |
| `sim/model/fusion/armrest[n]` | Accoudoir intérieur, 0 pilote, 1 copilote : `0` relevé, `1` baissé. |
| `controls/fusion/...` | Positions des nouvelles commandes du cockpit (nombres, 0 = position basse). |
| `controls/fusion/cb/<nom>` | Disjoncteurs : `1` = tiré ; absent ou `0` = enfoncé. |
| `sim/model/fusion/panel-lights-norm` | Luminosité du rétroéclairage des inscriptions (0 à 1). |
| `sim/model/fusion/flood-norm[n]` | Projecteurs d'ambiance : 0 panneau, 1 pupitre, 2 plafonnier. |
| `sim/model/fusion/lamps/...` | État des voyants (calculé par `Nasal/fusion-lamps.nas`). |
| `instrumentation/fusion/ahrs-heading-deg` | Cap de l'AHRS affiché par le G1000. |

## Fichiers

| Fichier | Contenu |
|---|---|
| `Models/Fusion/fusion-cockpit.ac` | Géométrie (généré). |
| `Models/Fusion/fusion-cockpit.xml` | Animations, zones cliquables, bulles d'aide, écrans, éclairage (généré). |
| `Models/Fusion/fusion-panel-<n>.png`, `-lm.png` | Pages de texture des panneaux et leur carte de rétroéclairage (générées). |
| `Models/Fusion/Effects/fusion-panel-<n>.eff` | Effets de rétroéclairage (générés). |
| `Models/KingAir-G1000.xml` | Modèle de la variante : `KingAir.xml` + le cockpit Fusion. |
| `Nasal/fusion-cockpit.nas` | Logique des commandes : interrupteurs, disjoncteurs, FGP, audio, carburant, éclairage, boîtiers de curseur, clavier… |
| `Nasal/fusion-lamps.nas` | Conditions des voyants (généré). |
| `Nasal/fusion-standby.nas` | Écran de secours (canvas). |
| `Nasal/fg1000-kingair.nas` | Pose des écrans FG1000 sur les écrans du cockpit, réversion. |
| `Tools/fusion/` | Générateurs (voir ci-dessous). |

## Régénérer le cockpit

Tout se modifie dans `Tools/fusion`, jamais dans les fichiers générés. Il faut Python 3 avec Pillow, et Blender
(testé avec la version 5.2). Depuis la racine du dépôt :

```
python Tools/fusion/atlas.py
blender -b --factory-startup --python Tools/fusion/build_cockpit.py
python Tools/fusion/gen_xml.py
python Tools/fusion/gen_doc.py
```

1. `atlas.py` dessine les panneaux, les touches, les voyants et les cadrans dans les pages de texture et leurs cartes
   de rétroéclairage, et note leur place dans `Tools/fusion/_build/atlas.json`.
2. `build_cockpit.py` construit la 3D dans Blender et exporte `Models/Fusion/fusion-cockpit.ac`, avec les pivots des
   animations (`_build/pivots.json`). Option `--preview` : rendus de contrôle dans `Tools/fusion/_shots/`.
   Le fichier Blender est enregistré dans `Models/Fusion/Sources/` (non suivi par git).
3. `gen_xml.py` écrit `fusion-cockpit.xml`, les effets et `Nasal/fusion-lamps.nas`.
4. `gen_doc.py` met à jour [`Fusion-controls.md`](Fusion-controls.md).

| Script | Rôle |
|---|---|
| `spec_base.py` | Modèle de données : panneaux, inscriptions, commandes (interrupteur, bouton rotatif, poussoir, voyant, cadran…), actions. |
| `cockpit_spec.py` | Description de tous les panneaux : position, inscriptions, commandes, propriétés et actions. |
| `layout.py`, `shell.py`, `pedestal.py` | Repères géométriques, structure (auvent, planche de bord, écrans), géométrie du quadrant. |
| `shapes.py`, `controls3d.py`, `pedestal3d.py`, `misc3d.py` | Maillages Blender : panneaux et commandes, pupitre, plafonnier, compas, sièges. |
| `ac3d.py`, `bl_common.py`, `sections.py` | Lecture / écriture AC3D, caméras de contrôle, coupes du fuselage pour les mesures. |

Repère : x vers l'arrière, y vers la droite, z vers le haut, en mètres (repère de `Models/KingAir.xml`). Sur un
panneau, les positions sont en millimètres depuis son centre.

Pour ajouter une commande : l'ajouter au panneau voulu dans `cockpit_spec.py` avec sa propriété et ses actions,
écrire au besoin la fonction dans `Nasal/fusion-cockpit.nas`, puis relancer les quatre étapes.

## Limites

- Les écrans affichent les pages du G1000 (FG1000), pas celles du Pro Line Fusion ; l'image 4:3 est centrée sur
  l'écran large, avec des bandes noires.
- Le VNAV est simplifié ; les approches GPS avec guidage vertical ne sont pas simulées.
- Les commandes qui n'ont pas d'équivalent dans les systèmes de l'avion (essais, CVR…) ont un effet visible
  (voyants, sons) mais simplifié.
