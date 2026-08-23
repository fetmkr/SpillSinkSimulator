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

## 2026-08-22 밤 — 논문 넷을 더 찾았고, 내가 100배 잘못 읽은 걸 찾았다

세 재료의 정반사 실측을 찾아 나섰다. 넷을 찾았고 전부 `reference/papers/` 에 있다.

**검정 아노다이징** — TAMU 2018 (SPIE 10706) 표2. HeNe 633 nm 를 2도 간격으로
훑는 MADLaSR. 정반사 몫 10~44도 평균. 구슬분사 0.07 %, 기계가공 0.15 %,
그대로 0.57 %, 연마(무염색) 0.59 %. **전부 확산 0.99 위다.** 견줌으로 연마
스테인리스 무전해니켈이 76.3 %.

**무광 검정 페인트** — 세 논문이 백 배 갈린다. TAMU 무광 스프레이 0.1 %,
Zeng 2019 (NASA GSFC) Z307 은 0/45 BRF 를 8도 THR 로 나눈 값이 1.008 로
정면에서 램버시안과 1 % 안, Filip 아크릴은 5도 원뿔 안에 10 %.

**무소** — Filip 하나뿐이다. 정면 TIS 0.985~0.995. 완전 확산체도 원뿔에
0.76 % 를 넣으므로 광택 몫은 많아야 0.74 %, 즉 확산 0.9926 위다.
TAMU 도 NASA 도 무소를 안 쟀다.

### 100배 오류는 내 것이었다
**DePoy 2014 그림6 의 세로축은 "Specular Reflectance Ratio (%)" 이고 눈금이
0 에서 1 까지다. 퍼센트다.** 나는 막대를 분수로 읽었다. 0.03 은 0.03 % 다.
아노다이징 확산이 0.97 이 아니라 0.9997, 연마 아노다이징이 0.30 이 아니라
0.993 이다. TAMU 2018 이 같은 재료를 0.07~0.59 % 로 주고 두 논문이
"작은 양의 계통 차이만 두고 일치한다"고 적는데, 퍼센트로 읽어야 맞는다.
재료 11 개 전부 정정했다.

### 어제 쓴 화해 설명도 철회한다
"DePoy 와 Filip 은 광다이오드 크기 차이"라고 5e절에 적었다. 아니다.
GGX 덩어리 하나로는 5도 원뿔이 0.6도 원뿔보다 최대 69.5배 많이 담는데,
0.1 % 와 10 % 를 맞추려면 92.6배가 필요하다. **표면이 다른 것이다.**
Filip 시료는 연마 알루미늄에 얇게 칠한 취미용 스프레이이고 논문 스스로
아래 금속이 비칠 수 있다고 적는다. Shirsekar 도 같은 도료를 1회 칠하면
거칠고 3회 칠하면 광택 난다고 한다.
→ **무광 검정 페인트의 정반사는 상수가 아니라 도장 공정이 정한다.
발주서에 적을 항목이지 찾아 넣을 숫자가 아니다.**

### 법칙 하나가 나왔다
발표된 확산비율 6개 × 거칠기 양 끝을 다 재봤다
(`scripts/gate_specular_published.py`). **반사 총량은 전체에서 0.9 % 안에서만
움직인다** — 어둡기 순위는 이 모든 것에 안 흔들린다. 그리고

    정면 반짝임 − 1 = (1 − 확산비율) ÷ 거칠기⁴

확산에 선형(142.9배 → 135.5배), 거칠기에 네제곱(390,625배 예측 →
398,400 / 379,819 / 399,967 실측). 각도로 한 번, 공간으로 한 번 모이기
때문이다. **쿠폰에서 두 값만 재면 발표된 반짝임 전부를 계산으로 고칠 수
있다. 다시 렌더할 필요가 없다.**

## 2026-08-22 밤 늦게 — 거칠기는 논문에 있었고, 내 단위가 틀렸다

**거칠기 실측을 찾았다.** Ngan/Durand/Matusik 2005 (EGSR) 가 MERL 이 잰
등방성 재료 100 종(재료당 약 백만 점)에 미세면 모델 일곱을 맞춘 보충자료를
낸다. Cook-Torrance 의 m 과 Ward 의 a 가 곧 GGX α 다.

    paint-black 검정 페인트        Ward 0.0367  CT 0.0392
    black-oxidized-steel 검정 금속  Ward 0.198   CT 0.190
    black-obsidian                 Ward 0.0227  CT 0.0239
    fabric-black 검정 천            Ward 0.500   CT 0.650
    견줌 aluminium 거울             Ward 0.00845 CT 0.00776

**검정 페인트 α 0.039 는 Filip TIS 역산 창 0.012~0.089 의 한가운데다.**
서로 아무 관계 없는 두 방법이 같은 답을 냈다.

### 그리고 내 단위 오류
**Cycles 의 Glossy 노드는 슬라이더를 제곱해서 α 로 쓴다.** 나는 논문 α 를
슬라이더에 그대로 넣었다. 0.012 를 넣으려다 0.000144 를 렌더했다. 83 배
뾰족했다. 어제 낸 '574 배 폭', '백만 배', '1/α⁴' 는 전부 여기서 나왔다.

이미 잰 12 점이 증명한다. `(1-df)/(4·슬라이더⁴)` 예측은 오차 0.0~5.4 %,
`(1-df)/(4·슬라이더²)` 예측은 100 % 어긋난다. 슬라이더가 √α 다.

법칙은 교과서 식 그대로다:

    정면 반짝임 = 1 + (1 − 확산비율) ÷ (4 α²)

**슬라이더 0.30 은 α 0.09 이고 Filip 창의 위 끝이 0.089 다. 창 밖이 아니라
가장자리였다.**

### 단위 바로잡고 다시 잰 값 (gate_alpha_units.py, 렌더와 식이 2.2 % 안)

    구슬분사 검정 아노다이징  확산 0.9993  α 0.19   총량 5.000%  반짝임  1.004
    그대로 검정 아노다이징    확산 0.9943  α 0.19   총량 5.003%  반짝임  1.035
    무광 검정 스프레이        확산 0.999   α 0.039  총량 5.000%  반짝임  1.164
    5 % 무광 페인트           확산 0.99    α 0.039  총량 5.004%  반짝임  2.636
    얇게 칠한 아크릴          확산 0.90    α 0.039  총량 5.046%  반짝임 17.36

