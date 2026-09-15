# -*- coding: utf-8 -*-
"""두 실행 방식이 같은 요청을 같은 호출로 바꾸나. 렌더러 없음, 몇 초.

    python3 scripts/gate_dispatch_equivalence.py

2026-09-14 감사가 원본 `cyc_worker.main()` 을 돌려 보였다: 일반 Python 서버가
넘기는 `form` 요청에서 코팅·도장 깊이·관찰자 각·해상도 등 열 개가 목적 함수에
안 닿았다. Blender 안에서 뜬 서버는 따로 쓴 람다로 넘겨서 닿았다. 같은 서버,
다른 답.

이 검사는 측정 함수를 가짜(spy)로 바꿔 끼우고, 기본값이 아닌 값으로 가득 채운
요청을 세 길로 보낸다.

  1  Blender 안 서버:   in_blender -> on_main -> run_op
  2  일반 Python 서버:  cyc_worker.main (stdin JSON) -> run_op
  3  HTTP 처리기:      실제 H 처리기로 /api/measure, /api/form 에 POST
                       (in_blender 는 1 과 같은 길로)

  A  세 길의 호출이 인자까지 똑같다
  B  요청에 넣은 값이 전부 호출에 닿았다 (기본값이 아닌 값이라 우연히 같을 수 없다)
  C  모르는 키를 넣으면 `ignored_keys` 에 이름이 찍힌다 (조용히 안 사라진다)
  D  옛 cyc_worker 가 실제로 버렸던 값이 이제 닿는다 (감사 dispatch_probe 와 같은 요청)

이 검사는 **인자 전달**만 본다. 같은 인자로 두 실행 방식이 같은 숫자를 내는지는
`gate_dispatch_render.py` 가 실제로 렌더해서 본다.
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
OUT = os.path.join(ROOT, "results", "audit_2026_09_14",
                   "fix_dispatch_equivalence.json")

with contextlib.redirect_stdout(io.StringIO()):
    import sim_server as S                                          # noqa: E402
import cyc_worker as W                                              # noqa: E402

FAILED = []
CALLS = []
ORIG = {n: getattr(S, n) for n in ("measure", "form", "measure_lambert",
                                   "form_lambert")}


def say(ok, name, note):
    print("  [%s] %-50s %s%s" % ("PASS" if ok else "FAIL", name, note,
                                 "" if ok else "   <-- 실패"), flush=True)
    if not ok:
        FAILED.append(name)


def spy(name):
    sig = inspect.signature(ORIG[name])

    def f(*a, **kw):
        b = sig.bind(*a, **kw)
        b.apply_defaults()
        CALLS.append((name, dict(b.arguments)))
        if name == "measure":
            planes = {"0": {"0": 0.01}}
            return (planes, {"spy": True}) if kw.get("with_conditions") \
                else planes
        if name == "measure_lambert":
            return 0.01
        if name == "form":
            return {"converged": True, "smear": 1.0, "face_mm": 40.0}
        return {"smear": 1.0, "head_on": 0.1}
    return f


SPEC = {"top": "comb", "depth": 40, "panel": 100, "floor": "none",
        "top_params": {"pitch": 9.53}}
# EVERY VALUE IS NOT A DEFAULT, so reaching the call cannot be a coincidence
REQ = {
    "measure": dict(spec=SPEC, thetas=[40.0, -20.0], diffuse_frac=0.91,
                    roughness=0.2, samples=48, coating="wall_5pct",
                    deep_coating="anodised", paint_depth=15.0, deep_until=38.0,
                    paint_fade=3.0, phis=[45.0, 90.0],
                    floor_coating="musou_air",
                    slot_df={"coating": 0.92}, slot_rough={"coating": 0.3},
                    cycles_seed=7),
    "form": dict(spec=SPEC, thetas=[40.0], n_phase=5, samples=24, beam_w=9.0,
                 phis=[45.0, 90.0], mm_per_px=0.05, floor_coating="musou_air",
                 diffuse_frac=0.91, coating="wall_5pct",
                 deep_coating="anodised", paint_depth=15.0, roughness=0.2,
                 slot_df={"coating": 0.92}, slot_rough={"coating": 0.3},
                 obs_elev=40.0, cycles_seed=7),
    "lambert": dict(spec=SPEC, theta=35.0, rho=0.03, samples=40),
    "form_lambert": dict(spec=SPEC, rho=0.03, n_phase=5, samples=24,
                         thetas=[-30.0, 30.0], beam_w=9.0),
}
FN = {"measure": "measure", "form": "form", "lambert": "measure_lambert",
      "form_lambert": "form_lambert"}
# request key -> the function's parameter name, where they differ
RENAME = {"lambert": {}, "measure": {}, "form": {}, "form_lambert": {}}


def install():
    for n in ORIG:
        setattr(S, n, spy(n))


def via_in_blender(op, req):
    S.IN_BLENDER = True
    S.on_main = lambda fn, *a, **kw: fn(*a, **kw)
    n0 = len(CALLS)
    out = S.in_blender(op, **req)
    return CALLS[n0:], out


def via_worker(op, req):
    n0 = len(CALLS)
    old_in, old_out = sys.stdin, sys.stdout
    sys.stdin = io.StringIO(json.dumps(dict(req, op=op)))
    buf = io.StringIO()
    sys.stdout = buf
    try:
        W.main()
    finally:
        sys.stdin, sys.stdout = old_in, old_out
    line = [ln for ln in buf.getvalue().splitlines() if "@@RESULT@@" in ln][-1]
    return CALLS[n0:], json.loads(line.split("@@RESULT@@", 1)[1])


def norm(v):
    return json.loads(json.dumps(v))


def main():
    install()
    res = {"ops": {}}
    print("A/B  세 길이 같은 호출을 만들고, 요청 값이 전부 닿나")
    for op, req in REQ.items():
        ca, oa = via_in_blender(op, req)
        cb, ob = via_worker(op, req)
        a = norm(ca[-1][1]) if ca else None
        b = norm(cb[-1][1]) if cb else None
        same = a == b and len(ca) == len(cb) == 1
        say(same, "A %s: in-process == worker" % op,
            "호출 %d / %d" % (len(ca), len(cb)))
        missing = []
        for k, v in req.items():
            p = RENAME[op].get(k, k)
            got = (a or {}).get(p)
            if isinstance(v, list) and op == "form_lambert" and p == "thetas":
                got = list(got) if got is not None else None
            if norm(got) != norm(v):
                missing.append("%s: 보냄 %s 닿음 %s" % (k, v, got))
        say(not missing, "B %s: 요청 %d 개 값이 전부 닿았다" % (op, len(req)),
            ("빠짐 " + " | ".join(missing))[:140] if missing else "")
        res["ops"][op] = {"call": a, "missing": missing,
                          "ignored_in": oa.get("ignored_keys"),
                          "ignored_worker": ob.get("ignored_keys")}

    print("\nC  모르는 키는 이름이 찍히나")
    _, o = via_in_blender("form", dict(REQ["form"], bogus_knob=1.0,
                                       renderer="cycles"))
    say(o.get("ignored_keys") == ["bogus_knob"],
        "C 모르는 키 bogus_knob 이 ignored_keys 에", str(o.get("ignored_keys")))

    print("\nD  감사가 버려진다고 보인 값이 이제 닿나")
    probe = json.load(open(os.path.join(ROOT, "results", "audit_2026_09_14",
                                        "dispatch_probe.json")))
    for rec in probe:
        op = rec["op"]
        req = {k: v for k, v in rec["request"].items() if k != "op"}
        calls, out = via_worker(op, req)
        call = norm(calls[-1][1])
        allowed = S._OP_KEYS[op]
        lost = [k for k in req if k in allowed and norm(call.get(k)) != norm(req[k])]
        say(not lost, "D %s: 감사 요청의 %d 개 키가 worker 에서 닿는다"
            % (op, len([k for k in req if k in allowed])),
            ("안 닿음 " + ", ".join(lost)) if lost else
            "모르는 키 %s" % out.get("ignored_keys"))
        res["ops"]["audit_" + op] = {"ignored": out.get("ignored_keys"),
                                     "lost": lost}

    print("\nE  HTTP 처리기가 요청을 통째로 넘기나 (/api/measure, /api/form)")
    from http.server import ThreadingHTTPServer
    S.IN_BLENDER = True
    S.on_main = lambda fn, *a, **kw: fn(*a, **kw)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), S.H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    for path, op in (("/api/measure", "measure"), ("/api/form", "form")):
        n0 = len(CALLS)
        body = dict(REQ[op], renderer="cycles")
        with contextlib.redirect_stdout(io.StringIO()):
            r = json.loads(urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:%d%s" % (port, path),
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"}),
                timeout=60).read())
        calls = CALLS[n0:]
        call = norm(calls[-1][1]) if calls else {}
        want = dict(REQ[op])
        if op == "form":
            want["thetas"] = None       # this endpoint always reads protocol angles
        lost = [k for k, v in want.items() if norm(call.get(k)) != norm(v)]
        say(calls and not lost and r.get("ignored_keys") == [],
            "E %s: 처리기 -> 호출에 전부 닿음" % path,
            ("안 닿음 " + ", ".join(lost)) if lost
            else "ignored %s" % r.get("ignored_keys"))
        res["ops"]["http_" + op] = {"lost": lost,
                                    "ignored": r.get("ignored_keys")}
    srv.shutdown()

    res["failed"] = FAILED
    json.dump(res, open(OUT, "w"), indent=1)
    print("\n%d 실패 -> %s" % (len(FAILED), os.path.relpath(OUT, ROOT)))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
