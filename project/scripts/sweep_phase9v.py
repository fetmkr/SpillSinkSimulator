"""Phase 9.v: does the double-floor artifact touch ANY published number?

    Blender --background --factory-startup --python scripts/sweep_phase9v.py

WHY. The print-file audit (2026-08-17) found every floor-family mesh is
composed of overlapping solids: the pyramid field closes its own base
at y = -20 and a separate backing slab (-22..-20) sits under it, so the
-20 plane carries two coincident face layers (field base facing down,
slab top facing up), plus T-vertex rims. Every published floor number
-- the anchor, the final sample, the whole aspect law -- was rendered
on such meshes. The union is what Cycles integrates and the coincident
plane is interior, so the artifact SHOULD be invisible; this project's
history (winding alone moved a glossy number 49 %) says prove it,
don't assume it.

METHOD. The final sample (pyramid 4/20/0.1, face 60) is rendered twice
in the same harness: once through the normal builder, once with
`geom_floor.build_mesh` monkeypatched to return the CLEANED solid --
internal coincident faces removed, slab re-tessellated to the 4 mm
grid, winding made coherent by edge propagation, one manifold shell
(the same repair applied to the exports). Same envelope, same windows,
same coating, same seed.

    PREDICTIONS, numeric, before any render.

    P1  THE BOOK STANDS: cleaned-solid worst over 3 mats x 5 theta
        equals the book value 0.17668 % within +-2.5 % relative
        (0.1723-0.1811). The artifact plane is interior to the union
        and unreachable by transport.
    P2  PER-CELL AGREEMENT: every (mat, theta) cell agrees with the
        same-run composed-mesh cell within +-3 % relative; no cell
        flips which material owns the worst.
    P3  The composed-mesh rerun itself reproduces 0.17668 within the
        seed-determinism of the harness (exact digits expected, as the
        anchor always has).

    If P1/P2 FAIL the entire floor book is suspect and a full re-sweep
    gets scheduled; the FINDINGS will say so in those words.

Anchor: P5_j00 d100@-40 (composed, as always) must equal 0.13392 %.
"""

import sys
import os
import csv
import json
import struct
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase9v.csv")
OUT = "/tmp/phase9v"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
FINAL = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 20.0,
         "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0, "backing": 2.0}
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
TH5 = (0.0, -20.0, 20.0, -40.0, 40.0)
COLS = ["tag", "family", "topology", "phi", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def clean_solid(v, f):
    """The export repair, as a function: strip the internal -20 plane and
    the composed slab, rebuild the slab on the 4 mm grid, weld, orient."""
    tris = [[list(v[i]) for i in face] for face in f]
    # triangulate quads
    tt = []
    for t in tris:
        if len(t) == 3:
            tt.append(t)
        else:
            for k in range(1, len(t) - 1):
                tt.append([t[0], t[k], t[k + 1]])
    field = []
    for t in tt:
        ys = [p[1] for p in t]
        if min(ys) < -20.0 - 1e-6:
            continue
        if max(ys) - min(ys) < 1e-9 and abs(ys[0] + 20.0) < 1e-6:
            continue
        field.append(t)
    xs = [p[0] for t in field for p in t]
    zs = [p[2] for t in field for p in t]
    x0, x1 = round(min(xs), 6), round(max(xs), 6)
    z0, z1 = round(min(zs), 6), round(max(zs), 6)
    P = 4.0
    nx = int(round((x1 - x0) / P))
    nz = int(round((z1 - z0) / P))
    out = list(field)

    def quad(a, b, c, d):
        out.append([list(a), list(b), list(c)])
        out.append([list(a), list(c), list(d)])
    yT, yB = -20.0, -22.0
    for i in range(nx):
        xa, xb = x0 + i * P, x0 + (i + 1) * P
        quad((xa, yT, z0), (xb, yT, z0), (xb, yB, z0), (xa, yB, z0))
        quad((xa, yT, z1), (xb, yT, z1), (xb, yB, z1), (xa, yB, z1))
    for j in range(nz):
        za, zb = z0 + j * P, z0 + (j + 1) * P
        quad((x0, yT, za), (x0, yT, zb), (x0, yB, zb), (x0, yB, za))
        quad((x1, yT, za), (x1, yT, zb), (x1, yB, zb), (x1, yB, za))
    for i in range(nx):
        for j in range(nz):
            xa, xb = x0 + i * P, x0 + (i + 1) * P
            za, zb = z0 + j * P, z0 + (j + 1) * P
            quad((xa, yB, za), (xb, yB, za), (xb, yB, zb), (xa, yB, zb))
    vmap, verts, faces = {}, [], []
    for t in out:
        idx = []
        for p in t:
            k = (round(p[0], 5), round(p[1], 5), round(p[2], 5))
            if k not in vmap:
                vmap[k] = len(verts)
                verts.append(list(k))
            idx.append(vmap[k])
        if len(set(idx)) == 3:
            faces.append(tuple(idx))
    # coherent winding by edge propagation, then outward by volume
    edge2f = collections.defaultdict(list)
    for fi, f3 in enumerate(faces):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            edge2f[tuple(sorted((f3[a], f3[b])))].append(fi)
    faces = [list(f3) for f3 in faces]
    seen = [False] * len(faces)
    for start in range(len(faces)):
        if seen[start]:
            continue
        seen[start] = True
        stack = [start]
        while stack:
            fi = stack.pop()
            f3 = faces[fi]
            for a, b in ((0, 1), (1, 2), (2, 0)):
                e = tuple(sorted((f3[a], f3[b])))
                u, vv = f3[a], f3[b]
                for gj in edge2f[e]:
                    if gj == fi or seen[gj]:
                        continue
                    g = faces[gj]
                    gdir = None
                    for c, d in ((0, 1), (1, 2), (2, 0)):
                        if tuple(sorted((g[c], g[d]))) == e:
                            gdir = (g[c], g[d])
                    if gdir == (u, vv):
                        faces[gj] = [g[0], g[2], g[1]]
                    seen[gj] = True
                    stack.append(gj)
    vol = 0.0
    for f3 in faces:
        a = verts[f3[0]]; b = verts[f3[1]]; c = verts[f3[2]]
        vol += (a[0] * (b[1] * c[2] - b[2] * c[1])
                - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0]))
    if vol < 0:
        faces = [[f3[0], f3[2], f3[1]] for f3 in faces]
    return verts, [tuple(f3) for f3 in faces]


