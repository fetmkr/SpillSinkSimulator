# -*- coding: utf-8 -*-
"""최종 후보 보고서의 숫자를 시뮬레이터 화면에서 그대로 다시 낼 수 있나. 렌더 없음.

    python3 scripts/gate_finalists_ui_path.py

사용자가 보고서 값을 화면에서 재 보고 검증하기로 했다 (2026-09-15). 그러려면
화면이 보내는 요청과 보고서 측정(measure_finalists.py)이 서버에서 **같은 호출**이
되어야 한다.

이 검사가 하는 것
    1  보고서의 "시뮬레이터에서 다시 내는 법" 대로 화면 칸을 채웠을 때 화면이
       보내는 요청 본문을 만든다. index.html 의 요청 조립 코드를 한 줄씩 옮겼다
       (measure(): 1090 줄 부근, #mf onclick: 2742 줄 부근, FLOORMAT, pcovSync).
       **옮긴 것이다. 실제 브라우저를 돌린 것이 아니다.**
    2  그 본문을 실제 HTTP 처리기(/api/measure, /api/form)에 보내고, 측정 함수를
       가짜로 바꿔 끼워 서버가 만든 호출 인자를 받는다.
    3  보고서 측정이 쓴 인자(결과 파일의 spec·finish + form_metrics 의 방 조건)와
       견준다. 뜻이 같은 값(예: thetas None 과 FORM_THETAS)은 같게 친다.

다르면 무엇이 다른지 적는다. 알려진 차이 하나: 첫 8 개 후보(측정이 먼저 끝난
것)는 바닥판 칸을 비워 보냈고, 화면은 "바탕과 같게" 를 바탕 재료 이름으로 보낸다.
같은 재료라 숫자 차이는 작을 것이다 [추측: gate_backing_slot 에서 0.017 %].
실제 크기는 GPU 가 비면 렌더로 잰다.
"""
import io
import os
import sys
import json
import inspect
import threading
import contextlib
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import sim_server as S                                          # noqa: E402
import form_metrics as FM                                           # noqa: E402

SRC = os.path.join(ROOT, "results", "finalists_2026_09_15.json")
OUT = os.path.join(ROOT, "results", "audit_2026_09_14", "fix_finalists_ui_path.json")
CALLS = []
ORIG = {n: getattr(S, n) for n in ("measure", "form")}


def spy(name):
    sig = inspect.signature(ORIG[name])

    def f(*a, **kw):
        b = sig.bind(*a, **kw)
        b.apply_defaults()
        CALLS.append((name, dict(b.arguments)))
        if name == "measure":
            pl = {"0": {"0": 0.01}}
            return (pl, {}) if kw.get("with_conditions") else pl
        return {"converged": True, "smear": 1.0, "face_mm": 60.0, "planes": {}}
    return f


def ui_controls(row):
    """What the user sets on screen, from the report recipe."""
    fin = row.get("finish") or {}
    spec = row["spec"]
    depth = float(spec.get("depth", 0) or 0)
    if fin.get("paint_depth") and fin.get("deep_coating"):
        pcov = 100.0 * float(fin["paint_depth"]) / depth
        deep = fin["deep_coating"]
    else:
        pcov, deep = 100.0, fin.get("coating")
    return {"coat": fin.get("coating"), "deepcoat": deep, "pcov": pcov,
            "floorcoat": fin.get("floor_coating") or "__same",
            "top": spec.get("top"), "depth": depth}


def ui_body(row, which, obs=0.0, proto=None, seed=None):
    """index.html's request builder, transcribed. `seed` is the #seed box
    (empty = None = default seed)."""
    c = ui_controls(row)
    NOTOP = c["top"] in ("none", "flat")
    NOPAINT = c["coat"] == "none"
    FLOORMAT = c["deepcoat"] if c["floorcoat"] == "__same" else c["floorcoat"]
    coating = c["deepcoat"] if (NOTOP or NOPAINT or c["pcov"] <= 0) else c["coat"]
    no_deep = NOTOP or NOPAINT or c["pcov"] >= 100 or c["pcov"] <= 0
    pd = c["depth"] * c["pcov"] / 100.0
    body = {"spec": row["spec"], "renderer": "cycles", "diffuse_frac": None,
            "roughness": None, "floor_coating": None if NOTOP else FLOORMAT,
            "slot_df": None, "slot_rough": None, "coating": coating,
            "deep_coating": None if no_deep else c["deepcoat"],
            "paint_depth": None if no_deep else pd, "cycles_seed": seed}
    if which == "measure":
        body.update(thetas=proto["total_thetas"], phis=proto["total_phis"])
    else:
        body.update(beam_w=None, mm_per_px=None, obs_elev=obs,
                    phis=proto["form_phis"])
    return body


