# -*- coding: utf-8 -*-
"""왜 정면이 비스듬한 빛보다 어두운가 -- 그림을 짓는다. 한글판과 영문판.

2026-08-24 에 이 그림을 채팅 안에서 한 번 짜서 SVG 만 남겼다. 그래서
**다시 만들 수가 없었다** -- 영문 보고서에 넣을 영어판이 필요해졌을 때
그림만 한글로 남아 있었다. 보고서는 스크립트로 짓는다는 규칙이 그림에도
그대로 적용된다.

각도는 계산해서 그린다. 손으로 찍은 좌표가 하나도 없다.

    python3 scripts/build_ray_figure.py

쓰는 것
    figures/comb_headon_vs_oblique.svg      (한글, report/comb/paint_depth_2026-08-24.html 이 씀)
    figures/comb_headon_vs_oblique_en.svg   (영문, ..._en.html 이 씀)
"""
import io
import os
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTDIR = os.path.join(ROOT, "figures")

P, D, T = 9.53, 40.0, 0.08
S = 8.0                                   # mm 당 화소
HALF0 = math.degrees(math.atan((P / 2) / D))
D40 = (P / 2) / math.tan(math.radians(40.0))
HALF40 = math.degrees(math.atan((P / 2) / D40))
ESC0 = math.sin(math.radians(HALF0)) ** 2
ESC40 = math.sin(math.radians(HALF40)) ** 2

W, H = 1080, 640
TOPY, BOTY = 150.0, 150.0 + D * S

KO = {
    "title": "벌집 관은 한쪽으로만 열린 덫이다",
    "sub": ("셀 %.2f mm · 깊이 %.0f mm · 단면 하나. 각도는 실제 각도로 그렸다. "
            "포일은 실제 %.2f mm 인데 보이라고 굵게 그렸다." % (P, D, T)),
    "a_title": "정면으로 들어온 빛",
    "a_sub": "벽을 한 번도 안 스치고 바닥까지 간다",
    "a_exit": "바닥에서 본 출구는 반각 %.1f 도" % HALF0,
    "a_big": "%.1f %% 만 곧장 나간다" % (100 * ESC0),
    "a_note": "나머지 %.1f %% 는 벽에 부딪힌다" % (100 * (1 - ESC0)),
    "b_title": "비스듬히 들어온 빛 (40도)",
    "b_sub": "깊이 %.1f mm 에서 벽에 닿는다. 바닥까지 안 간다" % D40,
    "b_exit": "거기서 본 출구는 반각 %.0f 도" % HALF40,
    "b_big": "%.0f %% 가 곧장 나간다" % (100 * ESC40),
    "b_note": "정면보다 %.0f 배 잘 빠져나간다" % (ESC40 / ESC0),
    "depth": "깊이 %.0f mm" % D,
    "box": [("들어가기는 정면이 쉽다.", 1), ("벽을 안 스치니까.", 0), None,
            ("나오기는 정면이 어렵다.", 1), ("바닥에서 올려다보면 출구가", 0),
            ("반각 %.1f 도밖에 안 된다." % HALF0, 0), None,
            ("비스듬한 빛은 얕은 데서", 1), ("벽에 닿는다. 거기 출구는", 0),
            ("반각 40도로 활짝 열려 있다.", 0), None,
            ("그래서 정면이 5배 어둡다.", 2)],
}
EN = {
    "title": "A honeycomb cell is a trap that opens one way",
    "sub": ("%.2f mm cell · %.0f mm deep · one cross-section. Angles are drawn "
            "true. The foil is %.2f mm; drawn thick to be visible." % (P, D, T)),
    "a_title": "Light arriving head-on",
    "a_sub": "never touches a wall, reaches the floor",
    "a_exit": "exit seen from the floor: %.1f deg half-angle" % HALF0,
    "a_big": "only %.1f %% leaves directly" % (100 * ESC0),
    "a_note": "the other %.1f %% hits a wall" % (100 * (1 - ESC0)),
    "b_title": "Light arriving at 40 degrees",
    "b_sub": "meets a wall %.1f mm down. Never reaches the floor" % D40,
    "b_exit": "exit seen from there: %.0f deg half-angle" % HALF40,
    "b_big": "%.0f %% leaves directly" % (100 * ESC40),
    "b_note": "%.0f times the head-on share" % (ESC40 / ESC0),
    "depth": "%.0f mm deep" % D,
    "box": [("Getting in is easy head-on.", 1), ("Nothing is in the way.", 0),
            None,
            ("Getting out is hard head-on.", 1), ("From the floor the exit is", 0),
            ("only %.1f degrees wide." % HALF0, 0), None,
            ("Oblique light meets a wall", 1), ("near the top, where the exit", 0),
            ("is wide open at 40 degrees.", 0), None,
            ("Hence 5x darker head-on.", 2)],
}


