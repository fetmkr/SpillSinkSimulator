"""GATE 16: how many pixels does the smallest observer-facing feature need?

Head-on brightness is a PEAK, and the peak comes from whatever faces the
observer: a pyramid's tip flat, a honeycomb's wall top, a blade's edge. So the
sampling density that matters is not a global constant but a ratio to the
MINIMUM FEATURE -- which this project already computes, for buildability, and
has never used optically.

Where the protocol density stands today:

    design                    min feature   pixels across it at 0.215 mm/px
    pyramid p4 / tip 0.4      0.400 mm      1.86
    pyramid p4 / tip 0.1      0.100 mm      0.47
    honeycomb wall 0.08       0.080 mm      0.37
    blade 0.1                 0.100 mm      0.47

Three of those are SUB-PIXEL. Their published head-on is not the brightness of
the feature, it is the feature averaged with the darkness around it. And the
bias runs downward, which is the dangerous direction on the one axis that says
whether the audience is dazzled.

This finds N in  mm_per_px = min_feature / N  by measurement rather than by my
guess of 8. One design, sample fixed, density swept as a multiple of its own
tip. Head-on must climb and then flatten; where it flattens is N.

PRE-REGISTERED:
  N1  head-on rises monotonically with N and flattens. Today's density sweep
      already showed the rising half: 0.0821 -> 0.1064 -> 0.1835 going
      1.200 -> 0.600 -> 0.215 mm/px, i.e. N = 0.33 -> 0.67 -> 1.86.
  N2  it flattens by N = 8-16. If it is still moving at 32, a rasterised peak
      is the wrong instrument for this axis and it needs a ray-count estimator
      instead.
  N3  smear and rho stay flat across the whole sweep -- they already did over
      5.6x of density, and this extends that to ~40x.
  N4  the converged head-on is materially above the published 0.173. If so,
      every head-on number in the project is low, and the finer the design the
      worse: tip 0.1 is 4x further sub-pixel than tip 0.4.
"""
import json as J, urllib.request, time, os

OUT="/tmp/simsrv/featpx"; os.makedirs(OUT,exist_ok=True)
BASE={"top":"pyramid","top_params":{"pitch":4.0,"tip_flat":0.4},
      "depth":22.0,"panel":100.0,"margin_depths":2.0,"floor":"none"}
TIP=0.4

def call(mmpx, nph=8, spp=256):
    body=J.dumps({"spec":BASE,"renderer":"cycles","coat":"musou_fit",
                  "n_phase":nph,"samples":spp,"beam_w":7.5,
                  "mm_per_px":mmpx}).encode()
    t=time.time()
    d=J.loads(urllib.request.urlopen(
        "http://127.0.0.1:8777/api/form",body,timeout=7200).read())
    return d, time.time()-t

rows=[]
print("발주 사양 팁 0.4 mm — 팁 하나에 픽셀 몇 개를 주면 정면 반짝임이 멈추는가",flush=True)
print("%-6s %-10s %-10s %-10s %-9s %s" % ("N","밀도","정면","뭉개기","화면px","시간"),flush=True)
prev=None
for N in (1, 2, 4, 8, 16, 32):
    mmpx = TIP / N
    d,sec = call(mmpx)
    ch = "" if prev is None else " (%+.1f %%)" % (100*(d["peak"]-prev)/prev)
    rows.append({"N":N,"mmpx":mmpx,"head_on":d["peak"],"smear":d["smear"],"sec":sec})
    print("%-6d %-10.4f %-10.5f%-10s %-9s %.0fs"
          % (N, mmpx, d["peak"], ch, "-", sec),flush=True)
    print("       뭉개기 %.4f" % d["smear"],flush=True)
    prev=d["peak"]
    J.dump(rows,open(os.path.join(OUT,"featpx.json"),"w"),indent=1)

print("\n=== 판정 ===",flush=True)
for i in range(1,len(rows)):
    a,b=rows[i-1]["head_on"],rows[i]["head_on"]
    if abs(b-a)/b <= 0.02:
        print("  정면 반짝임 수렴: N = %d (밀도 %.4f mm/px), 값 %.5f"
              % (rows[i]["N"], rows[i]["mmpx"], b),flush=True)
        break
else:
    print("  **N = 32 에서도 안 멈춤 — 픽셀로 봉우리를 재는 방식 자체가 부적합**",flush=True)
sm=[r["smear"] for r in rows]
print("  모양 뭉개기 흩어짐 %.2f %%  %s"
      % (100*(max(sm)-min(sm))/(sum(sm)/len(sm)),
         "N3 PASS" if (max(sm)-min(sm))/(sum(sm)/len(sm))<=0.02 else "N3 FAIL"),flush=True)
print("  발표값 0.173 대비 수렴값: %+.1f %%" % (100*(rows[-1]["head_on"]-0.173)/0.173),flush=True)
print("@@DONE@@",flush=True)
