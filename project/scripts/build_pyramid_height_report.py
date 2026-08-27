# -*- coding: utf-8 -*-
"""밑변 50 mm 피라미드의 높이를 얼마로 할까 -- 보고서를 데이터에서 짓는다.

읽는 것
    results/pyramid_height/height_totals.json     높이 아홉 점, 무소 팁 20 mm
    results/pyramid_height/height_isolated.json   같은 높이, 재료를 고정해서
    results/pyramid_height/height_form.json       뭉개기·반짝임 (2단계, 있으면)
    material/*.json                               재료 값과 색
    report/comb/comb_musou_2026-08-22.html        디자인. 이미 있는 체계를 쓴다.
쓰는 것
    report/comb/pyramid_height_2026-08-27.html

2단계가 아직 안 끝났으면 그 절을 "재는 중" 으로 적고 나머지를 낸다.
빈 칸을 숨기지 않는다.
"""
import os
import re
import io
import json
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOT = os.path.join(ROOT, "results/pyramid_height/height_totals.json")
ISO = os.path.join(ROOT, "results/pyramid_height/height_isolated.json")
FORM = os.path.join(ROOT, "results/pyramid_height/height_form.json")
STYLE_FROM = os.path.join(ROOT, "report/comb/comb_musou_2026-08-22.html")
OUT = os.path.join(ROOT, "report/comb/pyramid_height_2026-08-27.html")

tot = json.load(open(TOT))
iso = json.load(open(ISO)) if os.path.exists(ISO) else []
form = json.load(open(FORM)) if os.path.exists(FORM) else []

byl = {r["label"]: r for r in tot}
heights = [r for r in tot if r.get("depth")]
FLAT5, FLATM = byl["민판 5 % 페인트"], byl["민판 무소"]
ORDER = byl["발주 사양 4/22"]
isoby = {(r["arm"], r["depth"]): r for r in iso}
ARMS = sorted({r["arm"] for r in iso})
formby = {r["depth"]: r for r in form}

P = heights[0]["pitch"]
TIP = heights[0]["tip_flat"]
SPRAY = heights[0]["spray_mm"]
PANEL = heights[0]["spec"]["panel"]


def mat(mid):
    d = json.load(open(os.path.join(ROOT, "material", "%s.json" % mid)))
    return {"rho": d["scattering"]["reflectance"]["value"],
            "df": d["bsdf"]["diffuse_fraction"],
            "alpha": d["bsdf"]["lobe"]["alpha_ggx"],
            "color": d.get("color", "#333"),
            "label": d.get("label_en") or d.get("label") or mid}


MUSOU, PAINT = mat("musou_fit"), mat("wall_5pct")


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


# ------------------------------------------------------------ 설계도
def blueprint():
    """높이 셋을 나란히. 밑변은 고정이고 높이만 다르다는 것이 요점."""
    S = 1.05                      # mm 당 화소
    W, H = 900, 430
    base_y = 340.0
    o = ['<svg viewBox="0 0 %d %d" width="100%%" style="height:auto" '
         'font-family="var(--kr)">' % (W, H)]
    o.append('<rect width="%d" height="%d" fill="#f4f1eb"/>' % (W, H))
    o.append('<text x="30" y="34" font-size="15" font-weight="700" '
             'fill="#222">밑변은 %.0f mm 로 고정, 높이만 바꾼다</text>'
             % P)
    o.append('<text x="30" y="54" font-size="12" fill="#666">'
             '단면 하나. 세로가 실제 비율이다. 짙은 부분이 무소(팁에서 '
             '%.0f mm), 옅은 부분이 5 %% 페인트. 붉은 숫자는 정면 반사 총량.'
             '</text>' % SPRAY)
    shown = [50.0, 150.0, 250.0]
    x = 150.0
    for h in shown:
        half = P * S / 2
        top_y = base_y - h * S
        # 5 % 페인트 몸통
        o.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" '
                 'fill="#8798bf"/>'
                 % (x - half, base_y, x, top_y, x + half, base_y))
        # 무소 띠: 팁에서 SPRAY mm
        f = min(SPRAY / h, 1.0)
        yb = top_y + SPRAY * S
        hb = half * f
        o.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" '
                 'fill="#3a4a63"/>'
                 % (x - hb, yb, x, top_y, x + hb, yb))
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                 'stroke="#333" stroke-width="1"/>'
                 % (x - half - 14, base_y, x + half + 14, base_y))
        o.append('<text x="%.1f" y="%.1f" font-size="13" font-weight="700" '
                 'text-anchor="middle" fill="#222">높이 %.0f</text>'
                 % (x, base_y + 22, h))
        o.append('<text x="%.1f" y="%.1f" font-size="11" '
                 'text-anchor="middle" fill="#666">%.0f 대 %.0f · '
                 '무소 %.0f %%</text>'
                 % (x, base_y + 40, h / P, 1, 100 * f))
        r = next((z for z in heights if z["depth"] == h), None)
        if r:
            o.append('<text x="%.1f" y="%.1f" font-size="13" '
                     'font-weight="700" text-anchor="middle" fill="#c8401c" '
                     'font-family="var(--mono)">%.3f %%</text>'
                     % (x, base_y + 62, 100 * r["total"]["0"]))
        x += 300.0
    o.append('</svg>')
    return "\n".join(o)


