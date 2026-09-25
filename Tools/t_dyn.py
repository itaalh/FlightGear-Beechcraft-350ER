from sim2 import *
import numpy as np
def loadW(W,fuelfrac=0.5):
    fuel_tot=3611*fuelfrac; pax=max(0,W-9650-190-fuel_tot-100)
    return dict(fuel=[266*fuelfrac,1273*fuelfrac,1273*fuelfrac,266*fuelfrac],payload=[190,0,pax,100])
def trimmed(alt,v,W=13500,fl=0,g=0,yd=1):
    f=mk(alt,v,fl,g,thr=0.5,**loadW(W)); f['/controls/flight/yaw-damper']=yd
    c=Hold(f,alt,v=v); settle(f,c,120)
    # freeze controls at trimmed values
    return f,dict(e=f['fcs/elevator-cmd-norm'],a=f['fcs/aileron-cmd-norm'],r=f['fcs/rudder-cmd-norm'],t=f['fcs/throttle-cmd-norm[0]'])
def hold_ctl(f,ctl):
    f['fcs/elevator-cmd-norm']=ctl['e']; f['fcs/aileron-cmd-norm']=ctl['a']; f['fcs/rudder-cmd-norm']=ctl['r']
    for i in (0,1): f[f'fcs/throttle-cmd-norm[{i}]']=ctl['t']
def damping_from_peaks(t,y):
    y=np.array(y)-np.mean(y[-len(y)//4:]); t=np.array(t)
    pk=[i for i in range(1,len(y)-1) if y[i]>y[i-1] and y[i]>y[i+1] and y[i]>0.02*np.max(np.abs(y))]
    if len(pk)<2: return None,None
    T=np.mean(np.diff(t[pk][:4])); ratios=[y[pk[i+1]]/y[pk[i]] for i in range(min(3,len(pk)-1)) if y[pk[i]]>0]
    if not ratios: return T,None
    delta=-np.log(np.mean(ratios)); zeta=delta/np.sqrt(4*np.pi**2+delta**2)
    return T,zeta
print("== Modes propres, 13500 lb, 10000 ft, 200 KCAS (pilote automatique off)")
f,ctl=trimmed(10000,200); dt=f['simulation/dt']
# short period: elevator doublet
hold_ctl(f,ctl); ts=[];qs=[]
for k in range(int(12/dt)):
    f['fcs/elevator-cmd-norm']=ctl['e']-0.3*(0.2<k*dt<0.7)+0.3*(0.7<=k*dt<1.2)
    f.run(); ts.append(k*dt); qs.append(f['velocities/q-rad_sec']*R2D)
T,z=damping_from_peaks(ts[int(1.3/dt):],qs[int(1.3/dt):])
print(f" court terme (doublet profondeur): période ≈ {T} s, amortissement ζ ≈ {z}, q max {max(qs):.1f}°/s")
# phugoid: pull to +10 kt then release
f,ctl=trimmed(10000,200); hold_ctl(f,ctl); ts=[];vs=[]
for k in range(int(240/dt)):
    f['fcs/elevator-cmd-norm']=ctl['e']-0.15*(0.5<k*dt<3.0)
    phi=f['attitude/phi-deg']; f['fcs/aileron-cmd-norm']=ctl['a']+0.05*(-phi)-0.02*f['velocities/p-rad_sec']*R2D
    f.run(); ts.append(k*dt); vs.append(f['velocities/vc-kts'])
T,z=damping_from_peaks(ts[int(5/dt):],vs[int(5/dt):])
print(f" phugoïde: période ≈ {T} s, ζ ≈ {z}, ΔV ±{(max(vs[int(5/dt):])-min(vs[int(5/dt):]))/2:.1f} kt")
for yd in (1,0):
    f,ctl=trimmed(10000,200,yd=yd); hold_ctl(f,ctl); ts=[];bs=[]
    for k in range(int(40/dt)):
        f['fcs/rudder-cmd-norm']=ctl['r']+0.5*(0.5<k*dt<1.5)
        f.run(); ts.append(k*dt); bs.append(f['aero/beta-deg'])
    T,z=damping_from_peaks(ts[int(2/dt):],bs[int(2/dt):])
    print(f" roulis hollandais (YD {'on ' if yd else 'off'}): période ≈ {T} s, ζ ≈ {z}, β max {max(np.abs(bs)):.1f}°")
# roll rate
for v in (120,160,220):
    f,ctl=trimmed(10000,v); hold_ctl(f,ctl); pmax=0
    for k in range(int(3/dt)):
        f['fcs/aileron-cmd-norm']=1.0; f.run(); pmax=max(pmax,f['velocities/p-rad_sec']*R2D)
    print(f" taux de roulis max, manche en butée, {v} KCAS: {pmax:.0f} °/s (φ après 3 s: {f['attitude/phi-deg']:.0f}°)")
# spiral: bank 20 deg and release
f,ctl=trimmed(10000,200); hold_ctl(f,ctl)
for k in range(int(6/dt)):
    f['fcs/aileron-cmd-norm']=ctl['a']+0.3*(k*dt<2.5); f.run()
phi0=f['attitude/phi-deg']
for k in range(int(30/dt)): f['fcs/aileron-cmd-norm']=ctl['a']; f.run()
print(f" spirale: inclinaison {phi0:.1f}° → {f['attitude/phi-deg']:.1f}° après 30 s mains libres")
print("== Vmca (moteur droit en drapeau, gauche plein gaz, β tenu au palonnier, 5° d'inclinaison), 15000 lb, niveau mer")
f=mk(2000,120,0,0,thr=1.0,**loadW(15000,0.9)); f['fcs/advance-cmd-norm[1]']=0.0; f['propulsion/active_engine']=1; f['propulsion/cutoff_cmd']=1; f['propulsion/active_engine']=-1
c=Hold(f,2000,thr=1.0,vpitch=120,phi=-5,beta_hold=True); settle(f,c,30)
res=None
for k in range(int(200/dt)):
    c.vpitch=max(70,120-0.4*k*dt); f['fcs/throttle-cmd-norm[1]']=0
    c.step()
    if k*dt>5 and f['fcs/rudder-cmd-norm']>=0.999 and f['aero/beta-deg']<-4:
        res=(f['velocities/vc-kts'],f['aero/beta-deg'],f['fcs/rudder-pos-rad']*R2D,f['fcs/rudder-boost-lag']); break
print(f" Vmca ≈ {res[0]:.0f} KCAS (β {res[1]:.1f}°, direction {res[2]:.1f}°, boost {res[3]:.2f}) — POH 94 KIAS" if res else " pas de perte de contrôle jusqu'à 70 kt")
