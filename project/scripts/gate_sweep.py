"""
The five checks that must pass BEFORE a sweep whose output will be ranked.

    Blender --background --factory-startup --python scripts/gate_sweep.py
    python3 scripts/gate_sweep.py --offline      # checks 2-5 only, no renders

Exit 0 = cleared to sweep. Exit 1 = do not sweep, and do not report anything
already swept until the failure is understood.

WHY THIS EXISTS. Four conclusions were published and withdrawn on 2026-08-12/13.
None was overturned by new physics; all four were setup errors that a check
costing minutes would have caught before a sweep costing hours. CONTEXT.md 11a
lists them. The rule that was broken every time: **validate before you measure,
not after.**

The checks are deliberately cheap. A gate nobody runs is worse than no gate.
"""

import sys
import os
import csv
import json
import glob
import re
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

# Filip & Vavra 2026 (JOSA A 43, 1037), Musou Black paint, Fig. 6.
PUBLISHED = {0: 0.0100, 15: 0.0100, 30: 0.0103, 45: 0.0113,
             60: 0.0143, 75: 0.0233, 80: 0.0318}
TOL = 0.12                      # 12%: the recorded fit is 9.5% worst-case

FAILS = []
NOTES = []


def fail(check, msg):
    FAILS.append((check, msg))
    print("  FAIL  %s: %s" % (check, msg))


def ok(check, msg):
    print("  ok    %s: %s" % (check, msg))


# --- 1. controls reproduce known answers ------------------------------------

def check_controls():
    """Flat plate against the published curve; rho=0 reads 0; control 0.05."""
    print("\n[1] controls reproduce known answers")
    try:
        import blender_render as BR
    except Exception:
        NOTES.append("check 1 skipped: no Blender")
        print("  skip  (offline)")
        return

    PLATE = dict(face_w=100.0, face_h=100.0, depth=0.001, pitch_mean=50.0,
                 tip_width=50.0, tip_round=False, pitch_jitter=0.0,
                 arc_segments=4, valley_round=0.0, margin_depths=6.5)
    cfg = {"tag": "gate_flat", "family": "ridge",
           "out_dir": os.path.join(ROOT, "renders", "gate"),
           "results_dir": os.path.join(ROOT, "renders", "gate"),
           "samples": 512, "res_x": 900, "res_y": 420, "gpu": True,
           "material_mode": "coating", "rho_control": 0.05,
           "coating": {"body": BR.MUSOU_BODY, "spec_scale": BR.MUSOU_SPEC_SCALE,
                       "ior": BR.MUSOU_IOR, "roughness": 0.30},
           "params": dict(PLATE),
           "renders": [{"mode": "hemi_view", "theta": -float(t)}
                       for t in sorted(PUBLISHED)]}
    res = BR.run(cfg)
    got = {int(round(-r["theta"])): r["panel"]["mean"]
           for r in res["modes"].values()}
    worst = max(abs(got[t] - PUBLISHED[t]) / PUBLISHED[t] for t in PUBLISHED)
    if worst > TOL:
        fail("flat plate", "worst residual %.1f%% against the published curve "
                           "(tolerance %.0f%%)" % (100 * worst, 100 * TOL))
    else:
        ok("flat plate", "worst residual %.1f%%" % (100 * worst))

    ctrl = [r["control"]["mean"] for r in res["modes"].values()]
    if abs(min(ctrl) - 0.05) > 5e-4 or abs(max(ctrl) - 0.05) > 5e-4:
        fail("0.05 control", "reads %.6f .. %.6f" % (min(ctrl), max(ctrl)))
    else:
        ok("0.05 control", "%.6f .. %.6f" % (min(ctrl), max(ctrl)))


# --- 2. every baseline traces to a render -----------------------------------

def check_baselines():
    """A denominator must come from a measurement, not from a typed constant."""
    print("\n[2] baselines trace to a measurement")
    import re
    src = open(os.path.join(ROOT, "scripts", "analyze_buildable.py")).read()
    m = re.search(r"FLAT_COATING_WORST\s*=\s*([0-9.]+)", src)
    if not m:
        fail("baseline", "FLAT_COATING_WORST not found")
        return
    val = float(m.group(1))
    head = src[:m.start()]
    if "MEASURED" not in head.upper():
        fail("baseline", "%.6f has no comment saying how it was measured" % val)
    elif val > 0.02:
        fail("baseline", "%.6f is implausibly high for this coating -- the "
                         "published flat plate is ~0.011 at these angles" % val)
    else:
        ok("baseline", "%.6f, documented as measured" % val)


