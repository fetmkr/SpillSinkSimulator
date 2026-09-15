"""Read-only arithmetic/provenance probe for the scientific-readiness review.

Run from any directory with numpy installed. This is an identity check, not a
physical measurement or a validation of the new Cycles coating node tree.
"""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT.parent
sys.path.insert(0, str(PROJECT / "scripts"))
import brdf_model as M
import math

rho = 0.01
cone = 5.0
result = M.integrate(0, rho, 0, 0.1, cone_deg=cone,
                     n_theta=360, n_phi=720)
expected = rho * math.sin(math.radians(cone)) ** 2
fitted = json.loads((PROJECT / "results/fit_coating/musou_fit2_fit.json").read_text())
files = ["scripts/blender_render.py", "scripts/brdf_model.py",
         "scripts/fit_musou_fit2.py", "scripts/gate_coating_reciprocity.py",
         "scripts/cyc_worker.py", "scripts/form_buildable.py",
         "scripts/form_metrics.py", "scripts/sim_server.py",
         "material/musou_fit.json", "material/_filip2026_fig6_read.json",
         "results/fit_coating/musou_fit2_fit.json"]
out = {
    "review_time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "sha256": {name: hashlib.sha256((PROJECT / name).read_bytes()).hexdigest()
               for name in files},
    "identity_probe": {
        "description": "1% Lambertian, normal incidence, 5 degree specular cone",
        "analytic_cone_reflectance": expected,
        "output": result,
        "correct_rs_from_reported_tis": (1-result["tis"]) * result["thr"],
        "reported_rs_over_expected": result["rs"] / expected,
    },
    "fit_summary": fitted["fitted"],
    "fit_angle_rows": [r for r in fitted["rows"] if "angle" in r],
    "gate_result_present": (PROJECT / "results/audit_2026_09_14/fix_coating_gate.json").exists(),
    "limits": ["Arithmetic probe only; no new Blender render in this follow-up.",
               "Graph-read targets are not new physical measurements.",
               "Rs is displayed by fit_musou_fit2 but not used in its chi2 objective."]
}
dest = Path(__file__).with_suffix(".json")
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"saved": str(dest), "identity_probe": out["identity_probe"],
                  "gate_result_present": out["gate_result_present"]}, indent=2))