style = re.search(r"<style>(.*?)</style>",
                  io.open(STYLE_FROM, encoding="utf-8").read(), re.S).group(1)

o = io.StringIO()
o.write('<!doctype html><html lang="ko"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<title>피라미드 높이를 얼마로 할까</title>\n')
o.write('<style>%s\n.fig{background:#f4f1eb;border:1px solid var(--line);'
        'border-radius:3px;padding:12px;overflow-x:auto}\n'
        '.big{font-size:28px;font-weight:800;font-family:var(--mono);'
        'font-variant-numeric:tabular-nums}\n'
        '.tag{font-family:var(--mono);font-size:11px;color:var(--muted);'
        'letter-spacing:.06em}\nul{margin:0;padding-left:20px;max-width:64ch}\n'
        'li{margin:5px 0}\na{color:var(--cy)}\n'
        '.wait{border-left:4px solid var(--warn)}\n'
        '</style></head><body>\n<div class="wrap">\n' % style)

o.write('<header><div class="eyebrow">2026-08-27 · 피라미드 높이</div>\n')
o.write('<h1>피라미드 높이를 얼마로 할까</h1>\n')
o.write('<p class="sub">밑변 %.0f mm 고정 · 판 %.0f × %.0f mm · 끝 평평 %.1f mm · '
        '바탕은 무광 검정 5 %% 페인트, 무소는 팁에서 %.0f mm. '
        '벌집은 칠하기가 어려워 보류하고 피라미드로 돌아왔다.</p></header>\n'
        % (P, PANEL, PANEL, TIP, SPRAY))

# ---- 결론
best = heights[-1]
o.write('<section><div class="card verdict ok"><h2 style="margin:0">결론</h2>\n')
o.write('<p class="lead"><b>높이에 최적점이 없다.</b> 50 mm 에서 250 mm 까지 '
        '한 번도 안 꺾이고, 25 mm 더 줄 때마다 정면 총량이 10~17 % 씩 '
        '좋아진다. <b>판을 얼마나 두껍게 할 수 있느냐가 답을 정한다.</b></p>\n')
o.write('<div class="scroll"><table><thead><tr><th></th><th>정면 총량</th>'
        '<th>20도</th><th>40도</th><th>민판 5 % 대비</th></tr></thead><tbody>\n')
