# -*- coding: utf-8 -*-
"""두 실행 방식이 같은 요청에 **같은 숫자**를 내나. 실제 렌더.

    python3 scripts/gate_dispatch_render.py          (몇 분, GPU)

`gate_dispatch_equivalence.py` 는 인자 전달만 가짜 함수로 봤다. 이건 서버 둘을
진짜로 띄운다.

  P  일반 Python:  python3 scripts/sim_server.py            (포트 8791)
                   측정마다 Blender 를 subprocess 로 띄워 cyc_worker 를 부른다
  B  Blender 안:   Blender --background --python sim_server.py (포트 8792)
                   측정을 자기 메인 스레드에서 돈다

사용자가 쓰는 서버(8777)는 건드리지 않는다.

같은 요청을 두 서버에 보낸다. 요청은 **기본값이 아닌 값**으로 채운다: 5 %
도료 위에 아노다이징 바닥, 도장 깊이 10 mm, 관찰자 30 도, 해상도 0.1 mm/px,
빔 5 mm, 방위 두 개. 감사 전 코드에서 P 는 이 값 대부분을 버렸다.

  A  총량 (/api/measure): P 와 B 가 같은 숫자      상대 1e-6 안
  B  뭉개기·반짝임 (/api/form): 같은 숫자           상대 1e-6 안
  C  두 서버가 적은 `conditions` 가 같다
  D  대조: 같은 요청에서 코팅만 기본값으로 바꾸면 숫자가 **달라진다**.
     안 달라지면 손잡이가 안 닿은 것이고, A/B 의 "같다" 는 아무것도 증명 못 한다.
  E  `gate_no_shadow_defaults` D 를 두 서버에 각각

허용 폭 1e-6 의 근거: 같은 요청을 같은 서버에 두 번 보내면 상대 3.1e-08 만큼
흔들린다 (`gate_observer_angle.py` 에 적힌 실측).
"""
import os
import sys
import json
import time
import subprocess
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BLENDER = os.environ.get("BLENDER_BIN",
                         "/Applications/Blender.app/Contents/MacOS/Blender")
OUT = os.path.join(ROOT, "results", "audit_2026_09_14",
                   "fix_dispatch_render.json")
PORTS = {"plain": 8791, "blender": 8792}
TOL = 1e-6
FAILED = []

SPEC = {"top": "pyramid",
        "top_params": {"pitch": 4.0, "tip_flat": 0.1, "apex_jitter": 0.0,
                       "tip_drop": 0.0},
        "depth": 22.0, "panel": 40.0, "floor": "none", "margin_depths": 0.2}
FINISH = dict(coating="wall_5pct", deep_coating="anodised", paint_depth=10.0,
              floor_coating="musou_air")
MEASURE = dict(spec=SPEC, thetas=[40.0], samples=16, phis=[0.0, 45.0],
               **FINISH)
FORM = dict(spec=SPEC, n_phase=2, samples=16, beam_w=5.0, mm_per_px=0.1,
            obs_elev=30.0, renderer="cycles", **FINISH)


def say(ok, name, note):
    print("  [%s] %-46s %s%s" % ("PASS" if ok else "FAIL", name, note,
                                 "" if ok else "   <-- 실패"), flush=True)
    if not ok:
        FAILED.append(name)


def post(port, path, body, timeout=3600):
    r = urllib.request.urlopen(urllib.request.Request(
        "http://127.0.0.1:%d%s" % (port, path), data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}), timeout=timeout)
    return json.loads(r.read())


def up(port, proc, log, limit=180):
    t0 = time.time()
    while time.time() - t0 < limit:
        if proc.poll() is not None:
            raise RuntimeError("server on %d exited; see %s" % (port, log))
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/api/coatings" % port,
                                   timeout=3)
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("server on %d did not come up; see %s" % (port, log))


def rel(a, b):
    return abs(a - b) / max(abs(b), 1e-30)


def flat(d, pre=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flat(v, pre + str(k) + "."))
    elif isinstance(d, (int, float)) and not isinstance(d, bool):
        out[pre[:-1]] = float(d)
    return out


