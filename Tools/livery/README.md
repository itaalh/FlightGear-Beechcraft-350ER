# Générateur de la livrée ALSR et de la normal map

`alsr.py` peint `Models/Liveries/ALSR.png` (ALSR « Vador » n° 1030, F-RACH) et `Models/Effects/KingAir-350-normalmap.png`
(relief commun à toutes les livrées) directement sur le modèle 3D : chaque texel de la texture connaît sa position
sur l'avion (`maps.py`), les marquages sont dessinés en mètres puis projetés.

```
pip install numpy scipy pillow numba
git clone https://github.com/playbeing/dinish          # police DIN 1451 libre (SIL OFL)
DINISH_DIR=dinish/ofl/dinish python3 alsr.py            # écrit dans Models/…
DINISH_DIR=… python3 alsr.py --out /tmp/essai           # ou ailleurs
```

Environ 40 s et 4 Go de mémoire pour une texture 4096.

## Mesures

Les positions viennent de photographies du F-RACH (vue aérienne trois-quarts avant gauche de J.-L. Brunet /
armée de l'Air et de l'Espace, vues au sol côté droit). Pour chaque zone, la pose de l'appareil photo a été
calculée à partir de points reconnaissables du modèle (hublots, porte, pointe du nez, saumons, winglets), puis
la photo a été reprojetée sur le modèle en vue de côté ou de dessus orthographique pour y lire les cotes :

| Élément | Position (m, repère du modèle : x vers l'arrière, y vers le haut) |
|---|---|
| F-RACH fuselage | x 1,20 → 2,71, ligne de base y 0,01, hauteur 0,33 ; repères d'angle x 2,15 / 2,78, y −0,03 / 0,47 |
| Cocarde fuselage | centre x 3,12, y 0,38, Ø 0,335 (liseré jaune) |
| ARMEE DE L'AIR | x −1,80 → −0,07, ligne de base y 0,08, hauteur 0,18 |
| 1030 (dérive) | x 5,05 → 5,49, ligne de base y 2,30, hauteur 0,175 |
| Bande d'hélice | x −5,36, largeur 0,075, du bas du fuselage à y 0,23 |
| F-RACH aile droite | z −4,45 → −7,0 (lecture de l'emplanture vers le saumon, haut des lettres vers le bord d'attaque), hauteur 0,49 |
| F-RACH sous l'aile gauche | symétrique de l'aile droite : z 4,45 → 7,0, même hauteur ; position OACI (annexe 7), lisible par-dessous nez vers le haut |
| Cocarde aile gauche | x −1,85, z 5,95, Ø 0,48 (extrados) |
| Cocarde aile droite | symétrique : x −1,85, z −5,95, Ø 0,48, sous l'aile |

Le gris des inscriptions a été mesuré à environ 73 % de la luminance du blanc (photo par temps couvert).

## Changements de l'UV du modèle (`KingAir.ac`)

- Intrados des ailes, des ailerons et de leurs tabs : nouvelles îles, aile gauche à (661, 828) px, aile droite à
  (24, 963) px dans une texture 2048 (échelle 0,616 et 0,448 de l'île d'extrados). Pour adapter une ancienne
  livrée : copier le rectangle de l'aile gauche (u 0,5009–1,0002, v 0–0,1507) et celui de l'aile droite
  (u 0,0002–0,4996, v 0,0013–0,1516), les réduire à ces échelles et les coller à ces positions (c'est ce qui a été
  fait pour les livrées fournies).
- `WindowPlugL1` : disque qui obture le premier hublot gauche, texturé dans le carré (1600, 24) px de 96 px de
  côté (texture 2048) ; affiché si la livrée met `sim/model/livery/window-plug-l1` à `true`.
- `fix_degenerate_uv.py` : donne une surface de texture minuscule (0,6 texel) aux polygones dont les UV étaient
  réduites à un point ou à une ligne, sinon OpenGL ne peut pas calculer les tangentes de la normal map.
