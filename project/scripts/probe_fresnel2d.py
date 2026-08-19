"""Phase 10.2 — does the wedge plate work from EVERY azimuth?

The 1D prism plate (10.1) is a chopped-up tilted window: grooves run
horizontally, so it can only fold light in one plane. The user's question:
make it 2D so any approach azimuth is folded somewhere useful.

Four plates, identical thickness and material (acrylic n=1.49, prism 30 deg,
under the 42.2 deg TIR cliff found in 10.1), all tilted 15 deg top-hinge:

  W1   1D grooves, horizontal        (10.1's F15 -- the incumbent)
  W2   1D grooves, VERTICAL          (folds sideways instead of down)
  W3   2D pyramid wedges (square grid, both slopes toward one corner)
  W4   2D "hip roof" cells: four faces per cell, all sloping to the cell's
       low edge -- folds every azimuth toward the same downward quadrant

Metric: the phase-8 audience matrix at THREE azimuths. The sun is placed at
(theta, phi) and the observer camera sits at eye level or below, in the
theta plane. phi rotates the PLATE about its normal, exactly as the panel
sweeps do -- the plate's own geometry meets the beam from a different
compass direction while the rig stays put.

PRE-REGISTERED (before rendering):
  P1  W1 keeps its zeros at phi 0 but leaks at phi 90 (grooves parallel to
      the tilt plane cannot fold that beam): >= one audience cell above the
      flat-Musou level.
  P2  W2 is W1's mirror image: clean at phi 90, leaking at phi 0.
  P3  W3 (pyramid wedges) splits each beam into two folded branches and
      lands at most cells dark, but a diagonal (phi 45) beam finds the cell
      diagonal and returns a specular branch into the audience band.
  P4  W4 is the only one dark in all 45 cells (3 phi x 5 theta x 3 obs).
      If it holds, a 15 deg plate replaces the 35 deg hopper at ANY azimuth.
"""
import os
import sys
import math
import json

HERE = "/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts"
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import blender_render as BR  # noqa: E402
from geom_floor import FloorParams  # noqa: E402
from probe_fresnel import make_glass, black_surroundings  # noqa: E402

OUT = "/tmp/simsrv/fresnel2d"
os.makedirs(OUT, exist_ok=True)

FACE = 60.0
PWIN = FloorParams(kind="pyramid", face_w=FACE, face_h=FACE, depth=22.0,
                   pitch=4.0, margin_depths=2.0)
SUNS = [0.0, 20.0, 40.0, -20.0, -40.0]      # the five measured angles
OBS = [0.0, -10.0, -20.0]                   # eye level and below
PHIS = [0.0, 45.0, 90.0]
PRISM = 30.0
PITCH = 3.0
THICK = 3.0
TILT = 15.0


def _tilt(verts, tilt_deg):
    """Rotate about the plate's top edge (z=+FACE/2, y=0); bottom swings -y."""
    t = math.radians(tilt_deg)
    ct, st = math.cos(t), math.sin(t)
    zt = FACE / 2.0
    out = []
    for (x, y, z) in verts:
        dz = z - zt
        out.append((x, y * ct + dz * st, zt + (-y * st + dz * ct)))
    return out


def _finish(verts, faces, name):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(make_glass("gl_" + name))
    return ob


def plate_1d(vertical=False):
    """Sawtooth along z (or x if vertical). Closed solid, flat front at y=0."""
    h = PITCH * math.tan(math.radians(PRISM))
    n = int(FACE / PITCH)
    verts, faces = [], []
    prof = []                       # (y, s) along the grooved axis s
    for k in range(n):
        s0 = k * PITCH
        prof.append((-THICK - h, s0))
        prof.append((-THICK, s0 + PITCH))
    ring = [(0.0, 0.0), (0.0, FACE)] + list(reversed(prof))
    m = len(ring)
    if vertical:
        # grooves run vertically: profile varies with x, extruded along z
        ids0 = [len(verts) + i for i in range(m)]
        verts += [(s, y, -FACE / 2.0) for (y, s) in ring]
        ids1 = [len(verts) + i for i in range(m)]
        verts += [(s, y, FACE / 2.0) for (y, s) in ring]
    else:
        ids0 = [len(verts) + i for i in range(m)]
        verts += [(0.0, y, s - FACE / 2.0) for (y, s) in ring]
        ids1 = [len(verts) + i for i in range(m)]
        verts += [(FACE, y, s - FACE / 2.0) for (y, s) in ring]
    for i in range(m):
        faces.append((ids0[i], ids0[(i + 1) % m],
                      ids1[(i + 1) % m], ids1[i]))
    faces.append(tuple(ids0))
    faces.append(tuple(reversed(ids1)))
    return _finish(_tilt(verts, TILT), faces, "w1v" if vertical else "w1h")