def main():
    env = dict(os.environ)
    logs, procs = {}, {}
    try:
        for mode, port in PORTS.items():
            logs[mode] = "/tmp/simsrv/dispatch_render_%s.log" % mode
            e = dict(env, SIM_PORT=str(port))
            cmd = ([sys.executable, os.path.join(HERE, "sim_server.py")]
                   if mode == "plain" else
                   [BLENDER, "--background", "--factory-startup", "--python",
                    os.path.join(HERE, "sim_server.py")])
            procs[mode] = subprocess.Popen(cmd, env=e, cwd=ROOT,
                                           stdout=open(logs[mode], "w"),
                                           stderr=subprocess.STDOUT)
        for mode, port in PORTS.items():
            up(port, procs[mode], logs[mode])
        print("servers up: plain %d, blender %d" % (PORTS["plain"],
                                                    PORTS["blender"]))

        res = {"request_measure": MEASURE, "request_form": FORM, "runs": {}}
        for mode, port in PORTS.items():
            t0 = time.time()
            m = post(port, "/api/measure", MEASURE)
            f = post(port, "/api/form", FORM)
            res["runs"][mode] = {"measure": m, "form": f,
                                 "seconds": round(time.time() - t0, 1)}
            print("  %s: measure %s  smear %s  peak %s  (%.0fs)"
                  % (mode, m.get("rho_planes") or m.get("error"),
                     f.get("smear") if "error" not in f else f["error"][-200:],
                     f.get("peak"), time.time() - t0), flush=True)

        P, B = res["runs"]["plain"], res["runs"]["blender"]
        # A. totals
        fa, fb = flat(P["measure"].get("rho_planes")), flat(
            B["measure"].get("rho_planes"))
        worst = max((rel(fa[k], fb[k]) for k in fb if k in fa), default=None)
        say(fa and fa.keys() == fb.keys() and worst is not None
            and worst <= TOL, "A /api/measure 두 서버가 같은 숫자",
            "값 %d 개, 최대 상대차 %s" % (len(fb), worst))
        # B. form
        keys = ("smear", "peak")
        diffs = {k: rel(P["form"][k], B["form"][k]) for k in keys
                 if P["form"].get(k) is not None
                 and B["form"].get(k) is not None}
        pbs = flat(P["form"].get("planes"))
        bbs = flat(B["form"].get("planes"))
        worst_f = max((rel(pbs[k], bbs[k]) for k in bbs if k in pbs),
                      default=None)
        say(len(diffs) == 2 and max(diffs.values()) <= TOL
            and worst_f is not None and worst_f <= TOL,
            "B /api/form 두 서버가 같은 숫자",
            "smear/peak %s, 평면별 최대 %s" % (diffs, worst_f))
        # C. conditions
        cm = (P["measure"].get("conditions") == B["measure"].get("conditions"))
        cf = (P["form"].get("conditions") == B["form"].get("conditions"))
        say(cm and cf and P["form"].get("conditions"),
            "C 두 서버가 적은 실행 조건이 같다",
            "measure %s form %s; form 코팅 %s, 관찰자 %s"
            % (cm, cf, ((P["form"].get("conditions") or {}).get("coating")
                        or {}).get("id"),
               (P["form"].get("conditions") or {}).get("obs_elev_deg")))
        # D. the knob moves the number (on the plain server, the one that
        #    used to drop it)
        plain_default = post(PORTS["plain"], "/api/form",
                             dict(FORM, coating=None, deep_coating=None,
                                  paint_depth=None, floor_coating=None,
                                  obs_elev=0.0))
        res["plain_form_defaults"] = plain_default
        moved = (plain_default.get("peak") is not None and P["form"].get("peak")
                 and rel(plain_default["peak"], P["form"]["peak"]) > 0.01)
        say(bool(moved), "D 코팅·관찰자를 기본으로 바꾸면 숫자가 움직인다",
            "peak %s -> %s" % (P["form"].get("peak"),
                               plain_default.get("peak")))
        # E. the shadow-defaults gate against each live server
        for mode, port in PORTS.items():
            p = subprocess.run([sys.executable, os.path.join(
                HERE, "gate_no_shadow_defaults.py")],
                env=dict(env, SIM="http://127.0.0.1:%d" % port),
                capture_output=True, text=True, timeout=600)
            line = [ln for ln in p.stdout.splitlines() if " D " in ln]
            ok = bool(line) and "[PASS]" in line[0] and "건너뜀" not in line[0]
            say(ok, "E 설정 검사 D, %s 서버" % mode,
                line[0].strip()[:90] if line else p.stdout[-200:])
        res["failed"] = FAILED
        json.dump(res, open(OUT, "w"), indent=1)
        print("\n%d 실패 -> %s" % (len(FAILED), os.path.relpath(OUT, ROOT)))
        print("@@DONE@@")
        return 1 if FAILED else 0
    finally:
        for p in procs.values():
            p.terminate()
        for p in procs.values():
            try:
                p.wait(timeout=20)
            except Exception:
                p.kill()


if __name__ == "__main__":
    sys.exit(main())