# --- 3. comparisons are matched on feature AND process ----------------------

def check_matched(csv_path):
    print("\n[3] compared designs are matched on feature and process")
    if not os.path.exists(csv_path):
        NOTES.append("check 3 skipped: %s absent" % os.path.basename(csv_path))
        print("  skip  (%s not present yet)" % os.path.basename(csv_path))
        return
    rows = list(csv.DictReader(open(csv_path)))
    if "feature" not in (rows[0] if rows else {}):
        fail("matching", "%s has no `feature` column -- a ranking from it "
                         "cannot be checked" % os.path.basename(csv_path))
        return
    if "process" not in rows[0]:
        fail("matching", "%s has no `process` column" % os.path.basename(csv_path))
        return
    feats = sorted({(r["process"], r["feature"]) for r in rows})
    procs = {p for p, _ in feats}
    ok("matching", "%d process x feature combinations across %d processes"
       % (len(feats), len(procs)))
    FLOOR = {"expanded foil": 0.03, "sheet, parallel": 0.05,
             "sheet, lanced": 0.05, "sheet, grid": 0.05, "mould": 0.40,
             "print": 0.40}
    bad = [(p, f) for p, f in feats
           if p in FLOOR and float(f) < FLOOR[p] - 1e-9]
    if bad:
        # Their PRESENCE is fine and often useful -- they show how much of a
        # ranking is bought with feature size. What must not happen is one of
        # them being reported as a recommendation without the flag. So the gate
        # checks that the analyser marks them, not that they are absent.
        import subprocess as _sp
        r = _sp.run([sys.executable,
                     os.path.join(ROOT, "scripts", "analyze_buildable.py")],
                    capture_output=True, text=True)
        if "**NO**" in r.stdout and "CANNOT BE MADE" in r.stdout:
            ok("process floor", "%d combination(s) below floor, and the "
               "analyser marks every one" % len(bad))
        else:
            fail("process floor", "%d combinations below their own process "
                 "floor and the analyser does not flag them: %s"
                 % (len(bad), ", ".join("%s %s" % b for b in bad[:4])))
    else:
        ok("process floor", "every combination is at or above its floor")


# --- 4. the measured geometry is the documented geometry --------------------

def check_spec_matches(csv_path, spec_md):
    """Diff the params actually rendered against the numbers in the spec."""
    print("\n[4] measured geometry == documented geometry")
    if not (os.path.exists(csv_path) and os.path.exists(spec_md)):
        print("  skip  (need both the CSV and the spec)")
        return
    rows = list(csv.DictReader(open(csv_path)))
    if not rows or "params_json" not in rows[0]:
        fail("spec diff", "no params_json column -- what was rendered is not "
                          "recorded, so it cannot be diffed against anything")
        return
    text = open(spec_md).read()
    # a taper is the specific trap that cost two days: the document says sheet,
    # the render says wedge. Any design whose two thicknesses differ, in a spec
    # that promises constant-thickness sheet, is a hard fail.
    # only the designs the SPEC actually points at. Historical rows for
    # superseded geometry are data, not a contradiction -- the failure mode
    # being guarded against is the spec describing one part while the number
    # beside it came from another.
    try:
        cands = {e["tag"] for e in json.load(
            open(os.path.join(RESULTS, "form_candidates.json")))}
    except Exception:
        cands = set()
    wedges = set()
    for r in rows:
        if cands and r["tag"] not in cands:
            continue
        p = json.loads(r["params_json"])
        a, b = p.get("plate_t_top"), p.get("plate_t_bot")
        if a is not None and b is not None and abs(a - b) > 1e-9:
            wedges.add((a, b))
    if wedges and ("판재" in text or "sheet" in text.lower()):
        fail("spec diff", "spec says sheet but %d rendered design(s) taper: %s"
             % (len(wedges), ", ".join("%.2f->%.2f" % w for w in
                                       sorted(wedges)[:3])))
    else:
        ok("spec diff", "no taper/sheet contradiction found")


