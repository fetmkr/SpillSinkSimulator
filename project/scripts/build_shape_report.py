# -*- coding: utf-8 -*-
"""벌집의 모양을 어디서 고칠 것인가 -- 보고서를 데이터에서 짓는다.

`build_paint_depth_report.py` 가 답한 질문은 "안쪽을 어디까지 칠하나" 였다.
이건 그 다음 질문이다: **칠로는 더 못 가는 두 면의 모양을 바꾸면 어떻게 되나.**

읽는 것
    results/comb_depth/rim_and_floor.json      테두리 깎기 · 바닥판 피라미드
    results/comb_depth/pyramid_inverted.json   뒤집힌 피라미드
    results/paint_depth/paint_depth_9p53_40.json  세 면이 맡는 몫(인용용)
    material/*.json                            재료 값과 색
    report/comb/comb_musou_2026-08-22.html     디자인. 이미 있는 체계를 쓴다.
쓰는 것
    report/comb/rim_floor_2026-08-25.html

설계도는 여기서 그린다. 셀 하나를 잘라서 고치는 두 면을 표시한다 --
숫자 표만 있는 보고서는 읽는 사람이 어디를 고치는 건지 모른다.
"""
import os
import re
import io
import json
import glob
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RIM = os.path.join(ROOT, "results/comb_depth/rim_and_floor.json")
INV = os.path.join(ROOT, "results/comb_depth/pyramid_inverted.json")
DEPTHF = os.path.join(ROOT, "results/paint_depth/paint_depth_9p53_40.json")
STYLE_FROM = os.path.join(ROOT, "report/comb/comb_musou_2026-08-22.html")
# 벌집 연구는 전부 report/comb/ 에 모은다. 2026-08-24 에 내가 만든
# report/coating/ 은 같은 주제에 폴더만 하나 더 늘린 것이라 없앴다.
OUT = os.path.join(ROOT, "report/comb/rim_floor_2026-08-25.html")

rim = {r["name"]: r for r in json.load(open(RIM))}
inv = {r["name"]: r for r in json.load(open(INV))}
pd = json.load(open(DEPTHF))
pdby = {r["paint_depth"]: r for r in pd}
BASE, BEST = rim["기준"], rim["AB 0.03 + 피라미드 15"]
PITCH, DEPTH = BASE["pitch"], BASE["depth"]


def mat(mid):
    d = json.load(open(os.path.join(ROOT, "material", "%s.json" % mid)))
    return {"rho": d["scattering"]["reflectance"]["value"],
            "df": d["bsdf"]["diffuse_fraction"],
            "color": d.get("color", "#333"),
            "label": d.get("label_en") or d.get("label") or mid}


MUSOU = mat("musou_fit")

# 정면 반사를 셋으로 나눈 몫 -- paint_depth 자료에서 다시 계산한다.
t_none, t_rim = pdby[0.0]["total"]["0"], pdby[1.0]["total"]["0"]
t_wall, t_all = pdby[20.0]["total"]["0"], pdby[40.0]["total"]["0"]
span = t_none - t_all
SHARE = {"rim": 100.0 * (t_none - t_rim) / span,
         "wall": 100.0 * (t_rim - t_wall) / span,
         "floor": 100.0 * (t_wall - t_all) / span}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


