from sim2 import *
def loadW(W,fuelfrac=0.5):
    fuel_tot=3611*fuelfrac; pax=max(0,W-9650-190-fuel_tot-100)
    return dict(fuel=[266*fuelfrac,1273*fuelfrac,1273*fuelfrac,266*fuelfrac],payload=[190,0,pax,100])
f=mk(2000,120,0,0,thr=1.0,**loadW(15000,0.9)); f['fcs/advance-cmd-norm[1]']=0.0; f['propulsion/active_engine']=1; f['propulsion/cutoff_cmd']=1; f['propulsion/active_engine']=-1
dt=f['simulation/dt']
c=Hold(f,2000,thr=1.0,vpitch=120,phi=-5,beta_hold=True); settle(f,c,30)
for k in range(int(130/dt)):
    c.vpitch=max(70,120-0.4*k*dt); f['fcs/throttle-cmd-norm[1]']=0; c.step()
    if k%(int(10/dt))==0:
        qSb=f['aero/qbar-psf']*310*57.92
        print(f" V {f['velocities/vc-kts']:5.1f} kt: palonnier pilote {f['fcs/rudder-cmd-norm']:+.2f}, boost {f['fcs/rudder-boost-lag']:+.2f}, δr {f['fcs/rudder-pos-rad']*R2D:+5.1f}°, β {f['aero/beta-deg']:+.1f}°, φ {f['attitude/phi-deg']:+.1f}, T gauche {f['propulsion/engine[0]/thrust-lbs']:5.0f} lb, N_prop {f['moments/n-prop-lbsft']:7.0f}, N_rudder {f['aero/moment/Yaw_rudder']:7.0f}, N_beta {f['aero/moment/Yaw_beta']:7.0f} ft.lb, ROC {f['velocities/h-dot-fps']*60:5.0f}")
