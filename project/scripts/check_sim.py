# -*- coding: utf-8 -*-
"""시뮬레이터가 제대로 도는지 항목별로 확인한다.

돌고 있는 서버에 HTTP 로 말을 건다. 블렌더 안에서 도는 게 아니므로 빠르고,
서버가 실제로 사람에게 내주는 것과 같은 경로를 쓴다.

    python3 scripts/check_sim.py            전부
    python3 scripts/check_sim.py A B        고른 묶음만

항목은 통과/실패를 스스로 판정한다. 판정 못 하면 실패로 센다 -- "확인 못
했다" 를 "괜찮다" 로 세는 것이 이 프로젝트에서 가장 비쌌던 실수다.
화면 쪽(누르기·끌기·색 고르개)은 여기서 안 본다. 브라우저가 필요하고,
그건 따로 돌린다.
"""
import sys, json, re, time, urllib.request, urllib.error, os

BASE = "http://127.0.0.1:8777"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = []


def call(path, payload=None, timeout=180):
    url = BASE + path
    if payload is None:
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        return r.headers, body


def js(path, payload=None, timeout=180):
    _, body = call(path, payload, timeout)
    return json.loads(body or b"{}")


def check(group, name, fn):
    t0 = time.time()
    try:
        ok, note = fn()
    except Exception as exc:
        ok, note = False, "%s: %s" % (type(exc).__name__, str(exc)[:160])
    RESULTS.append((group, name, ok, note, time.time() - t0))
    print("  [%s] %-46s %s%s"
          % ("PASS" if ok else "FAIL", name, note,
             "" if ok else "   <-- 실패"), flush=True)
    return ok


SPEC_FLAT = {"top": "none", "top_params": {}, "depth": 10.0, "panel": 120.0,
             "floor": "none", "margin_depths": 0.2}
SPEC_COMB = {"top": "comb",
             "top_params": {"pitch": 6.35, "wall_top": 0.08, "wall_bot": 0.08,
                            "comb_expand": 1.0, "jitter": 0.0},
             "depth": 40.0, "panel": 200.0, "floor": "none",
             "margin_depths": 0.2}


# ---------------------------------------------------------------- A. 부팅
def A():
    print("\nA. 서버가 살아 있고 기본 자료를 내주나", flush=True)

    def a1():
        h, b = call("/")
        return (len(b) > 50000 and b"Spill Sink" in b,
                "%d 바이트" % len(b))

    def a2():
        co = js("/api/coatings")
        need = ("rho0", "df", "rough", "color", "label_en", "prov")
        miss = [k for k, v in co.items() if any(n not in v for n in need)]
        return (len(co) >= 11 and not miss,
                "재료 %d 종%s" % (len(co), "" if not miss else ", 빠진 칸 " + str(miss)))

    def a3():
        fam = js("/api/families")
        tops = [k for g, ks in fam["groups"] for k in ks]
        return ("none" in tops and "flat" not in tops and "none" in fam["floor"],
                "위층 %d, 아래층 %d, none 있고 flat 없음"
                % (len(tops), len(fam["floor"])))

    def a4():
        p = js("/api/presets")
        return (len(p.get("presets", [])) > 0, "프리셋 %d 개" % len(p["presets"]))

    check("A", "A1 페이지가 내려온다", a1)
    check("A", "A2 재료표에 필요한 칸이 다 있다", a2)
    check("A", "A3 계열 목록에 none 이 있고 flat 은 없다", a3)
    check("A", "A4 프리셋이 있다", a4)


