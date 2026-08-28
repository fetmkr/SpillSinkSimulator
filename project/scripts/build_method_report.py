# -*- coding: utf-8 -*-
"""공식과 구현 -- 이 시뮬레이터가 무엇을 어떻게 재는지 한 장에.

사용자가 물었다. "우리 시뮬레이터 공식과 구현 섹션이 있어야 이게 제대로
만들어졌는지 알 수 있을 것 같다. 나중에 다른 사람한테 보여주기도 하고.
거기에는 왜 우리가 그렇게 구현했는지 보고서 한 장과 참고 논문들도 다 넣어놔."

지금까지 이 프로젝트의 방법은 코드 주석에만 있었다. 주석은 고친 사람만 읽는다.
세 축이 각각 무슨 식이고, 설정값이 어디서 왔고, 왜 그렇게 정했는지를 한 장에
모은다. **설정값은 코드에서 직접 읽는다** -- 문서에 손으로 옮겨 적으면 코드를
고쳤을 때 문서가 조용히 거짓말을 한다.

이 문서를 짓는 규칙
------------------
- 숫자는 `scripts/` 의 실제 상수에서 읽는다. 손으로 안 적는다.
- 근거가 있는 값과 없는 값을 **표에서 갈라 보인다.** 없는 것을 있는 것처럼
  적지 않는다.
- 참고 문헌은 실제로 원문을 열어 확인한 것만 싣는다.

    python3 scripts/build_method_report.py
"""
import os
import re
import io
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STYLE_FROM = os.path.join(ROOT, "report/comb/comb_musou_2026-08-22.html")
OUT = os.path.join(ROOT, "report/METHOD.html")


def const(path, name):
    """소스에서 상수를 그대로 읽는다. 문서가 코드와 어긋날 수 없게."""
    t = io.open(os.path.join(HERE, path), encoding="utf-8").read()
    m = re.search(r"^%s\s*=\s*([^\n#]+)" % re.escape(name), t, re.M)
    if not m:
        m = re.search(r"^%s[^=\n]*=\s*([^\n#]+)" % re.escape(name), t, re.M)
    return m.group(1).strip() if m else "?"


FB = "form_buildable.py"
BR = "blender_render.py"

SETTINGS = [
    # (이름, 값, 어디, 근거 등급, 근거)
    ("화소 밀도 mm/px", const(FB, "MM_PER_PX"), FB,
     "잼", "최소 피처를 4 화소로 해상하는 밀도. 판 크기가 바뀌어도 고정이라 "
     "같은 장비가 같은 잣대로 잰다. 못 지키면 성기게 가는 대신 거절한다."),
    ("화소 상한 RES_CAP", const(FB, "RES_CAP"), FB,
     "정함", "메모리 한계다. 물리가 아니다. 넘으면 거절하고 왜 넘었는지 말한다."),
    ("빔 폭 mm", const(FB, "STRIPE_W"), FB,
     "잼", "LaserCube Ultra MK2 를 벽에서 재면 7~14 mm. 그 아래쪽 값."),
    ("빔 퍼짐 도", const(FB, "SPREAD_DEG"), FB,
     "정함", "거의 평행한 빔을 흉내내는 값."),
    ("빔 자리 수", const(FB, "N_PHASE"), FB,
     "반쯤", "6/12/24 사다리에서 한 자리가 24 에서도 6.7 % 움직였다. 소볼로 "
     "바꾼 뒤 다시 안 쟀다."),
    ("빛줄기 수 (표본)", const(FB, "SAMPLES"), FB,
     "잼", "모양 셋 x 각도 넷, 열두 경우 사다리. p99 로 재면 16 부터 512 와 "
     "1 % 안에서 같다. 뭉개기는 4 에서도 1 % 안. 최대값을 쓰던 시절엔 어두운 "
     "자리에서 512 로도 안 멎었다."),
    ("봉우리 재는 법", const(FB, "PEAK_STAT"), FB,
     "잼", "최대값은 위로 치우친다 (승자의 저주). 사진 두 장으로 고르는 자리와 "
     "읽는 값을 나눠 재니 최대값이 2.6 % 높았고, 정면에서는 9 배까지 높았다. "
     "p99 는 그 값과 1 % 안에서 같았다. 목표 0.040 은 최대값 기준이라 "
     "다시 봐야 한다."),
    ("빔 자리 뽑는 법", const(FB, "BEAM_POS"), FB,
     "잼", "한 주기를 균등하게 나누면 자리가 늘 골·꼭짓점에 박힌다. 실제 "
     "레이저는 그 격자에 안 맞춰 떨어진다. 자리마다 값이 23 배 갈리므로 "
     "골고루 흩어야 한다. 되풀이가 정확한 판에서 발표 값을 재현할 때만 "
     "uniform."),
    ("읽는 창 가로 잘라내기", const(BR, "MEAS_INSET_X"), BR,
     "없음", "**근거 없음.** 판의 20 % 를 양쪽에서 잘라낸다. 왜 20 % 인지 "
     "코드에 아무 말이 없다. 그리고 이 상수가 네 파일에 따로 적혀 있다."),
    ("읽는 창 세로 잘라내기", const(BR, "MEAS_INSET_Z"), BR,
     "반쯤", "30 % 자체는 근거가 없다. 다만 '간격 + 빔 x 2' 가 안 들어가면 "
     "넓히는 규칙이 붙어 있고 그건 물리적 근거가 있다."),
]

