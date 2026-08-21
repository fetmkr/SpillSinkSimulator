"""같은 페인트끼리 견준다. 벌집이 구조로 무엇을 하는가.

앞선 32 가지는 사용자 사양대로 벌집을 5 % 반사 페인트로 칠하고, 비교 대상은
무소(1 %) 를 칠한 맨 벽이었다. 도료가 5 배 다른 둘을 견주고서 "벌집이 5 배
번쩍인다"고 적었다. 틀렸다. 그 차이는 대부분 도료다.

여기서는 도료를 고정하고 구조만 바꾼다.

PRE-REGISTERED:
  E1  같은 5 % 페인트에서 벌집이 맨 벽보다 번쩍임이 낮다. 앞 데이터가 이미
      7.15 대 8.23 으로 그렇게 말하고 있다.
  E2  같은 무소에서도 벌집이 맨 벽보다 낮다. 구조가 하는 일은 도료와 무관해야
      한다.
  E3  벌집을 통째로 무소로 칠하면 번쩍임이 맨 벽 무소(1.644)보다 낮아진다.
      낮아지지 않으면, 벌집은 번쩍임에 아무 도움이 안 되는 물건이다.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT="/tmp/simsrv/comb_musou"; os.makedirs(OUT, exist_ok=True)
THETAS=[0.0,-20.0,20.0,-40.0,40.0]; SPP=256
COMB=lambda d: {"top":"comb","top_params":{"pitch":6.35,"wall_top":0.08,
    "wall_bot":0.08,"comb_expand":1.0,"jitter":0.0},"depth":d,"floor":"none",
    "panel":200.0}
FLAT={"top":"flat","top_params":{},"depth":0.0,"floor":"none","panel":200.0}
CASES=[
  ("맨 벽 · 5% 페인트",        FLAT,       dict(coating="wall_5pct"),  63.5),
  ("벌집 깊이60 · 5% 페인트",   COMB(60.0), dict(coating="wall_5pct"),  63.5),
  ("맨 벽 · 무소",            FLAT,       dict(coating="musou_fit"),  63.5),
  ("벌집 깊이30 · 무소",       COMB(30.0), dict(coating="musou_fit"),  63.5),
  ("벌집 깊이60 · 무소",       COMB(60.0), dict(coating="musou_fit"),  63.5),
]
rows=[]
print("도료를 고정하고 구조만 바꾼다. 판 200 mm, 셀 6.35 mm.\n", flush=True)
print("%-26s | %-9s %-9s %-9s | %s" % ("","정면 %","20도 %","40도 %","번쩍임(원래눈금)"), flush=True)
for label, spec, kw, patch in CASES:
    tot=SS.measure(spec, THETAS, 0.76, 0.30, SPP, **kw)["0"]
    f=SS.form(dict(spec, panel=patch), thetas=[0.0], n_phase=6, samples=SPP,
              beam_w=7.5, **kw)
    v={("%.0f"%t):tot.get("%.0f"%t) for t in THETAS}
    if f.get("peak") is None or any(x is None for x in v.values()):
        raise SystemExit("빈 칸: %s" % label)
    rows.append({"label":label,"total":v,"peak":f["peak"]})
    print("%-26s | %9.4f %9.4f %9.4f | %9.4f"
          % (label, 100*v["0"], 100*max(v["-20"],v["20"]),
             100*max(v["-40"],v["40"]), f["peak"]), flush=True)
    json.dump(rows, open(os.path.join(OUT,"fair.json"),"w"), indent=1, ensure_ascii=False)
print("\n같은 도료끼리 벌집이 맨 벽 대비:", flush=True)
d={r["label"]:r for r in rows}
for a,b,tag in (("맨 벽 · 5% 페인트","벌집 깊이60 · 5% 페인트","5% 페인트"),
                ("맨 벽 · 무소","벌집 깊이60 · 무소","무소")):
    print("   %-10s 번쩍임 %.4f -> %.4f  (%+.1f %%)   빛의 양 정면 %.4f -> %.4f (%+.1f %%)"
          % (tag, d[a]["peak"], d[b]["peak"], 100*(d[b]["peak"]-d[a]["peak"])/d[a]["peak"],
             100*d[a]["total"]["0"], 100*d[b]["total"]["0"],
             100*(d[b]["total"]["0"]-d[a]["total"]["0"])/d[a]["total"]["0"]), flush=True)
print("\n@@DONE@@", flush=True)