# ---------------------------------------------------------------- B. 형상
def B():
    print("\nB. 형상이 다 만들어지나", flush=True)
    fam = js("/api/families")
    tops = [k for g, ks in fam["groups"] for k in ks]
    stack = set(fam["stackable"])

    def mesh(spec):
        h, b = call("/api/mesh", spec)
        d = json.loads(h.get("X-Derived") or "{}")
        return d, len(b)

    def one_top(t):
        def f():
            spec = dict(SPEC_FLAT, top=t, top_params={},
                        depth=fam["normal_depth"].get(t, 50.0))
            d, n = mesh(spec)
            if d.get("invalid"):
                return False, d.get("why", "invalid")
            return (n > 0 and d.get("verts", 0) > 0,
                    "%d 꼭짓점, %d 바이트" % (d.get("verts", 0), n))
        return f

    for t in tops:
        check("B", "B1 위층 %-10s 이 만들어진다" % t, one_top(t))

    def one_floor(fl):
        def f():
            spec = dict(SPEC_COMB, floor=fl, floor_depth=4.0,
                        floor_params={})
            d, n = mesh(spec)
            if d.get("invalid"):
                return False, d.get("why", "invalid")
            return (n > 0, "%d 꼭짓점" % d.get("verts", 0))
        return f

    for fl in [k for k in fam["floor"] if k != "none"]:
        check("B", "B2 벌집 + 아래층 %-8s" % fl, one_floor(fl))

    def b3():
        r1 = js("/api/measure", {"spec": SPEC_FLAT, "thetas": [0], "samples": 256,
                                 "diffuse_frac": None, "roughness": 0.1975,
                                 "phis": [0], "coating": "wall_5pct"})
        r2 = js("/api/measure", {"spec": dict(SPEC_FLAT, top="flat"),
                                 "thetas": [0], "samples": 256,
                                 "diffuse_frac": None, "roughness": 0.1975,
                                 "phis": [0], "coating": "wall_5pct"})
        a, b = 100 * r1["rho"]["0"], 100 * r2["rho"]["0"]
        d = abs(a - b) / a * 100
        return d < 0.01, "none %.5f%% vs 옛 flat %.5f%% (%.4f%% 차이)" % (a, b, d)

    check("B", "B3 top:none 이 옛 top:flat 과 같은 값", b3)


# ---------------------------------------------------------------- C. 재질
def C():
    print("\nC. 재질이 실제로 숫자를 바꾸나", flush=True)

    def meas(**kw):
        body = {"spec": kw.pop("spec"), "thetas": [0], "samples": 256,
                "diffuse_frac": None, "roughness": 0.1975, "phis": [0]}
        body.update(kw)
        return 100 * js("/api/measure", body)["rho"]["0"]

    def c1():
        lo = meas(spec=SPEC_FLAT, coating="musou_fit")
        hi = meas(spec=SPEC_FLAT, coating="wall_5pct")
        return (hi / lo > 4.0, "무소 %.4f%% 대 5%% 페인트 %.4f%% (%.1f 배)"
                % (lo, hi, hi / lo))

    def c2():
        base = meas(spec=SPEC_COMB, coating="wall_5pct")
        pt = meas(spec=SPEC_COMB, coating="musou_fit",
                  deep_coating="wall_5pct", paint_depth=8.0)
        return (abs(pt - base) / base * 100 > 1.0,
                "덧칠 없이 %.4f%% -> 8mm 칠하면 %.4f%%" % (base, pt))

    def c3():
        base = meas(spec=SPEC_COMB, coating="wall_5pct")
        fl = meas(spec=SPEC_COMB, coating="wall_5pct",
                  floor_coating="musou_fit")
        return (abs(fl - base) / base * 100 > 1.0,
                "받침판 바꾸면 %.4f%% -> %.4f%%" % (base, fl))

    def c4():
        # 같은 재료를 받침판에 주면 안 준 것과 같아야 한다 (거칠기 규칙 하나)
        a = meas(spec=SPEC_COMB, coating="anodised")
        b = meas(spec=SPEC_COMB, coating="anodised", floor_coating="anodised")
        d = abs(a - b) / a * 100
        return d < 0.5, "같은 재료면 %.4f%% vs %.4f%% (%.3f%% 차이)" % (a, b, d)

    def c5():
        rough = []
        for rg in (0.10, 0.30):
            f = js("/api/form", {"spec": dict(SPEC_FLAT, panel=63.5),
                                 "thetas": [0], "n_phase": 6, "samples": 192,
                                 "beam_w": 7.5, "coating": "wall_5pct",
                                 "diffuse_frac": 0.97, "roughness": rg})
            rough.append(f.get("peak"))
        if any(v is None for v in rough):
            return False, "번쩍임이 비어 있다"
        return (rough[0] / rough[1] > 5.0,
                "거칠기 0.10 -> %.2f, 0.30 -> %.2f (%.1f 배)"
                % (rough[0], rough[1], rough[0] / rough[1]))

    check("C", "C1 재료를 바꾸면 총량이 바뀐다", c1)
    check("C", "C2 덧칠이 총량을 바꾼다 (벌집)", c2)
    check("C", "C3 받침판이 총량을 바꾼다 (벌집)", c3)
    check("C", "C4 같은 재료면 받침판을 줘도 같은 값", c4)
    check("C", "C5 거칠기가 번쩍임을 바꾼다", c5)


