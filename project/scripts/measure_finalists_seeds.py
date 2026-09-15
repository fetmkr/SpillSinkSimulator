# -*- coding: utf-8 -*-
"""최종 후보 14 개를 무작위 씨앗 2 개로 더 잰다. 켜 둔 시뮬레이터 서버로, 화면 요청 모양 그대로.

    python3 scripts/measure_finalists_seeds.py          # 서버 8777 (씨앗 칸이 있는 새 코드)

사용자 규칙 (2026-09-15): 결론은 원래 씨앗(0)에 무작위 씨앗 두 개를 더해 세 번 잰
값으로 낸다. 같은 씨앗으로 다시 재면 같은 빛줄기를 다시 쏘는 것이라 흔들림이 0 으로
보인다 (reproduce_finalists_server.py 가 0.00001 % 로 맞은 이유).

씨앗은 처음 돌 때 `secrets` 로 한 번 뽑아 결과 파일에 적는다. 이어 돌면 같은 씨앗을 쓴다.
씨앗 0 값은 results/finalists_2026_09_15.json 에 이미 있으니 다시 재지 않는다.
각 행이 서버가 실제로 쓴 씨앗(conditions.cycles_seed)을 같이 적어, 씨앗 칸이
안 닿았으면 (옛 서버) 멈춘다.

쓰는 것: results/finalists_2026_09_15_seeds.json
"""
import os
import sys
import json
import time
import secrets
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
import gate_finalists_ui_path as G                                  # noqa: E402

URL = "http://127.0.0.1:%s" % os.environ.get("SIM_PORT", "8777")
SRC = os.path.join(ROOT, "results", "finalists_2026_09_15.json")
OUT = os.path.join(ROOT, "results", "finalists_2026_09_15_seeds.json")


def call(path, body=None):
    req = urllib.request.Request(
        URL + path, data=None if body is None else json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=None).read())


def form_summary(f):
    p = (f.get("planes") or {}).get("0") or {}
    return {"smear_pm40": f.get("smear"), "converged_pm40": f.get("converged"),
            "smear_by_theta": p.get("smear_by_theta"),
            "converged_by_theta": p.get("converged_by_theta"),
            "peak_by_stat_by_theta": p.get("peak_by_stat_by_theta"),
            "grown_face_mm": f.get("grown_face_mm"),
            "cycles_seed": (f.get("conditions") or {}).get("cycles_seed"),
            "sec": f.get("seconds")}


def main():
    data = json.load(open(SRC))
    proto = call("/api/protocol")
    if os.path.exists(OUT):
        state = json.load(open(OUT))
    else:
        seeds = []
        while len(seeds) < 2:
            s = 1 + secrets.randbelow(2 ** 31 - 2)
            if s not in seeds:
                seeds.append(s)
        state = {"meta": {"seeds": seeds, "base_seed": 0,
                          "drawn_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                          "rule": "원래 씨앗 0 + 무작위 2 개, 차이가 흔들림보다 클 때만 결론",
                          "server": URL, "protocol": proto,
                          "path": "화면 요청 본문(ui_body)을 실제 서버로 보냄"},
                 "rows": {}}
        json.dump(state, open(OUT, "w"), indent=1, ensure_ascii=False)
    seeds = state["meta"]["seeds"]
    print("씨앗 %s" % seeds, flush=True)
    keys = sorted(data["rows"], key=lambda k: "50/높이 250" in k)
    for seed in seeds:
        for key in keys:
            row = data["rows"][key]
            slot = "%s @ %d" % (key, seed)
            if slot in state["rows"] and "error" not in state["rows"][slot]:
                continue
            print("\n[seed] %s" % slot, flush=True)
            t0 = time.time()
            rec = {"key": key, "seed": seed}
            try:
                meas = call("/api/measure",
                            G.ui_body(row, "measure", proto=proto, seed=seed))
                if "error" in meas:
                    raise RuntimeError(meas["error"])
                got = (meas.get("conditions") or {}).get("cycles_seed")
                if got != seed:
                    raise RuntimeError("서버가 씨앗 %s 를 썼다 (보낸 것 %s). "
                                       "옛 서버인가?" % (got, seed))
                planes = meas["rho_planes"]
                rec["totals"] = planes
                rec["worst_total"] = max(v for pl in planes.values()
                                         for v in pl.values())
                rec["form"] = {}
                for obs in proto["observers"]:
                    f = call("/api/form", G.ui_body(row, "form", obs, proto, seed))
                    if "error" in f:
                        raise RuntimeError(f["error"])
                    s = form_summary(f)
                    if s["cycles_seed"] != seed:
                        raise RuntimeError("form 씨앗 %s != %s" % (s["cycles_seed"], seed))
                    rec["form"]["%g" % obs] = s
                    print("   관찰 %g  뭉개기 %s (씨앗0 %s)" % (
                        obs, s["smear_pm40"],
                        row["form"]["%g" % obs].get("smear_pm40")), flush=True)
            except Exception as exc:
                rec["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:300])
            rec["sec"] = round(time.time() - t0, 1)
            rec["measured_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            state["rows"][slot] = rec
            json.dump(state, open(OUT, "w"), indent=1, ensure_ascii=False)
            print("[seed done] %s  총량 %s (씨앗0 %s)  %s" % (
                slot, rec.get("worst_total"), row.get("worst_total"),
                rec.get("error", "")), flush=True)
            if "error" in rec and "옛 서버" in rec["error"]:
                print("@@STOP@@ 씨앗 칸이 서버에 안 닿음", flush=True)
                return 2
    print("@@DONE@@", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