# ---------------------------------------------------------------- 설계도
def blueprint():
    """셀 하나를 잘라, 고치는 두 면을 표시한다. 각도와 비율은 실제 값."""
    S = 7.0                      # mm 당 화소
    W, H = 900, 470
    x0, y0 = 250.0, 70.0         # 셀 왼쪽 위
    cw, ch = PITCH * S, DEPTH * S
    o = ['<svg viewBox="0 0 %d %d" width="100%%" style="height:auto" '
         'font-family="var(--kr)">' % (W, H)]
    o.append('<rect width="%d" height="%d" fill="#f4f1eb"/>' % (W, H))

    def cell(ox, title, wall_px, floor_kind, note):
        g = ['<text x="%.0f" y="%.0f" font-size="15" font-weight="700" '
             'text-anchor="middle" fill="#222">%s</text>'
             % (ox + cw / 2, y0 - 30, title)]
        # 벽 두 장
        for x in (ox, ox + cw):
            g.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                     'fill="#c8401c"/>' % (x - wall_px / 2, y0, wall_px, ch))
        # 바닥
        if floor_kind == "flat":
            g.append('<rect x="%.1f" y="%.1f" width="%.1f" height="12" '
                     'fill="#1e5fa8"/>' % (ox - 4, y0 + ch, cw + 8))
        else:
            # 눌러 찍은 판이지 덩어리가 아니다. 밑에 판을 깔고 그 위에
            # 봉우리를 세운다 -- 첫 판은 통짜 파랑이라 판으로 안 읽혔다.
            fh = 15.0 * S                       # 피라미드 깊이 15 mm
            n = 3
            pw = cw / n
            g.append('<rect x="%.1f" y="%.1f" width="%.1f" height="9" '
                     'fill="#1e5fa8"/>' % (ox - 4, y0 + ch, cw + 8))
            for i in range(n):
                g.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" '
                         'fill="#1e5fa8"/>'
                         % (ox + i * pw, y0 + ch,
                            ox + (i + 0.5) * pw, y0 + ch - fh,
                            ox + (i + 1) * pw, y0 + ch))
        # 정면으로 들어오는 빛
        g.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#333" '
                 'stroke-width="2" marker-end="url(#ar)"/>'
                 % (ox + cw / 2, y0 - 18, ox + cw / 2, y0 + ch - 10))
        g.append('<text x="%.0f" y="%.0f" font-size="12" fill="#555" '
                 'text-anchor="middle">%s</text>'
                 % (ox + cw / 2, y0 + ch + 40, note))
        return "\n".join(g)

    o.append('<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="7" '
             'refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 z" fill="#333"/>'
             '</marker></defs>')
    o.append(cell(x0, "지금", 8.0, "flat", "테두리 0.08 mm · 평평한 바닥판"))
    o.append(cell(x0 + cw + 150, "고친 것", 3.0, "pyr",
                  "테두리 0.03 mm · 눌러 찍은 피라미드"))

    # 세 면이 맡는 몫
    lx = 40
    o.append('<text x="%d" y="%d" font-size="14" font-weight="700" fill="#222">'
             '정면 반사를 누가 맡나</text>' % (lx, y0 + 6))
    for i, (nm, key, col, can) in enumerate(
            (("포일 테두리", "rim", "#c8401c", "겉면이다"),
             ("셀 벽", "wall", "#888", "손댈 게 없다"),
             ("바닥판", "floor", "#1e5fa8", "평평한 판이다"))):
        y = y0 + 40 + i * 62
        o.append('<rect x="%d" y="%d" width="12" height="12" fill="%s"/>'
                 % (lx, y - 10, col))
        o.append('<text x="%d" y="%d" font-size="13" fill="#222">%s</text>'
                 % (lx + 20, y, nm))
        o.append('<text x="%d" y="%d" font-size="19" font-weight="800" '
                 'fill="%s" font-family="var(--mono)">%.1f %%</text>'
                 % (lx + 20, y + 22, col, SHARE[key]))
        # 설명은 퍼센트 오른쪽에 붙이면 겹친다 -- 실제로 "51.4 %겉면이다" 로
        # 찍혔다. 줄을 바꾼다.
        o.append('<text x="%d" y="%d" font-size="11" fill="#666">%s</text>'
                 % (lx + 20, y + 37, can))
    o.append('<text x="%d" y="%d" font-size="11" fill="#666">'
             '깊이는 이 둘을 못 없앤다</text>' % (lx, y0 + 40 + 3 * 62))
    o.append('</svg>')
    return "\n".join(o)


