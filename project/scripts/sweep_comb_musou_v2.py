"""Bought honeycomb foil, painted 5 % all over, Musou only in the top few mm.

The buyer's real choice, laid out so it can be read off a chart:

    cell        6.35, 9.53 mm      the two foils actually stocked
    depth       30, 40, 50, 60 mm
    Musou       0, 5, 10, 15 mm from the tip down; 0 is the control that says
                whether the black paint is worth buying at all
    panel       200 x 200 mm       >= 21 cells even for the 9.53 foil
    foil        0.08 mm
    base        5 % reflectance paint on the panel and on the comb

32 cases:
    total reflectance at theta 0, +-20, +-40, WORST of phi 0/45/90
    head-on peak (the flash back at the projector) -- 10-cell patch, 5 s

Head-on is read on a patch ten cells across rather than the whole 200 mm panel.
Measured, not assumed: 8.22411 on the patch against 8.22378 on the full panel,
and 5 s against 75 s. Head-on is a LOCAL event -- the flash comes off one wall
edge -- so a patch that contains many cells contains the whole phenomenon.

Smear is NOT measured here, and that is a deliberate cut. It needs the full
panel at three angles (the expensive part, ~70 s a case) and it has nothing to
say about this question: paint changes how much light returns, not where it
lands. Today's floor-coating sweep moved smear by 0.0 % across four finishes.
Smear gets measured on the two or three finalists, not on all 32.

The head-on axis is why the Musou band exists. A dark rim near the mouth is
supposed to kill the flash off the top edge of the wall; the total will barely
notice it, because the rim is a sliver of the panel's area. Reading the total
alone would say the paint does nothing. That mistake has already been made once
in this project, today.

PRE-REGISTERED:
  M1  total is nearly flat in Musou depth. The rim is a few percent of the wall
      area and the total is an area average.
  M2  head-on FALLS with Musou depth, and most of the fall happens by 5 mm --
      the flash comes off the mouth, not the floor.
  M3  head-on falls with cell depth as well, but the two do not simply add: on
      a deep cell the mouth is already the only lit part, so the Musou band
      should matter MORE there, not less.
  M5  the 9.53 cell is worse than the 6.35 on head-on at equal depth, because
      a wider mouth shows more of its own wall to an observer on the axis.
"""
import os, sys, json, time, math
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = "/tmp/simsrv/comb_musou_v2"
os.makedirs(OUT, exist_ok=True)
JSONF = os.path.join(OUT, "comb_musou_v2.json")

PITCHES = [6.35, 9.53]
DEPTHS = [30.0, 40.0, 50.0, 60.0]
MUSOU = [0.0, 5.0, 10.0, 15.0]
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
PANEL = 200.0
FOIL = 0.08
BASE = "wall_5pct"      # 5 % 무광 검정, 확산 0.99 (Zeng 2019)
SLIDER = math.sqrt(0.039)   # MERL paint-black alpha 0.039.
# 렌더러가 슬라이더를 제곱해서 alpha 로 쓴다. 2026-08-22 이전 판은
# 0.30 을 넣었고 그건 alpha 0.09 였다.
SPP = 256

rows = []
if os.path.exists(JSONF):                       # resumable
    rows = json.load(open(JSONF))
done = {(r["pitch"], r["depth"], r["musou"]) for r in rows}

print("벌집 포일 %.2f mm, 판 %.0f x %.0f, 바탕 5 %% 페인트." % (FOIL, PANEL, PANEL),
      flush=True)
print("무소는 팁에서부터 아래로 칠한 깊이입니다. 0 은 안 칠한 경우.\n", flush=True)
hdr = ("%-6s %-6s %-6s | %-9s %-9s %-9s | %-9s %s"
       % ("셀", "깊이", "무소", "0도", "20도", "40도", "번쩍임", "시간"))
print(hdr, flush=True)
print("-" * len(hdr), flush=True)

for pitch in PITCHES:
    for depth in DEPTHS:
        for mus in MUSOU:
            if (pitch, depth, mus) in done:
                continue
            t0 = time.time()
            spec = {"top": "comb",
                    "top_params": {"pitch": pitch, "wall_top": FOIL,
                                   "wall_bot": FOIL, "comb_expand": 1.0,
                                   "jitter": 0.0},
                    "depth": depth, "floor": "none", "panel": PANEL}
            if mus > 0:
                kw = dict(coating="musou_fit", deep_coating=BASE,
                          paint_depth=mus)
            else:
                kw = dict(coating=BASE)
            # THREE AZIMUTH PLANES, worst of them. The first run took the
            # phi = 0 plane alone, which is `measure`'s default, and reported
            # it as the panel's number. The project's own standard is the
            # worst of phi 0/45/90 -- the dashboard has always done that -- and
            # for this comb the diagonal planes read up to 15 % HIGHER at 40
            # degrees (0.813 -> 0.907). Head-on barely moves (0.291 -> 0.294),
            # which is why the error hid: the column being argued about was
            # the one column it did not touch.
            # 확산 비율을 넘기지 않는다: 재료마다 자기 값을 쓴다.
            # 5 % 무광 검정 0.97, 무소 0.76. 전에는 판 전체에 0.76 하나였다.
            planes = SS.measure(spec, THETAS, None, SLIDER, SPP,
                                phis=[0.0, 45.0, 90.0], **kw)
            tot = {k: max(planes[p][k] for p in planes) for k in planes["0"]}
            tot_phi0 = planes["0"]
            # head-on on a 10-cell patch: same number, 15x less time
            patch = dict(spec, panel=pitch * 10.0)
            f = SS.form(patch, thetas=[0.0], n_phase=6, samples=SPP,
                        beam_w=7.5, diffuse_frac=None,
                        roughness=SLIDER, **kw)
            pk = f.get("peak")
            vals = {("%.0f" % t): tot.get("%.0f" % t) for t in THETAS}
            if pk is None or any(v is None for v in vals.values()):
                raise SystemExit("빈 칸 (셀 %.2f 깊이 %.0f 무소 %.0f) -- 결과로 "
                                 "인정 안 함" % (pitch, depth, mus))
            sec = time.time() - t0
            rows.append({"pitch": pitch, "depth": depth, "musou": mus,
                         "total": vals,
                         "total_phi0": {("%.0f" % t): tot_phi0.get("%.0f" % t)
                                        for t in THETAS},
                         "phis": [0, 45, 90], "peak": pk,
                         "panel": PANEL, "foil": FOIL, "base": BASE,
                         "alpha": 0.039, "slider": SLIDER,
                         "sec": round(sec, 1)})
            json.dump(rows, open(JSONF, "w"), indent=1, ensure_ascii=False)
            print("%-6.2f %-6.0f %-6.0f | %9.5f %9.5f %9.5f | %9.5f %.0f초"
                  % (pitch, depth, mus, vals["0"],
                     max(vals["-20"], vals["20"]), max(vals["-40"], vals["40"]),
                     pk, sec), flush=True)
print("\n%d 가지 완료. 표: %s" % (len(rows), JSONF), flush=True)
print("@@DONE@@", flush=True)
