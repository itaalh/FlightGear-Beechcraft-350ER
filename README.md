# Beechcraft King Air 350 (B300) pour FlightGear — modèle de vol JSBSim reconstruit

Version 2.8.1 (2026) — modèle de vol, moteurs, hélices, systèmes et pilote automatique entièrement refaits ;
historique des versions dans `CHANGELOG.md`.
Modèle 3D et cockpit d'origine : SM, D-ECHO, Lesbof, Bomber, it0uchpods, GabrielYV, IAHM-COL, JWocky (2015-2017,
FGMEMBERS, USA Tour). Refonte 2026 : Itaalh — modèle de vol, moteurs et hélices, systèmes, pilote automatique,
check-lists, livrées, cockpit Pro Line Fusion de la variante G1000 (généré par les scripts de `Tools/fusion`) et
intégration du G1000.
Photo de l'écran de chargement : Armée de l'Air et de l'Espace.
Licence : GPL v2 ou ultérieure (voir `COPYING`).

## Installation

**Après téléchargement, renommez le dossier obtenu en KingAir-350 avant de le placer dans votre dossier Aircraft.**

Copier le dossier `KingAir-350` dans un répertoire d'avions FlightGear (par exemple
`~/.fgfs/Aircraft/` ou le dossier `Aircraft` de votre installation), puis choisir
**KingAir-350**, **KingAir-350ER** ou **KingAir-350ER-G1000** dans le lanceur (les trois variantes sont dans le
même dossier). FlightGear 2020.3 ou plus récent (JSBSim ≥ 1.1).

Le nom du dossier doit rester `KingAir-350` (les chemins du modèle 3D en dépendent).

## Utilisation rapide