# ---------------------------------------------------------------- 문서
style = re.search(r"<style>(.*?)</style>",
                  io.open(STYLE_FROM, encoding="utf-8").read(), re.S).group(1)

o = io.StringIO()
o.write('<!doctype html><html lang="ko"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<title>벌집의 어디를 고칠 것인가</title>\n')
o.write('<style>%s\n.fig{background:#f4f1eb;border:1px solid var(--line);'
        'border-radius:3px;padding:12px;overflow-x:auto}\n'
        '.big{font-size:28px;font-weight:800;font-family:var(--mono);'
        'font-variant-numeric:tabular-nums}\n'
        '.grid3{display:grid;grid-template-columns:repeat(auto-fit,'
        'minmax(200px,1fr));gap:12px}\n'
        '.tag{font-family:var(--mono);font-size:11px;color:var(--muted);'
        'letter-spacing:.06em}\nul{margin:0;padding-left:20px;max-width:64ch}\n'
        'li{margin:5px 0}\na{color:var(--cy)}\n'
        'tr.no td{color:var(--bad)}\n</style></head><body>\n<div class="wrap">\n'
        % style)

o.write('<header><div class="eyebrow">2026-08-25 · 모양</div>\n')
o.write('<h1>벌집의 어디를 고칠 것인가</h1>\n')
o.write('<p class="sub">칠로는 더 못 간다. 정면 반사의 %.0f %% 를 포일 테두리가, '
        '%.0f %% 를 바닥판이 맡고, 둘 다 정면을 향한 평평한 면이라 깊이로는 '
        '안 없어진다. 그 두 면의 <b>모양</b>을 바꾸면 어떻게 되는지 잰 것이다.'
        '</p></header>\n' % (SHARE["rim"], SHARE["floor"]))

# ---- 결론
o.write('<section><div class="card verdict ok"><h2 style="margin:0">결론</h2>\n')
o.write('<p class="lead">테두리를 <b>0.08 에서 0.03 mm 로 깎고</b>, 평평한 '
        '바닥판을 <b>눌러 찍은 피라미드 판으로</b> 바꾼다.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>세 축</th>'
        '<th>지금</th><th>고친 것</th><th>몇 배</th></tr></thead><tbody>\n')
AX = [("반사 총량 정면", lambda r: 100 * r["total"]["0"], "%.5f %%", True),
      ("반사 총량 20도", lambda r: 100 * r["total"]["20"], "%.5f %%", True),
      ("반사 총량 40도", lambda r: 100 * r["total"]["40"], "%.5f %%", True),
      ("정면 반짝임", lambda r: r["head_on"], "%.4f", True)]
for nm, get, fmt, lower_better in AX:
    a, b = get(BASE), get(BEST)
    o.write('<tr><td>%s</td><td class="n">%s</td><td class="n"><b>%s</b></td>'
            '<td class="n">%.2f 배 어두움</td></tr>\n'
            % (nm, fmt % a, fmt % b, a / b))
sm_a = rim["기준"]["smear"]
sm_b = rim["AB 0.05 + 피라미드 10"]["smear"]
o.write('<tr><td>모양 뭉개기 <span class="tag">클수록 좋다 · 목표 1.42</span>'
        '</td><td class="n">%.4f</td><td class="n"><b>%.4f</b></td>'
        '<td class="n">처음 움직였다</td></tr>\n' % (sm_a, sm_b))
o.write('</tbody></table></div>\n')
o.write('<p class="tag">뭉개기는 테두리 0.05 + 피라미드 10 에서 잰 값이다 '
        '(한 점에 5 분이라 두 점만 쟀다). 나머지는 테두리 0.03 + 피라미드 15.</p>\n')
o.write('</div></section>\n')

# ---- 설계도
o.write('<section><h2>어디를 고치나</h2>\n')
o.write('<figure><div class="fig">%s</div>\n' % blueprint())
o.write('<figcaption class="tag">셀 하나를 자른 것. 벽 두께는 보이라고 굵게 '
        '그렸다 (실제 0.08 과 0.03 mm). 몫은 '
        '<code>results/paint_depth/paint_depth_9p53_40.json</code> 에서 '
        '다시 계산했다.</figcaption></figure>\n')
