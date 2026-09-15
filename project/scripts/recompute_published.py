# -*- coding: utf-8 -*-
"""발표된 설계 전부를 지금 규약으로 다시 잰다. 세 축, 설계 하나에 한 줄.

    zsh scripts/run_batch.sh scripts/recompute_published.py recompute

무엇을 다시 재나
----------------
`sim_server.published()` 가 결과 CSV 51,567 행을 설계별로 묶은 1,643 개. 각
설계의 파라미터는 발표 행에 적힌 그대로 쓴다 (판 크기·여백·깊이 전부).

바뀌는 것은 측정 규약뿐이다.
    코팅 트리    reciprocal (옛 결과는 fresnel_mix)
    재료        기본 무소 musou_fit2, 모든 면에 한 벌
                (옛 결과는 스크립트마다 확산 0.76 / 0 / 1 봉투, 또는 다른 재료)
    총량        hemi_view, 입사 0 / +-20 / +-40, 방위 0, 빛줄기 256
    뭉개기·반짝임  form_buildable.run_case 규약값 그대로 (위상 16, sobol, 16 빛줄기,
                빔 7.5 mm, 0.215 mm/px, 가장 넓은 창 판정, box 봉우리)
    대조판      2026-09-15 부터 필드 밖에 놓인다

**옛 값과 나란히 놓을 때 주의.** 옛 `worst_rho` 는 재료 봉투의 최악이고 새 값은
재료 한 벌이다. 그래서 절대값 차이는 재료 차이를 섞는다. 이 스크립트가 끝에
보여 주는 것은 **순위가 살아남는가** (스피어만 순위 상관) 와, 가족별로 가장
어두운 설계가 바뀌었는가다.

이어서 돌 수 있다. 결과 파일에 이미 있는 설계는 건너뛴다. 실패한 설계는 오류와
함께 적고 넘어간다.

결과: results/recompute_published_2026_09_15.json (새 폴더를 만들지 않는다)
"""
import os
import sys
import json
import time
import math
import dataclasses
import importlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS             # noqa: E402
import form_buildable as FB         # noqa: E402
import blender_render as BR         # noqa: E402
import form_metrics as FM           # noqa: E402
import rig_v2 as R2                 # noqa: E402
from cone3d_sweep import COAT       # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "recompute_published_2026_09_15.json")
TMP = "/tmp/simsrv/recompute"
THETAS_T = [0.0, -20.0, -40.0, 20.0, 40.0]
TOTAL_SPP = 256

# 1D families the rig_v2 table does not list
EXTRA = [("ridge", "profile_ridge", "RidgeParams"),
         ("scatter", "profile_scatter", "ScatterParams"),
         ("slat", "profile2d", "PanelParams")]


def family_of(params):
    try:
        return R2._infer_family(dict(params))
    except Exception as first:
        for fam, mod, cls in EXTRA:
            try:
                C = getattr(importlib.import_module(mod), cls)
            except Exception:
                continue
            if not set(params) - {f.name for f in dataclasses.fields(C)}:
                return fam, dict(params)
        raise first


