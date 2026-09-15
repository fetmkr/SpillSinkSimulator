# -*- coding: utf-8 -*-
"""최종 후보 보고서. 세 축 순위, 전체 순위, 후보마다 3D 그림과 설계도 단면.

    python3 scripts/build_finalists_report.py

읽는 것
    results/finalists_2026_09_15.json            측정 (measure_finalists.py)
    /tmp/simsrv/finalist_previews/manifest.json  3D 그림 (render_finalist_previews.py)
    report/comb/comb_musou_2026-08-22.html       디자인. 이미 있는 체계를 쓴다.
쓰는 것
    report/comb/finalists_2026-09-15.html

순위를 매기는 규칙 (보고서 첫머리에도 적는다)
    총량    방 조건 입사 30, 40, 45, -40 도 x 방위 0, 45 중 가장 밝은 값. 낮을수록 좋다.
    반짝임  box 봉우리, 빔 -40, 30, 40 도 x 관객 20, 40, 60 도 중 가장 밝은 값.
            낮을수록 좋다. 빔 -40 / 관객 +40 은 프로젝터 반대편 관객 (거울 방향).
    뭉개기  +-40 평균, 관찰 0 도. 높을수록 좋다. 수렴 안 한 값은 하한이라 표시한다.
    전체    세 축 순위의 평균. 같으면 반짝임이 낮은 쪽. 어느 축에서도 다른 후보에
            다 지지 않는 후보(파레토)는 따로 표시한다.

설계도는 실제 측정 메시를 평면으로 잘라 그린다. 손으로 그린 모양이 아니다
(figure-traced-equals-drawn). 가로 세로 같은 축척이라 각도가 참이다.
"""
import os
import re
import io
import json
import math
import base64
import importlib
import dataclasses
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
import sys                                                           # noqa: E402
if HERE not in sys.path:
    sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import sim_server as SS                                         # noqa: E402

SRC = os.path.join(ROOT, "results", "finalists_2026_09_15.json")
PREV = "/tmp/simsrv/finalist_previews/manifest.json"
STYLE_FROM = os.path.join(ROOT, "report/comb/comb_musou_2026-08-22.html")
OUT = os.path.join(ROOT, "report/comb/finalists_2026-09-15.html")

# 순위에 쓰는 각도는 form_metrics 한 곳에서 읽는다 (시뮬레이터 화면과 같은 목록).
import form_metrics as FM                                           # noqa: E402
ROOM_TOTAL_THETAS = tuple("%.0f" % t for t in FM.RANK_TOTAL_THETAS)
ROOM_BEAMS = tuple("%+.0f" % t for t in FM.RANK_BEAMS)
ROOM_OBS = tuple("%g" % t for t in FM.RANK_OBSERVERS)


def ui_recipe(row):
    """How to get this row's numbers out of the simulator screen, control by
    control. The finish mapping follows index.html's request builder: coverage
    100 % sends no deep coat, and the floor slot 'same as base' sends the base."""
    m2 = "Musou Black — fit to THR, TIS and lobe shape"
    names = {"musou_fit2": m2, "wall_5pct": "matte black wall — 5% (control)"}
    fin = row.get("finish") or {}
    spec = row.get("spec") or {}
    items = []
    if row.get("design"):
        items.append(("디자인", "위쪽 목록 <b>published</b> 에서 <code>%s</code>"
                      % (SS.HEADLINE.get(row["design"]) or row["design"])))
    else:
        tp = spec.get("top_params") or {}
        items.append(("구조", "top <code>%s</code>, %s" % (
            spec.get("top"), ", ".join("%s <b>%g</b>" % (k, v) for k, v in tp.items()
                                       if isinstance(v, (int, float))))))
        items.append(("깊이 / 바닥", "depth <b>%g</b> mm, floor <code>%s</code>%s"
                      % (spec.get("depth", 0), spec.get("floor", "none"),
                         (", floor depth <b>%g</b> mm, floor pitch <b>%g</b>"
                          % (spec.get("floor_depth", 0),
                             (spec.get("floor_params") or {}).get("pitch", 0)))
                         if spec.get("floor", "none") != "none" else "")))
    items.append(("판", "panel <b>%g</b> mm" % float(spec.get("panel")
                                                   or spec.get("face") or 60)))
    depth = float(spec.get("depth", 0) or 0)
    pd_ = fin.get("paint_depth")
    if pd_ and fin.get("deep_coating"):
        cov = 100.0 * float(pd_) / depth if depth else 0
        items.append(("도장", "위 칠 <b>%s</b>, 바탕 <b>%s</b>, 칠 깊이 <b>%g mm</b> "
                      "(coverage %.1f %%)" % (names.get(fin["coating"], fin["coating"]),
                                              names.get(fin["deep_coating"]),
                                              float(pd_), cov)))
    else:
        items.append(("도장", "위 칠 <b>%s</b>, coverage <b>100 %%</b>, 바탕도 <b>%s</b>"
                      % (names.get(fin.get("coating")), names.get(fin.get("coating")))))
    fl = fin.get("floor_coating")
    items.append(("바닥판", "<b>%s</b>" % (names.get(fl) if fl else
                                           "same as base (기본값)")))
    items.append(("재기", "Renderer <b>Cycles</b>. 총량 버튼 한 번, 뭉개기·반짝임 버튼은 "
                  "관객 각도(observer) <b>0 / 20 / 40 / 60</b> 도 로 한 번씩. "
                  "빔 폭·해상도 칸은 비워 둔다."))
    items.append(("읽기", "총량은 입사각 × 방위 표. 뭉개기·반짝임은 <b>&phi; 0&deg;</b> "
                  "평면의 빔 각도별 표 (box)."))
    return "".join("<dt>%s</dt><dd>%s</dd>" % kv for kv in items)


