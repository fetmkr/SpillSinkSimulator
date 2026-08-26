# -*- coding: utf-8 -*-
"""벌집 안쪽을 어디까지 칠해야 하나 -- 보고서를 데이터에서 짓는다.

읽는 것
    results/paint_depth/paint_depth_9p53_40.json   오늘 잰 열두 점
    results/comb_musou/comb_musou_v2.json          32가지 연구 (같은 설정인지 대조)
    figures/comb_headon_vs_oblique.svg             빛이 어떻게 다니는지 그린 것
    material/*.json                                재료 값과 색
    report/comb/comb_musou_2026-08-22.html         디자인. 이미 있는 체계를 쓴다.
쓰는 것
    report/comb/paint_depth_2026-08-24.html

손으로 안 짓는다. 재료 값이 또 정정되면 이 스크립트를 다시 돌리면 된다.
"""
import os
import re
import json
import glob
import math
import io

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "results/paint_depth/paint_depth_9p53_40.json")
DEPTHF = os.path.join(ROOT, "results/comb_depth/comb_depth_pick.json")
FOILF = os.path.join(ROOT, "results/comb_depth/comb_foil.json")
V2 = os.path.join(ROOT, "results/comb_musou/comb_musou_v2.json")
FIG = os.path.join(ROOT, "figures/comb_headon_vs_oblique.svg")
STYLE_FROM = os.path.join(ROOT, "report/comb/comb_musou_2026-08-22.html")
OUT = os.path.join(ROOT, "report/comb/paint_depth_2026-08-24.html")

rows = json.load(open(SRC))
by_d = {r["paint_depth"]: r for r in rows}
r0 = rows[0]
P, D, T = r0["pitch"], r0["depth"], r0["foil"]


def materials():
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "material", "*.json"))):
        b = os.path.basename(f)[:-5]
        if b.startswith("_"):
            continue
        d = json.load(open(f))
        # 확산 비율과 로브는 scattering 이 아니라 bsdf 아래에 있다.
        # 처음에 scattering 밑에서 찾다가 None 을 곱해서 죽었다.
        bsdf = d.get("bsdf", {}) or {}
        out[b] = {"color": d.get("color", "#3a3f47"),
                  "label": d.get("label_en") or d.get("label") or b,
                  "rho": (d.get("scattering", {}).get("reflectance", {})
                          .get("value")),
                  "df": bsdf.get("diffuse_fraction"),
                  "alpha": (bsdf.get("lobe", {}) or {}).get("alpha_ggx")}
    return out


MAT = materials()
RHO_BASE = (MAT.get(r0["base"], {}) or {}).get("rho")
RHO_TOP = (MAT.get(r0["top"], {}) or {}).get("rho")

# ---- 손계산. 렌더와 따로, 종이 위에서 같은 답이 나오는지 본다. -------------
# 펼쳐 만든 벌집은 여섯 벽 중 셋이 포일 두 겹(붙인 자리)이라 3t/p 다.
F_RIM = 3.0 * T / P
F_OPEN = 1.0 - F_RIM
HALF0 = math.degrees(math.atan((P / 2.0) / D))
ESC0 = math.sin(math.radians(HALF0)) ** 2
D40 = (P / 2.0) / math.tan(math.radians(40.0))
HALF40 = math.degrees(math.atan((P / 2.0) / D40))
ESC40 = math.sin(math.radians(HALF40)) ** 2


def hand(rho):
    return F_RIM * rho + F_OPEN * rho * ESC0


# ---- 정면 반사를 세 조각으로 나눈다 ---------------------------------------
t_none = by_d[0.0]["total"]["0"]
t_rim = by_d[1.0]["total"]["0"]     # 테두리만 좋은 검정
t_wall = by_d[20.0]["total"]["0"]   # 벽까지 20 mm
t_all = by_d[40.0]["total"]["0"]    # 바닥판까지
span = t_none - t_all
PARTS = [("포일 테두리", t_none - t_rim, "판 겉면이다. 뿌리면 닿는다."),
         ("셀 벽 1~20 mm", t_rim - t_wall, "칠해도 정면은 안 바뀐다."),
         ("바닥판", t_wall - t_all, "평평한 판이다. 붙이기 전에 칠하면 된다.")]

FLASH_FLOOR = by_d[10.0]["head_on"] / by_d[40.0]["head_on"]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


style = re.search(r"<style>(.*?)</style>",
                  io.open(STYLE_FROM, encoding="utf-8").read(), re.S).group(1)
fig = io.open(FIG, encoding="utf-8").read()
fig = re.sub(r'^<\?xml[^>]*\?>\s*', '', fig)
fig = fig.replace('width="1080" height="640"',
                  'width="100%" style="max-width:1080px;height:auto"', 1)

