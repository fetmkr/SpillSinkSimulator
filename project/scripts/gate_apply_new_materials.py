# -*- coding: utf-8 -*-
"""정정된 재질을 실제 설계에 넣고, 옛 값과 나란히 놓는다.

바뀐 것 (2026-08-22 밤):
    5 % 무광 페인트   확산 0.97 -> 0.99      α 0.09 -> 0.039
    무소             확산 0.99 -> 0.993     α 0.09 -> 0.039
확산은 DePoy 2014 그림6 의 퍼센트 축을 분수로 읽은 오독을 고친 것이고,
α 는 MERL paint-black (Ngan 2005) 실측 맞춤값이다. 렌더러 슬라이더는
제곱돼서 α 가 되므로 슬라이더에는 √α 를 넣는다.

**먼저 옛 값으로 돌려서 저장된 32가지 숫자를 재현하는지 본다.**
재현이 안 되면 이 비교는 아무 뜻이 없다. 검사기부터 검사한다.

PRE-REGISTERED:
  V0  옛 값 팔은 results/comb_musou/comb_musou.json 을 0.5 % 안에서 재현한다.
      못 하면 여기서 멈추고 아무 비교도 안 낸다.
  V1  반사 총량은 설계마다 몇 % 안에서만 움직인다. 순위는 안 뒤집힌다.
  V2  정면 반짝임은 내려간다. 옛 α 0.09 가 새 α 0.039 보다 무디기 때문이다.
      민판에서는 1.90 -> 2.64 로 오르고, 구조물에서는 다르게 움직일 수 있다.
  V3  민판의 반짝임은 1 + (1-df)/(4α²) 과 맞고, 구조물은 안 맞는다.
      구조물의 반짝임에는 여러 번 튕긴 빛이 섞이기 때문이다. 그 차이가
      '구조가 반짝임에 얼마나 기여하나' 의 답이다.
"""
import os, sys, json, math, time
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = "/tmp/simsrv/applynew"
os.makedirs(OUT, exist_ok=True)
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
SPP = 256
PANEL = 200.0
FOIL = 0.08
STORED = "results/comb_musou/comb_musou.json"

# 옛 값 / 새 값. slider 는 렌더러에 넘기는 값(=√α).
OLD = {"paint_df": 0.97, "musou_df": 0.99,  "slider": 0.30}
NEW = {"paint_df": 0.99, "musou_df": 0.993, "slider": math.sqrt(0.039)}


def comb(pitch, depth, musou):
    spec = {"top": "comb",
            "top_params": {"pitch": pitch, "wall_top": FOIL, "wall_bot": FOIL,
                           "comb_expand": 1.0, "jitter": 0.0},
            "depth": depth, "floor": "none", "panel": PANEL}
    if musou > 0:
        kw = dict(coating="musou_fit", deep_coating="wall_5pct",
                  paint_depth=musou)
    else:
        kw = dict(coating="wall_5pct")
    return spec, kw, pitch * 10.0


DESIGNS = [
    ("민판 5% 페인트", {"top": "flat", "top_params": {}, "depth": 0.0,
                      "floor": "none", "panel": 120.0},
     dict(coating="wall_5pct"), 63.5, None),
    ("피라미드 p4/d22", {"top": "pyramid",
                       "top_params": {"pitch": 4.0, "tip_flat": 0.4},
                       "depth": 22.0, "floor": "none", "panel": 120.0},
     dict(coating="musou_fit"), 40.0, None),
]
for pitch, depth, mus in [(6.35, 30.0, 0.0), (6.35, 60.0, 15.0),
                          (9.53, 40.0, 10.0), (9.53, 60.0, 15.0)]:
    s, kw, patch = comb(pitch, depth, mus)
    DESIGNS.append(("벌집 %.2f/d%.0f/무소%.0f" % (pitch, depth, mus),
                    s, kw, patch, (pitch, depth, mus)))

stored = {}
if os.path.exists(STORED):
    for r in json.load(open(STORED)):
        stored[(r["pitch"], r["depth"], r["musou"])] = r


def set_materials(df_paint, df_musou):
    """재료표를 통째로 갈아끼운다.

    확산비율을 인자로 넘기면 판 전체가 그 값 하나를 쓴다. 팁의 무소와 안쪽
    페인트가 서로 다른 값을 써야 하므로 그 길은 못 쓴다. 32가지 연구도
    diffuse_frac=None 으로 돌았다. 실제로 이걸 틀려서 V0 이 무소 칠한
    설계에서만 31.5 % 어긋났고, 검사기가 스스로 멈췄다.
    """
    SS.MATERIALS["wall_5pct"]["df"] = df_paint
    SS.MATERIALS["acryl_5pct"]["df"] = df_paint
    for k in ("musou_fit", "musou_air", "musou_brush"):
        SS.MATERIALS[k]["df"] = df_musou


def run(spec, kw, patch, slider):
    """재료표는 미리 set_materials 로 맞춰 둔다. df 는 재료가 정한다."""
    pl = SS.measure(spec, THETAS, None, slider, SPP,
                    phis=[0.0, 45.0, 90.0], **kw)
    tot = {k: max(pl[p][k] for p in pl) for k in pl["0"]}
    f = SS.form(dict(spec, panel=patch), thetas=[0.0], n_phase=6, samples=SPP,
                beam_w=7.5, diffuse_frac=None, roughness=slider, **kw)
    if f.get("peak") is None or any(v is None for v in tot.values()):
        raise SystemExit("빈 칸이 나왔다. 결과로 안 쓴다.")
    return tot, f["peak"], f.get("rms")