| Action | Commande |
|---|---|
| Démarrage automatique | menu *King Air 350 › Automatic start-up* |
| Démarrage manuel | batterie ON, manettes de puissance IDLE, manettes d'hélice plein avant, condition levers CUT-OFF ; starter (interrupteur cockpit ou `s`) ; à 12 % N1 condition lever LOW IDLE (`Shift-F`) ; l'allumage suit, N1 se stabilise à 62 % ; générateurs ON |
| Condition levers | `Shift-F` cran suivant / `Shift-C` cran précédent (CUT-OFF → LOW IDLE → HIGH IDLE), ou les commandes *Mixture* du joystick (axe ou boutons ; mixture 0 = CUT-OFF, 0,5 = LOW IDLE, 1 = HIGH IDLE) |
| Manettes d'hélice | `n` (petit pas, plus de tours) / `N` (grand pas) : 1 450–1 700 tr/min, plein arrière = DRAPEAU |
| Beta / inverse | manettes de puissance au ralenti, `Suppr` (ou menu) puis avancer les manettes : plage beta jusqu'à 35 % de course, inverse au-delà |
| Volets | `[` `]` ou levier du piédestal : UP / APPROACH 40 % (14°) / DOWN 35° |
| Essuie-glaces | sélecteur du panneau supérieur (clic gauche / molette) : PARK / OFF / SLOW / FAST ; PARK ramène les balais en butée puis revient sur OFF |
| Volants | menu *King Air 350 › Yokes visible* (réglage conservé d'une session à l'autre) |
| Départ en vol | `--in-air --altitude=… --vc=…` avec `--prop:/sim/presets/running=true` : moteurs en marche, puissance, pas d'hélice et trims réglés pour le palier, train rentré au-dessus de 150 kt ; l'avion est tenu 4 s, le temps que les hélices se stabilisent. Sans cette option, les moteurs sont arrêtés |
| Pilote automatique | panneau FGC du cockpit (HDG, NAV, APPR, BC, ALT, ALTS, VS, CLIMB, molette de tangage, AP, YD, SR, BNK ; variante G1000 : panneau FGP, voir plus bas) ou dialogue standard *Autopilot* (F11) ; `Ctrl-F` engage/désengage ; l'action joystick *Autopilot disconnect* déconnecte seulement (bouton AP DISC du volant) |
| Amortisseur de lacet | bouton YD ou `Ctrl-Y` (obligatoire au-dessus de 5 000 ft sur l'avion réel) |
| Porte / escalier | `D` |
| Carburant | menu *System failures* (dialogue systèmes) : crossfeed, pompes de transfert aux, générateurs, batterie… |

Limitations : Vmo 263 KIAS / M 0,58 · Vfe 202 (APP) / 158 (DOWN) · Vle 184 · Va 184 · Vmca 94 ·
Vs 96 / Vso 81 KCAS à 15 000 lb · couple 100 % = 3 200 ft·lb · ITT 820 °C · hélice 1 700 tr/min max.
Masses : 15 000 lb décollage/atterrissage, 12 500 lb ZFW, 3 611 lb (539 gal) de carburant.

## Variante 350ER (`KingAir-350ER-set.xml`, `Aero/KingAir-350ER.xml`)

Même cellule, même aile et mêmes PT6A-60A, mais : MTOW 16 500 lb, MLW 15 675 lb, MZFW 13 000 lb, masse à vide
≈ 10 150 lb, 775 gal (5 192 lb) de carburant grâce aux réservoirs de nacelles allongées (les *main* passent à
308,5 gal chacun), train renforcé, légère traînée supplémentaire des nacelles. C'est la cellule de l'ALSR
« Vador » de l'Armée de l'air et de l'Espace (le modèle 3D reste celui du 350, sans boule optronique ; la
livrée de l'ALSR n° 1030 F-RACH est fournie, voir *Livrées* plus bas).
Validation à 16 500 lb : décrochage 100 / 94 / 89 KCAS, montée initiale 2 430 ft/min (livre 2 400),
croisière max 305 KTAS FL240 (livre 303), décollage 3 910 ft sur 50 ft (BFL livre 5 105 ft), monomoteur
725 ft/min (livre 337, même optimisme que le 350). Les deux versions apparaissent séparément dans le lanceur
(`KingAir-350` et `KingAir-350ER`) et partagent tout le reste du paquet.

## Variante 350ER G1000 (`KingAir-350ER-G1000-set.xml`, `Models/KingAir-G1000.xml`)

Cellule et modèle de vol du **350ER** (ci-dessus). Le cockpit est entièrement refait **façon Collins Pro Line Fusion**
(King Air 350ER / 360), d'après photographies. Ses trois grands écrans affichent les pages du **G1000** : c'est le FG1000
fourni avec FlightGear (`$FG_ROOT/Aircraft/Instruments-3d/FG1000`, FlightGear ≥ 2018.3), seul système d'écrans
disponible dans FlightGear. Toutes les commandes du cockpit sont animées, cliquables et reliées aux systèmes. La
description détaillée des panneaux, et la façon de régénérer le cockpit, sont dans `Docs/Fusion-cockpit.md`.
Moteurs, systèmes et pilote automatique sont communs aux trois variantes ; le lanceur propose donc `KingAir-350`,
`KingAir-350ER` et `KingAir-350ER-G1000`.

### Le cockpit

- **Écrans :** PFD pilote, MFD au centre, PFD copilote : trois écrans larges de 14 pouces. L'image G1000 (4:3) occupe
  le centre de chaque écran. Les touches programmables du G1000 se commandent en cliquant leur libellé en bas de
  l'écran, comme sur un écran tactile. Les radios se règlent aussi directement sur les cadres NAV et COM en haut des
  PFD : clic sur une fréquence d'attente pour choisir la radio, molette dessus pour la régler (MHz ; Maj : kHz), clic
  sur la flèche ou la fréquence active pour les permuter. Sur les cartes (carte du MFD, encart du PFD) : molette
  pour changer l'échelle, clic sur l'orientation en haut à droite pour passer de NORTH UP à HDG UP, cliquer-glisser
  pour déplacer la carte ; la case RECENTER, sous l'orientation (ou un double clic), la recentre sur l'avion. Les molettes et touches du G1000 sont reportées :
  - sur le panneau de pilote automatique (FGP) : CRS1, HDG, ALT, CRS2 ;
  - sur les panneaux audio : BARO ;
  - sur les deux boîtiers de curseur du pupitre : FMS, RANGE, D→, MENU, FPL, PROC, CLR, ENT, radios NAV et COM. Le
    sélecteur DISPLAY de chaque boîtier choisit l'écran commandé : PFD 1 ou MFD pour le pilote, MFD ou PFD 2 pour le
    copilote.
- **Clavier (MKP) :** lettres et chiffres pour saisir directement un identifiant (D→, plan de vol, pages WPT), sur
  l'écran du dernier boîtier de curseur utilisé.
- **Écran de secours :** au-dessus du FGP, avec attitude, vitesse, altitude avec son propre calage, cap et bille.
  MENU épure l'affichage, BARO passe en STD, la molette règle le calage (appui : calage du PFD pilote).
- **Pilote automatique :** celui de l'avion (boucles JSBSim), commandé par le FGP. Boutons FD, VS, VNAV, FLC, NAV,
  HDG, APPR, 1/2 BANK, ALT, YD, CPL, AP et YD/AP DISC ; molettes SPEED et de tangage.
  - **CPL :** couple le pilote automatique au PFD pilote ou copilote. Le mode NAV suit la source CDI de ce PFD : GPS
    (plan de vol actif du G1000), NAV1 ou NAV2.
  - **VNAV :** tient une pente vers la prochaine contrainte d'altitude de la route active, en VS avec capture ALTS.
  - **ALT :** l'altitude choisie à la molette ALT est capturée depuis VS, FLC ou PIT (ALTS armé).
  - **Autres commandes :** le bouton GO AROUND de la manette de puissance gauche passe le directeur de vol à 7° à
    cabrer, ailes à plat ; les volants portent le trim électrique, la déconnexion AP / YD et l'alternat.
- **Réversion d'écran :** un écran mis sur OFF s'éteint, et le PFD du même côté passe sur l'écran central. L'inhibition
  TOUCH / CURSOR désactive les touches tactiles ou le boîtier de curseur d'un écran.
- **Nuit :** inscriptions rétroéclairées (rhéostat PANEL LIGHTS et MASTER PANEL LIGHTS du plafonnier), écrans
  auto-éclairés (rhéostats des écrans) et projecteurs d'ambiance (PANEL / PEDESTAL / OVERHEAD FLOOD).
- **Disjoncteurs :** environ 90, sur les parois gauche et droite. Chacun coupe réellement son circuit : radios et
  écrans, éclairages, démarrage, pompes, trims, volets, train, chauffages, conditionnement, etc.

### Le G1000

- `Nasal/fg1000-kingair.nas` charge le FG1000 après l'initialisation du FDM, avec un *Engine Indication System*
  bimoteur turbopropulseur (`Nasal/fg1000-kingair-eis.nas`, cadre `Models/Instruments/FG1000/EIS-KingAir.svg`,
  données publiées par `Nasal/fg1000-kingair-interfaces.nas`) : couple, ITT, tr/min hélice, N1, débit carburant,
  pression et température d'huile en échelles horizontales à deux index L/R avec valeurs numériques, carburant
  par côté et total, tension / courant / charge des générateurs. Plages de couleur = marquages des instruments
  du 350 (couple 100 %, ITT 400-820 °C, hélice 1 450-1 700 tr/min, N1 62-104 %, huile 60/90-135 psi et
  0-99/110 °C, carburant 0-265 lb interdit au décollage). La touche ENGINE du MFD choisit le bas du bandeau :
  ENGINE (ce résumé), SYSTEM (électrique, prélèvement d'air, dégivrage, pressurisation) ou FUEL (chaque réservoir,
  débits, autonomie, distance franchissable, consommé, intercommunication).
- PFD pilote et copilote (écrans FG1000 n° 1 et 3, mêmes réglages) : Vmo 263 kt (fond de l'anémomètre rouge au-delà),
  repères Vr 110, Vx 125, Vy 140, plané 135 kt ; bande de vitesse marquée comme l'anémomètre du 350 (arc blanc
  large 81-96 / étroit 96-158 kt, repère volets APP 202 kt, trait rouge Vmca 94, trait bleu Vyse 125, bande rayée
  au-delà de Vmo).
- PFD : fenêtre CAS (à droite de l'altimètre) alimentée par `Nasal/annunciators.nas` : alarmes en rouge, cautions
  en jaune, avis en blanc ; les nouvelles alarmes clignotent en vidéo inverse jusqu'à l'appui sur MASTER WARNING /
  MASTER CAUTION.
- Heure : l'encadré horaire des PFD affiche l'heure UTC (Z) sur 24 h (heure UTC du simulateur).
- Cap : le cap affiché vient de l'AHRS du cockpit. Il est asservi au compas, ou devient un directionnel libre avec
  DG FREE, recalé par SLEW.
- Alimentation : sorties `fg1000-pfd`, `fg1000-mfd` et `fg1000-pfd2` du bus avionique (`Nasal/electrical.nas`), avec
  leurs disjoncteurs ; les écrans s'éteignent avec l'avionique.
- Fenêtres détachables : menu *King Air 350 › G1000: PFD pop-up window* / *MFD pop-up window* / *copilot PFD
  pop-up window* ; commandes clavier du FG1000 via `fg1000-multikey.xml` (touche `:` puis séquence, voir le
  dialogue *Help › Aircraft keys*).
- Carte hors ligne : menu *King Air 350 › G1000: map tiles (offline map)* (`Nasal/fg1000-maptiles.nas`). On y choisit
  la source des tuiles du fond de carte (TOPO du MFD, encart carte du PFD) :
  - **OpenStreetMap** (par défaut) : téléchargement par Internet, cache dans `$FG_HOME/cache/maps/osm-cache` ;
  - **Local server** : un serveur de tuiles, par exemple `http://localhost:8090/{z}/{x}/{y}.png` ou
    `http://hôte/tile/{z}/{y}/{x}`. Les marqueurs peuvent être dans n'importe quel ordre et l'URL n'a pas besoin
    d'extension :
    - `{z}` `{x}` `{y}` (alias WMTS `{TileMatrix}` `{TileCol}` `{TileRow}`), `{-y}` ou `{tms_y}` pour une
      numérotation TMS, `{s}` pour un sous-domaine `a` / `b` / `c`, `{q}` ou `{quadkey}` pour une numérotation Bing ;
    - `{bbox}` pour un serveur WMS : emprise de la tuile en EPSG:3857, par exemple
      `http://localhost/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=ortho&SRS=EPSG:3857&BBOX={bbox}&WIDTH=256&HEIGHT=256&FORMAT=image/jpeg`.

    FlightGear choisit le décodeur d'image d'après l'extension du fichier en cache : le format réel des tuiles (PNG
    ou JPEG) est donc lu dans une tuile de test (*Test*, *Apply* et au démarrage), pas déduit de l'URL. Les tuiles
    WebP ne sont pas lisibles par FlightGear. FlightGear n'utilise pas le proxy de Windows : sur un réseau où le
    navigateur passe par un proxy, ajouter `--proxy=hôte:port` dans les options du lanceur (sinon le message d'état
    indique « server name not found »). Les tuiles reçues sont mises en cache dans
    `$FG_HOME/cache/maps/tiles-<serveur>-<somme de contrôle>` et restent disponibles serveur arrêté. Un simple dossier
    de tuiles peut être servi avec `python -m http.server 8090 --directory D:\Tiles` ;
  - **Local folder** : un dossier de tuiles `zoom/x/y.png` ou `.jpg`, lu directement sans téléchargement. FlightGear n'autorise
    la lecture que sous FG_HOME, FG_ROOT et les dossiers d'avions et de scènerie. Un dossier situé ailleurs est
    refusé (FlightGear 2024.1 plante sur une lecture interdite) ; il faut alors le servir en *Local server*.

  Un serveur peut être enregistré sous un nom (*Name*, puis *Save* : URL et zoom maximal) ; la liste *Saved
  servers* permet ensuite d'en changer en un clic, et *Delete* retire le serveur choisi.
  Les champs de saisie ne prennent pas Ctrl+V : le bouton *Paste* à côté colle le contenu du presse-papiers.
  Le bouton *Test* vérifie la source à la position de l'avion. *Max zoom* indique le niveau de zoom le plus fin que
  possède la source : au-delà, les tuiles sont agrandies. Les réglages sont conservés d'une session à l'autre.
- Limites :
  - Les pages et symboles sont ceux du G1000, pas ceux du Pro Line Fusion ; l'écran large garde donc des bandes
    noires de chaque côté de l'image 4:3.
  - Le VNAV est simplifié ; les approches GPS avec guidage vertical ne sont pas simulées.
  - Si le dossier FG1000 est absent, les écrans restent noirs et un message s'affiche ; le reste du cockpit
    fonctionne.

## Livrées

Menu *King Air 350 › Select livery* (ou `--prop:/sim/model/livery/file=ALSR` au lancement, nom du fichier sans `.xml`). Toutes les livrées
s'appliquent aux trois variantes ; le choix est conservé d'une session à l'autre.

**Armée de l'Air – ALSR Vador 1030 F-RACH** (`Models/Liveries/ALSR.xml`, texture 4096 × 4096). Livrée de l'ALSR
n° 1030 de l'escadron électronique aéroporté 1/54 « Dunkerque », reproduite d'après des photographies de l'avion :

- blanc intégral, inscriptions basse visibilité gris clair en caractères DIN : **F-RACH** sur le fuselage arrière
  (les deux côtés, dans ses repères d'angle noirs), sur l'extrados de l'aile droite et sous l'aile gauche (lisible
  par-dessous, nez vers le haut), **ARMEE DE L'AIR** sous les hublots, numéro **1030** en haut de la dérive ;
- cocardes à liseré jaune sur le cône arrière (les deux côtés), sur l'extrados de l'aile gauche et, en
  symétrie, sous l'aile droite ;
- bande rouge d'hélice avec **HELICE** et **DANGER** fléchés sur le nez, marquages de la porte (poignée, flèche
  rouge), « DEACTIVATED EMERGENCY EXIT » sur l'issue de secours gauche, prise statique ;
- premier hublot cabine gauche obturé, comme sur l'avion (objet `WindowPlugL1`, affiché seulement avec cette
  livrée) ;