o.write('<p>셀 벽은 %.1f %% 밖에 안 맡는다. 그래서 <b>관 안쪽은 손댈 것이 '
        '없다.</b> 고칠 수 있는 두 면은 둘 다 겉으로 드러나 있다 — 테두리는 '
        '판의 앞면이고, 바닥판은 벌집을 붙이기 전의 평평한 판이다.</p>\n'
        % SHARE["wall"])
o.write('</section>\n')

# ---- 전파
o.write('<section><h2>무엇으로 바꿀지는 전파 쪽에서 찾았다</h2>\n')
o.write('<p>무반향실은 원래 피라미드를 쓴다. 설계 규칙이 파장으로 딱 정해져 '
        '있고 — 높이는 가장 낮은 주파수의 파장 이상, 밑변은 그 절반 이상, '
        '끝 폭은 가장 높은 주파수 파장의 절반 미만 — 1.5~9 GHz 에서 평균 '
        '-40 dB 이 나온다. 작동 원리도 우리와 같다. 여러 번 튕기고 튕길 때마다 '
        '먹힌다.</p>\n')
o.write('<p><b>그런데 요즘 수법 대부분은 우리에게 안 넘어온다.</b> 파장과 '
        '구조의 크기 관계가 다르기 때문이다.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th></th><th>파장</th>'
        '<th>구조</th><th>비</th></tr></thead><tbody>\n')
o.write('<tr><td>전파 10 GHz</td><td class="n">30 mm</td>'
        '<td class="n">mm~cm</td><td class="n">비슷함</td></tr>\n')
o.write('<tr><td>우리 빛 445 nm</td><td class="n">0.000445 mm</td>'
        '<td class="n">%.2f mm</td><td class="n"><b>%s 배</b></td></tr>\n'
        % (PITCH, format(int(PITCH / 0.000445), ",")))
o.write('</tbody></table></div>\n')
o.write('<p>전파는 파동 문제라 임피던스 정합도 위상 간섭도 메타표면 코딩도 '
        '성립한다. 우리는 순수 광선 문제다. 그 수법들은 전부 <b>파장 규모의 '
        '구조</b>를 요구하므로 쓸 수 없다.</p>\n')
o.write('<p>넘어오는 것은 원리 하나다. <b>갑자기 바꾸지 말고 서서히 바꾼다.</b> '
        '전파는 그걸 임피던스로 하고(377 옴에서 0 옴까지), 우리는 '
        '<b>살 두께</b>로 한다.</p>\n')
o.write('<p class="tag">논문은 <code>reference/papers_rf/</code>, 목록은 '
        '<code>reference/INDEX.md</code></p></section>\n')

# ---- A
o.write('<section><h2>A. 테두리만 깎는다</h2>\n')
o.write('<p>벌집의 <b>강도는 아래벽이 정하고 정면 반사는 위벽이 정한다.</b> '
        '노출 넓이 계산이 <code>wall_top</code> 만 쓴다 '
        '(<code>geom_topo.py:248</code>). 그러니 위만 얇게 하면 강도를 안 잃고 '
        '반사만 준다.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>위벽</th><th>테두리 넓이</th>'
        '<th>정면</th><th>20도</th><th>40도</th><th>반짝임</th>'
        '</tr></thead><tbody>\n')
for nm in ("기준", "A 테두리 0.05", "A 테두리 0.03", "A 테두리 0.02"):
    r = rim[nm]
    pick = ' class="pick"' if r["wall_top"] == 0.03 else ""
    o.write('<tr%s><td>%.2f mm</td><td class="n">%.2f %%</td>'
            '<td class="n"><b>%.5f %%</b></td><td class="n">%.5f %%</td>'
            '<td class="n">%.5f %%</td><td class="n">%.4f</td></tr>\n'
            % (pick, r["wall_top"], 100 * r["rim_fraction_est"],
               100 * r["total"]["0"], 100 * r["total"]["20"],
               100 * r["total"]["40"], r["head_on"]))