def plate_2d(hip=False):
    """Back face is a grid of cells. Each cell is a shallow pyramid (hip=False)
    or a four-face hip roof whose faces all drain toward the cell's low
    corner/edge (hip=True). Front face flat at y=0; a rim skirt closes it."""
    h = (PITCH / 2.0) * math.tan(math.radians(PRISM))
    n = int(FACE / PITCH)
    verts, faces = [], []

    def V(x, y, z):
        verts.append((x, y, z))
        return len(verts) - 1

    # back surface grid, y depends on position within the cell
    for i in range(n):
        for j in range(n):
            x0, z0 = i * PITCH, j * PITCH - FACE / 2.0
            c = (x0 + PITCH / 2.0, z0 + PITCH / 2.0)
            if hip:
                # four faces sloping to the cell's LOW edge (z0 side):
                # apex ridge at the high edge, valley at the low edge
                a = V(x0, -THICK, z0)
                b = V(x0 + PITCH, -THICK, z0)
                cc = V(x0 + PITCH, -THICK - h, z0 + PITCH)
                d = V(x0, -THICK - h, z0 + PITCH)
                mid = V(c[0], -THICK - h / 2.0, c[1])
                faces += [(a, b, mid), (b, cc, mid), (cc, d, mid), (d, a, mid)]
            else:
                a = V(x0, -THICK, z0)
                b = V(x0 + PITCH, -THICK, z0)
                cc = V(x0 + PITCH, -THICK, z0 + PITCH)
                d = V(x0, -THICK, z0 + PITCH)
                apex = V(c[0], -THICK - h, c[1])
                faces += [(a, b, apex), (b, cc, apex),
                          (cc, d, apex), (d, a, apex)]
    # flat front + skirt (a simple box lid; interior overlap is fine for a
    # solid glass body -- Cycles integrates the union of closed shells)
    f0 = V(0.0, 0.0, -FACE / 2.0)
    f1 = V(FACE, 0.0, -FACE / 2.0)
    f2 = V(FACE, 0.0, FACE / 2.0)
    f3 = V(0.0, 0.0, FACE / 2.0)
    b0 = V(0.0, -THICK, -FACE / 2.0)
    b1 = V(FACE, -THICK, -FACE / 2.0)
    b2 = V(FACE, -THICK, FACE / 2.0)
    b3 = V(0.0, -THICK, FACE / 2.0)
    faces += [(f0, f1, f2, f3), (b3, b2, b1, b0),
              (f0, f3, b3, b0), (f1, b1, b2, f2),
              (f0, b0, b1, f1), (f3, f2, b2, b3)]
    return _finish(_tilt(verts, TILT), faces,
                   "w4_hip" if hip else "w3_pyr")


def rotate_plate_phi(ob, phi_deg):
    """Spin the plate about the panel normal (y), around the face centre."""
    if abs(phi_deg) < 1e-9:
        return
    a = math.radians(phi_deg)
    ca, sa = math.cos(a), math.sin(a)
    cx, cz = FACE / 2.0, 0.0
    for v in ob.data.vertices:
        x, z = v.co.x - cx, v.co.z - cz
        v.co.x = cx + x * ca - z * sa
        v.co.z = cz + x * sa + z * ca
    ob.data.update()


def run(tag, builder):
    res = {}
    for phi in PHIS:
        BR.clear_scene()
        ob = builder()
        rotate_plate_phi(ob, phi)
        black_surroundings()
        BR.configure_cycles(192, True)
        w_panel, _ = BR.measurement_windows(PWIN, FACE + BR.GAP, None)
        for sun in SUNS:
            for oe in OBS:
                for o in list(bpy.data.objects):
                    if o.type in ("LIGHT", "CAMERA"):
                        bpy.data.objects.remove(o, do_unlink=True)
                BR.setup_camera(FACE / 2.0, 0.0, FACE * 1.4, 480, 220,
                                elev_deg=oe)
                BR.set_world(0.0)
                sun_ob = BR.add_sun(sun, strength=1.0, angular_size_deg=0.5)
                # the lamp disc itself must never be photographed: at negative
                # elevations it drifts into frame and every geometry reported
                # the SAME 144.4 (2026-08-19) -- an instrument artifact, not a
                # panel return
                sun_ob.visible_camera = False
                name = "%s_p%02.0f_s%+03.0f_o%+03.0f" % (tag, phi, sun, oe)
                exr = os.path.join(OUT, name + ".exr")
                BR.render_to(exr, os.path.join(OUT, name + ".png"))
                arr = BR.read_exr(exr, 480, 220)
                v = BR.window_stats(arr, BR.to_pixel_window(w_panel))["mean"]
                res["p%.0f_s%+.0f_o%+.0f" % (phi, sun, oe)] = v
                if v > 1e-6:
                    print("[%s] phi %2.0f sun %+3.0f obs %+3.0f  %.6f  <<"
                          % (tag, phi, sun, oe, v), flush=True)
        print("[%s] phi %2.0f done, worst %.6f"
              % (tag, phi, max(v for k, v in res.items()
                               if k.startswith("p%.0f_" % phi))), flush=True)
    return res


def main():
    res = {}
    res["W1_grooves_horizontal"] = run("w1h", lambda: plate_1d(False))
    res["W2_grooves_vertical"] = run("w1v", lambda: plate_1d(True))
    res["W3_pyramid_wedges"] = run("w3", lambda: plate_2d(False))
    res["W4_hip_cells"] = run("w4", lambda: plate_2d(True))
    with open(os.path.join(OUT, "fresnel2d_results.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    for k, v in res.items():
        print("SUMMARY %-24s worst %.6f  nonzero cells %d/%d"
              % (k, max(v.values()), sum(1 for x in v.values() if x > 1e-6),
                 len(v)))
    print("@@DONE@@")


if __name__ == "__main__":
    main()
