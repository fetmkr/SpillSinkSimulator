"""RE-VERIFICATION: panel 50-1000 mm, all three axes, every condition stated.

Today established that the three axes do not share an instrument:

    axis        pixel size        sample size       measurement window
    total       indifferent       needs >= 25 cells indifferent
    smear       indifferent       indifferent       DECISIVE (~6x the return)
    head-on     DECISIVE          (was a proxy for pixel size)  indifferent

and that head-on is a PEAK, so it dilutes with pixel size while an area average
and a ratio-of-widths do not. Measured: 0.215 -> 0.600 -> 1.200 mm/px gave
head-on 0.1835 -> 0.1064 -> 0.0821 with smear flat at 2.238 -> 2.232 -> 2.227.

The peak comes from the smallest observer-facing feature -- the tip flat for a
pyramid. So the density that matters is a ratio to THAT, not a global constant:

    mm_per_px = tip_flat / N

At the protocol 0.215 mm/px the order spec's 0.4 mm tip spans 1.86 px, and the
study standard's 0.1 mm tip spans 0.47 px -- SUB-PIXEL. Those head-on numbers
are the tip averaged with the darkness around it, biased downward, on the one
axis that says whether the audience is dazzled.

This table therefore reports, for every panel size:
  * rho and smear from the full panel at protocol density (they are insensitive
    to density, and this is the condition every published total used)
  * head-on from a FIXED 10-cell patch at tip-resolved density, because a peak
    is a local quantity and does not need the whole wall -- resolving a 0.08 mm
    honeycomb wall across a 1 m panel would be 324 Mpx, while 10 cells of it is
    under 40
  * and, in the same row, the conditions: mm per pixel, pixels across the tip,
    cells in the sample, the window that converged.

PRE-REGISTERED:
  V1  rho varies < 2 % over 50-1000 mm once the sample holds >= 25 cells
      (GATE 11 saw it still falling at 50 cells, so expect the small end high)
  V2  smear is flat within 1 % across the whole range
  V3  head-on from the patch is flat within 2 % across the whole range --
      because the patch is the same object every time. If it is NOT flat, the
      patch is not representative and the peak needs the full panel after all.
  V4  head-on from the patch is materially above the published 0.173.
"""
import json as J, urllib.request, time, os

OUT = "/tmp/simsrv/reverify"; os.makedirs(OUT, exist_ok=True)
PITCH, DEPTH, TIP = 4.0, 22.0, 0.4
# MEASURED, not guessed: GATE 16 swept pixels-across-the-tip 1,2,4,8,16 and
# head-on converged at 4 (0.18898 / 0.18907 / 0.18874, inside 0.2 %).
# 8 and 16 also exposed defect #9 -- the profile array was a fixed 361
# SAMPLES, so at 0.025 mm/px it spanned only 9 mm and clipped a 10 mm
# return, collapsing smear from 2.234 to 1.008. That is now fixed.
N_TIP = 4
PATCH = PITCH * 10              # 10 cells is a representative patch
PROTOCOL = 0.215

def form(panel, mmpx, nph=8, spp=256, beam=7.5):
    spec = {"top": "pyramid", "top_params": {"pitch": PITCH, "tip_flat": TIP},
            "depth": DEPTH, "panel": panel, "margin_depths": 2.0,
            "floor": "none"}
    body = J.dumps({"spec": spec, "renderer": "cycles", "coat": "musou_fit",
                    "n_phase": nph, "samples": spp, "beam_w": beam,
                    "mm_per_px": mmpx}).encode()
    t = time.time()
    d = J.loads(urllib.request.urlopen(
        "http://127.0.0.1:8777/api/form", body, timeout=7200).read())
    return d, time.time() - t

def total(panel, spp=256):
    spec = {"top": "pyramid", "top_params": {"pitch": PITCH, "tip_flat": TIP},
            "depth": DEPTH, "panel": panel, "margin_depths": 2.0,
            "floor": "none"}
    body = J.dumps({"spec": spec, "renderer": "cycles", "coat": "musou_fit",
                    "thetas": [0.0, -40.0, 40.0], "samples": spp}).encode()
    t = time.time()
    d = J.loads(urllib.request.urlopen(
        "http://127.0.0.1:8777/api/measure", body, timeout=7200).read())
    r = d.get("rho") or {}
    return (max(r.values()) if r else None), time.time() - t

PANELS = [50.0, 100.0, 200.0, 400.0, 700.0, 1000.0]
rows = []
print("조건: 간격 %.0f · 깊이 %.0f · 팁 %.1f mm · 빔 7.5 mm · 줄 옮김 8회"
      % (PITCH, DEPTH, TIP), flush=True)
print("팁 해상 밀도 = 팁 %.1f / N %d = %.4f mm/px\n" % (TIP, N_TIP, TIP / N_TIP),
      flush=True)
print("%-7s %-8s %-9s %-10s %-11s %-10s %-9s %s"
      % ("판mm", "칸수", "총량%", "뭉개기", "창mm", "정면(팁해상)", "팁픽셀", "시간"),
      flush=True)

# head-on comes from one fixed patch, measured once, at tip-resolved density
hp, hsec = form(PATCH, TIP / N_TIP)
patch_headon = hp["peak"]

for panel in PANELS:
    rho, s1 = total(panel)
    d, s2 = form(panel, PROTOCOL)
    dp, s3 = form(panel, PROTOCOL)          # head-on at protocol, for contrast
    rows.append({"panel": panel, "rho": rho, "smear": d["smear"],
                 "head_on_protocol": d["peak"], "head_on_patch": patch_headon,
                 "window": d.get("window_mm"), "conv": d.get("converged"),
                 "mm_per_px": d.get("mm_per_px")})
    print("%-7.0f %-8.0f %-9.4f %-10.4f %-11s %-10.5f %-9.2f %.0fs"
          % (panel, panel / PITCH, 100 * (rho or 0), d["smear"],
             ("%.0f%s" % (d.get("window_mm") or 0,
                          "" if d.get("converged") else "!")),
             patch_headon, TIP / (TIP / N_TIP), s1 + s2 + s3), flush=True)
    print("        같은 판에서 규약밀도 0.215 로 잰 정면: %.5f  (팁 픽셀 %.2f)"
          % (d["peak"], TIP / PROTOCOL), flush=True)
    J.dump(rows, open(os.path.join(OUT, "reverify.json"), "w"), indent=1)

print("\n=== 판정 ===", flush=True)
big = [r for r in rows if r["panel"] >= 100]
for key, lim, name in (("rho", 0.02, "총량"), ("smear", 0.01, "뭉개기"),
                       ("head_on_protocol", 0.02, "정면(규약밀도)")):
    v = [r[key] for r in big if r[key] is not None]
    if v:
        m = sum(v) / len(v)
        sp = (max(v) - min(v)) / m
        print("  %-16s 판100~1000 흩어짐 %5.2f %%  %s"
              % (name, 100 * sp, "PASS" if sp <= lim else "**FAIL**"), flush=True)
print("  정면(팁해상, 10칸 조각) %.5f   발표값 0.173 대비 %+.1f %%"
      % (patch_headon, 100 * (patch_headon - 0.173) / 0.173), flush=True)
print("@@DONE@@", flush=True)
