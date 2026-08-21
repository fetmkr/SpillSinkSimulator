# Working journal — 2026-08-12 → 13

Kept because the session can die and the reasoning is worth more than the
numbers. Newest at the bottom. `results/*.md` hold the finished findings; this
holds how they were arrived at, including the wrong turns.

---

## The through-line of the last two days

**The same error class has now appeared three times, and each time it put an
unmanufacturable feature at the top of a ranking.**

1. **The 8x tip mismatch.** The 2026-08-12 report claimed shingle beat cone by
   29%. The shingle used a 0.05 mm plate edge, the cone a 0.4 mm tip. Matched at
   0.4 mm the cone wins and seven of nine families sit inside 1.11x. The report
   was published before this was checked. `results/PEER_REVIEW.md` found it.
   **CONTEXT.md:503 records the project catching the identical error once
   before, in the "fair fight", and I had read and summarised that section
   earlier the same session.**

2. **The feature axis was still wrong.** Fixing (1) by holding minimum feature
   common assumed a common process. Aluminium honeycomb is a bought commodity
   with 0.03-0.1 mm foil; a cone is moulded or printed at 0.4 mm. Comparing them
   at a "matched" 0.4 mm penalises the honeycomb for a constraint it does not
   have. Hence `sweep_buildable.py`, where each family sits at what its own
   process delivers.

3. **CELLNEST, 2026-08-13.** The current darkness leader is a nested cell at
   **wall 0.1 mm, 50 mm deep, 11 mm cell** — the wall is 1:500 thickness to
   height. It is labelled `process = print` and **cannot be FDM printed**
   (0.4 mm nozzle floor), is not expanded foil (that is a regular hexagon, not
   an irregular Voronoi with a floor lattice), and has no demonstrated sheet
   route. `sweep_buildable.py`'s docstring says "0.1 mm walls, optimistic for
   FDM, kept for comparison" — but the ranking output does not carry that
   caveat, so it reads as the winner. **Seen by rendering it
   (profiles/097) and looking, not from the numbers.**

**The pattern:** an optimiser will always walk to the edge of whatever box it is
given, and the box is set by parameters chosen for convenience. Every ranking in
this project has to state the process and the minimum feature next to the
number, or it ranks the box rather than the design.

---

## What was settled, with the measurement that settled it

| claim | number | how |
|---|---|---|
| structure vs flat, same coating, same footing | **~30x** (6.1218% -> 0.2041%) | flat plate measured over the same 5 thetas and 3 materials |
| between the nine topologies, each at its own process | **1.6x** | `sweep_buildable.csv` |
| coating diffuse fraction | **11.7 % at theta 0, 34.4 % at theta -40** on the order spec, opposite signs; flat plate 0.2 % / 6.9 % | `gate_diffuse_fraction.py`, 2026-08-21. The old "41x, rank inversion" was withdrawn in CONTEXT.md and is struck here too |
| coating specular roughness, on theta=0 form peak | **332x** (0.10 -> 0.50) | `FINDINGS_form_baseline.md` |

An earlier framing of mine — "coating beats geometry" — conflated the first two
rows. The user caught it. **Correct statement: having a structure is decisive
(30x); which structure is nearly irrelevant (1.6x); and two unmeasured coating
parameters sit above both.**

## Things that turned out to be non-problems

- **margin_depths 6.5.** Carried a note "margin 1.0 moves head-on by -15%,
  reason not understood". `test_margin.py` swept 1.0-6.5 on a wall network and a
  pillar array: flat within 3.5%, i.e. inside the realisation noise. The -15%
  does not reproduce at theta <= 40 and was almost certainly measured with
  grazing angles in the set. Margin is now 2.0, which is what made 0.86 mm cells
  computable (14.2 M faces -> 1.9 M).
- **The theta=0 form peak > 1.** Not the lamp (visible_camera on/off identical
  to six decimals), not `recentre` (raw and recentred agree to four decimals).
  It is the coating: a flat plate of the same coating reads 1.64 where the
  structured panel reads 1.34. The baseline was wrong, not the measurement.

## Things that are still wrong or unfinished

- `form_roughness` was added to `run_queue.sh` while the queue was RUNNING, and
  zsh had already parsed the loop body, so it silently did not run. A restart is
  armed for when `sweep_seeds` finishes. **Edit the queue only when it is idle.**
- The flat control plate sits inside the panel field (`GAP` 100 mm vs a field
  reaching 160 mm at margin 2.0). Absolute rho_dh is unaffected — measured — but
  every ratio against the control is. Not yet fixed.
- Honeycomb is 4th on darkness and LAST on form: smear 0.96x, i.e. **narrower
  than a flat wall**, MTF 0.970. Vertical-walled cells trap light but do not
  move it sideways, so the line comes back where it went in. Shingle is the only
  design in the top 3 of both.
