"""Robust BEMT (Ning 2014 phi-residual formulation) for JSBSim propeller tables.
Hartzell 4-blade 105 in (King Air 350). Blade angle parameter = beta at 0.75R."""
import numpy as np, math
D_in=105.0; R=D_in/2/12.0; B=4; hub=0.20
r_c=np.array([0.20,0.30,0.45,0.60,0.75,0.90,0.97,1.00])
c_in=np.array([7.0,8.6,9.3,9.2,8.6,7.0,5.0,2.5])
def twist_rel(x, PD=1.25):
    return math.degrees(math.atan(PD/(math.pi*x))-math.atan(PD/(math.pi*0.75)))
def section(alpha_deg, M):
    a0=-1.5; a=alpha_deg-a0; cla=0.1; astall=15.0
    if abs(a)<=astall: cl=cla*a
    else:
        s=np.sign(a); aa=abs(a); cl_stall=cla*astall
        fp=2.0*math.sin(math.radians(aa))*math.cos(math.radians(aa))
        w=min(1.0,(aa-astall)/15.0)
        cl=s*((1-w)*cl_stall*(1.0-0.15*w)+w*max(fp,0.6))
    bpg=math.sqrt(max(1-M*M,0.25)) if M<0.85 else math.sqrt(1-0.85**2)
    cl/=bpg
    cd=0.0085+0.0075*cl*cl
    if abs(a)>astall:
        aa=abs(a); w=min(1.0,(aa-astall)/18.0)
        cd=(1-w)*cd+w*(2.0*math.sin(math.radians(aa))**2+0.02)
    if M>0.80: cd+=0.02*((M-0.80)/0.15)**2+(0.15*((M-0.9)/0.1)**2 if M>0.9 else 0)
    return cl,cd
def element(x, beta_deg, lam, Wref_fn):
    """solve one element; returns (Cn, Ctan, W) with induction. lam=V/(omega r)"""
    c=np.interp(x,r_c,c_in)/12.0; r=x*R; sigma=B*c/(2*math.pi*r)
    beta=math.radians(beta_deg)
    def parts(phi):
        alpha=beta-phi
        W=Wref_fn(phi)  # approx speed for Mach only
        cl,cd=section(math.degrees(alpha), W)
        Cn=cl*math.cos(phi)-cd*math.sin(phi); Ct=cl*math.sin(phi)+cd*math.cos(phi)
        f=B/2*(1-x)/max(x*abs(math.sin(phi)),1e-6)
        F=max(2/math.pi*math.acos(min(1.0,math.exp(-f))),0.02)
        return Cn,Ct,F
    def resid(phi):
        Cn,Ct,F=parts(phi)
        s=math.sin(phi); cph=math.cos(phi)
        den_a=4*F*s*s-sigma*Cn
        a = sigma*Cn/den_a if abs(den_a)>1e-9 else 1e9
        den_b=4*F*s*cph+sigma*Ct
        b = sigma*Ct/den_b if abs(den_b)>1e-9 else 1e9
        return s/(1+a) - lam*cph/(1-b) if abs(1-b)>1e-9 else 1e9, a, b
    # bracket search in (eps, pi/2)
    phis=np.linspace(1e-3, math.pi/2-1e-3, 60)
    vals=[resid(p)[0] for p in phis]
    root=None
    for i in range(len(phis)-1):
        if np.isfinite(vals[i]) and np.isfinite(vals[i+1]) and vals[i]*vals[i+1]<0 and abs(vals[i])<50 and abs(vals[i+1])<50:
            lo,hi=phis[i],phis[i+1]
            for _ in range(40):
                mid=0.5*(lo+hi); rm=resid(mid)[0]
                if rm*resid(lo)[0]<0: hi=mid
                else: lo=mid
            root=0.5*(lo+hi); break
    if root is None:
        # fallback: no induction
        phi=math.atan(lam) if lam>0 else 1e-3
        a=0.0;b=0.0
    else:
        phi=root; _,a,b=resid(phi)
        a=max(min(a,1e4),-0.5); b=max(min(b,0.9),-0.5)
    return phi,a,b,sigma
def bemt(J, beta75_deg, n_rps=1700/60.0, rho=0.002377, a_snd=1116.0, nseg=30):
    D=2*R; omega=2*math.pi*n_rps
    V=max(J,0.003)*n_rps*D
    xs=np.linspace(hub,1.0,nseg+1); xm=0.5*(xs[1:]+xs[:-1]); dx=(xs[1:]-xs[:-1])*R
    T=0.0;Q=0.0
    for x,dr in zip(xm,dx):
        r=x*R; c=np.interp(x,r_c,c_in)/12.0
        beta_l=beta75_deg+twist_rel(x)
        lam=V/(omega*r)
        Wref=lambda phi: math.hypot(V,omega*r)/a_snd
        phi,a,b,sigma=element(x,beta_l,lam,Wref)
        Va=V*(1+a); Vt=omega*r*(1-b); W=math.hypot(Va,Vt)
        # recompute forces with final phi from velocities (consistent)
        phi2=math.atan2(Va,Vt) if root_ok(phi) else phi
        alpha=math.radians(beta_l)-phi2
        cl,cd=section(math.degrees(alpha), W/a_snd)
        Cn=cl*math.cos(phi2)-cd*math.sin(phi2); Ct=cl*math.sin(phi2)+cd*math.cos(phi2)
        T+=0.5*rho*W*W*B*c*Cn*dr
        Q+=0.5*rho*W*W*B*c*Ct*r*dr
    n=n_rps
    return T/(rho*n*n*D**4), Q*omega/(rho*n**3*D**5), T, Q
def root_ok(phi): return True
if __name__=='__main__':
    n=1700/60
    for b in [-15,-10,0,15,20,25,28,30,35,45,60,87]:
        row=[]
        for J in [0.0,0.3,0.6,1.0,1.5,2.0,2.5,3.0]:
            ct,cp,T,Q=bemt(J,b); row.append(f"{ct:6.3f}/{cp:6.3f}")
        print(f"beta {b:4d}: "+"  ".join(row))
    ct,cp,T,Q=bemt(0,28.5); print("static 28.5:",T,Q*2*math.pi*n/550)
