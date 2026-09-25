# PT6A-60A turboprop for JSBSim (FGTurboProp). Power vs N1 at 1700 rpm, scaled by the free-turbine rpm curve.
import numpy as np
N1=[0,5,15,30,45,55,62,66,70,75,80,85,90,95,100,104,110]
P1700=[0,0.5,2,6,14,25,35,50,85,165,300,480,690,880,1040,1100,1100]
rpms=[0,300,600,900,1200,1500,1700,1900,2200]
def f(rpm):
    x=rpm/1700.0
    return max(x*(2-x),0.0) if rpm<=2200 else 0
rows=""
for r in rpms:
    fac=f(r) if r>0 else 0.0
    vals=[ (0.5 if (p>0 and r==0) else p*fac) for p in P1700]
    # keep a small positive value at N1>=5 so that the starter can spin the prop (JSBSim needs >0)
    vals=[max(v,0.5) if n>=5 else 0.0 for v,n in zip(vals,N1)]
    rows+=f"      {r:5d}  "+" ".join(f"{v:7.1f}" for v in vals)+"\n"
hdr="             "+" ".join(f"{n:7d}" for n in N1)
xml=f'''<?xml version="1.0"?>
<!--
  Pratt & Whitney Canada PT6A-60A (Beechcraft King Air 350 / B300)
  1050 shp flat rated (ISA+10 C at sea level), N1 idle 62% (low idle) / max 104%,
  propeller 1450-1700 rpm, 100% torque = 3200 ft.lb at 1700 rpm, ITT limit 820 C (T/O, MCP).
  JSBSim FGTurboProp model: power = EnginePowerRPM_N1(prop rpm, N1) * EnginePowerVC(pressure, speed, temperature), clipped at maxpower.
  Fuel flow = psfc / CombustionEfficiency_N1(N1) * power.
  Sources: Beechcraft B300 spec & description, TCDS A24CE (Model 300 PT6A-60A limits), operator limitation sheets.
-->
<turboprop_engine name="PT6A-60A">
  <milthrust unit="LBS">      3300.0 </milthrust>
  <idlen1>                      62.0  </idlen1>
  <maxn1>                      104.0  </maxn1>
  <maxpower unit="HP">        1050.0  </maxpower>
  <psfc unit="LBS/HR/HP">        0.52 </psfc>
  <n1idle_max_delay>             1.3  </n1idle_max_delay>
  <maxstartingtime>             45    </maxstartingtime>
  <startern1>                   22    </startern1>
  <ielumaxtorque unit="FT*LB">  -1    </ielumaxtorque>
  <itt_delay>                    2.5  </itt_delay>
  <betarangeend>                35    </betarangeend>
  <reversemaxpower>             65    </reversemaxpower>

  <!-- Power available factor: pressure altitude (rows, P-psf), equivalent airspeed (columns, kt),
       multiplied by a temperature factor (about -1.1 %/degC above ISA). The flat rating is obtained by
       the maxpower clip: 1100 hp * factor > 1050 below ~12000 ft ISA. -->
  <function name="EnginePowerVC">
    <product>
      <table>
        <independentVar lookup="row">atmosphere/P-psf</independentVar>
        <independentVar lookup="column">velocities/ve-kts</independentVar>
        <tableData>
                    0      100     200     300
          400    0.300   0.310   0.323   0.336
          498    0.385   0.397   0.414   0.431
          552    0.445   0.459   0.478   0.497
          629    0.550   0.567   0.590   0.612
          686    0.610   0.628   0.653   0.680
          786    0.725   0.747   0.777   0.808
          973    0.825   0.850   0.884   0.916
         1194    0.895   0.922   0.959   0.993
         1456    0.990   1.020   1.060   1.100
         1761    1.060   1.092   1.135   1.180
         2116    1.120   1.155   1.200   1.245
        </tableData>
      </table>
      <!-- temperature factor: 1 - 0.011 * (T - T_ISA) [degC]; T_ISA from pressure altitude -->
      <max>
        <value>0.55</value>
        <difference>
          <value>1.0</value>
          <product>
            <value>0.011</value>
            <difference>
              <product><value>0.5555556</value><difference><property>atmosphere/T-R</property><value>491.67</value></difference></product>
              <difference>
                <value>15.0</value>
                <product><value>0.0019812</value><max><value>0</value><min><property>position/h-sl-ft</property><value>36089</value></min></max></product>
              </difference>
            </difference>
          </product>
        </difference>
      </max>
    </product>
  </function>

  <table name="EnginePowerRPM_N1" type="internal">
    <description> Shaft power (hp) vs propeller rpm (rows) and N1 (columns, %) </description>
    <tableData>
{hdr}
{rows}    </tableData>
  </table>

  <table name="ITT_N1" type="internal">
    <description> ITT (deg C) vs N1 (%) for engine off (0) and running (1) </description>
    <tableData>
              0     1
        0     0     0
       20    40   250
       40    60   480
       62    80   560
       70    90   600
       80   100   660
       90   110   725
      100   120   785
      104   125   805
      110   130   900
      120   140  1000
    </tableData>
  </table>

  <table name="CombustionEfficiency_N1" type="internal">
    <description> Fuel efficiency multiplier vs N1: fuel flow = psfc / eff * power </description>
    <tableData>
       50   0.12
       62   0.17
       66   0.22
       70   0.33
       75   0.52
       80   0.68
       85   0.80
       90   0.90
       95   0.97
      100   1.04
      104   1.06
      110   1.06
    </tableData>
  </table>
</turboprop_engine>
'''
import os
open('../Engines/PT6A-60A.xml','w').write(xml)
print(xml[:200]); print("ok")