o = io.StringIO()
o.write('<!doctype html><html lang="ko"><head><meta charset="utf-8">\n')
o.write('<meta name="viewport" content="width=device-width,initial-scale=1">\n')
o.write('<title>벌집 안쪽을 어디까지 칠해야 하나</title>\n')
o.write('<style>%s\n.fig{background:#f4f1eb;border:1px solid var(--line);'
        'border-radius:3px;padding:10px;overflow-x:auto}\n'
        '.big{font-size:30px;font-weight:800;font-family:var(--mono);'
        'font-variant-numeric:tabular-nums}\n'
        '.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));'
        'gap:12px}\n.tag{font-family:var(--mono);font-size:11px;color:var(--muted);'
        'letter-spacing:.06em}\nul{margin:0;padding-left:20px;max-width:64ch}\n'
        'li{margin:4px 0}\na{color:var(--cy)}\n</style></head><body>\n'
        % style)
o.write('<div class="wrap">\n')

o.write('<header><div class="eyebrow">2026-08-24 · 코팅 깊이</div>\n')
o.write('<h1>벌집 안쪽을 어디까지 칠해야 하나</h1>\n')
o.write('<p class="sub">셀 %.2f mm · 깊이 %.0f mm · 포일 %.2f mm. '
        '중국 업체가 "안쪽까지 검게 못 칠한다, 아노다이징도 안 된다"고 답한 '
        '바로 그 벌집이다.</p></header>\n' % (P, D, T))

# ---------------- 결론 ----------------
o.write('<section><div class="card verdict ok">\n')
o.write('<h2 style="margin:0">결론</h2>\n')
o.write('<p class="lead"><b>관 안쪽 깊은 데는 칠할 필요가 없다.</b> '
        '정면으로 오는 빛에 대해서는 <b>포일 테두리</b>와 <b>바닥판</b>이 거의 전부를 '
        '정하고, 둘 다 평평하게 드러난 면이다. 셀 벽은 비스듬한 빛만 쓰는데 '
        '위에서 15 mm 면 끝난다.</p>\n')
o.write('<div class="grid3">\n')
for name, val, note in PARTS:
    # 소수 한 자리로 쓴다. 벽은 0.35 % 인데 반올림해서 "0 %" 로 찍으면
    # 딱 0 이라는 말이 되고, 그건 잰 값이 아니다.
    o.write('<div><div class="tag">%s</div><div class="big">%.1f %%</div>'
            '<div style="font-size:13px;color:var(--muted)">%s</div></div>\n'
            % (esc(name), 100.0 * val / span, esc(note)))
o.write('</div>\n')
o.write('<p style="font-size:14px;color:var(--muted)">정면 반사가 %.3f %% 에서 '
        '%.3f %% 로 내려가는 몫을 셋으로 나눈 것이다.</p>\n'
        % (100 * t_none, 100 * t_all))
o.write('</div></section>\n')

# ---------------- 왜 정면이 어두운가 ----------------
o.write('<section><h2>벌집 관은 한쪽으로만 열린 덫이다</h2>\n')
o.write('<p>표에서 제일 이상한 것은 <b>정면이 비스듬한 빛보다 5배 어둡다</b>는 '
        '점이다. 이유는 나가는 길에 있다.</p>\n')
o.write('<figure><div class="fig">%s</div>\n' % fig)
o.write('<figcaption class="tag">각도는 실제 각도로 그렸다. '
        '포일은 실제 %.2f mm 인데 보이라고 굵게 그렸다.</figcaption></figure>\n' % T)
o.write('<p>정면으로 온 빛은 벽을 한 번도 안 스치고 바닥까지 간다. 문제는 '
        '나올 때다. 깊이 %.0f mm 바닥에서 출구는 반각 %.1f 도밖에 안 되고, '
        '흩어진 빛 중 <b>%.1f %%</b> 만 곧장 빠져나간다. 나머지는 벽에 부딪히고 '
        '부딪힐 때마다 대부분을 잃는다.</p>\n' % (D, HALF0, 100 * ESC0))
o.write('<p>비스듬한 빛(40도)은 깊이 <b>%.1f mm</b> 에서 벌써 벽에 닿는다. '
        '바닥까지 안 간다. 그 얕은 자리에서는 출구가 반각 %.0f 도로 열려 있어 '
        '<b>%.0f %%</b> 가 그냥 나간다. 정면의 %.0f 배다.</p>\n'
        % (D40, HALF40, 100 * ESC40, ESC40 / ESC0))
o.write('</section>\n')

