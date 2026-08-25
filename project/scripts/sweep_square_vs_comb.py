# -*- coding: utf-8 -*-
"""사각 격자가 육각 벌집보다 나은가. 같은 간격 9.53, 같은 깊이 40.

왜 재나. 2026-08-25 에 나온 생각이다. 사각 셀은 평평한 날을 슬롯으로 끼워
만들 수 있으니, 날을 **미리 칠하고 나서 조립**하면 된다. 관 안쪽을 칠하는
문제가 아예 사라진다. 바닥판도 따로 칠해 붙이면 된다.

광학적으로도 다를 근거가 있다. 수학적으로는 육각과 사각의 벽 길이가 같지만
(`2/간격`, geom_cell.py 의 wall_length_density 주석), **펼쳐 만든 벌집은
붙인 자리가 포일 두 겹**이라 테두리가 더 넓다. 앱의 기하 계산으로
같은 간격 9.5 / 벽 0.08 에서

    사각 격자   1.68 %      = 2t/p, 벽이 전부 홑겹
    펼친 벌집   2.25 %      붙인 자리가 두 겹

테두리가 정면 반사의 절반을 맡으므로 그대로면 사각이 유리하다.

반대 방향의 걱정도 있다. 사각 셀은 모서리가 **90 도**다. 직각으로 만난 두
벽은 빛을 온 방향으로 되돌려 보낸다(코너 리플렉터). 육각은 120 도라
그렇지 않다. 두 번 튕기며 도료가 두 번 먹으니 크지 않을 것 같지만 [추측],
이건 재서 정할 일이다. 그래서 공식이 아니라 실제 반사를 잰다.

    A  바닥판 못 칠함 -- 위에서 15 mm 만 무소, 나머지는 5 % 도료
    B  바닥판까지 칠함 -- 전부 무소. 격자는 원래 이쪽이 쉽다.

세 축을 다 잰다.

    zsh scripts/run_batch.sh scripts/sweep_square_vs_comb.py sqvscomb
"""
import os
import sys
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "comb_depth")
os.makedirs(OUT, exist_ok=True)
PATH = os.path.join(OUT, "square_vs_comb.json")

PITCH, DEPTH, PANEL = 9.53, 40.0, 200.0
BASE, TOP = "wall_5pct", "musou_fit"
SLIDER, SAMPLES = 0.19748417658131498, 512
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
PHIS = [0, 45, 90]
SPRAY = 15.0
WALLS = [0.04, 0.08]
SMEAR_WALL = 0.08          # 뭉개기는 한 점에 5 분이라 한 두께만


def spec(family, wall, panel=None):
    if family == "comb":
        tp = {"pitch": PITCH, "wall_top": wall, "wall_bot": wall,
              "comb_expand": 1.0, "jitter": 0.0}
    else:
        # 사각 격자. jitter 는 반드시 0 -- 기본값 0.30 은 꼭짓점을 흔들어
        # 셀을 찌그러뜨린다. 슬롯으로 끼운 격자는 반듯하다.
        tp = {"pitch": PITCH, "wall_top": wall, "wall_bot": wall,
              "jitter": 0.0}
    return {"top": family, "top_params": tp, "depth": DEPTH,
            "panel": panel or PANEL, "floor": "none", "margin_depths": 0.2}


def arms(kind):
    if kind == "A":
        return dict(coating=TOP, deep_coating=BASE, paint_depth=SPRAY)
    return dict(coating=TOP)


rows = []
print("같은 간격 %.2f mm / 깊이 %.0f mm. A = 바닥판 못 칠함, B = 칠함.\n"
      % (PITCH, DEPTH), flush=True)
print("%-8s %-6s %-3s | %10s %10s %10s | %8s | %5s"
      % ("모양", "벽", "칠", "총량 정면", "총량 20도", "총량 40도",
         "반짝임", "초"), flush=True)

for family in ("comb", "square"):
    for wall in WALLS:
        for kind in ("A", "B"):
            t0 = time.time()
            kw = arms(kind)
            planes = SS.measure(spec(family, wall), THETAS, None, SLIDER,
                                SAMPLES, phis=PHIS, **kw)
            tot = {k: max(planes[p][k] for p in planes) for k in planes["0"]}
            f = SS.form(spec(family, wall, panel=PITCH * 10.0), thetas=[0.0],
                        n_phase=6, samples=SAMPLES, beam_w=7.5,
                        diffuse_frac=None, roughness=SLIDER, **kw)
            pk = f.get("peak")
            if pk is None or tot.get("0") is None:
                raise SystemExit("빈 칸 (%s 벽 %.2f %s) -- 인정 안 함"
                                 % (family, wall, kind))
            rows.append({"family": family, "pitch": PITCH, "depth": DEPTH,
                         "wall": wall, "arm": kind,
                         "spray_mm": SPRAY if kind == "A" else DEPTH,
                         "base": BASE, "top": TOP, "alpha": 0.039,
                         "slider": SLIDER, "samples": SAMPLES,
                         "total": tot, "planes": planes, "head_on": pk,
                         "smear": None, "sec": round(time.time() - t0, 1)})
            json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
            print("%-8s %-6.2f %-3s | %9.5f%% %9.5f%% %9.5f%% | %8.4f | %5.0f"
                  % (family, wall, kind, 100 * tot["0"], 100 * tot["20"],
                     100 * tot["40"], pk, rows[-1]["sec"]), flush=True)

by = {(r["family"], r["wall"], r["arm"]): r for r in rows}
print("\n모양 뭉개기 -- 벽 %.2f mm, 바닥판까지 칠한 경우 (한 점에 5 분)\n"
      % SMEAR_WALL, flush=True)
print("%-8s | %8s | %6s | %5s" % ("모양", "뭉개기", "담겼나", "초"), flush=True)
for family in ("comb", "square"):
    t0 = time.time()
    fm = SS.form(spec(family, SMEAR_WALL), thetas=[-40.0, 40.0], n_phase=6,
                 samples=SAMPLES, phis=PHIS, **arms("B"))
    r = by[(family, SMEAR_WALL, "B")]
    r["smear"] = fm.get("smear")
    r["smear_converged"] = fm.get("converged")
    r["smear_n_phase"] = 6
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
    print("%-8s | %8s | %6s | %5.0f"
          % (family, ("%.4f" % r["smear"]) if r["smear"] is not None else "-",
             r["smear_converged"], time.time() - t0), flush=True)

print("\n사각이 벌집보다 몇 배 어두운가 (1 보다 크면 사각이 낫다)", flush=True)
for wall in WALLS:
    for kind in ("A", "B"):
        c, s = by[("comb", wall, kind)], by[("square", wall, kind)]
        print("  벽 %.2f %s: 정면 %.2f 배 · 20도 %.2f 배 · 40도 %.2f 배 · "
              "반짝임 %.2f 배"
              % (wall, kind,
                 c["total"]["0"] / s["total"]["0"],
                 c["total"]["20"] / s["total"]["20"],
                 c["total"]["40"] / s["total"]["40"],
                 c["head_on"] / s["head_on"]), flush=True)
print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
