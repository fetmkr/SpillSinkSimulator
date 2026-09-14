# -*- coding: utf-8 -*-
"""무소 도료를 THR 과 TIS 에 같이 맞춘다. 렌더러 없이, `brdf_model` 로.

    python3 scripts/fit_musou_fit2.py            (1 분 안쪽, CPU)

왜 다시 맞추나 (2026-09-14 감사)
--------------------------------
1. `musou_fit.json` 의 확산 0.993 은 논문 그림 6 의 정면 TIS 를 0.985~0.995 로
   읽고 정한 값인데, 그림에서 0 도 값은 0.96 이다. 판독값은
   `material/_filip2026_fig6_read.json` 에 오차와 같이 적어 두었다.
2. 그 위에 "5 도 원뿔 안 1.5 % 이하이니 광택 몫 0.74 % 이하" 라고 추론했는데,
   광택 덩어리가 원뿔 안에 다 들어간다는 가정이 있어야 성립한다. 넓은
   덩어리는 원뿔 밖으로도 나간다. 그래서 TIS 하나로 확산 비율을 못 정한다.
3. 현재 재료로 민판을 재면 60 도 -30 %, 80 도 -67 % 로 논문 곡선을 못 낸다.

그래서 세 값 (body, spec_scale, alpha) 을 THR 일곱 점과 TIS 일곱 점에 **동시에**
맞춘다. 85 도는 두 판 다 축 밖이라 경계 조건으로만 쓴다. Rs 판은 다른 두 판과
어긋나서 (파일의 _주의) 맞춤에 안 넣고 대조로만 찍는다.

모델이 body 와 spec_scale 에 선형이라 (brdf_model.terms) 격자 적분은 alpha 한 축
에서만 한다. 첫 판은 세 축을 다 훑어서 30 분 넘게 걸렸다.

무엇이 나오나
------------
- 가장 잘 맞는 세 값, 그리고 chi^2 가 최소에서 4 안에 드는 값의 범위.
  범위가 넓은 값은 그만큼 논문이 못 묶어 준 것이다. 그대로 적는다.
- 옛 값 두 벌 (2026-08-22 이전 body 0.00758 / 0.0605 / 거칠기 0.30,
  현재 musou_fit 확산 0.993 / 거칠기 0.1975) 의 같은 잔차. 견주기 위해서다.
- `results/fit_coating/musou_fit2_fit.json` 에 전부 적는다.

THR 절대 눈금은 논문이 밝히지 않은 불확실성이 있다 (BRDF 가 상대 단위).
그건 세 점 모두에 같은 배율로 걸리므로 여기 맞춤이 못 잡는다. 모양은
맞추고, 절대값은 +-20 % 로 열려 있다고 적는다 (blender_render 주석과 같다).
"""
import os
import sys
import json
import math
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import brdf_model as M                                              # noqa: E402

ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "material", "_filip2026_fig6_read.json")
OUT = os.path.join(ROOT, "results", "fit_coating", "musou_fit2_fit.json")

F0 = 0.04                      # 굴절률 1.5 의 정면 프레넬, coating_split 과 같다
IOR = 1.5
FRESNEL = "exact"              # Cycles 쪽이 무엇을 쓰는지는 gate 가 잰다
GRID = dict(n_theta=1800, n_phi=720)


def load():
    d = json.load(open(DATA, encoding="utf-8"))
    pts = []
    for i, a in enumerate(d["angles_deg"]):
        pts.append(dict(angle=float(a), thr=d["thr"]["value"][i],
                        thr_sigma=d["thr"]["sigma"][i],
                        tis=d["tis"]["value"][i],
                        tis_sigma=d["tis"]["sigma"][i],
                        rs=d["rs"]["value"][i]))
    bounds = {"thr_min": {float(k): v["min"]
                          for k, v in d["thr"]["bound"].items()},
              "tis_max": {float(k): v["max"]
                          for k, v in d["tis"]["bound"].items()}}
    # 그림 5 단면: 모양만 쓴다 (바탕 90 도 값에 대한 비). BRDF 가 상대 단위라
    # 절대값은 못 쓰고, 세 판의 눈금이 서로 다르니 판끼리도 못 견준다.
    prof = []
    for k, v in d.get("fig5_profile", {}).items():
        if not k.isdigit():
            continue
        base = v["value"][0]
        prof.append(dict(theta=float(k), phis=v["phi"],
                         ratio=[x / base for x in v["value"]],
                         sigma_rel=v["sigma_rel"]))
    return pts, bounds, d["cone_half_deg"], prof


_TERMS = {}
_PROF = {}


def terms_for(alpha, angles, cone):
    key = round(alpha, 6)
    if key not in _TERMS:
        _TERMS[key] = {a: M.terms(a, alpha, IOR, FRESNEL, cone, **GRID)
                       for a in angles}
    return _TERMS[key]


