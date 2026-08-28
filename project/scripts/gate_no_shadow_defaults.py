# -*- coding: utf-8 -*-
"""설정 기본값이 두 군데 적혀 있나. 한 군데만 고치면 조용히 어긋난다.

**규칙: 설정의 기본값은 딱 한 곳에만 적는다.** 그 한 곳은 그 설정이 사는
모듈이다 (`form_buildable`). 다른 파일은 값을 안 적고 거기서 읽는다.

이 결함이 세 번 나왔다
--------------------
1. 2026-08-27 `/api/measure` 가 확산을 안 받으면 **버린 값 0.76** 을,
   거칠기는 **버린 0.30** 을 썼다. 재료 파일은 0.99 로 고쳐졌는데 서버가
   옛 숫자를 따로 들고 있었다. 25 % 틀린 값이 조용히 나왔다.
   (`gate_api_defaults.py` 가 그 자리를 지킨다.)
2. 같은 날 `/api/rays` 도 같았다.
3. 2026-08-28 `form_buildable.SAMPLES` 를 512 에서 16 으로 내렸는데
   화면은 여전히 256 으로 돌았다. `sim_server.form` 이
   `int(samples or 256)` 으로 자기 숫자를 들고 있었다. 실측으로 확인했다 --
   설정에는 16 이라 적혀 있고 결과에는 `samples 256` 이 찍혔다.

세 번 다 같은 꼴이다. **상수를 두 군데 적어 놓고 한 군데만 고쳤다.**

무엇을 보나
----------
소스를 읽어서, 모듈 상수와 같은 뜻인데 숫자를 따로 적은 자리를 찾는다.
렌더를 안 하므로 몇 초면 끝난다.

    A  sim_server 에 `or <숫자>` 꼴로 박힌 기본값이 없나
    B  정본 상수(창 크기, 빔 너비)가 여러 파일에 따로 적혀 있지 않나
    C  화면이 요청 본문에 설정 숫자를 적어 보내지 않나
    D  살아 있는 서버가 파일과 같은 값을 들고 있나 (서버가 떠 있을 때만)

D 가 필요한 이유는, 서버가 계속 떠 있는 프로세스라 **파일을 고쳐도 안
바뀌기 때문이다.** 2026-08-28 에 코드를 고치고 검사를 돌려 통과를 봤는데
옛 코드를 검사한 것이었다. 파일만 보는 검사는 그걸 못 잡는다.

    python3 scripts/gate_no_shadow_defaults.py
"""
import os
import re
import io
import sys
import json
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get("SIM", "http://127.0.0.1:8777")
FAILED = []

# 모듈 상수와 같은 뜻인 요청 인자들. 여기 있는 이름 옆에 숫자가 박혀 있으면
# 그게 그림자 기본값이다.
SHADOWED = {
    "n_phase": ("form_buildable.py", "N_PHASE"),
    "samples": ("form_buildable.py", "SAMPLES"),
    "beam_w": ("form_buildable.py", "STRIPE_W"),
}


def read(path):
    return io.open(os.path.join(HERE, path), encoding="utf-8").read()


def const(path, name):
    m = re.search(r"^%s\s*=\s*([^\n#]+)" % re.escape(name), read(path), re.M)
    return m.group(1).strip() if m else None


def check(name, fn):
    try:
        ok, note = fn()
    except Exception as exc:
        ok, note = False, "%s: %s" % (type(exc).__name__, str(exc)[:130])
    print("  [%s] %-44s %s%s" % ("PASS" if ok else "FAIL", name, note,
                                 "" if ok else "   <-- 실패"), flush=True)
    if not ok:
        FAILED.append(name)


def a_no_or_number():
    """숫자가 박힌 기본값을 찾는다. 파이썬이 기본값을 적는 꼴 두 가지를 다 본다.

        n_phase or 6                 `or` 꼴
        req.get("samples", 256)      `.get` 두 번째 인자 꼴

    처음에는 `or` 꼴만 봤다. 그래서 `.get` 꼴 다섯 곳을 놓쳤고, 그 중 하나가
    총량 단추가 쓰는 빛줄기 64 였다. 검사기가 놓치면 없는 것이 된다.
    """
    pat = [r"%s[\"')\s]*\s+or\s+\d",                     # or 꼴
           r"get\(\s*[\"']%s[\"']\s*,\s*[\d.]"]          # .get 꼴
    bad = []
    for fn in ("sim_server.py",):
        for i, ln in enumerate(read(fn).split("\n"), 1):
            if ln.lstrip().startswith("#"):
                continue
            for key in SHADOWED:
                if any(re.search(p % re.escape(key), ln) for p in pat):
                    bad.append("%s:%d %s" % (fn, i, ln.strip()[:56]))
    return (not bad,
            "그림자 기본값 %d 곳%s"
            % (len(bad), ("  " + " | ".join(bad[:3])) if bad else ""))


# 이름 -> 그 값이 살아야 할 단 한 파일. `form_metrics` 는 bpy 가 없어도
# 열리므로 블렌더 쪽과 Mitsuba 쪽이 둘 다 읽을 수 있다.
OWNER = {
    "MEAS_INSET_X": "form_metrics.py",
    "MEAS_INSET_Z": "form_metrics.py",
    "STRIPE_W": "form_metrics.py",
}