# ---------------- 손계산 대조 ----------------
o.write('<section><h3>렌더 말고 손으로 따로 계산해 봤다</h3>\n')
o.write('<p>정면 반사 = 포일 테두리(넓이 %.2f %%) + 바닥에서 빠져나온 몫. '
        '블렌더와 아무 상관 없는 종이 계산이다.</p>\n' % (100 * F_RIM))
o.write('<div class="scroll"><table><thead><tr><th>관 안쪽 도료</th>'
        '<th>테두리</th><th>바닥 탈출</th><th>손계산 합</th><th>렌더</th>'
        '<th>차이</th></tr></thead><tbody>\n')
for label, rho, meas in (("5 %% 무광 검정", RHO_BASE, t_none),
                         ("무소 1 %%", RHO_TOP, t_all)):
    a, b = F_RIM * rho, F_OPEN * rho * ESC0
    s = a + b
    o.write('<tr><td>%s</td><td class="n">%.5f %%</td><td class="n">%.5f %%</td>'
            '<td class="n"><b>%.5f %%</b></td><td class="n">%.5f %%</td>'
            '<td class="n">%.1f %%</td></tr>\n'
            % (label % (), 100 * a, 100 * b, 100 * s, 100 * meas,
               100 * abs(meas - s) / meas))
o.write('</tbody></table></div>\n')
# 서식을 안 쓰는 줄이라 %% 를 그대로 쓰면 화면에 %% 로 찍힌다. 실제로 찍혔다.
o.write('<p>2 % 와 6 % 안에서 맞는다. 렌더가 맞다는 뜻이고, 위 설명이 '
        '이야기가 아니라 계산이라는 뜻이다.</p></section>\n')

# ---------------- 측정 표 ----------------
o.write('<section><h2>좋은 검정을 위에서부터 N mm 넣었을 때</h2>\n')
o.write('<p>바탕은 5 % 무광 검정. 그 위에 무소(1 %)를 위에서부터 N mm 만 '
        '얹는다. 세 축을 다 적는다 &mdash; 하나만 보면 나머지 둘의 문제를 '
        '숨기게 된다.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>N mm</th>'
        '<th>반사 총량 정면</th><th>총량 20도</th><th>총량 40도</th>'
        '<th>모양 뭉개기</th><th>정면 반짝임</th></tr></thead><tbody>\n')
for r in rows:
    d = r["paint_depth"]
    pick = ' class="pick"' if d == 15.0 else ""
    o.write('<tr%s><td>%.0f</td><td class="n">%.5f %%</td>'
            '<td class="n">%.5f %%</td><td class="n">%.5f %%</td>'
            '<td class="n">%s</td><td class="n">%s</td></tr>\n'
            % (pick, d, 100 * r["total"]["0"], 100 * r["total"]["20"],
               100 * r["total"]["40"],
               ("%.4f" % r["smear"]) if r["smear"] is not None else "&middot;",
               ("%.4f" % r["head_on"]) if r["head_on"] is not None else "&middot;"))
o.write('</tbody></table></div>\n')
o.write('<p class="tag">초록 줄은 40도 총량이 멈추는 지점이다. '
        'N = %.0f 은 판 전체가 무소인 경우이고, 바닥판까지 포함한다.</p>\n' % D)
o.write('<ul>\n')
o.write('<li><b>정면 총량</b>은 1 mm 에서 %.5f %% 로 떨어지고, 거기서 20 mm 까지 '
        '더 칠해도 %.5f %% 다. 사실상 안 움직인다.</li>\n'
        % (100 * t_rim, 100 * t_wall))
o.write('<li><b>40도 총량</b>은 15 mm 에서 %.5f %%, 20 mm 에서 %.5f %%, '
        '40 mm 에서 %.5f %%. <b>15 mm 에서 끝난다.</b></li>\n'
        % (100 * by_d[15.0]["total"]["40"], 100 * by_d[20.0]["total"]["40"],
           100 * by_d[40.0]["total"]["40"]))
o.write('<li><b>모양 뭉개기</b>는 %.4f 에서 %.4f 사이. 깊이를 바꿔도 안 움직인다. '
        '뭉개기는 모양이 정하는 것이라 도료 깊이와 상관이 없다.</li>\n'
        % (min(r["smear"] for r in rows if r["smear"]),
           max(r["smear"] for r in rows if r["smear"])))
o.write('<li><b>정면 반짝임</b>은 2 mm 에서 %.4f 로 내려간 뒤 10 mm 까지 그대로다. '
        '그러다 바닥판까지 무소로 칠하면 <b>%.4f</b> 로 떨어진다 &mdash; '
        '%.1f 배다.</li>\n'
        % (by_d[2.0]["head_on"], by_d[40.0]["head_on"], FLASH_FLOOR))