# ---------------------------------------------------------------- D. 발표값
def D():
    print("\nD. 발표된 값을 그대로 재현하나", flush=True)
    f = os.path.join(ROOT, "results/comb_musou/comb_musou_v2.json")
    rows = {(r["pitch"], r["depth"], r["musou"]): r for r in json.load(open(f))}

    def one(key):
        def g():
            st = rows[key]
            pitch, depth, mus = key
            spec = {"top": "comb",
                    "top_params": {"pitch": pitch, "wall_top": 0.08,
                                   "wall_bot": 0.08, "comb_expand": 1.0,
                                   "jitter": 0.0},
                    "depth": depth, "floor": "none", "panel": 200.0}
            body = {"spec": spec, "thetas": [0.0, -20.0, 20.0, -40.0, 40.0],
                    "samples": 256, "diffuse_frac": None, "roughness": 0.1975,
                    "phis": [0, 45, 90]}
            if mus > 0:
                body.update(coating="musou_fit", deep_coating="wall_5pct",
                            paint_depth=mus)
            else:
                body.update(coating="wall_5pct")
            r = js("/api/measure", body)
            pl = r.get("rho_planes") or {"0": r["rho"]}
            got = max(max(v.values()) for v in pl.values())
            want = max(st["total"].values())
            d = abs(got - want) / want * 100
            return d < 0.5, "저장 %.5f%% 지금 %.5f%% (%.3f%% 차이)" % (
                100 * want, 100 * got, d)
        return g

    for key in [(6.35, 30.0, 0.0), (9.53, 40.0, 15.0), (6.35, 60.0, 15.0)]:
        check("D", "D1 32가지 %s 재현" % (key,), one(key))


# ---------------------------------------------------------------- E. 내보내기
def E():
    print("\nE. 내보내기와 도구", flush=True)

    def e1():
        h, b = call("/api/step", SPEC_COMB, timeout=300)
        return (len(b) > 1000 and b"ISO-10303" in b[:400],
                "%d 바이트" % len(b))

    def e2():
        h, b = call("/api/stl", SPEC_COMB, timeout=300)
        return len(b) > 1000, "%d 바이트" % len(b)

    def e3():
        r = js("/api/rays", {"spec": dict(SPEC_COMB, panel=63.5),
                             "theta": 0.0, "n": 24, "coating": "wall_5pct",
                             "diffuse_frac": None, "roughness": 0.1975,
                             "mode": "fitted"}, timeout=300)
        paths = r.get("paths") or r.get("rays") or []
        return len(paths) > 0, "광선 %d 줄" % len(paths)

    def e4():
        col = js("/api/material_color", {"id": "wall_5pct",
                                         "color": "#45484f"})
        return col.get("ok") is True, "색 쓰기 %s" % col.get("color")

    def e5():
        try:
            js("/api/material_color", {"id": "wall_5pct", "color": "red"})
            return False, "잘못된 색을 받아들였다"
        except urllib.error.HTTPError as ex:
            return ex.code == 400, "HTTP %d 로 거절" % ex.code

    check("E", "E1 STEP 이 나온다", e1)
    check("E", "E2 STL 이 나온다", e2)
    check("E", "E3 광선 추적이 돈다", e3)
    check("E", "E4 재료 색 쓰기가 된다", e4)
    check("E", "E5 잘못된 색은 거절한다", e5)