def b_defined_once():
    """정본으로 정한 이름이 다른 파일에도 대입돼 있나.

    검사 파일과 훑기 파일은 뺀다. 거기서는 일부러 다른 값을 넣어 보는 것이
    실험이다 (`mts_worker` 가 창을 0.0 으로 두고 온 판을 재는 것처럼).
    실제로 재는 길에 있는 파일만 본다.
    """
    core = ("blender_render.py", "form_buildable.py", "form_metrics.py",
            "mts_form.py", "crosscheck_mitsuba.py", "sim_server.py")
    bad = []
    for name, owner in sorted(OWNER.items()):
        for fn in core:
            if fn == owner:
                continue
            if re.search(r"^%s\s*=" % re.escape(name), read(fn), re.M):
                bad.append("%s in %s" % (name, fn))
    return (not bad,
            "정본 밖에 적힌 곳 %d%s"
            % (len(bad), ("  " + " | ".join(bad)) if bad else ""))


def d_ui_sends_no_numbers():
    """화면이 요청에 설정 숫자를 적어 보내지 않나.

    2026-08-28 에 화면이 정확히 이걸 했다 -- `n_phase: 6, samples: 256` 을
    본문에 적어 보냈다. 서버 쪽을 아무리 고쳐도 화면은 256 으로 돌았다.
    설정은 서버가 소스에서 읽어야 하고, 화면은 안 보내야 한다.
    """
    path = os.path.join(os.path.dirname(HERE), "sim", "index.html")
    bad = []
    for i, ln in enumerate(io.open(path, encoding="utf-8").read().split("\n"),
                           1):
        if ln.lstrip().startswith("//"):
            continue
        for key in ("n_phase", "samples"):
            if re.search(r"%s\s*:\s*\d" % re.escape(key), ln):
                bad.append("index.html:%d %s" % (i, ln.strip()[:56]))
    return (not bad,
            "화면이 적어 보내는 곳 %d%s"
            % (len(bad), ("  " + " | ".join(bad[:3])) if bad else ""))


def c_server_matches_file():
    """살아 있는 서버가 파일과 같은 값을 들고 있나. 서버가 떠 있을 때만."""
    # 설정은 `/api/mesh` 응답의 `X-Derived` 머리글에 실려 온다. 화면 오른쪽
    # 표를 채우는 바로 그 값이라, 이걸 보면 화면이 무엇으로 도는지 알 수 있다.
    try:
        r = urllib.request.Request(
            BASE + "/api/mesh", data=json.dumps({
                "top": "none", "top_params": {}, "depth": 10.0,
                "panel": 120.0, "floor": "none",
                "margin_depths": 0.2}).encode(),
            headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(r, timeout=120)
        got = json.loads(resp.headers.get("X-Derived") or "{}")
    except Exception as exc:
        return True, "서버가 안 떠 있다 -- 건너뜀 (%s)" % type(exc).__name__
    m = (got.get("rig") or got).get("method") or {}
    if not m:
        return False, "서버가 method 를 안 준다 -- 옛 코드일 수 있다"
    want = {"samples": const("form_buildable.py", "SAMPLES"),
            "n_phase": const("form_buildable.py", "N_PHASE"),
            "peak_stat": const("form_buildable.py", "PEAK_STAT"),
            "beam_pos": const("form_buildable.py", "BEAM_POS"),
            "stripe_w": const("form_metrics.py", "STRIPE_W"),
            "inset_x": const("form_metrics.py", "MEAS_INSET_X"),
            "inset_z": const("form_metrics.py", "MEAS_INSET_Z")}
    off = []
    for k, v in sorted(want.items()):
        if v is None:
            continue
        a, b = m.get(k), v.strip('"\'')
        try:
            # 0.20 과 0.2 는 같은 값이다. 글자로 견주면 틀린 경보가 난다.
            same = abs(float(a) - float(b)) < 1e-9
        except (TypeError, ValueError):
            same = str(a).strip('"\'') == b
        if not same:
            off.append("%s 파일 %s 서버 %s" % (k, b, a))
    return (not off, "어긋남 %d 곳%s"
            % (len(off), ("  " + " | ".join(off)) if off else ""))


if __name__ == "__main__":
    print("설정 기본값이 두 군데 적혀 있나\n", flush=True)
    check("A sim_server 에 숫자 박힌 기본값이 없다", a_no_or_number)
    check("B 정본 상수는 한 파일에만 적혀 있다", b_defined_once)
    check("C 화면이 설정 숫자를 적어 보내지 않는다", d_ui_sends_no_numbers)
    check("D 살아 있는 서버가 파일과 같은 값이다", c_server_matches_file)
    print("\n4 항목 중 %d 실패" % len(FAILED), flush=True)
    if FAILED:
        print("실패: %s" % ", ".join(FAILED), flush=True)
        print("설정을 한 곳에서만 정하고 나머지는 거기서 읽어야 한다.",
              flush=True)
    print("@@DONE@@", flush=True)
    sys.exit(1 if FAILED else 0)
