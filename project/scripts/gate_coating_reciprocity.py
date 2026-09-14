# -*- coding: utf-8 -*-
"""코팅 노드가 상반성(reciprocity)을 지키나, 그리고 `brdf_model` 과 같은 값을 내나.

    Blender --background --factory-startup --python scripts/gate_coating_reciprocity.py

2026-09-14 감사가 잰 것: 민판에서 광원 80 도·관측자 -65 도와 그 반대를 견주면
옛 코팅(`fresnel_mix`)의 BRDF 가 55 % 다르다. 수동 재료는 그 둘이 같아야 한다.
`hemi_view` 가 총반사율을 읽는 근거가 바로 그 대칭이다.

이 검사가 하는 것 (전부 민판, 옆에 5 % 램버시안 대조판)
--------------------------------------------------------
  A  방향 교환. 세 쌍 x 두 방향 x 세 재료 (새 코팅, 옛 코팅, 램버시안).
     새 코팅은 2 % 안에서 같아야 한다. 옛 코팅은 55 % 어긋나야 한다 --
     안 어긋나면 검사기가 틀린 것이다. 램버시안은 0.1 % 안.
  B  균일 하늘 아래 일곱 각도. 새 코팅의 읽은 값을 `brdf_model` 의
     directional_albedo 와 견준다. 정확 프레넬과 Schlick 둘 다 찍어서
     Cycles 가 어느 쪽인지 **데이터로** 정한다 [모름 을 없애는 자리].
  C  램버시안 대조판이 모든 각도에서 0.05 를 읽나 (측정 사슬 검사).

렌더 조건은 감사의 render_probe.py 와 같다: 100 x 300 판, 직교 카메라,
빛줄기 256, 씨앗 17. 결과: results/audit_2026_09_14/fix_coating_gate.json
"""
import os
import sys
import json
import math
import time
from types import SimpleNamespace

import bpy
import bmesh
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import blender_render as BR                                         # noqa: E402
import brdf_model as M                                              # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "audit_2026_09_14", "fix_coating_gate.json")
TMP = "/tmp/simsrv/coating_gate"
os.makedirs(TMP, exist_ok=True)
FIT = json.load(open(os.path.join(ROOT, "results", "fit_coating",
                                  "musou_fit2_fit.json")))["fitted"]
NEW = dict(body=FIT["body"], spec_scale=FIT["spec_scale"],
           roughness=FIT["roughness_cycles"])
OLD = dict(body=BR.MUSOU_BODY, spec_scale=BR.MUSOU_SPEC_SCALE, roughness=0.30)
SPP = 256
FAILED = []


def say(ok, name, note):
    print("  [%s] %-46s %s%s" % ("PASS" if ok else "FAIL", name, note,
                                 "" if ok else "   <-- 실패"), flush=True)
    if not ok:
        FAILED.append(name)


def plate(coat, model):
    BR.clear_scene()
    p = SimpleNamespace(face_w=100.0, face_h=300.0)
    if coat is None:
        mat = BR.make_diffuse("lam", 0.01)
    else:
        mat = BR.make_coating("coat", roughness=coat["roughness"],
                              body=coat["body"], spec_scale=coat["spec_scale"],
                              model=model)
    ob = BR.make_flat_plate(p, 0, "sample", mat)
    # the open-plane builder winds toward -Y; measure the +Y front, as the
    # audit did, and print the normal so it is on record
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    BR.make_flat_plate(p, 120, "control", BR.make_diffuse("ctrl", 0.05))
    return tuple(ob.data.polygons[0].normal)


def read(ti, to):
    """ti None = uniform sky (hemi_view at observer `to`); else a sun at ti."""
    for o in list(bpy.data.objects):
        if o.type in ("LIGHT", "CAMERA"):
            bpy.data.objects.remove(o, do_unlink=True)
    BR.setup_camera(110, 0, 240, 160, 80, elev_deg=to)
    BR.configure_cycles(SPP, True, seed=17)
    BR.set_world(1.0 if ti is None else 0.0)
    if ti is not None:
        BR.add_sun(ti, 1.0, 0.0)
    f = os.path.join(TMP, "g.exr")
    BR.render_to(f, os.path.join(TMP, "g.png"))
    arr = BR.read_exr(f, 160, 80)
    a = BR.window_stats(arr, BR.to_pixel_window((20, 80, -30, 30)))["mean"]
    b = BR.window_stats(arr, BR.to_pixel_window((140, 200, -30, 30)))["mean"]
    return a, b