# ---------------------------------------------------------------- V0
print("=== V0. 옛 값으로 저장된 32가지를 재현하나 ===", flush=True)
print("%-24s %10s %10s %8s | %10s %10s %8s"
      % ("설계", "총량 저장", "총량 지금", "차이", "번쩍임 저장", "지금", "차이"),
      flush=True)
old_rows, worst_v0 = {}, 0.0
set_materials(OLD["paint_df"], OLD["musou_df"])
for name, spec, kw, patch, key in DESIGNS:
    tot, pk, rms = run(spec, kw, patch, OLD["slider"])
    old_rows[name] = (tot, pk, rms)
    if key and key in stored:
        st = stored[key]
        s_tot = max(st["total"].values()); s_pk = st["peak"]
        d1 = 100 * (max(tot.values()) - s_tot) / s_tot
        d2 = 100 * (pk - s_pk) / s_pk
        worst_v0 = max(worst_v0, abs(d1), abs(d2))
        print("%-24s %9.5f%% %9.5f%% %6.2f%% | %10.4f %10.4f %6.2f%%"
              % (name, 100 * s_tot, 100 * max(tot.values()), d1,
                 s_pk, pk, d2), flush=True)
    else:
        print("%-24s %10s %9.5f%% %8s | %10s %10.4f %8s"
              % (name, "-", 100 * max(tot.values()), "-", "-", pk, "-"),
              flush=True)

print("\n저장값과 최대 %.2f %% 어긋난다." % worst_v0, flush=True)
if worst_v0 > 0.5:
    raise SystemExit("0.5 %% 를 넘는다. 옛 값을 재현 못 하므로 비교를 안 낸다.")
print("재현됐다. 비교로 넘어간다.\n", flush=True)

# ---------------------------------------------------------------- 비교
print("=== 정정된 재질로 다시 ===", flush=True)
print("%-24s | %9s %9s %6s | %8s %8s %6s | %7s %7s"
      % ("설계", "총량 옛", "총량 새", "차이", "번쩍임 옛", "새", "배",
         "뭉개짐 옛", "새"), flush=True)
rows = []
set_materials(NEW["paint_df"], NEW["musou_df"])
for name, spec, kw, patch, key in DESIGNS:
    o_tot, o_pk, o_rms = old_rows[name]
    tot, pk, rms = run(spec, kw, patch, NEW["slider"])
    ot, nt = max(o_tot.values()), max(tot.values())
    rows.append({"name": name, "old_total": ot, "new_total": nt,
                 "old_peak": o_pk, "new_peak": pk,
                 "old_rms": o_rms, "new_rms": rms,
                 "old_by_theta": o_tot, "new_by_theta": tot})
    print("%-24s | %8.5f%% %8.5f%% %5.1f%% | %8.4f %8.4f %5.2fx | %7s %7s"
          % (name, 100 * ot, 100 * nt, 100 * (nt - ot) / ot, o_pk, pk,
             pk / o_pk,
             ("%.2f" % o_rms) if o_rms else "-",
             ("%.2f" % rms) if rms else "-"), flush=True)
    json.dump(rows, open(os.path.join(OUT, "applynew.json"), "w"),
              indent=1, ensure_ascii=False)

# ---------------------------------------------------------------- V1 순위
print("\n=== V1. 어둡기 순위가 뒤집히나 (총량 밝은쪽, 작을수록 좋다) ===",
      flush=True)
for tag, k in (("옛 재질", "old_total"), ("새 재질", "new_total")):
    o = sorted(rows, key=lambda r: r[k])
    print("   %s : %s" % (tag, "  <  ".join(r["name"] for r in o)), flush=True)

# ---------------------------------------------------------------- V3 법칙
print("\n=== V3. 민판 법칙이 구조물에도 맞나 ===", flush=True)
alpha = NEW["slider"] ** 2
print("   민판 법칙: 1 + (1-확산)/(4α²), α = %.3f" % alpha, flush=True)
# 어느 재료의 식과 견줄지: 무소를 칠한 벌집도 정면에서 보이는 넓이의
# 대부분은 안쪽 5 % 페인트다. 그래서 두 식을 다 낸다. "무소0" 을 이름에
# 담은 설계에 무소 값을 갖다 대는 실수를 한 번 했다 -- 이름에 '무소' 가
# 들어간다고 무소가 칠해진 게 아니다.
law_paint = 1.0 + (1.0 - NEW["paint_df"]) / (4.0 * alpha * alpha)
law_musou = 1.0 + (1.0 - NEW["musou_df"]) / (4.0 * alpha * alpha)
print("   민판 식: 5 %% 페인트 %.4f · 무소 %.4f" % (law_paint, law_musou),
      flush=True)
for r in rows:
    print("   %-24s 잰 값 %8.4f · 페인트 식의 %5.3f 배 · 무소 식의 %5.3f 배"
          % (r["name"], r["new_peak"], r["new_peak"] / law_paint,
             r["new_peak"] / law_musou), flush=True)

print("\n@@DONE@@", flush=True)