- No experiment. Nothing here has been built or measured. Kaster 2025 (JAP 138
  174904, Carl Zeiss AG) is the same: simulation only, and it reports 0.65x
  average reduction where we report ~0.03x. **That gap has to be explained
  before any comparison is published.**

## Supervision, and why it is on disk

Two failures drove this:
- sweep_topo finished at 00:34 and nothing started the next job for **eight
  hours**, because the only thing that ever started a job was a chat turn.
- A watchdog *agent* was tried and terminated after four minutes while
  reporting it was "standing by". An agent lives inside a session.

So: `run_queue.sh` (job loop, survives a crashing job) + `keepalive.sh`
(restarts the queue, flags a 45-minute output stall). Both on disk, both
stoppable with `touch logs/STOP`.

---

## 2026-08-22 — 거칠기가 반짝임을 정하고, 우리 값은 논문 밖이었다

**"거칠기는 영향 없다"가 틀렸다.** `form()` 에 `roughness` 인자가 아예 없어서
훑기가 매번 같은 0.30 을 렌더했다. 인자를 이어붙이고 다시 재니 5 % 페인트
민판의 정면 반짝임이 거칠기 0.05 에서 1200.97, 0.60 에서 1.04 다. **1160배.**
모델에서 제일 센 손잡이인데 아무도 안 쟀다.

**거칠기를 그 이름으로 주는 논문은 없다. 그런데 TIS 를 주는 논문이 있다.**
Filip & Vávra 2026 (arXiv:2601.05094) 그림 6 은 재료마다 TIS 를 준다. 정반사
방향 5도 원뿔 **밖**으로 나간 몫이다. 그러니 `1 − TIS` 가 원뿔 **안**에 들어간
몫이고, 그게 광택 덩어리가 얼마나 좁은지를 바로 말해 준다.

우리 BSDF 로 거꾸로 풀었다 (`scripts/gate_roughness_from_tis.py`). 알루미늄에
칠한 무광 아크릴 검정은 정면 TIS 가 0.87~0.90 이다.

  - **확산비율 0.97 은 답이 없다.** 광택이 3 % 뿐이면 5도 원뿔 안에 10 % 를
    못 넣는다. 우리가 쓰던 짝이 실측에 걸려 탈락했다.
  - 답이 되는 짝: 0.90/0.012, 0.80/0.034~0.046, 0.70/0.052~0.064,
    0.50/0.075~0.089. **전부 거칠기 0.01~0.11.** 0.30 은 어떤 확산비율로도 안 나온다.

**두 번째 근거.** Shirsekar 2019 (Virginia Tech 석사) 가 Aeroglaze Z302 의
BRDF 를 고니오미터로 쟀다. 532 nm, 입사 10도에서 제일 밝은 값 대 바닥이 약
440배, 반값 폭 약 8도 → 거칠기 약 0.06. Z302 는 유광이라 위쪽 한계다.
논문은 `reference/papers/` 에 받아 뒀다.

**두 논문이 어긋나 보이던 것도 풀렸다.** DePoy 2014 는 무광 검정을 0.97 로
쟀다. 광다이오드가 약 1 m 거리라 0.6도쯤만 본다. 거칠기 0.046 인 덩어리는
0.6도 안에 1.3 %, 5도 안에 47 % 를 넣는다. DePoy 는 꼭대기만 잡고 어깨를
놓친 것이다. 둘은 확산 0.8 / 거칠기 0.04 에서 동시에 만족된다.

**세 축에 어떻게 오나** (`scripts/gate_paper_pairs.py`, 5 % 페인트 민판):

| 짝 | 총량 밝은쪽 | 뭉개짐 | 정면 반짝임 |
|---|---|---|---|
| 지금까지 0.97/0.30 | 5.014 % | 2.17 mm | 1.90 |
| 0.90/0.012 | 5.046 % | 2.18 mm | **1 143 834** |
| 0.80/0.046 | 5.098 % | 2.17 mm | 11 168 |
| 0.50/0.089 | 5.287 % | 2.17 mm | 1 993 |

**총량은 살아 있고(5.4 % 폭), 뭉개짐도 살아 있고(0 %), 반짝임은 죽었다.**
논문이 허용하는 창 안에서만 574배, 우리가 낸 값과는 최대 60만배 차이다.
반짝임 절대값은 쿠폰 하나를 고니오미터로 재기 전까지 못 쓴다.

**사용자가 어제 물리로 이상하다고 한 게 맞았다.** "정면이면 거울처럼
되돌아 와야 하는데 무슨 저런게 나와?" — 관이 설명한다고 답했는데, 관이
아니었다. 거칠기 0.30 이 칠한 벽의 정면 반사를 눌러 감추고 있었다.

재료 파일에는 `constraint_2026_08_22` 칸으로 창만 적어 두고 기본값은 안
바꿨다. 공개된 66,426 줄이 그 위에 서 있어서 조용히 바꾸면 안 된다.
바꿀지는 `NEXT.md` 2번에 갈래로 적어 뒀다.