# --- 5. ratios name their baseline ------------------------------------------

def check_ratio_language(*paths):
    print("\n[5] every quoted ratio names its baseline")
    import re
    bad = []
    for path in paths:
        if not os.path.exists(path):
            continue
        for i, line in enumerate(open(path), 1):
            # a ratio, not a dimension or a count. "100 x 100 mm" and
            # "36 장" are not ratios and must not be flagged, or the check
            # becomes noise and gets ignored -- which is how a real one hides.
            if not re.search(r"\d+(\.\d+)?\s*배(?!열)", line):
                continue
            if re.search(r"mm|장|개|명|번|쪽|각도|°", line):
                continue
            if re.search(r"평판|flat|대비|vs|against|control|기준|baseline",
                         line, re.I):
                continue
            bad.append("%s:%d  %s" % (os.path.basename(path), i,
                                      line.strip()[:70]))
    if bad:
        for b in bad[:6]:
            print("      %s" % b)
        fail("ratio language", "%d ratio(s) with no baseline named on the same "
                               "line" % len(bad))
    else:
        ok("ratio language", "every ratio names what it is against")


def check_candidates_ranked():
    """Every candidate must appear in the ranking, with a rank.

    A candidate that renders but cannot be ranked is worse than an absent one:
    it appears in the gallery looking complete, with a dash where its position
    should be, while its number gets quoted by hand somewhere else. That
    happened to the blade array when its re-measurement went to a second CSV
    the analyser did not read.
    """
    print("\n[6] every candidate has a rank in both rankings")
    # The NEWEST data.json, not today's. Looking only at today's folder went
    # blind the moment a second report was written on a later date: the phase 3
    # report has no data.json, so "today" was empty and the check skipped while
    # the ranked report it was meant to guard sat one folder back, unchecked.
    # "No folder for today" is not the same as "nothing to check".
    import glob
    cands = sorted(glob.glob(os.path.join(ROOT, "report", "*", "data.json")))
    if not cands:
        print("  skip  (no report data yet)")
        return
    dp = cands[-1]
    print("  ..    checking %s" % os.path.relpath(dp, ROOT))
    # data.json is a SNAPSHOT of the last build. If a measurement or the
    # analyser has changed since, it is stale and checking it blocks the very
    # rebuild that would fix it -- which is what happened when the commercial
    # honeycomb was added: the pre-gate failed on the previous build's file and
    # stopped the run at step 1. Stale means "not yet checkable", not "failed".
    inputs = [os.path.join(RESULTS, f) for f in
              ("sweep_buildable.csv", "sweep_blade.csv", "sweep_comb.csv",
               "form_buildable.json", "form_candidates.json")]
    inputs.append(os.path.join(ROOT, "scripts", "analyze_buildable.py"))
    newest = max((os.path.getmtime(f) for f in inputs if os.path.exists(f)),
                 default=0)
    if newest > os.path.getmtime(dp):
        print("  skip  (data.json is older than its inputs -- the post-build "
              "gate will check it)")
        return
    d = json.load(open(dp))
    # ALL THREE rankings, not just darkness. The first version checked
    # rank_dark alone and passed a build where the commercial honeycomb had a
    # darkness rank and blank form and head-on columns -- it had entered the
    # darkness sweep but its form measurement was still rendering. A card with
    # two empty axes is exactly the "looks complete, is not" failure this check
    # was added to stop.
    bad = {}
    for axis in ("rank_dark", "rank_form", "rank_peak"):
        m = [e["design"] for e in d["entries"] if not e.get(axis)]
        if m:
            bad[axis] = m
    if bad:
        fail("candidate ranked", "; ".join(
            "%s missing for %s" % (a, ", ".join(v[:3]))
            for a, v in bad.items()))
    else:
        ok("candidate ranked", "all %d candidates ranked on all three axes"
           % len(d["entries"]))