def spearman(a, b):
    def ranks(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        for k, i in enumerate(order):
            r[i] = float(k)
        return r
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = math.sqrt(sum((x - ma) ** 2 for x in ra))
    vb = math.sqrt(sum((y - mb) ** 2 for y in rb))
    return cov / (va * vb) if va and vb else float("nan")


def one(i, e, coat):
    fam, prm = family_of(e["params"])
    row = {"family": fam}
    # --- totals, the same cfg shape sim_server.measure builds ---
    cfg = {"tag": "rc_%04d" % i, "family": fam, "out_dir": TMP,
           "results_dir": TMP, "samples": TOTAL_SPP, "res_x": 480,
           "res_y": 220, "gpu": True,
           "spec_roughness": float(coat["roughness"]),
           "coating": {"body": coat["body"], "spec_scale": coat["spec_scale"],
                       "roughness": float(coat["roughness"])},
           "params": dict(prm),
           "renders": [{"mode": "hemi_view", "theta": t} for t in THETAS_T]}
    cfg.update({k: v for k, v in COAT.items() if k != "spec_roughness"})
    cfg["material_mode"] = "coating"
    t0 = time.time()
    res = BR.run(cfg)
    row["totals"] = {"%+.0f" % r["theta"]: r["panel"]["mean"]
                     for r in res["modes"].values()}
    row["control"] = [r["control"]["mean"] for r in res["modes"].values()]
    row["worst_rho"] = max(row["totals"].values())
    row["total_sec"] = round(time.time() - t0, 1)
    # --- smear and head-on, form_buildable's own run ---
    pitch = (prm.get("pitch") or prm.get("pitch_mean") or prm.get("width_mean")
             or 6.5)
    entry = {"tag": "rcf_%04d" % i, "family": fam, "topology": fam,
             "process": "recompute", "params": dict(prm),
             "pitch": float(pitch),
             "coating": {"body": coat["body"], "spec_scale": coat["spec_scale"]},
             "roughness": float(coat["roughness"])}
    t0 = time.time()
    FB.PROGRESS_CB = None
    rec = FB.run_case(entry)
    t = rec["thetas"]
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    row["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b and a["rms_control_mm"] and b["rms_control_mm"]
                    else None)
    row["smear_converged"] = bool(a and b and a["converged"] and b["converged"])
    row["smear_first_agreement_reversed"] = [
        ((x or {}).get("smear_verdict") or {}).get("first_agreement_reversed")
        for x in (a, b)]
    row["head_on"] = {s: (z or {}).get("peak_ratio_%s_mean" % s)
                      for s in ("box", "p99", "max")}
    row["form_face_mm"] = rec.get("face_h")
    row["control_x0_mm"] = rec.get("control_x0_mm")
    row["form_sec"] = round(time.time() - t0, 1)
    return row


def main():
    os.makedirs(TMP, exist_ok=True)
    pub = SS.published()
    coat = SS._coat(SS.DEFAULT_COATING)
    state = {"meta": {}, "rows": {}}
    if os.path.exists(OUT):
        state = json.load(open(OUT))
    state["meta"] = {
        "date": "2026-09-15", "n_published_designs": len(pub),
        "coating": SS._finish_record(coat), "coating_model": BR.COATING_MODEL,
        "totals": {"thetas": THETAS_T, "phi": 0.0, "samples": TOTAL_SPP,
                   "mode": "hemi_view"},
        "form": {"samples": FM.SAMPLES, "n_phase": FM.N_PHASE,
                 "beam_w": FM.STRIPE_W, "mm_per_px": FM.MM_PER_PX,
                 "peak_stat": FM.PEAK_STAT, "peak_box_mm": FM.PEAK_BOX_MM,
                 "beam_pos": FM.BEAM_POS, "thetas": list(FB.THETAS)}}
    t_all = time.time()
    n_new = 0
    for i, e in enumerate(pub):
        key = "%s|%s" % (e["source"], e["design"])
        if key in state["rows"]:
            continue
        row = {"source": e["source"], "design": e["design"],
               "old_worst_rho": e.get("worst_rho"), "old_n": e.get("n"),
               "params": e["params"]}
        try:
            row.update(one(i, e, coat))
        except Exception as exc:
            row["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:300])
        state["rows"][key] = row
        n_new += 1
        json.dump(state, open(OUT, "w"), indent=1, ensure_ascii=False)
        done = len(state["rows"])
        el = time.time() - t_all
        print("[%4d/%4d] %-40s %s  worst %s  smear %s  head-on box %s  (%.0fs, "
              "avg %.0fs/design this run)"
              % (done, len(pub), key[:40], row.get("family", "?"),
                 row.get("worst_rho"), row.get("smear"),
                 (row.get("head_on") or {}).get("box"),
                 (row.get("total_sec") or 0) + (row.get("form_sec") or 0),
                 el / max(n_new, 1)), flush=True)

    ok = [r for r in state["rows"].values()
          if r.get("worst_rho") is not None and r.get("old_worst_rho") is not None]
    rho = spearman([r["old_worst_rho"] for r in ok],
                   [r["worst_rho"] for r in ok]) if len(ok) > 2 else None
    by_src = {}
    for r in ok:
        by_src.setdefault(r["source"], []).append(r)
    src_summary = {}
    for s, rs in by_src.items():
        old_best = min(rs, key=lambda r: r["old_worst_rho"])["design"]
        new_best = min(rs, key=lambda r: r["worst_rho"])["design"]
        src_summary[s] = {"n": len(rs), "old_darkest": old_best,
                          "new_darkest": new_best,
                          "same": old_best == new_best,
                          "spearman": (spearman([r["old_worst_rho"] for r in rs],
                                                [r["worst_rho"] for r in rs])
                                       if len(rs) > 2 else None)}
    state["summary"] = {"n_rows": len(state["rows"]), "n_ok": len(ok),
                        "n_error": sum(1 for r in state["rows"].values()
                                       if r.get("error")),
                        "spearman_all": rho, "by_source": src_summary}
    json.dump(state, open(OUT, "w"), indent=1, ensure_ascii=False)
    print("\n설계 %d, 성공 %d, 실패 %d, 전체 순위 상관 %s"
          % (len(state["rows"]), len(ok), state["summary"]["n_error"], rho),
          flush=True)
    for s, v in sorted(src_summary.items()):
        print("  %-40s n %4d  가장 어두운 설계 %s  순위상관 %s"
              % (s, v["n"], "그대로" if v["same"] else
                 "%s -> %s" % (v["old_darkest"], v["new_darkest"]),
                 v["spearman"]), flush=True)
    print(OUT)
    print("@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
