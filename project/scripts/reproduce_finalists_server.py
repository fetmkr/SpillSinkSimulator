# -*- coding: utf-8 -*-
"""최종 후보 보고서 값을 **켜 둔 시뮬레이터 서버**로 다시 낸다. 실제 렌더.

    python3 scripts/reproduce_finalists_server.py          # 서버 8777 이 켜져 있어야 함

gate_finalists_ui_path.py 는 요청 인자만 견줬다 (렌더 없음). 이 스크립트는 같은
요청 본문(ui_body, index.html 요청 조립을 옮긴 것)을 진짜 서버의 /api/measure 와
/api/form 에 보내고, 돌아온 숫자를 results/finalists_2026_09_15.json 과 견준다.
브라우저를 돌린 것은 아니다.

견주는 것
    총량      rho_planes[방위][각도] 전부
    뭉개기    관찰자마다 smear (±40 평균), converged
    반짝임    관찰자마다 planes["0"].peak_by_stat_by_theta[빔].box
/api/form 은 요청한 판의 값을 먼저 돌려준다 (grown 은 따로). 보고서도 요청한 판 값이다.

쓰는 것: results/audit_2026_09_14/reproduce_finalists_server.json (행마다 저장, 이어 돌기 가능)
"""
import os
import sys
import json
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
import gate_finalists_ui_path as G                                  # noqa: E402

URL = "http://127.0.0.1:%s" % os.environ.get("SIM_PORT", "8777")
SRC = os.path.join(ROOT, "results", "finalists_2026_09_15.json")
OUT = os.path.join(ROOT, "results", "audit_2026_09_14",
                   "reproduce_finalists_server.json")


def call(path, body=None):
    req = urllib.request.Request(
        URL + path, data=None if body is None else json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=None).read())


def rel(a, b):
    if a is None or b is None:
        return None
    return (float(a) - float(b)) / max(abs(float(b)), 1e-15)


def compare_row(row, meas, forms):
    out = {"total": {}, "form": {}}
    for ph, pl in (row["totals"] or {}).items():
        for th, v in pl.items():
            got = ((meas.get("rho_planes") or {}).get(ph) or {}).get(th)
            out["total"]["phi%s/th%s" % (ph, th)] = {"report": v, "server": got,
                                                     "rel": rel(got, v)}
    for obs, want in row["form"].items():
        f = forms.get(obs) or {}
        pk = ((f.get("planes") or {}).get("0") or {}).get("peak_by_stat_by_theta") or {}
        e = {"smear": {"report": want.get("smear_pm40"), "server": f.get("smear"),
                       "rel": rel(f.get("smear"), want.get("smear_pm40"))},
             "converged": {"report": want.get("converged_pm40"),
                           "server": f.get("converged")},
             "box": {}}
        for th, st in (want.get("peak_by_stat_by_theta") or {}).items():
            g = (pk.get(th) or {}).get("box")
            e["box"][th] = {"report": (st or {}).get("box"), "server": g,
                            "rel": rel(g, (st or {}).get("box"))}
        out["form"][obs] = e
    rels = [abs(x["rel"]) for x in out["total"].values() if x["rel"] is not None]
    rels += [abs(e["smear"]["rel"]) for e in out["form"].values()
             if e["smear"]["rel"] is not None]
    rels += [abs(b["rel"]) for e in out["form"].values() for b in e["box"].values()
             if b["rel"] is not None]
    missing = sum(1 for x in out["total"].values() if x["server"] is None)
    missing += sum(1 for e in out["form"].values() for b in e["box"].values()
                   if b["server"] is None)
    out["max_abs_rel"] = max(rels) if rels else None
    out["missing"] = missing
    out["converged_same"] = all(e["converged"]["report"] == e["converged"]["server"]
                                for e in out["form"].values())
    return out


def main():
    data = json.load(open(SRC))
    proto = call("/api/protocol")
    state = json.load(open(OUT)) if os.path.exists(OUT) else {"rows": {}}
    state["meta"] = {"server": URL, "protocol": proto, "source": os.path.relpath(SRC, ROOT),
                     "note": "화면 요청 본문(ui_body)을 실제 서버로 보냄. 브라우저 아님."}
    # the slowest row (panel 500, smear does not converge, so the server also
    # grows the sample) goes last
    keys = sorted(data["rows"], key=lambda k: "50/높이 250" in k)
    for key in keys:
        row = data["rows"][key]
        if key in state["rows"] and "error" not in state["rows"][key]:
            continue
        print("\n[repro] %s" % key, flush=True)
        t0 = time.time()
        try:
            meas = call("/api/measure", G.ui_body(row, "measure", proto=proto))
            if "error" in meas:
                raise RuntimeError(meas["error"])
            forms = {}
            for obs in proto["observers"]:
                f = call("/api/form", G.ui_body(row, "form", obs, proto))
                if "error" in f:
                    raise RuntimeError(f["error"])
                forms["%g" % obs] = f
                print("   관찰 %g  뭉개기 %s (보고서 %s)  %.0fs" % (
                    obs, f.get("smear"), row["form"]["%g" % obs].get("smear_pm40"),
                    f.get("seconds") or 0), flush=True)
            res = compare_row(row, meas, forms)
            res["measure_conditions"] = meas.get("conditions")
            res["ignored_keys"] = meas.get("ignored_keys")
            res["form_conditions"] = forms[next(iter(forms))].get("conditions")
            res["grown"] = {o: f.get("grown_face_mm") for o, f in forms.items()}
        except Exception as exc:
            res = {"error": "%s: %s" % (type(exc).__name__, str(exc)[:300])}
        res["sec"] = round(time.time() - t0, 1)
        res["at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        state["rows"][key] = res
        json.dump(state, open(OUT, "w"), indent=1, ensure_ascii=False)
        print("[repro done] %s  최대 차 %s  빠진 값 %s  수렴 같음 %s  %s" % (
            key, res.get("max_abs_rel"), res.get("missing"),
            res.get("converged_same"), res.get("error", "")), flush=True)
    print("@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