def check_cross_sweep_agreement():
    """[8] A new sweep must re-measure at least one design an old sweep already
    has, and get the same answer.

    This is the check that would have caught the most damage. Every recent
    defect produced a number that looked plausible on its own and was only
    wrong RELATIVE to something already measured:

        the comb lattice with 30 % holes  -- plausible 0.2092 %
        the CSV whose columns shifted     -- plausible rho, actually a theta
        plate_over left to its default    -- plausible, and unrecorded
        mean-over-angle called worst-case -- plausible, 40 % too dark

    The last one was caught by luck: one design in `sweep_floor.csv` also
    exists in `sweep_blade.csv`, and the summaries disagreed while the raw
    theta-0 rows matched to five decimals. Nothing forced that comparison. This
    does.

    The rule: for every pair of sweeps that share a design (same geometry
    params, ignoring keys absent on one side), the scored value must agree to
    1e-9. A sweep with NO overlap at all is reported as unanchored -- not a
    failure, but it means nothing in it can be compared to anything else.
    """
    print("\n[8] new sweeps agree with old ones where they overlap")
    import hashlib

    def scored(path):
        """(design, seed) -> (worst over theta then coating, params).

        PER SEED, not averaged over them. Two sweeps may sample different seed
        sets -- `sweep_buildable` has 13 realisations of the cone and the newer
        sweeps have 3 -- and their means then differ for a legitimate reason.
        Comparing means would either raise a false alarm or, worse, force the
        tolerance so wide that a real disagreement slips under it. The same
        design at the same seed is deterministic and must match exactly.
        """
        rows = list(csv.DictReader(open(path)))
        if not rows or "params_json" not in rows[0]:
            return {}
        # MEASUREMENT CONDITIONS, not geometry. `params_json` carries the
        # shape; the coating roughness and the azimuth of incidence live in
        # their own columns and change the answer just as much. Leaving them
        # out made this check compare a design at roughness 0.10 against the
        # same shape at 0.30 and report a disagreement -- the same failure as
        # `plate_over`: a parameter that moves the number, absent from the
        # record used for identity.
        per, key, cond = collections.defaultdict(dict), {}, {}
        for r in rows:
            per[(r["tag"], r["diffuse_frac"])][float(r["theta"])] = \
                float(r["rho"])
            key[r["tag"]] = r["params_json"]
            cond[r["tag"]] = tuple(
                (c, r[c]) for c in ("roughness", "phi") if r.get(c))
        worst = {}
        for (tag, mat), d in per.items():
            if len(d) == 5:
                worst.setdefault(tag, {})[mat] = max(d.values())
        out = {}
        for tag, m in worst.items():
            if len(m) != 3 or "_s" not in tag:
                continue
            base, seed = tag.rsplit("_s", 1)
            out[(base, seed)] = (max(m.values()), key[tag], cond[tag])
        return out

    def fingerprint(pj):
        """Geometry identity: every param, nested ones flattened -- MINUS the
        keys that name the realisation rather than the design.

        `seed` was in here, and it is why this check reported "all agreeing"
        while two files held different numbers for `B_CONE_p0550`: the
        representative row happened to be seed 112 in one sweep and 102 in the
        other, the fingerprints differed, and the pair was never compared at
        all. A check that silently skips the comparison it exists to make is
        worse than no check.
        """
        try:
            d = json.loads(pj)
        except Exception:
            return None
        out = {}

        def walk(prefix, v):
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    walk("%s%s." % (prefix, k2) if prefix else "%s." % k2, v2)
            elif isinstance(v, list):
                out[prefix.rstrip(".")] = tuple(v)
            else:
                out[prefix.rstrip(".")] = v
        walk("", d)
        return {k: v for k, v in out.items()
                if k.split(".")[-1] not in ("seed", "pitch_seed",
                                            "width_seed", "baffle_seed")}

    paths = sorted(glob.glob(os.path.join(RESULTS, "sweep_*.csv")))
    data = {os.path.basename(p): scored(p) for p in paths}
    data = {k: v for k, v in data.items() if v}
    seen, bad, npair, unrec = {}, [], 0, set()
    for name, designs in data.items():
        for (base, seed), (val, pj, cnd) in designs.items():
            fp = fingerprint(pj)
            if fp is None:
                continue
            fp = dict(fp, **{"cond." + k: v for k, v in cnd})
            h = hashlib.md5((json.dumps(fp, sort_keys=True, default=str)
                             + "|" + seed).encode()).hexdigest()
            if h in seen:
                oname, obase, oval, ofp = seen[h]
                if oname != name:
                    npair += 1
                    if abs(val - oval) > 1e-9:
                        bad.append("%s:%s(s%s)=%.8f vs %s:%s=%.8f"
                                   % (name, base, seed, val, oname, obase,
                                      oval))
                continue
            # same geometry, different seed, or a near-miss on what is recorded
            for _h, (oname, obase, oval, ofp) in list(seen.items()):
                if oname == name:
                    continue
                only = set(fp) ^ set(ofp)
                if only and len(set(fp) & set(ofp)) >= 8 and \
                        all(fp[c] == ofp[c] for c in set(fp) & set(ofp)):
                    unrec.add("%s vs %s differ only in what they RECORD (%s)"
                              % (name, oname, ", ".join(sorted(only)[:4])))
                    break
            seen[h] = (name, base, val, fp)
    if bad:
        fail("cross-sweep", "; ".join(sorted(set(bad))[:4])
             + " -- the same geometry scored two different ways")
    elif npair:
        ok("cross-sweep", "%d shared design(s) across sweeps, all agreeing"
           % npair)
        for u in sorted(unrec)[:3]:
            print("  note  %s" % u)
    else:
        NOTES.append("check 8: no design is measured in two sweeps, so no "
                     "sweep is anchored to another")
        print("  ..    no overlap found -- nothing is anchored")


