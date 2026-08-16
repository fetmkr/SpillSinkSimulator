"""Phase 5.13: the ordering package — export the finalists from the code
that measured them, and pre-register what the printed coupon must read.

    Blender --background --factory-startup --python scripts/sweep_phase513.py

WHY. Q12's lesson: the last time this project tried to order a part, the
export ran different geometry than the measurement (height_seg 3 vs 12,
tileable flag) and the files for the chosen design did not exist at all.
This script builds the coupon meshes with THE SAME build_mesh calls the
sweeps used (only measurement margins removed), writes binary STLs, and
verifies the round trip. It also answers the practical print problem: no
printer holds a 0.05 mm tip at pitch 2 — but the aspect law is
scale-invariant (5 confirmations, p1-p10), so a 2x coupon (p4/d36, tip
tolerance 0.1 mm at the same flat fraction) prints THE SAME optics with
achievable features. The 2x coupon's numbers are pre-registered here so
the physical measurement has its target before the part exists.

    EXPORTS (face 60 x 60 + 2 mm backing, no margins):
      pyr_p2_d18_t005.stl     the spec (tips beyond most printers - for CNC/mould quotes)
      pyr_p4_d36_t010.stl     2x print coupon, SLA-feasible tip
      cone_p2_d18_r003.stl    the spec (mould quotes)
      cone_p4_d36_r006.stl    2x print coupon

    PREDICTIONS, numeric, before any render or write.

    P1  ROUND TRIP IDENTITY: each STL re-read has the same triangle
        count, bounds within 1e-5 mm, signed volume within 0.1 %.

    P2  KERNEL CLEANLINESS: every export passes mesh_check (closed,
        every edge on 2 faces, outward-oriented components).

    P3  THE 2x PYRAMID COUPON MEASURES THE SPEC: p4/d36/t0.1
        (f 0.0625 %) totals 0.130 ± 8 % (aspect law, 6th confirmation),
        head-on 0.035 ± 0.007 (the f-law value the 1x spec carries at
        t0.05), span <= 1.6x.

    P4  ITS SMEAR IS BEAM-CLASS-HONEST: at the protocol's 2 mm stripe a
        4 mm cell reads LOW (beam/pitch 0.5): smear 1.2 - 2.2 — this is
        the number the LAB coupon will show under a narrow probe, and it
        is NOT a defect: at the real 7-14 mm beam the class difference
        compresses (phase 5.5). Registered so nobody panics at the bench.

    ACCEPTANCE BAND FOR THE PHYSICAL COUPON, fixed now: if the printed
    2x pyramid coupon, painted with the fitted Musou and measured over
    theta 0/±20/±40, reads within ±25 % of the P3 totals (the coating
    fit's own residual is 9.5 %), the simulator is validated end-to-end;
    outside ±40 %, something in the chain (paint, print, model) is wrong
    and must be named before any 1 m² order.

Anchor: P5_j00 (identical params to sweep_phase5.csv).
"""

import sys
import os
import csv
import json
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
EXPORT = os.path.join(ROOT, "export")
CSV = os.path.join(RESULTS, "sweep_phase513.csv")
FORMJSON = os.path.join(RESULTS, "form_phase513.json")
OUT = "/tmp/phase513"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
PYR2X = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 36.0,
         "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0, "backing": 2.0}

S = 2.0 / 5.5


def coupon_params():
    """(name, family, params) for the four export files — margins ZERO:
    the printed part is the face, not the measurement scaffolding."""
    return [
        ("pyr_p2_d18_t005", "floor",
         {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 18.0,
          "pitch": 2.0, "tip_flat": 0.05, "margin_depths": 0.0,
          "backing": 2.0}),
        ("pyr_p4_d36_t010", "floor",
         {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 36.0,
          "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 0.0,
          "backing": 2.0}),
        ("cone_p2_d18_r003", "cone3d",
         {"face_w": 60.0, "face_h": 60.0, "depth": 50.0 * S, "pitch": 2.0,
          "tip_radius": 0.03, "jitter": 0.3, "depth_jitter": 0.0,
          "profile_power": 1.0, "radial_seg": 24, "height_seg": 12,
          "seed": 23, "margin_depths": 0.0, "backing": 2.0}),
        ("cone_p4_d36_r006", "cone3d",
         {"face_w": 60.0, "face_h": 60.0, "depth": 100.0 * S, "pitch": 4.0,
          "tip_radius": 0.06, "jitter": 0.3, "depth_jitter": 0.0,
          "profile_power": 1.0, "radial_seg": 24, "height_seg": 12,
          "seed": 23, "margin_depths": 0.0, "backing": 2.0}),
    ]


def build(family, prm):
    if family == "floor":
        from geom_floor import FloorParams, build_mesh
        return build_mesh(FloorParams(**prm))
    from geom3d import Cone3DParams, build_mesh
    return build_mesh(Cone3DParams(**prm))


def triangulate(faces):
    """Fan-triangulate faces of any arity (the kernel emits quads)."""
    out = []
    for face in faces:
        for i in range(1, len(face) - 1):
            out.append((face[0], face[i], face[i + 1]))
    return out


