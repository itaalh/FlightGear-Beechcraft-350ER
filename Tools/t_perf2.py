from sim2 import *
def loadW(W,fuelfrac=0.5):
    fuel_tot=3611*fuelfrac; pax=max(0,W-9650-190-fuel_tot-100)
    return dict(fuel=[266*fuelfrac,1273*fuelfrac,1273*fuelfrac,266*fuelfrac],payload=[190,0,pax,100])
def stall_ramp(fl,g,W=15000,alt=3000):
    v0=125 if fl==0 else 110
    f=mk(alt,v0,fl,g,thr=0.3,**loadW(W,0.9)); c=Hold(f,alt,v=v0); dt=f['simulation/dt']
    settle(f,c,30); rec=None
    for k in range(int(120/dt)):
        c.v=max(60,v0-0.7*k*dt); c.step()
        a=f['aero/alpha-deg']; h=f['position/h-sl-ft']
        if h<alt-80 or (a>16.5 and f['velocities/h-dot-fps']<-3):
            rec=(f['velocities/vc-kts'],a,f['fcs/elevator-cmd-norm'],f['aero/cl-squared']**0.5,f['fcs/throttle-cmd-norm[0]']); break
    return rec
def can_hold(v,fl,g,W=15000,alt=3000,T=70):
    f=mk(alt,v,fl,g,thr=0.3,**loadW(W,0.9)); c=Hold(f,alt,v=v); dt=f['simulation/dt']
    for k in range(int(T/dt)):
        c.step()
        if k*dt>25 and (abs(f['position/h-sl-ft']-alt)>60 or f['aero/alpha-deg']>19): return False,f
    return abs(f['position/h-sl-ft']-alt)<60 and abs(f['velocities/vc-kts']-v)<3, f
print("== Vitesse minimale de palier stabilisé (quasi-statique), 15000 lb, 3000 ft")
for fl,g,name in [(0,0,"lisse"),(0.5,1,"volets 14 + train"),(1,1,"volets 35 + train")]:
    rec=stall_ramp(fl,g)
    print(f" {name:22s}: Vs ≈ {rec[0]:5.1f} KCAS (α {rec[1]:4.1f}°, δe {rec[2]:5.2f}, CL {rec[3]:4.2f}, thr {rec[4]:.2f})")
print("== Montée plein gaz, 140 KIAS (Vy), 15000 lb, ISA (vitesse tenue au tangage)")
for alt in [0,10000,20000,30000]:
    f=mk(alt+50,140,0,0,thr=1.0,**loadW(15000,0.9)); c=Hold(f,alt,thr=1.0,vpitch=140); settle(f,c,90)
    print(f" {alt:5d} ft: ROC {f['velocities/h-dot-fps']*60:5.0f} fpm à {f['velocities/vc-kts']:5.1f} KCAS, θ {f['attitude/theta-deg']:4.1f}°, {f['propulsion/engine/power-hp']:4.0f} hp/eng, FF {f['propulsion/engine/fuel-flow-rate-pps']*7200:4.0f} pph")
print("== Montée monomoteur (droit en drapeau), 125 KIAS, 15000 lb, plein gaz gauche, β≈0, 3° d'inclinaison côté moteur vif")
for alt in [0,5000,10000,15000,21000]:
    f=mk(alt+50,125,0,0,thr=1.0,**loadW(15000,0.9)); c=Hold(f,alt,thr=1.0,vpitch=125,phi=-3,beta_hold=True)
    f['fcs/advance-cmd-norm[1]']=0.0; f['propulsion/active_engine']=1; f['propulsion/cutoff_cmd']=1; f['propulsion/active_engine']=-1
    for k in range(int(120/f['simulation/dt'])):
        c.step(); f['fcs/throttle-cmd-norm[1]']=0
    print(f" {alt:5d} ft: ROC {f['velocities/h-dot-fps']*60:5.0f} fpm à {f['velocities/vc-kts']:5.1f} KCAS, palonnier pilote {f['fcs/rudder-cmd-norm']:+.2f} + boost {f['fcs/rudder-boost-lag']:+.2f} = {f['fcs/rudder-pos-rad']*R2D:+.1f}°, β {f['aero/beta-deg']:+.1f}°, hélice D {f['propulsion/engine[1]/propeller-rpm']:4.0f} rpm, feather {f['fcs/feather-pos-norm[1]']:.0f}, {f['propulsion/engine/power-hp']:4.0f} hp")
