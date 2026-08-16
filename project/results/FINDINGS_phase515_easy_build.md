# Phase 5.15 — the easy-build tier: a half-steep pyramid beats the honeycomb stack where it counts

2026-08-16. Data: `sweep_phase515.csv` (75 rows), `form_phase515.json`
(easy pyramid + stack form). Predictions pre-registered in
`scripts/sweep_phase515.py` (stack head-on band 0.06 ± 0.03 registered in
chat before its run).

## The question (user's)

Aspect-9 tips are hard. Can a LOW pyramid be helped by a structure in
front — specifically a bought honeycomb over a shallow pyramid floor?

## Measurements

| worst over 3 mats × 5θ | φ0 | φ30 | smear | head-on | span | tip req. | panel |
|---|---|---|---|---|---|---|---|
| easy pyramid p4/d20 (aspect 5) | 0.17865 % | 0.25133 % | 4.087 | **0.02718** | 1.01× | ~0.2 mm | 22 mm |
| stack: comb(5.2/0.05) 35 + pyr floor 15 | 0.22488 % | **0.22479 %** | 0.973 | 0.09786 | 1.96× | off-the-shelf comb | 52 mm |

Reference (finalists, worst-φ): cone r0.03 0.212 / head-on 0.0317;
pyramid p2/d18 0.226 / 0.0272.

## Grading

- P1 (easy pyramid φ0 = 0.194 ± 0.012): **miss low, good direction**
  (0.17865) — same small fine-pitch edge p2 showed vs p10; the aspect
  curve's points are pitch-4-and-under generous by a few percent.
- P2 (φ30 = 0.30 ± 0.05): held at the band's floor (0.25133). The
  shallow pyramid's azimuth hole is RELATIVELY milder (+41 % vs the
  aspect-9 field's +74 %).
- P3 (deep floor lifts the stack to 0.165 ± 0.025): **WRONG** — 0.22488,
  indistinguishable from the 2–5 mm-floor stacks of Phase 4. "The top
  layer owns the result" (Phase 3 law) re-confirmed: floor depth is
  irrelevant to totals once a comb sits on it.
- P4 (stack φ-safe, ≤ 25 % move): **HELD spectacularly** — 0.0 % move.
  The user's instinct is measurably right on this axis.
- P5 (easy head-on sharp-class): HELD (0.02718; sharp tips are head-on
  aspect-independent, again).
- Stack head-on (0.06 ± 0.03): **miss high** — 0.09786, 3.6× the
  pyramid; smear 0.973 (a flat wall's class at the 2 mm probe).

## Verdict on the idea

The honeycomb stack wins exactly one thing: azimuth-flat totals (0.225 at
every φ, 11 % better than the easy pyramid's worst-φ 0.251). It loses the
two axes that survive deployment: **head-on 3.6× worse** (comb wall tops
own it — the beam-and-azimuth-proof axis) and form destruction (0.97 vs
4.09 at the probe). It is also 52 mm thick against 22.

**The better "easy" option is the half-steep pyramid itself: p4/d20,
sharp, tip tolerance ~0.2 mm (4× looser than the p2 spec), single pressed
part, 22 mm panel — only 11–19 % behind the hard finalists on worst-φ
totals while matching them exactly on head-on.** The build menu is now a
clean three-row trade of performance vs tooling:

| tier | worst-φ total | head-on | tip req. |
|---|---|---|---|
| cone r0.03 | 0.212 % | 0.0317 | r 0.03 mm |
| pyramid p2/d18 | 0.226 % | 0.0272 | flat ≤ 0.05 mm |
| **pyramid p4/d20 (easy)** | 0.251 % | 0.0272 | flat ~0.2 mm |

Honeycomb's only remaining role would need its head-on solved, and its
head-on is its wall tops — the one thing a honeycomb cannot remove.
