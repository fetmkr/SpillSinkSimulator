# -*- coding: utf-8 -*-
"""광선 그림이 렌더와 같은 재료로 튕기나. 렌더러 없음, CPU.

    python3 scripts/gate_rays_brdf.py

2026-09-14 감사 8 절: 광선 그림의 `fitted` 는 반사마다 같은 rho 를 곱하고, 확산
비율로 동전을 던져 확산/거울을 고르고, 거울을 GGX 가 아닌 흔들기로 흐렸다.
프레넬도 없고 재료도 한 벌이었다. 그래서 그 그림의 탈출 비율로 렌더를 검증할 수
없었다.

  A  scalar BRDF (광선마다 쓰는 것) == numpy BRDF (산술 기준)   무작위 2000 쌍
  B  민판에 쏜 광선의 rho_est == brdf_model.directional_albedo
     musou_fit2 와 wall_5pct, 입사 0/40/60/80 도. 허용: 표본 오차 4 시그마
  C  흰 램버시안 (body 1, 광택 0) -> rho_est 정확히 1
  D  옛 모드(diffuse, rho 0.5) 는 그대로 0.5
  E  미리보기 메시의 깊이 방향: 피라미드 깊이 22 가 y 0 ~ -22 에 있다
     (층 고르기가 y < -paint_depth 로 바닥을 가르므로 부호가 맞아야 한다)

B 는 렌더와 같은 BRDF 라는 뜻이지 렌더 숫자와 같다는 뜻이 아니다. 렌더 트리와
brdf_model 이 같다는 것은 gate_coating_reciprocity.py 가 따로 쟀다 (0.08 %).
"""
import io
import os
import sys
import json
import math
import random
import contextlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import brdf_model as M                                              # noqa: E402
import raytrace_viz as RV                                           # noqa: E402
with contextlib.redirect_stdout(io.StringIO()):
    import sim_server as S                                          # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "audit_2026_09_14", "fix_rays_brdf.json")
FAILED = []
R = {}


def say(ok, name, note):
    print("  [%s] %-50s %s%s" % ("PASS" if ok else "FAIL", name, note,
                                 "" if ok else "   <-- 실패"), flush=True)
    if not ok:
        FAILED.append(name)


def rand_up(rng):
    u1, u2 = rng.random(), rng.random()
    ct = u1
    st = math.sqrt(1 - ct * ct)
    return (st * math.cos(2 * math.pi * u2), st * math.sin(2 * math.pi * u2), ct)


def a_scalar():
    rng = random.Random(7)
    worst = 0.0
    for _ in range(2000):
        wi, wo = rand_up(rng), rand_up(rng)
        body, s, a = rng.random() * 0.05, rng.random() * 0.6, 0.02 + rng.random()
        fs = M.brdf_scalar(wi, wo, body, s, a)
        fa = float(M.brdf(np.array(wi), np.array(wo), body, s, a))
        worst = max(worst, abs(fs - fa) / max(abs(fa), 1e-30))
    say(worst < 1e-9, "A scalar == numpy BRDF", "최대 상대차 %.1e" % worst)
    R["scalar_vs_numpy_worst"] = worst


def flat(layer, theta, n, mode="fitted", rho=0.5):
    V = [(0.0, 0.0, 0.0), (100.0, 0.0, 0.0), (100.0, 0.0, 100.0),
         (0.0, 0.0, 100.0)]
    F = [(0, 1, 2, 3)]
    lay = {"top": layer, "deep": None, "paint_depth": None, "floor": None,
           "floor_depth": None} if layer else None
    out = RV.trace(V, F, 100.0, 100.0, theta_deg=theta, n_rays=n,
                   max_bounces=4, rho=rho, mode=mode, seed=11, layers=lay)
    hits = [i for i, d in enumerate(out["depths"]) if d > 0]
    w = np.array([out["weights"][i] if out["escaped"][i] else 0.0
                  for i in hits])
    return out["stats"]["rho_est"], float(w.std() / math.sqrt(max(len(w), 1)))


def b_flat():
    print("\nB  민판 rho_est 대 directional_albedo")
    rows = []
    for mid in ("musou_fit2", "wall_5pct"):
        c = S._coat(mid)
        lay = {"body": c["body"], "spec_scale": c["spec_scale"],
               "alpha": c["roughness"] ** 2}
        for th in (0.0, 40.0, 60.0, 80.0):
            est, se = flat(lay, th, 20000)
            ref = M.directional_albedo(th, lay["body"], lay["spec_scale"],
                                       lay["alpha"])
            z = (est - ref) / se if se > 0 else float("inf")
            ok = abs(est - ref) <= 4 * se + 0.005 * ref
            rows.append(dict(material=mid, theta=th, rho_est=est, se=se,
                             model=ref, z=z, ok=ok))
            print("     %-10s %2.0f°  광선 %.5f ± %.5f   모델 %.5f   (%+.1f σ)"
                  % (mid, th, est, se, ref, z))
    say(all(r["ok"] for r in rows), "B 민판 8 경우가 표본 오차 안",
        "최대 %.1f σ" % max(abs(r["z"]) for r in rows))
    R["flat"] = rows


def c_white():
    est, _ = flat({"body": 1.0, "spec_scale": 0.0, "alpha": 0.5}, 30.0, 2000)
    say(abs(est - 1.0) < 1e-12, "C 흰 램버시안 rho_est == 1", "%.12f" % est)


def d_legacy():
    est, _ = flat(None, 30.0, 2000, mode="diffuse", rho=0.5)
    say(abs(est - 0.5) < 1e-12, "D 옛 diffuse 모드는 그대로", "%.12f" % est)


def e_depth():
    spec = {"top": "pyramid", "top_params": {"pitch": 4.0, "tip_flat": 0.1},
            "depth": 22.0, "panel": 40.0, "floor": "none", "margin_depths": 0.0}
    with contextlib.redirect_stdout(io.StringIO()):
        v, f, _p = S.build(spec)
    ys = [p[1] for p in v]
    say(max(ys) <= 1e-6 and -24.5 < min(ys) < -21.5,
        "E 미리보기 메시 깊이가 y 0 ~ -22", "y %.2f .. %.2f" % (min(ys), max(ys)))
    R["preview_y"] = [min(ys), max(ys)]


if __name__ == "__main__":
    print("광선 그림 BRDF 검사 (렌더 없음)")
    a_scalar()
    b_flat()
    c_white()
    d_legacy()
    e_depth()
    R["failed"] = FAILED
    json.dump(R, open(OUT, "w"), indent=1, default=float)
    print("\n%d 실패 -> %s" % (len(FAILED), os.path.relpath(OUT, ROOT)))
    sys.exit(1 if FAILED else 0)
