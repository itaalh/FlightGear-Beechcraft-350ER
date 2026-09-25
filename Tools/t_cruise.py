from sim2 import *
import sys
def cruise(alt,W,thr=1.0,v0=200,isa_dev=0.0,T=700,rpm=1.0):
    # set weight via payload+fuel: pilot 190 + pax such that W matches with fuel 60%
    fuel_tot=3611*0.55; pax=max(0,W-9650-190-fuel_tot-100)
    f=mk(alt,v0,0,0,thr=thr,fuel=[266*0.55,1273*0.55,1273*0.55,266*0.55],payload=[190,0,pax,100])
    if isa_dev: f['atmosphere/delta-T']=isa_dev*1.8
    for i in (0,1): f[f'fcs/advance-cmd-norm[{i}]']=rpm
    c=Hold(f,alt,thr=thr); settle(f,c,T)
    return rep(f)
print("== Croisière plein gaz (ISA), palier tenu, poids/altitude : cible POH")
for alt,W,note in [(24000,12500,"312 KTAS max cruise FL240"),(26000,13000,"310 KTAS 1500rpm spec"),(28000,14400,"295 KTAS (ISA+3) AOPA stock"),(35000,13000,"267 KTAS FL350 stock"),(10000,14000,""),(5000,14500,"")]:
    r=cruise(alt,W,1.0,rpm=0.2 if alt==26000 else 1.0)
    print(f"FL{alt//100:03d} W{r['W']:5.0f} : {r['KTAS']:5.1f} KTAS {r['KCAS']:5.1f} KCAS  FF {r['FF']:4.0f} pph  {r['HP']:4.0f} hp/eng  N1 {r['N1']:5.1f} tq {r['tq']:3.0f}% ITT {r['itt']:3.0f} Np {r['prpm']:4.0f} β{r['blade']:4.1f}  α{r['alpha']:4.1f} δe{r['elev']:5.1f}   <- {note}")
print("== Long range cruise FL330 (237 KTAS, 12000 lb) : chercher la manette")
for thr in [0.45,0.55,0.65]:
    r=cruise(33000,12000,thr)
    print(f"thr {thr}: {r['KTAS']:5.1f} KTAS FF {r['FF']:4.0f} pph {r['HP']:4.0f} hp N1 {r['N1']:5.1f}")
