# VOID — comb lattice did not tessellate (2026-08-14)

`geom_topo._build_comb` stepped its hexagon lattice along the wrong two axes:

    shipped:  dx = S*sqrt(3)/2 * ex     dz_row = 1.5*S      odd-COLUMN z shift
    correct:  dx = S * ex               dz_row = 1.5*S/sqrt(3)   odd-ROW x shift

Measured consequence, by point sampling the face at pitch 5.2:

    shipped   30.12 % of the panel area belongs to NO cell
    fixed      0.16 % (sampling noise at the tile boundary)

Those 30 % are open channels running straight down to the flat backing slab,
with no confining wall. Optically that is 30 % flat plate wearing a honeycomb
costume, and it inflates every axis: total reflectance, and above all head-on
brightness, where a flat slab seen at normal incidence is the worst case there
is.

Nothing crashed. The CSV looked fine. The 3D render still read as "a
honeycomb" — the user caught it by eye in the phase 3 report gallery.

## Voided

    __void__sweep_comb_lattice.csv    540 rows, 12 designs x 3 seeds
    __void__sweep_stack_lattice.csv   450 rows — EVERY stack contains a comb
                                      layer, so none survives

Also void: the `CB_*` and `ST_*` rows in `form_buildable.json`, the honeycomb
and stack numbers in `report/2026-08-13` and `report/2026-08-14`, and the
phase 3 conclusion that head-on brightness comes from the flat cell FLOOR —
that was measured against a honeycomb which was 30 % open floor by area, so it
has to be re-tested before it can be claimed.

## Guard added

`geom_topo._assert_tessellates` raises at build time unless each cell shares
exactly 6 of its 6 edges with its neighbours. It fires on the shipped lattice.