- bords d'attaque en caoutchouc noir, légères salissures de ventre et traces d'échappement sur les nacelles.

L'immatriculation fait partie de la texture : FlightGear n'a pas de fonction générique pour la changer en vol.

**Relief de surface (toutes livrées)** : une *normal map* 4096 × 4096 (`Models/Effects/KingAir-350-normalmap.png`)
ajoute les jointures de tôles, les lignes de rivets, les trappes de visite et les verrous de capots ; son canal
alpha règle la brillance (caoutchouc et pneus mats, échappements satinés).

**Faire une livrée** : les dessous des ailes et des ailerons ont maintenant leur propre place dans la texture
(ils partageaient celle de l'extrados, un marquage d'aile apparaissait donc aussi, inversé, sous l'aile). Les
livrées existantes ont été complétées en conséquence et s'affichent comme avant. Gabarit à jour :
`PaintKit/UV-template-4096.png` (les anciens `KingAir.xcf` / `.svg` restent valables pour tout le reste ; recopier
simplement l'aile sur les deux nouveaux emplacements, voir `Tools/livery/README.md`). Une texture en 2048 × 2048
reste utilisable. Dans la texture, le flanc gauche du fuselage est dessiné en miroir et le flanc droit tourné de
180° (dépliage d'origine du modèle) : les inscriptions y paraissent inversées dans le fichier mais se lisent à
l'endroit sur l'avion.

## Ce qui a été refait

### Aérodynamique (`Aero/KingAir-350.xml`)
- Géométrie réelle : 310 ft², envergure 57,92 ft, CMA 70 in, dièdre 6°, empennage en T 68 ft², dérive 52,3 ft²
  (Beechcraft *Specification and Description* 350i). Position de la CMA, du train, des hélices et des
  réservoirs mesurée directement dans le modèle 3D pour que le visuel et la physique coïncident.
- Portance/traînée par tables (incidence × volets 0/14/35°), décrochage progressif (CLmax 1,55 / 1,85 / 2,18),
  effet de sol, traînée du train, de la direction, des hélices en drapeau, montée en Mach.
- Dérivées de stabilité et de commande estimées par méthodes classiques puis ajustées sur les chiffres publiés
  (Vmca, taux de roulis, roulis hollandais). Débattements TCDS : profondeur 20°/14°, ailerons 25°/15°
  (différentiels), direction 25°, volets 35°.
- Couple des hélices : les deux hélices tournent dans le sens horaire vu de l'arrière. Leur couple de réaction fait
  rouler l'avion à gauche ; la rotation du souffle sur l'aile en compense 85 % (ligne portante, `Tools/swirl_ll.py`).
  Il reste une légère tendance à gauche avec la puissance : environ 3 % d'aileron en montée initiale plein gaz et
  moins de 1 % en croisière, pilote seul à gauche compris.
- Centrage : plage réelle 7,8–31,7 % CMA ; masse à vide 9 650 lb, inerties estimées (Roskam), 4 masses
  ponctuelles (pilote, copilote, cabine, soute) modifiables par le dialogue *Fuel and Payload*.
- Train : géométrie du modèle 3D, roulette de nez orientable (autorité 48° au taxi, réduite en vitesse),
  patins de sécurité bouts d'aile / queue / nez.

### Moteurs et hélices (`Engines/`)
- **PT6A-60A** (`FGTurboProp`) : 1 050 ch plat jusqu'à ≈ ISA+10 au niveau de la mer, puissance fonction de
  la pression, de la vitesse et de la température ; N1 62 % (low idle) – 70 % (high idle) – 104 % ; ITT ;
  débit carburant calibré (≈ 100 lb/h au ralenti, ≈ 515 lb/h par moteur au décollage, ≈ 350 en croisière) ;
  démarrage réaliste (starter → 12 % N1 → ouverture carburant → allumage).
- **Hélice Hartzell 4 pales 105 in** : tables de poussée et de puissance calculées par théorie de l'élément
  de pale (`Tools/bemt2.py`) de −15° (inverse) à 87° (drapeau) ; butée petit pas 7,5°, régulateur
  1 450–1 700 tr/min, drapeau manuel (manette plein arrière) et **autofeather** (armé par défaut,
  déclenche sous 17 % de couple quand les deux manettes sont au-dessus de 90 % N1).
- Plage **beta / inverse** : touche `Suppr`, ≈ −1 500 lb par moteur en pleine inverse.

### Systèmes (`Systems/`, `Nasal/`)
- Carburant : 2 × 190 gal (main) + 2 × 79,5 gal (aux) ; les aux se transfèrent d'abord dans les main
  (pompes AUTO/OFF), crossfeed gauche→droite / droite→gauche.
- Circuit électrique : 2 générateurs 28 V (interrupteurs cockpit), batterie 24 V avec décharge, inverter
  115 V AC pour les EFIS, bus avionique, éclairages. Ampèremètre batterie : décharge sur batterie seule (bus et
  démarreurs, environ 300 A par démarreur), recharge décroissante une fois une génératrice en ligne.
- **Rudder boost** pneumatique (déflexion proportionnelle à l'écart de couple) et **amortisseur de lacet**.
- **Pilote automatique 3 axes** dont les boucles tournent dans JSBSim (`Systems/autopilot.xml`, testées
  hors FlightGear) : HDG, NAV/VOR, LOC avec programmation de gain à l'approche de la station, back course,
  ALT avec capture de l'altitude présélectionnée, VS, IAS, glide. Trim automatique lente en tangage
  (zone morte), déconnexion sur action pilote ou attitude excessive. Le panneau FGC du cockpit (HDG, NAV,
  APPR, BC, ALT, ALTS, VS, CLIMB, AP, YD, SR, 1/2 BANK, molette de tangage) et le dialogue standard de
  FlightGear pilotent les mêmes modes ; le pilote automatique générique de FlightGear est désactivé
  (`Systems/no-generic-autopilot.xml`), sinon il agissait lui aussi sur les gouvernes. Gains vérifiés sur le
  350 et le 350ER (tenue d'altitude et VS à 3 000 et 10 000 ft).
- Instrumentation complète (deux NAV/COM, ADF, DME, transpondeur, GPS KLN-90B, EGPWS).
- **Annonciateurs** (`Nasal/annunciators.nas`, trois variantes) : panneau d'alarmes/cautions du cockpit classique,
  MASTER WARNING / MASTER CAUTION clignotants (extinction par appui), test des voyants, et messages CAS du G1000.
  Messages et seuils des tableaux d'annonciateurs du 350 : #1/#2 AC BUS, DOOR UNLOCKED, L/R FUEL PRES LO,
  L/R OIL PRES LO (< 60 psi), L/R DC GEN, L/R FUEL QTY (< 300 lb, délai 6 s), L/R NO FUEL XFR, BATTERY CHARGE,
  EXT PWR, RVS NOT READY, AUTOFTHER OFF, RUD BOOST OFF, L/R IGNITION ON, FUEL CROSSFEED, L/R AUTOFEATHER (N1 > 88 %),
  L/R PROP PITCH (beta/reverse), LDG/TAXI LIGHT, CABIN ALT HI / CABIN DIFF HI / CABIN ALTITUDE, L/R BL AIR OFF,
  L/R ENG ANTI-ICE, WING / TAIL DEICE, L/R BK DEICE ON, MAN TIES CLOSE. Sans modèle de feu ni de fuite d'air de
  prélèvement, les voyants correspondants ne s'allument qu'au test.
- **Protection contre le givre** (`Nasal/ice-protection.nas`) : panneau ICE PROTECTION animé et fonctionnel
  (antigivrage moteur avec séparateur inertiel ~20 s, cycle SINGLE des boudins ailes 6 s puis empennage 4 s,
  dégivrage hélice AUTO / MANUAL 26-32 A, réchauffage pare-brise, pitots, avertisseur de décrochage, mises à
  l'air carburant, freins), charges électriques correspondantes ; interrupteurs AUTOFEATHER, GEN TIES, PROP TEST,
  poignées coupe-feu (fermeture du robinet carburant) et bouton de test des voyants de train.
- **Pressurisation** (`Nasal/pressurization.nas`, menu *King Air 350 › Pressurization*) : air de prélèvement des
  deux moteurs, contrôleur altitude cabine / vitesse de variation, différentiel limité à 6,5 psid (cabine
  ~2 800 ft au FL200, ~8 600 ft au FL310), cabine dépressurisée au sol (sauf TEST) et fuite sans air de
  prélèvement ; altitude, variation et différentiel cabine affichés sur l'EIS du G1000.
- **Check-lists** (`Checklists/KingAir-350-checklists.xml`) : procédures normales et deux urgences moteur, dans
  *Aide › Check-lists de l'appareil* et sur la page CHKLIST du MFD G1000 ; items cochés automatiquement.

## Validation (JSBSim autonome, ISA, 15 000 lb sauf mention)

| Grandeur | Modèle | Publié |
|---|---|---|
| Décrochage lisse / volets 14 + train / volets 35 + train | 94 / 89 / 81 KCAS | 96 / – / 81 KCAS |
| Taux de montée initial, 140 KIAS | 2 870 ft/min | 2 731 ft/min |
| FL300 à 15 000 lb | 14,5 min | ≈ 20 min (livre, ISA) |
| Croisière max FL240 (12 000 lb) | 307 KTAS, 860 lb/h | 312 KTAS |
| Croisière FL260, 1 500 tr/min (13 000 lb) | 314 KTAS | 310 KTAS |
| Croisière FL280 (14 000 lb) | 298 KTAS, 705 lb/h | 295 KTAS |
| Croisière FL350 (12 600 lb) | 268 KTAS, 440 lb/h | 267 KTAS |
| Long range cruise FL330, 237 KTAS | ≈ 390 lb/h | ≈ 1 570 nm ferry |
| Décollage, 50 ft (volets 0 / 14) | 3 080 / 2 480 ft | 3 300 ft |
| Atterrissage, roulage avec inverse | 1 230 ft | 2 692 ft sur 50 ft sans inverse |
| Vmca (rudder boost, 5° d'inclinaison) | ≈ 95 KCAS | 94 KIAS |
| Montée monomoteur, 125 KIAS, niveau mer | 970 ft/min | 552 ft/min (valeur certifiée, conservative) |
| Plafond monomoteur | ≈ 23 000 ft | 21 500 ft |
| Ralenti sol / haut ralenti | 960 / 1 330 tr/min, 5 / 11 % couple | ≈ 1 050 tr/min |
| Phugoïde (200 KCAS, FL100) | 62 s, ζ 0,13 | typique |
| Roulis hollandais sans / avec amortisseur | 2,8 s, ζ 0,17 / apériodique | – |
| Taux de roulis plein manche 120 / 160 / 220 KCAS | 23 / 36 / 54 °/s | – |

Points connus : la montée en altitude et le monomoteur restent un peu optimistes par rapport au manuel de vol ;
la traînée en configuration lisse a été réglée en priorité sur les vitesses de croisière publiées.

## Sources
- Beechcraft King Air 350i *Specification and Description* (dimensions, masses, centrage, performances, limitations).
- FAA TCDS A24CE (PT6A-60A : 1 050 ch, 3 200 ft·lb, 1 700 tr/min, ITT 820 °C ; débattements des gouvernes ; hélice).
- Fiches de limitations opérateur (vitesses, carburant, autofeather, rudder boost, amortisseur de lacet).
- Articles AOPA / King Air Magazine (croisière réelle FL280 / FL350, temps de montée).
- ICAS 2002-783 (enveloppe d'essais en vol du 350), code source JSBSim (FGTurboProp, FGPropeller) et interface JSBSim de FlightGear.
- FlightSafety *King Air 300/350 Pilot Training Manual* (marquages des instruments, vitesses, tableaux
  d'annonciateurs) et check-list King Air 350 (V1/Vr/V2), fournis avec le *King Air 350 Realism Mod* pour MSFS.
- MSFS (Asobo King Air 350i) : débattements de gouvernes et incidence de l'empennage utilisés comme recoupement.

## Outils (`Tools/`)
`bemt2.py`/`gen_prop2.py` (hélice), `pkg_engine.py` (moteur), `gen_aero.py` (avion) régénèrent les fichiers
JSBSim ; `t_*.py` sont les scripts de validation (nécessitent `pip install jsbsim`) ; `t_level.py` calcule les tables
de vol en palier du départ en vol et `swirl_ll.py` le moment de roulis dû à la rotation du souffle. Lancer depuis `Tools/`
avec un dossier `aircraft/KingAir-350` + `engine/` recopié comme dans les scripts, ou adapter les chemins.
`Tools/livery/` régénère la livrée ALSR et la normal map (voir son `README.md`).