def prof_for(alpha, prof):
    key = round(alpha, 6)
    if key not in _PROF:
        _PROF[key] = [M.profile_terms(p["theta"], p["phis"], alpha, IOR,
                                      FRESNEL) for p in prof]
    return _PROF[key]


def chi2(body, s, alpha, pts, bounds, cone, prof=()):
    if body < 0 or s < 0 or alpha <= 0 or s > 1.0:
        return 1e9
    angles = [q["angle"] for q in pts]
    T = terms_for(alpha, angles, cone)
    c = 0.0
    for q in pts:
        r = M.from_terms(T[q["angle"]], body, s)
        if q["thr"] is not None:
            c += ((r["thr"] - q["thr"]) / q["thr_sigma"]) ** 2
        if q["tis"] is not None:
            c += ((r["tis"] - q["tis"]) / q["tis_sigma"]) ** 2
    # 그림 5 의 덩어리 모양: 바탕(phi 90) 에 대한 비
    for p, lobe in zip(prof, prof_for(alpha, prof)):
        f = body / math.pi + s * lobe
        ratio = f / f[0] if f[0] > 0 else f * 0
        for r_model, r_read in zip(ratio, p["ratio"]):
            c += ((r_model - r_read) / (p["sigma_rel"] * r_read)) ** 2
    # 축 밖으로 나간 점: 경계를 넘지 않으면 0, 넘으면 벌점
    for a, lo in bounds["thr_min"].items():
        c += max(0.0, (lo - M.from_terms(T[a], body, s)["thr"]) / (0.05 * lo)) ** 2
    for a, hi in bounds["tis_max"].items():
        c += max(0.0, (M.from_terms(T[a], body, s)["tis"] - hi) / 0.02) ** 2
    return c


def best_linear(alpha, pts, bounds, cone, prof):
    """alpha 를 고정하고 (body, s) 를 찾는다. 둘은 싸니까 Nelder-Mead."""
    from scipy.optimize import minimize
    # body 는 0 이 될 수 있으니 선형으로, s 는 로그로 찾는다
    f = lambda x: chi2(max(x[0], 0.0) * 0.01, math.exp(x[1]), alpha, pts, bounds, cone, prof)  # noqa
    best = None
    for b0 in (0.2, 0.6, 0.9):
        for s0 in (0.02, 0.08, 0.2):
            r = minimize(f, [b0, math.log(s0)], method="Nelder-Mead",
                         options=dict(xatol=1e-5, fatol=1e-4, maxiter=800))
            if best is None or r.fun < best[0]:
                best = (r.fun, max(r.x[0], 0.0) * 0.01, math.exp(r.x[1]))
    return best


def table(body, s, alpha, pts, cone, prof=()):
    T = terms_for(alpha, [q["angle"] for q in pts], cone)
    rows = []
    for q in pts:
        r = M.from_terms(T[q["angle"]], body, s)
        rows.append(dict(angle=q["angle"], thr_model=r["thr"], thr_read=q["thr"],
                         thr_resid=((r["thr"] - q["thr"]) / q["thr"]
                                    if q["thr"] else None),
                         tis_model=r["tis"], tis_read=q["tis"],
                         tis_resid=((r["tis"] - q["tis"]) if q["tis"] else None),
                         rs_model=r["rs"], rs_read=q["rs"]))
    for p, lobe in zip(prof, prof_for(alpha, prof)):
        f = body / math.pi + s * lobe
        rows.append(dict(profile_theta=p["theta"], phis=p["phis"],
                         ratio_model=[float(x) for x in f / f[0]],
                         ratio_read=p["ratio"]))
    return rows


def show(name, body, s, alpha, rows, c2):
    print("\n== %s   body %.5f  spec_scale %.4f  alpha %.4f  "
          "(Cycles roughness %.4f)   chi2 %.1f"
          % (name, body, s, alpha, math.sqrt(alpha), c2))
    print("  %5s %8s %8s %7s | %6s %6s %7s | %7s %7s"
          % ("theta", "THR", "read", "resid", "TIS", "read", "resid",
             "Rs", "read"))
    for r in rows:
        if "profile_theta" in r:
            print("  lobe %2.0f/%2.0f  model %s\n              read  %s"
                  % (r["profile_theta"], r["profile_theta"],
                     " ".join("%4.2f" % x for x in r["ratio_model"]),
                     " ".join("%4.2f" % x for x in r["ratio_read"])))
            continue
        print("  %5.0f %8.5f %8s %7s | %6.4f %6s %7s | %7.4f %7.4f"
              % (r["angle"], r["thr_model"],
                 "%.4f" % r["thr_read"] if r["thr_read"] else "  off",
                 "%+.1f%%" % (100 * r["thr_resid"]) if r["thr_resid"] is not None else "",
                 r["tis_model"],
                 "%.3f" % r["tis_read"] if r["tis_read"] else " off",
                 "%+.3f" % r["tis_resid"] if r["tis_resid"] is not None else "",
                 r["rs_model"], r["rs_read"]))


