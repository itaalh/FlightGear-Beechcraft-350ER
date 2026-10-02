# Cockpit Pro Line Fusion — référence des commandes

Généré par `Tools/fusion/gen_doc.py` à partir de `Tools/fusion/cockpit_spec.py` (ne pas modifier à la main).
La colonne *Info* reprend la bulle d'aide affichée dans FlightGear au survol de la commande.
Les volants, manettes, levier de volets, roue de trim et le compas sont décrits dans `Docs/Fusion-cockpit.md`.

## Auvent : MASTER WARNING / CAUTION pilote (`GS.masterL`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `MWL` | poussoir lumineux | voyant `master_warning` | Master warning: press to reset |
| `MCL` | poussoir lumineux | voyant `master_caution` | Master caution: press to reset |

## Auvent : MASTER WARNING / CAUTION copilote (`GS.masterR`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `MWR` | poussoir lumineux | voyant `master_warning` | Master warning: press to reset |
| `MCR` | poussoir lumineux | voyant `master_caution` | Master caution: press to reset |

## Auvent : incendie moteur gauche (`GS.fireL`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `FIREL` | poussoir lumineux | voyant `fire_0` | Left engine fire extinguisher (push to discharge) |
| `DISCHL` | voyant | voyant `ext_disch_0` |  |
| `FWL` | poussoir lumineux | voyant `fw_valve_0` | Left firewall fuel valve: … |

## Auvent : incendie moteur droit (`GS.fireR`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `FIRER` | poussoir lumineux | voyant `fire_1` | Right engine fire extinguisher (push to discharge) |
| `DISCHR` | voyant | voyant `ext_disch_1` |  |
| `FWR` | poussoir lumineux | voyant `fw_valve_1` | Right firewall fuel valve: … |

## Auvent : balises et TAWS (`GS.marker`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `TAWS` | voyant | voyant `ann_taws` |  |
| `MKRO` | voyant | voyant `ann_mkro` |  |
| `MKRM` | voyant | voyant `ann_mkrm` |  |
| `MKRI` | voyant | voyant `ann_mkri` |  |

## Auvent : RADIO CALL (`GS.radiocall`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `RADIOCALL` | poussoir lumineux | voyant `radio_call` | Radio call: lights when ATC calls on the radio, press to reset |

## Panneau de pilote automatique (FGP) (`FGP`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `FGP.FDL` | poussoir | voyant `fgp_fd` | Flight director on / off |
| `FGP.FDR` | poussoir | voyant `fgp_fd` | Flight director on / off |
| `FGP.VS` | poussoir | voyant `fgp_vs` | VS: vertical speed hold (pitch wheel sets the rate) |
| `FGP.VNAV` | poussoir | voyant `fgp_vnav` | VNAV: vertical navigation (see the message) |
| `FGP.FLC` | poussoir | voyant `fgp_flc` | FLC: flight level change (holds the SPEED target) |
| `FGP.NAV` | poussoir | voyant `fgp_nav` | NAV: lateral navigation (source: CDI of the coupled PFD) |
| `FGP.BANK` | poussoir | voyant `fgp_bank` | 1/2 BANK: bank limit 14 deg |
| `FGP.HDG` | poussoir | voyant `fgp_hdg` | HDG: heading select |
| `FGP.APPR` | poussoir | voyant `fgp_appr` | APPR: approach (localizer and glideslope) |
| `FGP.ALT` | poussoir | voyant `fgp_alt` | ALT: altitude hold |
| `FGP.YD` | poussoir | voyant `fgp_yd` | YD: yaw damper |
| `FGP.CPL` | poussoir |  | CPL: autopilot coupled to the pilot or copilot PFD |
| `FGP.AP` | poussoir | voyant `fgp_ap` | AP: autopilot engage / disengage |
| `FGP.CPLL` | voyant | voyant `cpl_left` |  |
| `FGP.CPLR` | voyant | voyant `cpl_right` |  |
| `FGP.DISC` | poussoir |  | YD/AP DISC: disconnects the autopilot and the yaw damper |
| `FGP.CRS1` | bouton rotatif | `sim/model/fusion/knobs/crs1` | CRS1: pilot PFD course (push: centre on the station) |
| `FGP.CRS2` | bouton rotatif | `sim/model/fusion/knobs/crs2` | CRS2: copilot PFD course (push: centre on the station) |
| `FGP.SPD` | bouton rotatif | `sim/model/fusion/knobs/spd` | SPEED: FLC target … kt (push: current speed) |
| `FGP.HDGK` | bouton rotatif | `sim/model/fusion/knobs/hdg` | HDG: heading bug … (push: sync on the current heading) |
| `FGP.ALTK` | bouton rotatif | `sim/model/fusion/knobs/alt` | ALT: preselected altitude … ft (shift: 1000 ft) |
| `FGP.PITCHUP` | zone cliquable |  | Pitch wheel: nose DOWN (VS / FLC / pitch target) |
| `FGP.PITCHDN` | zone cliquable |  | Pitch wheel: nose UP |

## Écran de secours (`STBY`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `STBY.MENU` | poussoir |  | Standby display: MENU (declutter) |
| `STBY.BARO` | poussoir |  | Standby display: BARO STD / setting |
| `STBY.KNOB` | bouton rotatif | `instrumentation/altimeter[1]/setting-inhg` | Standby altimeter setting: … inHg (push: pilot PFD setting) |

