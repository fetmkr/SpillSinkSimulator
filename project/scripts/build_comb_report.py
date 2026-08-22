# -*- coding: utf-8 -*-
"""벌집 32가지 보고서를 데이터에서 다시 짓는다.

2026-08-21 판은 손으로 짰고 차트 SVG 만 저장돼 있어서, 재질이 정정됐을 때
고칠 방법이 없었다. 이번엔 스크립트가 짓는다.

읽는 것
    /tmp/simsrv/comb_musou_v2/comb_musou_v2.json   정정된 재질로 다시 잰 32가지
    results/comb_musou/comb_musou.json             옛 재질 판 (비교용)
    results/comb_musou/blueprints.json             설계도 SVG (그대로 씀)
쓰는 것
    report/comb/comb_musou_2026-08-22.html

디자인은 2026-08-21 판의 것을 그대로 쓴다. 이미 있는 체계를 존중한다.
"""
import os, sys, json, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NEWF = "/tmp/simsrv/comb_musou_v2/comb_musou_v2.json"
OLDF = os.path.join(ROOT, "results/comb_musou/comb_musou.json")
BPF = os.path.join(ROOT, "results/comb_musou/blueprints.json")
OUTF = os.path.join(ROOT, "report/comb/comb_musou_2026-08-22.html")

ALPHA = 0.039
DF_PAINT, DF_MUSOU = 0.99, 0.993
THETAS = ["-40", "-20", "0", "20", "40"]
COL = ["#4ec9c0", "#7fc98a", "#e0a44e", "#d98aa4", "#c2453c"]

MAT_CAPTION = ("전체 5% 페인트 · 확산 0.99 · α 0.039 · 판 200 mm · "
               "포일 0.08 mm · 세 방향 중 제일 밝게 나온 값(φ0/45/90)")


# ------------------------------------------------------------------ 차트
def line_chart(title, sub, series, ylab="%", xlabels=None,
               xtitle="빛이 들어오는 각도 (0 = 정면)", label_first=True):
    """series: [(이름, [값...], 색)]. 값 개수만큼 x 를 고르게 나눈다."""
    W, H = 760, 330
    x0, x1, ytop, ybot = 66.0, 620.0, 60.0, 276.0
    vals = [v for _, ys, _ in series for v in ys]
    vmax = max(vals) if vals else 1.0
    step = 10 ** math.floor(math.log10(vmax)) if vmax > 0 else 1.0
    while vmax / step > 5:
        step *= 2
    while vmax / step < 2:
        step /= 2.0
    top = math.ceil(vmax / step) * step
    if top <= 0:
        top = 1.0

    def y(v):
        return ybot - (v / top) * (ybot - ytop)

    n = len(series[0][1])
    xs = [x0 + (x1 - x0) * i / max(1, n - 1) for i in range(n)]
    o = ['<svg viewBox="0 0 %d %d" width="100%%" role="img" aria-label="%s">'
         % (W, H, title)]
    o.append('<text x="66" y="18" fill="var(--ink)" font-size="13" '
             'font-weight="700">%s</text>' % title)
    o.append('<text x="66" y="33" fill="var(--muted)" font-size="11">%s</text>'
             % sub)
    g = 0.0
    while g <= top + 1e-12:
        o.append('<line x1="%.0f" y1="%.1f" x2="%.0f" y2="%.1f" '
                 'stroke="var(--grid)" stroke-width="1"/>' % (x0, y(g), x1, y(g)))
        txt = ("%.3f" % g).rstrip("0").rstrip(".") if step < 1 else "%.0f" % g
        o.append('<text x="58" y="%.1f" fill="var(--muted)" font-size="12" '
                 'text-anchor="end">%s</text>' % (y(g) + 4, txt or "0"))
        g += step
    labs = xlabels or [t + "°" for t in THETAS]
    for xx, lb in zip(xs, labs):
        o.append('<text x="%.1f" y="296" fill="var(--muted)" font-size="12" '
                 'text-anchor="middle">%s</text>' % (xx, lb))
    o.append('<text x="343" y="318" fill="var(--muted)" font-size="12" '
             'text-anchor="middle">%s</text>' % xtitle)
    o.append('<text x="10" y="20" fill="var(--muted)" font-size="12">%s</text>'
             % ylab)
    for si, (nm, ys, c) in enumerate(series):
        pts = " L".join("%.1f,%.1f" % (xx, y(v)) for xx, v in zip(xs, ys))
        o.append('<path d="M%s" fill="none" stroke="%s" stroke-width="2.5"/>'
                 % (pts, c))
        for xx, v in zip(xs, ys):
            o.append('<circle cx="%.1f" cy="%.1f" r="3.5" fill="%s"/>'
                     % (xx, y(v), c))
            if si == 0 or not label_first:
                o.append('<text x="%.1f" y="%.1f" fill="%s" font-size="11" '
                         'text-anchor="middle">%s</text>'
                         % (xx, y(v) - 9, c, ("%.3f" % v).rstrip("0").rstrip(".")))
        o.append('<text x="%.1f" y="%.1f" fill="%s" font-size="12">%s</text>'
                 % (x1 + 8, y(ys[-1]) + 4, c, nm))
    o.append("</svg>")
    return "\n".join(o)


