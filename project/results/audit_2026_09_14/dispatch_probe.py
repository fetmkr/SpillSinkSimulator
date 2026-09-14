import sys, io, json, types, importlib.util, contextlib
from pathlib import Path
ROOT=Path.cwd(); S=ROOT/'project/scripts';OUT=ROOT/'project/results/audit_2026_09_14'
calls=[]
fake=types.ModuleType('sim_server')
def spy(*args,**kw):
 r=dict(args=args,kwargs=kw);calls.append(r);return r
fake.form=spy;fake.measure=spy
sys.modules['sim_server']=fake
sp=importlib.util.spec_from_file_location('worker_under_audit',S/'cyc_worker.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)
base=dict(spec={'top':'comb','depth':40,'panel':100,'floor':'none'},thetas=[40],samples=64,n_phase=6,beam_w=7.5,coating='wall_5pct',deep_coating='anodised',paint_depth=15,floor_coating='musou_air',obs_elev=40,phis=[45,90],mm_per_px=.05,diffuse_frac=.91,roughness=.2,slot_df={'coating':.92},slot_rough={'coating':.3})
R=[]
for op in ('form','measure'):
 req=dict(base,op=op)
 sys.stdin=io.StringIO(json.dumps(req))
 with contextlib.redirect_stdout(io.StringIO()):w.main()
 R.append(dict(op=op,request=req,forwarded=calls[-1]))
(OUT/'dispatch_probe.json').write_text(json.dumps(R,indent=2))
print(json.dumps(R,indent=2))
