# -*- coding: utf-8 -*-
"""봉우리와 뭉개기 통계를 합성 반례로 검사한다. 렌더러 없음.

    python3 scripts/gate_form_stats.py

**합성 반례다. 실제 패널 측정이 아니다.** 여기서 통과한다는 것은 통계 계산이
정해 둔 뜻대로 움직인다는 것뿐이다. 실제 렌더에서 값이 얼마나 바뀌는지는
`gate_reference_before_after.py` 가 잰다.

반례는 2026-09-14 감사의 `arithmetic_probe.py` 와 같은 신호를 쓴다. 그 스크립트가
옛 규칙의 실패를 재현했고, 이 검사는 그 실패를 먼저 다시 보인 뒤 새 규칙이
고쳤는지 본다. 옛 실패가 안 보이면 검사기가 틀린 것이므로 그것도 불합격이다.

  A  봉우리: 같은 신호를 0 으로 채운 길이만 바꾼다.
     A1 옛 p99 가 10 배 흔들린다 (재현)
     A2 새 box 는 1e-12 안에서 안 흔들린다 (1D)
     A3 2D 에서도: 좁은 점 반사를 어두운 빈 칸으로 감싸도 box 가 그대로다
  B  뭉개기 거짓 수렴: 중심 72.7 %, +-34 mm 에 27.3 %, 창 24/48/96/100
     B1 옛 규칙은 48 mm 에서 1.00 으로 멈춘다 (재현)
     B2 새 규칙은 22.22 를 값으로, 수렴으로 낸다
     B3 옛 규칙이 틀렸다는 표시(first_agreement_reversed)가 켜진다
  C  판이 꼬리를 겨우 담을 때 (창 24/48/72, 꼬리가 가장자리 10 % 에 걸림)
     -> 수렴이 아니다 (아래 한계)
  D  꼬리 없는 신호 (창 24/48/96) -> 1.00, 수렴
  E  **알려진 한계**: 창이 24/48 뿐이면 +-34 mm 꼬리는 프레임 밖이다.
     새 규칙도 1.00, 수렴이라고 한다. 이건 통과가 아니라 한계를 적는 칸이다.
     이 칸이 바뀌면 문서(form_metrics.smear_ladder)를 고쳐야 한다.
"""
import os
import sys
import json

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import form_metrics as FM                                           # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "audit_2026_09_14", "fix_form_stats.json")
FAILED = []
R = {}


def say(ok, name, note):
    print("  [%s] %-52s %s%s" % ("PASS" if ok else "FAIL", name, note,
                                 "" if ok else "   <-- 실패"), flush=True)
    if not ok:
        FAILED.append(name)


def peak_padding():
    print("\nA  봉우리가 판 크기(0 으로 채운 길이)에 흔들리나")
    mm = 0.215
    x = np.arange(400) - 200
    panel = 0.1 * (np.abs(x) < 18) + 0.9 * (np.abs(x) < 4)
    ctrl = 1.0 * (np.abs(x) < 18)
    rows = []
    for n in (361, 465, 931, 2327):
        pp, pc = FM.recentre(panel, n), FM.recentre(ctrl, n)
        rows.append(dict(
            nwin=n,
            p99=float(np.percentile(pp, 99) / np.percentile(pc, 99)),
            maximum=float(pp.max() / pc.max()),
            box=float(FM.box_max_1d(pp, mm) / FM.box_max_1d(pc, mm))))
        print("     nwin %5d  p99 %.4f  max %.4f  box %.6f"
              % (n, rows[-1]["p99"], rows[-1]["maximum"], rows[-1]["box"]))
    p99s = [r["p99"] for r in rows]
    boxes = [r["box"] for r in rows]
    say(max(p99s) / min(p99s) > 5, "A1 옛 p99 가 판 크기로 흔들린다 (재현)",
        "%.2f 배" % (max(p99s) / min(p99s)))
    say(max(boxes) - min(boxes) < 1e-12, "A2 box 는 판 크기에 안 흔들린다",
        "차이 %.1e" % (max(boxes) - min(boxes)))

    # 2D: a 3 x 3 px glint of 1.0 inside a 35 px beam at 0.1, surrounded by an
    # increasing amount of dark panel in both directions
    g = []
    for pad in (0, 50, 400):
        img = np.zeros((35 + 2 * pad, 200 + 2 * pad))
        img[pad:pad + 35, pad:pad + 200] = 0.1
        img[pad + 16:pad + 19, pad + 98:pad + 101] = 1.0
        ref = np.zeros_like(img)
        ref[pad:pad + 35, pad:pad + 200] = 1.0
        bx = round(FM.PEAK_BOX_MM / mm)
        a = FM.box_max_2d(img, bx, bx) / FM.box_max_2d(ref, bx, bx)
        pa = np.percentile(img.mean(axis=1), 99) / np.percentile(
            ref.mean(axis=1), 99)
        g.append(dict(pad=pad, box=a, p99_of_x_mean=float(pa)))
        print("     2D pad %3d  box %.6f  p99(가로 평균) %.4f" % (pad, a, pa))
    say(max(r["box"] for r in g) - min(r["box"] for r in g) < 1e-12,
        "A3 2D box 도 빈 칸에 안 흔들린다", "box %.4f" % g[0]["box"])
    R["peak_padding"] = rows
    R["peak_padding_2d"] = g


