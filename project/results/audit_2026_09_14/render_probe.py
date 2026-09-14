import sys, os, json, math
from types import SimpleNamespace
import bpy, numpy as np
ROOT = os.getcwd()
sys.path.insert(0, os.path.join(ROOT, 'project/scripts'))
import blender_render as BR

OUT = os.path.join(ROOT, 'project/results/audit_2026_09_14')
TMP = '/private/tmp/spillsink-audit'
os.makedirs(TMP,exist_ok=True)
os.makedirs(OUT,exist_ok=True)
records = []

def render(name, coat, ti=None, to=0, samples=128):
    BR.clear_scene()
    p=SimpleNamespace(face_w=100.,face_h=300.)
    ob=BR.make_flat_plate(p,0,'sample',BR.make_coating('coat',**coat))
    # Open plane builder winds toward -Y. Use the front (+Y) of the coating.
    import bmesh
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    ob.data.update()
    print('NORMAL',tuple(ob.data.polygons[0].normal),flush=True)
    BR.make_flat_plate(p,120,'control',BR.make_diffuse('diffuse',0.05))
    BR.setup_camera(110,0,240,160,80,elev_deg=to)
    BR.configure_cycles(samples,False,seed=17)
    BR.set_world(1. if ti is None else 0.)
    if ti is not None: BR.add_sun(ti,1.,0.)
    f=os.path.join(TMP,'probe.exr')
    BR.render_to(f,os.path.join(TMP,'probe.png'))
    arr=BR.read_exr(f,160,80)
    a=BR.window_stats(arr,BR.to_pixel_window((20,80,-30,30)))['mean']
    b=BR.window_stats(arr,BR.to_pixel_window((140,200,-30,30)))['mean']
    rec=dict(name=name,ti=ti,to=to,samples=samples,coating=coat,normal=list(ob.data.polygons[0].normal),sample=a,control=b,ratio=a/b,brdf=(a/b)*0.05/math.pi if ti is not None else None)
    records.append(rec)
    json.dump(dict(blender=bpy.app.version_string,records=records),open(os.path.join(OUT,'render_probe.json'),'w'),indent=2)
    print('AUDIT_RESULT',json.dumps(rec),flush=True)

mat=json.load(open(os.path.join(ROOT,'project/material/musou_fit.json')))
b,sp=BR.coating_split(mat['bsdf']['diffuse_fraction'],mat['scattering']['reflectance']['value'])
cc=dict(body=b,spec_scale=sp,roughness=mat['bsdf']['lobe']['roughness'])
coat={k:cc[k] for k in ('body','spec_scale','roughness')}
for to in (0,60,80): render('current_musou_hemi',coat,to=to,samples=256)
# Reciprocal configurations have source and viewer directions exchanged.
for name,c in [('current_musou',coat),('historical_musou',dict(body=BR.MUSOU_BODY,spec_scale=BR.MUSOU_SPEC_SCALE,roughness=.30)),('lambert_control',dict(body=.01,spec_scale=0.,roughness=.30))]:
 for ti,to in ((80,-65),(-65,80),(60,-40),(-40,60)):
  render(name,c,ti,to)
for ti,to in ((80,-65),(-65,80)): render('current_musou_high_spp',coat,ti,to,samples=1024)
print('AUDIT_COMPLETE',flush=True)
