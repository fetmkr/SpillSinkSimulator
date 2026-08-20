"""Which part of the structure is each face? Derived, never tabulated.

A SLOT IS A PART, NOT A FACET. Two faces belong to the same slot when a
fabricator would finish them in one operation. A honeycomb's foil wall has two
sides and nobody has ever anodised one of them differently.

------------------------------------------------------------------------------
WHY THIS IS DERIVED FROM THE MESH RATHER THAN TAGGED BY THE BUILDERS

The obvious alternative is to have each `build_mesh` label its own faces. It
was considered and rejected for this pass:

  * it needs an edit in every one of nine geometry modules, all of which are
    the most heavily-validated code in the project, to add data that can be
    recovered exactly from geometry that is already there;
  * a tag and a face list are two things that must stay in step, and every
    operation that rebuilds faces -- `clip_to_panel`'s Sutherland-Hodgman,
    fan triangulation, `geom_stack`'s slab strip -- is another place they can
    drift apart silently;
  * `prebuilt_mesh` callers and any family added later would carry no tags.

The rules below are exact, not heuristic: an up-facing face IS the surface a
head-on observer strikes, whatever built it. `uses()` in sim_server makes the
same argument about field lists -- a hand-written one "is exactly the thing
that goes stale" -- and a stale slot table is worse, because the panel renders
with the wrong finish on a third of its area and every number still looks
plausible.

WHAT THIS CANNOT DO, and it is worth being clear: a depth band. A honeycomb
wall is ONE quad from y = 0 to y = -50, so "paint reaches 10 mm" is not a
partition of the faces at all -- it needs the polygon cut. That is a separate
operation and does not belong here.

------------------------------------------------------------------------------
COORDINATES.  x across the face, y depth (entrance plane at 0, deeper
negative), z vertical.  Faces are 3- or 4-index tuples, wound outward.
"""

# cos of the half-angle that counts as facing the sky. 0.5 is 60 degrees from
# vertical: generous enough that a shallow pyramid's flank does not read as a
# tip, tight enough that a wall crown always does.
UP = 0.5

TIPS, WALLS, BASE, HIDDEN = 0, 1, 2, 3

SLOTS = [
    {"key": "tips", "id": TIPS, "label": "tips", "assignable": True,
     "why": "Everything that faces the sky -- wall crowns, tip flats, cone "
            "apex discs. One bounce here and the light leaves with the beam's "
            "position intact, which is why this is the surface the whole "
            "study is about. On honeycomb 6.5/0.08 it is under 1 % of the "
            "area and it sets the answer."},
    {"key": "walls", "id": WALLS, "label": "inner sides", "assignable": True,
     "why": "The structure's flanks. One part, one finish: a foil wall's two "
            "faces were never finished separately. This is where light must "
            "survive several bounces to be destroyed, and it is almost all of "
            "the area."},
    {"key": "base", "id": BASE, "label": "base", "assignable": True,
     "why": "The floor under the structure -- a shaped floor layer, or the "
            "slab the cells stand on. A separate part in every real build, "
            "painted flat before assembly, which is why it gets its own "
            "finish rather than inheriting the tube's."},
    {"key": "hidden", "id": HIDDEN, "label": "hidden (unlit)",
     "assignable": False,
     "why": "Downward faces buried inside the interpenetrating union, plus "
            "the backing slab's underside and rim. No light reaches these. "
            "Listed so the areas add to 100 % -- a slot that silently "
            "vanishes is a slot that looks forgotten."},
]

BY_KEY = {s["key"]: s for s in SLOTS}
BY_ID = {s["id"]: s for s in SLOTS}
ASSIGNABLE = [s["key"] for s in SLOTS if s["assignable"]]


def _tri_normal_area(a, b, c):
    """Unnormalised normal and twice the area of one triangle."""
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    return nx, ny, nz, (nx * nx + ny * ny + nz * nz) ** 0.5


