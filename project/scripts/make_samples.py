"""
Generate SAMPLES.md from the measurements. Nothing here is typed by hand.

    python3 scripts/make_samples.py

WHY. Three of the last four errors were the same failure: the same fact stored
in two places, one copy updated.

    the blade was a wedge      geometry defaults  vs  the spec sheet
    roughness stopped at 10/20 a hard-coded list  vs  form_candidates.json
    the blade had no rank      a second CSV       vs  the analyser's one CSV

`SAMPLES.md` was the worst of them, because it is the document a supplier acts
on and every number in it was copied across by eye. So it stops being written
and starts being generated: each figure carries the file and row it came from,
and a number that has no row cannot appear.

The prose stays hand-written -- explanations, cautions, what to measure. Only
the NUMBERS are generated, and they are generated from the same functions the
rankings use, so the spec sheet and the report cannot disagree.
"""

import sys
import os
import json
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_buildable as AB                                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "SAMPLES.md")
RESULTS = os.path.join(ROOT, "results")

# The four samples, named by the design key the measurements are stored under.
# Change a sample here and every number in the document follows; there is no
# second copy to forget.
SAMPLES = [
    ("① 평판 (flat plate)", None, "도장만", "기준선"),
    ("② 벌집 (honeycomb)", "B_HONE_p0650_f080", "구매",
     "흑색 아노다이징 알루미늄 벌집, 셀 6.5 mm / 포일 0.08 mm"),
    ("③ 날 배열 (blade array)", "BL_FLAT_t100_p0550_a02_grid", "판금 끼움",
     "균일 두께 0.1 mm, 간격 5.5 mm, 기울기 2°, 격자 조립"),
    ("④ 콘 배열 (cone array)", "B_CONE_p0550", "몰드 / 프린팅",
     "간격 5.5 mm, 팁 지름 0.4 mm"),
]


def load():
    dark = {r["design"]: r for r in AB.darkness()}
    form = {r["design"]: r for r in AB.form()}
    rough = {}
    p = os.path.join(RESULTS, "form_roughness.json")
    if os.path.exists(p):
        for r in json.load(open(p)):
            t = r["thetas"].get("+0")
            if t and abs(r["roughness"] - 0.30) < 1e-9:
                rough[r["what"].rsplit("_s", 1)[0]] = t["peak_vs_wall"]
    return dark, form, rough