def check_no_typed_measurements():
    """[7] No report template may carry a measurement as a literal.

    The comb lattice fix moved every honeycomb number. The tables moved with
    it, because they are generated. The PROSE did not, because someone had
    typed 0.2092% and "1.640 to 0.140" into the template — so the page argued
    against its own figures for one build, quoting values measured on geometry
    that was 30 % hole.

    This is the same defect as the flat baseline that sat at a typed 6.12 %
    while the measurement said 1.14 %, and as `make_report.py` hard-coding
    claims that had been withdrawn. Three times is a rule, not an accident: a
    number that appears in a template is a number nobody will update.

    Anything that looks like an optical measurement — a percentage with 3+
    decimals, or a bare 3-decimal figure in the 0.0-9.9 range next to a word
    like "reads" or "head-on" — must be a {{PLACEHOLDER}}.
    """
    print("\n[7] no measurement is typed into a report template")
    pat = re.compile(r"(?<![\w.>])(\d\.\d{3,4})\s*%|"
                     r"reads\s*(?:<b>)?(\d\.\d{3})|"
                     r"from\s*(?:<b>)?(\d\.\d{3})\s*to")
    bad = []
    for name in ("report_2rank_template.html", "report_phase3_template.html"):
        p = os.path.join(ROOT, "scripts", name)
        if not os.path.exists(p):
            continue
        for m in pat.finditer(open(p).read()):
            bad.append("%s: %s" % (name, next(g for g in m.groups() if g)))
    if bad:
        fail("typed measurement", "; ".join(bad[:6])
             + " -- replace with a {{PLACEHOLDER}} read from the data")
    else:
        ok("typed measurement", "templates carry placeholders, not numbers")


def main():
    offline = "--offline" in sys.argv or "-h" in sys.argv
    print("=" * 68)
    print("SWEEP GATE — validate before you measure (CONTEXT.md 11a)")
    print("=" * 68)
    if not offline:
        check_controls()
    else:
        print("\n[1] controls — skipped (--offline)")
    check_baselines()
    csvp = os.path.join(RESULTS, "sweep_buildable.csv")
    check_matched(csvp)
    check_spec_matches(csvp, os.path.join(ROOT, "SAMPLES.md"))
    check_ratio_language(os.path.join(ROOT, "SAMPLES.md"))
    check_candidates_ranked()
    check_no_typed_measurements()
    check_cross_sweep_agreement()

    print("\n" + "=" * 68)
    for n in NOTES:
        print("note: %s" % n)
    if FAILS:
        print("GATE FAILED — %d check(s). Do not sweep, and do not report "
              "anything already swept." % len(FAILS))
        for c, m in FAILS:
            print("  - %s: %s" % (c, m))
        sys.exit(1)
    print("GATE PASSED — cleared to sweep.")
    sys.exit(0)


if __name__ == "__main__":
    main()