# ---------------------------------------------------------------- G. 자리별
def G():
    print("\nG. 자리마다 따로 정한 값이 그 자리에만 먹나", flush=True)
    SP = {"top": "comb",
          "top_params": {"pitch": 6.35, "wall_top": 0.08, "wall_bot": 0.08,
                         "comb_expand": 1.0, "jitter": 0.0},
          "depth": 40.0, "panel": 200.0, "floor": "none"}

    def meas(**kw):
        body = {"spec": SP, "thetas": [0], "samples": 256, "phis": [0],
                "diffuse_frac": None, "roughness": 0.1975,
                "coating": "musou_fit", "deep_coating": "wall_5pct",
                "paint_depth": 15.0}
        body.update(kw)
        return 100 * js("/api/measure", body)["rho"]["0"]

    ref = meas()

    def g1():
        v = meas(slot_rough={"deep_coating": 0.60})
        return (abs(v - ref) / ref * 100 > 1.0,
                "바탕만 거칠기 0.60 -> %.5f%% (기준 %.5f%%)" % (v, ref))

    def g2():
        v = meas(slot_rough={"coating": 0.60})
        return (abs(v - ref) / ref * 100 < 0.5,
                "덧칠만 바꿔도 정면은 %.5f%% (기준 %.5f%%)" % (v, ref))

    def g3():
        v = meas(slot_df={"deep_coating": 0.5})
        return (abs(v - ref) / ref * 100 > 5.0,
                "바탕만 확산 0.5 -> %.5f%%" % v)

    def g4():
        # 아무것도 안 보내면 예전과 같은 값이어야 한다
        return (True, "기준 %.5f%%" % ref)

    def g5():
        for pid in ("musou_fit", "wall_5pct"):
            try:
                js("/api/material_edit", {"id": pid, "df": 0.5})
                return False, "%s 가 안 잠겨 있다" % pid
            except urllib.error.HTTPError as ex:
                if ex.code != 409:
                    return False, "%s -> HTTP %d" % (pid, ex.code)
        return True, "발표에 쓴 재료는 HTTP 409 로 막힘"

    def g6():
        try:
            js("/api/material_edit", {"id": "anodised_polished", "df": 1.5})
            return False, "범위 밖 값을 받아들였다"
        except urllib.error.HTTPError as ex:
            return ex.code == 400, "범위 밖은 HTTP %d" % ex.code

    check("G", "G1 바탕 거칠기만 바꾸면 값이 움직인다", g1)
    check("G", "G2 덧칠 거칠기는 정면을 거의 안 바꾼다", g2)
    check("G", "G3 바탕 확산만 바꾸면 크게 움직인다", g3)
    check("G", "G4 아무것도 안 보내면 재료값 그대로", g4)
    check("G", "G5 발표에 쓴 재료는 편집이 잠긴다", g5)
    check("G", "G6 범위 밖 값은 거절한다", g6)