o.write('</tbody></table></div>\n')
o.write('<p>0.08 에서 0.03 으로 깎으면 정면이 %.0f %% 줄고 40 도도 %.0f %% '
        '좋아진다. 아래벽은 0.08 그대로다.</p>\n'
        % (100 * (1 - rim["A 테두리 0.03"]["total"]["0"] / BASE["total"]["0"]),
           100 * (1 - rim["A 테두리 0.03"]["total"]["40"] / BASE["total"]["40"])))
o.write('<p class="tag">0.05 는 사용자가 정한 취급 한계다("너무 얇으면 손으로 '
        '쉽게 찌그러진다"). 0.03 과 0.02 는 그 아래이고, 만들 수 있는지는 '
        '업체에 물어야 한다.</p></section>\n')

# ---- B
o.write('<section><h2>B. 바닥판을 피라미드로</h2>\n')
o.write('<p>정면으로 관을 들여다보면 평평한 판이 보인다. 그 판을 기울어진 '
        '면으로 바꾸면 <b>반짝임이 무너진다.</b></p>\n')
o.write('<div class="scroll"><table><thead><tr><th>바닥</th><th>정면</th>'
        '<th>20도</th><th>40도</th><th>반짝임</th></tr></thead><tbody>\n')
for nm in ("기준", "B 피라미드 바닥 10", "B 피라미드 바닥 15"):
    r = rim[nm]
    pick = ' class="pick"' if r["floor_depth"] == 15.0 else ""
    o.write('<tr%s><td>%s</td><td class="n">%.5f %%</td><td class="n">%.5f %%</td>'
            '<td class="n">%.5f %%</td><td class="n"><b>%.4f</b></td></tr>\n'
            % (pick, "평판" if not r["floor"] else "피라미드 깊이 %.0f"
               % r["floor_depth"], 100 * r["total"]["0"],
               100 * r["total"]["20"], 100 * r["total"]["40"], r["head_on"]))
o.write('</tbody></table></div>\n')
o.write('<p class="lead">반짝임 %.4f → <b>%.4f</b>, %.1f 배.</p>\n'
        % (BASE["head_on"], rim["B 피라미드 바닥 15"]["head_on"],
           BASE["head_on"] / rim["B 피라미드 바닥 15"]["head_on"]))
o.write('<p>만들기도 어렵지 않다. 평판 대신 <b>눌러 찍은 피라미드 판</b>을 '
        '깔고 그 위에 벌집을 붙이는 것뿐이고, 둘 다 이 연구가 이미 쓰는 '
        '공정이다.</p>\n')
o.write('<p>비스듬한 각도는 조금 나빠진다 (20도 %.1f %%, 40도 %.1f %%). '
        '정면과 반짝임에서 얻는 것이 훨씬 크다.</p></section>\n'
        % (100 * (rim["B 피라미드 바닥 15"]["total"]["20"] / BASE["total"]["20"] - 1),
           100 * (rim["B 피라미드 바닥 15"]["total"]["40"] / BASE["total"]["40"] - 1)))

# ---- 합친 것
o.write('<section><h2>둘을 합치면</h2>\n')
o.write('<div class="scroll"><table><thead><tr><th>경우</th><th>정면</th>'
        '<th>20도</th><th>40도</th><th>반짝임</th><th>뭉개기</th>'
        '</tr></thead><tbody>\n')