def build(L, lang):
    o = io.StringIO()
    o.write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d" font-family="Helvetica,Arial,sans-serif">\n'
            % (W, H, W, H))
    o.write('<rect width="%d" height="%d" fill="#f4f1eb"/>\n' % (W, H))
    o.write('<defs>%s</defs>\n' % "".join(
        '<marker id="m%s" markerWidth="10" markerHeight="10" refX="8" '
        'refY="3.2" orient="auto"><path d="M0,0 L8,3.2 L0,6.4 z" fill="%s"/>'
        '</marker>' % (i, c) for i, c in (("r", "#c8401c"), ("b", "#1e5fa8"))))

    def tube(cx, colour, title, sub):
        Lx, Rx = cx - P * S / 2, cx + P * S / 2
        o.write('<rect x="%.1f" y="%.1f" width="%.1f" height="14" fill="#333"/>\n'
                % (Lx - 4, BOTY, (Rx - Lx) + 8))
        for x in (Lx, Rx):
            o.write('<rect x="%.1f" y="%.1f" width="4" height="%.1f" '
                    'fill="#333"/>\n' % (x - 2, TOPY, BOTY - TOPY))
        o.write('<text x="%.1f" y="%.1f" font-size="16" font-weight="bold" '
                'fill="%s" text-anchor="middle">%s</text>\n'
                % (cx, TOPY - 66, colour, title))
        o.write('<text x="%.1f" y="%.1f" font-size="13" fill="#555" '
                'text-anchor="middle">%s</text>\n' % (cx, TOPY - 46, sub))
        return Lx, Rx

    # 정면
    cxA = 250.0
    LA, RA = tube(cxA, "#c8401c", L["a_title"], L["a_sub"])
    o.write('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#c8401c" '
            'stroke-width="2.5" marker-end="url(#mr)"/>\n'
            % (cxA, TOPY - 32, cxA, BOTY - 8))
    o.write('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" fill="#c8401c" '
            'fill-opacity="0.22"/>\n' % (cxA, BOTY, LA, TOPY, RA, TOPY))
    o.write('<text x="%.1f" y="%.1f" font-size="13" fill="#c8401c" '
            'text-anchor="middle">%s</text>\n' % (cxA, BOTY + 48, L["a_exit"]))
    o.write('<text x="%.1f" y="%.1f" font-size="21" font-weight="bold" '
            'fill="#c8401c" text-anchor="middle">%s</text>\n'
            % (cxA, BOTY + 78, L["a_big"]))
    o.write('<text x="%.1f" y="%.1f" font-size="13" fill="#666" '
            'text-anchor="middle">%s</text>\n' % (cxA, BOTY + 100, L["a_note"]))

    # 40 도
    cxB = 620.0
    LB, RB = tube(cxB, "#1e5fa8", L["b_title"], L["b_sub"])
    hy = TOPY + D40 * S
    sx = RB - 58 * math.sin(math.radians(40))
    sy = hy - 58 * math.cos(math.radians(40))
    o.write('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#1e5fa8" '
            'stroke-width="2.5" marker-end="url(#mb)"/>\n'
            % (sx, sy, RB - 5, hy - 4))
    o.write('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" fill="#1e5fa8" '
            'fill-opacity="0.22"/>\n' % (RB, hy, LB, TOPY, RB, TOPY))
    o.write('<circle cx="%.1f" cy="%.1f" r="4.5" fill="#1e5fa8"/>\n' % (RB, hy))
    o.write('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#1e5fa8" '
            'stroke-width="1" stroke-dasharray="3 3"/>\n' % (LB - 30, hy, RB, hy))
    o.write('<text x="%.1f" y="%.1f" font-size="12" fill="#1e5fa8" '
            'text-anchor="end">%.1f mm</text>\n' % (LB - 34, hy + 4, D40))
    o.write('<text x="%.1f" y="%.1f" font-size="13" fill="#1e5fa8" '
            'text-anchor="middle">%s</text>\n' % (cxB, BOTY + 48, L["b_exit"]))
    o.write('<text x="%.1f" y="%.1f" font-size="21" font-weight="bold" '
            'fill="#1e5fa8" text-anchor="middle">%s</text>\n'
            % (cxB, BOTY + 78, L["b_big"]))
    o.write('<text x="%.1f" y="%.1f" font-size="13" fill="#666" '
            'text-anchor="middle">%s</text>\n' % (cxB, BOTY + 100, L["b_note"]))

    # 치수와 제목
    o.write('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#aaa"/>\n'
            % (LA - 60, TOPY, LA - 60, BOTY))
    o.write('<text x="%.1f" y="%.1f" font-size="13" fill="#666" '
            'text-anchor="middle" transform="rotate(-90 %.1f %.1f)">%s</text>\n'
            % (LA - 74, (TOPY + BOTY) / 2, LA - 74, (TOPY + BOTY) / 2,
               L["depth"]))
    o.write('<text x="40" y="42" font-size="20" font-weight="bold" '
            'fill="#222">%s</text>\n' % L["title"])
    o.write('<text x="40" y="66" font-size="14" fill="#555">%s</text>\n'
            % L["sub"])

    # 설명 상자
    bx, by = 796, TOPY - 34
    o.write('<rect x="%d" y="%d" width="248" height="272" rx="6" fill="#e9e5dc" '
            'stroke="#d3cdc1"/>\n' % (bx, by))
    yy = by + 32
    for item in L["box"]:
        if item is None:
            yy += 9
            continue
        text, weight = item
        col = ("#666", "#222", "#c8401c")[weight]
        fs = (13, 15, 15)[weight]
        bold = ' font-weight="bold"' if weight else ""
        o.write('<text x="%d" y="%.0f" font-size="%d" fill="%s"%s>%s</text>\n'
                % (bx + 18, yy, fs, col, bold, text))
        yy += 22
    o.write('</svg>\n')
    return o.getvalue()


os.makedirs(OUTDIR, exist_ok=True)
for L, suffix, lang in ((KO, "", "한글"), (EN, "_en", "영문")):
    p = os.path.join(OUTDIR, "comb_headon_vs_oblique%s.svg" % suffix)
    io.open(p, "w", encoding="utf-8").write(build(L, lang))
    print("%s  %s  (%d 바이트)" % (lang, p, os.path.getsize(p)))