def two_peak(windows):
    z = np.arange(-50, 50.001, 0.05)
    core = np.exp(-0.5 * (z / 0.8) ** 2)
    core /= core.sum()
    tails = (np.exp(-0.5 * ((z - 34) / 0.5) ** 2)
             + np.exp(-0.5 * ((z + 34) / 0.5) ** 2))
    tails /= tails.sum()
    p = 0.727 * core + 0.273 * tails
    ps = [p * (np.abs(z) <= h / 2) for h in windows]
    cs = [core * (np.abs(z) <= h / 2) for h in windows]
    return ps, cs


def ladder():
    print("\nB  뭉개기 거짓 수렴")
    W = (24.0, 48.0, 96.0, 100.0)
    ps, cs = two_peak(W)
    v = FM.smear_ladder(W, ps, cs, 0.05)
    for c in v["curve"]:
        print("     창 %5.0f  smear %.3f" % (c["window_mm"], c["smear"]))
    fa = v["first_agreement"]
    say(fa and fa["window_mm"] == 48.0 and abs(fa["smear"] - 1.0) < 1e-6,
        "B1 옛 규칙은 48 mm, 1.00 에서 멈춘다 (재현)",
        "옛 선택 %s mm, %.3f" % (fa and fa["window_mm"], fa and fa["smear"]))
    say(abs(v["value"]["smear"] - 22.2248) < 1e-3 and v["converged"],
        "B2 새 규칙은 22.22 를, 수렴으로 낸다",
        "%.4f  converged %s" % (v["value"]["smear"], v["converged"]))
    say(v["first_agreement_reversed"], "B3 옛 선택이 틀렸다고 표시한다",
        "reversed %s" % v["first_agreement_reversed"])
    R["false_convergence"] = {k: v[k] for k in v if k != "curve"}
    R["false_convergence"]["curve"] = v["curve"]

    print("\nC  꼬리가 판 가장자리에 걸릴 때")
    W = (24.0, 48.0, 72.0)
    ps, cs = two_peak(W)
    v = FM.smear_ladder(W, ps, cs, 0.05)
    say(not v["converged"], "C  가장자리에 빛이 남으면 수렴이 아니다",
        "edge moment %.3f  converged %s" % (v["edge_moment"], v["converged"]))
    R["edge"] = {k: v[k] for k in v if k != "curve"}

    print("\nD  꼬리 없는 신호")
    W = (24.0, 48.0, 96.0)
    z = np.arange(-50, 50.001, 0.05)
    core = np.exp(-0.5 * (z / 0.8) ** 2)
    ps = [core * (np.abs(z) <= h / 2) for h in W]
    v = FM.smear_ladder(W, ps, ps, 0.05)
    say(v["converged"] and abs(v["value"]["smear"] - 1.0) < 1e-9,
        "D  1.00, 수렴", "%.4f converged %s" % (v["value"]["smear"],
                                                v["converged"]))
    R["clean"] = {k: v[k] for k in v if k != "curve"}

    print("\nE  알려진 한계: 꼬리가 프레임 밖")
    W = (24.0, 48.0)
    ps, cs = two_peak(W)
    v = FM.smear_ladder(W, ps, cs, 0.05)
    limit = v["converged"] and abs(v["value"]["smear"] - 1.0) < 1e-6
    print("     [LIMIT] 창 48 mm 가 끝이면 새 규칙도 %.2f, 수렴 %s 라고 한다. "
          "프레임에 안 들어온 빛은 어떤 통계로도 못 본다."
          % (v["value"]["smear"], v["converged"]))
    say(limit, "E  한계가 문서대로다 (바뀌면 문서를 고칠 것)",
        "smear %.2f converged %s" % (v["value"]["smear"], v["converged"]))
    R["known_limit_outside_frame"] = {k: v[k] for k in v if k != "curve"}


if __name__ == "__main__":
    print("봉우리·뭉개기 통계, 합성 반례 (실제 측정 아님)")
    peak_padding()
    ladder()
    R["failed"] = FAILED
    R["_note"] = "합성 반례. 실제 패널 측정이 아니다."
    json.dump(R, open(OUT, "w"), indent=1, default=float)
    print("\n%d 실패 -> %s" % (len(FAILED), os.path.relpath(OUT, ROOT)))
    sys.exit(1 if FAILED else 0)