for nm in ("기준", "A 테두리 0.03", "B 피라미드 바닥 15",
           "AB 0.05 + 피라미드 10", "AB 0.03 + 피라미드 15"):
    r = rim[nm]
    pick = ' class="pick"' if nm.startswith("AB 0.03") else ""
    o.write('<tr%s><td>%s</td><td class="n">%.3f</td><td class="n">%.3f</td>'
            '<td class="n">%.3f</td><td class="n">%.3f</td>'
            '<td class="n">%s</td></tr>\n'
            % (pick, esc(nm), r["total"]["0"] / BASE["total"]["0"],
               r["total"]["20"] / BASE["total"]["20"],
               r["total"]["40"] / BASE["total"]["40"],
               r["head_on"] / BASE["head_on"],
               ("%.4f" % r["smear"]) if r["smear"] is not None else "&middot;"))
o.write('</tbody></table></div>\n')
o.write('<p class="tag">기준을 1 로 놓은 값. 작을수록 어둡다. '
        '뭉개기만 클수록 좋다.</p>\n')
o.write('<div class="card"><h3 style="margin:0">모양 뭉개기가 처음으로 '
        '움직였다</h3>\n')
o.write('<p><b>%.4f → %.4f.</b> 깊이도 셀 크기도 포일 두께도 셀 모양도 '
        '이 축을 못 움직였다. 목표 1.42 에는 아직 못 미치지만 처음으로 '
        '방향이 보인다.</p></div></section>\n' % (sm_a, sm_b))

# ---- 뒤집힌 피라미드
o.write('<section><h2>뒤집힌 피라미드는 우리에게 안 좋다</h2>\n')
o.write('<p>시트를 눌러 피라미드를 만들면 반대면이 그대로 뒤집힌 피라미드다. '
        '<b>같은 부품을 뒤집어 다는 것</b>이라 공정이 안 는다. 태양전지 쪽이 '
        '둘을 비교해 놨고 이유도 우리 계산과 같아 보였다 — 파인 홈에서 빛이 '
        '한두 번 더 튕긴다. 그래서 나을 것이라고 <b>말했다가 재보고 '
        '취소했다.</b></p>\n')
o.write('<div class="scroll"><table><thead><tr><th>간격 4 / 깊이 22</th>'
        '<th>정면</th><th>20도</th><th>40도</th><th>반짝임</th>'
        '<th>모양 뭉개기</th></tr></thead><tbody>\n')
u = inv["선 피라미드 끝0.1"]
for nm, cls in (("선 피라미드 끝0.1", ""), ("뒤집힌 피라미드 끝0.1", ' class="no"'),
                ("선 피라미드 끝0.4", ""), ("뒤집힌 피라미드 끝0.4", ' class="no"')):
    r = inv[nm]
    o.write('<tr%s><td>%s</td><td class="n">%.3f</td><td class="n">%.3f</td>'
            '<td class="n">%.3f</td><td class="n">%.3f</td>'
            '<td class="n"><b>%s</b></td></tr>\n'
            % (cls, esc(nm), r["total"]["0"] / u["total"]["0"],
               r["total"]["20"] / u["total"]["20"],
               r["total"]["40"] / u["total"]["40"],
               r["head_on"] / u["head_on"],
               ("%.4f" % r["smear"]) if r["smear"] is not None else "&middot;"))
o.write('</tbody></table></div>\n')
o.write('<p class="tag">선 피라미드 끝0.1 을 1 로 놓은 값. 뭉개기만 실제 값.</p>\n')
o.write('<p>총량과 반짝임은 사실상 같고 <b>뭉개기가 %.4f 에서 %.4f 로 '
        '무너진다.</b> 목표가 1.42 이니 선 피라미드는 넘고 뒤집힌 것은 못 '
        '넘는다.</p>\n'
        % (u["smear"], inv["뒤집힌 피라미드 끝0.1"]["smear"]))
o.write('<p>이유는 로그에 그대로 있다. 40 도에서 되돌아온 봉우리가 선 '
        '피라미드 0.037, 뒤집힌 것 0.163 — <b>4.4 배</b>다. '
        '<b>파인 홈은 직각으로 만난 두 면이 코너 리플렉터가 되어 빛을 온 '
        '쪽으로 되돌려 보낸다.</b> 솟은 봉우리는 반대로 밖으로 흩는다.</p>\n')
