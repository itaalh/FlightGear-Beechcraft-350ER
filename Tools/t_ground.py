from sim2 import *
def loadW(W,fuelfrac=0.5):
    fuel_tot=3611*fuelfrac; pax=max(0,W-9650-190-fuel_tot-100)
    return dict(fuel=[266*fuelfrac,1273*fuelfrac,1273*fuelfrac,266*fuelfrac],payload=[190,0,pax,100])
def onground(W=15000,flap=0,fuelfrac=0.9):
    f=jsbsim.FGFDMExec('.',None); f.set_debug_level(0); f.load_model('KingAir-350')
    l=loadW(W,fuelfrac)
    for i,w in enumerate(l['payload']): f[f'inertia/pointmass-weight-lbs[{i}]']=w
    for i,w in enumerate(l['fuel']): f[f'propulsion/tank[{i}]/contents-lbs']=w
    f['ic/h-agl-ft']=6.5; f['ic/vc-kts']=0; f['ic/psi-true-deg']=0; f['ic/lat-geod-deg']=45; f['ic/long-gc-deg']=0; f['ic/terrain-elevation-ft']=0
    f['gear/gear-cmd-norm']=1; f['fcs/flap-cmd-norm']=flap
    f['/controls/engines/engine[0]/condition']=0.5; f['/controls/engines/engine[1]/condition']=0.5
    for i in (0,1): f[f'fcs/throttle-cmd-norm[{i}]']=0; f[f'fcs/advance-cmd-norm[{i}]']=1.0
    f.run_ic(); f['propulsion/set-running']=-1; f['fcs/left-brake-cmd-norm']=1; f['fcs/right-brake-cmd-norm']=1
    f['gear/gear-pos-norm']=1; f['fcs/flap-pos-deg']={0:0,0.5:14,1:35}[flap]
    dt=f['simulation/dt']
    for k in range(int(60/dt)): f.run()   # settle on gear, engines idle
    return f
print("== Sol : ralenti")
f=onground(); print(f" repos: h_agl {f['position/h-agl-ft']:.2f} ft, θ {f['attitude/theta-deg']:5.2f}°, N1 {f['propulsion/engine/n1']:.0f}%, hélice {f['propulsion/engine/propeller-rpm']:.0f} rpm, pas {f['propulsion/engine/blade-angle']:.1f}°, poussée {2*f['propulsion/engine/thrust-lbs']:.0f} lb, couple {f['propulsion/engine[0]/torque-pct']:.0f}%, FF {f['propulsion/engine/fuel-flow-rate-pps']*7200:.0f} pph, compression nez {f['gear/unit[0]/compression-ft']:.2f} ft, main {f['gear/unit[1]/compression-ft']:.2f} ft")
f['/controls/engines/engine[0]/condition']=1.0; f['/controls/engines/engine[1]/condition']=1.0
for k in range(int(10/f['simulation/dt'])): f.run()
print(f" high idle: N1 {f['propulsion/engine/n1']:.0f}%, hélice {f['propulsion/engine/propeller-rpm']:.0f} rpm, couple {f['propulsion/engine[0]/torque-pct']:.0f}%, FF {f['propulsion/engine/fuel-flow-rate-pps']*7200:.0f} pph")
print("== Décollage 15000 lb, volets 0, ISA, niveau de la mer, rotation à 104 kt")
for flap,vr in [(0,104),(0.5,98)]:
    f=onground(15000,flap); dt=f['simulation/dt']
    f['fcs/left-brake-cmd-norm']=0; f['fcs/right-brake-cmd-norm']=0
    for i in (0,1): f[f'fcs/throttle-cmd-norm[{i}]']=1.0
    x0=f['position/distance-from-start-mag-mt']; t=0; lift=None; d50=None; vlof=None; groundroll=None; ie=0
    while t<60:
        v=f['velocities/vc-kts']; agl=f['position/h-agl-ft']-6.5
        wow=f['gear/unit[1]/WOW']
        if v<vr: f['fcs/elevator-cmd-norm']=0.0
        else:
            # rotate to ~10 deg pitch, then hold V2+ ~ 120 kt
            th=f['attitude/theta-deg']; q=f['velocities/q-rad_sec']*R2D
            tgt=10 if agl<50 else 12
            f['fcs/elevator-cmd-norm']=max(-1,min(1,-0.08*(tgt-th)+0.04*q))
        phi=f['attitude/phi-deg']; f['fcs/aileron-cmd-norm']=max(-1,min(1,0.05*(-phi)-0.02*f['velocities/p-rad_sec']*R2D))
        b=f['aero/beta-deg']; r=f['velocities/r-rad_sec']*R2D; psi=f['attitude/psi-deg']; psi=psi-360 if psi>180 else psi
        f['fcs/rudder-cmd-norm']=max(-1,min(1, 0.05*psi + 0.1*r))
        f.run(); t+=dt
        if wow==0 and lift is None: lift=t; vlof=v; groundroll=(f['position/distance-from-start-mag-mt']-x0)*3.281
        if agl>50 and d50 is None: d50=(f['position/distance-from-start-mag-mt']-x0)*3.281; v50=v; break
    print(f" volets {'0' if flap==0 else '14'}: roulage {groundroll:5.0f} ft, Vlof {vlof:5.1f} kt, passage 50 ft à {d50:5.0f} ft / {v50:5.1f} kt, t={t:4.1f} s  (POH: 3300 ft sur 50 ft)")
print("== Atterrissage 15000 lb, volets 35, Vref 105 kt, ralenti au toucher, freins + reverse")
f=mk(60,105,1,1,thr=0.25,**loadW(15000,0.5)); f['ic/terrain-elevation-ft']=0
dt=f['simulation/dt']; c=Hold(f,60,v=105,vs=-560); t=0; touch=None; x_touch=None; stop=None
# stabilised 3 deg descent from 60 ft agl... run
c.h=f['position/h-sl-ft']
while t<120:
    if touch is None:
        c.vs=-550 if f['position/h-agl-ft']>25 else -200
        c.step()
        if f['gear/unit[1]/WOW']==1: touch=t; x_touch=f['position/distance-from-start-mag-mt']*3.281; vt=f['velocities/vc-kts']
    else:
        for i in (0,1): f[f'fcs/throttle-cmd-norm[{i}]']=0.0 if t-touch<1.0 else 1.0; f[f'propulsion/engine[{i}]/reverser']=1 if t-touch>1.0 else 0
        f['fcs/elevator-cmd-norm']=0.0; f['fcs/left-brake-cmd-norm']=1 if t-touch>2 else 0; f['fcs/right-brake-cmd-norm']=f['fcs/left-brake-cmd-norm']
        f['fcs/aileron-cmd-norm']=0; f['fcs/rudder-cmd-norm']=max(-1,min(1,0.05*(f['attitude/psi-deg'] if f['attitude/psi-deg']<180 else f['attitude/psi-deg']-360)))
        f.run()
        if f['velocities/vg-fps']<3: stop=f['position/distance-from-start-mag-mt']*3.281; break
    t+=dt
print(f" toucher à {vt:5.1f} kt, distance de roulage {stop-x_touch:5.0f} ft, poussée inverse par moteur ≈ {f['propulsion/engine/thrust-lbs']:.0f} lb (pas {f['propulsion/engine/blade-angle']:.1f}°, {f['propulsion/engine/propeller-rpm']:.0f} rpm, N1 {f['propulsion/engine/n1']:.0f})  (POH: 2692 ft sur 50 ft, sans inverse)")