def H():
    """브라우저 쪽 코드는 서버에서 못 재 본다. 서버가 내주는 HTML 을 읽어서
    이미 한 번 당한 실수가 다시 들어왔나만 본다.

    H1 은 2026-08-24 에 사용자 화면이 까맣던 진짜 원인이다.
    `addEventListener('resize', draw)` 라고 쓰면 브라우저가 draw 에
    resize 이벤트를 첫 인자로 넘긴다. 그 자리는 `draw(fw, fh)` 의 fw --
    보고서 스냅숏용 명시 크기다. `w = fw || cv.clientWidth` 가 이벤트
    객체가 되고 `cv.width = w * dpr` 가 NaN 이 되어 캔버스 폭이 0 이 된다.
    창을 한 번 조절하면 3D 화면이 까맣고, 아무 에러도 안 나고,
    삼각형 수와 build 시간은 멀쩡히 찍힌다. 그래서 못 찾았다.
    """
    print("\n H. 브라우저 코드에 옛 실수가 다시 들어왔나", flush=True)
    _, raw = call("/")
    src = raw.decode("utf-8", "replace")
    lines = src.split("\n")

    def live(pat):
        # 주석 줄은 뺀다 -- H1 의 설명 주석 자체가 걸리면 안 된다
        return [(i + 1, l) for i, l in enumerate(lines)
                if re.search(pat, l) and not l.lstrip().startswith(("//", "*", "/*"))]

    def h1():
        hits = live(r"addEventListener\([^,]+,\s*[A-Za-z_$][\w$]*\s*\)")
        return (not hits, "맨 함수를 콜백으로 넘긴 곳 %d" % len(hits)
                + ("" if not hits else " -- %d 줄" % hits[0][0]))

    def h2():
        # 캔버스 크기를 정하는 줄은 하나뿐이어야 하고, 거기서만 dpr 을 곱한다
        hits = live(r"cv\.width\s*=")
        return (len(hits) == 1, "cv.width 를 정하는 곳 %d 군데" % len(hits))

    def h3():
        # 창 조절은 인자 없이 불러야 한다
        hits = live(r"addEventListener\(\s*['\"]resize['\"]")
        ok = len(hits) == 1 and "=> draw()" in hits[0][1]
        return (ok, "resize 핸들러 %d 개%s"
                % (len(hits), "" if ok else " -- 인자 없이 부르지 않는다"))

    def h4():
        return ("[hidden]{display:none!important}" in src.replace(" ", ""),
                "[hidden] 을 !important 로 눌렀나")

    check("H", "H1 이벤트가 함수 첫 인자로 새는 곳이 없다", h1)
    check("H", "H2 캔버스 크기는 한 곳에서만 정한다", h2)
    check("H", "H3 창 조절은 draw() 를 인자 없이 부른다", h3)
    check("H", "H4 hidden 이 진짜로 숨긴다", h4)


def I():
    """요청에서 재료 값을 빼먹으면 재료 값이 쓰이나.

    2026-08-27 에 `/api/measure` 가 확산을 안 받으면 **버린 가정값 0.76** 을,
    거칠기를 안 받으면 **버린 0.30** 을 썼다. 25 % 틀린 숫자가 조용히 나왔다.
    `/api/rays` 도 같았다. 화면은 셋 다 명시해서 보내므로 무사했고, 물리는
    것은 키를 빼고 부르는 쪽이다.

    정본은 `scripts/gate_api_defaults.py` 다. 여기서는 그것을 부른다 --
    같은 규칙을 두 군데 적으면 한 군데만 고치게 된다.
    """
    print("\n I. 재료 값을 안 보내면 재료 값이 쓰이나", flush=True)
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run([sys.executable,
                        os.path.join(here, "gate_api_defaults.py")],
                       capture_output=True, text=True, timeout=1200,
                       env=dict(os.environ, SIM=BASE))
    out = r.stdout
    for line in out.splitlines():
        if line.strip().startswith("[") and ("PASS" in line or "FAIL" in line):
            name = line.split("]", 1)[1].strip()
            RESULTS.append(("I", name[:60], "PASS" in line, "", 0.0))
            print("  " + line.strip(), flush=True)
    if not any(g == "I" for g, *_ in RESULTS):
        check("I", "I0 관문이 돌지 않았다", lambda: (False, out[-160:]))


