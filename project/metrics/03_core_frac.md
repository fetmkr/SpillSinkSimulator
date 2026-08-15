# 03 · core fraction — RETIRED

**Status:** RETIRED 2026-08-11 · superseded by [02 smear rms](02_smear_rms.md)
and [04 peak radiance](04_peak_radiance.md)

## What it was

The fraction of the returned energy landing within the central 10 mm of the
line-spread profile. 1.0 meant the line came back intact; a small value was
supposed to mean it came back as a formless smear.

## Why it was retired

**It is a ratio whose denominator shrinks with the thing it is measuring.**

The denominator is the energy inside the measurement window. Once a design
smears the line far enough that some of the return leaves the window, that
energy leaves the denominator too — so the score *improves*. Measured
demonstration: a cone at depth 120 has **twice** the rms smear of one at depth
50 (13.17 mm vs 6.79 mm) and yet a **higher** core fraction.

So the metric inverts exactly where it matters most, on the designs that
destroy form best.

## What it cost

The claim "the cone returns core 0.11 where the groove returns 0.99" reached
two reports. Both figures were also taken from designs that were not the ones
being compared. The qualitative conclusion survived re-measurement; the numbers
did not.

## What replaced it

- **rms smear** ([02](02_smear_rms.md)) — no denominator problem, ranks the
  designs monotonically.
- **peak radiance ratio** ([04](04_peak_radiance.md)) — the quantity that
  actually decides whether the wall copy is visible.

Do not reintroduce a "fraction of energy inside a fixed window" metric without
first widening the window until truncated energy is under 1% and *proving* it.
