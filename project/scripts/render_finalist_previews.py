# -*- coding: utf-8 -*-
"""최종 보고서용 3D 그림. 후보마다 위에서 / 옆에서 / 비스듬히 세 장을 한 장으로.

    zsh scripts/run_batch.sh scripts/render_finalist_previews.py finalprev

`preview_geom.render` 를 그대로 쓴다 (측정과 같은 메시 빌더). 보고서용이라
방향 표시 기둥은 뺀다 (`PREVIEW_NO_MARKER=1`). 그림은 형상을 보여 주려는 것이지
측정이 아니다. 조명도 모양이 읽히게 고른 것이다.

판 크기는 그림에만 줄인다 (칸 여섯 개 너비). 측정 조건과는 무관하다.
V 홈은 `preview_geom` 이 모르는 1D 단면 계열이라, 단면 고리를 X 로 늘여 메시로
만든 뒤 같은 카메라로 찍는다.

읽는 것:  results/finalists_2026_09_15.json
쓰는 것:  /tmp/simsrv/finalist_previews/NN.png 와 manifest.json
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
os.environ["PREVIEW_NO_MARKER"] = "1"
import sim_server as SS             # noqa: E402
import preview_geom as PG           # noqa: E402
import recompute_published as RP    # noqa: E402

ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "results", "finalists_2026_09_15.json")
OUT = "/tmp/simsrv/finalist_previews"


def ridge_mesh(params):
    """Extrude the ridge cross-section loops along X into a mesh, the same way
    `blender_render.loops_to_object` does, so the picture is the measured part."""
    import dataclasses
    import profile_ridge as PR
    # only the fields RidgeParams has: preview_geom needs a `pitch` key to frame
    # the camera, and RidgeParams rejects it (first run failed on that)
    keep = {f.name for f in dataclasses.fields(PR.RidgeParams)}
    p = PR.RidgeParams(**{k: v for k, v in params.items() if k in keep})
    cs = PR.build_cross_section(p)
    L = 3.0 * float(params.get("pitch_mean", 13.0))
    V, F = [], []
    for loop in list(cs.stage1) + list(cs.stage2) + list(cs.shell):
        pts = []
        for y, z in loop:
            if not pts or abs(pts[-1][0] - y) > 1e-7 or abs(pts[-1][1] - z) > 1e-7:
                pts.append((y, z))
        n = len(pts)
        if n < 3:
            continue
        b = len(V)
        for y, z in pts:
            V.append((0.0, y, z))
        for y, z in pts:
            V.append((L, y, z))
        for i in range(n):
            j = (i + 1) % n
            F.append((b + i, b + j, b + n + j, b + n + i))
    return V, F


def family_params(row):
    if row.get("spec"):
        spec = dict(row["spec"], margin_depths=0.2)
        fam = SS._render_family(spec)
        prm = SS._render_params(spec)
    else:
        fam, prm = RP.family_of(row["params"])
        prm = dict(prm)
    pitch = float(prm.get("pitch") or prm.get("pitch_mean")
                  or (prm.get("top_params") or {}).get("pitch") or 6.0)
    face = min(float(prm.get("face_w", 60.0)), 6.0 * pitch)
    prm.update(face_w=face, face_h=face, margin_depths=0.2)
    # NO `depth` KEY FOR A STACK: StackParams has top_depth/bot_depth only and
    # rejects `depth` (first run: 4 stacks failed on exactly that). The camera
    # in preview_geom falls back to its own default depth, which only frames
    # the shot.
    return fam, prm, pitch


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = json.load(open(SRC))["rows"]
    manifest = {}
    orig_build = PG.build
    for i, (key, row) in enumerate(rows.items()):
        png = os.path.join(OUT, "%02d.png" % i)
        try:
            fam, prm, pitch = family_params(row)
            if fam == "ridge":
                PG.build = lambda f, p: ridge_mesh(p)
                prm.setdefault("pitch", prm.get("pitch_mean", 13.0))
            else:
                PG.build = orig_build
            PG.render(fam, prm, png, cells=3.0)
            got = png if os.path.exists(png) else None
            if got is None:
                tq = png.replace(".png", "_threequarter.png")
                got = tq if os.path.exists(tq) else None
            manifest[key] = {"png": got, "family": fam}
            print("[preview] %s -> %s" % (key, got), flush=True)
        except Exception as exc:
            manifest[key] = {"png": None, "error": "%s: %s" % (type(exc).__name__, exc)}
            print("[preview FAIL] %s: %s" % (key, exc), flush=True)
        finally:
            PG.build = orig_build
        json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"),
                  indent=1, ensure_ascii=False)
    print("@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