# ---------------------------------------------------------------- geometry

FAMILY_CLASS = [("floor", "geom_floor", "FloorParams"),
                ("cone3d", "geom3d", "Cone3DParams"),
                ("topo", "geom_topo", "TopoParams"),
                ("cell", "geom_cell", "CellParams"),
                ("stack", "geom_stack", "StackParams")]


def mesh_for(row):
    """(kind, data): ("mesh", (verts, faces)) or ("loops", loops) for 1D."""
    if row.get("spec"):
        spec = dict(row["spec"], margin_depths=0.0)
        with contextlib.redirect_stdout(io.StringIO()):
            v, f, _p = SS.build(spec)
        return "mesh", (v, f)
    prm = dict(row["params"])
    for fam, mod, cls in FAMILY_CLASS:
        C = getattr(importlib.import_module(mod), cls)
        if set(prm) - {x.name for x in dataclasses.fields(C)}:
            continue
        return "mesh", importlib.import_module(mod).build_mesh(C(**prm))
    import profile_ridge as PR
    cs = PR.build_cross_section(PR.RidgeParams(**prm))
    return "loops", list(cs.stage1) + list(cs.stage2) + list(cs.shell)


def slice_mesh(verts, faces, c0, axis=2, horiz=0):
    """Cut the mesh with the plane coordinate[axis] = c0. Returns segments as
    (horizontal coordinate, depth y) pairs. axis 2 / horiz 0 cuts across Z for
    point fields; axis 0 / horiz 2 cuts across X for anything extruded along X
    (the V-groove), where a Z cut runs along the grooves and shows nothing."""
    segs = []
    for fc in faces:
        idx = list(fc)
        for a in range(1, len(idx) - 1):
            tri = [verts[idx[0]], verts[idx[a]], verts[idx[a + 1]]]
            d = [p[axis] - c0 for p in tri]
            pts = []
            for i in range(3):
                j = (i + 1) % 3
                if (d[i] < 0) != (d[j] < 0):
                    t = d[i] / (d[i] - d[j])
                    pts.append((tri[i][horiz] + t * (tri[j][horiz] - tri[i][horiz]),
                                tri[i][1] + t * (tri[j][1] - tri[i][1])))
            if len(pts) == 2:
                segs.append(pts)
    return segs