def face_normal_area(verts, face):
    """Area-weighted normal of a polygon, and its area.

    Fan-summed rather than taken from the first triangle: a clipped polygon
    from `clip_to_panel` can have a sliver first triangle whose normal is
    numerically useless while the polygon as a whole is perfectly well defined.
    """
    idx = list(face)
    nx = ny = nz = 0.0
    for k in range(1, len(idx) - 1):
        ax, ay, az, _ = _tri_normal_area(verts[idx[0]], verts[idx[k]],
                                         verts[idx[k + 1]])
        nx += ax
        ny += ay
        nz += az
    L = (nx * nx + ny * ny + nz * nz) ** 0.5
    if L <= 0.0:
        return (0.0, 0.0, 0.0), 0.0
    return (nx / L, ny / L, nz / L), L * 0.5


def slab_at_end(verts, faces):
    """(y_lo, y_hi) if the last 8 verts / 6 faces are the backing slab.

    THE SAME TEST `clip_to_panel` AND `geom_stack` ALREADY MAKE, in one place.
    `geom_stack._build_layer` asserts it outright ("last 6 faces are not the
    slab") and `clip_to_panel` re-detects it to rebuild the slab at panel size,
    so it holds on both the trimmed preview mesh and the measured one.
    """
    if len(faces) < 6 or len(verts) < 8:
        return None
    if not all(len(f) == 4 for f in faces[-6:]):
        return None
    ys = {round(verts[i][1], 3) for f in faces[-6:] for i in f}
    if len(ys) != 2:
        return None
    return min(ys), max(ys)


def classify(verts, faces, depth=50.0, floor_depth=0.0, one_slot=False):
    """-> (ids, stats). One slot id per face, in the order given.

    `one_slot=True` puts everything in `tips` and says so in the stats. It is
    for the 1D extruded families: `sim_server._profile_mesh` extrudes
    cross-section loops without `geom_kit.orient_outward`, so face orientation
    there is not something this tool can trust. Guessing from an untrusted
    normal would put a material on the wrong surface and still look plausible,
    so it degrades loudly instead.
    """
    n = len(faces)
    ids = [WALLS] * n
    areas = [0.0] * n

    slab = slab_at_end(verts, faces)
    n_struct = n - 6 if slab else n
    # A mesh that is NOTHING BUT the slab is the flat control: its top face is
    # the optical surface, not a base to stand something on.
    only_slab = slab is not None and n_struct == 0

    # The floor layer, when a stack has one, is everything at or below the
    # plane where the top layer stops. Exact -- geom_stack shifts the bottom
    # layer by exactly -top_depth -- and tested on the face's HIGHEST vertex so
    # a feature straddling the join is never counted as floor.
    floor_y = None
    if floor_depth and floor_depth > 0:
        floor_y = -(abs(float(depth)) - abs(float(floor_depth))) + 1e-6

    for i, f in enumerate(faces):
        nrm, a = face_normal_area(verts, f)
        areas[i] = a
        if one_slot:
            ids[i] = TIPS
            continue
        if slab is not None and i >= n_struct:
            # the slab: its top face is base (or the control surface), the
            # underside and the four rim quads never see light
            ids[i] = (TIPS if only_slab else BASE) if nrm[1] > UP else HIDDEN
            continue
        if floor_y is not None and max(verts[k][1] for k in f) <= floor_y:
            ids[i] = BASE
            continue
        if nrm[1] > UP:
            ids[i] = TIPS
        elif nrm[1] < -UP:
            # Buried in the union: a wall's foot, a pyramid's base quad. These
            # are inside solid geometry and no ray reaches them. Kept out of
            # `walls` so that the walls area fraction means what it says.
            ids[i] = HIDDEN
        else:
            ids[i] = WALLS

    total = sum(areas) or 1.0
    per = {}
    for i, sid in enumerate(ids):
        d = per.setdefault(sid, [0.0, 0])
        d[0] += areas[i]
        d[1] += 1
    stats = []
    for s in SLOTS:
        if s["id"] not in per:
            continue
        a, c = per[s["id"]]
        stats.append({"key": s["key"], "id": s["id"], "label": s["label"],
                      "faces": c, "area_mm2": round(a, 3),
                      "area_frac": a / total, "assignable": s["assignable"],
                      "why": s["why"]})
    return ids, stats


def slot_rules_json():
    return [{k: s[k] for k in ("key", "id", "label", "assignable", "why")}
            for s in SLOTS]
