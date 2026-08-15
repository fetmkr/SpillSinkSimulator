# VOID — extruded families were measured against their own edge (2026-08-15)

`blender_render.loops_to_object` extruded a 1D cross-section exactly `face_w`
long. `margin_depths` widens those families in Z only; along the extrusion axis
there was never any margin at all.

Found by adding a `phi_deg` axis and rotating a V-groove 90 degrees, which put
the un-margined axis into the camera's tilt plane:

    V-groove 13 mm, seed 23, d76, theta -40
      phi  0    0.30055 %   (published)
      phi 90   27.21208 %   -- 24x a 1.14 % flat plate. Impossible.

The control patch read exactly 0.0500 at every phi, so the rotation itself was
sound; the panel simply ran out before the window did.

## The part that is NOT just about rotation

Re-measuring at phi = 0 with the extrusion overrun added:

    theta      0      -40     +40
    before   0.15721  0.30055  0.28333 %
    after    0.13917  0.28087  0.26303 %
             -11.5%   -6.5%    -7.2%

**So phi = 0 was wrong too.** At theta +-40 the window reaches the panel's own
X edges and sees the open ends of the grooves. Every number this project has
published for an extruded family -- V-groove, slat, trough -- is high by
roughly 6-12 %.

## Voided

    __void__sweep_azimuth_extrusion.csv   1575 rows (vgroove invalid at all
                                          phi; the 3D families in it are fine
                                          but are re-run together for one
                                          consistent file)
    __void__sweep_phase1_extrusion.csv     225 rows (the V-groove arm)

Also affected and NOT yet re-measured: `sweep_ridge*.csv`, `sweep_v2.csv`,
`sweep_fairfight.csv`, and the "V-groove 13 mm = 0.3863 %" figure carried as a
preset in the simulator. Those belong to phase 1, which was already flagged as
not being on the current ruler.

Not affected: every 3D family. `geom3d`, `geom_topo`, `geom_cell`, `geom_stack`
and `geom_floor` build explicit meshes that already cover face + margin in both
directions, and they never go through `loops_to_object`.

## Fixed

`loops_to_object` is now called with `face_w + 2m` and `x0 = -m`, m being the
same margin the cross-section gets.