def norm(v):
    return json.loads(json.dumps(v))


def report_call(row, which, obs=0.0):
    fin = dict(row.get("finish") or {})
    if which == "measure":
        return dict(spec=row["spec"], thetas=list(FM.ROOM_TOTAL_THETAS),
                    diffuse_frac=None, roughness=None, samples=FM.RHO_SAMPLES,
                    phis=list(FM.ROOM_TOTAL_PHIS), **fin)
    return dict(spec=row["spec"], thetas=list(FM.FORM_THETAS), n_phase=None,
                samples=None, phis=list(FM.FORM_PHIS), obs_elev=obs,
                diffuse_frac=None, roughness=None, **fin)


def compare(got, want, which):
    diffs = []
    keys = ("coating", "deep_coating", "paint_depth", "floor_coating",
            "diffuse_frac", "roughness", "phis", "samples", "obs_elev", "thetas",
            "n_phase", "beam_w", "mm_per_px")
    for k in keys:
        if k not in got and k not in want:
            continue
        g, w = got.get(k), want.get(k)
        if k == "thetas" and which == "form" and g is None:
            g = list(FM.FORM_THETAS)            # server fills FB.THETAS
        if k == "samples" and which == "measure":
            g = g                               # run_op fills RHO_SAMPLES
        if k in ("paint_depth", "obs_elev") and g is not None and w is not None:
            if abs(float(g) - float(w)) > 1e-9:
                diffs.append("%s: 화면 %s / 보고서 %s" % (k, g, w))
            continue
        if isinstance(g, (list, tuple)) and isinstance(w, (list, tuple)):
            g, w = [float(x) for x in g], [float(x) for x in w]
        if norm(g) != norm(w):
            diffs.append("%s: 화면 %s / 보고서 %s" % (k, g, w))
    # geometry: the server builds from spec; margin is forced by the server
    gs = dict(got["spec"]); ws = dict(want["spec"])
    gs.pop("margin_depths", None); ws.pop("margin_depths", None)
    if norm(gs) != norm(ws):
        diffs.append("spec 다름")
    return diffs


def main():
    data = json.load(open(SRC))
    for n in ORIG:
        setattr(S, n, spy(n))
    S.IN_BLENDER = True
    S.on_main = lambda fn, *a, **kw: fn(*a, **kw)
    from http.server import ThreadingHTTPServer
    srv = ThreadingHTTPServer(("127.0.0.1", 0), S.H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    proto = json.loads(urllib.request.urlopen(
        "http://127.0.0.1:%d/api/protocol" % port, timeout=30).read())

    def post(path, body):
        n0 = len(CALLS)
        with contextlib.redirect_stdout(io.StringIO()):
            urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:%d%s" % (port, path),
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"}), timeout=60).read()
        return CALLS[n0:][-1][1]

    out, n_bad = {}, 0
    print("보고서 후보 %d 개, 화면 요청 대 보고서 호출" % len(data["rows"]))
    for key, row in data["rows"].items():
        if not row.get("spec"):
            out[key] = {"skip": "spec 없음 (옛 경로로 잰 행)"}
            print("  [SKIP] %s -- spec 없음" % key)
            continue
        res = {}
        got = post("/api/measure", ui_body(row, "measure", proto=proto))
        res["measure"] = compare(got, report_call(row, "measure"), "measure")
        for obs in FM.ROOM_OBSERVERS:
            got = post("/api/form", ui_body(row, "form", obs, proto))
            d = compare(got, report_call(row, "form", obs), "form")
            if d:
                res["form_obs%g" % obs] = d
        out[key] = res
        flat = res["measure"] + sum((v for k, v in res.items() if k != "measure"), [])
        uniq = sorted(set(flat))
        ok = not uniq
        n_bad += (not ok)
        print("  [%s] %s%s" % ("SAME" if ok else "DIFF", key,
                               "" if ok else "  ->  " + " | ".join(uniq)))
    srv.shutdown()
    json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
    print("\n다른 후보 %d 개 -> %s" % (n_bad, os.path.relpath(OUT, ROOT)))


if __name__ == "__main__":
    main()