o.write('</ul>\n')
o.write('<p>반짝임이 바닥판에서 그렇게 움직이는 이유는 광택이 아니다. '
        '두 재료는 확산 비율(%.3f 대 %.2f)과 거칠기가 사실상 같다. '
        '무소가 다섯 배 어두운 것이 그대로 나온 것이다.</p>\n'
        % (MAT[r0["top"]]["df"], MAT[r0["base"]]["df"]))
o.write('</section>\n')

# ---------------- 그래서 깊이와 셀과 포일을 몇으로 ----------------
# 32가지 연구의 깊이 비교는 바탕이 전부 5 % 도료인 경우다. 바닥판을 따로
# 칠할 수 있다는 것을 알고 나면 답이 바뀌므로 두 경우를 나란히 잰다.
DR = json.load(open(DEPTHF))
FR = json.load(open(FOILF))
dby = {(r["pitch"], r["depth"], r["arm"]): r for r in DR}
fby = {(r["foil"], r["arm"]): r for r in FR}
DEPTHS = sorted({r["depth"] for r in DR})
FOILS = sorted({r["foil"] for r in FR})
PICK_P, PICK_D, PICK_F = 9.53, 40.0, 0.04
NOW_F = 0.08


def axes(r):
    return (100 * r["total"]["0"], 100 * r["total"]["20"],
            100 * r["total"]["40"], r["smear"], r["head_on"])


o.write('<section><h2>그래서 깊이는 몇으로</h2>\n')
o.write('<p>아래는 셀 9.53 mm 에서 깊이만 바꾼 것이다. '
        '<b>A</b> 는 바닥판을 못 칠한 경우(위에서 15 mm 만 무소), '
        '<b>B</b> 는 바닥판까지 칠한 경우다.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>깊이</th>'
        '<th>정면 A</th><th>정면 B</th><th>20도 B</th><th>40도 B</th>'
        '<th>뭉개기 B</th><th>반짝임 B</th></tr></thead><tbody>\n')
for d in DEPTHS:
    a, b = dby[(9.53, d, "A")], dby[(9.53, d, "B")]
    pick = ' class="pick"' if d == PICK_D else ""
    o.write('<tr%s><td>%.0f mm</td><td class="n">%.5f %%</td>'
            '<td class="n"><b>%.5f %%</b></td><td class="n">%.5f %%</td>'
            '<td class="n">%.5f %%</td><td class="n">%s</td>'
            '<td class="n">%.4f</td></tr>\n'
            % (pick, d, 100 * a["total"]["0"], 100 * b["total"]["0"],
               100 * b["total"]["20"], 100 * b["total"]["40"],
               ("%.4f" % b["smear"]) if b["smear"] is not None else "&middot;",
               b["head_on"]))
o.write('</tbody></table></div>\n')
d20, d40, d60 = (dby[(9.53, x, "B")] for x in (20.0, 40.0, 60.0))
gain = (100 * (d20["total"]["0"] - d40["total"]["0"])
        / (d20["total"]["0"] - d60["total"]["0"]))
o.write('<ul>\n')
o.write('<li><b>40도 총량은 깊이와 상관이 없다.</b> 20 mm 에서 %.5f %%, '
        '60 mm 에서 %.5f %%. 그런데 이 값이 정면보다 다섯 배 크다. '
        '판 전체의 어두움은 깊이가 안 정한다.</li>\n'
        % (100 * d20["total"]["40"], 100 * d60["total"]["40"]))
o.write('<li><b>정면만 깊이가 산다.</b> 20 에서 60 까지 얻는 몫 중 '
        '<b>%.0f %% 를 40 mm 에서 이미 얻는다.</b> 40 을 넘기면 판만 '
        '두꺼워진다.</li>\n' % gain)
o.write('<li><b>반짝임은 완전히 무관하다.</b> 어느 깊이든 %.4f 다.</li>\n'
        % d40["head_on"])
o.write('<li><b>뭉개기도 깊이와 무관하다.</b> %.4f 에서 %.4f 사이인데 '
        '차례대로 늘거나 줄지 않는다. 재는 흔들림이지 경향이 아니다.</li>\n'
        % (min(dby[(9.53, d, "B")]["smear"] for d in DEPTHS
               if dby[(9.53, d, "B")]["smear"]),
           max(dby[(9.53, d, "B")]["smear"] for d in DEPTHS
               if dby[(9.53, d, "B")]["smear"])))
o.write('</ul>\n')

o.write('<h3>셀 크기 &mdash; 순위가 뒤집힌다</h3>\n')
o.write('<p>바닥판을 칠하고 나면 남는 것이 거의 포일 테두리뿐이고, '
        '테두리 넓이는 <span style="font-family:var(--mono)">3 &times; '
        '포일두께 &divide; 셀간격</span> 이라 셀이 크면 작아진다. '
        '그래서 바닥판을 칠하기 전과 후에 답이 달라진다.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>깊이 40 mm</th>'
        '<th>6.35 mm 셀</th><th>9.53 mm 셀</th><th>이기는 쪽</th>'
        '</tr></thead><tbody>\n')