# 어느 축이 어느 설정을 쓰나. 셋이 설정을 다 쓰는 게 아니다 -- 총량은
# 하늘 조명이라 빔도 창도 안 쓴다. 그걸 표로 못 박아 둔다.
USES = [
    # (설정, 총량, 뭉개기, 반짝임)
    ("화소 밀도 mm/px", "쓴다", "쓴다", "쓴다"),
    ("빔 폭", "안 씀", "쓴다", "쓴다"),
    ("빔 자리 수", "안 씀", "쓴다", "쓴다"),
    ("빔 자리 뽑는 법 (소볼)", "안 씀", "쓴다", "쓴다"),
    ("빛줄기 수", "쓴다", "쓴다", "쓴다"),
    ("읽는 창", "안 씀", "쓴다", "쓴다"),
    ("봉우리 재는 법 (p99)", "안 씀", "안 씀", "쓴다"),
]

AXES = [
    dict(
        ko="반사 총량", en="total reflectance", arrow="낮을수록 좋다",
        what="되돌아온 빛의 <b>양</b>",
        light="하늘처럼 사방에서 (uniform hemisphere, radiance 1). 램프가 아니다.",
        formula="판 창 화소의 <b>평균</b> &divide; 대조판 창 화소의 <b>평균</b>",
        code="blender_render.run() -- <code>ratio = s_panel['mean'] / "
             "s_ctrl['mean']</code>",
        window="없다. 면 전체를 넓이로 평균한다.",
        why="헬름홀츠 상반성(Helmholtz reciprocity)으로 &rho;<sub>dh</sub>(&theta;) "
            "를 읽는다. 하늘 조명 한 번으로 그 각도 빔의 되돌림 비율이 나온다. "
            "빔을 옮겨가며 잴 필요가 없다.",
        risk="없음. 빔 자리도 창도 안 쓰므로 이 문서의 다른 결함이 안 걸린다.",
        cost="각도 하나에 0.74 초",
    ),
    dict(
        ko="모양 뭉개기", en="smear", arrow="높을수록 좋다",
        what="되돌아온 빛의 <b>폭</b>",
        light="빔 띠 하나 (stripe). 세로는 빔 폭, 가로는 장면 전체.",
        formula="판 곡선의 <b>rms 폭</b> &divide; 대조판 곡선의 rms 폭",
        code="form_mtf.rms_width() -- 곡선을 확률로 보고 표준편차를 낸다. "
             "<code>sqrt(&Sigma;(z-c)&sup2;w)</code>, w = 곡선 &divide; 합",
        window="<b>값이 멎을 때까지 넓힌다.</b> 두 칸이 2 % 안에서 같으면 멈춘다. "
               "실측으로 되돌아온 빛 90 % 반폭의 6 배 근처에서 멎었다.",
        why="민판이 1.0 이 되도록 대조판으로 나눈다. 판 크기와 무관한 값이 "
            "되고, 되돌아온 빛이 창을 넘치면 <code>converged False</code> 로 "
            "알린다.",
        risk="가로 창이 판의 60 % 로 고정이라 근거가 없다. 세로는 물리 규칙이 "
             "붙어 있다.",
        cost="각도 하나에 6~7 분 (판 500, 자리 8, 빛줄기 512)",
    ),
    dict(
        ko="정면 반짝임", en="head-on peak", arrow="낮을수록 좋다",
        what="되돌아온 빛의 <b>가장 밝은 곳</b>",
        light="뭉개기와 <b>같은 사진</b>을 쓴다. 렌더는 한 번이고 읽기만 두 번이다.",
        formula="판 곡선의 <b>99 번째 백분위수</b> &divide; 대조판 곡선의 같은 값, "
                "빔 자리마다 내고 <b>평균</b>",
        code="<code>percentile(pp,99) / percentile(pc,99)</code>. "
             "<code>PEAK_STAT=\"max\"</code> 로 옛 최대값 방식으로 되돌린다.",
        window="뭉개기와 같은 창을 쓴다. <b>이게 남은 결함이다</b> -- 창이 "
               "넓어지면 뽑을 점이 많아지고 값이 커진다.",
        why="민판 무광 검정을 1.0 으로 놓는다. 목표 0.040 은 그 잣대에서 나온 "
            "값이다.",
        risk="옛 최대값 방식은 위로 치우쳤다. 여러 개 중 가장 큰 것을 고르면 "
             "잡음이 도운 것을 고르게 된다 -- 승자의 저주(winner's curse). "
             "실측으로 정면에서 편향 없는 값보다 <b>9 배</b> 높았다. p99 는 "
             "그 값과 1 % 안에서 같다. <b>목표 0.040 은 최대값 기준이라 "
             "다시 봐야 한다.</b>",
        cost="뭉개기와 같은 사진. 따로 안 든다.",
    ),
]