def main():
    import blender_render as BR
    import geom_floor as GF
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []

    def run_one(tag, prm, mat, th, variant):
        body, spec = BR.coating_split(DF[mat])
        cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
               "family": "floor", "out_dir": OUT, "results_dir": OUT,
               "samples": 64, "res_x": 480, "res_y": 220, "gpu": True,
               "spec_roughness": 0.30, "params": prm,
               "renders": [{"mode": "hemi_view", "theta": th}],
               "material_mode": "coating",
               "coating": {"body": body, "spec_scale": spec,
                           "roughness": 0.30}}
        cfg.update({k: v for k, v in COAT.items()
                    if k != "spec_roughness"})
        res = BR.run(cfg)
        rec = list(res["modes"].values())[0]
        rows.append({"tag": tag, "family": "floor", "topology": "pyramid",
                     "phi": 0, "seed": 23, "diffuse_frac": mat,
                     "theta": th, "rho": rec["panel"]["mean"],
                     "control": rec["control"]["mean"],
                     "params_json": json.dumps(
                         dict(prm, mesh=variant), sort_keys=True)})
        return rec["panel"]["mean"]

    print("=" * 74)
    print("PHASE 9.v — the double-floor artifact, cross-checked")
    print("=" * 74)

    v = run_one("P5_j00", ANCHOR, "d100", -40.0, "composed")
    print("  anchor: %.5f %% (book 0.13392)" % (100 * v), flush=True)

    cells = {}
    w = 0.0
    for mat in ("d00", "d76", "d100"):
        for th in TH5:
            r = run_one("P9v_composed", FINAL, mat, th, "composed")
            cells[("composed", mat, th)] = r
            w = max(w, r)
    print("  composed worst: %.5f %% (book 0.17668)" % (100 * w),
          flush=True)

    orig = GF.build_mesh
    vc, fc = clean_solid(*orig(GF.FloorParams(**FINAL)))
    print("  cleaned solid: %d faces" % len(fc), flush=True)
    GF.build_mesh = lambda p: (vc, fc)
    try:
        w2 = 0.0
        for mat in ("d00", "d76", "d100"):
            for th in TH5:
                r = run_one("P9v_cleaned", FINAL, mat, th, "cleaned")
                cells[("cleaned", mat, th)] = r
                w2 = max(w2, r)
    finally:
        GF.build_mesh = orig
    print("  cleaned worst: %.5f %%" % (100 * w2), flush=True)

    worstrel = 0.0
    for mat in ("d00", "d76", "d100"):
        for th in TH5:
            a = cells[("composed", mat, th)]
            b = cells[("cleaned", mat, th)]
            if a > 1e-9:
                worstrel = max(worstrel, abs(b - a) / a)
    print("  worst per-cell relative difference: %.2f %%"
          % (100 * worstrel), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
