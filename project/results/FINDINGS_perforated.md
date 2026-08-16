# Perforated pyramids: the holes work, the mouth still decides

`FINDINGS_anechoic_shapes.md` left one idea untested. A hollow pyramid folded
from sheet came second last, but the reason was the **rim** the fold leaves
around its mouth — flat, facing the viewer, 33 % of the mouth at pitch 5.5. The
cavity behind it was never actually measured, only the flat plate in front of
it.

So: a shell with no rim (the skin meets the entrance plane at a knife edge) and
holes in the skin, interior and exterior the same coating. Perforated aluminium
is a stock product. Light that bounces off one pyramid can enter a
neighbour's holes and be trapped in a cavity it cannot easily leave.

## Perforation helps. The shell still loses.

Standard protocol, worst case, 50 mm depth.

| structure | pitch | open area | worst ρ |
|---|---|---|---|
| **solid sharp pyramid** | 5.50 | — | **0.17910 %** |
| shell, unperforated | 5.50 | 0 % | 0.33810 % |
| shell | 5.50 | 35 % | 0.31412 % |
| shell | 5.50 | 55 % | 0.29566 % |
| shell | 5.50 | 70 % | 0.28310 % |
| solid sharp pyramid | 17.67 | — | 0.25254 % |
| shell | 17.67 | 55 % | 0.31960 % |
| shell | 17.67 | 70 % | 0.58643 % |

Holes are worth 16 % (0.338 → 0.283) and the direction is right at both
pitches until the skin runs out at 70 % open on the coarse one. But **the shell
starts 1.9× behind before a single hole is cut**, and no amount of perforation
closes that: a 0.5 mm sheet seen edge-on at the mouth of a 5.5 mm cell is 18 %
of the cell, and 18 % of flat area facing the viewer is what the exposed-area
law says decides everything.

Predictions 1 and 4 held in direction; prediction 1 over-stated the size (I said
~0.45 %, it is 0.28-0.34 %). Prediction 2 — that the coarse pitch would make it
competitive — was **wrong**: at 17.67 the shell loses to the solid pyramid by
the same ratio it does at 5.5.

## Why the holes do so little, measured

Rays cast at the array, ρ = 0.5, 1500 rays. If light reflected off one pyramid
enters a neighbour's holes and dies there, the perforated array must bounce
more and escape less. It does the opposite:

| structure | mean bounces | escaped |
|---|---|---|
| solid sharp pyramid | 1.83 | 6.5 % |
| shell, 0 % open | 1.78 | 11.4 % |
| shell, 35 % open | 1.78 | 11.4 % |
| shell, 70 % open | 1.71 | 14.1 % |

0 % and 35 % are **identical to four figures**, which is the clue. Rasterising
the array from above:

| open area on the face | 0 % | 35 % | 70 % |
|---|---|---|---|
| **occluded seen from above** | 100.0 % | **98.1 %** | 85.8 % |

A pyramid 50 mm deep on a 5.5 mm pitch has faces **3.1° from vertical**. Seen
from the entrance a face is almost edge-on, and each row of tiles covers the row
below's holes. Punching 35 % of the face open opens 2 % of the aperture. Light
arriving down the normal barely finds a hole at all, and a ray that does bounce
off a face 3° from vertical leaves upward rather than crossing to its neighbour.

**The mechanism is real and the geometry starves it.** It needs faces that face
each other, which means shallow pyramids — and the coarse pitch that would give
that costs more at the mouth than the holes give back.

## The sharpest test of the exposed-area law, and it survived

Hole size and sheet thickness move the same ratio in opposite directions. A
thicker sheet makes every hole a better tube — aspect `t/d` — and a worse mouth,
`4t/p`. One knob, two signs. Open area held at 35 %, pitch 5.5:

| sheet | hole | t/d | mouth edge | worst ρ |
|---|---|---|---|---|
| **0.25 mm** | 0.133 mm | 1.88 | **9.1 %** | **0.25349 %** |
| 0.50 mm | 0.266 mm | 1.88 | 18.2 % | 0.31412 % |
| 0.50 mm | 0.133 mm | 3.75 | 18.2 % | 0.30176 % |
| 0.50 mm | 0.089 mm | 5.63 | 18.2 % | 0.29565 % |
| 1.00 mm | 0.133 mm | 7.51 | 36.4 % | 0.39368 % |

* **Shrinking the hole at fixed thickness**: 0.266 → 0.089 mm buys 5.9 %.
* **Halving the thickness**: 0.5 → 0.25 mm buys **19 %**.
* **Doubling the thickness**: 30 % worse, even though the hole aspect rises
  from 1.88 to 7.51 — a four-fold better bore.

**The mouth is worth roughly three times the bore, and it wins outright when
they conflict.** Prediction 3 said exactly this and it is the cleanest evidence
the study has for the law, because for once the two effects were opposed rather
than aligned.

Prediction 2 named 0.24-0.26 % for the best shell. It is 0.25349 %, against the
solid pyramid's 0.17910 %.

## What to take from it

The perforated shell is **not** a better absorber than a solid sharp pyramid and
nothing in the parameter range brings it closer than 1.4×. What it is: a stock
sheet part, which a solid pyramid is not, at a cost that is now quantified.

If it is pursued, the ranking of levers is settled and unusual — **thin sheet
first, then hole size, and open area last**. The instinct to punch more or
bigger holes is the weakest of the three, and thickening the plate to make the
holes into better tubes is actively wrong.

The one configuration that has not been measured is the one the mechanism wants:
a **shallow** perforated pyramid, where faces see each other and reflected light
actually crosses into a neighbour. Every version here is a spike 3-10° from
vertical, which is the wrong shape for the effect it was built to exploit.

## A naming collision, fixed

`AN_pyr_a909` meant pitch 5.5006 in `sweep_anechoic.csv` (50 / 9.09) and pitch
5.5 in `sweep_perf.csv` — two designs under one tag, reading 0.18151 % and
0.17910 %, a 1.34 % difference that looks like a measurement disagreement and is
a naming one. The solid-pyramid rows in `sweep_perf.csv` are now tagged
`SP_p0550` and `SP_p1767`, after the pitch they actually have.

## Reproduce

    Blender --background --factory-startup --python scripts/sweep_perf.py
    Blender --background --factory-startup --python scripts/sweep_perf2.py
