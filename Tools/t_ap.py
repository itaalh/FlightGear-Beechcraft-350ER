from sim2 import *
import math
def loadW(W,fuelfrac=0.5):
    fuel_tot=3611*fuelfrac; pax=max(0,W-9650-190-fuel_tot-100)
    return dict(fuel=[266*fuelfrac,1273*fuelfrac,1273*fuelfrac,266*fuelfrac],payload=[190,0,pax,100])
f=mk(10000,200,0,0,thr=0.6,**loadW(13500)); dt=f['simulation/dt']
c=Hold(f,10000,v=200); settle(f,c,60)
thr=f['fcs/throttle-cmd-norm[0]']; e0=f['fcs/elevator-cmd-norm']
# hand over to AP: pilot controls neutral except trim = e0
f['fcs/elevator-cmd-norm']=0; f['fcs/pitch-trim-cmd-norm']=e0; f['fcs/aileron-cmd-norm']=0; f['fcs/rudder-cmd-norm']=0
for i in (0,1): f[f'fcs/throttle-cmd-norm[{i}]']=0.43
f['ap/engaged']=1; f['ap/roll-mode']=1; f['ap/target-heading-true-deg']=90; f['ap/pitch-mode']=1; f['ap/target-altitude-ft']=10000
print("== PA : virage vers le 090 + tenue d'altitude 10000 ft")
t=0
def log(tag):
    print(f" {tag:28s} t{t:5.0f} ψ{f['attitude/psi-deg']:6.1f} φ{f['attitude/phi-deg']:6.1f} h{f['position/h-sl-ft']:7.0f} vs{f['velocities/h-dot-fps']*60:6.0f} θ{f['attitude/theta-deg']:5.1f} V{f['velocities/vc-kts']:6.1f} ail{f['ap/aileron-cmd']:6.3f} el{f['ap/elevator-cmd']:6.3f} pt{f['ap/pitch-target-deg']:5.1f}")
for k in range(int(80/dt)):
    f.run(); t+=dt
    if k%(int(10/dt))==0: log("HDG 090 / ALT")
print("== PA : VS +1500 vers 14000 puis capture ALT")
f['ap/pitch-mode']=2; f['ap/target-vs-fpm']=1500; f['ap/target-altitude-ft']=14000
for i in (0,1): f[f'fcs/throttle-cmd-norm[{i}]']=1.0
for k in range(int(240/dt)):
    if f['ap/pitch-mode']==2 and abs(f['position/h-sl-ft']-14000)<200: f['ap/pitch-mode']=1
    f.run(); t+=dt
    if k%(int(20/dt))==0: log("VS/ALT capture")
print("== PA : IAS 180 kt en descente (manettes réduites) puis NAV interception d'un LOC 090")
f['ap/pitch-mode']=3; f['ap/target-ias-kt']=180
for i in (0,1): f[f'fcs/throttle-cmd-norm[{i}]']=0.25
lat0=f['position/lat-geod-deg']; lon0=f['position/long-gc-deg']; coslat=math.cos(math.radians(lat0))
# course 090 line 3 nm north of current position, station 15 nm east
f['ap/roll-mode']=2; f['ap/nav-is-loc']=1; f['ap/nav-valid']=1; f['ap/nav-course-true-deg']=90
for k in range(int(300/dt)):
    x_n=(f['position/lat-geod-deg']-lat0)*364000; y_e=(f['position/long-gc-deg']-lon0)*coslat*364000
    xtk=x_n-3*6076; dist=15*6076-y_e
    ang=math.degrees(math.atan2(-xtk,max(dist,1000)))
    f['ap/nav-deflection']=max(-1,min(1,ang/2.5*-1)); f['ap/nav-distance-nm']=max(dist,0)/6076
    f.run(); t+=dt
    if k%(int(25/dt))==0: print(f" NAV/IAS t{t:5.0f} ψ{f['attitude/psi-deg']:6.1f} φ{f['attitude/phi-deg']:6.1f} xtk{xtk/6076:6.2f}nm defl{f['ap/nav-deflection']:6.2f} h{f['position/h-sl-ft']:7.0f} vs{f['velocities/h-dot-fps']*60:6.0f} V{f['velocities/vc-kts']:6.1f}")