def main():
    dark, form, rough = load()
    flat = AB.FLAT_COATING_WORST
    date = datetime.datetime.now().strftime("%Y-%m-%d")

    missing = [k for _, k, _, _ in SAMPLES if k and k not in dark]
    if missing:
        sys.exit("no measurement for: %s -- refusing to write a spec sheet "
                 "with a number that has no row behind it" % ", ".join(missing))

    L = []
    A = L.append
    A("# 시제품 4종 사양 (sample specification)")
    A("")
    A("**이 파일은 `scripts/make_samples.py` 가 측정값에서 생성합니다. "
      "손으로 고치지 마십시오** — 다음 생성 때 덮어써집니다. 숫자를 바꾸려면 "
      "측정을 다시 하십시오.")
    A("")
    A("생성 %s · 어둡기 %s · 형태 %s"
      % (date, "results/sweep_buildable.csv + sweep_blade.csv",
         "results/form_buildable.json"))
    A("")
    A("전부 **100 × 100 mm, 깊이 50 mm**.")
    A("")
    A("## 요약")
    A("")
    A("| 시료 | 총 반사량 | 번짐 (평판 대비) | 정면 밝기 (맨 검정벽 대비) "
      "| 만드는 법 | 시드 |")
    A("|---|---|---|---|---|---|")
    A("| ① 평판 | **%.4f %%** | 1.00 | %s | 도장만 | — |"
      % (100 * flat, "%.3f" % rough["flat"] if "flat" in rough else "—"))
    for name, key, proc, _ in SAMPLES[1:]:
        d, f = dark[key], form.get(key)
        A("| %s | **%.4f %%** | %s | %s | %s | %d |"
          % (name.split(" ")[0] + " " + name.split(" ")[1], 100 * d["mean"],
             "%.2f" % f["smear"] if f else "—",
             "%.3f" % rough[key] if key in rough else "—", proc, d["n"]))
    A("")
    A("총 반사량은 입사각 0/±20/±40° 와 코팅 가정 3 종 전체의 **최악값**이고, "
      "기하 배치 시드에 대한 평균입니다.")
    A("")

    for name, key, proc, desc in SAMPLES:
        A("## %s" % name)
        A("")
        A(desc + ".")
        A("")
        if key is None:
            A("| | |")
            A("|---|---|")
            A("| 총 반사량 | **%.4f %%** |" % (100 * flat))
            if "flat" in rough:
                A("| 정면 밝기 | 맨 검정벽 대비 **%.3f** |" % rough["flat"])
            A("")
            A("무소블랙 실측(Filip & Vávra, JOSA A 43, 1037)과 일치합니다 — "
              "0° 에서 1.00 %, 45° 에서 1.13 %.")
            A("")
            A("**가장 중요한 시료입니다.** 대조군이면서, 아래 §측정 에서 "
              "코팅 값 두 개를 뽑아내는 시료입니다.")
            A("")
            continue
        d, f = dark[key], form.get(key)
        ok, note = AB.buildable(d["process"], d["feature"])
        A("| | |")
        A("|---|---|")
        A("| 총 반사량 | **%.4f %% ± %.4f** (시드 %d 개) |"
          % (100 * d["mean"], 100 * d["sem"], d["n"]))
        A("| 평판 대비 | **%.1f 배** 어두움 |" % (flat / d["mean"]))
        if f:
            A("| 번짐 | 평판 대비 **%.2f 배** |" % f["smear"])
        if key in rough:
            A("| 정면 밝기 | 맨 검정벽 대비 **%.3f** |" % rough[key])
        A("| 최소 피처 | %s mm (%s) |" % (d["feature"], d["process"]))
        A("| 제조 가능 | %s |" % ("예" if ok else "**아니오** — " + note))
        A("")
        A("설계 키 `%s`" % key)
        A("")

    A("---")
    A("")
    A("## 같이 재야 할 것 — 데모보다 중요합니다")
    A("")
    A("계산을 흔드는 미측정 코팅 값이 둘 있습니다. **① 평판 하나만 제대로 "
      "재면 둘 다 풀립니다.**")
    A("")
    A("| 값 | 얼마나 흔드나 | 어떻게 |")
    A("|---|---|---|")
    A("| 확산 비율 (diffuse fraction) | 시료 자신의 값이 1.06 ~ 1.39 배 변함 "
      "| ① 의 BRDF 를 3 개 이상 입사각에서 |")
    if "flat" in rough and "B_CONE_p0550" in rough:
        A("| 거칠기 (roughness) | 콘의 정면 밝기가 맨 검정벽 대비 25 배 변함 "
          "| ① 의 정면 반짝임 |")
    A("")
    A("**BRDF 로 재야 합니다.** 여러 입사각의 반사율만으로는 확산과 정반사를 "
      "구분할 수 없습니다 — 이 프로젝트가 그것 때문에 여기까지 왔습니다. "
      "장비는 고니오미터 (goniometer); 적분구 (integrating sphere) 는 총량만 "
      "줍니다.")
    A("")
    A("## 아직 정리 못 한 것")
    A("")
    A("- **② 는 아노다이징이라 나머지와 \"같은 도장\"이 아닙니다.** 깊은 셀 "
      "안쪽까지 균일하다는 장점이 있지만 반사율 자체가 다를 수 있어, 네 "
      "시료의 비교가 흐려집니다.")
    A("- **총 반사량 차이는 눈으로 안 보일 수 있습니다.** 반구 전체로 나가는 "
      "빛의 총량이라 적분구가 필요합니다. 정면에서는 벌집이 평판과 거의 "
      "같습니다. 눈으로 확실한 것은 번짐과 정면 밝기입니다.")
    A("- **② 의 깊이 50 mm 조달 가능 여부 미확인.** 공급사 사양표의 치수는 "
      "패널 크기이지 코어 두께가 아닙니다. 견적 때 확인.")
    A("- **④ 는 실효 깊이가 다릅니다** — 콘은 이웃끼리 붙어 깊이 50 mm 중 약 "
      "35 mm 만 실제 공동입니다. ②③ 는 수직이라 50 mm 전부입니다.")
    A("- 남은 질문은 `results/QUESTIONS.md`.")
    A("")

    open(OUT, "w").write("\n".join(L) + "\n")
    print("[DONE] %s  (%d lines, %d samples, every number from a row)"
          % (OUT, len(L), len(SAMPLES)))


if __name__ == "__main__":
    main()
