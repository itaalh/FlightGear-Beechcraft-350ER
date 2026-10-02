"""Bake model-space maps in texture space: for every texel of the body texture, the position (m), face normal
and object it belongs to. Everything else (decals, panel lines) is painted from these maps."""
import os, numpy as np
from acparse import parse_ac, triangulate
from raster import bake_uv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))          # aircraft directory (KingAir-350)
MODELS = os.path.join(ROOT, 'Models')

# objects textured with the livery (Models/KingAir.xml, animation "bodyWork") + the window plug
BODYWORK = """AileronsLeft AileronsRigth AiltrimtabLeft AiltrimtabsRight AxleshaftsFront AxleshaftsLeft AxleshaftsRight
DeicebootsHorizStab DeicebootsWings ElevatorsLeft ElevatorsRight EngCowlStrips Exhaust
FlapsLeft FlapsRight FlapstripsLeft FlapstripsRight FrontCargoDoorLeft FrontCargoDoorRight FrontCargoDoorStripsLeft
FrontCargoDoorStripsRight FrontCowls FrontEngineCowls FuelCaps Fuselage GearDoorFront.Open1 GearDoorFront.Open2
GearDoorLeft.Open1 GearDoorLeft.Open2 GearDoorRight.Open1 GearDoorRight.Open2 GearsDoorFront.Closed GearsDoorLeft.Closed
GearsDoorRight.Closed Horstab LGPistonFront LGPistonLeft LGPistonRight LowerEngCowls LowerStabFin MainEntrance
MainEntranceTrim MidEngineCowls NoseCone NoseConeStrips NoseVents PropCone PropConeLeft PropConeRight PropConeDisks
PropLeft PropRight Rudder RudHingPoints TailLight TailTop TopEngineCowl TorqueLinkBoltsFront TorqueLinkBoltsLeft
TorqueLinkBoltsRight TorqueLinksFront TorqueLinksLeft TorqueLinksRight TrunnionFront TrunnionLeft TrunnionRight
VertStab WheelsFront WheelsLeft WheelsRight WingLightsLeft Winglets WingLightsRight Wings WngCowl
TiresFront TiresLeft TiresRight TorqueLinksLeft2 TorqueLinksLeft3 TorqueLinksRight2 WindowPlugL1""".split()


def face_normals(P):
    n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)


def load_model(ac=None):
    objs, _ = parse_ac(ac or os.path.join(MODELS, 'KingAir.ac'))
    data = {}
    for o in objs:
        P, UV = triangulate(o)
        if len(P):
            data[o['name']] = (P, UV, o['texture'])
    return data


class Maps:
    def __init__(self, data, size=4096, names=BODYWORK):
        S = size
        pos = np.zeros((S, S, 3)); nrm = np.zeros((S, S, 3))
        obj = -np.ones((S, S), np.int32); cnt = np.zeros((S, S), np.int32)
        for oi, n in enumerate(names):
            if n not in data:
                continue
            P, UV, _ = data[n]
            uvpx = np.stack([UV[..., 0] * S, (1 - UV[..., 1]) * S], -1)
            bake_uv(uvpx.astype(np.float64), P.astype(np.float64), face_normals(P),
                    np.full(len(P), oi, np.int32), S, S, pos, nrm, obj, cnt)
        self.pos = pos.astype(np.float32); self.nrm = nrm.astype(np.float32); self.obj = obj.astype(np.int16)
        self.names = list(names); self.S = S; self.data = data
        self.idx = {n: i for i, n in enumerate(self.names)}

    def objmask(self, names):
        return np.isin(self.obj, [self.idx[n] for n in names if n in self.idx])
