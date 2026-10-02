# Journal des modifications

Toutes les évolutions notables du King Air 350 pour FlightGear.
Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), numérotation [SemVer](https://semver.org/lang/fr/).

## Non publié

### Ajouté
- **350ER G1000 : nouveau cockpit façon Collins Pro Line Fusion** (King Air 350ER / 360), refait d'après
  photographies. Il remplace, pour cette variante seulement, tout le cockpit classique, hors plancher et palonniers :
  - **Auvent et tableau :** auvent avec bosse de l'écran de secours, MASTER WARNING / MASTER CAUTION pilote et
    copilote, poussoirs incendie (extincteurs, robinets coupe-feu), balises et TAWS, RADIO CALL.
  - **Écrans :** trois écrans larges de 14 pouces qui affichent les pages du FG1000. Les touches programmables se
    commandent en cliquant leur libellé en bas de l'écran, comme sur un écran tactile.
  - **Pilote automatique (FGP) :** FD, VS, VNAV, FLC, NAV, HDG, APPR, 1/2 BANK, ALT, YD, CPL, AP, YD/AP DISC,
    molettes CRS1 / SPEED / HDG / ALT / CRS2 et molette de tangage.
  - **Écran de secours :** attitude, vitesse, altitude avec son propre calage, cap et bille.
  - **Tableau et panneaux inférieurs :**
    - panneaux audio pilote et copilote ;
    - bandeau de commande des écrans (réversion, sources AHS / ADS, inhibition tactile / curseur, PROP SYNC,
      DG FREE / SLEW, EMER FREQ, statique de secours) ;
    - panneaux inférieurs : électricité, démarrage, antigivrage, éclairage, train, conditionnement d'air, jauges de
      volets et de cabine ;
    - volants avec trim électrique, déconnexion AP / YD et alternat.
  - **Pupitre :** manettes de puissance (bêta / inverse, GO AROUND, silence de l'avertisseur de train), d'hélice et
    de condition ; volets ; trims. Deux boîtiers de curseur et un clavier commandent le G1000 : molette FMS, portée,
    D→, MENU, FPL, PROC, CLR, ENT, radios NAV / COM, saisie des identifiants au clavier. S'y ajoutent le contrôleur de
    pressurisation, RUDDER BOOST, ELEV TRIM, les tests d'avertisseurs et l'enregistreur de conversations.
  - **Plafonnier et parois :** rhéostats d'éclairage (inscriptions, écrans, projecteurs), essuie-glaces, signaux
    cabine, instruments électriques et OAT ; panneau carburant (jauges MAIN / AUX / TEST, intercommunication, pompes
    de secours, transfert) ; environ 90 disjoncteurs qui coupent réellement leur circuit ; compas de secours ;
    sièges, dont l'accoudoir intérieur se relève d'un clic (relevé au démarrage, pour laisser voir le pupitre).
  - **Nuit :** inscriptions rétroéclairées, écrans auto-éclairés et projecteurs d'ambiance.
- **Nouvelles fonctions** (Nasal/fusion-cockpit.nas) : synchroniseur d'hélices, VNAV simplifié (vers la prochaine
  contrainte d'altitude de la route), couplage du pilote automatique au PFD copilote (CPL), GO AROUND, avertisseur
  de train, directionnel libre (DG FREE / SLEW), prise statique de secours, réversion d'écran, température cabine,
  compteur d'heures, voyant RADIO CALL, pompes de secours carburant.

### Modifié
- **Systèmes communs** (sans effet sur le 350 et le 350ER) : démarreur seul sans allumage, allumage automatique
  commutable, test de mise en drapeau automatique et du régulateur de survitesse, pare-brise HI, air pneumatique
  des clapets de prélèvement, disjoncteurs lus par l'électricité, l'antigivrage, la pressurisation et les
  annonciateurs.

### Supprimé
- Plaque `Models/G1000-panel.ac` et documentation de pose des boîtiers GDU (`Docs/G1000-*`), remplacées par le
  cockpit Fusion.

## [2.4.2] — 2026-09-27

### Corrigé
- **Roulis à gauche avec la puissance** (350, 350ER, G1000). Les deux hélices tournent dans le même sens (horaire vu
  de l'arrière). Le modèle appliquait tout leur couple de réaction, qui fait rouler l'avion à gauche, sans l'effet
  inverse : la rotation du souffle sur l'aile placée derrière chaque hélice le fait rouler à droite. Ce terme est
  ajouté, à 85 % du couple (estimation par ligne portante, `Tools/swirl_ll.py`). Aileron nécessaire pour garder les
  ailes à plat, pilote seul à gauche compris :
  - montée initiale plein gaz : environ 3 % (18 % auparavant) ;
  - croisière : moins de 1 % (4,5 % auparavant).
- **Départ en vol moteurs en marche** (`--in-air` avec `--prop:/sim/presets/running=true`). L'équilibrage
  automatique de JSBSim n'aboutit pas avec les hélices régulées. Il laissait :
  - les hélices presque en drapeau sous 200 tr/min, donc sans poussée, ou tournant à deux régimes différents,
    d'où un fort lacet puis un roulis (−44° en 13 s) ;
  - les manettes au ralenti et aucun trim.

  L'avion part désormais en palier :
  - puissance, pas d'hélice et trim de profondeur tirés de tables de vol en palier (`Tools/t_level.py`) ;
  - train rentré au-dessus de 150 kt ;
  - avion maintenu 4 s à vitesse et attitude constantes, le temps que les hélices se calent à 1 700 tr/min,
    puis trim d'ailerons réglé.

  Avec du vent en altitude, FlightGear n'applique le vent qu'après l'initialisation : l'avion subit alors une
  courte rafale au départ, comme tous les avions.

## [2.4.1] — 2026-09-26

### Modifié
- **G1000 : heure UTC.** L'encadré horaire des PFD affiche l'heure UTC (Z) sur 24 h, libellé « UTC », comme les
  horloges analogiques. Il affichait l'heure locale sur 12 h (« LCL »). Les horloges analogiques suivent l'heure
  UTC du simulateur, et non celle du PC.

## [2.4.0] — 2026-09-26

### Ajouté
- **Essuie-glaces** : le sélecteur PARK / OFF / SLOW / FAST du panneau supérieur fonctionne (clic, molette) et
  anime les balais du pare-brise, qui balaient vers l'extérieur. Alimentés par le bus DC ; OFF les arrête sur
  place, PARK les ramène en butée et revient sur OFF.

### Corrigé
- **Volets APPROACH à 14°** (40 %, *Pilot Training Manual*) au lieu de 17,5° : le cran intermédiaire était réglé à
  50 % de la course, alors que les tables aérodynamiques sont construites pour 0 / 14 / 35°. Le levier du
  piédestal passe par les mêmes crans que les touches `[` `]`, et l'indicateur pointe sur le repère APPROACH.
- **Volants** : ils ne s'affichaient jamais (l'animation lisait une propriété que rien ne définissait) et le menu
  *Yokes visible* restait sans effet. Visibles par défaut, réglage conservé d'une session à l'autre.
- **Ampèremètre batterie** : il restait à zéro. Il indique la décharge sur batterie seule (bus, dégivrage,
  environ 300 A par démarreur au lancement, aiguille en butée) et la recharge, décroissante, une fois une
  génératrice ou le groupe de parc en ligne. La batterie ne se recharge plus interrupteur BATT sur OFF.

## [2.3.0] — 2026-09-26

### Ajouté
- **G1000 : trois écrans alignés**, comme les King Air 350 modernisés G1000 NXi : un PFD copilote (troisième GDU
  1044B, écran FG1000 n° 3) avec la même bande de vitesse et la même fenêtre CAS que le PFD pilote, et une plaque
  qui recouvre les anciens instruments des deux places, les radios et la colonne des jauges moteur (les moteurs
  sont sur l'EIS du MFD). Les objets recouverts sont masqués. Menu *copilot PFD pop-up window*.
- **G1000 : éclairage de nuit** des touches et boutons des trois écrans (rétroéclairage des cadres GDU), réglé par
  le rhéostat *Instruments* du dialogue *Lights* et alimenté par le bus DC.
- **G1000 : pilote automatique relié au G1000.**
  - **Touches :** celles des écrans GDU (AP, FD, HDG, NAV, APR, BC, ALT, VS, FLC, NOSE UP / DN) commandent le
    pilote automatique du King Air, comme le panneau FGC.
  - **Guidage :** la touche CDI du PFD pilote choisit la source. En GPS, le mode NAV suit le plan de vol actif du
    G1000 : interception à 45°, puis convergence sur la branche sans dépassement.
  - **ALT SEL :** l'altitude choisie est capturée depuis VS, FLC ou PIT, sans modifier l'altitude tenue en ALT.
  - **Affichage :** les modes actifs et armés, la référence (vitesse verticale, vitesse, altitude) et le directeur
    de vol s'affichent sur le PFD.

### Corrigé
- **Index de cap** : le bouton HDG du G1000 et le dialogue du pilote automatique n'agissaient qu'en mode HDG (le
  bouton du panneau FGC reprenait la main aussitôt dans les autres modes). Le dernier bouton tourné l'emporte
  désormais, sur les trois variantes.

## [2.2.0] — 2026-09-26

### Ajouté
- **G1000 : carte hors ligne.** Menu *King Air 350 › G1000: map tiles (offline map)* : le fond de carte du MFD et de
  l'encart du PFD peut venir d'un serveur de tuiles local (URL `{z}/{x}/{y}`, tuiles mises en cache pour le vol
  hors ligne) ou d'un dossier de tuiles, au lieu d'OpenStreetMap par Internet. Bouton de test, réglages conservés
  entre les sessions.

## [2.1.4] — 2026-09-26

### Corrigé
- **Aiguilles et boutons qui tournaient autour d'un mauvais point** (centres de rotation hérités d'une ancienne
  version du modèle 3D, décalés de 2 à 80 cm) : les aiguilles sortaient de leur cadran ou disparaissaient.
  Centres et axes recalculés sur la géométrie et vérifiés en vue de face dans FlightGear :
  - indicateur de volets (piédestal) ;
  - horloges pilote et copilote (heures, minutes, secondes) ;
  - jauges carburant gauche et droite, avec leur échelle non linéaire (graduations plus larges autour de 1 000 lb) ;
  - panneau supérieur : DC % LOAD (0-100 % sur toute l'échelle), voltmètre et ampèremètre batterie, AC VOLTS,
    PROP AMPS (chaque aiguille tourne du côté opposé à son échelle ; elles affichent maintenant le courant de
    dégivrage hélice au lieu de la charge des génératrices) ;
  - boutons calage altimétrique, alerteur d'altitude, volume COM/NAV/ADF, trims d'aileron et de direction, roue de
    trim de profondeur, bouton de roulis du pilote automatique, sélecteur d'essuie-glace ; axe des volants.

## [2.1.3] — 2026-09-26

### Corrigé
- **Leviers de condition au joystick** : les commandes *Mixture* de la configuration joystick de FlightGear (axes
  « Mixture », « Mixture All Engines », boutons Rich / Lean) déplacent maintenant les leviers de condition
  (0 = CUT-OFF, 0,5 = LOW IDLE, 1 = HIGH IDLE) ; auparavant ils restaient sans effet et seuls la souris, le clavier
  et le menu les manœuvraient. Seuls les mouvements sont suivis : la mixture à 1 du démarrage n'ouvre pas le
  carburant.

## [2.1.2] — 2026-09-26

### Corrigé
- **Bouton joystick « Autopilot disconnect »** : l'action standard de FlightGear écrit
  `/controls/autoflight/autopilot/engage`, que l'avion ne créait ni ne lisait (le bouton restait sans effet et
  provoquait une erreur Nasal). Elle déconnecte maintenant le pilote automatique, comme le bouton AP DISC du
  volant ; elle ne l'engage jamais (engagement : bouton AP du panneau FGC, `Ctrl-F` ou dialogue F11).

## [2.1.1] — 2026-09-26

### Corrigé
- **Page CHKLIST du G1000** : ouvrir la page faisait planter l'interface de données de navigation du FG1000
  (FlightGear 2024.1 ne gère pas les check-lists sans groupe), qui était alors retirée et ne répondait plus
  aux autres pages. Les check-lists sont maintenant rangées en deux groupes, « Normal Procedures » et
  « EMERGENCY » (celui qu'ouvre la touche EMERGENCY du G1000).

## [2.1.0] — 2026-09-26

Améliorations tirées de l'étude des mods MSFS 2020 (King Air G1000, Pro Line 21, Realism Mod) et du
*King Air 300/350 Pilot Training Manual* de FlightSafety. Testé dans FlightGear 2024.1.

### Ajouté
- **EIS bimoteur sur le MFD G1000** : couple, ITT, hélice, N1, débit carburant, pression et température
  d'huile (échelles à deux index L/R et valeurs numériques), carburant par côté et total, tension / courant /
  charge des générateurs, courant de dégivrage hélice, et bloc CABIN (altitude, variation, différentiel).
  Plages de couleur = marquages des instruments du 350.
- **Fenêtre CAS du PFD G1000** : alarmes en rouge, cautions en jaune, avis en blanc ; les nouvelles alarmes
  clignotent en vidéo inverse jusqu'à l'appui sur MASTER WARNING / MASTER CAUTION.
- **Bande de vitesse du PFD** marquée comme l'anémomètre du 350 (arc blanc large 81-96 / étroit 96-158 kt,
  repère volets APP 202 kt, trait rouge Vmca 94, trait bleu Vyse 125, bande rayée au-delà de Vmo 263) et repères
  Vr 110, Vx 125, Vy 140, plané 135 kt.
- **Logique d'annonciateurs** commune aux trois variantes (`Nasal/annunciators.nas`) : le panneau d'alarmes du
  cockpit classique est enfin alimenté, MASTER WARNING / CAUTION clignotants, test des voyants ; messages et
  seuils des tableaux d'annonciateurs du 350.
- **Check-lists** (`Checklists/KingAir-350-checklists.xml`) : 14 check-lists (procédures normales et deux pannes
  moteur), dans *Aide › Check-lists de l'appareil* et sur la page CHKLIST du MFD G1000 ; items cochés
  automatiquement.
- **Protection contre le givre** (`Nasal/ice-protection.nas`) : panneau ICE PROTECTION animé et fonctionnel
  (antigivrage moteur, boudins ailes et empennage, dégivrage hélice, réchauffage pare-brise, pitots,
  avertisseur de décrochage, mises à l'air carburant, freins) avec leurs charges électriques et leurs avis CAS.
- **Pressurisation** (`Nasal/pressurization.nas`, menu *King Air 350 › Pressurization*) : air de prélèvement,
  contrôleur altitude cabine / vitesse de variation, différentiel limité à 6,5 psid, dépressurisation au sol ;
  alarmes CABIN ALT HI, CABIN DIFF HI, CABIN ALTITUDE, L/R BL AIR OFF.
- Commandes du cockpit jusque-là inertes : interrupteur AUTOFEATHER, GEN TIES, PROP TEST, poignées coupe-feu
  (fermeture du robinet carburant), bouton de test des voyants de train ; boutons ALTS, VS et CLIMB du
  panneau FGC.

### Corrigé
- **Pilote automatique** :
  - les boutons du panneau FGC (HDG, NAV, APPR, BC, ALT, VS, AP, YD, SR, 1/2 BANK, molette de tangage) étaient
    désactivés dans le modèle 3D : ils sont de nouveau cliquables ;
  - le pilote automatique générique de FlightGear agissait en parallèle sur les gouvernes et provoquait des
    désengagements : il est remplacé par un fichier vide (`Systems/no-generic-autopilot.xml`) ;
  - la tenue d'altitude oscillait sur le 350ER : trim automatique ralentie avec zone morte, gain intégral de la
    boucle VS divisé par deux, décalage altitude vraie / indiquée filtré.
- **Jauges d'huile** : JSBSim et le script Nasal écrivaient la même propriété, ce qui faisait trembler les
  aiguilles ; le modèle Nasal a ses propres propriétés (`oil-pressure-ind-psi`, `oil-temperature-ind-degf`) et
  les jauges du tableau classique sont réétalonnées sur leur cadran (la température tournait en °F × 30).
- Valeurs de l'EIS colorées d'après la valeur affichée (une hélice régulée à 1 700 tr/min n'est plus en rouge).

### Modifié
- Le publieur moteur du FG1000 envoie les données des deux moteurs (auparavant moteur 1 seulement, sur les
  cases d'un moteur à pistons) et remplace le publieur carburant générique.

## [2.0.0] — 2026-09-25

Première publication de la version reconstruite.

### Ajouté
- Modèle de vol JSBSim entièrement refait (aérodynamique, PT6A-60A, hélices Hartzell), validé sur les données
  constructeur (voir le README).
- Variantes **KingAir-350**, **KingAir-350ER** et **KingAir-350ER-G1000** (FG1000 de FlightGear).
- Systèmes carburant, électrique, rudder boost, amortisseur de lacet, pilote automatique 3 axes dont les
  boucles tournent dans JSBSim, démarrage automatique, beta / inverse, autofeather.

[2.4.2]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/v2.4.1...v2.4.2
[2.4.1]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/v2.4.0...v2.4.1
[2.4.0]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/v2.1.4...v2.2.0
[2.1.4]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/v2.1.3...v2.1.4
[2.1.3]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/v2.1.2...v2.1.3
[2.1.2]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/v2.1.1...v2.1.2
[2.1.1]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/42422ea...v2.1.1
[2.1.0]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/c71f701...f75b48e
[2.0.0]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/tree/c71f701
