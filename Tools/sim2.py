import jsbsim, math
R2D=57.29578
def mk(alt,kcas,flap=0,gear=0,thr=0.6,running=True,fuel=None,payload=None,heading=0,lat=45.0,gamma=0):
    f=jsbsim.FGFDMExec('.',None); f.set_debug_level(0); f.load_model('KingAir-350')
    if payload:
        for i,w in enumerate(payload): f[f'inertia/pointmass-weight-lbs[{i}]']=w
    if fuel is not None:
        for i,w in enumerate(fuel): f[f'propulsion/tank[{i}]/contents-lbs']=w
    f['ic/h-sl-ft']=alt; f['ic/vc-kts']=kcas; f['ic/gamma-deg']=gamma; f['ic/psi-true-deg']=heading; f['ic/lat-geod-deg']=lat; f['ic/long-gc-deg']=0
    f['fcs/flap-cmd-norm']=flap; f['gear/gear-cmd-norm']=gear
    f['/controls/engines/engine[0]/condition']=0.5; f['/controls/engines/engine[1]/condition']=0.5
    for i in (0,1): f[f'fcs/throttle-cmd-norm[{i}]']=thr; f[f'fcs/advance-cmd-norm[{i}]']=1.0; f[f'fcs/mixture-cmd-norm[{i}]']=1.0
    f.run_ic()
    if running:
        f['propulsion/set-running']=-1
        for i in (0,1):
            f[f'propulsion/engine[{i}]/propeller-rpm']=1700; print('rpm set',f[f'propulsion/engine[{i}]/propeller-rpm']) if i==0 and False else None
    f['fcs/flap-pos-deg']=35*flap if flap==1 else (14*2*flap if flap<=0.5 else 14+(35-14)*(flap-0.5)*2); f['gear/gear-pos-norm']=gear
    f['fcs/flap-pos-deg']={0:0,0.5:14,1:35}.get(flap,f['fcs/flap-pos-deg'])
    return f
def rep(f):
    return dict(KCAS=f['velocities/vc-kts'],KTAS=f['velocities/vtrue-kts'],alt=f['position/h-sl-ft'],alpha=f['aero/alpha-deg'],theta=f['attitude/theta-deg'],
      elev=f['fcs/elevator-pos-rad']*R2D,elevn=f['fcs/elevator-cmd-norm'],thr=f['fcs/throttle-cmd-norm[0]'],HP=f['propulsion/engine/power-hp'],
      N1=f['propulsion/engine/n1'],prpm=f['propulsion/engine/propeller-rpm'],blade=f['propulsion/engine/blade-angle'],T=f['propulsion/engine/thrust-lbs'],
      FF=f['propulsion/engine/fuel-flow-rate-pps']*3600*2,W=f['inertia/weight-lbs'],CL=f['aero/cl-squared']**0.5,vs=f['velocities/h-dot-fps']*60,itt=f['propulsion/engine/itt-c'],
      tq=f['propulsion/engine[0]/torque-pct'],cg=(f['inertia/cg-x-in']+118.1)/70*100,gamma=f['flight-path/gamma-deg'])
FMT="{alt:6.0f}ft {KCAS:5.1f}KCAS {KTAS:5.1f}KTAS α{alpha:5.2f} θ{theta:5.2f} δe{elev:6.2f}°({elevn:5.2f}) thr{thr:4.2f} {HP:5.0f}hp N1{N1:5.1f} Np{prpm:5.0f} β{blade:4.1f} T{T:5.0f} FF{FF:4.0f}pph tq{tq:4.0f}% ITT{itt:4.0f} CL{CL:4.2f} W{W:5.0f} cg{cg:4.1f}%"
class Hold:
    """closed-loop: altitude (or vs) via elevator, wings level via aileron, speed via throttle (or fixed thr).
       vpitch=target speed -> speed is held with pitch (climb/descent), throttle fixed."""
    def __init__(s,f,h,v=None,thr=None,vs=0,phi=0,vpitch=None,beta_hold=False):
        s.f=f;s.h=h;s.v=v;s.thr=thr;s.ie=0;s.it=0;s.vs=vs;s.phi_cmd=phi;s.vpitch=vpitch;s.iv=0;s.beta_hold=beta_hold;s.ir=0
    def step(s):
        f=s.f;dt=f['simulation/dt']
        if s.vs: s.h+=s.vs/60*dt
        herr=s.h-f['position/h-sl-ft']; hdot=f['velocities/h-dot-fps']
        if s.vpitch is not None:
            ev=f['velocities/vc-kts']-s.vpitch; s.iv+=ev*dt; s.iv=max(-60,min(60,s.iv))
            gcmd=max(-12,min(20,0.6*ev+0.08*s.iv))
        else:
            gcmd=max(-8,min(8,0.02*herr+(s.vs/60-hdot)*0.25))
        th=f['attitude/theta-deg']; q=f['velocities/q-rad_sec']*R2D; gam=f['flight-path/gamma-deg']; al=f['aero/alpha-deg']
        thc=al+gcmd+1.0*(gcmd-gam); e=thc-th
        s.ie+=e*dt; s.ie=max(-60,min(60,s.ie))
        el=-(0.10*e+0.05*s.ie)+0.06*q
        f['fcs/elevator-cmd-norm']=max(-1,min(1,el))
        phi=f['attitude/phi-deg']; p=f['velocities/p-rad_sec']*R2D
        f['fcs/aileron-cmd-norm']=max(-1,min(1,0.05*(s.phi_cmd-phi)-0.02*p))
        if s.beta_hold:
            b=f['aero/beta-deg']; s.ir+=b*dt; s.ir=max(-30,min(30,s.ir))
            f['fcs/rudder-cmd-norm']=max(-1,min(1,-(0.15*b+0.05*s.ir)+0.05*f['velocities/r-rad_sec']*R2D))
        if s.v is not None:
            ve=s.v-f['velocities/vc-kts']; s.it+=ve*dt; s.it=max(-50,min(50,s.it))
            t=0.05*ve+0.02*s.it+0.5
            for i in (0,1): f[f'fcs/throttle-cmd-norm[{i}]']=max(0,min(1,t))
        elif s.thr is not None:
            for i in (0,1): f[f'fcs/throttle-cmd-norm[{i}]']=s.thr
        f.run()
def settle(f,ctl,T):
    for _ in range(int(T/f['simulation/dt'])): ctl.step()
