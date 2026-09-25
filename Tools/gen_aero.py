"""Generates Aero/KingAir-350.xml (and the 350ER variant with --er) for the Beechcraft King Air 350 / 350ER."""
import numpy as np, math, os, sys
ER = "--er" in sys.argv
M2IN=39.3701
# ---------------- geometry (structural frame: x aft, y right, z up, inches; origin = 3D model origin)
S=310.0; b=57.92; cbar=5.83               # ft
MAC_LE_x=-3.00*M2IN                        # in (from 3D model)
AERO_x=MAC_LE_x+0.25*cbar*12               # 25% MAC
AERO_z=-0.40*M2IN
def pct_mac(x): return (x-MAC_LE_x)/(cbar*12)*100
def mac_x(p): return MAC_LE_x+p/100*cbar*12
# ---------------- lift / drag tables
alphas=[-12,-8,-4,0,2,4,6,8,10,12,13,14,15,16,17,18,20,25,30,40,60,90]
def cl_curve(flap):
    if flap==0:
        base={-12:-0.78,-8:-0.40,-4:-0.02,0:0.35,2:0.54,4:0.73,6:0.92,8:1.10,10:1.27,12:1.42,13:1.48,14:1.53,15:1.55,16:1.54,17:1.48,18:1.38,20:1.20,25:1.00,30:0.90,40:0.85,60:0.55,90:0.0}
    elif flap==14:
        base={-12:-0.45,-8:-0.07,-4:0.32,0:0.70,2:0.89,4:1.08,6:1.27,8:1.45,10:1.62,12:1.76,13:1.82,14:1.85,15:1.83,16:1.76,17:1.66,18:1.55,20:1.35,25:1.10,30:0.95,40:0.88,60:0.55,90:0.0}
    else:
        base={-12:-0.08,-8:0.30,-4:0.70,0:1.08,2:1.27,4:1.46,6:1.64,8:1.82,10:1.98,12:2.12,13:2.18,14:2.16,15:2.10,16:2.00,17:1.88,18:1.75,20:1.50,25:1.20,30:1.00,40:0.90,60:0.55,90:0.0}
    return [base[a] for a in alphas]
CL={f:cl_curve(f) for f in (0,14,35)}
AR=b*b/S
def cd_curve(flap):
    cd0={0:0.0275,14:0.0425,35:0.0985}[flap]+(0.0008 if ER else 0.0); e={0:0.68,14:0.66,35:0.62}[flap]; clmd={0:0.20,14:0.45,35:0.75}[flap]
    K=1/(math.pi*AR*e); out=[]
    astall={0:15,14:14,35:13}[flap]
    for a,cl in zip(alphas,CL[flap]):
        cd=cd0+K*(cl-clmd)**2
        if a>astall: cd+=0.012*(a-astall)+0.0004*(a-astall)**2
        if a<-8: cd+=0.01*(-8-a)
        cd=min(cd,1.6)
        # flat-plate limit at very high alpha
        cd=max(cd,1.6*math.sin(math.radians(abs(a)))**2*0.9 if abs(a)>30 else cd)
        out.append(cd)
    return out
CD={f:cd_curve(f) for f in (0,14,35)}
def tbl2(rows,cols,data,rowvar,colvar,indent=12):
    s=" "*indent+"<table>\n"+" "*indent+f"  <independentVar lookup=\"row\">{rowvar}</independentVar>\n"+" "*indent+f"  <independentVar lookup=\"column\">{colvar}</independentVar>\n"+" "*indent+"  <tableData>\n"
    s+=" "*indent+"          "+"".join(f"{c:9.1f}" for c in cols)+"\n"
    for r,row in zip(rows,data):
        s+=" "*indent+f"    {r:8.4f}"+"".join(f"{v:9.4f}" for v in row)+"\n"
    s+=" "*indent+"  </tableData>\n"+" "*indent+"</table>\n"
    return s
