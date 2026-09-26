# Beechcraft King Air 350 (B300) pour FlightGear — modèle de vol JSBSim reconstruit

Version 2.0.0 (2026) — modèle de vol, moteurs, hélices, systèmes et pilote automatique entièrement refaits.
Modèle 3D et cockpit : SM, D-ECHO, Lesbof, Bomber, it0uchpods, GabrielYV, IAHM-COL, JWocky (2015-2017).
Licence : GPL v2 ou ultérieure (voir `COPYING`).

## Installation

##Après téléchargement, renommez le dossier obtenu en KingAir-350 avant de le placer dans votre dossier Aircraft.

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
| Condition levers | `Shift-F` cran suivant / `Shift-C` cran précédent (CUT-OFF → LOW IDLE → HIGH IDLE) ou axe *condition* du joystick |
| Manettes d'hélice | `n` (petit pas, plus de tours) / `N` (grand pas) : 1 450–1 700 tr/min, plein arrière = DRAPEAU |
| Beta / inverse | manettes de puissance au ralenti, `Suppr` (ou menu) puis avancer les manettes : plage beta jusqu'à 35 % de course, inverse au-delà |
| Volets | `[` `]` : UP / APPROACH 14° / DOWN 35° |
| Pilote automatique | panneau FGC du cockpit (HDG, NAV, APPR, BC, ALT, molette de tangage, AP, YD, SR, BNK) ou dialogue standard *Autopilot* (F11) ; `Ctrl-F` engage/désengage |
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
« Vador » de l'Armée de l'air et de l'Espace (le modèle 3D reste celui du 350, sans boule optronique).
Validation à 16 500 lb : décrochage 100 / 94 / 89 KCAS, montée initiale 2 430 ft/min (livre 2 400),
croisière max 305 KTAS FL240 (livre 303), décollage 3 910 ft sur 50 ft (BFL livre 5 105 ft), monomoteur
725 ft/min (livre 337, même optimisme que le 350). Les deux versions apparaissent séparément dans le lanceur
(`KingAir-350` et `KingAir-350ER`) et partagent tout le reste du paquet.

## Variante 350ER G1000 (`KingAir-350ER-G1000-set.xml`, `Models/KingAir-G1000.xml`)

Cellule et modèle de vol du **350ER** (ci-dessus) avec un cockpit modernisé façon **King Air 350i / retrofit Garmin** : les deux écrans Garmin GDU 1044B du
FG1000 fourni avec FlightGear (`$FG_ROOT/Aircraft/Instruments-3d/FG1000`, FlightGear ≥ 2018.3) remplacent
le PFD EFIS-84 du pilote (ADI, HSI, anémomètre, altimètre, variomètre, RMI) et la pile radio COM1/NAV1/ADF1,
l'alerteur d'altitude et le KLN-90B, qui sont masqués automatiquement (`sim/model/g1000/enabled`).
Moteurs, systèmes et pilote automatique sont communs aux trois variantes ; le lanceur propose donc `KingAir-350`,
`KingAir-350ER` et `KingAir-350ER-G1000`.

- `Nasal/fg1000-kingair.nas` charge le FG1000 après l'initialisation du FDM ; `Nasal/fg1000-kingair-interfaces.nas`
  remplace l'*Engine Indication System* piston du FG1000 par un éditeur turbopropulseur (moteur 1 : tr/min hélice,
  MAN = couple %, FF, huile, EGT = ITT). Les jauges analogiques des deux moteurs restent dans le tableau de bord.
- Alimentation : sorties `fg1000-pfd` et `fg1000-mfd` du bus avionique (`Nasal/electrical.nas`) ; les écrans
  s'éteignent avec l'avionique.
- Fenêtres détachables : menu *King Air 350 › G1000: PFD pop-up window* / *MFD pop-up window* ; commandes clavier du
  FG1000 via `fg1000-multikey.xml` (touche `:` puis séquence, voir le dialogue *Help › Aircraft keys*).
- Les écrans sont posés en applique 3,7 cm devant le tableau de bord ; pour un montage affleurant, voir
  `Docs/G1000-Blender.md` (gabarits de découpe `Docs/G1000-cutters.obj/.ac`, plan `Docs/G1000-panel-layout.png`).
  Les propriétés `sim/model/g1000/pfd|mfd/dx-m|dy-m|dz-m` permettent de recaler les écrans en vol.
- Limites : EIS conçu pour un monomoteur, pilote automatique = panneau FGC de l'avion (le GFC 700 du FG1000
  n'est pas chargé), page carburant sur `tank[0]`/`tank[1]`. Si le dossier FG1000 est absent, la variante
  démarre avec les instruments d'origine et affiche un message.

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
  115 V AC pour les EFIS, bus avionique, éclairages.
- **Rudder boost** pneumatique (déflexion proportionnelle à l'écart de couple) et **amortisseur de lacet**.
- **Pilote automatique 3 axes** dont les boucles tournent dans JSBSim (`Systems/autopilot.xml`, testées
  hors FlightGear) : HDG, NAV/VOR, LOC avec programmation de gain à l'approche de la station, back course,
  ALT avec capture de l'altitude présélectionnée, VS, IAS, glide. Trim automatique en tangage,
  déconnexion sur action pilote ou attitude excessive. Le panneau FGC du cockpit et le dialogue
  standard de FlightGear pilotent les mêmes modes.
- Instrumentation complète (deux NAV/COM, ADF, DME, transpondeur, GPS KLN-90B, EGPWS).

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
- MSFS (Asobo King Air 350i) : débattements de gouvernes et incidence de l'empennage utilisés comme recoupement.

## Outils (`Tools/`)
`bemt2.py`/`gen_prop2.py` (hélice), `pkg_engine.py` (moteur), `gen_aero.py` (avion) régénèrent les fichiers
JSBSim ; `t_*.py` sont les scripts de validation (nécessitent `pip install jsbsim`). Lancer depuis `Tools/`
avec un dossier `aircraft/KingAir-350` + `engine/` recopié comme dans les scripts, ou adapter les chemins.