**칠한 벽의 정면 반짝임은 2.6 배쯤이다.** 백만이 아니었다. 잘 칠하면 1.2 배,
얇게 칠하면 17 배. 검정 아노다이징은 덩어리가 다섯 배 넓어서 거의 안 번쩍인다.

재료 파일에 `lobe.alpha_ggx`(물리값)와 `lobe.roughness`(슬라이더=√α)를
둘 다 적었다. 다시는 헷갈리지 않게.

**배운 것: 논문 값을 코드에 넣기 전에 아는 식으로 먼저 대조한다.**
여기서는 `1 + (1−확산)/(4α²)` 이 그 대조식이었고, 그걸로 단위가 잡혔다.

## 2026-08-22 밤 — 정정된 재질을 실제 설계에 넣고 검증

`scripts/gate_apply_new_materials.py`. 설계 여섯 개, 옛 재질과 새 재질, 세 축.
**옛 재질 팔이 저장된 32가지를 재현하기 전까지 비교를 안 내도록 막았다.**

첫 판에서 검사기가 스스로 멈췄다. 총량은 0.00 % 로 재현되는데 무소 칠한
벌집만 번쩍임이 31.5 % 낮았다. **내 비교 코드 잘못이었다.** 확산비율을
인자로 넘기면 판 전체에 하나가 간다. 무소를 0.99 로 강제하니 팁 아래 5 %
페인트까지 0.99 가 됐다. 32가지는 None 으로 돌아 재료마다 자기 값을 쓴다.
`SS.MATERIALS` 를 갈아끼우는 방식으로 고쳤다. 두 번째 판은 **총량·번쩍임
모두 0.00 % 재현.**

### 결과
| 설계 | 총량 옛→새 | 번쩍임 옛→새 |
|---|---|---|
| 민판 5% 페인트 | 5.014 → 5.004 % | 1.903 → 2.636 |
| 피라미드 p4/d22 | 0.2315 → 0.2320 % | 0.0402 → 0.0560 |
| 벌집 6.35/d30/무소0 | 1.106 → 1.125 % | 1.903 → 2.635 |
| 벌집 6.35/d60/무소15 | 0.2206 → 0.2211 % | 1.873 → 2.591 |
| 벌집 9.53/d40/무소10 | 0.2150 → 0.2158 % | 1.876 → 2.599 |
| 벌집 9.53/d60/무소15 | 0.2081 → 0.2086 % | 1.885 → 2.609 |

**총량 최대 1.7 % 변화, 어둡기 순위 완전히 동일.** 발표된 어둡기 숫자와
순위는 재질 정정을 다 견딘다. 6 만 줄을 다시 렌더할 필요가 없다.

**내 예측 V2 는 틀렸다.** 번쩍임이 내려간다고 적었는데 여섯 설계 전부
정확히 1.38 배 올랐다. α 가 0.09 에서 0.039 로 좁아져 5.3 배 올리고,
확산이 0.97 에서 0.99 로 올라 3 배 내린다. 좁아진 쪽이 이겼다.

### 구조가 정면 번쩍임에 하는 일
민판 식 값: 5 % 페인트 2.6437, 무소 2.1506.

    민판                 2.6358   페인트 식의 0.997 배
    벌집 6.35/d30/무소0   2.6349   페인트 식의 0.997 배
    벌집 6.35/d60/무소15  2.5914   페인트 식의 0.980 배
    벌집 9.53/d40/무소10  2.5990   페인트 식의 0.983 배
    벌집 9.53/d60/무소15  2.6085   페인트 식의 0.987 배
    피라미드 p4/d22        0.0560   페인트 식의 0.021 배

**벌집은 어떤 깊이든 어떤 셀이든 민판과 똑같이 번쩍인다. 2 % 안이다.**
팁에서 15 mm 무소를 칠해도 안 바뀐다 (2.635 → 2.591). 같은 무소가 총량은
1.125 % 에서 0.221 % 로 다섯 배 낮추는데도 그렇다.

**피라미드는 민판의 0.021 배다. 48 배 낮다.**

한 문장으로: **관 속을 정면으로 보는 것은 민판을 보는 것과 같다. 정면
번쩍임을 바꾸는 것은 면을 기울이는 것뿐이다.** 5c 절이 포일 테두리로 얻은
결론과 같고, 이번엔 세 번째 방법으로 다시 나왔다.

작은 실수 하나: 첫 V3 표에서 이름에 '무소' 가 들어간다는 이유로 무소0 설계에
무소 확산비율을 갖다 댔다. 그 설계엔 무소가 없다. 고쳤고, 이제 두 식을 다 낸다.

## 2026-08-22 밤 — 32가지 재측정과 보고서 2판

정정된 재질(페인트 확산 0.99·α 0.039, 무소 0.993)로 **32가지를 값보간이 아니라
실제로 다시 렌더했다.** 약 12분. `results/comb_musou/comb_musou_v2.json`.

**어둡기 순위는 1판과 완전히 같다.** 32가지 전부 최대 1.9 % 만 움직였다.
1위는 양쪽 판 다 셀 9.53 / 깊이 40 / 무소 15 (0.2004 → 0.2009 %).
아까 여섯 개만 비교했을 때 깊이 60 이 1위로 보인 건 그 조합이 표본에
없었기 때문이다.

보고서 2판 `report/comb/comb_musou_2026-08-22.html`, 아티팩트는 1판과 같은
링크로 갈아 끼웠다 (`claude.ai/code/artifact/76342af1-...`). 1판에 틀린
반짝임 값이 살아 있어서 그대로 두면 위험하다. 1판 파일은 디스크에 남는다.

**1판은 손으로 짜서 고칠 수가 없었다. 2판은 `scripts/build_comb_report.py`
가 데이터에서 짓는다.** 설계도 SVG 만 1판 것을 그대로 쓴다.