for arm, name in (("A", "바닥판 못 칠함 &mdash; 정면"),
                  ("B", "바닥판까지 칠함 &mdash; 정면")):
    x, y = dby[(6.35, 40.0, arm)], dby[(9.53, 40.0, arm)]
    win = "6.35" if x["total"]["0"] < y["total"]["0"] else "9.53"
    o.write('<tr><td>%s</td><td class="n">%.5f %%</td><td class="n">%.5f %%</td>'
            '<td><b>%s</b></td></tr>\n'
            % (name, 100 * x["total"]["0"], 100 * y["total"]["0"], win))
for k, name in (("40", "바닥판까지 칠함 &mdash; 40도"),
                ("20", "바닥판까지 칠함 &mdash; 20도")):
    x, y = dby[(6.35, 40.0, "B")], dby[(9.53, 40.0, "B")]
    win = "6.35" if x["total"][k] < y["total"][k] else "9.53"
    o.write('<tr><td>%s</td><td class="n">%.5f %%</td><td class="n">%.5f %%</td>'
            '<td><b>%s</b></td></tr>\n'
            % (name, 100 * x["total"][k], 100 * y["total"][k], win))
o.write('</tbody></table></div>\n')
o.write('<p>바닥판을 칠하면 <b>9.53 이 세 각도에서 모두 이긴다.</b> '
        '32가지 연구에서 6.35 가 앞섰던 것은 바탕이 5 % 도료였기 때문이다.</p>\n')

o.write('<h3>포일이 깊이보다 센 지렛대다</h3>\n')
o.write('<p>테두리가 남은 몫의 주인이 됐으니, 포일을 얇게 하는 것이 '
        '판을 깊게 하는 것보다 낫다. 셀 9.53 / 깊이 40, 바닥판까지 칠한 경우.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>포일</th><th>테두리 넓이</th>'
        '<th>정면</th><th>20도</th><th>40도</th><th>반짝임</th>'
        '</tr></thead><tbody>\n')
for f in FOILS:
    r = fby[(f, "B")]
    pick = ' class="pick"' if f == PICK_F else ""
    o.write('<tr%s><td>%.2f mm</td><td class="n">%.2f %%</td>'
            '<td class="n"><b>%.5f %%</b></td><td class="n">%.5f %%</td>'
            '<td class="n">%.5f %%</td><td class="n">%.4f</td></tr>\n'
            % (pick, f, 100 * r["rim_fraction"], 100 * r["total"]["0"],
               100 * r["total"]["20"], 100 * r["total"]["40"], r["head_on"]))
o.write('</tbody></table></div>\n')
fa, fb = fby[(NOW_F, "B")], fby[(PICK_F, "B")]
o.write('<div class="scroll"><table><thead><tr><th>같은 40 mm 판에서</th>'
        '<th>정면</th><th>20도</th><th>40도</th><th>판 두께</th>'
        '</tr></thead><tbody>\n')
def times(x):
    # 1 보다 작으면 좋아진 게 아니라 나빠진 것이다. 같은 색으로 두면
    # "0.96 배 좋아짐" 으로 읽힌다. 실제로 그렇게 읽혔다.
    return ('<td class="n%s">%.2f 배%s</td>'
            % ("" if x >= 1.0 else " bad", x, "" if x >= 1.0 else " (나빠짐)"))


o.write('<tr><td>깊이 40 &rarr; 60 (포일 0.08)</td>%s%s%s'
        '<td class="n bad">1.5 배 두꺼워짐</td></tr>\n'
        % (times(d40["total"]["0"] / d60["total"]["0"]),
           times(d40["total"]["20"] / d60["total"]["20"]),
           times(d40["total"]["40"] / d60["total"]["40"])))
o.write('<tr class="pick"><td>포일 0.08 &rarr; 0.04 (깊이 40)</td>%s%s%s'
        '<td class="n">그대로</td></tr>\n'
        % (times(fa["total"]["0"] / fb["total"]["0"]),
           times(fa["total"]["20"] / fb["total"]["20"]),
           times(fa["total"]["40"] / fb["total"]["40"])))
o.write('</tbody></table></div>\n')
o.write('<p>깊이를 1.5 배로 늘리면 40도가 오히려 조금 나빠진다. '
        '포일을 반으로 줄이면 세 각도가 다 좋아지고 판 두께는 그대로다.</p>\n')