def blueprint(row):
    """Cross-section SVG from the measured mesh, three pitches wide, equal
    scale on both axes, dimension lines, English labels."""
    kind, data = mesh_for(row)
    params = row.get("params") or SS._render_params(dict(row["spec"],
                                                         margin_depths=0.0))
    spec = row.get("spec") or {}
    tp = spec.get("top_params") or params.get("top_params") or {}
    pitch = float(tp.get("pitch") or params.get("pitch")
                  or params.get("pitch_mean") or 6.5)
    if kind == "loops":
        segs = []
        for loop in data:
            for i in range(len(loop) - 1):
                (y1, z1), (y2, z2) = loop[i], loop[i + 1]
                segs.append([(z1, y1), (z2, y2)])
    else:
        v, f = data
        span0 = 3.0 * pitch
        # WHERE TO CUT (2026-09-15). The first rule guessed "points or walls"
        # from how many vertices sit at the top; a pyramid with a flat tip has
        # half its vertices there and was cut like a honeycomb, off its apexes,
        # and the drawing said depth 6.4 mm for a 22 mm part. Now: step the cut
        # across one pitch and keep the cut whose window shows the deepest
        # section -- that is the one through the apexes / across the cells.
        # Both cutting directions are tried: a Z cut for point fields, an X cut
        # for parts extruded along X (the V-groove came out empty on a Z cut).
        best = None
        for axis, horiz in ((2, 0), (0, 2)):
            ca = [p[axis] for p in v]
            ch = [p[horiz] for p in v]
            cmid = 0.5 * (min(ca) + max(ca))
            hmid = 0.5 * (min(ch) + max(ch))
            for k in range(24):
                c0 = cmid + (k + 0.37) * pitch / 24.0
                ss = [s for s in slice_mesh(v, f, c0, axis, horiz)
                      if all(abs(p[0] - hmid) <= span0 / 2.0 + 1e-6 for p in s)]
                if not ss:
                    continue
                yy = [p[1] for s in ss for p in s]
                dep = max(yy) - min(yy)
                if best is None or dep > best[0] + 1e-6:
                    best = (dep, ss)
        segs = best[1] if best else []
    if not segs:
        return "<p class='tag'>단면을 못 잘랐다.</p>"
    xs = sorted(0.5 * (s[0][0] + s[1][0]) for s in segs)
    xc = xs[len(xs) // 2]
    span = 3.0 * pitch
    segs = [s for s in segs if all(abs(p[0] - xc) <= span / 2.0 + 1e-6 for p in s)]
    ys = [p[1] for s in segs for p in s]
    ylo, yhi = min(ys), max(ys)
    depth = yhi - ylo
    W = 640.0
    scale = (W - 180.0) / max(span, depth * 0.9)
    H = depth * scale + 120.0
    X = lambda x: 90.0 + (x - (xc - span / 2.0)) * scale        # noqa: E731
    Y = lambda y: 50.0 + (yhi - y) * scale                     # noqa: E731
    o = io.StringIO()
    o.write('<svg viewBox="0 0 %.0f %.0f" role="img" aria-label="cross-section">'
            % (W, H))
    o.write('<rect x="0" y="0" width="%.0f" height="%.0f" fill="var(--bp-bg)"/>'
            % (W, H))
    for k in range(0, 13):
        gx = 90 + k * (W - 180) / 12.0
        o.write('<line x1="%.1f" y1="30" x2="%.1f" y2="%.1f" stroke="var(--bp-grid)" '
                'stroke-width="0.6"/>' % (gx, gx, H - 30))
    fin = row.get("finish") or {}
    pdp = fin.get("paint_depth")
    if pdp:
        yp = Y(yhi - float(pdp))
        o.write('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                'fill="var(--bp-paint)"/>' % (X(xc - span / 2), Y(yhi), span * scale,
                                              yp - Y(yhi)))
        o.write('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="var(--pk)" '
                'stroke-dasharray="5 4" stroke-width="1.2"/>'
                % (X(xc - span / 2), yp, X(xc + span / 2), yp))
        o.write('<text x="%.1f" y="%.1f" class="bp-t" fill="var(--pk)">Musou above '
                '%.0f mm, 5%% paint below</text>' % (X(xc + span / 2) + 6, yp + 4,
                                                      float(pdp)))
    for (a, b) in segs:
        o.write('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="var(--bp-ink)" '
                'stroke-width="1.4" stroke-linecap="round"/>'
                % (X(a[0]), Y(a[1]), X(b[0]), Y(b[1])))
    # dimension: pitch (above), depth (left), scale bar (bottom)
    ytop = 32.0
    o.write('<g stroke="var(--cy)" fill="var(--cy)" stroke-width="1">')
    x1, x2 = X(xc - pitch / 2), X(xc + pitch / 2)
    o.write('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (x1, ytop, x2, ytop))
    for xx, s in ((x1, 1), (x2, -1)):
        o.write('<path d="M%.1f %.1f l%.1f -3 l0 6 z"/>' % (xx, ytop, 7 * s))
    o.write('</g><text x="%.1f" y="%.1f" class="bp-t" text-anchor="middle" '
            'fill="var(--cy)">pitch %.2f mm</text>' % ((x1 + x2) / 2, ytop - 6, pitch))
    xd = 58.0
    o.write('<g stroke="var(--cy)" fill="var(--cy)" stroke-width="1">'
            '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
            '<path d="M%.1f %.1f l-3 7 l6 0 z"/><path d="M%.1f %.1f l-3 -7 l6 0 z"/></g>'
            % (xd, Y(yhi), xd, Y(ylo), xd, Y(yhi), xd, Y(ylo)))
    o.write('<text x="%.1f" y="%.1f" class="bp-t" fill="var(--cy)" '
            'transform="rotate(-90 %.1f %.1f)" text-anchor="middle">depth %.1f mm'
            '</text>' % (xd - 8, (Y(yhi) + Y(ylo)) / 2, xd - 8, (Y(yhi) + Y(ylo)) / 2,
                         depth))
    bar = 10.0 ** math.floor(math.log10(span / 2.0))
    o.write('<line x1="90" y1="%.1f" x2="%.1f" y2="%.1f" stroke="var(--bp-ink)" '
            'stroke-width="2"/><text x="%.1f" y="%.1f" class="bp-t" '
            'fill="var(--bp-ink)">%g mm</text>'
            % (H - 18, 90 + bar * scale, H - 18, 96 + bar * scale, H - 14, bar))
    o.write('<text x="%.1f" y="%.1f" class="bp-t" text-anchor="end" '
            'fill="var(--muted)">section through the measured mesh, true scale</text>'
            % (W - 12, H - 14))
    o.write('</svg>')
    return o.getvalue()


# ---------------------------------------------------------------- metrics

def num(x, nd=4):
    return "—" if x is None else ("%.*f" % (nd, x))


def metrics(row):
    tot = []
    for ph, pl in (row.get("totals") or {}).items():
        for t in ROOM_TOTAL_THETAS:
            if t in pl:
                tot.append(pl[t])
    total = max(tot) if tot else None
    peak, where = None, None
    for ob in ROOM_OBS:
        pk = ((row.get("form") or {}).get(ob) or {}).get("peak_by_stat_by_theta") or {}
        for bm in ROOM_BEAMS:
            v = (pk.get(bm) or {}).get("box")
            if v is not None and (peak is None or v > peak):
                peak, where = v, (bm, ob)
    f0 = (row.get("form") or {}).get("0") or {}
    return {"total": total, "peak": peak, "peak_at": where,
            "smear": f0.get("smear_pm40"), "smear_conv": f0.get("converged_pm40")}


def ranks(vals, higher_better=False, sig=3):
    """Competition ranking (1, 2, 2, 4). Two values that agree to `sig`
    significant figures -- the precision the tables print -- share a rank:
    0.14524773 and 0.14524780 are the same measurement, and ranking them 5th and
    6th would report render noise as an ordering."""
    def key(v):
        if v is None:
            return float("inf")
        q = float("%.*g" % (sig, v))
        return -q if higher_better else q
    keys = [key(v) for v in vals]
    return [1 + sum(1 for k in keys if k < keys[i]) for i in range(len(vals))]


def panel_of(row):
    if row.get("spec"):
        return float(row["spec"].get("panel", 0))
    return float((row.get("params") or {}).get("face_w", 0))


# ---------------------------------------------------------------- page

def main():
    data = json.load(open(SRC))
    rows = [dict(v, key=k) for k, v in data["rows"].items() if not v.get("error")]
    errs = [k for k, v in data["rows"].items() if v.get("error")]
    prev = json.load(open(PREV)) if os.path.exists(PREV) else {}
    M = [metrics(r) for r in rows]
    rt = ranks([m["total"] for m in M])
    rp = ranks([m["peak"] for m in M])
    rs = ranks([m["smear"] for m in M], higher_better=True)
    for i, m in enumerate(M):
        m.update(r_total=rt[i], r_peak=rp[i], r_smear=rs[i],
                 r_mean=(rt[i] + rp[i] + rs[i]) / 3.0)
    for i, m in enumerate(M):
        dominated = False
        for j, n in enumerate(M):
            if i == j or None in (m["total"], m["peak"], m["smear"], n["total"],
                                  n["peak"], n["smear"]):
                continue
            if (n["total"] <= m["total"] and n["peak"] <= m["peak"]
                    and n["smear"] >= m["smear"]
                    and (n["total"] < m["total"] or n["peak"] < m["peak"]
                         or n["smear"] > m["smear"])):
                dominated = True
                break
        m["pareto"] = not dominated
    order = sorted(range(len(rows)), key=lambda i: (M[i]["r_mean"], M[i]["peak"] or 9))
    meta = data["meta"]

    style = re.search(r"<style>(.*?)</style>",
                      io.open(STYLE_FROM, encoding="utf-8").read(), re.S).group(1)
    o = io.StringIO()
    o.write('<!doctype html><html lang="ko"><head><meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<title>천장 패널 최종 후보</title>\n<style>%s\n'
            ':root{--bp-bg:#f3f7fa;--bp-grid:#dde8ef;--bp-ink:#1d3a52;'
            '--bp-paint:rgba(184,87,122,.08)}\n'
            '@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){'
            '--bp-bg:#141c24;--bp-grid:#1f2b36;--bp-ink:#c9dceb;'
            '--bp-paint:rgba(217,138,164,.10)}}\n'
            ':root[data-theme="dark"]{--bp-bg:#141c24;--bp-grid:#1f2b36;'
            '--bp-ink:#c9dceb;--bp-paint:rgba(217,138,164,.10)}\n'
            '.bp-t{font-family:var(--mono);font-size:12px}\n'
            '.bp svg{display:block;width:100%%;height:auto;border:1px solid var(--line);'
            'border-radius:3px}\n'
            '.shot img{display:block;width:100%%;height:auto;border-radius:3px;'
            'border:1px solid var(--line)}\n'
            '.tag{font-family:var(--mono);font-size:12px;color:var(--muted)}\n'
            'a{color:var(--cy)}\n'
            '.pill{font-family:var(--mono);font-size:11px;padding:1px 7px;'
            'border-radius:9px;border:1px solid var(--line);color:var(--muted)}\n'
            '.pill.par{border-color:var(--good);color:var(--good)}\n'
            '.pill.low{border-color:var(--warn);color:var(--warn)}\n'
            '.rk{font-family:var(--mono);font-weight:700}\n'
            '.cand{scroll-margin-top:16px}\n'
            '</style></head><body>\n<div class="wrap">\n' % style)

    best = rows[order[0]]
    o.write('<header><div class="eyebrow">Spill Sink Simulator · 2026-09-15 · '
            '감사 조치 뒤 첫 비교</div>\n<h1>천장 패널 최종 후보</h1>\n'
            '<p class="sub">마지막 후보 구조와 도장 조합 %d 가지를 같은 규약으로 다시 '
            '쟀다. 세 축을 따로 순위 매기고, 셋을 합친 순위도 낸다. 후보마다 3D 그림과 '
            '측정 메시에서 자른 단면을 붙였다.</p></header>\n' % len(rows))

    # --- conditions
    o.write('<section><h2>어떤 조건으로 쟀나</h2>\n<div class="card"><dl>\n')
    for dt, dd in (
            ("방", "10 x 10 m, 천장 6 m, 프로젝터 높이 2 m 에서 45~60 도 위로. "
                   "패널이 받는 빔은 30~45 도, 관객은 0~60 도에서 본다."),
            ("재료", "무소 musou_fit2 (논문 THR·TIS·덩어리 모양 맞춤), 5 %% 무광 검정 "
                     "wall_5pct. 코팅 트리 %s." % meta.get("coating_model")),
            ("총량", "하늘 조명 hemi_view, 빛줄기 %d, 입사 %s 도, 방위 %s 도"
                     % (meta["total_samples"],
                        ", ".join("%g" % t for t in meta["total_thetas"]),
                        ", ".join("%g" % p for p in meta["total_phis"]))),
            ("뭉개기·반짝임", "빔 %.1f mm, 빛줄기 %d, 빔 자리 %d (%s), %.3f mm/px, "
                           "봉우리 %s %.0f mm 상자, 빔 %s 도, 관객 %s 도"
                           % (meta["beam_w"], meta["form_samples"], meta["n_phase"],
                              meta["beam_pos"], meta["mm_per_px"], meta["peak_stat"],
                              meta["peak_box_mm"],
                              ", ".join("%g" % t for t in meta["form_thetas"]),
                              ", ".join("%g" % t for t in meta["observers"]))),
            ("잣대", "민판 무광 검정 = 1.0 (뭉개기·반짝임). 총량은 되돌아온 빛의 비율.")):
        o.write('<dt>%s</dt><dd>%s</dd>\n' % (dt, dd))
    o.write('</dl></div>\n')
    o.write('<div class="card"><h3 style="margin:0">순위 매기는 규칙</h3><ul>'
            '<li><b>총량</b>: 방 조건 입사 30·40·45·−40 도 × 방위 0·45 도 중 가장 밝은 값. '
            '낮을수록 좋다.</li>'
            '<li><b>반짝임</b>: 빔 −40·30·40 도 × 관객 20·40·60 도 중 가장 밝은 box 값. '
            '낮을수록 좋다. 빔 −40 은 프로젝터 반대편 관객이 보는 거울 방향이다.</li>'
            '<li><b>뭉개기</b>: ±40 도 평균, 관찰 0 도. 높을수록 좋다. '
            '<span class="pill low">하한</span> 은 판이 되돌아온 빛을 다 못 담아 '
            '수렴하지 않은 값이다.</li>'
            '<li><b>전체</b>: 세 축 순위의 평균. 같으면 반짝임이 낮은 쪽이 앞. '
            '<span class="pill par">파레토</span> 는 세 축 모두에서 자기보다 나은 '
            '후보가 없는 것이다.</li></ul></div></section>\n')

    # --- overall
    o.write('<section><h2>전체 순위</h2>\n<p>%s 이 세 축 순위 평균에서 가장 앞이다. '
            '다만 판 크기와 도장이 후보마다 다르다. 아래 "견줄 때 주의" 를 같이 읽는다.'
            '</p>\n' % best["case"])
    o.write('<div class="scroll"><table><thead><tr><th>전체</th><th>구조</th>'
            '<th>도장</th><th>판 mm</th><th>총량 %</th><th>순위</th>'
            '<th>반짝임</th><th>순위</th><th>뭉개기</th><th>순위</th><th></th>'
            '</tr></thead><tbody>\n')
    for k, i in enumerate(order):
        r, m = rows[i], M[i]
        o.write('<tr%s><td class="rk">%d</td><td><a href="#c%d">%s</a></td><td>%s</td>'
                '<td class="n">%.0f</td><td class="n">%s</td><td class="n">%d</td>'
                '<td class="n">%s</td><td class="n">%d</td><td class="n">%s%s</td>'
                '<td class="n">%d</td><td>%s</td></tr>\n'
                % (' class="pick"' if k == 0 else '', k + 1, i, r["case"], r["combo"],
                   panel_of(r), num(m["total"] and 100 * m["total"], 3), m["r_total"],
                   num(m["peak"], 3), m["r_peak"], num(m["smear"], 2),
                   '' if m["smear_conv"] else ' <span class="pill low">하한</span>',
                   m["r_smear"],
                   '<span class="pill par">파레토</span>' if m["pareto"] else ''))
    o.write('</tbody></table></div></section>\n')

    # --- per axis
    for title, keyv, keyr, fmt, note in (
            ("반사 총량 순위", "total", "r_total",
             lambda m: num(m["total"] and 100 * m["total"], 3) + " %",
             "방 조건 입사각에서 가장 밝은 값. 낮을수록 좋다."),
            ("정면 반짝임 순위", "peak", "r_peak",
             lambda m: "%s <span class='tag'>빔 %s / 관객 %s</span>"
                       % (num(m["peak"], 3), *(m["peak_at"] or ("—", "—"))),
             "관객 자리에서 가장 밝은 box. 낮을수록 좋다."),
            ("모양 뭉개기 순위", "smear", "r_smear",
             lambda m: num(m["smear"], 2) + ("" if m["smear_conv"]
                                             else " <span class='pill low'>하한</span>"),
             "±40 평균, 관찰 0 도. 높을수록 좋다.")):
        o.write('<section><h2>%s</h2><p class="tag">%s</p>\n<div class="scroll"><table>'
                '<thead><tr><th>순위</th><th>구조</th><th>도장</th><th>판 mm</th>'
                '<th>값</th></tr></thead><tbody>\n' % (title, note))
        for i in sorted(range(len(rows)), key=lambda i: M[i][keyr]):
            o.write('<tr><td class="rk">%d</td><td>%s</td><td>%s</td>'
                    '<td class="n">%.0f</td><td class="n">%s</td></tr>\n'
                    % (M[i][keyr], rows[i]["case"], rows[i]["combo"],
                       panel_of(rows[i]), fmt(M[i])))
        o.write('</tbody></table></div></section>\n')

    # --- simulator check (2026-09-15): the screen's request, sent to the running
    # server, gives the report's numbers. Reads what the two check scripts wrote.
    rep_p = os.path.join(ROOT, "results", "audit_2026_09_14",
                         "reproduce_finalists_server.json")
    ui_p = os.path.join(ROOT, "results", "audit_2026_09_14",
                        "fix_finalists_ui_path.json")
    rep = (json.load(open(rep_p)).get("rows") or {}) if os.path.exists(rep_p) else {}
    uip = json.load(open(ui_p)) if os.path.exists(ui_p) else {}
    n_all = len(data["rows"])
    ui_same = sum(1 for v in uip.values()
                  if isinstance(v, dict) and "skip" not in v
                  and not any(v.values()))
    done = [v for v in rep.values() if not v.get("error")]
    ok = [v for v in done if v.get("missing") == 0 and v.get("converged_same")
          and (v.get("max_abs_rel") or 0) <= 1e-3]
    worst = max((v.get("max_abs_rel") or 0 for v in done), default=None)
    if len(ok) == n_all and ui_same == n_all:
        verdict = ('시뮬레이터도 잘 검증됐다. 보고서의 모든 후보를 시뮬레이터 화면과 같은 '
                   '요청으로 다시 재서 같은 값을 얻었다.')
    else:
        verdict = ('시뮬레이터 검증 진행 중: 다시 잰 후보 %d / %d.' % (len(done), n_all))
    o.write('<section><div class="card"><h2 style="margin:0">시뮬레이터 검증</h2>'
            '<p><b>%s</b></p><ul>'
            '<li>화면이 보내는 요청과 이 보고서의 측정 호출을 견줬다. %d / %d 후보가 같다.</li>'
            '<li>켜 둔 시뮬레이터 서버에 화면과 같은 요청을 보내 실제로 다시 렌더했다. '
            '%d / %d 후보가 끝났고, 모든 칸(총량 각도·방위, 관객별 뭉개기와 수렴, '
            '빔별 반짝임)이 보고서와 맞았다. 가장 큰 차이는 %s 다.</li>'
            '<li>같은 렌더 씨앗으로 잰 비교라 경로가 같다는 확인이다. 씨앗을 바꿨을 때의 '
            '흔들림은 따로 잰다.</li></ul>'
            '<p class="tag">scripts/gate_finalists_ui_path.py, '
            'scripts/reproduce_finalists_server.py</p></div></section>\n'
            % (verdict, ui_same, n_all, len(ok), n_all,
               "—" if worst is None else "%.3f %%" % (100 * worst)))

    # --- caveats
    o.write('<section><div class="card verdict"><h2 style="margin:0">견줄 때 주의</h2><ul>'
            '<li><b>판 크기가 다르다.</b> 발표 설계와 표준 샘플은 60 mm, 발주 사양은 '
            '116, 벌집은 200, 밑변 50 피라미드는 500 이다. 총량과 반짝임은 판 크기에 '
            '거의 안 흔들리지만, 뭉개기는 작은 판에서 되돌아온 빛을 다 못 담아 하한이 '
            '된다.</li>'
            '<li><b>도장이 다르다.</b> 발표 설계는 무소를 모든 면에 칠했고, 발주 사양·'
            '벌집·뒤집힌 피라미드는 팁에서 20 mm 만 무소다.</li>'
            '<li><b>무소 재료가 도표 판독이다.</b> 덩어리 폭이 0.45~0.75 사이로 열려 '
            '있고 절대 눈금이 ±20 %% 흔들린다. 반짝임 절대값은 이 폭을 안고 있다. '
            '같은 재료로 잰 후보끼리의 순서는 덜 흔들린다 [추측].</li>'
            '<li><b>실물 측정이 없다.</b> 모든 값이 시뮬레이터에서 나왔다.</li>'
            '<li>빛줄기 256 에서 box 봉우리는 12 경우 모두 1 %% 안이었지만 256 위는 '
            '안 쟀다.</li>%s</ul></div></section>\n'
            % ("<li>측정 실패: %s</li>" % ", ".join(errs) if errs else ""))

    # --- candidates
    o.write('<section><h2>후보별</h2></section>\n')
    for i in order:
        r, m = rows[i], M[i]
        o.write('<section class="cand" id="c%d"><h3>%s · %s</h3>\n' % (i, r["case"],
                                                                     r["combo"]))
        o.write('<p>전체 %d 위 · 총량 %d 위 · 반짝임 %d 위 · 뭉개기 %d 위 %s</p>\n'
                % (order.index(i) + 1, m["r_total"], m["r_peak"], m["r_smear"],
                   '<span class="pill par">파레토</span>' if m["pareto"] else ''))
        pv = (prev.get(r["key"]) or {}).get("png")
        # STITCH THE THREE VIEWS HERE. preview_geom stitches with PIL inside
        # Blender, whose Python has no PIL, so only single views came out.
        # The three files sit next to each other; join them in plain Python.
        if pv:
            base = re.sub(r"(_threequarter)?\.png$", "", pv)
            views = [base + "_%s.png" % v for v in ("topdown", "edge", "threequarter")]
            if all(os.path.exists(v) for v in views):
                try:
                    from PIL import Image
                    ims = [Image.open(v).convert("RGB") for v in views]
                    sheet = Image.new("RGB", (sum(i.width for i in ims),
                                              max(i.height for i in ims)), (20, 22, 25))
                    x = 0
                    for im in ims:
                        sheet.paste(im, (x, 0))
                        x += im.width
                    sheet = sheet.resize((sheet.width // 2, sheet.height // 2))
                    pv = base + "_sheet.png"
                    sheet.save(pv, optimize=True)
                except ImportError:
                    pass
        if pv and os.path.exists(pv):
            b64 = base64.b64encode(open(pv, "rb").read()).decode()
            o.write('<figure class="shot"><img alt="%s 3D" src="data:image/png;base64,%s">'
                    '<figcaption>왼쪽부터 위에서 본 것 (측정 카메라가 정면에서 보는 '
                    '모습), 옆에서 본 것, 비스듬히 본 것. 모양을 보이려는 그림이지 '
                    '측정이 아니다.</figcaption></figure>\n' % (r["case"], b64))
        else:
            o.write('<p class="tag">3D 그림 없음 (render_finalist_previews.py 를 '
                    '아직 안 돌렸거나 실패)</p>\n')
        try:
            o.write('<figure class="bp">%s<figcaption>측정한 메시를 평면으로 자른 단면. '
                    '가로 세로 같은 축척.</figcaption></figure>\n' % blueprint(r))
        except Exception as exc:
            o.write('<p class="tag">단면 실패: %s</p>\n' % exc)
        o.write('<div class="card"><h3 style="margin:0">시뮬레이터에서 다시 내는 법</h3>'
                '<dl>%s</dl></div>\n' % ui_recipe(r))
        # per-observer table
        o.write('<div class="scroll"><table><thead><tr><th>관객</th>'
                '<th>반짝임 빔 −40</th><th>빔 0</th><th>빔 +30</th><th>빔 +40</th>'
                '<th>뭉개기 ±40</th></tr></thead><tbody>\n')
        for ob in ("0", "20", "40", "60"):
            f = (r.get("form") or {}).get(ob) or {}
            pk = f.get("peak_by_stat_by_theta") or {}
            o.write('<tr><td>%s 도</td>%s<td class="n">%s%s</td></tr>\n'
                    % (ob, "".join('<td class="n">%s</td>'
                                   % num((pk.get(b) or {}).get("box"), 3)
                                   for b in ("-40", "+0", "+30", "+40")),
                       num(f.get("smear_pm40"), 2),
                       "" if f.get("converged_pm40") else ' <span class="pill low">하한</span>'))
        o.write('</tbody></table></div>\n')
        o.write('<div class="scroll"><table><thead><tr><th>총량 %</th>')
        ths = ("0", "20", "30", "40", "45", "-20", "-40")
        o.write("".join('<th>%s 도</th>' % t for t in ths) + '</tr></thead><tbody>\n')
        for ph, pl in (r.get("totals") or {}).items():
            o.write('<tr><td>방위 %s 도</td>%s</tr>\n'
                    % (ph, "".join('<td class="n">%s</td>'
                                   % num(pl.get(t) and 100 * pl[t], 3) for t in ths)))
        o.write('</tbody></table></div></section>\n')

    o.write('<section><p class="tag">이 문서를 짓는 스크립트: '
            '<code>scripts/build_finalists_report.py</code>. 측정: '
            '<code>scripts/measure_finalists.py</code> → '
            '<code>results/finalists_2026_09_15.json</code>. 방법과 근거: '
            '<code>report/METHOD.html</code>, 감사와 조치: '
            '<code>results/FINDINGS_simulator_audit_2026_09_14.md</code>.</p>'
            '</section>\n</div></body></html>\n')

    html = o.getvalue()
    bad = [ln.strip()[:80] for ln in html.split("\n") if "%%" in ln or "%s" in ln]
    if bad:
        for ln in bad[:5]:
            print("남은 서식: %s" % ln)
        raise SystemExit("서식이 안 풀렸다 -- 발행 안 함")
    io.open(OUT, "w", encoding="utf-8").write(html)
    print("%s  (%d 바이트, 후보 %d, 실패 %d)" % (OUT, len(html), len(rows), len(errs)))


if __name__ == "__main__":
    main()