def main():
    pts, bounds, cone, prof = load()
    t0 = time.time()

    # 1. alpha 한 축을 훑고, 축마다 (body, s) 는 닫힌식에 가깝게 찾는다
    scan = []
    for alpha in np.geomspace(0.01, 0.8, 40):
        c, b, s = best_linear(alpha, pts, bounds, cone, prof)
        scan.append((c, b, s, float(alpha)))
    scan.sort()
    c0, b0, s0, a0 = scan[0]
    print("alpha scan best: chi2 %.1f  body %.5f  s %.4f  alpha %.4f  (%.0fs)"
          % (c0, b0, s0, a0, time.time() - t0))
    # 2. alpha 를 좁게 다듬는다
    for alpha in np.geomspace(a0 / 1.25, a0 * 1.25, 21):
        c, b, s = best_linear(alpha, pts, bounds, cone, prof)
        scan.append((c, b, s, float(alpha)))
    scan.sort()
    c_best, body, s, alpha = scan[0]
    print("refined: chi2 %.1f  body %.5f  s %.4f  alpha %.4f  (%.0fs)"
          % (c_best, body, s, alpha, time.time() - t0))

    # 3. 범위: chi2 <= 최소 + 4 인 점들. alpha 축은 훑은 값에서, body/s 는 그
    #    alpha 에서 다시 훑는다. 세 값이 서로 물려 있어 같이 봐야 한다.
    keep = []
    for c, b, s_, a in scan:
        for fb in np.geomspace(0.7, 1.3, 13):
            for fs in np.geomspace(0.5, 2.0, 15):
                cc = chi2(b * fb, s_ * fs, a, pts, bounds, cone, prof)
                if cc <= c_best + 4.0:
                    keep.append((b * fb, s_ * fs, a, cc))
    rng = None
    if keep:
        arr = np.array(keep)
        rng = {"body": [float(arr[:, 0].min()), float(arr[:, 0].max())],
               "spec_scale": [float(arr[:, 1].min()), float(arr[:, 1].max())],
               "alpha": [float(arr[:, 2].min()), float(arr[:, 2].max())],
               "n_points": int(len(keep)), "delta_chi2": 4.0}
        print("within chi2+4: body %.5f..%.5f  s %.4f..%.4f  alpha %.4f..%.4f"
              % (rng["body"][0], rng["body"][1], rng["spec_scale"][0],
                 rng["spec_scale"][1], rng["alpha"][0], rng["alpha"][1]))

    rows = table(body, s, alpha, pts, cone, prof)
    show("fitted (musou_fit2)", body, s, alpha, rows, c_best)

    # 4. 옛 값 두 벌, 같은 잣대로
    old = {}
    for name, (b_, s_, a_) in {
            "historical 2026-08 (df 0.76, rough 0.30)":
                (0.00758, 0.0605, 0.30 ** 2),
            "current musou_fit (df 0.993, rough 0.1975)":
                (0.993 * 0.00998, (1 - 0.993) * 0.00998 / F0, 0.1975 ** 2)}.items():
        c = chi2(b_, s_, a_, pts, bounds, cone, prof)
        rw = table(b_, s_, a_, pts, cone, prof)
        show(name, b_, s_, a_, rw, c)
        old[name] = dict(body=b_, spec_scale=s_, alpha=a_, chi2=c, rows=rw)

    rho0_nom = body + s * F0
    out = {"date": "2026-09-14", "data": os.path.relpath(DATA, ROOT),
           "fresnel": FRESNEL, "ior": IOR, "cone_half_deg": cone,
           "grid": GRID,
           "fitted": {"body": body, "spec_scale": s, "alpha": alpha,
                      "roughness_cycles": math.sqrt(alpha),
                      "rho0_nominal": rho0_nom,
                      "diffuse_fraction_nominal": body / rho0_nom,
                      "thr0_model": rows[0]["thr_model"],
                      "chi2": c_best, "n_data": 14 + sum(len(p["phis"]) for p in prof)},
           "range_chi2_plus_4": rng, "rows": rows,
           "alpha_scan": [dict(chi2=c, body=b, spec_scale=s_, alpha=a)
                          for c, b, s_, a in sorted(scan, key=lambda r: r[3])],
           "comparison": old,
           "energy": {str(k): v for k, v in
                      M.energy_check(body, s, alpha, IOR, FRESNEL).items()},
           "model_reciprocity_gap": M.reciprocity_gap(body, s, alpha, IOR,
                                                      FRESNEL),
           "seconds": round(time.time() - t0, 1),
           "_note": "THR 절대 눈금은 논문이 안 밝힌 불확실성(+-20 % 정도)이 "
                    "있고 세 값에 같은 배율로 걸린다. 여기 잔차는 모양 "
                    "맞춤이다. 85 도는 경계 조건으로만 썼다."}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print("\nwrote", os.path.relpath(OUT, ROOT), "(%.0fs)" % (time.time() - t0))


if __name__ == "__main__":
    main()