FINDINGS = [
    ("최대값은 위로 치우친다",
     "픽셀 하나하나는 편향이 없는데, 그 중 가장 큰 것을 고르는 순간 치우친다. "
     "고르는 행위가 편향을 만든다. 빛줄기를 늘리면 줄어든다.",
     "벌집 정면에서 빛줄기 64&rarr;2048 로 값이 8 % 내려왔고 아직 안 멎었다. "
     "사진 두 장으로 고르는 자리와 읽는 값을 나눠 재니, 최대값이 편향 없는 "
     "값보다 2.6 % 높았다. 정면 자리에서는 9 배까지 높았다.",
     "Efron 2011 · Forde 2023 · Kriegeskorte 2009"),
    ("백분위수가 대안이고 근거가 있다",
     "거칠기 표준 쪽에서 같은 문제를 겪고 같은 답을 냈다. 최대값 대신 위쪽 "
     "백분위수를 쓰거나, 여러 창의 최대값을 평균한다. 둘이 같은 값이다.",
     "우리 실측에서 p99 는 편향 없는 값과 <b>1 % 안</b>에서 같았고, 빛줄기 "
     "4 개에서도 그랬다. 순위는 여섯 각도 전부 안 바뀐다.",
     "Pawlus 2023 · evalglare 매뉴얼"),
    ("읽는 창이 판 크기를 따라간다",
     "창을 판의 60 % 로 잡으니 판을 키우면 창도 커진다. 최대값은 창 안의 점이 "
     "많아질수록 커진다. 그래서 판 크기가 값을 움직인다.",
     "피라미드 봉우리가 칸 4/6/10/14/18 개에서 0.467 / 0.535 / 0.508 / 0.496 "
     "/ 0.502 로 움직였다. 화소 밀도는 전부 같았다.",
     "Pawlus 2023 (면 측정이 선 측정보다 최대값이 큰 이유가 점 수) · "
     "Hartigan 2013"),
    ("빔 자리를 한 주기 균등 분할했다 (지금은 소볼)",
     "걸음이 구조 주기와 항상 맞아떨어진다. 늘 같은 자리를 밟는다. 되풀이 "
     "안 되는 모양(STEP, 꼭짓점 흔든 것)에는 애초에 못 쓴다.",
     "매끄러운 주기 함수에는 균등이 최적이다 (사다리꼴 적분, 지수 수렴). "
     "그런데 실제 레이저는 그 격자에 안 맞춰 떨어진다. 한 칸 안에서 자리를 "
     "옮기며 재니 정면에서 <b>23 배</b> 갈렸다 (골 0.00116, 꼭짓점 너머 "
     "0.02658). 그래서 소볼로 바꿨다.",
     "Cook 1986 · Owen 2023"),
    ("빔 자리마다 사진을 한 장씩 찍는다",
     "자리 수에 시간이 정비례한다. 남들은 광선마다 다른 출발점을 줘서 한 번에 "
     "넣는다.",
     "띠 조명을 자리마다 놓고 한 번에 렌더해 봤더니 <b>다른 물건</b>이 된다 "
     "(뭉개기 &minus;65 %, 봉우리 +196 %). Cycles 로는 광선 생성에 손을 못 "
     "댄다.",
     "genBSDF.pl · RayFlare 소스"),
]

