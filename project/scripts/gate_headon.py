"""GATE 15: when is head-on quotable?

Two independent measurements today say the same thing: head-on is a PEAK and a
peak dilutes with pixel size, while the other two axes do not.

  density 0.215 -> 0.600 -> 1.200 mm/px : head-on 0.1835 -> 0.1064 -> 0.0821
                                          smear    2.238 ->  2.232 ->  2.227
  the old RES_CAP on a 1000 mm panel    : head-on -13.3 %, rho +0.02 %, smear +0.21 %

And the panel ladder showed it also moves with SAMPLE size: 0.1776 at 100 mm,
0.1850 at 300 mm, 0.1846 at 500 mm.

Both biases point the same way -- DOWNWARD -- which is the dangerous direction:
head-on is the axis that says whether the audience is dazzled, so reading it low
makes a design look safer than it is.

So map both axes of the bias at once and find the conditions under which the
number stops moving.

PRE-REGISTERED:
  H1  at fixed sample, head-on rises as density gets finer and flattens; find
      where. I expect it to need FINER than the 0.215 protocol, because a peak
      keeps sharpening until the pixel is small against the tip.
  H2  at fixed density, head-on rises with sample and flattens by ~200 mm, as
      the ladder hinted.
  H3  the converged value is the same by either route -- if fine density on a
      small sample and protocol density on a large one disagree, there are two
      separate effects and not one.
  H4  smear stays flat over the whole grid (it already did on both axes
      separately), confirming the two axes need different quoting rules.
"""
import os, sys, json
HERE=os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0,HERE)
import json as J, urllib.request, time  # noqa: E402

OUT="/tmp/simsrv/headon"; os.makedirs(OUT,exist_ok=True)
BASE={"top":"pyramid","top_params":{"pitch":4.0,"tip_flat":0.4},
      "depth":22.0,"margin_depths":2.0,"floor":"none"}

def call(panel, mmpx, nph=8, spp=256):
    spec=dict(BASE, panel=panel)
    body=J.dumps({"spec":spec,"renderer":"cycles","coat":"musou_fit",
                  "n_phase":nph,"samples":spp,"beam_w":7.5,
                  "mm_per_px":mmpx}).encode()
    t=time.time()
    d=J.loads(urllib.request.urlopen(
        "http://127.0.0.1:8777/api/form",body,timeout=7200).read())
    return d, time.time()-t

rows=[]
print("=== H1/H2: head-on over sample x density ===",flush=True)
print("%-8s %-9s %-10s %-10s %s" % ("판","밀도","정면","뭉개기","시간"),flush=True)
for panel in (100.0, 200.0, 400.0):
    for mmpx in (0.430, 0.215, 0.108):
        d,sec=call(panel,mmpx)
        rows.append({"panel":panel,"mmpx":mmpx,"head_on":d["peak"],
                     "smear":d["smear"],"sec":sec})
        print("%-8.0f %-9.3f %-10.5f %-10.4f %.0fs"
              % (panel,mmpx,d["peak"],d["smear"],sec),flush=True)
        J.dump(rows,open(os.path.join(OUT,"headon.json"),"w"),indent=1)
    print("",flush=True)

print("=== verdicts ===",flush=True)
for panel in (100.0,200.0,400.0):
    v=[r for r in rows if r["panel"]==panel]
    if len(v)>=2:
        a,b=v[-2]["head_on"],v[-1]["head_on"]
        print("  판 %-6.0f 밀도 0.215 -> 0.108 : %+6.2f %%  %s"
              % (panel,100*(b-a)/a,"converged" if abs(b-a)/b<=0.02 else "STILL MOVING"),
              flush=True)
fine=[r for r in rows if abs(r["mmpx"]-0.108)<1e-6]
if len(fine)>=2:
    vals=[r["head_on"] for r in fine]
    print("  가장 고운 밀도에서 판 100->400 : %+6.2f %%"
          % (100*(vals[-1]-vals[0])/vals[0]),flush=True)
sm=[r["smear"] for r in rows]
print("  모양 뭉개기 전체 흩어짐 : %.2f %%  %s"
      % (100*(max(sm)-min(sm))/(sum(sm)/len(sm)),
         "H4 PASS" if (max(sm)-min(sm))/(sum(sm)/len(sm))<=0.02 else "H4 FAIL"),flush=True)
print("@@DONE@@",flush=True)