o.write('<p>얇은 포일은 특별 주문이 아니다. Hexcel 규격 표기가 '
        '"셀 크기 &ndash; 합금 &ndash; 포일 두께" 이고 '
        '<b>3/8-5052-.001</b> 은 셀 3/8인치(9.53 mm)에 포일 0.001인치'
        '(0.0254 mm)인 항공용 카탈로그 품목이다. 우리가 쓰던 0.08 mm 는 '
        '3/8인치 셀 기준으로 오히려 두꺼운 축이다.</p>\n')
o.write('<p class="tag">[확인] <a href="https://www.matweb.com/search/'
        'datasheettext.aspx?matguid=f0e82888dc7a462b85afef04e7620ee9">'
        'Hexcel HexWeb CR III 3/8-5052-.002</a> &middot; '
        '<a href="https://www.hexcel.com/wp-content/uploads/2025/12/'
        'HexWeb_CRIII_DataSheet.pdf">CR III 규격서</a></p>\n')

# ---- 추천 ----
pick = fby[(PICK_F, "B")]
now = fby[(NOW_F, "B")]
o.write('<div class="card verdict ok"><h3 style="margin:0">추천</h3>\n')
o.write('<p class="lead">셀 <b>9.53 mm</b> · 깊이 <b>40 mm</b> · '
        '포일 <b>0.03~0.04 mm</b> · <b>바닥판을 따로 칠해서 붙일 것</b></p>\n')
o.write('<div class="scroll"><table><thead><tr><th>세 축</th>'
        '<th>지금 견적 (포일 0.08)</th><th>추천 (포일 0.04)</th>'
        '</tr></thead><tbody>\n')
for nm, i, fmt in (("반사 총량 정면", 0, "%.5f %%"),
                   ("반사 총량 20도", 1, "%.5f %%"),
                   ("반사 총량 40도", 2, "%.5f %%"),
                   ("모양 뭉개기", 3, "%.4f"),
                   ("정면 반짝임", 4, "%.4f")):
    a, b = axes(now)[i], axes(pick)[i]
    o.write('<tr><td>%s</td><td class="n">%s</td><td class="n"><b>%s</b></td>'
            '</tr>\n' % (nm, fmt % a if a is not None else "&middot;",
                         fmt % b if b is not None else "&middot;"))
o.write('</tbody></table></div>\n')
o.write('<p><b>벌집이 못 사는 축이 하나 있다.</b> 모양 뭉개기 목표는 1.42 인데 '
        '벌집은 어느 깊이·셀·포일에서도 0.96 근처다. 민판이 1.0 이니 '
        '벌집은 모양을 <b>전혀 안 뭉갠다.</b> 그 축이 중요하면 벌집이 답이 '
        '아니다.</p>\n')
o.write('</div></section>\n')

# ---------------- 만드는 법 ----------------
o.write('<section><h2>그래서 어떻게 만드나</h2>\n')
WAYS = [
    ("바닥판을 따로 칠해서 나중에 붙인다",
     "정면 반사의 절반과 정면 반짝임 6배가 여기서 나온다. 그런데 바닥판은 "
     "평평한 판이다. 벌집을 붙이기 전에 칠하면 깊이 문제가 아예 없다.",
     None),
    ("위에서 15 mm 만 뿌린다",
     "40 mm 를 다 칠할 필요가 없다. 깊이 대 지름이 4.2 대 1 이 아니라 "
     "1.6 대 1 이 된다. 이건 뿌려서 들어간다.",
     None),
    ("담근다",
     "자동차 촉매 담체는 1 mm 관에 길이 100 mm 다. 깊이 대 지름 100 대 1. "
     "이걸 담가서 30 &micro;m 두께로 균일하게 칠하고 모서리에도 금이 안 간다. "
     "우리는 4.2 대 1 이라 24배 쉽다. 고이는 게 걱정이면 담그고 원심력으로 "
     "터는 방식(dip-spin)이 있다.",
     [("코디어라이트 벌집 담금 코팅",
       "https://www.sciencedirect.com/science/article/abs/pii/S0272884216308343"),
      ("Chem-Plate 담그고 돌리기",
       "https://www.chemplateindustries.com/dip-spin")]),
    ("전착도장 (ED, e-coat)",
     "담그기의 전기 버전이다. 겉이 칠해지면 절연이 되어 전류가 안 칠해진 안쪽으로 "
     "옮겨간다. 그래서 막힌 구멍과 안쪽 빈 공간까지 균일하게 칠해진다. 가루 도장이 "
     "안 되는 이유(패러데이 상자)가 여기엔 없다. 두께 25~50 &micro;m. "
     "<b>다만 표면이 매끈하게 나온다.</b> 매끈하면 광택이고 광택은 반짝임을 키운다. "
     "드러나는 면은 반드시 무광으로 따로 마감해야 한다.",
     [("Valence: e-coat 대 powder coat",
       "https://www.valencesurfacetech.com/the-news/e-coat-vs-powder-coat/")]),
    ("포일을 펼치기 전에 칠한다",
     "벌집은 원래 평평한 포일에 접착제 줄을 찍고, 쌓아 눌러 붙이고, 잘라서 펼쳐 "
     "만든다. 표면 처리를 붙이기 전 포일 단계에서 하는 것이 표준이다. "
     "이러면 깊이 문제가 아예 없다.",
     [("Corex 알루미늄 벌집 제조 공정",
       "https://corex-honeycomb.com/products-and-services/aluminium-honeycomb-manufacturing/")]),
    ("벌집 대신 격자(eggcrate)",
     "평평한 날을 슬롯으로 끼워 맞추는 구조다. 날 하나하나가 평평하니 미리 칠하고 "
     "조립하면 된다. 깊이는 날 높이일 뿐이다. 다만 셀이 사각형이라 "
     "우리 측정을 다시 해야 한다.",
     [("Edee 알루미늄 격자 루버", "https://www.edee.com/fbseries.htm")]),
]
for i, (title, body, links) in enumerate(WAYS, 1):
    o.write('<div class="card"><h3 style="margin:0">%d. %s</h3>\n<p>%s</p>\n'
            % (i, esc(title), body))
    if links:
        o.write('<p class="tag">[확인] %s</p>\n'
                % " &middot; ".join('<a href="%s">%s</a>' % (u, esc(t))
                                    for t, u in links))
    o.write('</div>\n')