REFS = [
    ("Efron, B. (2011)",
     "Tweedie's Formula and Selection Bias", "JASA 106(496)",
     "가장 큰 몇 개는 참값을 상당히 과대추정한다. 선택 편향, 평균 회귀.",
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC3325056/"),
    ("Forde, Hemani, Ferguson (2023)",
     "Review of Battling the Winner's Curse", "PLoS Genetics 19(9):e1010546",
     "순위 편향. 표본을 늘리면 편향이 상당히 준다.",
     "https://doi.org/10.1371/journal.pgen.1010546"),
    ("Kriegeskorte 외 (2009)",
     "Circular analysis in systems neuroscience", "Nature Neuroscience 12",
     "고르는 자료와 재는 자료를 나누면 편향이 사라진다. 표본 분할.",
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC2841687/"),
    ("Pawlus, Reizer, &#379;elasko (2023)",
     "Characterization of the Maximum Height of a Surface Texture",
     "Materials 16(22):7109",
     "최대 높이는 안정된 값이 아니다. 백분위수와 '여러 최대값의 평균' 이 "
     "같은 값이고 더 안정적이다. 면 측정이 선 측정보다 큰 이유는 점 수.",
     "https://doi.org/10.3390/ma16227109"),
    ("Wienold, J.", "evalglare v2.10 매뉴얼", "Radiance",
     "눈부심원을 문턱값으로 고르고 묶어서 <b>평균</b>을 낸다. 중앙값과 "
     "75 / 95 백분위수를 같이 낸다. 점 최대값을 안 쓴다.",
     "https://www.radiance-online.org/learning/documentation/manual-pages/"
     "pdfs/evalglare.pdf"),
    ("Nicodemus 외 (1977)",
     "Geometrical Considerations and Nomenclature for Reflectance",
     "NBS Monograph 160",
     "유한한 판은 옆으로 빛을 흘리기만 한다. 무한한 판이면 옆에서 되돌아 "
     "들어오는 몫이 그걸 메운다. 그 차이를 edge losses 라 부른다. 빛이 옆으로 "
     "걷는 거리 r<sub>m</sub> 을 재는 절차가 우리 수렴 시험과 같다.",
     "https://nvlpubs.nist.gov/nistpubs/Legacy/MONO/nbsmonograph160.pdf"),
    ("IEA SHC Task 61 (2021)",
     "BSDF generation procedures for daylighting systems", "T61.C.2.1",
     "빛 비추는 자리가 되풀이 주기보다 최소 5 배, 되도록 10 배 커야 한다. "
     "<b>우리는 0.15 배다.</b> 그래서 BSDF 로 형상을 대체할 수 없다.",
     "https://www.iea-shc.org/Data/Sites/1/publications/"
     "IEA-SHC-Task61--Technical-Report-C2.1-Whitepaper-BSDF.pdf"),
    ("McNeil, A. (2015)", "genBSDF Tutorial v1.0.1", "LBNL",
     "가장자리에서 출발한 광선은 원래 만났을 형상을 안 만나고 빠져나간다. "
     "해법은 크게 짓고 가운데만 쏘는 것. 원뿔 예제는 21 주기를 깔고 가운데 "
     "1 주기만 쏜다.",
     "https://www.radiance-online.org/learning/tutorials/"
     "Tutorial-genBSDF_v1.0.1.pdf"),
    ("Cook, R. (1986)", "Stochastic Sampling in Computer Graphics",
     "ACM TOG 5(1)",
     "규칙적인 표본 격자가 규칙적인 구조와 맞부딪히면 무늬가 생긴다. 적분 "
     "변수를 차원을 더 늘린 것으로 보고 그 축에 표본을 흩뿌린다.",
     "https://www.cs.cmu.edu/afs/cs/academic/class/15869-f11/www/readings/"
     "cook86_sampling.pdf"),
    ("Owen, A. (2023)", "Practical quasi-Monte Carlo integration", "Stanford",
     "스크램블 소볼은 매끄러운 경우 오차가 n<sup>&minus;1.5</sup> 로 준다. "
     "주기성도 매끄러움도 요구하지 않고, 최악에도 몬테카를로의 2.72 배를 "
     "안 넘는다.",
     "https://artowen.su.domains/mc/practicalqmc.pdf"),
    ("Veach, E. (1997)",
     "Robust Monte Carlo Methods for Light Transport Simulation", "Stanford",
     "효율은 분산과 시간의 곱의 역수다. 헬름홀츠 상반성 원문은 거울 반사에만 "
     "해당한다 -- 실제 근거는 굴절률로 나눈 BSDF 의 대칭이다.",
     "https://graphics.stanford.edu/papers/veach_thesis/thesis.pdf"),
    ("Zirr, Hanika, Dachsbacher (2018)",
     "Reweighting Firefly Samples", "Computer Graphics Forum",
     "튀는 표본(반딧불)이 들어 있으면 유한 표본 추정이 참값보다 크다. 그런데 "
     "그냥 지우면 아래로 치우친다.",
     "https://jo.dreggn.org/home/2018_fireflies.pdf"),
    ("Kanit 외 (2003)",
     "Determination of the size of the representative volume element",
     "Int. J. Solids and Structures 40",
     "단 하나의 최소 크기라는 발상을 버려야 한다. 무엇을 재느냐, 어느 정확도를 "
     "원하느냐, 몇 번 반복하느냐에 따라 달라진다. 답은 경계 조건 종류에 "
     "무관해야 한다.",
     "https://matperso.minesparis.psl.eu/Donnees/data04/464-kanit03.pdf"),
    ("Kulesza 외 (2022)", "MCNP 6.3.0 매뉴얼", "LANL LA-UR-22-30006",
     "거울 경계를 쓰면 면 전체 평균은 정확히 두 배가 되는데 한 점 값은 "
     "1.67 배로 <b>항상 틀리고 항상 낮게</b> 나온다. 주기 경계도 같다.",
     "https://mcnp.lanl.gov/pdf_files/"
     "TechReport_2022_LANL_LA-UR-22-30006Rev.1_KuleszaAdamsEtAl.pdf"),
]

OPEN = [
    "<b>읽는 창 가로 60 % 에 근거가 없다.</b> 그리고 그 상수가 네 파일에 따로 "
    "적혀 있어서 (<code>blender_render</code>, <code>crosscheck_mitsuba</code>, "
    "<code>mts_form</code>, <code>mts_worker</code> 는 0.0) 고치면 어긋난다.",
    "<b>빔 자리가 주기를 전제한다.</b> <code>apex_jitter</code> 나 "
    "<code>row_offset</code> 을 켜면 주기가 깨지는데 코드가 확인 없이 주기대로 "
    "걷는다. STEP 파일은 넣을 값이 없다.",
    "<b>벌집이 왜 판 381 mm 를 필요로 했는지 모른다.</b> 되돌아온 빛이 3 mm "
    "인데 문헌의 두 규칙이 각각 38 배, 4 배 빗나간다.",
    "<b>실물 측정이 0 회다.</b> CIE 171:2006 은 기준 자료의 절반을 실험에서 "
    "가져오라고 한다. 시뮬레이터를 시뮬레이터로만 검사했다.",
    "<b>도료의 거칠기와 확산이 우리 값이 아니다.</b> MERL 의 검정 페인트에서 "
    "빌렸다. 거칠기가 반짝임을 1160 배 움직인다.",
]

style = re.search(r"<style>(.*?)</style>",
                  io.open(STYLE_FROM, encoding="utf-8").read(), re.S).group(1)

o = io.StringIO()
o.write('<!doctype html><html lang="ko"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<title>공식과 구현</title>\n')
o.write('<style>%s\n.tag{font-family:var(--mono);font-size:11px;'
        'color:var(--muted);letter-spacing:.06em}\nul{margin:0;padding-left:20px;'
        'max-width:70ch}\nli{margin:6px 0}\na{color:var(--cy)}\n'
        '.ax{border-left:3px solid var(--a);padding-left:14px;margin:22px 0}\n'
        '.g-jaem{color:#6bb873;font-weight:700}\n'
        '.g-none{color:var(--bad);font-weight:700}\n'
        '.g-half{color:#e0a44e;font-weight:700}\n'
        '</style></head><body>\n<div class="wrap">\n' % style)

o.write('<header><div class="eyebrow">Spill Sink Simulator · 방법</div>\n'
        '<h1>공식과 구현</h1>\n'
        '<p class="sub">이 시뮬레이터가 무엇을 어떻게 재는지, 설정값이 어디서 '
        '왔는지, 무엇이 아직 근거가 없는지. <b>숫자는 코드에서 직접 읽는다</b> '
        '-- 손으로 옮겨 적으면 코드를 고쳤을 때 이 문서가 조용히 거짓말을 '
        '한다.</p></header>\n')

# ---- 세 축
o.write('<section><h2>재는 값 셋</h2>\n')
for a in AXES:
    o.write('<div class="ax"><h3 style="margin:0 0 4px">%s <span class="tag">'
            '%s · %s</span></h3>\n' % (a["ko"], a["en"], a["arrow"]))
    o.write('<div class="scroll"><table><tbody>\n')
    for k, v in (("무엇을 재나", a["what"]), ("조명", a["light"]),
                 ("공식", a["formula"]), ("코드", a["code"]),
                 ("읽는 창", a["window"]), ("왜 이렇게", a["why"]),
                 ("걸리는 시간", a["cost"]), ("아는 결함", a["risk"])):
        o.write('<tr><td style="width:9em;color:var(--muted)">%s</td>'
                '<td>%s</td></tr>\n' % (k, v))
    o.write('</tbody></table></div></div>\n')
o.write('</section>\n')

# ---- 어느 축이 무엇을 쓰나
o.write('<section><h2>어느 축이 어느 설정을 쓰나</h2>\n'
        '<p>셋이 설정을 다 쓰는 게 아니다. 반사 총량은 하늘 조명이라 빔도 '
        '창도 안 쓴다. 그래서 이 문서의 결함이 총량에는 안 걸린다.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>설정</th>'
        '<th>반사 총량<br><span class="tag">total</span></th>'
        '<th>모양 뭉개기<br><span class="tag">smear</span></th>'
        '<th>정면 반짝임<br><span class="tag">head-on peak</span></th>'
        '</tr></thead><tbody>\n')
for nm, a_, b_, c_ in USES:
    cell = lambda v: ('<td class="n" style="color:#6bb873">%s</td>' % v
                      if v == "쓴다"
                      else '<td class="n" style="color:var(--muted)">%s</td>' % v)
    o.write('<tr><td>%s</td>%s%s%s</tr>\n'
            % (nm, cell(a_), cell(b_), cell(c_)))
o.write('</tbody></table></div>\n')
o.write('<p class="tag">지금 값: 봉우리 <b>%s</b> · 빔 자리 <b>%s</b> · '
        '빛줄기 <b>%s</b> · 자리 수 <b>%s</b></p></section>\n'
        % (const(FB, "PEAK_STAT"), const(FB, "BEAM_POS"),
           const(FB, "SAMPLES"), const(FB, "N_PHASE")))

# ---- 설정값
o.write('<section><h2>설정값과 그 근거</h2>\n'
        '<p>값은 소스에서 읽는다. 근거 등급을 같이 적는다 -- '
        '<span class="g-jaem">잼</span>은 재거나 문헌에서 온 것, '
        '<span class="g-half">반쯤</span>은 일부만, '
        '<span class="g-none">없음</span>은 그냥 정한 것이다.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>설정</th><th>값</th>'
        '<th>어디</th><th>근거</th><th>설명</th></tr></thead><tbody>\n')
for nm, val, where, grade, note in SETTINGS:
    cls = {"잼": "g-jaem", "없음": "g-none"}.get(grade, "g-half")
    o.write('<tr><td>%s</td><td class="n"><b>%s</b></td>'
            '<td class="tag">%s</td><td class="%s">%s</td><td>%s</td></tr>\n'
            % (nm, val, where, cls, grade, note))
o.write('</tbody></table></div>\n')
o.write('<p class="tag">설정이 아홉 군데에 흩어져 있다. 한곳에 모으는 것이 '
        '남은 일이다.</p></section>\n')

# ---- 왜 이렇게 만들었나
o.write('<section><h2>왜 이렇게 만들었나 -- 재서 알아낸 것</h2>\n')
o.write('<div class="scroll"><table><thead><tr><th>알아낸 것</th>'
        '<th>무슨 일인가</th><th>우리가 잰 것</th><th>근거</th>'
        '</tr></thead><tbody>\n')
for t, w, m, r in FINDINGS:
    o.write('<tr><td><b>%s</b></td><td>%s</td><td>%s</td>'
            '<td class="tag">%s</td></tr>\n' % (t, w, m, r))
o.write('</tbody></table></div></section>\n')

# ---- 아직 근거 없는 것
o.write('<section><div class="card verdict"><h2 style="margin:0">'
        '아직 근거가 없는 것</h2>\n<ul>\n')
for x in OPEN:
    o.write('<li>%s</li>\n' % x)
o.write('</ul></div></section>\n')

# ---- 참고 문헌
o.write('<section><h2>참고 문헌</h2>\n'
        '<p class="tag">원문을 열어 확인한 것만 싣는다. 유료라 못 읽은 것은 '
        '싣지 않았다. 받아 둔 원문은 '
        '<code>project/reference/papers_method/</code> 에 있다 -- 링크가 '
        '죽어도 읽을 수 있게.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>저자</th><th>제목</th>'
        '<th>어디</th><th>무엇을 말하나</th></tr></thead><tbody>\n')
for who, title, where, says, url in REFS:
    o.write('<tr><td>%s</td><td><a href="%s">%s</a></td>'
            '<td class="tag">%s</td><td>%s</td></tr>\n'
            % (who, url, title, where, says))
o.write('</tbody></table></div></section>\n')

o.write('<section><p class="tag">이 문서를 짓는 스크립트: '
        '<code>scripts/build_method_report.py</code>. 설정값은 '
        '<code>scripts/form_buildable.py</code> 와 '
        '<code>scripts/blender_render.py</code> 에서 읽는다.</p></section>\n')
o.write('</div></body></html>\n')

html = o.getvalue()
bad = [ln.strip()[:80] for ln in html.split("\n") if "%%" in ln or "%s" in ln]
if bad:
    for ln in bad:
        print("남은 서식: %s" % ln)
    raise SystemExit("서식이 안 풀렸다 -- 발행 안 함")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, "w", encoding="utf-8").write(html)
print("%s  (%d 바이트)" % (OUT, len(html)))
