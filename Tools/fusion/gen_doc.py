"""Writes Docs/Fusion-controls.md: every control of the Pro Line Fusion cockpit, panel by panel, with its property
and its tooltip (from cockpit_spec.py)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cockpit_spec as SPEC                    # noqa: E402
from spec_base import Button, DualKnob, Gauge, Hotspot, Knob, Lamp, PushLight, Toggle, Decor   # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, "..", ".."))

PANEL_TITLES = {
    "GS.masterL": "Auvent : MASTER WARNING / CAUTION pilote", "GS.masterR": "Auvent : MASTER WARNING / CAUTION copilote",
    "GS.fireL": "Auvent : incendie moteur gauche", "GS.fireR": "Auvent : incendie moteur droit",
    "GS.marker": "Auvent : balises et TAWS", "GS.radiocall": "Auvent : RADIO CALL",
    "FGP": "Panneau de pilote automatique (FGP)", "STBY": "Écran de secours",
    "AUDIOL": "Panneau audio pilote", "AUDIOR": "Panneau audio copilote", "STRIP": "Bandeau de commande des écrans",
    "PSUB": "Sous-panneau pilote", "LTS": "Éclairage et antigivrage", "GEAR": "Train, feux anticollision",
    "CTR": "Centre : volets et pressurisation", "ENV": "Conditionnement d'air", "CSUB": "Sous-panneau copilote",
    "PBRAKE": "Frein de parc", "PED.QUAD": "Quadrant (dessin)", "PED.ETRIM": "Indicateur de trim de profondeur",
    "PED.TRIM": "Trims d'aileron et de direction, freins de manettes", "CCPL": "Boîtier de curseur pilote",
    "CCPR": "Boîtier de curseur copilote", "MKP": "Clavier", "PRESS": "Pressurisation et essais",
    "CVR": "Enregistreur de conversations", "PED.BLANK": "Plaque", "OVH": "Plafonnier", "OVHG": "Instruments du plafonnier",
    "FUEL": "Panneau carburant", "CBL": "Disjoncteurs, paroi gauche", "CBR": "Disjoncteurs, paroi droite",
}

KIND = {Toggle: "interrupteur", Knob: "bouton rotatif", DualKnob: "molettes concentriques", Button: "poussoir",
        PushLight: "poussoir lumineux", Lamp: "voyant", Gauge: "cadran", Hotspot: "zone cliquable", Decor: "décor"}


def main():
    out = ["# Cockpit Pro Line Fusion — référence des commandes",
           "",
           "Généré par `Tools/fusion/gen_doc.py` à partir de `Tools/fusion/cockpit_spec.py` (ne pas modifier à la main).",
           "La colonne *Info* reprend la bulle d'aide affichée dans FlightGear au survol de la commande.",
           "Les volants, manettes, levier de volets, roue de trim et le compas sont décrits dans `Docs/Fusion-cockpit.md`.",
           ""]
    for p in SPEC.PANELS:
        ctrls = [c for c in p.controls if not isinstance(c, Decor)]
        if not ctrls:
            continue
        out.append("## %s (`%s`)" % (PANEL_TITLES.get(p.name, p.name), p.name))
        out.append("")
        out.append("| Commande | Type | Propriété | Info |")
        out.append("|---|---|---|---|")
        for c in ctrls:
            prop = getattr(c, "prop", "") or ""
            if isinstance(c, Gauge):
                prop = ", ".join(n[0] for n in c.needles)
            if isinstance(c, (Lamp, PushLight, Button)) and getattr(c, "lamp", None):
                prop = (prop + " " if prop else "") + "voyant `%s`" % c.lamp
            info = (c.tooltip or {}).get("label", "") if c.tooltip else ""
            info = info.replace("%s", "…").replace("%d", "…").replace("%.0f", "…").replace("%.2f", "…").replace("%03d", "…")
            info = info.replace("%%", "%").replace("|", "/")
            out.append("| `%s` | %s | %s | %s |" % (c.name, KIND.get(type(c), type(c).__name__),
                                                   ("`%s`" % prop) if prop and not prop.startswith("voyant") else prop,
                                                   info))
        out.append("")
    path = os.path.join(REPO, "Docs", "Fusion-controls.md")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    print("wrote", path)


if __name__ == "__main__":
    main()