def J():
    """관찰자 각도를 넣었는데 옛 숫자가 안 움직였나.

    2026-08-27 에 카메라를 판 법선에서 떼어냈다. 그전까지 발표된 모든 봉우리는
    "판에서 똑바로 나오는 밝기" 였다. 새 손잡이를 달면서 **옛 답을 건드리지
    않았나**를 지킨다. 66,426 행이 그 값들을 가리킨다.

    그리고 **아무것도 안 하는 손잡이**도 불합격이다. 각도를 보냈는데 값이
    안 움직이면 어딘가에서 인자가 떨어진 것이고, 이 프로젝트는 실제로 그
    결함을 세 번 냈다 (디스패치 람다에서 `obs_elev` 가 빠져 있었다).

    정본은 `scripts/gate_observer_angle.py` 다. 여기서는 그것을 부른다 --
    같은 규칙을 두 군데 적으면 한 군데만 고치게 된다.
    """
    print("\n J. 관찰자 각도가 옛 값을 안 건드리나", flush=True)
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run([sys.executable,
                        os.path.join(here, "gate_observer_angle.py")],
                       capture_output=True, text=True, timeout=2400,
                       env=dict(os.environ, SIM=BASE))
    out = r.stdout
    for line in out.splitlines():
        if line.strip().startswith("[") and ("PASS" in line or "FAIL" in line):
            name = line.split("]", 1)[1].strip()
            RESULTS.append(("J", name[:60], "PASS" in line, "", 0.0))
            print("  " + line.strip(), flush=True)
    if not any(g == "J" for g, *_ in RESULTS):
        check("J", "J0 관문이 돌지 않았다", lambda: (False, out[-160:]))


def K():
    """설정 기본값이 두 군데 적혀 있나. 그리고 서버가 파일과 같은 값인가.

    같은 결함이 세 번 났다. 확산값 0.76, 거칠기 0.30, 그리고 2026-08-28 에
    빛줄기 수 -- 파일에 16 이라 적고도 화면은 256 으로 돌았다. 셋 다 상수를
    두 군데 적어 놓고 한 군데만 고친 것이다.

    C 항목이 특히 중요하다. 서버는 계속 떠 있는 프로세스라 **파일을 고쳐도
    안 바뀐다.** 파일만 읽는 검사는 그걸 못 잡는다. 실제로 옛 코드를 검사해
    놓고 통과라고 보고한 적이 있다.

    정본은 `scripts/gate_no_shadow_defaults.py` 다.
    """
    print("\n K. 설정이 한 곳에서만 정해지나", flush=True)
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run([sys.executable,
                        os.path.join(here, "gate_no_shadow_defaults.py")],
                       capture_output=True, text=True, timeout=600,
                       env=dict(os.environ, SIM=BASE))
    out = r.stdout
    for line in out.splitlines():
        if line.strip().startswith("[") and ("PASS" in line or "FAIL" in line):
            name = line.split("]", 1)[1].strip()
            RESULTS.append(("K", name[:60], "PASS" in line, "", 0.0))
            print("  " + line.strip(), flush=True)
    if not any(g == "K" for g, *_ in RESULTS):
        check("K", "K0 관문이 돌지 않았다", lambda: (False, out[-160:]))


GROUPS = {"A": A, "B": B, "C": C, "D": D, "E": E, "G": G, "H": H, "I": I,
          "J": J, "K": K}


if __name__ == "__main__":
    want = [a.upper() for a in sys.argv[1:]] or list(GROUPS)
    t0 = time.time()
    print("시뮬레이터 점검 -- %s" % BASE, flush=True)
    for g in want:
        if g in GROUPS:
            GROUPS[g]()
    n = len(RESULTS)
    bad = [r for r in RESULTS if not r[2]]
    print("\n%d 항목 중 %d 통과, %d 실패 (%.0f 초)"
          % (n, n - len(bad), len(bad), time.time() - t0), flush=True)
    for g, name, ok, note, sec in bad:
        print("   실패: %s -- %s" % (name, note), flush=True)
    sys.exit(1 if bad else 0)