arad=[math.radians(a) for a in alphas]
CLdata=[[CL[0][i],CL[14][i],CL[35][i]] for i in range(len(alphas))]
CDdata=[[CD[0][i],CD[14][i],CD[35][i]] for i in range(len(alphas))]
Cm_flap=[[0.0,-0.06,-0.17]]  # flap pitching moment increments
# ---------------- masses (lb) & arms (in)
EMPTY_W=10150.0 if ER else 9650.0; EMPTY_CG_PCT=21.5
empty_cg_x=mac_x(EMPTY_CG_PCT); empty_cg_z=-0.12*M2IN
# inertia (empty), slug ft2
IXX=21300 if ER else 19700; IYY=20400 if ER else 18900; IZZ=39200 if ER else 36300; IXZ=800
# gear (in)
nose=(-6.64*M2IN, 0.0, -1.88*M2IN); mainL=(-1.93*M2IN,-2.77*M2IN,-1.92*M2IN); mainR=(-1.93*M2IN,2.77*M2IN,-1.92*M2IN)
# tanks: 0 L aux, 1 L main, 2 R main, 3 R aux (gal usable, lb at 6.7 lb/gal)
TX=-97.8
MAIN_GAL=308.5 if ER else 190.0; MAIN_Y=(3.40 if ER else 3.80)*M2IN
tanks=[("L aux",79.5,TX,-1.50*M2IN,-0.50*M2IN,1),("L main",MAIN_GAL,TX,-MAIN_Y,-0.45*M2IN,2),
       ("R main",MAIN_GAL,TX,MAIN_Y,-0.45*M2IN,2),("R aux",79.5,TX,1.50*M2IN,-0.50*M2IN,1)]
def tankxml():
    s=""
    for i,(n,gal,x,y,z,pr) in enumerate(tanks):
        s+=f'''
    <tank type="FUEL" number="{i}">  <!-- {n}: {gal} US gal usable -->
      <location unit="IN"><x>{x:.1f}</x><y>{y:.1f}</y><z>{z:.1f}</z></location>
      <capacity unit="LBS"> {gal*6.7:.1f} </capacity>
      <contents unit="LBS"> {gal*6.7*0.8:.1f} </contents>
      <priority> {pr} </priority>
      <density unit="LBS/GAL"> 6.7 </density>
    </tank>'''
    return s
