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
