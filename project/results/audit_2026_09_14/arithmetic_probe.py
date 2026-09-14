import ast, json, math, sys
from pathlib import Path
import numpy as np
ROOT=Path.cwd(); S=ROOT/'project/scripts'; OUT=ROOT/'project/results/audit_2026_09_14'
sys.path.insert(0,str(S))
from form_metrics import recentre, rms_width
from gate_roughness_from_tis import inside_cone
src=(S/'form_buildable.py').read_text()
# Execute the actual independent production function without importing bpy.
node=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='beam_positions')
ns={'BEAM_POS':'sobol'};exec(compile(ast.Module(body=[node],type_ignores=[]),'beam_positions','exec'),ns)
R={}
# P99 changes when only the zero padding / nominal panel changes.
x=np.arange(400)-200
panel=.1*(np.abs(x)<18)+.9*(np.abs(x)<4)
ctrl=1.*(np.abs(x)<18)
R['p99_padding']=[dict(nwin=n,peak_max=float(recentre(panel,n).max()/recentre(ctrl,n).max()),peak_p99=float(np.percentile(recentre(panel,n),99)/np.percentile(recentre(ctrl,n),99))) for n in (361,465,931,2327)]
# Exact production stopping condition with detached weak tails.
z=np.arange(-50,50.001,.05)
core=np.exp(-.5*(z/.8)**2);core/=core.sum()
tails=np.exp(-.5*((z-34)/.5)**2)+np.exp(-.5*((z+34)/.5)**2);tails/=tails.sum()
p=.727*core+.273*tails
curve=[]
for h in (24,48,96,100):
 mask=abs(z)<=h/2
 rp=rms_width(p[mask],.05);rc=rms_width(core[mask],.05)
 curve.append(dict(window_mm=h,rms=rp,smear=rp/rc,energy=float(p[mask].sum())))
ci=len(curve)-1;conv=False
for i in range(1,len(curve)):
 a,b=curve[i-1]['smear'],curve[i]['smear']
 if a and b and abs(b-a)/b<=.02:ci=i;conv=True;break
R['false_convergence']=dict(curve=curve,chosen=curve[ci],converged=conv)
R['beam_positions']={str(n):ns['beam_positions'](50,n) for n in (6,16)}
R['tis_counterexamples']=[dict(df=d,alpha=a,tis=1-inside_cone(d,a)) for d,a in ((.993,.039),(.98,.055),(.95,.1),(.94,.2),(.9,.25))]
# Source macro-normal Fresnel Mix law, exact in a unit-energy glossy furnace.
def fres(theta,n=1.5):
 c=math.cos(math.radians(theta));ct=math.sqrt(1-(1-c*c)/(n*n))
 return .5*((c-n*ct)/(c+n*ct))**2+.5*((n*c-ct)/(n*c+ct))**2
rho=.00998;df=.993;b=df*rho;s=(1-df)*rho/.04
R['current_hemi_ideal_glossy']=[dict(theta=t,rho=b*(1-s*fres(t))+s*fres(t)) for t in (0,60,80,85)]
# Inventory actual bytes, not extension.
R['invalid_pdf']=[str(p.relative_to(ROOT)) for p in (ROOT/'project/reference').rglob('*.pdf') if p.read_bytes()[:5]!=b'%PDF-']
(OUT/'arithmetic_probe.json').write_text(json.dumps(R,indent=2))
print(json.dumps(R,indent=2))