def main():
    t0 = time.time()
    res = {"blender": bpy.app.version_string, "spp": SPP,
           "coating_model_default": BR.COATING_MODEL, "new": NEW, "old": OLD,
           "swap": {}, "hemi": {}, "control": []}
    print("=" * 72)
    print("COATING GATE: reciprocity and agreement with brdf_model")
    print("=" * 72)

    # --- A. source/viewer swap ------------------------------------------
    pairs = ((80.0, -65.0), (60.0, -40.0), (45.0, 20.0))
    for label, coat, model, tol, expect_break in (
            ("reciprocal", NEW, "reciprocal", 0.02, False),
            ("fresnel_mix (legacy)", OLD, "fresnel_mix", None, True),
            ("lambert", None, None, 0.002, False)):
        n = plate(coat, model)
        rows = []
        worst = 0.0
        for a, b in pairs:
            f = {}
            for ti, to in ((a, b), (b, a)):
                s, c = read(ti, to)
                f["%g->%g" % (ti, to)] = (s / c) * 0.05 / math.pi
            v = list(f.values())
            gap = abs(v[0] - v[1]) / max(v[0], 1e-30)
            worst = max(worst, gap)
            rows.append(dict(pair=[a, b], brdf=f, gap=gap))
        res["swap"][label] = dict(normal=n, rows=rows, worst_gap=worst)
        if expect_break:
            say(worst > 0.2, "swap: %s breaks, as the audit found" % label,
                "worst gap %.1f%% (audit: 55.5%%)" % (100 * worst))
        else:
            say(worst <= tol, "swap: %s reciprocal" % label,
                "worst gap %.3f%% (tol %.1f%%)" % (100 * worst, 100 * tol))

    # --- B. uniform sky, seven angles, against the arithmetic model ------
    plate(NEW, "reciprocal")
    angles = (0, 15, 30, 45, 60, 75, 80)
    hemi = {}
    for t in angles:
        s, c = read(None, t)
        hemi[t] = dict(cycles=s / c * 0.05, control=c)
        res["control"].append(c)
    alpha = NEW["roughness"] ** 2
    worst = {"exact": 0.0, "schlick": 0.0}
    print("\n  %5s %10s %10s %10s %8s %8s" % ("theta", "cycles", "exact",
                                              "schlick", "d_exact", "d_schl"))
    for t in angles:
        ex = M.directional_albedo(t, NEW["body"], NEW["spec_scale"], alpha,
                                  1.5, "exact")
        sc = M.directional_albedo(t, NEW["body"], NEW["spec_scale"], alpha,
                                  1.5, "schlick")
        cy = hemi[t]["cycles"]
        de, ds = (cy - ex) / ex, (cy - sc) / sc
        hemi[t].update(model_exact=ex, model_schlick=sc, d_exact=de,
                       d_schlick=ds)
        worst["exact"] = max(worst["exact"], abs(de))
        worst["schlick"] = max(worst["schlick"], abs(ds))
        print("  %5d %10.6f %10.6f %10.6f %+7.2f%% %+7.2f%%"
              % (t, cy, ex, sc, 100 * de, 100 * ds))
    which = min(worst, key=worst.get)
    res["hemi"] = {str(k): v for k, v in hemi.items()}
    res["fresnel_in_cycles"] = which
    res["worst_vs_model"] = worst
    say(worst[which] <= 0.03, "hemi_view == brdf_model (%s fresnel)" % which,
        "worst %.2f%% (tol 3%%); other fresnel %.2f%%"
        % (100 * worst[which], 100 * worst[min(worst, key=lambda k: k == which)]))

    # --- C. the 0.05 control ----------------------------------------------
    cbad = [c for c in res["control"] if abs(c - 0.05) > 5e-4]
    say(not cbad, "control plate reads 0.05 at every angle",
        "min %.5f max %.5f" % (min(res["control"]), max(res["control"])))

    res["seconds"] = round(time.time() - t0, 1)
    res["failed"] = list(FAILED)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w"), indent=1)
    print("\n%d failed  (%.0fs)  -> %s" % (len(FAILED), res["seconds"],
                                          os.path.relpath(OUT, ROOT)))
    print("@@DONE@@")
    return len(FAILED)


if __name__ == "__main__":
    sys.exit(main())