def write_stl(path, verts, faces):
    import numpy as np
    v = np.asarray(verts, dtype=np.float64)
    f = np.asarray(triangulate(faces), dtype=np.int64)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.where(ln > 0, ln, 1.0)
    with open(path, "wb") as fh:
        fh.write(b"SpillSink coupon, built by the measuring code".ljust(80))
        fh.write(struct.pack("<I", len(f)))
        blk = np.zeros((len(f),), dtype=[("n", "<3f4"), ("v", "<9f4"),
                                         ("attr", "<u2")])
        blk["n"] = n.astype("<f4")
        blk["v"] = tri.reshape(len(f), 9).astype("<f4")
        fh.write(blk.tobytes())


def read_stl(path):
    import numpy as np
    with open(path, "rb") as fh:
        fh.seek(80)
        nf = struct.unpack("<I", fh.read(4))[0]
        blk = np.frombuffer(fh.read(), dtype=[("n", "<3f4"), ("v", "<9f4"),
                                              ("attr", "<u2")], count=nf)
    return blk["v"].reshape(nf, 3, 3).astype(np.float64)


def signed_volume(tris):
    import numpy as np
    return float(np.einsum('ij,ij->i', tris[:, 0],
                           np.cross(tris[:, 1], tris[:, 2])).sum() / 6.0)


def main():
    import numpy as np
    import blender_render as BR
    import form_buildable as FB
    import mesh_check as MC
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(EXPORT, exist_ok=True)
    print("=" * 74)
    print("PHASE 5.13 — the ordering package")
    print("=" * 74)

    # --- exports + round trip + kernel check -------------------------------
    manifest = {}
    for name, family, prm in coupon_params():
        v, f = build(family, prm)
        v = np.asarray(v)
        ftri = np.asarray(triangulate(f), dtype=np.int64)
        path = os.path.join(EXPORT, name + ".stl")
        write_stl(path, v, f)
        tris = read_stl(path)
        tri0 = v[ftri]
        db = np.abs(np.array([tri0.min(0).min(0), tri0.max(0).max(0)])
                    - np.array([tris.min(0).min(0), tris.max(0).max(0)]))
        vol0, vol1 = signed_volume(tri0), signed_volume(tris)
        rep = MC.check(v, f, name=name)
        clean = bool(rep.get("clean"))
        ok = (len(tris) == len(ftri) and db.max() < 1e-5
              and abs(vol1 - vol0) / abs(vol0) < 1e-3)
        manifest[name] = {
            "file": os.path.basename(path), "tris": int(len(ftri)),
            "bounds_mm": [list(map(float, v.min(0))),
                          list(map(float, v.max(0)))],
            "volume_mm3": round(vol0, 2), "roundtrip_ok": bool(ok),
            "mesh_clean": bool(clean), "params": prm, "family": family}
        print("  %-20s tris %7d  vol %10.1f mm3  roundtrip %s  clean %s"
              % (name, len(f), vol0, "OK" if ok else "FAIL",
                 "OK" if clean else "FAIL"), flush=True)
    json.dump(manifest, open(os.path.join(EXPORT,
                                          "finalists_manifest.json"), "w"),
              indent=1)

    # --- the 2x coupon's target numbers ------------------------------------
    DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
    THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
    rows = []
    for tag, prm in (("P5_j00", ANCHOR), ("P513_pyr2x", PYR2X)):
        pj = json.dumps(dict(prm, winding="out"), sort_keys=True)
        w = 0.0
        for mat in ("d00", "d76", "d100"):
            body, spec = BR.coating_split(DF[mat])
            for th in THETAS:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": "floor", "out_dir": OUT,
                       "results_dir": OUT, "samples": 64, "res_x": 480,
                       "res_y": 220, "gpu": True, "spec_roughness": 0.30,
                       "params": prm,
                       "renders": [{"mode": "hemi_view", "theta": th}],
                       "material_mode": "coating",
                       "coating": {"body": body, "spec_scale": spec,
                                   "roughness": 0.30}}
                cfg.update({k: v2 for k, v2 in COAT.items()
                            if k != "spec_roughness"})
                res = BR.run(cfg)
                rec = list(res["modes"].values())[0]
                w = max(w, rec["panel"]["mean"])
                rows.append({"tag": tag, "family": "floor",
                             "topology": "pyramid", "seed": 23,
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-12s worst %.5f %%" % (tag, 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=["tag", "family", "topology",
                                              "seed", "diffuse_frac",
                                              "theta", "rho", "control",
                                              "params_json"])
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    print("\n=== form: P513_pyr2x ===", flush=True)
    entry = {"tag": "P513_pyr2x", "family": "floor", "topology": "pyramid",
             "process": "print", "params": PYR2X, "pitch": 4.0}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["span_0"] = z["peak_ratio_span"] if z else None
    rec["winding"] = "out"
    fout["P513_pyr2x"] = rec
    print("  smear %.3f  head-on %.5f  span@0 %.2fx"
          % (rec["smear"], rec["head_on"], rec["span_0"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
