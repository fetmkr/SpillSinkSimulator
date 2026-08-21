# -*- coding: utf-8 -*-
"""빔을 쐈을 때 되돌아오는 총 에너지. 하늘 조명이 아니라 빔으로.

지금까지 '빛의 양'은 하늘이 골고루 밝은 상태에서 쟀다(rho_dh). 그건 방 안
조명이 벽에서 얼마나 돌아오는가의 잣대다. 그런데 이 판이 막아야 하는 것은
레이저 빔이고, 빔은 관 바닥까지 온전한 세기로 들어간다. 하늘 조명에서는
바닥이 6도짜리 하늘만 보므로 어둡고, 빔에서는 환하다. 같은 각도인데 답이
반대로 나온다.

그래서 빔을 쏘고 창 안의 에너지를 전부 더한다. 봉우리가 아니라 합이다.
대조판의 합으로 나누어 배수로 적는다.

PRE-REGISTERED:
  T1  빔 기준 정면 값은 하늘 기준보다 훨씬 크다. 하늘 기준 정면이 낮은 것은
      바닥이 어둡게 조명되기 때문이고, 빔에는 그 이유가 없다.
  T2  빔 기준에서도 벌집이 민판보다 낮다. 흩어진 빛은 여전히 갇힌다.
  T3  바닥 판을 무소로 칠하면 빔 기준 정면 값이 크게 떨어진다. 빔이 닿는
      자리가 바닥이기 때문이다.
"""
import os, sys, json
HERE=os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0,HERE)
import bpy, numpy as np                              # noqa: E402
import blender_render as BR, rig_v2 as R2            # noqa: E402
import form_buildable as FB                          # noqa: E402
import sim_server as SS                              # noqa: E402

OUT="/tmp/simsrv/beamtot"; os.makedirs(OUT, exist_ok=True)
N_PHASE=6

def beam_total(prm, coat, theta, deep=None, pdep=None, floorcoat=None, spp=256):
    kw={"coating": SS._coat(coat, 0.76)}
    if pdep and deep:
        kw["deep_coating"]=SS._coat(deep,0.76); kw["paint_depth"]=float(pdep)
    if floorcoat:
        kw["floor_coating"]=SS._coat(floorcoat,0.76)
        kw["floor_boundary_depth"]=float(prm.get("depth",50.0))
    sc=R2.build(prm, samples=spp, roughness=0.30, **kw)
    p,cx0=sc["p"],sc["ctrl_x0"]; tw=sc["total_w"]; ortho=tw*1.02
    rx,ry,mmpx,_=R2.resolution_for(ortho,p.face_h)
    wp,wc=R2.full_face_windows(p,cx0)
    # 도료를 장면에 심는다
    BR.configure_cycles(spp,True)
    accp=accc=0.0
    for i in range(N_PHASE):
        dz=(-p.pitch/2.0)+p.pitch*i/N_PHASE if hasattr(p,"pitch") else 0.0
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT","CAMERA"): bpy.data.objects.remove(o,do_unlink=True)
        BR.setup_camera(tw/2.0,0.0,ortho,rx,ry,elev_deg=0.0)
        BR.set_world(0.0)
        BR.add_stripe(theta, tw/2.0, 0.0, 7.5, tw, strength=400.0,
                      spread_deg=FB.SPREAD_DEG, target_z=dz)
        f=os.path.join(OUT,"b.exr"); BR.render_to(f,f.replace(".exr",".png"))
        a=BR.read_exr(f,rx,ry)
        px=BR.to_pixel_window(wp); pc=BR.to_pixel_window(wc)
        accp+=a[int(px[2]):int(px[3]), int(px[0]):int(px[1])].sum()
        accc+=a[int(pc[2]):int(pc[3]), int(pc[0]):int(pc[1])].sum()
        try: os.remove(f)
        except OSError: pass
    # numpy 값 그대로 두면 json 저장에서 터진다. 12초 만에 죽었다.
    return float(accp)/max(float(accc),1e-30)

def comb(pitch, depth):
    return dict(topology="comb", pitch=pitch, wall_top=0.08, wall_bot=0.08,
                jitter=0.0, depth=depth, face_w=pitch*10.0, face_h=pitch*10.0,
                margin_depths=2.0, backing=2.0)
FLAT=dict(kind="gap",pitch=6.35,depth=0.0,face_w=63.5,face_h=63.5,
          margin_depths=2.0,backing=2.0)
PIT=[6.35,9.53]; DEP=[30.0,40.0,50.0,60.0]; MUS=[0.0,5.0,10.0,15.0]
JS=os.path.join(OUT,"beam_total.json")
rows=json.load(open(JS)) if os.path.exists(JS) else []
done={r["key"] for r in rows}
print("빔 7.5 mm 로 쏘고 창 안 에너지를 전부 더한 값. 대조판 = 1.", flush=True)
print("판은 셀 10 개짜리 조각. 바탕 5 % 페인트, 무소는 팁에서부터.\n", flush=True)
print("%-26s %9s %9s %9s %9s" % ("","정면","20도","40도","번쩍임"), flush=True)

def one(key, label, prm, kw, spec_for_peak):
    if key in done: return
    v=[beam_total(dict(prm), kw.get("coating","wall_5pct"), th,
                  deep=kw.get("deep_coating"), pdep=kw.get("paint_depth"))
       for th in (0.0,-20.0,-40.0)]
    pk=SS.form(spec_for_peak, thetas=[0.0], n_phase=6, samples=256,
               beam_w=7.5, **kw)["peak"]
    rows.append({"key":key,"label":label,"beam_total":[float(x) for x in v],
                 "peak":float(pk)})
    print("%-26s %9.4f %9.4f %9.4f %9.4f" % (label, v[0],v[1],v[2], pk), flush=True)
    json.dump(rows,open(JS,"w"),indent=1,ensure_ascii=False)

one("flat5","맨 벽 · 5% 페인트", FLAT, dict(coating="wall_5pct"),
    {"top":"flat","top_params":{},"depth":0.0,"floor":"none","panel":63.5})
one("flatm","맨 벽 · 무소", FLAT, dict(coating="musou_fit"),
    {"top":"flat","top_params":{},"depth":0.0,"floor":"none","panel":63.5})
for pitch in PIT:
    for depth in DEP:
        for mus in MUS:
            key="c%.2f_%d_%d" % (pitch,depth,mus)
            lab="벌집 %.2f · 깊이%d · 무소%d" % (pitch,depth,mus)
            kw=(dict(coating="musou_fit",deep_coating="wall_5pct",paint_depth=mus)
                if mus>0 else dict(coating="wall_5pct"))
            sp={"top":"comb","top_params":{"pitch":pitch,"wall_top":0.08,
                "wall_bot":0.08,"comb_expand":1.0,"jitter":0.0},"depth":depth,
                "floor":"none","panel":pitch*10.0}
            one(key, lab, comb(pitch,depth), kw, sp)
print("\n@@DONE@@", flush=True)
