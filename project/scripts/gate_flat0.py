"""평평한 바닥에 0도로 쏜다 — 렌더가 확산을 제대로 쓰는가.

질문: 총량 렌더가 확산을 고려하는가. 0도로 들어온 빛이 곧게 되돌아온다면
실제와 다르다.

평평한 판은 답이 미리 정해져 있다. 반사율 rho 인 판은 어떤 각도에서 재든
rho 를 돌려준다. 구조가 없으니 여러 번 튕길 데도 없고, 확산이든 정반사든
나가는 총량은 같아야 한다 -- 방향만 다르다.

그래서 이 판으로 두 가지를 한 번에 본다.
  1. 렌더가 평판에서 rho 를 정확히 돌려주는가 (장비 검사)
  2. 확산 비율을 0(전부 거울)에서 1(전부 확산)까지 바꿔도 총량이 유지되는가
     -- coating_split 이 rho_dh(0) 를 고정하도록 만들어졌으니 유지돼야 한다.
     안 유지되면 도료 모델이 에너지를 만들거나 잃는 것이다.

그리고 대조로 피라미드를 같이 잰다. 거기서는 확산 비율이 값을 크게 바꿔야
한다 -- 확산은 사방으로 흩어져 옆벽에 다시 맞고, 정반사는 한 방향으로 나가
탈출하기 쉽기 때문이다. 평판에서 안 변하고 피라미드에서 변하면, 렌더는
확산을 제대로 쓰고 있고 그 효과는 기하가 만드는 것이다.

미리 적어 둔 예측:
  F1  평판 rho_dh(0) = 1.00 % ± 2 %, 확산 비율과 무관
  F2  피라미드는 확산 비율이 오를수록 총량이 내려간다 (흩어진 빛이 다시 갇힘)
  F3  둘의 차이가 곧 '기하가 하는 일'이다
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import bpy, blender_render as BR, form_buildable as FB, rig_v2 as R2  # noqa

OUT="/tmp/simsrv/flat0"; os.makedirs(OUT,exist_ok=True)
SPP=512

def rho(prm, df, rough=0.30, thetas=(0.0,-40.0)):
    q=dict(prm); q.update(face_w=100.0,face_h=100.0,margin_depths=2.0,backing=2.0)
    body,spec=BR.coating_split(df, rho0=0.00998)
    cfg={"tag":"f0","out_dir":OUT,"results_dir":OUT,"samples":SPP,
         "res_x":1400,"res_y":620,"gpu":True,"spec_roughness":rough,
         "params":q,"renders":[],"material_mode":"coating","family":"floor",
         "coating":{"body":body,"spec_scale":spec,"roughness":rough}}
    cfg.update({k:v for k,v in FB.COAT.items() if k!="spec_roughness"})
    cfg["coating"]={"body":body,"spec_scale":spec,"roughness":rough}
    BR.clear_scene()
    p,cs,cx0=BR.build_scene(cfg)
    tw=cx0+p.face_w; ortho=tw*1.02
    rx,ry,mm,cap=R2.resolution_for(ortho,p.face_h)
    wp,wc=R2.full_face_windows(p,cx0,inset_mm=R2.sky_inset_mm(mm))
    BR.configure_cycles(SPP,True)
    out={}
    for th in thetas:
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT","CAMERA"): bpy.data.objects.remove(o,do_unlink=True)
        BR.setup_camera(tw/2,0.0,ortho,rx,ry,elev_deg=th)
        BR.set_world(1.0)
        f=os.path.join(OUT,"a.exr"); BR.render_to(f,f.replace(".exr",".png"))
        a=BR.read_exr(f,rx,ry)
        out[th]=100*BR.window_stats(a,BR.to_pixel_window(wp))["mean"]
        ctl=BR.window_stats(a,BR.to_pixel_window(wc))["mean"]
        out[("ctrl",th)]=ctl
        os.remove(f)
    return out

FLAT=dict(kind="pyramid",pitch=4.0,depth=0.5,tip_flat=0.0)   # 사실상 평판
PYR =dict(kind="pyramid",pitch=4.0,depth=22.0,tip_flat=0.4)

print("도료 총 반사율 1.00 % 고정 · 확산 비율만 바꿈\n",flush=True)
print("%-10s %-14s %-14s %-14s %s"
      % ("확산비율","평판 0도%","평판 40도%","피라미드 0도%","대조판"),flush=True)
rows=[]
for df in (0.0,0.25,0.50,0.76,1.0):
    a=rho(FLAT,df); b=rho(PYR,df)
    rows.append((df,a[0.0],a[-40.0],b[0.0],b[-40.0]))
    print("%-10.2f %-14.5f %-14.5f %-14.5f %.6f"
          % (df,a[0.0],a[-40.0],b[0.0],a[("ctrl",0.0)]),flush=True)

print("\n=== 판정 ===",flush=True)
fl=[r[1] for r in rows]; py=[r[3] for r in rows]
print("  평판 0도  : %.5f ~ %.5f  흩어짐 %.1f %%  -> %s"
      % (min(fl),max(fl),100*(max(fl)-min(fl))/(sum(fl)/len(fl)),
         "F1 통과 (확산 비율과 무관)" if (max(fl)-min(fl))/(sum(fl)/len(fl))<=0.02
         else "**F1 실패 — 도료 모델이 에너지를 만들거나 잃음**"),flush=True)
print("  평판이 도료 반사율 1.00 %% 를 돌려주나: %.5f %%  -> %s"
      % (sum(fl)/len(fl), "예" if abs(sum(fl)/len(fl)-1.0)<=0.05 else "**아니오**"),flush=True)
print("  피라미드 0도: %.5f ~ %.5f  확산 0 -> 1 에서 %+.1f %%"
      % (min(py),max(py),100*(py[-1]-py[0])/py[0]),flush=True)
print("  -> %s" % ("F2 통과: 확산이 커질수록 더 갇힌다" if py[-1]<py[0]*0.98
                   else "**F2 실패: 확산이 총량을 안 바꿈**"),flush=True)
print("@@DONE@@",flush=True)
