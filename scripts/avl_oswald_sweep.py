"""Sweep AVL over the planform family to measure span efficiency properly."""
import math, os, subprocess, json
from argus7.cad.airfoil_coords import load_airfoil
SP = os.environ["SP"]; AVL = "vendor/bin/avl"
open(f"{SP}/fx.dat","w").write("FX63137\n"+"".join(f"{x:12.7f}{y:12.7f}\n" for x,y in load_airfoil('fx63137')))

def deck(path, S, AR, taper, twist_tip, inc=2.0, dih=3.0, sweep=1.0, nsec=12):
    b=math.sqrt(AR*S); cr=S/((b/2)*(1+taper)); ct=taper*cr
    mac=(2/3)*cr*(1+taper+taper**2)/(1+taper); semi=b/2
    L=["sweep","0.0","0 0 0.0",f"{S:.5f} {mac:.5f} {b:.5f}",f"{0.25*mac:.5f} 0.0 0.0","0.0","",
       "SURFACE","Wing","12 1.0 24 -2.0","YDUPLICATE","0.0","ANGLE","0.0",""]
    for i in range(nsec):
        f=i/(nsec-1); y=f*semi; c=cr+f*(ct-cr)
        L+=["SECTION",f"{y*math.tan(math.radians(sweep)):.5f} {y:.5f} {y*math.tan(math.radians(dih)):.5f} {c:.5f} {inc+f*twist_tip:.4f} 0 0",
            "AFILE",f"{SP}/fx.dat",""]
    open(path,"w").write("\n".join(L)+"\n")

rows=[]
for AR in (14,18,22,26,30):
    for taper in (0.30,0.45,0.60):
        for tw in (0.0,-3.0,-6.0):
            p=f"{SP}/sw.avl"; deck(p,3.9,AR,taper,tw)
            out=subprocess.run([AVL],input=f"load {p}\noper\na c 1.21\nx\n",capture_output=True,text=True,timeout=180).stdout
            e=None
            for line in out.splitlines():
                if " e =" in line:
                    try: e=float(line.split(" e =")[1].split()[0])
                    except Exception: pass
            if e: rows.append({"AR":AR,"taper":taper,"twist_tip":tw,"e_inviscid":e})
            print(f"AR {AR:2d} taper {taper:.2f} twist {tw:5.1f} -> e = {e}", flush=True)
json.dump(rows, open("opt_runs/avl_oswald.json","w"), indent=2)
print(f"\nWROTE opt_runs/avl_oswald.json ({len(rows)} points)")