### 표기 결함 하나 — 사용자가 잡았다
32가지 표의 칸을 "가장 밝은 %" 라고만 적었다. 그 뜻은 "그 설계가 제일 밝게
보이는 각도에서의 값" 인데, 순위표 옆에 그렇게 적히니 **"1위가 제일 밝다"**
로 읽힌다. 숫자와 정렬은 처음부터 맞았다(맨 위 0.2009 %, 맨 아래 1.1262 %).
틀린 건 이름이다.

고친 것: 순위 칸을 따로 만들고 "어두운 순" 이라고 적음. 칸 이름을
"반사 총량 % · 제일 밝은 각도에서" 로 바꾸고 단위를 작은 글씨로 분리.
표 위에 "맨 위가 1위, 가장 어두운 설계입니다" 를 굵게. 그리고 "제일 밝은
각도에서" 가 설계 사이의 순위가 아니라는 문장을 붙였다.

**교훈: 축 이름은 그 값이 무엇인지와 어느 방향이 좋은지를 같이 말해야 한다.**
'가장 밝은' 은 값을 고른 방법이지 성적이 아니다. 순위표 옆에서는 성적으로
읽힌다. [[say-brightest-not-worst]] 의 다음 조항이다.

## 2026-08-23 — 시뮬레이터가 안 뜨던 이유, 그리고 MATERIALS 섹션

### 모델이 안 뜬 건 내가 어제 넣은 회귀였다
브라우저 콘솔에 `ReferenceError: CO is not defined at syncMaterialSliders`.
재료표 `CO` 는 `boot()` 안에서 `const` 로 선언되는데, 어제 커밋 `ba088fc` 에
넣은 `syncMaterialSliders` 와 `materialLine` 은 함수 바깥에 있다. 그 자리에서
`CO` 가 안 보인다. **시작하자마자 터지니 그 뒤 줄이 통째로 안 돌았고, 모델
그리는 줄도 거기 있었다.** 화면은 비어 있고 아무 메시지도 없었다.

고침: `let CO = {}` 를 맨 바깥으로, 1591 줄은 선언이 아니라 대입으로.

**이건 내가 화면을 고치고 화면을 한 번도 안 열어 봤기 때문에 생겼다.**
검사 스크립트는 다 돌렸는데 브라우저는 안 봤다.

서버도 다시 띄웠다. `MATERIALS` 를 불러올 때 한 번만 읽어서 정정된 재료값을
몇 시간이나 안 내보내고 있었다. `mts_worker` 유령도 같이 정리.

### MATERIALS 섹션 (1·2 단계)
3D 앱들이 하는 대로 갔다 -- 재료는 자산, 물건에는 자리(slot), 자리는 재료를
가리킨다. `material/*.json` 은 이미 그 구조였는데 화면에 아무것도 안 보였다.

  - 사이드바에 MATERIALS 섹션. 재료 11 종 목록(색 네모·이름·반사율·
    어느 자리에 쓰이는지 배지·제일 약한 근거등급 한 단어).
  - 그 위에 세 자리 범례 -- 바탕/덧칠/바닥. 자리마다 재료명, 반사율,
    확산, **α**(슬라이더 값이 아니라 물리값. 렌더러가 제곱하므로 슬라이더를
    보여 주면 논문과 못 견준다), 덧칠은 팁에서 몇 mm 인지.
  - `slotMaterials()` 하나가 "이 면에 무엇이 있나" 에 답한다. 범례와 3D 뷰
    색이 같은 함수를 읽으므로 둘이 어긋날 수 없다.

### 3D 뷰 색을 자리별로
분홍/파랑이 셰이더에 박혀 있었다. `cBase`/`cPaint`/`cFloor` uniform 셋으로 바꿨다.