## Panneau audio pilote (`AUDIOL`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `AUDL.XMT` | bouton rotatif | `controls/fusion/audio[0]/xmit` | Transmitter: … |
| `AUDL.VOL` | bouton rotatif | `controls/fusion/audio[0]/master-vol` | Audio master volume: … |
| `AUDL.T` | voyant | voyant `xmit_0` |  |
| `AUDL.COMM1` | bouton rotatif | `controls/fusion/audio[0]/comm1-vol` | COMM1 receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDL.COMM2` | bouton rotatif | `controls/fusion/audio[0]/comm2-vol` | COMM2 receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDL.NAV1` | bouton rotatif | `controls/fusion/audio[0]/nav1-vol` | NAV1 receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDL.NAV2` | bouton rotatif | `controls/fusion/audio[0]/nav2-vol` | NAV2 receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDL.DME1` | bouton rotatif | `controls/fusion/audio[0]/dme1-vol` | DME1 receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDL.DME2` | bouton rotatif | `controls/fusion/audio[0]/dme2-vol` | DME2 receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDL.ADF` | bouton rotatif | `controls/fusion/audio[0]/adf-vol` | ADF receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDL.MKR` | bouton rotatif | `controls/fusion/audio[0]/mkr-vol` | MKR receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDL.PA` | bouton rotatif | `controls/fusion/audio[0]/pa-vol` | PA receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDL.MIC` | interrupteur | `controls/fusion/audio[0]/mic-oxy` | Microphone: … |
| `AUDL.MKRHI` | interrupteur | `controls/fusion/audio[0]/mkr-hi` | Marker beacon sensitivity: … |
| `AUDL.IDENT` | interrupteur | `controls/fusion/audio[0]/filter` | NAV audio filter: … |
| `AUDL.EMER` | interrupteur | `controls/fusion/audio[0]/emer` | Audio EMER: … |
| `AUDL.BARO` | bouton rotatif | `sim/model/fusion/knobs/baro0` | BARO: pilot PFD altimeter setting (push: STD) |

## Panneau audio copilote (`AUDIOR`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `AUDR.XMT` | bouton rotatif | `controls/fusion/audio[1]/xmit` | Transmitter: … |
| `AUDR.VOL` | bouton rotatif | `controls/fusion/audio[1]/master-vol` | Audio master volume: … |
| `AUDR.T` | voyant | voyant `xmit_1` |  |
| `AUDR.COMM1` | bouton rotatif | `controls/fusion/audio[1]/comm1-vol` | COMM1 receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDR.COMM2` | bouton rotatif | `controls/fusion/audio[1]/comm2-vol` | COMM2 receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDR.NAV1` | bouton rotatif | `controls/fusion/audio[1]/nav1-vol` | NAV1 receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDR.NAV2` | bouton rotatif | `controls/fusion/audio[1]/nav2-vol` | NAV2 receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDR.DME1` | bouton rotatif | `controls/fusion/audio[1]/dme1-vol` | DME1 receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDR.DME2` | bouton rotatif | `controls/fusion/audio[1]/dme2-vol` | DME2 receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDR.ADF` | bouton rotatif | `controls/fusion/audio[1]/adf-vol` | ADF receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDR.MKR` | bouton rotatif | `controls/fusion/audio[1]/mkr-vol` | MKR receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDR.PA` | bouton rotatif | `controls/fusion/audio[1]/pa-vol` | PA receiver: click to pull on / push off, wheel for the volume (…) |
| `AUDR.MIC` | interrupteur | `controls/fusion/audio[1]/mic-oxy` | Microphone: … |
| `AUDR.MKRHI` | interrupteur | `controls/fusion/audio[1]/mkr-hi` | Marker beacon sensitivity: … |
| `AUDR.IDENT` | interrupteur | `controls/fusion/audio[1]/filter` | NAV audio filter: … |
| `AUDR.EMER` | interrupteur | `controls/fusion/audio[1]/emer` | Audio EMER: … |
| `AUDR.BARO` | bouton rotatif | `sim/model/fusion/knobs/baro1` | BARO: copilot PFD altimeter setting (push: STD) |

## Bandeau de commande des écrans (`STRIP`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `PSYNC` | poussoir lumineux | voyant `prop_sync` | Propeller synchrophaser: … |
| `DGFREEL` | interrupteur | `controls/fusion/dg-free[0]` | AHRS heading: … |
| `SLEWL` | interrupteur | `controls/fusion/slew[0]` | DG slew (DG FREE only): hold + / - |
| `DGFREER` | interrupteur | `controls/fusion/dg-free[1]` | AHRS heading: … |
| `SLEWR` | interrupteur | `controls/fusion/slew[1]` | DG slew (DG FREE only): hold + / - |
| `REVPFD1` | interrupteur | `controls/fusion/reversion-pfd1` | PFD1 display: … |
| `REVMFD` | interrupteur | `controls/fusion/reversion-mfd` | MFD display: … |
| `REVPFD2` | interrupteur | `controls/fusion/reversion-pfd2` | PFD2 display: … |
| `AHSSRC` | interrupteur | `controls/fusion/ahs-source` | AHS source for the pilot PFD: … |
| `ADSSRC` | interrupteur | `controls/fusion/ads-source` | ADS source for the pilot PFD: … |
| `INHPFD1` | interrupteur | `controls/fusion/inhibit-pfd1` | PFD1: … |
| `INHMFD` | interrupteur | `controls/fusion/inhibit-mfd` | MFD: … |
| `INHPFD2` | interrupteur | `controls/fusion/inhibit-pfd2` | PFD2: … |
| `ALTSTATIC` | interrupteur | `controls/switches/alt-static` | Pilot's static air source: … |
| `EMERFREQ` | poussoir |  | EMER FREQ: COM 1 on 121.500 |

## Sous-panneau pilote (`PSUB`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `MASTER` | interrupteur | `controls/fusion/master-emer` | DC master: … (guarded) |
| `BAT` | interrupteur | `controls/electric/battery-switch` | Battery: … |
| `LGEN` | interrupteur | `controls/fusion/gen[0]` | Left generator: … |
| `RGEN` | interrupteur | `controls/fusion/gen[1]` | Right generator: … |
| `AVMASTER` | interrupteur | `controls/electric/avionics-switch` | Avionics master: … |
| `STBYDSP` | interrupteur | `controls/fusion/stby-display` | Standby display: … |
| `BUSSENSE` | interrupteur | `controls/fusion/bus-sense` | Bus sense: TEST / RESET (hold) |
| `GENTIES` | interrupteur | `controls/fusion/gen-ties` | Generator ties: … |
| `ENGICEL` | interrupteur | `controls/anti-ice/engine[0]/inlet-heat` | Left engine anti-ice: … |
| `ACTL` | interrupteur | `controls/anti-ice/engine[0]/actuator-standby` | Left anti-ice actuator: … |
| `ENGICER` | interrupteur | `controls/anti-ice/engine[1]/inlet-heat` | Right engine anti-ice: … |
| `ACTR` | interrupteur | `controls/anti-ice/engine[1]/actuator-standby` | Right anti-ice actuator: … |
| `STARTL` | interrupteur | `controls/fusion/start[0]` | Left ignition and engine start: … |
| `STARTR` | interrupteur | `controls/fusion/start[1]` | Right ignition and engine start: … |
| `AUTOFTHR` | interrupteur | `controls/fusion/autofeather` | Autofeather: … |
| `PROPTEST` | interrupteur | `controls/engines/prop-overspeed-test` | Propeller overspeed governor test (hold) |
| `AUTOIGNL` | interrupteur | `controls/engines/engine[0]/auto-ignition` | Left auto ignition: … |
| `AUTOIGNR` | interrupteur | `controls/engines/engine[1]/auto-ignition` | Right auto ignition: … |

## Éclairage et antigivrage (`LTS`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `LDGL` | interrupteur | `controls/lighting/landing-lights[0]` | Left light: … |
| `LDGR` | interrupteur | `controls/lighting/landing-lights[1]` | Right light: … |
| `TAXI` | interrupteur | `controls/lighting/taxi-lights` | Taxi light: … |
| `ICEL` | interrupteur | `controls/lighting/ice-light` | Ice light: … |
| `NAVL` | interrupteur | `controls/lighting/nav-lights` | Nav light: … |
| `RECOG` | interrupteur | `controls/lighting/recog-lights` | Recog light: … |
| `WSHLDP` | interrupteur | `controls/fusion/wshld[0]` | Pilot windshield anti-ice: … |
| `WSHLDC` | interrupteur | `controls/fusion/wshld[1]` | Copilot windshield anti-ice: … |
| `PROPAUTO` | interrupteur | `controls/anti-ice/prop-heat` | Propeller deice AUTO: … |
| `PROPMAN` | interrupteur | `controls/anti-ice/prop-heat-manual` | Propeller deice MANUAL (hold) |
| `FVENTL` | interrupteur | `controls/anti-ice/fuel-vent-heat[0]` | Left fuel vent heat: … |
| `FVENTR` | interrupteur | `controls/anti-ice/fuel-vent-heat[1]` | Right fuel vent heat: … |
| `BRKDEICE` | interrupteur | `controls/anti-ice/brake-deice` | Brake deice: … |
| `SURFDEICE` | interrupteur | `controls/fusion/surface-deice` | Surface deice: SINGLE cycle (click) / MANUAL (hold) |
| `STALLHEAT` | interrupteur | `controls/anti-ice/stall-warn-heat` | Stall warning heat: … |
| `PITOTL` | interrupteur | `controls/anti-ice/pitot-heat[0]` | Left pitot heat: … |
| `PITOTR` | interrupteur | `controls/anti-ice/pitot-heat[1]` | Right pitot heat: … |
| `GEARRELAY` | bouton rotatif | `controls/fusion/cb/gear-relay` | Landing gear relay circuit breaker: … |

## Train, feux anticollision (`GEAR`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `DNLOCKREL` | poussoir |  | Down lock release (hold) |
| `HDLTEST` | poussoir |  | Landing gear handle and lights test (hold) |
| `BEACON` | interrupteur | `controls/lighting/beacon/switch` | Beacon: … |
| `STROBE` | interrupteur | `controls/lighting/strobe/switch` | Strobe: … |
| `GNOSE` | voyant | voyant `gear_0` |  |
| `GLEFT` | voyant | voyant `gear_1` |  |
| `GRIGHT` | voyant | voyant `gear_2` |  |
| `TAILFLOOD` | interrupteur | `controls/lighting/logo-lights` | Tail flood lights: … |

## Centre : volets et pressurisation (`CTR`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `FLAPIND` | cadran | `surface-positions/flap-pos-norm` |  |
| `CABCLIMB` | cadran | `systems/pressurization/cabin-rate-fpm` |  |
| `CABALT` | cadran | `systems/pressurization/cabin-altitude-ft, systems/pressurization/diff-psi` |  |

## Conditionnement d'air (`ENV`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `BLOWERCOC` | bouton rotatif | `controls/fusion/env/blower-cockpit` | Cockpit blower: … |
| `TEMPCOC` | bouton rotatif | `controls/fusion/env/temp-cockpit` | Cockpit temperature: … % |
| `BLOWERCAB` | bouton rotatif | `controls/fusion/env/blower-cabin` | Cabin blower: … |
| `TEMPCAB` | bouton rotatif | `controls/fusion/env/temp-cabin` | Cabin temperature: … % |
| `ENVMODE` | bouton rotatif | `controls/fusion/env/mode` | Environmental mode: … |
| `MANTEMP` | interrupteur | `controls/fusion/env/man-temp` | Manual temperature (MAN HEAT / MAN COOL): hold INCR / DECR |
| `ENVBLEED` | interrupteur | `controls/pressurization/envir-low` | Environmental bleed air: … |
| `BLEEDL` | interrupteur | `controls/fusion/bleed[0]` | Left bleed air valve: … |
| `BLEEDR` | interrupteur | `controls/fusion/bleed[1]` | Right bleed air valve: … |

## Sous-panneau copilote (`CSUB`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `WDEFOG` | interrupteur | `controls/fusion/window-defog` | Side window defog: … |
| `CABTEST` | interrupteur | `controls/fusion/cabin-warn-test` | Cabin altitude / differential warning test (hold) |
| `FTESTL` | interrupteur | `controls/fusion/fire-test[0]` | Left engine fire test: DET (up) / EXT (down), hold |
| `FTESTR` | interrupteur | `controls/fusion/fire-test[1]` | Right engine fire test: DET (up) / EXT (down), hold |
| `CABTEMP` | cadran | `systems/environment/cabin-temp-degc` |  |
| `HOURS` | cadran |  |  |
| `OXY` | cadran | `systems/oxygen/pressure-psi` |  |

## Frein de parc (`PBRAKE`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `PBRAKE.HS` | zone cliquable |  | Parking brake: … |

## Trims d'aileron et de direction, freins de manettes (`PED.TRIM`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `ATRIM` | bouton rotatif | `controls/flight/aileron-trim` | Aileron trim: … |
| `RTRIM` | bouton rotatif | `controls/flight/rudder-trim` | Rudder trim: … |
| `FRICPWR` | bouton rotatif | `controls/fusion/friction[0]` | Power lever friction lock: … % |
| `FRICPC` | bouton rotatif | `controls/fusion/friction[1]` | Propeller / condition lever friction lock: … % |

## Boîtier de curseur pilote (`CCPL`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `CCPL.DSPL` | interrupteur | `controls/fusion/ccp[0]/display` | Cursor control: … |
| `CCPL.MENU` | poussoir |  | MENU (selected display) |
| `CCPL.FPL` | poussoir |  | FPL (selected display) |
| `CCPL.PROC` | poussoir |  | PROC (selected display) |
| `CCPL.DTO` | poussoir |  | DIRECT TO (selected display) |
| `CCPL.CLR` | poussoir |  | CLR (selected display) |
| `CCPL.ENT` | poussoir |  | ENT (selected display) |
| `CCPL.RANGE` | bouton rotatif | `sim/model/fusion/knobs/range0` | Map range (push: pan mode) |
| `CCPL.FMS` | molettes concentriques |  | FMS knob: outer = page group / cursor, inner = page / value; push = CRSR |
| `CCPL.NAV` | molettes concentriques |  | NAV standby frequency: outer MHz, inner kHz (push: ident) |
| `CCPL.NAVXFR` | poussoir |  | NAV frequency transfer |
| `CCPL.COM` | molettes concentriques |  | COM standby frequency: outer MHz, inner kHz (push: squelch) |
| `CCPL.COMXFR` | poussoir |  | COM frequency transfer |

## Boîtier de curseur copilote (`CCPR`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `CCPR.DSPL` | interrupteur | `controls/fusion/ccp[1]/display` | Cursor control: … |
| `CCPR.MENU` | poussoir |  | MENU (selected display) |
| `CCPR.FPL` | poussoir |  | FPL (selected display) |
| `CCPR.PROC` | poussoir |  | PROC (selected display) |
| `CCPR.DTO` | poussoir |  | DIRECT TO (selected display) |
| `CCPR.CLR` | poussoir |  | CLR (selected display) |
| `CCPR.ENT` | poussoir |  | ENT (selected display) |
| `CCPR.RANGE` | bouton rotatif | `sim/model/fusion/knobs/range1` | Map range (push: pan mode) |
| `CCPR.FMS` | molettes concentriques |  | FMS knob: outer = page group / cursor, inner = page / value; push = CRSR |
| `CCPR.NAV` | molettes concentriques |  | NAV standby frequency: outer MHz, inner kHz (push: ident) |
| `CCPR.NAVXFR` | poussoir |  | NAV frequency transfer |
| `CCPR.COM` | molettes concentriques |  | COM standby frequency: outer MHz, inner kHz (push: squelch) |
| `CCPR.COMXFR` | poussoir |  | COM frequency transfer |

## Clavier (`MKP`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `MKP.1` | poussoir |  |  |
| `MKP.2` | poussoir |  |  |
| `MKP.3` | poussoir |  |  |
| `MKP.4` | poussoir |  |  |
| `MKP.5` | poussoir |  |  |
| `MKP.6` | poussoir |  |  |
| `MKP.7` | poussoir |  |  |
| `MKP.8` | poussoir |  |  |
| `MKP.9` | poussoir |  |  |
| `MKP.0` | poussoir |  |  |
| `MKP.A` | poussoir |  |  |
| `MKP.B` | poussoir |  |  |
| `MKP.C` | poussoir |  |  |
| `MKP.D` | poussoir |  |  |
| `MKP.E` | poussoir |  |  |
| `MKP.F` | poussoir |  |  |
| `MKP.G` | poussoir |  |  |
| `MKP.H` | poussoir |  |  |
| `MKP.I` | poussoir |  |  |
| `MKP.J` | poussoir |  |  |
| `MKP.K` | poussoir |  |  |
| `MKP.L` | poussoir |  |  |
| `MKP.M` | poussoir |  |  |
| `MKP.N` | poussoir |  |  |
| `MKP.O` | poussoir |  |  |
| `MKP.P` | poussoir |  |  |
| `MKP.Q` | poussoir |  |  |
| `MKP.R` | poussoir |  |  |
| `MKP.S` | poussoir |  |  |
| `MKP.T` | poussoir |  |  |
| `MKP.U` | poussoir |  |  |
| `MKP.V` | poussoir |  |  |
| `MKP.W` | poussoir |  |  |
| `MKP.X` | poussoir |  |  |
| `MKP.Y` | poussoir |  |  |
| `MKP.Z` | poussoir |  |  |
| `MKP.F0` | poussoir |  |  |
| `MKP.F1` | poussoir |  |  |
| `MKP.F2` | poussoir |  |  |
| `MKP.F3` | poussoir |  |  |
| `MKP.CLR` | poussoir |  |  |
| `MKP.ENT` | poussoir |  |  |
| `MKP.PAGE0` | poussoir |  |  |
| `MKP.PAGE1` | poussoir |  |  |
| `MKP.CRSR` | poussoir |  |  |

## Pressurisation et essais (`PRESS`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `CABALTSEL` | bouton rotatif | `controls/pressurization/cabin-alt-ft` | Cabin altitude selector: … ft |
| `CABRATE` | bouton rotatif | `controls/pressurization/rate-fpm` | Cabin rate of change: … ft/min |
| `CABPRESS` | interrupteur | `controls/fusion/cabin-press` | Cabin pressure: … |
| `RUDBOOST` | interrupteur | `controls/flight/rudder-boost` | Rudder boost: … |
| `ELECTRIM` | interrupteur | `controls/fusion/elec-trim` | Electric elevator trim (control wheel switches): … |
| `STALLTEST` | interrupteur | `controls/fusion/stall-test` | Stall warning test (hold) |
| `GEARWARN` | interrupteur | `controls/fusion/gear-warn-test` | Landing gear warning horn test (hold) |

## Enregistreur de conversations (`CVR`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `CVR.TEST` | poussoir |  | CVR test (hold: the green light shows) |
| `CVR.LAMP` | voyant | voyant `cvr_ok` |  |
| `CVR.ERASE` | poussoir |  | CVR erase (on the ground, parking brake set) |

## Plafonnier (`OVH`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `MSTRPANEL` | interrupteur | `controls/lighting/master-panel` | Master panel lights: … |
| `OVH.PANELLTS` | bouton rotatif | `controls/lighting/instruments-norm` | Panel back lighting: … % |
| `OVH.DSPL1` | bouton rotatif | `sim/model/fusion/display-brightness[0]` | Pilot PFD and standby brightness: … % |
| `OVH.DSPL2` | bouton rotatif | `sim/model/fusion/display-brightness[1]` | MFD brightness: … % |
| `OVH.DSPL3` | bouton rotatif | `sim/model/fusion/display-brightness[2]` | Copilot PFD brightness: … % |
| `OVH.FLOODP` | bouton rotatif | `sim/model/fusion/flood[0]` | Instrument panel flood lights: … % |
| `OVH.FLOODD` | bouton rotatif | `sim/model/fusion/flood[1]` | Pedestal flood lights: … % |
| `OVH.FLOODO` | bouton rotatif | `sim/model/fusion/flood[2]` | Overhead and side panel flood lights: … % |
| `ANNDIM` | interrupteur | `controls/fusion/annun-dim` | Annunciators: … |
| `OVH.WIPER` | bouton rotatif | `controls/electric/wipers/switch-pos` | Windshield wiper: … |
| `SIGNS` | interrupteur | `controls/fusion/cabin-signs` | Cabin signs: … |
| `CABLIGHTS` | interrupteur | `controls/fusion/cabin-lights` | Cabin lights: … |

## Instruments du plafonnier (`OVHG`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `OVHG.DCLOADL` | cadran | `systems/electrical/gen-load[0]` |  |
| `OVHG.DCLOADR` | cadran | `systems/electrical/gen-load[1]` |  |
| `OVHG.BATTAMP` | cadran | `systems/electrical/ammeter` |  |
| `OVHG.VOLTS` | cadran | `systems/electrical/volts` |  |
| `OVHG.PROPAMP` | cadran | `systems/anti-ice/prop-deice-amps` |  |
| `OVHG.OAT` | cadran | `environment/temperature-degc` |  |

## Panneau carburant (`FUEL`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `FQTYL` | cadran | `sim/model/fusion/fuel-qty-ind[0]` |  |
| `FQTYR` | cadran | `sim/model/fusion/fuel-qty-ind[1]` |  |
| `XFEED` | interrupteur | `controls/fusion/crossfeed` | Fuel crossfeed: … |
| `FQSEL` | interrupteur | `controls/fusion/fuel-qty-select` | Fuel quantity gauges: … |
| `STBYPUMPL` | interrupteur | `controls/fusion/stby-pump[0]` | Left standby fuel pump: … |
| `AUXXFERL` | interrupteur | `controls/fusion/aux-xfer[0]` | Left aux transfer: … |
| `STBYPUMPR` | interrupteur | `controls/fusion/stby-pump[1]` | Right standby fuel pump: … |
| `AUXXFERR` | interrupteur | `controls/fusion/aux-xfer[1]` | Right aux transfer: … |

## Disjoncteurs, paroi gauche (`CBL`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `CB.stby-pump0` | bouton rotatif | `controls/fusion/cb/stby-pump[0]` | Circuit breaker STBY PUMP LEFT (10 A): … |
| `CB.stby-pump1` | bouton rotatif | `controls/fusion/cb/stby-pump[1]` | Circuit breaker STBY PUMP RIGHT (10 A): … |
| `CB.aux-xfer0` | bouton rotatif | `controls/fusion/cb/aux-xfer[0]` | Circuit breaker AUX XFER LEFT (5 A): … |
| `CB.aux-xfer1` | bouton rotatif | `controls/fusion/cb/aux-xfer[1]` | Circuit breaker AUX XFER RIGHT (5 A): … |
| `CB.crossfeed` | bouton rotatif | `controls/fusion/cb/crossfeed` | Circuit breaker CROSS FEED (5 A): … |
| `CB.fuel-qty-main` | bouton rotatif | `controls/fusion/cb/fuel-qty-main` | Circuit breaker QTY IND MAIN (5 A): … |
| `CB.fuel-qty-aux` | bouton rotatif | `controls/fusion/cb/fuel-qty-aux` | Circuit breaker QTY IND AUX (5 A): … |
| `CB.fw-valve0` | bouton rotatif | `controls/fusion/cb/fw-valve[0]` | Circuit breaker F/W VALVE LEFT (5 A): … |
| `CB.fw-valve1` | bouton rotatif | `controls/fusion/cb/fw-valve[1]` | Circuit breaker F/W VALVE RIGHT (5 A): … |
| `CB.fuel-press-warn` | bouton rotatif | `controls/fusion/cb/fuel-press-warn` | Circuit breaker FUEL PRESS WARN (5 A): … |
| `CB.start0` | bouton rotatif | `controls/fusion/cb/start[0]` | Circuit breaker IGN START LEFT (5 A): … |
| `CB.start1` | bouton rotatif | `controls/fusion/cb/start[1]` | Circuit breaker IGN START RIGHT (5 A): … |
| `CB.auto-ign0` | bouton rotatif | `controls/fusion/cb/auto-ign[0]` | Circuit breaker AUTO IGN LEFT (5 A): … |
| `CB.auto-ign1` | bouton rotatif | `controls/fusion/cb/auto-ign[1]` | Circuit breaker AUTO IGN RIGHT (5 A): … |
| `CB.autofeather` | bouton rotatif | `controls/fusion/cb/autofeather` | Circuit breaker AUTO FEATHER (5 A): … |
| `CB.prop-sync` | bouton rotatif | `controls/fusion/cb/prop-sync` | Circuit breaker PROP SYNC (5 A): … |
| `CB.prop-gov-test` | bouton rotatif | `controls/fusion/cb/prop-gov-test` | Circuit breaker PROP GOV TEST (5 A): … |
| `CB.eng-ice0` | bouton rotatif | `controls/fusion/cb/eng-ice[0]` | Circuit breaker ENG ANTI ICE LEFT (5 A): … |
| `CB.eng-ice1` | bouton rotatif | `controls/fusion/cb/eng-ice[1]` | Circuit breaker ENG ANTI ICE RIGHT (5 A): … |
| `CB.fire-det` | bouton rotatif | `controls/fusion/cb/fire-det` | Circuit breaker FIRE DETECT (5 A): … |
| `CB.landing-lights0` | bouton rotatif | `controls/fusion/cb/landing-lights[0]` | Circuit breaker LANDING LEFT (15 A): … |
| `CB.landing-lights1` | bouton rotatif | `controls/fusion/cb/landing-lights[1]` | Circuit breaker LANDING RIGHT (15 A): … |
| `CB.taxi-lights` | bouton rotatif | `controls/fusion/cb/taxi-lights` | Circuit breaker TAXI (10 A): … |
| `CB.nav-lights` | bouton rotatif | `controls/fusion/cb/nav-lights` | Circuit breaker NAV (5 A): … |
| `CB.beacon` | bouton rotatif | `controls/fusion/cb/beacon` | Circuit breaker BEACON (5 A): … |
| `CB.strobe` | bouton rotatif | `controls/fusion/cb/strobe` | Circuit breaker STROBE (10 A): … |
| `CB.recog-lights` | bouton rotatif | `controls/fusion/cb/recog-lights` | Circuit breaker RECOG (10 A): … |
| `CB.ice-light` | bouton rotatif | `controls/fusion/cb/ice-light` | Circuit breaker ICE (5 A): … |
| `CB.logo-lights` | bouton rotatif | `controls/fusion/cb/logo-lights` | Circuit breaker TAIL FLOOD (5 A): … |
| `CB.cabin-lights` | bouton rotatif | `controls/fusion/cb/cabin-lights` | Circuit breaker CABIN (10 A): … |
| `CB.instrument-lights` | bouton rotatif | `controls/fusion/cb/instrument-lights` | Circuit breaker PANEL LIGHTS (5 A): … |
| `CB.flood` | bouton rotatif | `controls/fusion/cb/flood` | Circuit breaker FLOOD LIGHTS (5 A): … |
| `CB.wipers` | bouton rotatif | `controls/fusion/cb/wipers` | Circuit breaker WSHLD WIPER (10 A): … |
| `CB.hobbs` | bouton rotatif | `controls/fusion/cb/hobbs` | Circuit breaker HOUR METER (2 A): … |
| `CB.cvr` | bouton rotatif | `controls/fusion/cb/cvr` | Circuit breaker CVR (5 A): … |
| `CB.annunciators` | bouton rotatif | `controls/fusion/cb/annunciators` | Circuit breaker ANNUN POWER (5 A): … |
| `CB.gear-warn` | bouton rotatif | `controls/fusion/cb/gear-warn` | Circuit breaker GEAR WARN (5 A): … |
| `CB.stall-warn` | bouton rotatif | `controls/fusion/cb/stall-warn` | Circuit breaker STALL WARN (5 A): … |
| `CB.oxygen` | bouton rotatif | `controls/fusion/cb/oxygen` | Circuit breaker OXYGEN IND (2 A): … |
| `CB.cabin-signs` | bouton rotatif | `controls/fusion/cb/cabin-signs` | Circuit breaker CABIN SIGNS (5 A): … |

## Disjoncteurs, paroi droite (`CBR`)

| Commande | Type | Propriété | Info |
|---|---|---|---|
| `CB.fg1000-pfd` | bouton rotatif | `controls/fusion/cb/fg1000-pfd` | Circuit breaker PFD 1 (7 A): … |
| `CB.fg1000-mfd` | bouton rotatif | `controls/fusion/cb/fg1000-mfd` | Circuit breaker MFD (7 A): … |
| `CB.fg1000-pfd2` | bouton rotatif | `controls/fusion/cb/fg1000-pfd2` | Circuit breaker PFD 2 (7 A): … |
| `CB.stby-display` | bouton rotatif | `controls/fusion/cb/stby-display` | Circuit breaker STBY DSPL (5 A): … |
| `CB.comm` | bouton rotatif | `controls/fusion/cb/comm` | Circuit breaker COM 1 (5 A): … |
| `CB.comm1` | bouton rotatif | `controls/fusion/cb/comm[1]` | Circuit breaker COM 2 (5 A): … |
| `CB.nav` | bouton rotatif | `controls/fusion/cb/nav` | Circuit breaker NAV 1 (3 A): … |
| `CB.nav1` | bouton rotatif | `controls/fusion/cb/nav[1]` | Circuit breaker NAV 2 (3 A): … |
| `CB.dme` | bouton rotatif | `controls/fusion/cb/dme` | Circuit breaker DME (3 A): … |
| `CB.adf` | bouton rotatif | `controls/fusion/cb/adf` | Circuit breaker ADF (3 A): … |
| `CB.transponder` | bouton rotatif | `controls/fusion/cb/transponder` | Circuit breaker XPDR (3 A): … |
| `CB.audio-panel` | bouton rotatif | `controls/fusion/cb/audio-panel` | Circuit breaker AUDIO 1 (5 A): … |
| `CB.audio-panel1` | bouton rotatif | `controls/fusion/cb/audio-panel[1]` | Circuit breaker AUDIO 2 (5 A): … |
| `CB.gps` | bouton rotatif | `controls/fusion/cb/gps` | Circuit breaker FMS GPS (5 A): … |
| `CB.fgc-65` | bouton rotatif | `controls/fusion/cb/fgc-65` | Circuit breaker FLT GUID PANEL (5 A): … |
| `CB.autopilot` | bouton rotatif | `controls/fusion/cb/autopilot` | Circuit breaker AP SERVOS (5 A): … |
| `CB.mk-viii` | bouton rotatif | `controls/fusion/cb/mk-viii` | Circuit breaker TAWS (3 A): … |
| `CB.turn-coordinator` | bouton rotatif | `controls/fusion/cb/turn-coordinator` | Circuit breaker AHRS (5 A): … |
| `CB.ccp` | bouton rotatif | `controls/fusion/cb/ccp` | Circuit breaker CCP MKP (3 A): … |
| `CB.avionics` | bouton rotatif | `controls/fusion/cb/avionics` | Circuit breaker AVIONICS MASTER (5 A): … |
| `CB.ext-power` | bouton rotatif | `controls/fusion/cb/ext-power` | Circuit breaker EXT PWR (5 A): … |
| `CB.gen0` | bouton rotatif | `controls/fusion/cb/gen[0]` | Circuit breaker GEN CONT LEFT (5 A): … |
| `CB.gen1` | bouton rotatif | `controls/fusion/cb/gen[1]` | Circuit breaker GEN CONT RIGHT (5 A): … |
| `CB.flap-motor` | bouton rotatif | `controls/fusion/cb/flap-motor` | Circuit breaker FLAP MOTOR (20 A): … |
| `CB.flap-control` | bouton rotatif | `controls/fusion/cb/flap-control` | Circuit breaker FLAP CONTROL (5 A): … |
| `CB.gear-control` | bouton rotatif | `controls/fusion/cb/gear-control` | Circuit breaker GEAR CONTROL (5 A): … |
| `CB.elec-trim` | bouton rotatif | `controls/fusion/cb/elec-trim` | Circuit breaker PITCH TRIM (5 A): … |
| `CB.rudder-boost` | bouton rotatif | `controls/fusion/cb/rudder-boost` | Circuit breaker RUDDER BOOST (5 A): … |
| `CB.yaw-damper` | bouton rotatif | `controls/fusion/cb/yaw-damper` | Circuit breaker YAW DAMP (5 A): … |
| `CB.press-control` | bouton rotatif | `controls/fusion/cb/press-control` | Circuit breaker PRESS CONTROL (5 A): … |
| `CB.temp-control` | bouton rotatif | `controls/fusion/cb/temp-control` | Circuit breaker TEMP CONTROL (5 A): … |
| `CB.blower0` | bouton rotatif | `controls/fusion/cb/blower[0]` | Circuit breaker BLOWER CKPT (15 A): … |
| `CB.blower1` | bouton rotatif | `controls/fusion/cb/blower[1]` | Circuit breaker BLOWER CABIN (20 A): … |
| `CB.window-heat0` | bouton rotatif | `controls/fusion/cb/window-heat[0]` | Circuit breaker WSHLD PILOT (25 A): … |
| `CB.window-heat1` | bouton rotatif | `controls/fusion/cb/window-heat[1]` | Circuit breaker WSHLD COPILOT (25 A): … |
| `CB.pitot-heat0` | bouton rotatif | `controls/fusion/cb/pitot-heat[0]` | Circuit breaker PITOT LEFT (7 A): … |
| `CB.pitot-heat1` | bouton rotatif | `controls/fusion/cb/pitot-heat[1]` | Circuit breaker PITOT RIGHT (7 A): … |
| `CB.stall-warn-heat` | bouton rotatif | `controls/fusion/cb/stall-warn-heat` | Circuit breaker STALL HEAT (7 A): … |
| `CB.prop-heat` | bouton rotatif | `controls/fusion/cb/prop-heat` | Circuit breaker PROP DEICE (25 A): … |
| `CB.surface-deice` | bouton rotatif | `controls/fusion/cb/surface-deice` | Circuit breaker SURF DEICE (5 A): … |
| `CB.fuel-vent-heat0` | bouton rotatif | `controls/fusion/cb/fuel-vent-heat[0]` | Circuit breaker FUEL VENT LEFT (5 A): … |
| `CB.fuel-vent-heat1` | bouton rotatif | `controls/fusion/cb/fuel-vent-heat[1]` | Circuit breaker FUEL VENT RIGHT (5 A): … |
| `CB.brake-deice` | bouton rotatif | `controls/fusion/cb/brake-deice` | Circuit breaker BRAKE DEICE (10 A): … |
| `CB.window-defog` | bouton rotatif | `controls/fusion/cb/window-defog` | Circuit breaker WINDOW DEFOG (7 A): … |
| `CB.bleed0` | bouton rotatif | `controls/fusion/cb/bleed[0]` | Circuit breaker BLEED VLV LEFT (5 A): … |
| `CB.bleed1` | bouton rotatif | `controls/fusion/cb/bleed[1]` | Circuit breaker BLEED VLV RIGHT (5 A): … |
| `CB.elec-heat` | bouton rotatif | `controls/fusion/cb/elec-heat` | Circuit breaker ELEC HEAT (5 A): … |
