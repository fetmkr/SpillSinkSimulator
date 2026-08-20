"""Honeycomb AND pyramid, every panel size, all three axes, conditions stated.

Why both families, and why size: today showed the three axes need different
instruments, and that head-on -- a PEAK -- is set by the smallest feature that
faces the observer. That feature differs by family, and the honeycomb's is far
smaller than the pyramid's:

    pyramid p4 / tip 0.4     min feature 0.400 mm   1.86 px at the 0.215 protocol
    pyramid p4 / tip 0.1     min feature 0.100 mm   0.47 px   SUB-PIXEL
    honeycomb 6.5 / wall .08 min feature 0.080 mm   0.37 px   SUB-PIXEL

So the honeycomb's published head-on (1.639, "the same as a flat plate") was
measured with its wall spanning about a third of a pixel: the wall's brightness
averaged with the dark cell beside it. That number decided a ranking.

Reported per row, with nothing implicit:
    cells across, mm per pixel, pixels across the min feature,
    the window that converged, and whether it converged.

PRE-REGISTERED:
  S1  pyramid total varies < 2 % for >= 25 cells; honeycomb likewise
  S2  smear is flat with size in both families (it was for the pyramid over
      50-500 mm at 0.05 %)
  S3  head-on at the protocol density FALLS as the panel grows in both
      families, because mm-per-pixel is fixed but the feature is not resolved
  S4  the honeycomb's head-on is biased WORSE than the pyramid's, since its
      wall is 5x further sub-pixel than the order spec's tip
"""
import json as J, urllib.request, time, os

OUT = "/tmp/simsrv/famsize"; os.makedirs(OUT, exist_ok=True)
PROTOCOL = 0.215

FAMILIES = {
    "pyramid p4/d22/t0.4": dict(top="pyramid", depth=22.0,
                                tp={"pitch": 4.0, "tip_flat": 0.4},
                                pitch=4.0, feat=0.4),
    "pyramid p4/d20/t0.1": dict(top="pyramid", depth=20.0,
                                tp={"pitch": 4.0, "tip_flat": 0.1},
                                pitch=4.0, feat=0.1),
    "honeycomb 6.5/w0.08": dict(top="honeycomb", depth=30.0,
                                tp={"pitch": 6.5, "wall_top": 0.08,
                                    "wall_bot": 0.08, "jitter": 0.0},
                                pitch=6.5, feat=0.08),
}
PANELS = [50.0, 100.0, 200.0, 400.0, 700.0, 1000.0]


def call_form(fam, panel, mmpx):
    spec = {"top": fam["top"], "top_params": fam["tp"], "depth": fam["depth"],
            "panel": panel, "margin_depths": 2.0, "floor": "none"}
    body = J.dumps({"spec": spec, "renderer": "cycles", "coat": "musou_fit",
                    "n_phase": 8, "samples": 256, "beam_w": 7.5,
                    "mm_per_px": mmpx}).encode()
    t = time.time()
    d = J.loads(urllib.request.urlopen(
        "http://127.0.0.1:8777/api/form", body, timeout=10800).read())
    return d, time.time() - t


def call_total(fam, panel):
    spec = {"top": fam["top"], "top_params": fam["tp"], "depth": fam["depth"],
            "panel": panel, "margin_depths": 2.0, "floor": "none"}
    body = J.dumps({"spec": spec, "renderer": "cycles", "coat": "musou_fit",
                    "thetas": [0.0, -40.0, 40.0], "samples": 256}).encode()
    t = time.time()
    d = J.loads(urllib.request.urlopen(
        "http://127.0.0.1:8777/api/measure", body, timeout=10800).read())
    r = d.get("rho") or {}
    return (max(r.values()) if r else None), time.time() - t


rows = []
for name, fam in FAMILIES.items():
    print("\n===== %s  (최소 피처 %.2f mm) =====" % (name, fam["feat"]),
          flush=True)
    print("%-7s %-7s %-9s %-9s %-11s %-9s %-8s %s"
          % ("판mm", "칸수", "총량%", "뭉개기", "창mm", "정면", "피처px", "시간"),
          flush=True)
    for panel in PANELS:
        try:
            rho, s1 = call_total(fam, panel)
            d, s2 = call_form(fam, panel, PROTOCOL)
        except Exception as e:
            print("%-7.0f  실패: %s" % (panel, repr(e)[:90]), flush=True)
            continue
        featpx = fam["feat"] / (d.get("mm_per_px") or PROTOCOL)
        rows.append({"family": name, "panel": panel, "rho": rho,
                     "smear": d["smear"], "head_on": d["peak"],
                     "window": d.get("window_mm"),
                     "converged": d.get("converged"),
                     "mm_per_px": d.get("mm_per_px"), "feat_px": featpx})
        print("%-7.0f %-7.0f %-9.4f %-9.4f %-11s %-9.5f %-8.2f %.0fs"
              % (panel, panel / fam["pitch"], 100 * (rho or 0), d["smear"],
                 "%.0f%s" % (d.get("window_mm") or 0,
                             "" if d.get("converged") else "!"),
                 d["peak"], featpx, s1 + s2), flush=True)
        J.dump(rows, open(os.path.join(OUT, "famsize.json"), "w"), indent=1)

print("\n===== 판정 (판 100 이상) =====", flush=True)
for name in FAMILIES:
    v = [r for r in rows if r["family"] == name and r["panel"] >= 100]
    if len(v) < 2:
        continue
    for key, lim, label in (("rho", 0.02, "총량"), ("smear", 0.01, "뭉개기"),
                            ("head_on", 0.02, "정면")):
        x = [r[key] for r in v if r[key] is not None]
        if not x:
            continue
        m = sum(x) / len(x)
        sp = (max(x) - min(x)) / m
        print("  %-22s %-8s 흩어짐 %6.2f %%  %s"
              % (name, label, 100 * sp,
                 "PASS" if sp <= lim else "**FAIL**"), flush=True)
print("@@DONE@@", flush=True)