**재료의 진짜 색으로 칠하는 건 안 된다.** 재료가 전부 새까맣다(무소 #2a2d33).
세 면이 다 검어져서 아무 말도 안 하게 된다. 그래서 뷰는 자리별 도식 색을 쓰고,
범례가 그 색과 재료의 진짜 색 네모를 나란히 보여 준다. 지도가 그림 옆에 늘 있다.

예전 규칙("칠한 곳은 분홍, 맨 재료는 파랑")도 버렸다. 산 마감 두 가지가 같은
파랑이 되고, 바닥은 자기 색이 없었다. 이제 벌집+바닥을 놓으면 분홍(덧칠 무소)·
파랑(바탕 아노다이징)·초록(바닥 5% 페인트)이 한눈에 갈린다.

`refresh()` 에 범례 갱신을 걸었다. 이름 목록을 손으로 관리하면 뒤처진다.

### 재료 화면 다시 (같은 날, 지적 받고)
사용자 지적: "머 어쩌자는거지? 선택해서 코팅으로 적용할수 있는거야?
파스텔 톤때문에 보이지도 않고." 둘 다 맞다.

**하나 -- 누를 수 있게 생겼는데 안 눌렸다.** 목록만 보여 주고 적용은 여전히
아래 COATING 드롭다운 셋에서 했다. 같은 걸 세 군데(범례·목록·드롭다운)에서
보여 주는 화면을 만들어 놓고 그 중 하나만 실제로 동작했다.

**둘 -- 색이 안 보였다.** 사이드바는 밝은 배경(`--bg #dedbd4`)인데 태그를
20 % 투명 배경에 옅은 글자로 깔았다. 어두운 뷰포트를 보고 고른 색이었다.
9 px 글자까지 겹쳐서 사실상 안 보인다.

고침:
  - 세 자리 카드를 **누르면 골라진다**(블렌더 슬롯 목록과 같다). 고른 카드에
    테두리가 생기고, 아래 목록이 그 자리가 받을 수 있는 재료만 보여 준다.
  - 목록에서 재료를 누르면 그 자리에 들어간다. 지금 들어 있는 것은 반전 표시.
  - 어느 재료를 보여 줄지는 **숨긴 `<select>` 의 options 를 읽는다.**
    `#deepcoat` 은 산 마감만, `#coat` 은 "안 칠함" 을 포함한다 -- 그 규칙을
    여기 베껴 오면 두 곳이 어긋난다.
  - COATING 의 드롭다운 셋은 **숨기되 DOM 에 남긴다.** `spec()`, 요청 만드는
    곳들, 디자인 저장·불러오기가 전부 그 값을 읽는다. 한 화면에서 같은 선택을
    두 군데 두면 그 둘이 어긋나는 게 이 프로젝트가 계속 겪은 일이다.
  - 색을 진한 단색으로. 사이드바용과 뷰포트용을 따로 둔다(같은 색상, 다른 밝기).

### 그러다 찾은 어긋남 하나 (아직 안 고침)
`floor: none` 이면 요청에 `floor_coating` 이 안 실린다. 그런데 UI 라벨은
"Backing finish -- the plate at the bottom of the wells" 라고 적고 메뉴를
내준다. **고를 수 있게 해 놓고 그 값을 측정에 안 보낸다.** 뷰포트도 그
받침판을 따로 칠하고 있었다.

지금은 범례가 사실대로 "받침판 -- 바탕 재료를 그대로 씁니다" 라고 적고,
뷰포트도 그 자리를 바탕 색으로 칠한다. **제대로 고치면 숫자가 바뀐다**
(받침판이 자기 마감을 갖게 되므로). 그래서 여기서는 안 했다.

### 세 번째 판 -- "무슨 기준으로 어떻게 적용하는지도 모르겠네"
지적 둘: 구조를 고르고 재료를 고르는 순서가 없다, 그리고 무엇이 자리를
나누는지 안 보인다. 두 번째가 진짜였다.

**세 자리를 나누는 경계가 다른 데 있는 컨트롤로 정해진다.** 덧칠 경계는
COATING 의 '덮는 비율' 슬라이더, 바닥 경계는 STRUCTURE 의 floor depth.
카드 세 장만 보고는 알 길이 없었다. 게다가 덮는 비율 슬라이더는 이 섹션
*아래*에 있어서, 카드가 가리키는 숫자에 손이 안 닿았다.

고침:
  - **셀 단면도**를 섹션 맨 위에 그린다. 팁에서 아래로 mm 눈금, 세 띠,
    경계마다 실제 숫자(0 / 12.0 / 34.0 / 40). 자리 색과 같은 색이다.
    바닥은 층이라 깊이 자르기보다 우선한다 -- 렌더러가 그 순서로 칠하므로
    그림도 그렇게 그린다.
  - **카드가 부품 이름을 말한다.** "바탕 · comb 표면 · 산 그대로",
    "덧칠 · 팁에서 아래로 · 덮는 비율이 정함",
    "바닥 · gap 층 · floor depth 가 정함".
  - **끌어다 놓기.** 재료를 카드 위로 끌면 그 자리에 들어간다. 누르는
    길도 그대로 둔다. 안내 문구를 붙였다 -- 아무도 안 알려 준 끌어놓기는
    없는 기능이다.
  - **덮는 비율 슬라이더를 이 섹션으로 옮겼다.** 복사가 아니라 이동이다
    (`insertAdjacentElement`). 노드가 id 와 리스너를 그대로 들고 오므로
    여전히 하나뿐이다. 경계를 정하는 컨트롤은 그 경계 그림 옆에 있어야 한다.

작은 것 하나: 옮긴 슬라이더의 설명이 한 줄로 뭉쳤다. `.nm` 이 다른 데서
`display:flex` 라 글자와 주석이 나란히 놓이고 `<br>` 이 무시된 것.
브라우저에서 computed style 을 찍어 보고 알았다. 추측으로 안 고쳤다.

### 바닥이 왜 안 골라지냐 -- 내가 막았고, 막은 게 틀렸다
`floor: none` 일 때 바닥 카드를 회색으로 죽여 놨었다. 사용자 지적을 받고 보니
**막을 게 아니라 되게 하는 게 맞았다.** 벌집을 칠한 판에 붙이면 그 판은
실제로 다른 부품이다.

그리고 **서버는 처음부터 준비돼 있었다.** `floor_coating` 이 오면
`floor_boundary_depth` 를 잡는데, `floor: none` 이면 전체 깊이로 떨어진다.
렌더러는 그 평면에서 메시를 잘라 아래 면에 다른 재료를 붙이고, 셀 바닥면이
정확히 평면 위에 놓이는 걸 알고 1e-3 만큼 밀어 올리기까지 한다.
**막고 있던 건 브라우저 한 줄이었다:**

    floor_coating: ($('#floor').value !== 'none') ? $('#floorcoat').value : null

### 그냥 열면 안 됐다 -- 검사기가 잡았다
`scripts/gate_backing_slot.py`. 미리 적은 B1: "받침판에 바탕과 같은 재료를
주면 안 준 것과 같은 값이 나온다". **실패했다. 벌집 정면이 4.56 % 달랐다.**

원인은 자르기가 아니었다(피라미드는 0.0008 % -- 골이 맞물려 잘릴 면이 없다).
**거칠기를 가져오는 규칙이 위아래가 달랐다.** 윗면은 요청이 준 값을 쓰고
(`cfg["coating"]["roughness"] = float(roughness)`), 바닥은 재료 파일 값을
썼다(`_coat` 가 `m["rough"]` 를 넣고 렌더러가 `fc.get("roughness", rough)`).
아노다이징만 0.4359 라 요청의 0.1975 와 어긋났다. **한 판에 두 규칙이 돌고
있었다.**

`_coat(..., roughness=)` 를 만들어 여섯 군데 호출부에 규칙을 하나로 맞췄다.
숫자를 주면 판 전체를 그 값으로(발표된 배치가 전부 그렇게 돌았으므로 그 행들이
그대로 재현된다), None 이면 재료마다 자기 값. 다시 재니 B1 0.0171 %, 통과.

### 열었다
  - `#floorcoat` 첫 항목이 **"— 바탕과 같게 —"** 이고 기본값이다. 이걸로
    옛 숫자가 그대로 나온다.
  - `floor_coating` 을 항상 보낸다.
  - 바닥 카드는 언제나 고를 수 있다. `floor: none` 이면 "셀 바닥의 받침판 ·
    방을 향한 면".
  - 단면도에 받침판 띠를 그린다. **바탕과 같은 재료면 바탕 색으로 둔다** --
    없는 경계를 색으로 만들어 내면 안 된다. 3D 뷰도 같은 규칙.

앱 경로로 검증 (벌집 6.35 / 깊이 40 / 판 120, 아노다이징 바탕):

    안 보냄(옛 동작)   정면 0.18710 %   40도 1.03917 %
    바탕과 같게        정면 0.18712 %   40도 1.03918 %   (+0.011 %, 잡음)
    5 % 페인트         정면 0.20037 %   40도 1.03918 %   (+7.1 %)

**40도는 안 움직인다.** 그 각도에서는 관 속 받침판이 안 보인다. 받침판은
정면에만 영향을 준다 -- 그리고 정면은 지금까지 가장 다루기 어려웠던 축이다.

### COATING 이 왜 살아 있냐 -- `hidden` 이 안 먹고 있었다
드롭다운 셋에 `hidden` 을 붙였는데 화면에 그대로 있었다. 브라우저에서
계산된 값을 찍어 보니 `display: flex`. **`.row{display:flex}` 클래스 규칙이
브라우저 기본 `[hidden]{display:none}` 을 이긴다.** 클래스가 속성 선택자보다
우선순위가 높다. `[hidden]{display:none!important}` 을 전역으로 못박았다.

추측 안 하고 computed style 부터 찍은 게 맞았다. 안 그랬으면 JS 를 뒤졌을 것이다.

### 남은 COATING 의 정체를 이름으로 밝혔다
드롭다운이 사라지고 나니 그 섹션에 남은 건 판 전체 확산·거칠기 슬라이더뿐이다.
그건 코팅을 고르는 게 아니라 **세 자리를 한꺼번에 덮어쓰는 것**이고,
NEXT.md 3 단계에서 없앨 물건이다. 없애기 전까지는 이름이라도 사실대로:

  제목  "Coating" -> "재질 값 직접 정하기"
  설명  "보통은 건드릴 일이 없습니다. 재료를 고르면 그 재료의 값이 자동으로
        들어갑니다. 여기서 바꾸면 세 자리 전부에 같은 값이 걸립니다 --
        자리마다 따로 정하는 기능은 아직 없습니다."

그리고 "these three describe the comb layer" 문장은 이제 화면에 없는 메뉴를
가리키고 있었다. Materials 단면도 밑으로 옮기고 한국어로 다시 썼다 --
"위 두 자리는 comb 층을 말합니다. 그 아래 pyramid 층은 자기 마감을 따로
가집니다."

### 화면 말이 뒤섞여 있었다 -- 그리고 같은 것을 두 이름으로 부르고 있었다
지적 셋. (1) 새로 넣은 부분만 한국어다. (2) Structure 의 "Top layer" 와
Materials 의 "Base" 가 같은 물건인데 이름이 다르다. (3) Floor 는 사실 아래 판이다.

**시뮬레이터 UI 는 영어다.** 세 축(반사 총량 / 모양 뭉개기 / 정면 반짝임)만
사용자가 정한 우리 용어라 한국어를 병기한다. 나는 새 섹션을 통째로 한국어로
써서 그 규칙을 깼다. 전부 영어로 되돌렸고 세 축만 남겼다.

이름 통일:

    Structure  Top layer            Bottom panel   (전에는 Floor)
    Materials  Top layer — bare     Bottom panel
               Top layer — painted

같은 표면을 "Top layer" 와 "Base" 로 다르게 부르던 걸 없앴다.
`floor` 라는 **값**은 그대로다 -- 저장된 디자인, 프리셋, 디스크의 모든 결과가
그 값을 쓴다. 바뀐 건 라벨뿐이다. `none` 도 마찬가지로 값은 두고 라벨만
"none — no layer, backing plate only" 로 바꿨다. "flat" 이라고 부르자는 제안은
안 받았다 -- 피라미드는 골이 선으로 만나 평평한 판이 아예 없다. 그건 다른 거짓말이다.

### 이름의 출처가 둘이었다
재료의 한국어 이름은 `material/*.json` 에, 영어 이름은 `index.html` 안
`NICE` 라는 손으로 관리하는 표에 있었다. 새 재료를 넣으면 누가 그 줄을
고칠 때까지 id 가 이름 노릇을 하고, 둘이 어긋날 수도 있었다.
**재료마다 `label_en` 을 넣고 `NICE` 를 없앴다.** 서버가 `/api/coatings` 로
둘 다 내보내고, 화면은 영어를, 보고서는 한국어를 쓴다.

### 카드가 없는 색을 약속하고 있었다
바닥이 바탕과 같은 재료면 모델은 따로 안 칠하는데(없는 경계를 만들지
않으려고) 카드의 막대는 초록이었다. 그래서 "색이 반영이 안 된다" 로 읽혔다.
같은 재료면 카드 막대도 바탕 색으로 바꾸고 "same as the top layer — not
tinted apart" 를 적었다. 카드·단면도·3D 가 이제 같은 규칙을 쓴다.

### dfnote 에 철회한 내용이 살아 있었다
"정면 반짝임 초과분 = (1 − 확산) ÷ 거칠기^4" 와 "반짝임 절대값은 못 씁니다"
가 그대로 떠 있었다. 둘 다 단위 오류를 찾기 전 이야기다. 영어로 다시 쓰면서
바로잡았다 -- `1 + (1 − diffuse) / (4 α²)`, 그리고 슬라이더가 √α 라는 것.

### 층 이름을 물건에 맞췄다 -- 그리고 내 반대가 틀렸었다
사용자 제안: 아래 판의 `none` 을 `flat` 으로 부르고, 위층에 `none` 을 추가해서
그게 "아무것도 없음" 이 되게 하자.

**나는 "피라미드는 골이 선으로 만나 평평한 판이 없다" 며 반대했다. 틀렸다.**
그건 *위층* 이야기였다. 사용자가 말한 건 **구조가 얹히는 판 자체**이고,
그건 어떤 위층이든 언제나 있다. 모형이 이쪽이 맞다:

    Top layer     구조 (또는 none = 아무것도 없음)
    Bottom panel  구조가 얹히는 판 (flat, 또는 pyramid/gap/... 층)

`top: none` + `bottom: flat` = 맨 판. 이 연구가 모든 순위를 견주는 그 대조판이다.
전에는 그걸 `top: flat` 이라고 불렀는데, 이제 `flat` 은 목록에서 뺐다 --
같은 형상을 두 이름으로 부르는 건 오늘 내내 고쳐 온 문제다.

바꾼 것:
  - `FAMILIES["none"]` 추가 (`flat` 과 같은 빌더). `flat` 은 등록해 둔 채로
    남긴다 -- 저장된 스펙·프리셋·디스크의 결과가 그 이름을 쓴다.
  - `NORMAL["none"]`, `_render_family` 의 `"none": "floor"`. 이게 없어서
    `CellParams.__init__() got an unexpected keyword argument 'kind'` 로
    죽었다. 브라우저 콘솔이 아니라 응답의 traceback 을 읽고 찾았다.
  - 목록 라벨: top `none — no structure`, bottom `flat — plain panel`.
    **값은 안 바꿨다** (`floor: "none"` 그대로). 서버 열 몇 군데와 저장된
    모든 결과가 그 문자열을 쓴다. 바뀐 건 사람이 읽는 글자뿐이다.

검증: `top: none` 과 옛 `top: flat` 이 5 % 페인트에서 정면 4.96906 %,
40도 4.97859 % 로 **마지막 자리까지 같다.**

### 위층이 없는데 "Top layer" 자리가 있었다
`none` 을 골라도 재료 카드가 "Top layer — bare" 라고 떴다. 방금 고른 것과
반대되는 말이다. 위층이 없으면 판 자체가 전부이므로 이름을 바꾼다:

    Panel — bare / Panel — painted / Backing

슬롯의 내부 키는 그대로다(`base` 는 여전히 요청의 `coating`). 글자만 바뀐다.

### 옛 이름을 쓰는 저장 디자인이 화면을 죽일 수 있었다
`flat` 을 목록에서 빼자, 그 이름으로 저장된 디자인을 불러오면 select 가
빈 값이 되고 `sliders()` 가 `undefined.length` 로 터진다. **부팅 중에 터지면
그 뒤 줄이 통째로 안 돈다 -- 이번 주에 이미 한 번 겪은 그 모양이다.**
불러올 때 `flat` → `none` 으로 옮기고, 모르는 계열이 와도 안 죽고
"unknown family — pick one from the list" 를 띄우게 했다.

### 조합을 스스로 훑어라 -- 그리고 훑으니 자리 셋 중 둘이 가짜였다
사용자: "야 이걸 말로 해줘야 해? 니가 스스로 컴비네이션을 생각해봐."
맞다. 한 조합씩 지적받아 고치고 있었다. `scripts/gate_slot_matrix.py` 를
만들어 위층 x 아래층을 전부 훑고, **자리마다 재료를 5 % 에서 1 % 로 바꿔
숫자가 움직이는지**로 그 자리가 실재하는지 판정했다.

| 위층 | 아래층 | 바탕 | 덧칠 | 바닥 |
|---|---|---|---|---|
| none | flat | OK 80 % | **없음 0 %** | **가로챔 80 %** |
| pyramid | flat | OK 80 % | OK 33 % | **없음 0 %** |
| pyramid | gap | OK 81 % | OK 32 % | **없음 0 %** |
| comb | flat | OK 81 % | OK 61 % | OK 20 % |
| comb | gap | OK 80 % | OK 76 % | OK 3.5 % |
| cone | flat | OK 81 % | OK 38 % | **없음 0 %** |
| cone | gap | OK 81 % | OK 24 % | OK 0.1 % |

**피라미드와 원뿔은 골이 맞물려 자기 받침판을 덮는다.** 그 아래는 빛이 안
닿으니 마감을 고를 이유가 없다. 관이 뚫린 벌집만 바닥이 보인다. 나는 그걸
"the far side, not lit" 이라고 캡션만 붙여 놓고 -- 정작 **평판에서는 그
자리가 판 전체를 가로채고 있었다.**

화면 규칙을 이 표에서 뽑았다:

    NOTOP()       위층 없음 -> 자리 하나(Panel). 덮는 비율 슬라이더도 숨김
    SEALED_TOP()  pyramid/cone/wave/vgroove + 아래층 없음 -> 바닥 자리 없음
    그 외          셋 다

요청도 같이 막는다. 화면에서만 숨기면 값은 계속 나가서 조용히 렌더를 바꾼다.

### 평판에서 나온 것 둘 (측정)
    덧칠  무소를 1 mm 든 9 mm 든 4.99650 % 로 같다 -- 보이는 면이 도장
          평면 아래에 있어서 늘 깊은 쪽 재료를 쓴다
    바닥  5 % 페인트 판 + 무소 바닥 = 0.99772 %, 정확히 무소. 판 전체가
          바닥 재료가 된다

### 덤으로 찾은 진짜 버그 (아직 안 고침)
**피라미드에 바닥층을 얹으면 죽는다.**
`CellParams.__init__() got an unexpected keyword argument 'tip_flat'`.
`geom_stack` 이 피라미드를 `CellParams` 로 만드는데 거기엔 `tip_flat` 이
없다. UI 는 그 조합을 제공하고, 고르면 같은 방식으로 죽는다.
검사기에서는 쌓을 때 위층 파라미터를 비워서 피해 갔고, 그 사실을 주석에
적어 뒀다. 고치려면 stack 쪽 파라미터 맵을 봐야 한다 -- NEXT.md 에 올린다.

### 카드는 고쳤는데 그림 밑 설명줄은 안 고쳤다
사용자가 평판인데 자리가 셋이라고 다시 지적했다. 캐시된 옛 화면이었지만,
**같은 스크린샷 아래쪽에 진짜로 안 고친 게 하나 보였다:**

    none · 10 mm · blue = top layer · pink = painted · green = bottom panel
         · painted 10 % from the tip

평판인데 덧칠과 바닥을 말하고 있다. 그 줄은 색 설명이니 **그 조합에 실제로
있는 자리만** 말해야 한다. 카드 목록과 같은 규칙(NOTOP / SEALED_TOP)으로
묶었다.

    none + flat     one surface
    pyramid + flat  blue = top layer · pink = painted
    comb + flat     + green = bottom panel

**교훈: 한 곳을 고치면 같은 사실을 말하는 다른 곳도 같이 찾는다.**
자리 목록은 이제 네 군데가 말한다 -- 카드, 단면도, 3D 색, 그림 밑 설명줄.
넷 다 `slotMaterials()` 와 같은 조건을 봐야 한다.

### 오늘 버그의 공통 원인: 내가 만든 금지 규칙
사용자: "어떤 병신 같은 규칙을 계속 남발하니까 이렇지." 맞다.
오늘 잡은 화면 버그를 늘어놓으면 전부 **내가 코드에 적어 넣은 금지**에서 나왔다.

    "Musou is never a base"          -> 평판을 무소로 칠할 수 없었다.
                                        이 연구의 대조판 중 하나가 그건데도.
    "the far side, not lit"          -> 실제로는 그 자리가 판 전체를 가로챘다
    "floor 는 층이 있을 때만"          -> 서버는 처음부터 받침판을 받고 있었다
    "flat 은 top 에도 floor 에도"      -> 같은 형상을 두 이름으로

하나같이 **재보지 않고 적은 문장**이고, 하나같이 나중에 특례를 하나씩
더 붙여 가며 풀어야 했다. 특례가 또 버그가 됐다.

**규칙: 메뉴는 금지하지 않는다. 무엇이 뜻이 있는지는 측정이 답한다.**
`scripts/gate_slot_matrix.py` 가 그 답을 내는 방식이다 -- 자리마다 재료를
바꿔 보고 숫자가 움직이는지 본다. 움직이면 실재하고, 안 움직이면 화면에서
빠진다. 사람이 정한 게 아니라 측정이 정한다.

`BOUGHT` 필터를 지웠다. 이제 모든 자리가 재료 11 종을 다 받는다
(덧칠·바닥은 "not painted" 까지 12).

### 교훈을 적자마자 다시 어겼다
"메뉴는 금지하지 않는다" 를 적어 놓고, 바로 그 아래에서 **측정을 근거로
자리를 없앴다** -- 피라미드·원뿔은 받침판이 0.000 % 니까 카드를 지웠다.
사용자가 바로 잡았다: "여전히 없잖아. 또 규칙만들고."

측정이 근거라도 **선택지를 없애는 것은 여전히 금지다.** 0 % 라는 사실은
사용자에게 알려 줄 정보이지, 대신 결정해 줄 근거가 아니다. 되돌렸다.

    없앤다  ->  카드에 적는다
              "measured: no effect on this shape -- the valleys meet and
               close over it"

값도 계속 보낸다. 화면에서만 숨기면 값이 조용히 나가고, 화면과 요청이
어긋난다.

**자리를 정말 빼는 경우는 하나뿐이다: 보여 주면 거짓말이 될 때.**
`top: none` 의 덧칠(아무 일도 안 함)과 바닥(판 전체를 가로챔)이 그렇다.
그 둘은 값도 안 보낸다.

### 딱지만 붙이고 이유를 안 보여 줬다
사용자: "paper disagree는 머야??" 화면이 `papers disagree` 라는 딱지를
붙여 놓고 무슨 논문이 무엇에 대해 어떻게 갈리는지는 어디에도 없었다.
**문제에 이름만 붙이고 내용을 안 주면 걱정만 시킨다.**

등급 여섯 개 전부에 한 문장씩 붙였다(`PROV_WHY`). 딱지의 툴팁으로 뜨고,
쓰이는 중인 재료는 목록 아래에 문장으로 펼쳐진다.

    papers disagree  이 재료의 실측이 100 배 갈린다. TAMU 2014 무광 스프레이
                     정반사 0.1 %(확산 0.999), Zeng 2019 Z307 정면에서
                     램버시안과 1 % 안, Filip & Vavra 2026 5 도 원뿔 안 10 %
                     (확산 0.90 이하). 검출기 크기로 화해 안 됨 -> 표면이
                     다름 -> 도장 공정이 정함. Zeng 의 0.99 를 쓰고, 그 폭은
                     발주서에 적을 항목이다.
    bounded          그 숫자를 직접 준 논문이 없고 실측이 범위만 묶는다.
                     보수적인 끝을 쓴다.
    analogue         비슷한 재료에서 빌려 왔다. 우리 것은 아무도 안 쟀다.
    guess            실측도 범위도 없다. 모르는 값으로 봐야 한다.

### 재료 색을 화면에서 바꾸게 했다 -- 보고서 라벨용
사용자: "그게 있어야 레포트에 칼라 라벨링도 하고 하지. 실제 렌더결과와는
상관없어도." 그게 정확히 이 값의 쓰임이다.

  - **재료 목록의 모든 줄에 색 고르개**를 달았다. 처음엔 "고른 재료 하나"에만
    달았다가 지적받고 줄마다로 바꿨다. 네모 자체가 컨트롤이므로 줄 클릭
    (=자리에 넣기)과 안 겹치게 `stopPropagation` 과 `draggable=false`.
  - **`POST /api/material_color`** 가 `material/<id>.json` 에 쓰고 메모리의
    `MATERIALS` 도 같이 갱신한다. 파일만 쓰면 2026-08-22 처럼 서버가 옛 값을
    몇 시간 내보낸다. `#rrggbb` 가 아니거나 없는 id 면 거절한다.
  - **잠금 없음.** 색은 계산에 안 들어간다 -- 렌더러는 안 보고, 3D 뷰는
    자리별 도식 색을 쓴다. 반사율·확산·거칠기는 다르다: 발표된 66,426 줄이
    id 로 그 값을 가리키므로 그건 잠가야 한다. **잠글 것과 안 잠글 것을
    가르는 기준은 "그 값이 숫자를 움직이나" 다.**
  - **보고서가 그 색을 읽는다.** `build_comb_report.py` 에 팔레트를 또 두지
    않고 `material/*.json` 에서 가져온다. 시뮬레이터에서 색을 바꾸면 보고서
    재료표의 네모가 따라 바뀐다. 보고서에도 "계산과 상관없는 이름표" 라고
    적었다.

목록을 두 줄짜리로 고치면서 색 네모를 빠뜨렸던 것도 같이 되살렸다.

## 2026-08-24 — 시뮬레이터 점검 체크리스트, 그리고 보고서 확인

### 항목별로 돌아가는 점검기를 만들었다
`scripts/check_sim.py`. 문서가 아니라 실제로 실행해서 통과/실패를 찍는다.
돌고 있는 서버에 HTTP 로 말을 걸므로 사람이 쓰는 것과 같은 경로다.

    A 부팅        4 항목   페이지·재료표·계열목록·프리셋
    B 형상       18 항목   위층 12 계열 + 아래층 5 계열 + top:none == 옛 flat
    C 재질        5 항목   재료·덧칠·받침판이 숫자를 바꾸나, 거칠기가 번쩍임을 바꾸나
    D 발표값      3 항목   32가지를 앱 경로로 재현
    E 내보내기     5 항목   STEP·STL·광선·색 쓰기·잘못된 색 거절
    F 화면       11 항목   브라우저로만 (누르기·끌기·자리 규칙·색 고르개)

**46 항목 전부 통과.** `top:none` 이 옛 `flat` 과 4.99650 % 로 완전 일치.
32가지는 0.003 % 안에서 재현. 옛 `top:flat` 디자인을 불러와도 `none` 으로
옮겨지고 모델이 그려진다.

점검하다 내 실수 셋을 또 잡았다:
  - `window.NTRI` 로 확인 -- `let` 전역은 window 에 안 붙는다. 앱이 아니라
    검사가 틀렸다. 캔버스 픽셀을 직접 읽어 확인했다.
  - F5·F6 에서 "바꾸기 전" 값이 이미 목표값이라 아무것도 증명 못 했다.
    다른 값으로 세팅하고 다시 했다. **대조군이 목표와 같으면 그 시험은
    통과해도 아무 말도 안 한다.**
  - 없는 함수(`loadSpec`)를 불렀다. 실제 경로(디자인 저장 -> 불러오기)로 바꿨다.

### 보고서: 숫자는 맞았고 눈으로 보니 둘이 틀렸다
표 32 줄을 데이터와 하나씩 대조했다 -- 총량·번쩍임 전부 일치, 정렬도
어두운 순. 그런데 열어 보니:

  1. **다크 모드에서 색 네모가 안 보인다.** 재료가 전부 새까만데 테두리를
     `rgba(0,0,0,.3)` 으로 줬다. 검정 위 검정. 구분하라고 붙인 네모가
     구분이 안 되면 없는 것과 같다. 테두리를 `var(--muted)` 로 바꿨다.
  2. **`<meta charset>` 이 없었다.** 아티팩트는 HTTP 헤더로 UTF-8 을 주니
     멀쩡한데, `report/comb/` 의 파일을 그냥 열면 한글이 전부 깨진다.
     보고서는 아티팩트이기도 하고 파일이기도 하다.

둘 다 **띄워서 눈으로 보지 않았으면 못 잡았다.** 태그 균형과 숫자 대조는
통과하고 있었다.

## 2026-08-24 — 남은 일 네 가지, 그리고 감시 스크립트

### 감시 스크립트
`scripts/watch_sim.sh`. 3 분마다 서버를 확인해서 안 답하면 다시 띄우고,
체크리스트(A·C·E)를 돌린다. 실패는 `/tmp/simsrv/WATCH_STATUS` 에 시각과
함께 쌓인다. `touch /tmp/simsrv/WATCH_STOP` 으로 멈춘다.
`pkill sim_server` 만으로는 `mts_worker` 가 안 죽고 CPU 를 계속 먹으므로
재시작할 때 둘 다 잡는다.

### 1. 피라미드 + 바닥층이 죽던 것
`CellParams.__init__() got an unexpected keyword argument 'tip_flat'`.
**형상 빌더는 피라미드를 `FloorParams` 로 제대로 만들고 있었다. 노출 면적
추정기만 `CellParams` 로 보냈다.** 그래서 삼각형 하나 만들기 전에 죽었다.
`geom_floor` 계열에는 그 추정기가 없으므로 None 을 돌려주고, 화면은 이미
빈 값을 '—' 로 그린다. 위층 3 x 아래층 4 = 12 조합 전부 만들어진다.

### 2·3. 자리마다 확산·거칠기
`make_depth_split` 이 거칠기를 하나만 받아서 무소를 아노다이징 위에 칠하면
아노다이징까지 무소 거칠기로 렌더됐다. 얕은 쪽·깊은 쪽을 따로 받게 했다.
**두 값이 같으면 노드를 안 잇는다** -- 발표된 측정과 노드 트리가 바이트까지
같아야 그 값들이 재현된다.

`measure`/`form` 에 `slot_df`/`slot_rough` 를 넣었다. 자리 이름으로 키를
주면 그 자리만 바뀐다. 판 전체 인자는 옛 배치용으로 남긴다.
**`in_blender` 의 dispatch lambda 가 새 인자를 안 넘기고 있었다** -- 코팅을
몇 달 동안 조용히 흘리던 바로 그 자리다. 이번엔 키워드로 넘긴다.

화면: 자리 카드마다 확산·α 칸과 reset. α 는 물리값이고 요청으로 나갈 때
√α 로 바뀐다(렌더러가 제곱하므로). `Override` 섹션은 숨겼다 -- 잘라내려다
훨씬 뒤 블록의 닫는 태그까지 삼켜서 `div` 균형이 깨졌다. **되돌리고
`hidden` 속성만 붙였다. 문서를 텍스트로 오려내는 건 그만.**

### 4. 재료 편집기
`POST /api/material_edit` 와 `/api/material_duplicate`.
반사율·확산·α 를 고치고, 파일에 `history` 를 남기고, 고친 값의 근거 등급을
`hand-set` 으로 바꾼다. α 를 고치면 `roughness`(=√α)도 같이 쓴다.

**잠금 대상을 손으로 안 정했다.** `results/` 와 `report/` 를 훑어 그 안에서
id 가 실제로 나오는 재료를 찾는다 -- `anodised`, `anodised_hi`,
`musou_fit`, `wall_5pct` 네 종. 잠긴 것을 고치려 하면 HTTP 409 와 함께
"복제해서 고치라" 고 한다. 색은 여기 없다: 숫자를 안 움직이므로 자유다.

### 검증
    A~E 35 항목   통과   (회귀 없음)
    G  6 항목     통과   자리별 값이 그 자리에만, 잠금 409, 범위 밖 400
    D  32가지     0.009 % 안에서 재현