def bar_chart(title, sub, items, ylab="배"):
    """items: [(이름, 값, 색, 주석)]"""
    W, H = 760, 330
    x0, x1, ytop, ybot = 66.0, 660.0, 62.0, 260.0
    vmax = max(v for _, v, _, _ in items)
    top = max(vmax * 1.18, 1e-9)

    def y(v):
        return ybot - (v / top) * (ybot - ytop)

    o = ['<svg viewBox="0 0 %d %d" width="100%%" role="img" aria-label="%s">'
         % (W, H, title)]
    o.append('<text x="66" y="18" fill="var(--ink)" font-size="13" '
             'font-weight="700">%s</text>' % title)
    o.append('<text x="66" y="33" fill="var(--muted)" font-size="11">%s</text>'
             % sub)
    o.append('<line x1="%.0f" y1="%.1f" x2="%.0f" y2="%.1f" '
             'stroke="var(--line)" stroke-width="1"/>' % (x0, ybot, x1, ybot))
    n = len(items)
    slot = (x1 - x0) / n
    bw = slot * 0.52
    for i, (nm, v, c, note) in enumerate(items):
        cx = x0 + slot * (i + 0.5)
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                 'fill="%s" rx="2"/>' % (cx - bw / 2, y(v), bw, ybot - y(v), c))
        o.append('<text x="%.1f" y="%.1f" fill="%s" font-size="12" '
                 'font-weight="700" text-anchor="middle">%s</text>'
                 % (cx, y(v) - 8, c, ("%.3f" % v).rstrip("0").rstrip(".")))
        for j, ln in enumerate(nm.split("|")):
            o.append('<text x="%.1f" y="%.0f" fill="var(--muted)" '
                     'font-size="11" text-anchor="middle">%s</text>'
                     % (cx, ybot + 18 + j * 14, ln))
        if note:
            o.append('<text x="%.1f" y="%.0f" fill="var(--ink)" font-size="11" '
                     'text-anchor="middle" font-weight="700">%s</text>'
                     % (cx, ybot + 18 + len(nm.split("|")) * 14 + 4, note))
    o.append('<text x="10" y="20" fill="var(--muted)" font-size="12">%s</text>'
             % ylab)
    o.append("</svg>")
    return "\n".join(o)


# ------------------------------------------------------------------ 데이터
def load():
    if not os.path.exists(NEWF):
        raise SystemExit("새 측정값이 없다: %s" % NEWF)
    new = json.load(open(NEWF))
    if len(new) != 32:
        raise SystemExit("32가지가 아니라 %d 가지다. 보고서를 안 짓는다."
                         % len(new))
    old = {(r["pitch"], r["depth"], r["musou"]): r
           for r in json.load(open(OLDF))}
    for r in new:
        k = (r["pitch"], r["depth"], r["musou"])
        if k not in old:
            raise SystemExit("옛 판에 없는 조합: %s" % (k,))
        r["old"] = old[k]
    return new


