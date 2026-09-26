# Journal des modifications

Toutes les évolutions notables du King Air 350 pour FlightGear.
Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), numérotation [SemVer](https://semver.org/lang/fr/).

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

[2.1.4]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/v2.1.3...v2.1.4
[2.1.3]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/v2.1.2...v2.1.3
[2.1.2]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/v2.1.1...v2.1.2
[2.1.1]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/42422ea...v2.1.1
[2.1.0]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/compare/c71f701...f75b48e
[2.0.0]: https://github.com/itaalh/FlightGear-Beechcraft-350ER/tree/c71f701