o.write('<p><b>태양전지에서 뒤집힌 쪽이 좋은 이유가 정확히 그것이다</b> — '
        '되돌아온 빛이 실리콘 안으로 다시 들어가 흡수된다. 같은 성질이 '
        '저쪽에선 이득이고 우리한테는 없애야 할 것이다.</p>\n')
o.write('<p>벌집 바닥으로 써도 선 피라미드와 차이가 없다 (정면 %.3f · 40도 '
        '%.3f · 반짝임 %.3f). 관 깊은 곳이라 곧게 온 빛만 닿아서다.</p>\n'
        % (inv["벌집 + 뒤집힌 피라미드 10"]["total"]["0"]
           / inv["벌집 + 선 피라미드 10"]["total"]["0"],
           inv["벌집 + 뒤집힌 피라미드 10"]["total"]["40"]
           / inv["벌집 + 선 피라미드 10"]["total"]["40"],
           inv["벌집 + 뒤집힌 피라미드 10"]["head_on"]
           / inv["벌집 + 선 피라미드 10"]["head_on"]))
o.write('</section>\n')

# ---- 업체에 물을 것
o.write('<section><h2>업체에 물어볼 것</h2><div class="card"><ul>\n')
for q in ("위벽만 0.03 mm 로 얇게 하고 아래벽은 0.08 로 둘 수 있습니까? "
          "강도는 아래벽이 정하고 정면 반사는 위벽이 정합니다.",
          "바닥판을 평판 대신 눌러 찍은 피라미드 판(간격 9.53, 깊이 15)으로 "
          "주실 수 있습니까? 그 위에 벌집을 붙이면 됩니다.",
          "그 두 장을 따로 주시면 우리가 칠해서 조립하겠습니다."):
    o.write('<li>%s</li>\n' % esc(q))
o.write('</ul></div></section>\n')

# ---- 안 잰 것
o.write('<section><h2>안 잰 것</h2><ul>\n')
for x in ("테두리 0.03 mm 를 실제로 만들 수 있는지. 취급 한계 0.05 아래다.",
          "바닥 피라미드의 간격과 깊이를 훑지 않았다. 9.53 / 10 과 15 만 봤다. "
          "뭉개기는 기울어진 면이 만드는 것이니 더 가파르면 더 갈 수 있다.",
          "바닥 피라미드에 <code>apex_jitter</code> 를 주면 셀마다 꼭짓점이 "
          "다른 각도를 가진다. 되돌아오는 방향이 흩어질 것이다 [추측].",
          "뒤집힌 피라미드의 끝 0.4 에서 뭉개기를 안 쟀다. 끝을 키우면 코너가 "
          "무뎌질 텐데 (끝 0.4 가 끝 0.1 보다 정면에서 8 % 나았다) 확인 못 했다.",
          "뭉개기와 반짝임은 위상 6 으로 줄여 잰 추정값이다."):
    o.write('<li>%s</li>\n' % x)
o.write('</ul></section>\n')

o.write('<section><p class="tag">잰 것: '
        '<code>results/comb_depth/rim_and_floor.json</code> · '
        '<code>results/comb_depth/pyramid_inverted.json</code> · '
        '전부 무소(%.3f %%, 확산 %.3f) · 거칠기 α %.3f · 표본 %d · '
        '면 0/45/90도 중 가장 밝은 값. 만든 것: '
        '<code>scripts/sweep_rim_and_floor.py</code>, '
        '<code>scripts/sweep_pyramid_inverted.py</code>. 이 문서: '
        '<code>scripts/build_shape_report.py</code>. 앞선 보고서: '
        '<code>report/comb/paint_depth_2026-08-24.html</code></p></section>\n'
        % (100 * MUSOU["rho"], MUSOU["df"], BASE["alpha"], BASE["samples"]))
o.write('</div></body></html>\n')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, "w", encoding="utf-8").write(o.getvalue())
print("%s  (%d 바이트)" % (OUT, len(o.getvalue())))