o.write('</section>\n')

# ---------------- 아노다이징 ----------------
o.write('<section><h2>아노다이징 못 한다는 건 손해가 아니다</h2>\n')
o.write('<div class="scroll"><table><thead><tr><th>재료</th><th>반사율</th>'
        '<th>확산 비율</th></tr></thead><tbody>\n')
for k in (r0["top"], "anodised", r0["base"]):
    m = MAT.get(k)
    if not m:
        continue
    o.write('<tr><td><span style="display:inline-block;width:10px;height:10px;'
            'background:%s;border:1px solid var(--line);margin-right:6px"></span>'
            '%s</td><td class="n">%.3f %%</td><td class="n">%.4f</td></tr>\n'
            % (m["color"], esc(m["label"]), 100 * m["rho"], m["df"]))
o.write('</tbody></table></div>\n')
o.write('<p><b>흑색 아노다이징과 보통 무광 검정 도료가 사실상 같다.</b> '
        '애초에 좋은 답이 아니었다.</p>\n')
o.write('<p>그리고 업체 말이 물리적으로도 맞다. 흑색 아노다이징은 보통 '
        '10~25 &micro;m 이고 그 절반이 알루미늄을 파먹으며 자란다. 포일이 '
        '%.0f &micro;m 인데 양면에 25 &micro;m 씩이면 금속이 %.0f &micro;m 만 '
        '남고 나머지는 잘 깨지는 산화막이다. 펼칠 때 접히는 자리가 버티기 '
        '어렵다.</p>\n' % (1000 * T, 1000 * T - 25))
o.write('<p class="tag">[확인] <a href="https://www.xometry.com/resources/'
        'machining/black-anodizing/">Xometry 흑색 아노다이징 두께</a></p>\n')
o.write('</section>\n')

# ---------------- 한국에서 어디에 맡기나 ----------------
# 아래는 "이런 공정을 한다고 적어 놓은 곳" 이다. 알루미늄 벌집에 무광 검정을
# 해 봤는지는 확인 못 했다. 전화해서 물어볼 목록이지 추천 목록이 아니다.
o.write('<section><h2>한국에서 어디에 맡기나</h2>\n')
o.write('<p>일을 둘로 나눠서 맡기면 된다. <b>벌집 코어는 국내에서 사고, '
        '검정 칠은 표면처리 업체에 따로 맡긴다.</b> 한 곳에서 다 해 주는 곳을 '
        '찾을 필요가 없다.</p>\n')
o.write('<div class="card"><h3 style="margin:0">벌집 코어 만드는 곳</h3>\n')
o.write('<ul>\n')
for n, u, note in (
        ("홍성산업 하이브텍스", "https://architecks.com/bbs/page.php?hid=m02_01_02",
         "국내 유일 연속라인 설비라고 적어 놓았다"),
        ("인토토", "https://intotocompany.co.kr/hoheycombcore",
         "알루미늄 하니컴 코어와 패널"),
        ("PP CORE", "http://www.ppcore.co.kr/default/m1/p01.php",
         "알루미늄·플라스틱 하니컴 판넬")):
    o.write('<li><a href="%s">%s</a> &mdash; %s</li>\n' % (u, esc(n), esc(note)))