engine_y=2.77*M2IN; prop_x=-5.46*M2IN; prop_z=-0.18*M2IN; eng_x=-4.40*M2IN
xml=f'''<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="http://jsbsim.sourceforge.net/JSBSim.xsl"?>
<fdm_config name="{"KingAir-350ER" if ER else "KingAir-350"}" version="2.0" release="BETA"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:noNamespaceSchemaLocation="http://jsbsim.sourceforge.net/JSBSim.xsd">

  <fileheader>
    <author> Rebuilt 2026 for the FlightGear KingAir-350 package (JSBSim) </author>
    <filecreationdate> 2026-09-24 </filecreationdate>
    <version> 2.0 </version>
    <description>
      Beechcraft King Air {"350ER (B300 Extended Range: MTOW 16500 lb, MLW 15675 lb, MZFW 13000 lb, 775 US gal in enlarged nacelle tanks, reinforced landing gear)" if ER else "350 (B300)"}. Twin PT6A-60A, Hartzell 4-blade 105 in propellers.
      Structural frame: origin at the 3D model origin, x positive aft, y right, z up, inches.
      Wing: S = 310 ft2, b = 57.92 ft, MAC = 5.83 ft (70 in), MAC leading edge at x = {MAC_LE_x:.1f} in,
      dihedral 6 deg, aspect ratio 10.8, NASA winglets. T-tail: 68 ft2, 17 deg sweep; fin 52.3 ft2.
      Aerodynamic reference point at 25 % MAC. CG envelope: 7.8 % (to 11800 lb) / 19.3 % (15000 lb) fwd, 31.7 % aft.
      Weights: BEW ~ {EMPTY_W:.0f} lb here (payload dialog adds crew/pax/baggage).
      Fuel: 2 x {MAIN_GAL:.1f} gal main + 2 x 79.5 gal aux (aux transfers first).
      Sources: Beechcraft King Air 350i Specification and Description, TCDS A24CE, operator limitation
      sheets (Vmo 263 KIAS / M 0.58, Vfe 202/158, Vle 184, Vs 96 / Vso 81 KCAS at 15000 lb, Vmca 94),
      published performance (ROC 2731 fpm, 312 KTAS max cruise FL240, 1572 nm), ICAS 2002 paper 783 (flight test envelope).
    </description>
  </fileheader>

  <metrics>
    <wingarea  unit="FT2"> {S:.1f} </wingarea>
    <wingspan  unit="FT" > {b:.2f} </wingspan>
    <wing_incidence unit="DEG"> 3.5 </wing_incidence>
    <chord     unit="FT" > {cbar:.2f} </chord>
    <htailarea unit="FT2"> 68.0 </htailarea>
    <htailarm  unit="FT" > 25.9 </htailarm>
    <vtailarea unit="FT2"> 52.3 </vtailarea>
    <vtailarm  unit="FT" > 24.4 </vtailarm>
    <location name="AERORP" unit="IN"> <x> {AERO_x:.1f} </x> <y> 0.0 </y> <z> {AERO_z:.1f} </z> </location>
    <location name="EYEPOINT" unit="IN"> <x> -157.5 </x> <y> -14.7 </y> <z> 22.0 </z> </location>
    <location name="VRP" unit="IN"> <x> 0.0 </x> <y> 0.0 </y> <z> 0.0 </z> </location>
  </metrics>

  <mass_balance>
    <ixx unit="SLUG*FT2"> {IXX} </ixx>
    <iyy unit="SLUG*FT2"> {IYY} </iyy>
    <izz unit="SLUG*FT2"> {IZZ} </izz>
    <ixz unit="SLUG*FT2"> {IXZ} </ixz>
    <emptywt unit="LBS"> {EMPTY_W:.0f} </emptywt>
    <location name="CG" unit="IN"> <x> {empty_cg_x:.1f} </x> <y> 0.0 </y> <z> {empty_cg_z:.1f} </z> </location>
    <pointmass name="Pilot">
      <weight unit="LBS"> 190.0 </weight>
      <location name="POINTMASS" unit="IN"> <x> -157.5 </x> <y> -14.7 </y> <z> 0.0 </z> </location>
    </pointmass>
    <pointmass name="Copilot">
      <weight unit="LBS"> 0.0 </weight>
      <location name="POINTMASS" unit="IN"> <x> -157.5 </x> <y> 14.7 </y> <z> 0.0 </z> </location>
    </pointmass>
    <pointmass name="Passengers">
      <weight unit="LBS"> 680.0 </weight>
      <location name="POINTMASS" unit="IN"> <x> -93.0 </x> <y> 0.0 </y> <z> 0.0 </z> </location>
    </pointmass>
    <pointmass name="Baggage">
      <weight unit="LBS"> 100.0 </weight>
      <location name="POINTMASS" unit="IN"> <x> 55.0 </x> <y> 0.0 </y> <z> -5.0 </z> </location>
    </pointmass>
  </mass_balance>

  <ground_reactions>
    <contact type="BOGEY" name="NOSE">
      <location unit="IN"> <x> {nose[0]:.1f} </x> <y> {nose[1]:.1f} </y> <z> {nose[2]:.1f} </z> </location>
      <static_friction> 0.80 </static_friction>
      <dynamic_friction> 0.50 </dynamic_friction>
      <rolling_friction> 0.02 </rolling_friction>
      <spring_coeff unit="LBS/FT"> {13500 if ER else 12000} </spring_coeff>
      <damping_coeff unit="LBS/FT/SEC"> {2000 if ER else 1800} </damping_coeff>
      <damping_coeff_rebound unit="LBS/FT/SEC"> 600 </damping_coeff_rebound>
      <max_steer unit="DEG"> 48 </max_steer>
      <brake_group> NONE </brake_group>
      <retractable> 1 </retractable>
    </contact>
    <contact type="BOGEY" name="LEFT_MAIN">
      <location unit="IN"> <x> {mainL[0]:.1f} </x> <y> {mainL[1]:.1f} </y> <z> {mainL[2]:.1f} </z> </location>
      <static_friction> 0.80 </static_friction>
      <dynamic_friction> 0.50 </dynamic_friction>
      <rolling_friction> 0.02 </rolling_friction>
      <spring_coeff unit="LBS/FT"> {23000 if ER else 20000} </spring_coeff>
      <damping_coeff unit="LBS/FT/SEC"> {3300 if ER else 2900} </damping_coeff>
      <damping_coeff_rebound unit="LBS/FT/SEC"> 1200 </damping_coeff_rebound>
      <max_steer unit="DEG"> 0.0 </max_steer>
      <brake_group> LEFT </brake_group>
      <retractable> 1 </retractable>
    </contact>
    <contact type="BOGEY" name="RIGHT_MAIN">
      <location unit="IN"> <x> {mainR[0]:.1f} </x> <y> {mainR[1]:.1f} </y> <z> {mainR[2]:.1f} </z> </location>
      <static_friction> 0.80 </static_friction>
      <dynamic_friction> 0.50 </dynamic_friction>
      <rolling_friction> 0.02 </rolling_friction>
      <spring_coeff unit="LBS/FT"> {23000 if ER else 20000} </spring_coeff>
      <damping_coeff unit="LBS/FT/SEC"> {3300 if ER else 2900} </damping_coeff>
      <damping_coeff_rebound unit="LBS/FT/SEC"> 1200 </damping_coeff_rebound>
      <max_steer unit="DEG"> 0.0 </max_steer>
      <brake_group> RIGHT </brake_group>
      <retractable> 1 </retractable>
    </contact>
    <contact type="STRUCTURE" name="LEFT_WINGTIP">
      <location unit="IN"> <x> -86.0 </x> <y> -346.0 </y> <z> -12.0 </z> </location>
      <static_friction> 0.8 </static_friction> <dynamic_friction> 0.6 </dynamic_friction>
      <spring_coeff unit="LBS/FT"> 40000 </spring_coeff> <damping_coeff unit="LBS/FT/SEC"> 4000 </damping_coeff>
    </contact>
    <contact type="STRUCTURE" name="RIGHT_WINGTIP">
      <location unit="IN"> <x> -86.0 </x> <y> 346.0 </y> <z> -12.0 </z> </location>
      <static_friction> 0.8 </static_friction> <dynamic_friction> 0.6 </dynamic_friction>
      <spring_coeff unit="LBS/FT"> 40000 </spring_coeff> <damping_coeff unit="LBS/FT/SEC"> 4000 </damping_coeff>
    </contact>
    <contact type="STRUCTURE" name="TAIL_SKID">
      <location unit="IN"> <x> 255.0 </x> <y> 0.0 </y> <z> -30.0 </z> </location>
      <static_friction> 0.8 </static_friction> <dynamic_friction> 0.6 </dynamic_friction>
      <spring_coeff unit="LBS/FT"> 40000 </spring_coeff> <damping_coeff unit="LBS/FT/SEC"> 4000 </damping_coeff>
    </contact>
    <contact type="STRUCTURE" name="NOSE_CONE">
      <location unit="IN"> <x> -277.0 </x> <y> 0.0 </y> <z> -10.0 </z> </location>
      <static_friction> 0.8 </static_friction> <dynamic_friction> 0.6 </dynamic_friction>
      <spring_coeff unit="LBS/FT"> 40000 </spring_coeff> <damping_coeff unit="LBS/FT/SEC"> 4000 </damping_coeff>
    </contact>
  </ground_reactions>

  <propulsion>
    <engine file="PT6A-60A">
      <location unit="IN"> <x> {eng_x:.1f} </x> <y> {-engine_y:.1f} </y> <z> {prop_z:.1f} </z> </location>
      <orient unit="DEG"> <pitch> 0.0 </pitch> <roll> 0.0 </roll> <yaw> 0.0 </yaw> </orient>
      <feed> 0 </feed>
      <feed> 1 </feed>
      <thruster file="Hartzell-4B-105">
        <location unit="IN"> <x> {prop_x:.1f} </x> <y> {-engine_y:.1f} </y> <z> {prop_z:.1f} </z> </location>
        <orient unit="DEG"> <pitch> 0.0 </pitch> <roll> 0.0 </roll> <yaw> 0.0 </yaw> </orient>
        <sense> 1 </sense>
      </thruster>
    </engine>
    <engine file="PT6A-60A">
      <location unit="IN"> <x> {eng_x:.1f} </x> <y> {engine_y:.1f} </y> <z> {prop_z:.1f} </z> </location>
      <orient unit="DEG"> <pitch> 0.0 </pitch> <roll> 0.0 </roll> <yaw> 0.0 </yaw> </orient>
      <feed> 2 </feed>
      <feed> 3 </feed>
      <thruster file="Hartzell-4B-105">
        <location unit="IN"> <x> {prop_x:.1f} </x> <y> {engine_y:.1f} </y> <z> {prop_z:.1f} </z> </location>
        <orient unit="DEG"> <pitch> 0.0 </pitch> <roll> 0.0 </roll> <yaw> 0.0 </yaw> </orient>
        <sense> 1 </sense>
      </thruster>
    </engine>
{tankxml()}
  </propulsion>

  <system file="engine-control"/>
  <system file="fuel-system"/>
  <system file="nws"/>
  <system file="autopilot"/>

  <flight_control name="FCS: KingAir-350">
    <property value="1"> /controls/flight/yaw-damper </property>
    <property value="1"> /controls/flight/rudder-boost </property>

    <channel name="Pitch">
      <!-- Elevator: 20 deg up (nose up, cmd -1) / 14 deg down (cmd +1). Trim (tab) adds to the command. -->
      <summer name="fcs/pitch-cmd-sum">
        <input> fcs/elevator-cmd-norm </input>
        <input> fcs/pitch-trim-cmd-norm </input>
        <input> ap/elevator-cmd </input>
        <clipto> <min> -1 </min> <max> 1 </max> </clipto>
      </summer>
      <aerosurface_scale name="fcs/elevator-control">
        <input> fcs/pitch-cmd-sum </input>
        <domain> <min> -1 </min> <max> 1 </max> </domain>
        <range> <min> -0.3491 </min> <max> 0.2443 </max> </range>
        <output> fcs/elevator-pos-rad </output>
      </aerosurface_scale>
      <aerosurface_scale name="fcs/elevator-normalization">
        <input> fcs/elevator-pos-rad </input>
        <domain> <min> -0.3491 </min> <max> 0.2443 </max> </domain>
        <range> <min> -1 </min> <max> 1 </max> </range>
        <output> fcs/elevator-pos-norm </output>
      </aerosurface_scale>
    </channel>

    <channel name="Roll">
      <!-- Ailerons: 25 deg up / 15 deg down, differential. Positive cmd = right roll. -->
      <summer name="fcs/roll-cmd-sum">
        <input> fcs/aileron-cmd-norm </input>
        <input> fcs/roll-trim-cmd-norm </input>
        <input> ap/aileron-cmd </input>
        <clipto> <min> -1 </min> <max> 1 </max> </clipto>
      </summer>
      <aerosurface_scale name="fcs/left-aileron-control">
        <input> fcs/roll-cmd-sum </input>
        <domain> <min> -1 </min> <max> 1 </max> </domain>
        <range> <min> -0.4363 </min> <max> 0.2618 </max> </range>
        <output> fcs/left-aileron-pos-rad </output>
      </aerosurface_scale>
      <pure_gain name="fcs/right-aileron-cmd">
        <input> fcs/roll-cmd-sum </input>
        <gain> -1.0 </gain>
      </pure_gain>
      <aerosurface_scale name="fcs/right-aileron-control">
        <input> fcs/right-aileron-cmd </input>
        <domain> <min> -1 </min> <max> 1 </max> </domain>
        <range> <min> -0.4363 </min> <max> 0.2618 </max> </range>
        <output> fcs/right-aileron-pos-rad </output>
      </aerosurface_scale>
      <!-- effective (average) aileron deflection for the aero model, positive = right roll -->
      <summer name="fcs/aileron-diff-rad">
        <input> fcs/left-aileron-pos-rad </input>
        <input> -fcs/right-aileron-pos-rad </input>
      </summer>
      <pure_gain name="fcs/aileron-eff-rad">
        <input> fcs/aileron-diff-rad </input>
        <gain> 0.5 </gain>
      </pure_gain>
      <aerosurface_scale name="fcs/left-aileron-normalization">
        <input> fcs/left-aileron-pos-rad </input>
        <domain> <min> -0.4363 </min> <max> 0.2618 </max> </domain>
        <range> <min> -1 </min> <max> 1 </max> </range>
        <output> fcs/left-aileron-pos-norm </output>
      </aerosurface_scale>
      <aerosurface_scale name="fcs/right-aileron-normalization">
        <input> fcs/right-aileron-pos-rad </input>
        <domain> <min> -0.4363 </min> <max> 0.2618 </max> </domain>
        <range> <min> -1 </min> <max> 1 </max> </range>
        <output> fcs/right-aileron-pos-norm </output>
      </aerosurface_scale>
    </channel>

    <channel name="Yaw">
      <!-- Yaw damper: washed-out yaw rate feedback (required above 5000 ft on the real aircraft) -->
      <washout_filter name="fcs/yaw-rate-washout">
        <input> velocities/r-aero-rad_sec </input>
        <c1> 0.5 </c1>
      </washout_filter>
      <pure_gain name="fcs/yaw-damper-gain">
        <input> fcs/yaw-rate-washout </input>
        <gain> 2.2 </gain>
        <clipto> <min> -0.35 </min> <max> 0.35 </max> </clipto>
      </pure_gain>
      <switch name="fcs/yaw-damper-cmd">
        <default value="0.0"/>
        <test value="fcs/yaw-damper-gain"> /controls/flight/yaw-damper == 1 </test>
      </switch>
      <!-- Rudder boost: pneumatic assist proportional to the torque differential (armed by switch) -->
      <fcs_function name="fcs/torque-diff">
        <function>
          <difference>
            <abs><property> propulsion/engine[0]/propeller-torque-ftlb </property></abs>
            <abs><property> propulsion/engine[1]/propeller-torque-ftlb </property></abs>
          </difference>
        </function>
      </fcs_function>
      <fcs_function name="fcs/rudder-boost-raw">
        <function>
          <product>
            <value> 0.00035 </value>
            <property> fcs/torque-diff </property>
          </product>
        </function>
        <clipto> <min> -0.45 </min> <max> 0.45 </max> </clipto>
      </fcs_function>
      <switch name="fcs/rudder-boost-cmd">
        <default value="0.0"/>
        <test value="fcs/rudder-boost-raw"> /controls/flight/rudder-boost == 1 </test>
      </switch>
      <lag_filter name="fcs/rudder-boost-lag">
        <input> fcs/rudder-boost-cmd </input>
        <c1> 2.0 </c1>
      </lag_filter>
      <summer name="fcs/rudder-cmd-sum">
        <input> fcs/rudder-cmd-norm </input>
        <input> fcs/yaw-trim-cmd-norm </input>
        <input> fcs/yaw-damper-cmd </input>
        <input> fcs/rudder-boost-lag </input>
        <clipto> <min> -1 </min> <max> 1 </max> </clipto>
      </summer>
      <aerosurface_scale name="fcs/rudder-control">
        <input> fcs/rudder-cmd-sum </input>
        <domain> <min> -1 </min> <max> 1 </max> </domain>
        <range> <min> -0.4363 </min> <max> 0.4363 </max> </range>
        <output> fcs/rudder-pos-rad </output>
      </aerosurface_scale>
      <aerosurface_scale name="fcs/rudder-normalization">
        <input> fcs/rudder-pos-rad </input>
        <domain> <min> -0.4363 </min> <max> 0.4363 </max> </domain>
        <range> <min> -1 </min> <max> 1 </max> </range>
        <output> fcs/rudder-pos-norm </output>
      </aerosurface_scale>
    </channel>

    <channel name="Flaps">
      <!-- UP / APPROACH (14 deg) / DOWN (35 deg). About 12 s full travel. -->
      <kinematic name="fcs/flaps-control">
        <input> fcs/flap-cmd-norm </input>
        <traverse>
          <setting> <position> 0 </position> <time> 0 </time> </setting>
          <setting> <position> 14 </position> <time> 5 </time> </setting>
          <setting> <position> 35 </position> <time> 7 </time> </setting>
        </traverse>
        <output> fcs/flap-pos-deg </output>
      </kinematic>
      <aerosurface_scale name="fcs/flap-normalization">
        <input> fcs/flap-pos-deg </input>
        <domain> <min> 0 </min> <max> 35 </max> </domain>
        <range> <min> 0 </min> <max> 1 </max> </range>
        <output> fcs/flap-pos-norm </output>
      </aerosurface_scale>
    </channel>

    <channel name="Landing Gear">
      <kinematic name="fcs/gear-control">
        <input> gear/gear-cmd-norm </input>
        <traverse>
          <setting> <position> 0 </position> <time> 0 </time> </setting>
          <setting> <position> 1 </position> <time> 6 </time> </setting>
        </traverse>
        <output> gear/gear-pos-norm </output>
      </kinematic>
    </channel>

  </flight_control>

  <aerodynamics>

    <!-- ground effect on lift and induced drag, h/b of the wing -->
    <function name="aero/function/kCLge">
      <table>
        <independentVar lookup="row"> aero/h_b-mac-ft </independentVar>
        <tableData>
          0.00  1.15
          0.10  1.10
          0.20  1.06
          0.40  1.02
          1.00  1.00
        </tableData>
      </table>
    </function>
    <function name="aero/function/kCDge">
      <table>
        <independentVar lookup="row"> aero/h_b-mac-ft </independentVar>
        <tableData>
          0.00  0.55
          0.10  0.70
          0.20  0.85
          0.40  0.95
          1.00  1.00
        </tableData>
      </table>
    </function>
    <!-- basic lift coefficient (alpha, flaps) -->
    <function name="aero/coefficient/CL-basic">
{tbl2(arad,[0,14,35],CLdata,"aero/alpha-rad","fcs/flap-pos-deg",6)}    </function>
    <function name="aero/coefficient/CD-basic">
{tbl2(arad,[0,14,35],CDdata,"aero/alpha-rad","fcs/flap-pos-deg",6)}    </function>

    <axis name="LIFT">
      <function name="aero/force/Lift_basic">
        <description> Lift due to alpha and flaps (with ground effect) </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> aero/function/kCLge </property>
          <property> aero/coefficient/CL-basic </property>
        </product>
      </function>
      <function name="aero/force/Lift_elevator">
        <description> Lift due to elevator deflection </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> fcs/elevator-pos-rad </property>
          <value> 0.40 </value>
        </product>
      </function>
      <function name="aero/force/Lift_pitchrate">
        <description> Lift due to pitch rate </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> aero/ci2vel </property>
          <property> velocities/q-aero-rad_sec </property>
          <value> 7.0 </value>
        </product>
      </function>
      <function name="aero/force/Lift_alphadot">
        <description> Lift due to alpha rate </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> aero/ci2vel </property>
          <property> aero/alphadot-rad_sec </property>
          <value> 2.0 </value>
        </product>
      </function>
    </axis>

    <axis name="DRAG">
      <function name="aero/force/Drag_basic">
        <description> Profile + induced drag (alpha, flaps), induced part reduced in ground effect </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <sum>
            <value> 0.0275 </value>
            <product>
              <property> aero/function/kCDge </property>
              <difference> <property> aero/coefficient/CD-basic </property> <value> 0.0275 </value> </difference>
            </product>
          </sum>
        </product>
      </function>
      <function name="aero/force/Drag_gear">
        <description> Landing gear drag </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> gear/gear-pos-norm </property>
          <value> 0.021 </value>
        </product>
      </function>
      <function name="aero/force/Drag_beta">
        <description> Drag due to sideslip </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <table>
            <independentVar lookup="row"> aero/beta-rad </independentVar>
            <tableData>
              -1.57   0.90
              -0.52   0.20
              -0.26   0.05
               0.00   0.00
               0.26   0.05
               0.52   0.20
               1.57   0.90
            </tableData>
          </table>
        </product>
      </function>
      <function name="aero/force/Drag_elevator">
        <description> Drag due to elevator deflection </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <abs> <property> fcs/elevator-pos-rad </property> </abs>
          <value> 0.035 </value>
        </product>
      </function>
      <function name="aero/force/Drag_feathered">
        <description> Drag of feathered propellers (blades edge-on, nacelle flow) </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <value> 0.003 </value>
          <sum> <property> fcs/feather-pos-norm[0] </property> <property> fcs/feather-pos-norm[1] </property> </sum>
        </product>
      </function>
      <function name="aero/force/Drag_rudder">
        <description> Drag due to rudder deflection </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <abs> <property> fcs/rudder-pos-rad </property> </abs>
          <value> 0.030 </value>
        </product>
      </function>
      <function name="aero/force/Drag_mach">
        <description> Compressibility drag rise </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <table>
            <independentVar lookup="row"> velocities/mach </independentVar>
            <tableData>
              0.00  0.000
              0.55  0.000
              0.62  0.003
              0.70  0.012
              0.80  0.045
              1.00  0.120
            </tableData>
          </table>
        </product>
      </function>
    </axis>

    <axis name="SIDE">
      <function name="aero/force/Side_beta">
        <description> Side force due to sideslip </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> aero/beta-rad </property>
          <value> -0.60 </value>
        </product>
      </function>
      <function name="aero/force/Side_rudder">
        <description> Side force due to rudder </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> fcs/rudder-pos-rad </property>
          <value> 0.16 </value>
        </product>
      </function>
      <function name="aero/force/Side_yawrate">
        <description> Side force due to yaw rate </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> aero/bi2vel </property>
          <property> velocities/r-aero-rad_sec </property>
          <value> 0.30 </value>
        </product>
      </function>
    </axis>

    <axis name="ROLL">
      <function name="aero/moment/Roll_beta">
        <description> Dihedral effect (6 deg dihedral, winglets, T-tail fin) </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/bw-ft </property>
          <property> aero/beta-rad </property>
          <table>
            <independentVar lookup="row"> aero/alpha-rad </independentVar>
            <tableData>
              -0.10  -0.070
               0.00  -0.085
               0.10  -0.105
               0.20  -0.120
               0.35  -0.110
            </tableData>
          </table>
        </product>
      </function>
      <function name="aero/moment/Roll_damp">
        <description> Roll damping </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/bw-ft </property>
          <property> aero/bi2vel </property>
          <property> velocities/p-aero-rad_sec </property>
          <value> -0.50 </value>
        </product>
      </function>
      <function name="aero/moment/Roll_yaw">
        <description> Roll due to yaw rate </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/bw-ft </property>
          <property> aero/bi2vel </property>
          <property> velocities/r-aero-rad_sec </property>
          <sum>
            <value> 0.06 </value>
            <product> <value> 0.22 </value> <property> aero/coefficient/CL-basic </property> </product>
          </sum>
        </product>
      </function>
      <function name="aero/moment/Roll_aileron">
        <description> Roll due to ailerons (effective average deflection) </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/bw-ft </property>
          <property> fcs/aileron-eff-rad </property>
          <table>
            <independentVar lookup="row"> aero/alpha-rad </independentVar>
            <tableData>
              -0.10  0.100
               0.20  0.100
               0.30  0.070
               0.50  0.040
            </tableData>
          </table>
        </product>
      </function>
      <function name="aero/moment/Roll_rudder">
        <description> Roll due to rudder (fin above CG) </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/bw-ft </property>
          <property> fcs/rudder-pos-rad </property>
          <value> 0.018 </value>
        </product>
      </function>
    </axis>

    <axis name="PITCH">
      <function name="aero/moment/Pitch_alpha">
        <description> Pitch moment due to alpha (static margin about 25 % MAC) plus Cm0 </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/cbarw-ft </property>
          <table>
            <independentVar lookup="row"> aero/alpha-rad </independentVar>
            <tableData>
              -0.35   0.320
              -0.20   0.200
               0.00   0.040
               0.10  -0.050
               0.20  -0.140
               0.26  -0.190
               0.30  -0.250
               0.35  -0.320
               0.44  -0.420
               0.52  -0.500
               0.70  -0.600
               1.57  -0.800
            </tableData>
          </table>
        </product>
      </function>
      <function name="aero/moment/Pitch_flap">
        <description> Pitch moment due to flaps </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/cbarw-ft </property>
          <table>
            <independentVar lookup="row"> fcs/flap-pos-deg </independentVar>
            <tableData>
               0.0   0.000
              14.0  -0.060
              35.0  -0.170
            </tableData>
          </table>
        </product>
      </function>
      <function name="aero/moment/Pitch_elevator">
        <description> Pitch moment due to elevator </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/cbarw-ft </property>
          <property> fcs/elevator-pos-rad </property>
          <table>
            <independentVar lookup="row"> aero/alpha-rad </independentVar>
            <tableData>
              -0.20  -1.40
               0.25  -1.40
               0.35  -1.10
               0.60  -0.70
               1.57  -0.40
            </tableData>
          </table>
        </product>
      </function>
      <function name="aero/moment/Pitch_damp">
        <description> Pitch damping (T-tail) </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/cbarw-ft </property>
          <property> aero/ci2vel </property>
          <property> velocities/q-aero-rad_sec </property>
          <value> -30.0 </value>
        </product>
      </function>
      <function name="aero/moment/Pitch_alphadot">
        <description> Pitch moment due to alpha rate </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/cbarw-ft </property>
          <property> aero/ci2vel </property>
          <property> aero/alphadot-rad_sec </property>
          <value> -9.0 </value>
        </product>
      </function>
      <function name="aero/moment/Pitch_ge">
        <description> Nose-down moment in ground effect (tail downwash change) </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/cbarw-ft </property>
          <difference> <property> aero/function/kCLge </property> <value> 1.0 </value> </difference>
          <value> -0.25 </value>
        </product>
      </function>
    </axis>

    <axis name="YAW">
      <function name="aero/moment/Yaw_beta">
        <description> Weathercock stability </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/bw-ft </property>
          <property> aero/beta-rad </property>
          <value> 0.095 </value>
        </product>
      </function>
      <function name="aero/moment/Yaw_damp">
        <description> Yaw damping </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/bw-ft </property>
          <property> aero/bi2vel </property>
          <property> velocities/r-aero-rad_sec </property>
          <value> -0.16 </value>
        </product>
      </function>
      <function name="aero/moment/Yaw_rollrate">
        <description> Yaw due to roll rate </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/bw-ft </property>
          <property> aero/bi2vel </property>
          <property> velocities/p-aero-rad_sec </property>
          <sum>
            <value> 0.01 </value>
            <product> <value> -0.08 </value> <property> aero/coefficient/CL-basic </property> </product>
          </sum>
        </product>
      </function>
      <function name="aero/moment/Yaw_rudder">
        <description> Yaw due to rudder </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/bw-ft </property>
          <property> fcs/rudder-pos-rad </property>
          <value> -0.095 </value>
        </product>
      </function>
      <function name="aero/moment/Yaw_aileron">
        <description> Adverse yaw </description>
        <product>
          <property> aero/qbar-psf </property>
          <property> metrics/Sw-sqft </property>
          <property> metrics/bw-ft </property>
          <property> fcs/aileron-eff-rad </property>
          <sum>
            <value> -0.004 </value>
            <product> <value> -0.012 </value> <property> aero/coefficient/CL-basic </property> </product>
          </sum>
        </product>
      </function>
    </axis>

  </aerodynamics>

  <external_reactions>
    <force name="pushback" frame="BODY">
      <location unit="IN"> <x> {nose[0]:.1f} </x> <y> 0.0 </y> <z> {nose[2]+10:.1f} </z> </location>
      <direction> <x> -1.0 </x> <y> 0.0 </y> <z> 0.0 </z> </direction>
    </force>
  </external_reactions>

</fdm_config>
'''
pass
open('../Aero/KingAir-350ER.xml' if ER else '../Aero/KingAir-350.xml','w').write(xml)
print("MAC LE x = %.1f in, AERORP x = %.1f in, empty CG x = %.1f in (%.1f%% MAC)"%(MAC_LE_x,AERO_x,empty_cg_x,EMPTY_CG_PCT))
print("CG limits (in): fwd 7.8%%: %.1f, 19.3%%: %.1f, aft 31.7%%: %.1f"%(mac_x(7.8),mac_x(19.3),mac_x(31.7)))