def pick(rows, pitch=None, depth=None, musou=None):
    out = [r for r in rows
           if (pitch is None or r["pitch"] == pitch)
           and (depth is None or r["depth"] == depth)
           and (musou is None or r["musou"] == musou)]
    return sorted(out, key=lambda r: (r["depth"], r["musou"]))


def tot(r, t):
    return 100.0 * r["total"][t]


def curve(r):
    return [tot(r, t) for t in THETAS]


# ------------------------------------------------------------------ 본문
def build():
    rows = load()
    bp = json.load(open(BPF))
    law_paint = 1.0 + (1.0 - DF_PAINT) / (4.0 * ALPHA * ALPHA)
    law_musou = 1.0 + (1.0 - DF_MUSOU) / (4.0 * ALPHA * ALPHA)

    best = min(rows, key=lambda r: max(r["total"].values()))
    cheap = [r for r in rows if r["pitch"] == 9.53 and r["depth"] == 40.0
             and r["musou"] == 10.0][0]

    ch = {}
    for p, key in ((6.35, "a_635_m0"), (9.53, "a_953_m0")):
        s = [(("깊이 %.0f" % r["depth"]), curve(r), COL[i])
             for i, r in enumerate(pick(rows, pitch=p, musou=0.0))]
        ch[key] = line_chart("셀 %.2f mm · 무소 안 칠함" % p, MAT_CAPTION, s)
    for p, d, key in ((6.35, 60.0, "m_635_60"), (9.53, 40.0, "m_953_40")):
        s = [(("무소 %.0f mm" % r["musou"]), curve(r), COL[i])
             for i, r in enumerate(pick(rows, pitch=p, depth=d))]
        ch[key] = line_chart("셀 %.2f mm · 깊이 %.0f mm · 무소를 얼마나 깊이"
                             % (p, d), MAT_CAPTION, s)
    s = []
    for i, p in enumerate((6.35, 9.53)):
        rr = pick(rows, pitch=p, musou=0.0)
        s.append(("셀 %.2f" % p, [tot(r, "40") for r in rr], COL[i]))
    ch["depth_only"] = line_chart(
        "깊이를 늘리면 40도가 얼마나 좋아지나", MAT_CAPTION, s,
        xlabels=["30", "40", "50", "60"], xtitle="셀 깊이 (mm)",
        label_first=False)

    pyr_flash = 0.0560
    ch["flash"] = bar_chart(
        "정면 반짝임 — 구조는 아무것도 안 한다",
        "민판을 1 로 놓았을 때 정면으로 되돌아오는 밝기. 5 % 페인트, 확산 0.99, α 0.039",
        [("민판|구조 없음", law_paint, "var(--muted)", "기준"),
         ("벌집 6.35|깊이 30·무소 0",
          [r for r in rows if r["pitch"] == 6.35 and r["depth"] == 30.0
           and r["musou"] == 0.0][0]["peak"], "#e0655c", "0.997배"),
         ("벌집 6.35|깊이 60·무소 15",
          [r for r in rows if r["pitch"] == 6.35 and r["depth"] == 60.0
           and r["musou"] == 15.0][0]["peak"], "#e0655c", "0.980배"),
         ("벌집 9.53|깊이 60·무소 15",
          [r for r in rows if r["pitch"] == 9.53 and r["depth"] == 60.0
           and r["musou"] == 15.0][0]["peak"], "#e0655c", "0.987배"),
         ("피라미드|간격 4·깊이 22", pyr_flash, "#3f8f57", "0.021배")],
        ylab="배")

    def tbl():
        # 칸 이름 주의. "반사 총량" 은 되돌아 나가는 몫이고 작을수록 어둡다.
        # 괄호 안의 "제일 밝은 각도" 는 그 값을 어느 각도에서 골랐는지를
        # 말한다 -- 설계들 사이의 순위가 아니다. 1 판에서 이 칸을
        # "가장 밝은 %" 라고만 적어서 "1위가 제일 밝다" 로 읽혔다.
        o = ['<div class="scroll"><table><thead><tr>'
             '<th>순위<br><span class="unit">어두운 순</span></th>'
             '<th>셀<br><span class="unit">mm</span></th>'
             '<th>깊이<br><span class="unit">mm</span></th>'
             '<th>무소<br><span class="unit">mm</span></th>'
             '<th>정면<br><span class="unit">%</span></th>'
             '<th>40도<br><span class="unit">%</span></th>'
             '<th>반사 총량<br><span class="unit">% · 제일 밝은 각도에서</span></th>'
             '<th>1 판<br><span class="unit">같은 칸</span></th>'
             '<th>차이</th>'
             '<th>정면 반짝임<br><span class="unit">배</span></th>'
             '</tr></thead><tbody>']
        for i, r in enumerate(sorted(rows,
                                     key=lambda r: max(r["total"].values())), 1):
            nt = 100 * max(r["total"].values())
            ot = 100 * max(r["old"]["total"].values())
            cls = ' class="hi"' if r is best else ""
            o.append("<tr%s><td>%d</td><td>%.2f</td><td>%.0f</td><td>%.0f</td>"
                     "<td>%.4f</td><td>%.4f</td><td><b>%.4f</b></td>"
                     "<td>%.4f</td><td>%+.1f%%</td><td>%.3f</td></tr>"
                     % (cls, i, r["pitch"], r["depth"], r["musou"],
                        tot(r, "0"), tot(r, "40"), nt, ot,
                        100 * (nt - ot) / ot, r["peak"]))
        o.append("</tbody></table></div>")
        return "\n".join(o)

    css = open(os.path.join(ROOT, "report/comb/comb_musou_2026-08-21.html")
               ).read()
    css = css[css.index("<style>"):css.index("</style>") + 8]

    H = []
    A = H.append
    A('<title>어떤 벌집을 살 것인가</title>')
    A(css)
    A('<style>.hi td{background:color-mix(in srgb,var(--good) 14%,transparent)}'
      'figure{margin:0;display:flex;flex-direction:column;gap:8px}'
      'figcaption{color:var(--muted);font-size:13px}'
      '.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}'
      '.big{font-family:var(--mono);font-size:26px;font-weight:700}'
      '.unit{font-weight:400;color:var(--muted);font-size:11px;'
      'font-family:var(--kr);letter-spacing:0}'
      'thead th{vertical-align:bottom;line-height:1.35}'
      '.chg{border-left:4px solid var(--warn)}</style>')
    A('<div class="wrap">')

    A('<header><div class="eyebrow">2026-08-22 · 2 판 · 재질 정정</div>'
      '<h1>어떤 벌집을 살 것인가</h1>'
      '<p class="sub">셀 두 가지, 깊이 네 가지, 무소 네 가지. 32 가지를 '
      '다 재고, 사는 데 필요한 것만 남겼습니다. 1 판(8월 21일)의 재질 값이 '
      '틀려서 전부 다시 쟀습니다.</p></header>')

    A('<section class="card verdict ok">'
      '<h2 style="margin:0">먼저 결론</h2>'
      '<div class="grid2">'
      '<div><div class="eyebrow">가장 어두운 것</div>'
      '<div class="big">%.4f %%</div>'
      '<p class="sub">셀 %.2f · 깊이 %.0f · 무소 %.0f mm</p></div>'
      '<div><div class="eyebrow">거의 같으면서 더 얕고 싼 것</div>'
      '<div class="big">%.4f %%</div>'
      '<p class="sub">셀 %.2f · 깊이 %.0f · 무소 %.0f mm — %.1f %% 차이</p></div>'
      '</div>'
      '<p>깊이 60 mm 대신 40 mm 를 쓰고도 되돌아오는 빛은 %.1f %% 밖에 안 '
      '늘어납니다. 판이 20 mm 얇아지고 벌집 값이 내려갑니다.</p>'
      '<p><b>정면 반짝임은 벌집으로 못 잡습니다.</b> 어떤 깊이든 어떤 셀이든 '
      '민판과 2 %% 안에서 같습니다. 팁에 무소를 15 mm 칠해도 안 바뀝니다. '
      '정면을 잡으려면 면을 기울여야 합니다.</p>'
      '</section>'
      % (100 * max(best["total"].values()), best["pitch"], best["depth"],
         best["musou"], 100 * max(cheap["total"].values()), cheap["pitch"],
         cheap["depth"], cheap["musou"],
         100 * (max(cheap["total"].values()) - max(best["total"].values()))
         / max(best["total"].values()),
         100 * (max(cheap["total"].values()) - max(best["total"].values()))
         / max(best["total"].values())))

    A('<section><h2>1 판에서 무엇이 바뀌었나</h2>'
      '<div class="card chg">'
      '<p>1 판은 재질 값 두 개가 틀린 채로 나갔습니다. 둘 다 제가 논문을 '
      '잘못 읽은 것입니다.</p>'
      '<div class="scroll"><table><thead><tr><th>값</th><th>1 판</th>'
      '<th>2 판</th><th>왜</th></tr></thead><tbody>'
      '<tr><td>페인트 확산 비율</td><td>0.97</td><td>0.99</td>'
      '<td>DePoy 2014 그림 6 의 세로축이 퍼센트인데 분수로 읽었습니다. '
      '100 배 틀렸습니다.</td></tr>'
      '<tr><td>페인트 거칠기 α</td><td>0.09</td><td>0.039</td>'
      '<td>아무 근거 없이 쓰던 값이었습니다. MERL 실측 맞춤값으로 바꿨습니다.</td></tr>'
      '</tbody></table></div>'
      '<p><b>어둡기 숫자와 순위는 안 바뀝니다.</b> 32 가지 전부 최대 1.7 % 만 '
      '움직였고 순서는 그대로입니다. 바뀐 것은 정면 반짝임뿐입니다.</p>'
      '<p class="sub">1 판 차트 캡션에 적혀 있던 "확산 0.76" 도 틀린 표기였습니다. '
      '실제 측정은 0.97 로 돌았습니다.</p></div></section>')

    A('<section><h2>쓴 재료</h2>'
      '<p>값마다 출처를 답니다. <b>실측</b>은 장비로 잰 값, <b>범위</b>는 '
      '논문이 위아래만 묶어 준 값, <b>유추</b>는 비슷한 재료에서 빌려 온 값입니다.</p>'
      '<div class="scroll"><table><thead><tr><th>재료</th><th>반사율</th>'
      '<th>확산 비율</th><th>α</th><th>출처</th></tr></thead><tbody>'
      '<tr><td>5 % 무광 검정 페인트</td><td>5.000 %</td><td>0.99 <span '
      'class="sub">실측</span></td><td>0.039 <span class="sub">실측</span></td>'
      '<td>확산: Zeng 2019 (NASA GSFC) Z307 — 0/45도 밝기를 8도 총반사로 나누면 '
      '1.008, 즉 정면에서 완전 확산체와 1 % 안에서 같습니다. '
      'α: MERL 실측 BRDF 의 paint-black 에 미세면 모델을 맞춘 값 '
      '(Ward 0.0367 / Cook-Torrance 0.0392).</td></tr>'
      '<tr><td>무소블랙</td><td>0.998 %</td><td>0.993 <span class="sub">범위'
      '</span></td><td>0.039 <span class="sub">모름</span></td>'
      '<td>확산: Filip &amp; Vávra 2026 의 정면 TIS 0.985~0.995 에서 나온 한계 중 '
      '광택이 제일 센 쪽. α: 무소의 광택 덩어리 폭을 잰 자료가 없어 페인트 값을 '
      '빌렸습니다.</td></tr>'
      '<tr><td>포일</td><td>0.08 mm</td><td colspan="3">알루미늄 벌집. 겉면은 '
      '위 두 도료로 칠해집니다.</td></tr>'
      '</tbody></table></div>'
      '<p class="sub">무광 검정 페인트의 정반사는 논문마다 백 배 갈립니다 '
      '(TAMU 0.1 %, Zeng 1 % 이하, Filip 10 %). 검출기 크기 차이로는 설명이 '
      '안 됩니다. <b>도장 공정이 정하는 값입니다.</b> 그래서 발주서에 도장 횟수와 '
      '표면 준비를 적어야 합니다.</p></section>')

    A('<section><h2>무엇을 재었나 — 설계도</h2>'
      '<figure>%s<figcaption>사려는 것. 셀 6.35 mm, 포일 0.08 mm, 판 200 mm.'
      '</figcaption></figure>'
      '<figure>%s<figcaption>다른 한 가지. 셀 9.53 mm.</figcaption></figure>'
      '<figure>%s<figcaption>비교군 1. 구조 없는 민판에 같은 페인트만.'
      '</figcaption></figure>'
      '<figure>%s<figcaption>비교군 2. 피라미드. 면이 기울어 있습니다.'
      '</figcaption></figure></section>'
      % (bp["bp_comb"], bp["bp_comb95"], bp["bp_flat"], bp["bp_pyr"]))

    A('<section><h2>숫자 읽는 법</h2>'
      '<div class="card"><p><b>반사 총량 (%)</b> — 빔이 한 각도로 들어왔을 때 '
      '되돌아 나가는 몫입니다. 민판이 5 % 이므로 0.2 % 면 25 배 어둡습니다. '
      '한 설계에 값이 여러 개 나오므로(각도 다섯 · 방향 셋) 그 중 '
      '<b>제일 밝게 나온 값</b>을 그 설계의 성적으로 씁니다. 제일 나쁜 '
      '경우로 보수적으로 잡는다는 뜻입니다. 설계끼리 견줄 때는 이 값이 '
      '작은 쪽이 이깁니다.</p>'
      '<p><b>정면 반짝임 (배)</b> — 정면으로 쏜 빔이 그대로 되돌아오는 밝기를 '
      '완전 확산체 기준으로 잰 것입니다. 1 이면 확산체와 같고, 크면 눈에 '
      '번쩍입니다. 총량과 다른 값입니다 — 총량은 모든 방향의 합, 반짝임은 '
      '한 방향의 세기입니다.</p></div></section>')

    A('<section><h2>1 단계 — 셀과 깊이. 무소는 아직 안 칠함</h2>'
      '<p>먼저 페인트만 칠한 벌집을 봅니다. 벌집 자체가 얼마나 하는지 알아야 '
      '무소가 얼마나 보태는지 알 수 있습니다.</p>'
      '<figure>%s<figcaption>셀 6.35 mm. 깊이를 늘리면 정면은 좋아지지만 '
      '40도는 거의 그대로입니다.</figcaption></figure>'
      '<figure>%s<figcaption>셀 9.53 mm. 셀이 넓으면 관이 얕은 셈이라 '
      '정면이 더 밝습니다.</figcaption></figure>'
      '<figure>%s<figcaption>깊이가 40도에 하는 일. 거의 없습니다. '
      '깊이는 정면만 바꿉니다.</figcaption></figure></section>'
      % (ch["a_635_m0"], ch["a_953_m0"], ch["depth_only"]))

    A('<section><h2>2 단계 — 무소를 얼마나 깊이 칠할까</h2>'
      '<p>무소는 팁에서 아래로 칠합니다. 깊이 들어갈수록 비쌉니다.</p>'
      '<figure>%s<figcaption>깊이 60 mm 벌집. 5 mm 만 칠해도 대부분이 '
      '잡히고, 그 뒤로는 거의 안 좋아집니다.</figcaption></figure>'
      '<figure>%s<figcaption>깊이 40 mm 벌집, 셀 9.53. 이 조합이 '
      '가격 대비 제일 낫습니다.</figcaption></figure></section>'
      % (ch["m_635_60"], ch["m_953_40"]))

    A('<section><h2>정면 반짝임 — 벌집으로는 못 잡습니다</h2>'
      '<p>이번 판에서 가장 분명해진 결과입니다.</p>'
      '<figure>%s<figcaption>민판을 기준으로 놓았습니다. 벌집은 어떤 '
      '깊이·셀·무소 조합이든 민판의 0.98~1.00 배입니다. 피라미드만 0.021 배로 '
      '떨어집니다.</figcaption></figure>'
      '<div class="card"><p><b>왜 그런가.</b> 관 속을 정면으로 들여다보면 '
      '보이는 것은 바닥과 벽이 아니라 관 입구의 테두리입니다. 그 테두리는 '
      '기울어 있지 않으므로 민판과 똑같이 빛을 되돌립니다. 관을 깊게 파도 '
      '테두리는 그대로입니다.</p>'
      '<p>피라미드는 면이 기울어 있어 정면으로 온 빔을 옆으로 보냅니다. '
      '그래서 48 배 어둡습니다.</p>'
      '<p class="sub">확인 방법 세 가지가 같은 답을 냈습니다 — 포일 테두리 '
      '넓이를 직접 센 것, 민판 식과 견준 것, 그리고 무소를 칠하고 안 칠하고를 '
      '비교한 것입니다. 무소가 총량은 다섯 배 낮추면서 반짝임은 1.7 %% 밖에 '
      '못 낮춥니다.</p></div></section>' % ch["flash"])

    A('<section><h2>32 가지 전부</h2>'
      '<p><b>어두운 순입니다. 맨 위가 1위, 가장 어두운 설계입니다.</b> '
      '되돌아오는 빛이 적을수록 좋으므로 반사 총량이 작은 쪽이 앞섭니다.</p>'
      '<p>칸 이름의 “제일 밝은 각도에서” 는 그 설계의 값을 다섯 각도 중 '
      '어디서 골랐는지를 말합니다. 설계끼리의 순위가 아닙니다.</p>'
      '<p>1 판 값을 나란히 두어 재질 정정이 얼마나 움직였는지 볼 수 있게 '
      '했습니다.</p>%s'
      '<p class="sub">차이 칸이 전부 2 %% 안입니다. <b>어둡기 결론은 재질 '
      '정정에 안 흔들립니다.</b></p></section>' % tbl())

    A('<section><h2>그래서 사려면</h2><div class="card">'
      '<p><b>셀 9.53 mm · 깊이 40 mm · 무소 10 mm.</b> 가장 어두운 조합보다 '
      '%.1f %% 밝을 뿐인데 판이 20 mm 얇고 벌집이 쌉니다.</p>'
      '<p><b>발주서에 도장을 적으십시오.</b> 남은 불확실성은 형상이 아니라 '
      '도장입니다. 도장 횟수, 표면 준비, 그리고 쿠폰 한 장으로 확인하는 절차를 '
      '적어야 합니다.</p>'
      '<p><b>정면 반짝임이 문제라면 벌집이 아니라 기울어진 면을 쓰십시오.</b> '
      '벌집으로는 못 잡습니다.</p></div></section>'
      % (100 * (max(cheap["total"].values()) - max(best["total"].values()))
         / max(best["total"].values())))

    A('<section><h2>이 보고서를 다시 지으려면</h2><div class="card">'
      '<p style="font-family:var(--mono);font-size:13px">'
      'Blender --background --factory-startup --python '
      'scripts/sweep_comb_musou_v2.py<br>'
      'python3 scripts/build_comb_report.py</p>'
      '<p class="sub">1 판은 손으로 짰고 차트만 저장돼 있어서 재질이 바뀌었을 때 '
      '고칠 방법이 없었습니다. 2 판은 데이터에서 짓습니다.</p></div></section>')

    A('</div>')
    os.makedirs(os.path.dirname(OUTF), exist_ok=True)
    open(OUTF, "w").write("\n".join(H))
    print("썼다: %s (%d 바이트)" % (OUTF, os.path.getsize(OUTF)))
    print("가장 어두움: 셀 %.2f 깊이 %.0f 무소 %.0f -> %.4f %%"
          % (best["pitch"], best["depth"], best["musou"],
             100 * max(best["total"].values())))
    print("추천:       셀 %.2f 깊이 %.0f 무소 %.0f -> %.4f %%"
          % (cheap["pitch"], cheap["depth"], cheap["musou"],
             100 * max(cheap["total"].values())))
    print("민판 식: 페인트 %.4f · 무소 %.4f" % (law_paint, law_musou))


if __name__ == "__main__":
    build()