o.write('</ul>\n<p style="font-size:14px;color:var(--muted)">'
        '물어볼 것: 셀 %.2f mm, 깊이 %.0f mm, 포일 %.2f mm 가 되는지. '
        '표준 셀은 3/8인치 = 9.53 mm 라 규격품이다.</p></div>\n' % (P, D, T))
o.write('<div class="card"><h3 style="margin:0">전착도장 하는 곳</h3>\n<ul>\n')
for n, u in (("디아스코", "http://diasco.co.kr/ed_coating.php"),
             ("이디탑", "http://edtop.co.kr/"),
             ("한상피앤티", "http://www.hansangpnt.com/ed_coating.php"),
             ("이에이치에스", "http://www.ehscoating.co.kr/edcoating.php")):
    o.write('<li><a href="%s">%s</a></li>\n' % (u, esc(n)))
o.write('</ul>\n<p style="font-size:14px;color:var(--muted)">'
        '이곳들이 알루미늄 벌집에 무광 검정을 해 봤는지는 확인 못 했다. '
        '전화해서 물어볼 목록이지 추천 목록이 아니다.</p></div>\n')
o.write('<div class="card"><h3 style="margin:0">더 찾고 싶으면</h3>\n<ul>\n')
o.write('<li><a href="http://www.bwpa.or.kr/">반월표면처리사업협동조합</a> '
        '&mdash; 안산 반월·시화 국가산업단지에 표면처리 업체가 모여 있다. '
        '도금·아노다이징·도장이 한 단지 안에 있다.</li>\n')
o.write('<li><a href="https://www.kicox.or.kr">한국산업단지공단</a> '
        '입주기업 검색 &mdash; 업종으로 걸러서 찾을 수 있다.</li>\n')
o.write('</ul></div>\n')
o.write('<p>업체에 말할 때 <b>"전착도장"</b> 또는 <b>"ED 도장"</b> 이라고 하면 '
        '통한다. 영어로는 e-coat, electrocoating, 또는 cationic ED 다. '
        '담그고 원심력으로 터는 방식은 <b>"딥스핀"</b> 이다.</p>\n')
o.write('</section>\n')

# ---------------- 업체에 물어볼 것 ----------------
o.write('<section><h2>업체에 물어볼 것</h2><div class="card"><ul>\n')
for q in ("바닥판을 따로 주시면 우리가 칠해서 보내겠습니다. "
          "벌집만 나중에 붙일 수 있습니까?",
          "위에서 15 mm 까지만 검게 칠하면 됩니다. 40 mm 전부가 아닙니다.",
          "담그거나 전착도장 하는 협력사가 있습니까?",
          "포일을 펼치기 전에 검게 칠할 수 있습니까?",
          "아노다이징은 필요 없습니다. 무광 검정 도료로 충분합니다. "
          "대신 광택이 낮아야 합니다."):
    o.write('<li>%s</li>\n' % esc(q))
o.write('</ul></div></section>\n')

# ---------------- 안 잰 것 ----------------
o.write('<section><h2>안 잰 것</h2><ul>\n')
for x in ("관 안쪽에 <b>아무것도</b> 못 넣는 경우. 맨 알루미늄 값이 재료표에 "
          "없고, 없는 재료로 숫자를 내지 않는다.",
          "격자(사각 셀)의 세 축. 우리 측정은 육각 벌집만이다.",
          "전착도장 표면의 실제 거칠기. 매끈하다는 것은 업체 설명이고 "
          "우리가 잰 값이 아니다.",
          "모양 뭉개기와 정면 반짝임은 위상 6 으로 줄여 잰 추정값이다. "
          "보고서에 실린 통계와 같은 수가 아니다. 다만 반짝임은 "
          "32가지 연구와 같은 방법(셀 열 개 조각, 정면, 빔 7.5 mm)으로 "
          "쟀고 같은 값(2.635 / 2.599)이 나왔다."):
    o.write('<li>%s</li>\n' % x)
o.write('</ul></section>\n')

o.write('<section><p class="tag">잰 것: %s · %d 점 · 표본 %d · '
        '거칠기 슬라이더 %.4f (알파 %.3f) · 면 0/45/90도 중 가장 밝은 값. '
        '만든 것: scripts/sweep_paint_depth.py, scripts/sweep_paint_depth_flash.py. '
        '이 문서: scripts/build_paint_depth_report.py</p></section>\n'
        % (os.path.basename(SRC), len(rows), r0["samples"], r0["slider"],
           r0["alpha"]))
o.write('</div></body></html>\n')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, "w", encoding="utf-8").write(o.getvalue())
print("%s  (%d 바이트)" % (OUT, len(o.getvalue())))