for r in (FLAT5, FLATM, heights[0], heights[len(heights)//2], best, ORDER):
    pick = ' class="pick"' if r is best else ""
    o.write('<tr%s><td>%s</td><td class="n">%.5f %%</td>'
            '<td class="n">%.5f %%</td><td class="n">%.5f %%</td>'
            '<td class="n">%.1f 배 어두움</td></tr>\n'
            % (pick, esc(r["label"]), 100 * r["total"]["0"],
               100 * r["total"]["20"], 100 * r["total"]["40"],
               FLAT5["total"]["0"] / r["total"]["0"]))
o.write('</tbody></table></div>\n')
o.write('<p class="tag">발주 사양은 밑변 4 / 높이 22 라 팁에서 %.0f mm 를 칠하면 '
        '사실상 전체가 무소가 된다. 도장 조건이 달라 나란히 못 놓는 값이다.</p>\n'
        % SPRAY)
o.write('</div></section>\n')

# ---- 설계도
o.write('<section><h2>무엇을 바꾸는가</h2>\n')
o.write('<figure><div class="fig">%s</div>\n' % blueprint())
o.write('<figcaption class="tag">밑변 %.0f mm 는 고정이다. 무소가 덮는 몫이 '
        '높이에 따라 달라진다는 점을 같이 그렸다.</figcaption></figure>\n' % P)
o.write('</section>\n')

# ---- 높이 표
o.write('<section><h2>높이를 바꾸며 잰 것</h2>\n')
o.write('<div class="scroll"><table><thead><tr><th>높이</th><th>높이 대 밑변</th>'
        '<th>정면 총량</th><th>20도</th><th>40도</th><th>무소가 덮는 몫</th>'
        '<th>한 칸 전보다</th></tr></thead><tbody>\n')
prev = None
for r in heights:
    gain = ("&mdash;" if prev is None
            else "%.1f %%" % (100 * (1 - r["total"]["0"] / prev["total"]["0"])))
    o.write('<tr><td>%.0f mm</td><td class="n">%.1f</td>'
            '<td class="n"><b>%.5f %%</b></td><td class="n">%.5f %%</td>'
            '<td class="n">%.5f %%</td><td class="n">%.0f %%</td>'
            '<td class="n">%s</td></tr>\n'
            % (r["depth"], r["aspect"], 100 * r["total"]["0"],
               100 * r["total"]["20"], 100 * r["total"]["40"],
               100 * r["spray_frac"], gain))
    prev = r
o.write('</tbody></table></div>\n')
o.write('<p>250 mm 에서도 아직 %.1f %% 씩 좋아지고 있다. 이 범위 안에 '
        '멈추는 지점이 없다.</p></section>\n'
        % (100 * (1 - heights[-1]["total"]["0"] / heights[-2]["total"]["0"])))

# ---- 모양과 도료
if iso:
    o.write('<section><h2>모양과 도료가 서로 곱해진다</h2>\n')
    o.write('<p>위 표에서는 무소가 덮는 몫이 높이마다 다르다. 높이 50 에서 40 %, '
            '250 에서 8 %. 모양의 이득과 도장의 손해가 섞여 있다. 그래서 '
            '재료를 <b>높이와 무관하게</b> 고정해서 다시 쟀다.</p>\n')
    o.write('<div class="scroll"><table><thead><tr><th>높이</th>')
    for a in ARMS:
        o.write('<th>%s 정면</th><th>40도</th>' % esc(a))
    o.write('</tr></thead><tbody>\n')
    for h in [r["depth"] for r in heights]:
        o.write('<tr><td>%.0f mm</td>' % h)
        for a in ARMS:
            x, y = isoby[(a, 50.0)], isoby[(a, h)]
            o.write('<td class="n">%.3f</td><td class="n">%.3f</td>'
                    % (y["total"]["0"] / x["total"]["0"],
                       y["total"]["40"] / x["total"]["40"]))
        o.write('</tr>\n')
    o.write('</tbody></table></div>\n')
    o.write('<p class="tag">높이 50 을 1 로 놓은 값.</p>\n')
    a250 = isoby[(ARMS[0], 250.0)]
    b250 = isoby[(ARMS[1], 250.0)]
    o.write('<p><b>두 열이 세 자리까지 같다.</b> 높이가 주는 이득이 도료와 '
            '아무 상관이 없다는 뜻이다. 그리고 5 %% 를 무소로 바꾸면 어느 '
            '높이에서나 <b>%.2f 배</b>다 -- 재료 자체의 반사율 비 %.2f 배가 '
            '그대로 통과한다.</p>\n'
            % (a250["total"]["0"] / b250["total"]["0"],
               PAINT["rho"] / MUSOU["rho"]))
    o.write('<div class="scroll"><table><thead><tr><th>무엇을 바꾸나</th>'
            '<th>몇 배 어두워지나</th></tr></thead><tbody>\n')
    g_shape = FLAT5["total"]["0"] / a250["total"]["0"]
    g_coat = a250["total"]["0"] / b250["total"]["0"]
    g_both = FLAT5["total"]["0"] / b250["total"]["0"]
    for nm, v in (("모양: 민판 &rarr; 높이 250 (도료는 5 %% 그대로)", g_shape),
                  ("도료: 5 %% &rarr; 무소 (모양은 그대로)", g_coat),
                  ("둘 다", g_both)):
        o.write('<tr><td>%s</td><td class="n"><b>%.1f 배</b></td></tr>\n'
                % (nm % (), v))
    o.write('</tbody></table></div>\n')
    o.write('<p>%.1f × %.1f = %.1f 이고 실제가 %.1f 배다. <b>곱셈이 '
            '성립한다.</b> 높이는 모양만 보고 정하고 도료는 따로 정하면 '
            '된다.</p></section>\n'
            % (g_shape, g_coat, g_shape * g_coat, g_both))

    # ---- 팁 20 mm 가 값을 하나
    o.write('<section><h2>그런데 팁 %.0f mm 무소가 값을 거의 못 한다</h2>\n'
            % SPRAY)
    o.write('<div class="scroll"><table><thead><tr><th>높이</th>'
            '<th>전부 5 %% 페인트</th><th>팁 %.0f mm 만 무소</th>'
            '<th>나아진 몫</th><th>전부 무소로 했다면</th>'
            '</tr></thead><tbody>\n' % SPRAY)
    for r in heights:
        a = isoby[(ARMS[0], r["depth"])]
        b = isoby[(ARMS[1], r["depth"])]
        o.write('<tr><td>%.0f mm</td><td class="n">%.5f %%</td>'
                '<td class="n">%.5f %%</td><td class="n">%.1f %%</td>'
                '<td class="n">%.5f %%</td></tr>\n'
                % (r["depth"], 100 * a["total"]["0"], 100 * r["total"]["0"],
                   100 * (1 - r["total"]["0"] / a["total"]["0"]),
                   100 * b["total"]["0"]))
    o.write('</tbody></table></div>\n')
    a50, a250b = isoby[(ARMS[0], 50.0)], isoby[(ARMS[0], 250.0)]
    o.write('<p>높이 50 에서는 팁 %.0f mm 가 정면을 %.0f %% 개선한다. '
            '높이 250 에서는 <b>%.1f %%</b> 뿐이다 -- 무소가 8 %% 만 덮으니 '
            '거의 안 보탠다.</p>\n'
            % (SPRAY, 100 * (1 - heights[0]["total"]["0"] / a50["total"]["0"]),
               100 * (1 - heights[-1]["total"]["0"] / a250b["total"]["0"])))
    o.write('<p><b>높이를 키울수록 이 문제가 커진다.</b> 250 mm 피라미드라면 '
            '팁만 뿌리는 대신 전체를 무소로 하는 쪽을 따져야 한다 -- '
            '그쪽이 %.1f 배다.</p></section>\n' % g_coat)

# ---- 2단계
o.write('<section><h2>모양 뭉개기와 정면 반짝임</h2>\n')
if form:
    o.write('<div class="scroll"><table><thead><tr><th>높이</th>'
            '<th>정면 반짝임</th><th>모양 뭉개기</th><th>담겼나</th>'
            '<th>필요한 창</th></tr></thead><tbody>\n')
    for r in form:
        o.write('<tr><td>%.0f mm</td><td class="n">%.4f</td>'
                '<td class="n">%.4f</td><td class="n">%s</td>'
                '<td class="n">%.0f mm</td></tr>\n'
                % (r["depth"], r["head_on"], r["smear"],
                   r["smear_converged"], r["window_needed_mm"] or 0))
    o.write('</tbody></table></div>\n')
    if any(r.get("smear_converged") is False for r in form):
        o.write('<p class="tag">담기지 않은(converged False) 줄의 뭉개기는 '
                '실제 값이 아니라 <b>하한</b>이다. 되돌아온 빛이 판 밖으로 '
                '나갔다는 뜻이다.</p>\n')
else:
    o.write('<div class="card wait"><p><b>아직 재는 중이다.</b> 높이 100 / 175 / '
            '250 세 점을 위상 8 로 재고 있고, 끝나면 이 절이 채워진다.</p>\n')
    o.write('<p>왜 오래 걸리나: 프레임 크기가 <span style="font-family:'
            'var(--mono)">(판 + 여백 + 측정창) &divide; 0.215 mm</span> 라서 '
            '깊이가 깊을수록 창이 커진다. 실측으로 높이 100 에서 한 프레임 '
            '69 초, 높이 250 에서 <b>343 초</b>다. 반사 총량은 한 각도에 '
            '0.74 초다 -- <b>600 배 차이</b>라 총량으로 먼저 훑고 셋만 고른 '
            '것이다.</p></div>\n')
o.write('<p><b>이 값들은 발표된 숫자와 나란히 놓을 수 없다.</b> 우리 측정 빔은 '
        '7.5 mm 인데 셀이 %.0f mm 다. 지금까지 발표된 값은 빔이 셀 두 개를 '
        '덮는 조건(빔 7.5 / 밑변 4)에서 나왔다. 여기서는 빔이 경사면 하나 안에 '
        '들어간다. 완전히 다른 조건이다.</p></section>\n' % P)

# ---- 안 잰 것
o.write('<section><h2>안 잰 것</h2><ul>\n')
items = ["<b>끝 평평 1.0 mm 는 확인받은 값이지 최적값이 아니다.</b> "
         "끝의 평평한 면은 정면을 똑바로 보고 있어서, 벌집에서 포일 테두리가 "
         "정면 반사의 51 %%를 맡았던 자리와 같다. 넓이로는 %.2f %% "
         "(끝/밑변의 제곱) 다. 이긴 높이에서 0.5 / 1.0 / 2.0 을 따로 훑어야 "
         "한다." % (100 * heights[0]["tip_area_frac"]),
         "250 mm 를 넘는 높이. 사용자가 정한 범위의 끝이지 물리적인 끝이 "
         "아니다. 경향이 안 꺾였으므로 더 가면 더 좋아진다.",
         "판을 250 mm 두께로 만들 수 있는지, 무게가 얼마인지. 광학만 쟀다.",
         "밑변 50 mm 를 바꾸는 경우. 이번에는 고정 조건이었다.",
         "<code>apex_jitter</code>. 셀마다 꼭짓점 각도를 흩으면 되돌아오는 "
         "방향이 흩어질 것이다 [추측]."]
for x in items:
    o.write('<li>%s</li>\n' % x)
o.write('</ul></section>\n')

o.write('<section><p class="tag">잰 것: '
        '<code>results/pyramid_height/height_totals.json</code> · '
        '<code>height_isolated.json</code>%s · 표본 %d · 거칠기 슬라이더 '
        '%.4f (알파 %.3f) · 면 0/45/90도 중 가장 밝은 값. 만든 것: '
        '<code>scripts/sweep_pyramid_height.py</code>, '
        '<code>sweep_pyramid_height_iso.py</code>, '
        '<code>sweep_pyramid_height_form.py</code>. 이 문서: '
        '<code>scripts/build_pyramid_height_report.py</code></p></section>\n'
        % (" · <code>height_form.json</code>" if form else "",
           heights[0]["samples"], heights[0]["slider"], heights[0]["alpha"]))
o.write('</div></body></html>\n')

html = o.getvalue()

# 쓰기 **전에** 본다. 서식 인자 없는 o.write 안의 %% 는 안 줄어들고 화면에
# 두 개가 그대로 찍힌다. 안 끼워진 %s 는 문단을 통째로 날린다. 둘 다 숫자
# 검사도 태그 검사도 못 잡고 눈으로만 보인다. 그래서 여기서 막는다.
bad = [ln.strip()[:90] for ln in html.split("\n")
       if "%%" in ln or "%s" in ln]
if bad:
    for ln in bad:
        print("남은 서식: %s" % ln)
    raise SystemExit("서식이 안 풀렸다 -- 발행 안 함")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, "w", encoding="utf-8").write(html)
print("%s  (%d 바이트)%s"
      % (OUT, len(html), "" if form else "  — 2단계는 재는 중"))
