from sim2 import *
def loadW(W,fuelfrac=0.5):
    fuel_tot=3611*fuelfrac; pax=max(0,W-9650-190-fuel_tot-100)
    return dict(fuel=[266*fuelfrac,1273*fuelfrac,1273*fuelfrac,266*fuelfrac],payload=[190,0,pax,100])
import sys
if "--start" in sys.argv:
  print("== Démarrage moteur (sol, batterie), condition lever LOW IDLE à 12 % N1")
  f=jsbsim.FGFDMExec('.',None); f.set_debug_level(0); f.load_model('KingAir-350')
  f['ic/h-agl-ft']=6.5; f['ic/vc-kts']=0; f['ic/lat-geod-deg']=45; f['ic/terrain-elevation-ft']=0; f['gear/gear-cmd-norm']=1
  f['/controls/engines/engine[0]/condition']=0.0
  for i in (0,1): f[f'fcs/advance-cmd-norm[{i}]']=1.0
  f.run_ic(); f['gear/gear-pos-norm']=1; f['fcs/left-brake-cmd-norm']=1; f['fcs/right-brake-cmd-norm']=1
  dt=f['simulation/dt']; t=0; f['propulsion/active_engine']=0; f['propulsion/cutoff_cmd']=1; f['propulsion/starter_cmd']=1; lit=None
  while t<60:
      n1=f['propulsion/engine[0]/n1']
      if n1>12 and f['propulsion/cutoff_cmd']==1 and t>1: f['propulsion/cutoff_cmd']=0; f['/controls/engines/engine[0]/condition']=0.5; print(f"  t={t:4.1f} s N1 {n1:4.1f}% -> condition lever LOW IDLE (fuel on)")
      f.run(); t+=dt
      if lit is None and f['propulsion/engine[0]/set-running']: lit=t
      if int(t*10)%50==0 and abs(t-round(t))<dt: print(f"  t={t:4.1f} s: N1 {f['propulsion/engine[0]/n1']:5.1f}%  ITT {f['propulsion/engine[0]/itt-c']:4.0f} C  Np {f['propulsion/engine[0]/propeller-rpm']:4.0f} rpm  FF {f['propulsion/engine[0]/fuel-flow-rate-pps']*3600:4.0f} pph  starter {f['propulsion/starter_cmd']:.0f} running {f['propulsion/engine[0]/set-running']:.0f}")
      if f['propulsion/engine[0]/n1']>55 and f['propulsion/starter_cmd']==1: f['propulsion/starter_cmd']=0
print("== Temps de montée 15000 lb, ISA, 160 KIAS -> FL350 (plein gaz, 1700 rpm)")
f=mk(100,160,0,0,thr=1.0,**loadW(15000,0.9)); c=Hold(f,0,thr=1.0,vpitch=160); dt=f['simulation/dt']; t=0; marks=[10000,20000,25000,30000,35000]; i=0; low=0
while t<3600 and i<len(marks):
    c.vpitch=150
    c.step(); t+=dt
    if f['position/h-sl-ft']>=marks[i]:
        print(f"  FL{marks[i]//100:03d} à t = {t/60:5.1f} min, ROC {f['velocities/h-dot-fps']*60:5.0f} fpm, {f['velocities/vc-kts']:5.1f} KCAS, carburant brûlé {2*f['propulsion/engine/fuel-used-lbs']:5.0f} lb, W {f['inertia/weight-lbs']:5.0f}"); i+=1
    low = low+dt if (f['velocities/h-dot-fps']*60<100 and f['position/h-sl-ft']>20000) else 0
    if low>20: print(f"  plafond pratique (ROC<100 fpm) ≈ {f['position/h-sl-ft']:.0f} ft"); break
print("== Temps de montée : livre ~ 20-25 min FL300")
print("== Autonomie : croisière FL280 plein gaz sur 3000 lb de carburant, 13000 lb au départ")
f=mk(28000,200,0,0,thr=1.0,**loadW(13000,0.83)); c=Hold(f,28000,thr=1.0); settle(f,c,400)
ff=f['propulsion/engine/fuel-flow-rate-pps']*7200; tas=f['velocities/vtrue-kts']
print(f"  {tas:5.0f} KTAS, {ff:4.0f} pph -> {tas/ff*3000:5.0f} nm avec 3000 lb (sans réserves) ; spec ferry 1572 nm en croisière haute vitesse")
