# -*- coding: utf-8 -*-
"""English text for build_method_report.py --lang en.

사용자 요청 (2026-09-24): 친구에게 줄 방법 문서를 영어로.
숫자 설정값은 여기서도 const() 로 코드에서 읽는다. 여기 있는 것은 글뿐이다.
한국어 쪽 목록과 줄 수·순서가 같아야 한다 -- 빌더가 길이를 견주고 다르면 멈춘다.
한국어 쪽을 고치면 여기도 같이 고친다.
"""


def texts(const, FM, FB, BR):
    T = {}

    T["lang"] = "en"
    T["title"] = "Formulas and Implementation"
    T["eyebrow"] = "Spill Sink Simulator · Method"
    T["sub"] = ("What this simulator measures and how, where each setting comes "
                "from, and what still has no basis. <b>Numbers are read directly "
                "from the code</b>. Copying them by hand would let this document "
                "silently drift from the code.")

    T["h_axes"] = "The three measured values"
    T["axis_rows"] = ("What it measures", "Lighting", "Formula", "Code",
                      "Sampling window", "Why this way", "Run time",
                      "Known defects")
    T["h_uses"] = "Which value uses which setting"
    T["uses_p"] = ("Not every value uses every setting. Total reflectance uses "
                   "hemispherical lighting, so it uses neither the beam nor the "
                   "sampling window. Defects in those settings do not affect it.")
    T["uses_head"] = ("Setting", "Total reflectance", "Smear", "Head-on peak")
    T["uses_tag"] = ("&rho;<sub>dh</sub>", "rms width", "box peak")
    T["uses"] = "uses"
    T["now"] = ("Current values: peak statistic <b>%s</b> · beam positions "
                "<b>%s</b> · samples <b>%s</b> · number of positions <b>%s</b>")

    T["h_settings"] = "Settings and their basis"
    T["settings_p"] = ("Values are read from the source. Each has a basis grade: "
                       "<span class=\"g-jaem\">measured</span> means measured or "
                       "taken from the literature, <span class=\"g-half\">partial"
                       "</span> means only partly, <span class=\"g-none\">none"
                       "</span> means simply chosen.")
    T["settings_head"] = ("Setting", "Value", "Where", "Basis", "Explanation")
    T["grade_cls"] = {"measured": "g-jaem", "none": "g-none"}
    T["settings_tail"] = ("Settings are spread over nine places. Gathering them "
                          "into one is still to do.")

    T["h_findings"] = "Why it is built this way: what measuring taught us"
    T["findings_head"] = ("Finding", "What happens", "What we measured", "Basis")

    T["h_valid"] = ("How the calculator was validated: validation against "
                    "closed forms")
    T["valid_p"] = ("Comparing two calculators with each other cannot tell which "
                    "one is right. So we ran both on <b>problems whose answer is "
                    "already known as a formula</b>. These are the six rows below.")
    T["valid_head"] = ("Reference", "Formula", "What it separates", "Result",
                       "Where it runs")
    T["valid_tail"] = ("Not yet done: there is <b>no full comparison of our "
                       "honeycomb lattice against the cavity theory (Gouffé)</b>. "
                       "One point was checked and came out at 0.83 times "
                       "(results/PEER_REVIEW.md). And <b>physical measurements: "
                       "zero</b>.")

    T["h_open"] = "What still has no basis"

    T["h_refs"] = "References"
    T["refs_p"] = ("Only sources we opened and checked are listed. The title "
                   "links to the original; the file column links to our saved "
                   "copy, so it stays readable if the link dies.")
    T["refs_head"] = ("Author", "Title", "Where", "What it says", "File")
    T["too_big"] = "Original link</a><br>%.0f MB, left out of the bundle"
    T["h_std"] = "Measurement standards"
    T["std_p"] = ("Standards read when we chose the mean over beam positions as "
                  "the reported value. The current ASTM and ISO editions are paid "
                  "and we could not read them. The editions listed are the older "
                  "ones we actually read. The two ASTM files are text-only "
                  "extracts (.txt).")
    T["footer"] = ("Script that builds this document: "
                   "<code>scripts/build_method_report.py --lang en</code> "
                   "(text in <code>scripts/method_en.py</code>). Settings are "
                   "read from <code>scripts/form_metrics.py</code>, "
                   "<code>scripts/form_buildable.py</code> and "
                   "<code>scripts/blender_render.py</code>. The audit and its "
                   "fixes are in "
                   "<code>results/FINDINGS_simulator_audit_2026_09_14.md</code>.")

    T["SETTINGS"] = [
        ("Coating tree", const(BR, "COATING_MODEL"), BR,
         "measured", "reciprocal since 2026-09-15. The old tree (fresnel_mix) "
         "used a Fresnel node as the mixing weight, so swapping light and "
         "observer changed the BRDF (238 % on a flat plate). hemi_view reads "
         "total reflectance through reciprocity, so that premise was broken. "
         "The new tree differs by 0.001 % under the swap and stays within "
         "0.08 % of the analytic model (brdf_model) at 7 angles. "
         "gate_coating_reciprocity.py."),
        ("Default Musou material", "musou_fit2", "material/",
         "partial", "Fitted jointly to THR and TIS in figure 6 of the paper and "
         "to the lobe shape in figure 5 (body 0, spec_scale 0.50, alpha 0.75). "
         "The plots were read by eye, and alpha is open between 0.45 and 0.75. "
         "The old musou_fit misread head-on TIS as 0.985 to 0.995 (it is "
         "0.96)."),
        ("Pixel density mm/px", const(FM, "MM_PER_PX"), FM,
         "measured", "Resolves the smallest feature with 4 pixels. It is fixed "
         "whatever the panel size, so the same instrument measures with the "
         "same ruler. If it cannot be met, the run is refused rather than made "
         "coarser."),
        ("Pixel cap RES_CAP", const(FB, "RES_CAP"), FB,
         "chosen", "A memory limit, not physics. Above it the run is refused "
         "with the reason."),
        ("Beam width mm", const(FM, "STRIPE_W"), FM,
         "measured", "The LaserCube Ultra MK2 measures 7 to 14 mm at the wall. "
         "This is the low end."),
        ("Beam divergence deg", const(FM, "SPREAD_DEG"), FM,
         "measured", "A nearly parallel beam. Reproducing the 0.040 target under "
         "the old conditions matched the published value within 1 % only at "
         "0.05 degrees (at 1.0 degrees smear was -31 %)."),
        ("Number of beam positions", const(FM, "N_PHASE"), FM,
         "partial", "On a 6/12/24 ladder one case still moved 6.7 % at 24. Not "
         "re-measured after switching to Sobol."),
        ("Samples per pixel", const(FM, "SAMPLES"), FM,
         "measured", "Re-measured on the real measurement path on 2026-09-15 "
         "(three shapes by four angles, two seeds, 256 taken as truth). Count "
         "needed to be within 1 %: smear 8, p99 64, <b>box 256</b>, max 256. At "
         "16 the box value was +4.6 % on the honeycomb head-on. The old ladder "
         "(16 is enough) ran with 1.0 degree spread, old coating constants and "
         "the same seed, so it was not a basis. Nothing above 256 was "
         "measured."),
        ("Peak statistic", const(FM, "PEAK_STAT"), FM,
         "measured", "The brightest average over a square <b>%s mm</b> on a "
         "side. It does not change when empty area is added to the panel. p99 "
         "dropped tenfold when the same signal was only padded with zeros (the "
         "array length follows the panel size). No row averaging is done "
         "first. 2 mm comes from one arcminute of visual acuity being 1.7 to "
         "2.9 mm at 6 to 10 m [guess: the glare threshold of a laser spot was "
         "not measured]. <b>The 0.040 target was set with the maximum, the old "
         "tree and the old material, so it cannot be compared.</b>"
         % const(FM, "PEAK_BOX_MM")),
        ("Smear convergence tolerance", const(FM, "SMEAR_TOL"), FM,
         "measured", "The widest window is the value. It counts as converged "
         "only if the last two windows are within this tolerance and no more "
         "than this tolerance of the second moment remains in the outer 10 %. "
         "The old rule (the first two windows that agree) passed a signal "
         "smeared 22 times as 1.00."),
        ("Beam position sampling", const(FM, "BEAM_POS"), FM,
         "measured", "Dividing one period evenly always lands on valleys and "
         "apexes. A real laser does not land on that grid. Values differ 23 "
         "times between positions, so positions must be spread. uniform is "
         "used only to reproduce published values on exactly periodic "
         "panels."),
        ("Sampling window horizontal inset", const(FM, "MEAS_INSET_X"), FM,
         "none", "<b>No basis.</b> 20 % of the panel is cut from each side. The "
         "code says nothing about why 20 %. On 2026-08-28 it was gathered from "
         "four files into one. That fixed where it lives, not its value."),
        ("Sampling window vertical inset", const(FM, "MEAS_INSET_Z"), FM,
         "partial", "30 % itself has no basis. But a rule widens the window "
         "when 'pitch + 2 x beam' does not fit, and that rule has a physical "
         "basis."),
        ("Samples for total reflectance", const(FM, "RHO_SAMPLES"), FM,
         "none", "<b>No basis.</b> Total reflectance is an area average, so "
         "noise cancels and fewer samples than the peak axis are fine. How "
         "many is enough was never measured. The number sat in the UI code "
         "since 2026-08-24. There is no ladder test yet."),
        ("Samples for cross-checks", const(FM, "RHO_XCHECK_SAMPLES"), FM,
         "partial", "Used when comparing the two renderers. Until 2026-08-28 "
         "Mitsuba ran at 256 and Cycles at 512, <b>different from each "
         "other</b>. With different conditions the gap gets read as 'the "
         "renderers differ'. It is now one value."),
    ]

    T["USES"] = [
        ("Pixel density mm/px", "uses", "uses", "uses"),
        ("Beam width", "-", "uses", "uses"),
        ("Number of beam positions", "-", "uses", "uses"),
        ("Beam position sampling (Sobol)", "-", "uses", "uses"),
        ("Samples per pixel", "uses", "uses", "uses"),
        ("Sampling window", "-", "uses", "uses"),
        ("Peak statistic (box 2 mm)", "-", "-", "uses"),
        ("Coating tree (reciprocal)", "uses", "uses", "uses"),
        ("Control plate position (field edge + 60 mm)", "uses", "uses",
         "uses"),
    ]

    T["AXES"] = [
        dict(
            ko="Total reflectance", en="&rho;<sub>dh</sub> ratio",
            arrow="lower is better",
            what="The <b>amount</b> of light sent back",
            light="From every direction like a sky (uniform hemisphere, "
                  "radiance 1). Not a lamp.",
            formula="<b>Mean</b> of panel window pixels &divide; <b>mean</b> of "
                    "control plate window pixels",
            code="blender_render.run(): <code>ratio = s_panel['mean'] / "
                 "s_ctrl['mean']</code>",
            window="None. The whole surface is area-averaged.",
            why="Reads &rho;<sub>dh</sub>(&theta;) through Helmholtz "
                "reciprocity. One hemispherical render gives the fraction a "
                "beam from that angle sends back. No need to move the beam. "
                "<b>This reading holds only if the material obeys "
                "reciprocity.</b> The coating tree before 2026-09-15 did not.",
            risk="Uses neither beam positions nor the window. It depends on the "
                 "coating tree instead: totals measured with the old tree are "
                 "not the beam's return fraction, and the error grows with the "
                 "glossy share of the material. The current tree passes the "
                 "swap test.",
            cost="0.74 s per angle",
        ),
        dict(
            ko="Smear", en="rms width ratio", arrow="higher is better",
            what="The <b>width</b> of the light sent back",
            light="One beam stripe. Beam width vertically, the whole scene "
                  "horizontally.",
            formula="<b>rms width</b> of the panel profile &divide; rms width "
                    "of the control plate profile",
            code="form_mtf.rms_width(): treats the profile as a probability "
                 "and takes its standard deviation. "
                 "<code>sqrt(&Sigma;(z-c)&sup2;w)</code>, w = profile &divide; "
                 "sum",
            window="<b>The window is widened to the panel edge, and the widest "
                   "window is the value.</b> Converged means the last two "
                   "windows are within 2 % and no more than 2 % of the second "
                   "moment remains in the outer 10 %. The value the old rule "
                   "(stop at the first two windows that agree) would have "
                   "picked is also recorded.",
            why="Divided by the control plate so a flat plate reads 1.0. The "
                "value is then independent of panel size. If the returned "
                "light overflows the panel it reports <code>converged "
                "False</code>, and the value is a lower bound.",
            risk="The horizontal window is fixed at 60 % of the panel with no "
                 "basis. <b>Light outside the frame cannot be seen by any "
                 "rule</b>: on a small panel a far tail can be missed and "
                 "still be called converged. Before 2026-09-15 the control "
                 "plate was sometimes covered by the field (1D grooves, deep "
                 "honeycomb).",
            cost="Several minutes or more per angle (256 samples, depends on "
                 "panel and depth)",
        ),
        dict(
            ko="Head-on peak", en="2 mm box peak ratio", arrow="lower is better",
            what="The <b>brightest spot</b> of the light sent back",
            light="Uses <b>the same image</b> as smear. One render, read "
                  "twice.",
            formula="<b>Maximum mean over a 2 mm square</b> in the panel window "
                    "(2D) &divide; the same value in the control plate window, "
                    "computed per beam position and <b>averaged</b>. p99 and "
                    "the maximum are recorded for every render too.",
            code="<code>form_metrics.peak_stats</code> (summed-area table). "
                 "<code>PEAK_STAT</code> selects <code>\"p99\"</code> or "
                 "<code>\"max\"</code> to reproduce old values. Cycles and "
                 "Mitsuba use the same function.",
            window="Same window as smear. The box is fixed in mm, so the value "
                   "does not change when the window or panel grows (checked "
                   "with a synthetic counterexample).",
            why="A flat matte black plate is 1.0. 2 mm is the size an "
                "observer sees as a single point [guess]. The 0.040 target "
                "came from the maximum, the old tree and the old material, so "
                "it cannot be compared with current values. The same sample "
                "measured under the current protocol reads 0.077.",
            risk="Noise lifts the peak in dark head-on views. At 16 samples "
                 "the honeycomb head-on was +4.6 %, within 1 % only at 256. The "
                 "old maximum was +11 % at the same spot. p99 varied up to "
                 "tenfold with panel size.",
            cost="Same image as smear. No extra cost.",
        ),
    ]

    T["FINDINGS"] = [
        ("The maximum is biased upward",
         "Each pixel is unbiased, but picking the largest one introduces "
         "bias. The act of choosing creates it. More samples reduce it.",
         "On the honeycomb head-on the value came down 8 % going from 64 to "
         "2048 samples and had not settled. Splitting into two images, one to "
         "choose the spot and one to read it, showed the maximum 2.6 % above "
         "the unbiased value. At the head-on spot it was up to 9 times "
         "higher.",
         "Efron 2011 · Forde 2023 · Kriegeskorte 2009"),
        ("A percentile is not a peak either (2026-09-15)",
         "p99 is the value at the 99 % position of the array. The array length "
         "follows the panel size, so adding only dark cells to the same signal "
         "shifts the position. Averaging rows first also dilutes narrow "
         "flashes.",
         "Placing the same profile in 461 and 931 cells moved p99 from 1.0 to "
         "0.1. The maximum mean over a fixed-mm box stayed 0.800 in both. In "
         "real renders, at 40 degrees observer angle the box value was twice "
         "p99.",
         "gate_form_stats.py (synthetic counterexample) · Pawlus 2023 · "
         "evalglare manual"),
        ("The coating broke reciprocity (2026-09-15)",
         "Using a Fresnel node as the mixing weight makes the weight depend "
         "only on the viewing angle. Swapping light and observer changes the "
         "BRDF. The premise of the hemispherical reading breaks.",
         "Flat plate swap difference: old tree 238 % (old constants), 55.5 % "
         "(audit, musou_fit). New tree 0.001 %. For the target sample measured "
         "with a 0.76 diffuse material, changing only the tree moved the "
         "head-on peak by -28 %.",
         "gate_coating_reciprocity.py · Walter 2007 · PBRT microfacet model"),
        ("The control plate was covered by the field (2026-09-15)",
         "The control plate sat at a fixed distance from the panel edge, but "
         "the field extends by the margin, and extruded families by half the "
         "panel. A covered control plate reads darker than 0.05.",
         "The 500 mm grooved flat plate in the regression lock: field x 750, "
         "control plate x 600, control reading 0.0439. After moving it to the "
         "shape edge + 60 mm it read 0.05000, and all 18 lock cells 0.0 %.",
         "FINDINGS_control_overlap.md (cause proven 2026-08-12) · rig_v2"),
        ("The sampling window followed the panel size",
         "The window was 60 % of the panel, so a bigger panel meant a bigger "
         "window. A maximum grows with the number of points in the window. "
         "So panel size moved the value.",
         "The pyramid peak moved 0.467 / 0.535 / 0.508 / 0.496 / 0.502 at "
         "4/6/10/14/18 cells. Pixel density was the same throughout.",
         "Pawlus 2023 (areal maxima exceed profile maxima because of point "
         "count) · Hartigan 2013"),
        ("Beam positions divided one period evenly (now Sobol)",
         "The step always lines up with the structure's period. It always "
         "lands on the same spots. It cannot be used at all for shapes that "
         "do not repeat (STEP files, jittered apexes).",
         "For smooth periodic functions even spacing is optimal (trapezoid "
         "rule, exponential convergence). But a real laser does not land on "
         "that grid. Moving the position within one cell changed the head-on "
         "value by <b>23 times</b> (valley 0.00116, just past the apex "
         "0.02658). So we switched to Sobol.",
         "Cook 1986 · Owen 2023"),
        ("The reported value is the mean over beam positions (2026-08-28)",
         "Each beam position gives a different value. We had to decide which "
         "to report. Reporting the maximum makes the value grow with the "
         "number of positions.",
         "We read the measurement standards. All three gloss standards "
         "measure several spots, report the mean and report the spread "
         "alongside it. The maximum is used only to orient the specimen. A "
         "scanning laser is seen as a time average. So the mean is reported, "
         "with p99 and the maximum recorded separately.",
         "ASTM D523 · ASTM E430 · ISO 2813 · NPL Guide 37 · "
         "Talbot&ndash;Plateau"),
        ("A setting that lives in two places gets fixed in only one",
         "The value in the file and the value the UI actually uses drift "
         "apart. Nothing in the results shows it. The numbers are simply "
         "different.",
         "On 2026-08-28 samples were lowered from 512 to 16, yet the UI ran "
         "at <b>256</b>. The UI code was writing <code>samples: 256</code> "
         "into the request body. The same defect had happened twice before: "
         "diffuse 0.76 and roughness 0.30 were written separately in the "
         "server. The window size was spread over four files and the beam "
         "width over three, and Cycles once ran 7.5 while Mitsuba ran 2.0. "
         "<code>gate_no_shadow_defaults.py</code> now guards four things: "
         "hard-coded defaults, assignments outside the canonical file, values "
         "the UI writes into requests, and <b>whether the running server "
         "uses the same values as the file</b>.",
         "Measured (we first confirmed the gate fails on the code it "
         "guards)"),
        ("One image per beam position",
         "Time is proportional to the number of positions. Others give each "
         "ray a different starting point and do it in one pass.",
         "Placing a stripe at every position and rendering once turned it "
         "into <b>a different object</b> (smear -65 %, peak +196 %). Cycles "
         "gives no access to ray generation.",
         "genBSDF.pl · RayFlare source"),
    ]

    # 문헌은 주소·파일을 한국어 쪽에서 쓰고, 여기서는 글만 파일 이름으로 찾는다.
    T["REFS"] = {
        "efron2011.pdf": ("Efron, B. (2011)",
            "Tweedie's Formula and Selection Bias", "JASA 106(496)",
            "The largest few estimates substantially overestimate their true "
            "values. Selection bias, regression to the mean."),
        "forde2023.pdf": ("Forde, Hemani, Ferguson (2023)",
            "Review of Battling the Winner's Curse",
            "PLoS Genetics 19(9):e1010546",
            "Ranking bias. A larger sample reduces the bias considerably."),
        "kriegeskorte2009.pdf": ("Kriegeskorte et al. (2009)",
            "Circular analysis in systems neuroscience",
            "Nature Neuroscience 12",
            "Separating the data used to select from the data used to measure "
            "removes the bias. Sample splitting."),
        "pawlus2023.pdf": ("Pawlus, Reizer, &#379;elasko (2023)",
            "Characterization of the Maximum Height of a Surface Texture",
            "Materials 16(22):7109",
            "Maximum height is not a stable value. Percentiles and 'the mean "
            "of several maxima' agree with each other and are more stable. "
            "Areal maxima exceed profile maxima because of point count."),
        "evalglare_man.pdf": ("Wienold, J.", "evalglare v2.10 manual",
            "Radiance",
            "Glare sources are picked by a threshold, grouped and "
            "<b>averaged</b>. The median and 75th / 95th percentiles are "
            "reported too. No point maximum is used."),
        "nbs_mono160.pdf": ("Nicodemus et al. (1977)",
            "Geometrical Considerations and Nomenclature for Reflectance",
            "NBS Monograph 160",
            "A finite panel only loses light sideways. On an infinite panel "
            "the light coming back in from the sides makes up for it. The "
            "difference is called edge losses. The procedure for measuring "
            "the lateral travel r<sub>m</sub> is the same as our convergence "
            "test."),
        "hsia_tn594-12.pdf": ("Hsia, J. J. (1976)",
            "The Translucent Blurring Effect -- Method of Evaluation and "
            "Estimation", "NBS Technical Note 594-12",
            "A real measurement procedure sets panel size as an absolute "
            "length. A sample opening of 19 mm radius can be treated as "
            "infinite; enlarging it makes no detectable difference. Basis "
            "for sizing the panel by <b>how far light travels sideways</b> "
            "rather than by the period."),
        "iea_task61_C21.pdf": ("IEA SHC Task 61 (2021)",
            "BSDF generation procedures for daylighting systems",
            "T61.C.2.1",
            "The lit area must be at least 5 and preferably 10 times the "
            "period. <b>Ours is 0.15 times.</b> So a BSDF cannot replace the "
            "geometry."),
        "genbsdf_tut.pdf": ("McNeil, A. (2015)", "genBSDF Tutorial v1.0.1",
            "LBNL",
            "Rays starting near the edge escape without meeting geometry they "
            "would otherwise have hit. The fix is to build large and shoot "
            "only the middle. The cone example tiles 21 periods and shoots "
            "only the central one."),
        "ufdtd.pdf": ("Schneider, J. B.",
            "Understanding the Finite-Difference Time-Domain Method",
            "WSU textbook, section 3.9",
            "Wave solvers (FDTD) cut space into a finite grid and close its "
            "ends with absorbing boundaries. Ray tracing has no such grid. We "
            "cut the panel not because of a grid but <b>because the panel is "
            "infinitely wide</b>."),
        "cook86.pdf": ("Cook, R. (1986)",
            "Stochastic Sampling in Computer Graphics", "ACM TOG 5(1)",
            "A regular sample grid meeting a regular structure produces "
            "patterns. Treat the integration variable as an extra dimension "
            "and scatter samples along it."),
        "practicalqmc.pdf": ("Owen, A. (2023)",
            "Practical quasi-Monte Carlo integration", "Stanford",
            "Scrambled Sobol error falls as n<sup>&minus;1.5</sup> in the "
            "smooth case. It needs neither periodicity nor smoothness, and at "
            "worst never exceeds 2.72 times Monte Carlo."),
        "veach_thesis.pdf": ("Veach, E. (1997)",
            "Robust Monte Carlo Methods for Light Transport Simulation",
            "Stanford",
            "Efficiency is the inverse of variance times time. Helmholtz's "
            "original reciprocity applies only to mirror reflection; the real "
            "basis is the symmetry of the BSDF divided by refractive index."),
        "zirr2018_fireflies.pdf": ("Zirr, Hanika, Dachsbacher (2018)",
            "Reweighting Firefly Samples", "Computer Graphics Forum",
            "With outlier samples (fireflies) present, finite-sample "
            "estimates exceed the truth. But simply removing them biases "
            "low."),
        "kanit2003_rve.pdf": ("Kanit et al. (2003)",
            "Determination of the size of the representative volume element",
            "Int. J. Solids and Structures 40",
            "The idea of a single minimum size must be dropped. It depends on "
            "what is measured, the accuracy wanted and the number of "
            "repetitions. The answer must not depend on the boundary "
            "condition type."),
        "mcnp63.pdf": ("Kulesza et al. (2022)", "MCNP 6.3.0 manual",
            "LANL LA-UR-22-30006",
            "With a mirror boundary the whole-surface mean is exactly doubled, "
            "but a point value comes out 1.67 times, <b>always wrong and "
            "always low</b>. Periodic boundaries behave the same."),
        "D523r.txt": ("ASTM D523-89 (reapproved 1999)",
            "Standard Test Method for Specular Gloss", "ASTM E12.03",
            "Gloss is the light a specimen sends back divided by the light a "
            "standard surface sends back <b>under the same geometric "
            "conditions</b>. Our peak value (panel &divide; control plate) "
            "has this structure. At least three readings, the <b>mean</b> is "
            "reported, and readings more than 5 % from the mean are noted "
            "separately."),
        "E430.txt": ("ASTM E430-97",
            "Measurement of Gloss of High-Gloss Surfaces by Goniophotometry",
            "ASTM E12",
            "<b>The maximum is used only to decide how to orient the "
            "specimen.</b> The reported value is the mean of three areas. "
            "Basis for reporting the mean over beam positions."),
        "iso2813_1994_preview.pdf": ("ISO 2813:1994",
            "Paints and varnishes -- Determination of specular gloss of "
            "non-metallic paint films at 20&deg;, 60&deg; and 85&deg;",
            "ISO TC 35 (preview)",
            "Six readings, reported as <b>mean and range</b>. If the extremes "
            "differ by more than 10 units or 20 % of the mean, the panel is "
            "not represented by the mean but <b>rejected</b>. The 1978 "
            "edition is saved too (iso2813_1978.pdf)."),
        "mgpg37.pdf": ("Leach, R. K. (NPL)",
            "The Measurement of Surface Texture using Stylus Instruments",
            "NPL Measurement Good Practice Guide No. 37",
            "Values like maximum height are called extreme-value parameters. "
            "With no averaging they swing on a single scratch. The default "
            "is to <b>measure in five windows and average</b>. Using the "
            "maximum requires declaring it with a max suffix in advance. The "
            "window length is chosen from a table after first estimating the "
            "structure's period (ISO 4288). The ISO texts are paid, so they "
            "were read through this guide."),
        "wiki_flicker_fusion.pdf": ("Talbot&ndash;Plateau law",
            "Flicker fusion threshold", "Wikipedia",
            "When flicker is faster than the eye's fusion threshold, <b>the "
            "perceived brightness equals the time average</b>. Basis for "
            "reporting the mean rather than the maximum for a scanning laser. "
            "The threshold is about 15 Hz for rods and about 60 Hz for cones "
            "at very high luminance. The original papers (1834, 1835) were "
            "not opened."),
    }

    T["OPEN"] = [
        "<b>The 60 % horizontal sampling window has no basis.</b> Nothing "
        "says why 20 % is cut off. On 2026-08-28 the constants scattered over "
        "four files were gathered into <code>form_metrics</code>, but that "
        "fixed where they live; the value still has no basis. The gloss "
        "standard (ASTM D523) fixes the receiver window <b>as an angle</b>. "
        "Our window is not yet set that way.",
        "<b>The case for the mean holds only if the laser scans faster than "
        "the eye's threshold.</b> The Talbot&ndash;Plateau threshold is about "
        "15 Hz for rods and about 60 Hz for cones at very high luminance. "
        "How many times per second our laser redraws a frame was not "
        "measured. If a bright reflection seen by cones is redrawn slower "
        "than the threshold, flicker is visible, and the mean is then not "
        "the perceived brightness.",
        "<b>64 samples for total reflectance has no basis.</b> Total "
        "reflectance is an area average, so it can use fewer than the peak. "
        "How many is enough was never measured. The peak axis was re-measured "
        "on the real path on 2026-09-15 and needs 256, but the total axis "
        "has no ladder yet.",
        "<b>The Musou material comes from reading plots.</b> The paper has "
        "no raw data table, so the figures were read by eye. The lobe width "
        "alpha is open between 0.45 and 0.75, the absolute scale is "
        "&plusmn;20 %, and the narrow peak at 85 degrees is outside the "
        "model. The paper's sample was brush-painted.",
        "<b>The 2 mm peak box has no measured basis.</b> It comes from visual "
        "acuity. Whether it matches the size at which a laser spot looks "
        "glaring to an observer was not measured.",
        "<b>Beam positions assume periodicity.</b> Turning on "
        "<code>apex_jitter</code> or <code>row_offset</code> breaks the "
        "period, yet the code walks by the period without checking. STEP "
        "files have no value to put in.",
        "<b>We do not know why the honeycomb needed a 381 mm panel.</b> The "
        "returned light spans 3 mm, and the two rules in the literature miss "
        "by 38 times and 4 times.",
        "<b>Zero physical measurements.</b> CIE 171:2006 asks for half of the "
        "reference data to come from experiment. The simulator was checked "
        "only against simulators.",
        "<b>The roughness and diffuse share of the 5 % paint are not ours.</b> "
        "They were borrowed from MERL's black paint. Roughness moves the peak "
        "a lot (1160 times with the old tree and a narrow lobe; not "
        "re-measured with the new tree).",
    ]

    T["VALIDATION"] = [
        ("Integrating sphere",
         "&rho;<sub>eff</sub> = &rho;f / (1 &minus; &rho;(1&minus;f))",
         "A Lambertian sphere with an opening of area fraction f. The standard "
         "formula in stray-light work. Raising &rho; pushes the mean bounce "
         "count past 25, so <b>a calculator that stops early always reads "
         "low</b>",
         "Cycles error <b>0.06 %</b> · Mitsuba 0.22 %",
         "scripts/bench_sphere.py"),
        ("Infinite canyon",
         "Cosine-weighted fraction of sky visible from a point on the floor",
         "Two walls of thickness t with a floor between. Separates <b>one "
         "bounce off a thin wall</b>. A sphere has no thin walls, so it cannot "
         "see this defect",
         "Matches Cycles · only Mitsuba deviates",
         "scripts/bench_canyon.py"),
        ("Flat Lambertian",
         "&rho;<sub>dh</sub>(&theta;) = &rho; (independent of angle)",
         "Does a 0.05 reflectance plate read the same at every angle. Checks "
         "the whole measurement chain at once",
         "<b>0.0500</b> (0.050001)",
         "gate_coating_reciprocity.py check C"),
        ("Energy conservation",
         "1 in a space that absorbs no light, whatever the bounce count",
         "Is energy still there after 2048 bounces",
         "<b>0.99974</b>",
         "results/FINDINGS_renderer_disagreement.md"),
        ("Helmholtz reciprocity",
         "f<sub>r</sub>(&omega;<sub>i</sub>,&omega;<sub>o</sub>) = "
         "f<sub>r</sub>(&omega;<sub>o</sub>,&omega;<sub>i</sub>)",
         "Does swapping light and eye give the same value. <b>Reading total "
         "reflectance with hemi_view rests on this symmetry</b>",
         "New coating <b>0.001 %</b> difference · old coating off by 238 %",
         "gate_coating_reciprocity.py check A"),
        ("Second renderer",
         "Not a closed form but a different implementation",
         "The same geometry recomputed with Mitsuba 3.9.1. <b>Comparing only "
         "the two cannot tell which is right</b>, so both were run against "
         "the references above",
         "They split by 27 % on thin walls and <b>Cycles matched the "
         "reference</b>",
         "results/FINDINGS_renderer_disagreement.md"),
    ]
    return T
