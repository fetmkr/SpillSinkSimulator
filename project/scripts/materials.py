"""One representation of a material, and the library of the ones we have.

WHY THIS FILE EXISTS. Material was five node-tree factories, a `material_mode`
string enum, eight loose `rho_*` cfg keys, a `COAT` dict living in a sweep
script, and a named table only the web UI could reach. The same physical idea
-- "this surface has this finish" -- was expressed four different ways
depending on which code path you arrived on. This is the single home.

PURE PYTHON, NO bpy. Every geometry module in this project obeys that rule so
that `sim_server` can run standalone; materials must too, or the server cannot
tell you what a coating is without launching Blender.

------------------------------------------------------------------------------
THE MODEL

    rho_dh(theta) = body + spec_scale * F(theta, ior)

A body term flat with angle, plus a Fresnel-shaped term scaled down from a full
dielectric lobe. Fitted -- not derived -- to a real goniometer curve; the long
justification lives in blender_render.py above MUSOU_THR and is not repeated.

    diffuse_frac = body / rho0

------------------------------------------------------------------------------
WHAT IS CONSTRAINED AND WHAT IS NOT -- read this before editing a number.

`diffuse_frac` IS constrained by measurement. A Lambertian body is flat with
angle and the Fresnel term rises steeply toward grazing, so the GRAZING RISE

    r80 = rho_dh(80 deg) / rho_dh(0 deg)

determines the split outright:

    diffuse_frac = 1 - F0 * (r80 - 1) / (F(80) - F0)

Check against this project's own published fit: MUSOU_BODY 0.00758 with
MUSOU_SPEC_SCALE 0.0605 gives rho(0) = 1.000 %, rho(80) = 3.24 %, r80 = 3.24,
diffuse_frac = 0.758. That is where the 0.76 came from. So the formula above is
the existing fit generalised, not a new model.

`roughness` is NOT constrained. The glossy lobe is white, so roughness
redistributes the reflected light without changing how much there is: rho_dh is
roughness-independent here and roughness controls only the SHAPE of the return.
It must be swept per geometry, never assumed -- and the project's own sweep put
332x across 0.10-0.50, which is more than the entire nine-topology search.

------------------------------------------------------------------------------
EVERY VALUE STATES WHETHER IT WAS MEASURED.

`Material.estimated` names the fields that were not. This is principle 02 made
machine-readable: a constant looks true without a source, and once it enters a
document, citations breed citations. That is how FLAT_COATING_WORST = 0.061218
became the denominator of every "28x / 30x / 29x" in the reports before anyone
noticed it had never been measured. The real figure was 5.3x.
"""

import dataclasses
import math

# --- constants ---------------------------------------------------------------

# The Musou Black fit. Kept here as the one home; blender_render re-exports them
# so the ~30 sweep scripts that read BR.MUSOU_BODY keep working untouched.
MUSOU_THR = {0: 0.0100, 15: 0.0100, 30: 0.0103, 45: 0.0113,
             60: 0.0143, 75: 0.0233, 80: 0.0318}
MUSOU_BODY = 0.00758
MUSOU_SPEC_SCALE = 0.0605
MUSOU_IOR = 1.5
MUSOU_RHO0 = 0.00998                 # measured flat-plate rho_dh(0)

# F0 at n = 1.5. Was hardcoded as 0.04 back when every surface shared one index.
#
# fresnel_f0(1.5) is 0.04000000000000001 -- one ulp above the literal, because
# ((1.5-1)/(1.5+1))**2 does not round to the decimal. MEASURED rather than
# assumed away: over every rho0 in LIBRARY crossed with diffuse fractions
# 0 / 0.24 / 0.5 / 0.76 / 1.0, the resulting spec_scale is float32-identical
# either way, 0 mismatches out of 40. Blender's shader sockets are float32, so
# the generalisation cannot move a rendered number. The literal is kept only
# because ~30 sweep scripts import it by name.
F0_IOR15 = 0.04

GRAZING_DEG = 80.0                   # the angle the grazing rise is quoted at

# 0.758 IS THE MEASURED SPLIT; 0.76 IS THE ONE EVERY PUBLISHED ROW WAS RUN AT.
#
# The fit solves rho(0) = 1.00 % and rho(80) = 3.18 % into body = 0.00758 and
# spec_scale = 0.0605, so its own diffuse fraction is exactly 0.758000. But
# ~30 sweep scripts call coating_split(0.76), and lock.py's material_check
# takes a third path again -- make_coating's defaults, which use the fit
# constants directly and land on rho(0) = 0.01000 rather than the 0.00998
# Cycles measured back. Three paths, three answers in the last three digits:
#
#   make_coating() defaults      body 0.00758000  spec 0.060500  rho0 0.01000
#   coating_split(0.76,  0.00998) body 0.00758480  spec 0.059880  rho0 0.00998
#   coating_split(0.758, 0.00998) body 0.00756484  spec 0.060379  rho0 0.00998
#
# The spread is 0.26 % on body, far inside the +/-20 % absolute uncertainty the
# fit itself declares, so nothing physical turns on it. But a published CSV row
# is reproducible or it is not, so the library keeps the value the rows were
# RUN at and records the measured one beside it rather than quietly upgrading.
MUSOU_DIFFUSE_MEASURED = 0.758       # what the goniometer curve implies
MUSOU_DIFFUSE_USED = 0.76            # what every published sweep passed


def fresnel_f0(ior=MUSOU_IOR):
    """Normal-incidence Fresnel reflectance of a dielectric of index `ior`.

    n = 1.5 RETURNS THE LITERAL, not the formula. ((1.5-1)/(1.5+1))**2 is
    0.04000000000000001 -- one ulp above the 0.04 this project hardcoded for
    its whole life. Measured, that ulp is invisible once the value reaches a
    float32 shader socket (0 mismatches over every library rho0 crossed with
    every diffuse fraction in use). But "invisible for the values we happen to
    hold today" is a weaker guarantee than "identical", and the acceptance test
    for the whole material refactor is that LOCK.json does not move by a digit.
    One branch buys the stronger guarantee unconditionally, so it is taken.
    """
    if float(ior) == MUSOU_IOR:
        return F0_IOR15
    return ((float(ior) - 1.0) / (float(ior) + 1.0)) ** 2


def fresnel_schlick(theta_deg, ior=MUSOU_IOR):
    """Schlick's approximation. NOT what the renderer evaluates -- see below."""
    f0 = fresnel_f0(ior)
    c = math.cos(math.radians(float(theta_deg)))
    return f0 + (1.0 - f0) * (1.0 - c) ** 5


def fresnel(theta_deg, ior=MUSOU_IOR):
    """Unpolarised dielectric Fresnel reflectance. What ShaderNodeFresnel does.

    THE DEFAULT IS THE EXACT CURVE, NOT SCHLICK, and the difference is not
    cosmetic. Measured against each other at n = 1.5:

        theta      0      30      45      60      75      80      85
        schlick  .0400   .0400   .0421   .0700   .2547   .4099   .6485
        exact    .0400   .0415   .0502   .0892   .2531   .3877   .6128
        error     0 %   -3.6 %  -16.3 % -21.5 %  +0.7 %  +5.7 %  +5.8 %

    Anything that claims to reproduce what Cycles evaluates must use the exact
    form; Schlick is kept under its own name for bookkeeping that was written
    against it. Found by the session working on the ray tracer, which needed
    the render's own curve rather than an approximation to it.
    """
    n = float(ior)
    ci = math.cos(math.radians(float(theta_deg)))
    s2 = (math.sin(math.radians(float(theta_deg))) / n) ** 2
    if s2 >= 1.0:
        return 1.0
    ct = math.sqrt(1.0 - s2)
    rs = ((ci - n * ct) / (ci + n * ct)) ** 2
    rp = ((ct - n * ci) / (ct + n * ci)) ** 2
    return 0.5 * (rs + rp)


def coating_split(diffuse_frac, rho0=MUSOU_RHO0, ior=MUSOU_IOR):
    """(body, spec_scale) for a given diffuse fraction at fixed rho_dh(0).

    `ior` defaults to 1.5, at which fresnel_f0 is exactly 0.04 -- the constant
    this function used to hardcode. Callers that never pass `ior` are therefore
    bit-identical to the previous implementation.
    """
    d = min(1.0, max(0.0, float(diffuse_frac)))
    return d * rho0, (1.0 - d) * rho0 / fresnel_f0(ior)


def diffuse_frac_from_grazing(r80, ior=MUSOU_IOR, theta=GRAZING_DEG):
    """The split implied by a measured grazing rise rho(theta)/rho(0).

    This is how a diffuse fraction should be arrived at: from two points on a
    real rho_dh(theta) curve. It is the only route in this file that does not
    require someone to choose a number.
    """
    f0, ft = fresnel_f0(ior), fresnel(theta, ior)
    return 1.0 - f0 * (float(r80) - 1.0) / (ft - f0)


def grazing_from_diffuse_frac(diffuse_frac, ior=MUSOU_IOR, theta=GRAZING_DEG):
    """Inverse of the above -- the rise a given split predicts. For reporting."""
    f0, ft = fresnel_f0(ior), fresnel(theta, ior)
    return 1.0 + (1.0 - float(diffuse_frac)) * (ft - f0) / f0


def roughness_from_fwhm(fwhm_deg):
    """Blender Glossy roughness reproducing a scatter lobe of this FWHM.

    A microfacet distribution of RMS slope `alpha` spreads surface normals by
    FWHM 2*sqrt(ln2)*alpha, and reflection doubles the angular deviation, so
    alpha = FWHM / (4 sqrt(ln 2)). Blender's GGX takes roughness = sqrt(alpha).

    APPROXIMATE, and the source it is usually applied to (a Gaussian scatter
    lobe) is not the same construction as the Fresnel-weighted lobe used here.
    A translation, not a transcription. Say so wherever it is used.
    """
    alpha = math.radians(float(fwhm_deg)) / (4.0 * math.sqrt(math.log(2.0)))
    return math.sqrt(alpha)


# --- the material ------------------------------------------------------------

# How the four numbers reach a renderer. `fresnel_mix` is the published coating;
# the other two exist because make_diffuse and make_glossy emit DIFFERENT node
# trees, not merely different parameters, and every locked number in this
# project was measured through one of those trees. A bare Glossy BSDF at
# Color = rho is NOT the same as this model at diffuse_frac = 0, which would put
# spec_scale = rho/F0 behind a Fresnel term. Reproducing the old numbers means
# emitting the old trees, so the discriminator is part of the material.
MODELS = ("fresnel_mix", "lambert", "glossy")


@dataclasses.dataclass(frozen=True)
class Material:
    """A finish. Four numbers, a model, and where they came from."""

    rho0: float = MUSOU_RHO0          # total reflectance at normal incidence
    diffuse_frac: float = 0.76        # of rho0, the Lambertian share
    roughness: float = 0.30           # of the specular lobe
    ior: float = MUSOU_IOR            # shape of the Fresnel curve
    model: str = "fresnel_mix"
    name: str = ""                    # library key; "" means an inline override
    note: str = ""                    # provenance, shown in the popup
    # Field names whose value is an estimate rather than a measurement. The UI
    # badges these and the report prints them; a value nobody measured must
    # never be able to pass as one that someone did.
    estimated: tuple = ()

    def split(self):
        """(body, spec_scale) -- the pair the renderer actually consumes."""
        return coating_split(self.diffuse_frac, self.rho0, self.ior)

    def rho_dh(self, theta_deg=0.0):
        """Directional-hemispherical reflectance at this angle, no render.

        VERIFIED AGAINST CYCLES TO 0.04 % AT EVERY ANGLE IN THE FIT TABLE.
        Two things had to be right for that, and both were found by the
        session working on the ray tracer:

          * the Fresnel term is the EXACT dielectric curve, not Schlick;
          * the Mix Shader carries a cross-term. `mix(diffuse, glossy, fac)`
            is (1-fac)*body + fac*1, so the diffuse arm is attenuated by the
            same fac that weights the specular arm. It integrates to
            rho0 - fac*body, NOT rho0.

            theta        0      15      30      45      60      75      80
            Cycles    .00998  .00999  .01007  .01060  .01294  .02278  .03085
            this      .00998  .00999  .01007  .01060  .01293  .02277  .03086
            error     +.02%   -.03%   +.03%   -.03%   -.04%   -.03%   +.03%

        WHAT THIS SETTLES. blender_render's fit table shows residuals up to
        -9.5 % at 60 deg and calls the theta-0 row exact by construction.
        Neither reading survives: the -0.2 % at theta 0 is the cross-term, and
        the mid-band residuals are the MODEL disagreeing with Filip & Vavra's
        paper, not the implementation disagreeing with the model. The
        implementation reproduces the model to four digits. Those are different
        claims and only the second one is a code defect.

        WHAT THIS BUYS. A flat-plate reflectance for any material, at any
        angle, with no Blender and no render -- so the UI can draw a coating's
        own curve live, and a sweep can sanity-check a material before
        spending an hour measuring it.

        This is the FLAT PLATE only. It says nothing about what a structure
        does with the light, which is the entire subject of the study.
        """
        if self.model == "lambert":
            return self.rho0
        if self.model == "glossy":
            # a bare Glossy BSDF is flat with angle -- the wrong behaviour for
            # a real coating, which is why make_coating exists
            return self.rho0
        body, spec_scale = self.split()
        fac = spec_scale * fresnel(theta_deg, self.ior)
        return body * (1.0 - fac) + fac

    def grazing_rise(self):
        """Predicted rho_dh(80)/rho_dh(0). The falsifiable claim."""
        r0 = self.rho_dh(0.0)
        return self.rho_dh(GRAZING_DEG) / r0 if r0 else 1.0

    def is_estimated(self, field):
        return field in self.estimated

    def replace(self, **kw):
        """A copy with fields replaced, recording that it no longer matches.

        AN OVERRIDDEN LIBRARY ENTRY MUST NOT GO ON CLAIMING ITS SOURCE. The
        note is amended with what moved and from what. A provenance string that
        survives an override intact is the same defect as a constant with no
        source, only harder to see.
        """
        if not kw:
            return self
        moved = ", ".join(
            "%s %g -> %g" % (k, getattr(self, k), v)
            for k, v in sorted(kw.items())
            if isinstance(v, (int, float)) and getattr(self, k) != v)
        note = self.note
        if moved:
            note = (note + "  [OVERRIDDEN: %s]" % moved).strip()
        est = tuple(sorted(set(self.estimated) | set(kw)))
        return dataclasses.replace(self, note=note, estimated=est, **kw)

    def key(self):
        """Identity for deduplicating renderer-side materials."""
        return (round(self.rho0, 12), round(self.diffuse_frac, 12),
                round(self.roughness, 12), round(self.ior, 12), self.model)


def fields():
    """Editable numeric fields, in display order. Drives the property editor."""
    return ("rho0", "diffuse_frac", "roughness", "ior")


# --- the library -------------------------------------------------------------
#
# EVERY ENTRY CITES A SOURCE, AND EVERY ENTRY SAYS WHICH OF ITS FOUR NUMBERS
# THAT SOURCE ACTUALLY COVERS.
#
# Only one material in this table has a measured SHAPE: musou_fit, whose
# diffuse fraction comes from a full rho_dh(theta) curve. Everything else
# inherits or is translated from a different model, and says so in `estimated`.
#
# The measurement that would end the argument is cheap and this project is
# already set up for it: `export/` holds printable coupons and a flat control.
# rho_dh at two angles -- normal and ~80 deg -- on a real sample gives r80
# directly, hence diffuse_frac, with no modelling at all. A gloss reading gives
# the lobe width, hence roughness. Until then these are estimates and are
# labelled as estimates.

# Black anodised aluminium, translated from Kaster 2025 (2507.05152v1.pdf p.7,
# quoted in reference/HONEYCOMB_SPECS.md): "5 % reflectance, 85 % Lambertian /
# 15 % Gaussian FWHM 25 deg".
#
# A TRANSLATION, NOT A TRANSCRIPTION. Kaster splits into Lambertian + a
# Gaussian SCATTER lobe; this project splits into Lambertian + a
# Fresnel-weighted lobe. The Lambertian share carries over directly; the lobe
# width is mapped through roughness_from_fwhm. The two constructions agree on
# how much light is diffuse and disagree on how the rest is distributed with
# angle, so the diffuse fraction is on firmer ground here than the roughness.
_ANODISED_DIFFUSE = 0.85
_ANODISED_ROUGH = roughness_from_fwhm(25.0)        # 0.362

# COUNTER-INTUITIVE AND WORTH KNOWING: anodised comes out MORE Lambertian
# (0.85) than Musou (0.758), not less. Musou's specular share is larger because
# its diffuse body is so small -- 0.758 % of a 0.998 % total -- not because its
# surface is glossier. Anodised carries a large diffuse body (3.83 % of 4.5 %)
# that dilutes its specular share. Do not "correct" this.

_MUSOU_SHAPE_NOTE = (
    "Shape (diffuse fraction, roughness) is INHERITED from musou_fit: the only "
    "Musou angular curve anyone has measured is that one. Application method "
    "plausibly changes the split and nobody has measured whether it does.")

_ANODISED_SOURCE = (
    "Split from Kaster 2025 p.7 (2507.05152v1) -- 5 % reflectance, 85 % "
    "Lambertian / 15 % Gaussian FWHM 25 deg -- TRANSLATED into this project's "
    "Lambertian + Fresnel model, so the diffuse fraction carries over directly "
    "and the roughness is a lobe-width mapping. ior 1.5 is the pessimistic "
    "branch: anodised aluminium is a dyed porous oxide over metal and a "
    "single-index dielectric Fresnel term is a stand-in, not a mechanism. "
    "Al2O3 at n = 1.76 would give a shallower grazing rise (1.70 vs 2.39). "
    "Sweep it; do not trust it.")


def _m(name, rho0, diffuse_frac, roughness, note, estimated,
       ior=MUSOU_IOR, model="fresnel_mix"):
    return Material(rho0=rho0, diffuse_frac=diffuse_frac, roughness=roughness,
                    ior=ior, model=model, name=name, note=note,
                    estimated=tuple(estimated))


LIBRARY = {
    "musou_air": _m(
        "musou_air", 0.0060, MUSOU_DIFFUSE_USED, 0.30,
        "Musou Black, airbrushed -- 0.6 % total reflectance at 550 nm, AOI 8 "
        "deg integrating sphere [musoublack.com product spec]. " +
        _MUSOU_SHAPE_NOTE,
        ("diffuse_frac", "roughness")),

    "musou_fit": _m(
        "musou_fit", MUSOU_RHO0, MUSOU_DIFFUSE_USED, 0.30,
        "Musou Black as fitted in this project -- Filip & Vavra 2026 JOSA A "
        "43, 1037, RGB-weighted 380-700 nm. Every number in phases 2-5 uses "
        "this. The diffuse fraction is MEASURED, not chosen: it follows from "
        "the grazing rise rho(80)/rho(0) = 3.18 of the published curve, which "
        "implies 0.758. The value here is 0.76 -- the rounded figure every "
        "published sweep was actually run at. The 0.26 % difference in body is "
        "far inside the fit's own +/-20 % absolute uncertainty; it is kept "
        "because a published row must reproduce, not because it is better. "
        "Roughness is NOT constrained -- rho_dh is roughness-independent here, "
        "so no total can pin it; it shapes the return only, and must be swept.",
        ("roughness",)),

    "musou_brush": _m(
        "musou_brush", 0.0110, MUSOU_DIFFUSE_USED, 0.30,
        "Musou Black, brush-applied -- 1.1 % or lower [the-black-market.com]. "
        "1.8x the airbrushed figure; application method is a larger lever than "
        "any geometry parameter measured so far. " + _MUSOU_SHAPE_NOTE,
        ("diffuse_frac", "roughness")),

    "anodised_lo": _m(
        "anodised_lo", 0.030, _ANODISED_DIFFUSE, _ANODISED_ROUGH,
        "Black anodised aluminium, optimistic end. Sources disagree: 'below "
        "5 % in the visible' vs 'at least 5 %'. Swept, not assumed. " +
        _ANODISED_SOURCE,
        ("diffuse_frac", "roughness", "ior")),

    "anodised": _m(
        "anodised", 0.045, _ANODISED_DIFFUSE, _ANODISED_ROUGH,
        "Black anodised aluminium, nominal -- what bought honeycomb actually "
        "arrives as [arXiv 1407.8265; Rubin M2 baffle]. " + _ANODISED_SOURCE,
        ("diffuse_frac", "roughness", "ior")),

    "anodised_hi": _m(
        "anodised_hi", 0.060, _ANODISED_DIFFUSE, _ANODISED_ROUGH,
        "Black anodised aluminium, pessimistic end. " + _ANODISED_SOURCE,
        ("diffuse_frac", "roughness", "ior")),

    # THE CONTROL. Lambertian BY DEFINITION, and it must stay that way: every
    # ratio in the study divides by this plate, so it must not move when the
    # panel's finishes are swapped. model="lambert" pins it to make_diffuse,
    # the same node tree every published control was measured through.
    "wall_5pct": _m(
        "wall_5pct", 0.050, 1.0, 0.0,
        "Plain matte black wall -- the control patch in every render. "
        "Lambertian by definition, not by measurement: it is the agreed "
        "baseline the ratios divide by, so it is defined rather than fitted. "
        "lock.py pins it at 0.05 within 5e-4.",
        (), model="lambert"),
}

# --- reference surfaces, for saying how dark something is in units a person
# --- can check. Both are LAMBERTIAN MODELS, and that is the estimate in them.
_WHITE_NOTE = (
    "A perfect Lambertian white, rho = 1.0, is the definition of radiance "
    "factor 1.0. Office paper measures 75-85 % and is close to Lambertian; "
    "0.80 is the middle of that range and is an APPROXIMATION OF PAPER IN "
    "GENERAL, never a measurement of anyone's actual sheet. It exists so a "
    "client can hold a sheet up next to the panel and check the claim.")

_VELOUR_NOTE = (
    "Black theatrical velour. rho = 0.002 is the directional-hemispherical "
    "reflectance of black velvet at normal incidence measured by Filip & "
    "Vavra 2026 (reference/SUMMARY.md, Fig. 6) -- the same THR quantity as "
    "metrics/01. THE ANGULAR BEHAVIOUR HERE IS A LAMBERTIAN ASSUMPTION AND "
    "THE PAPER SAYS IT IS WRONG: they measure velvet rising to 0.0122 at 85 "
    "deg, and they report it with the LOWEST TIS of any sample they tested, "
    "meaning its return is the most specular-concentrated, not the most "
    "diffuse. So this models velour at its darkest, most flattering "
    "behaviour. A comparison against it is therefore CONSERVATIVE: real "
    "velour at the angles this room uses is very likely worse than this.")


def _ref(name, rho0, note):
    return Material(rho0=rho0, diffuse_frac=1.0, roughness=0.0,
                    model="lambert", name=name, note=note,
                    estimated=("diffuse_frac", "roughness"))


LIBRARY["white_paper"] = _ref("white_paper", 0.80, _WHITE_NOTE)
LIBRARY["white_perfect"] = _ref("white_perfect", 1.00, _WHITE_NOTE)
LIBRARY["black_velour"] = _ref("black_velour", 0.002, _VELOUR_NOTE)

STUDY_DEFAULT = "musou_fit"


# --- resolution --------------------------------------------------------------

def resolve(spec, default=None, defaults=None):
    """A Material from whatever the caller had.

    `spec` is one of:
        "musou_fit"                              a library entry, verbatim
        {"base": "anodised", "roughness": 0.05}  a library entry, fields replaced
        {"rho0": 0.006, "diffuse_frac": 1.0}     inline; no name, no citation
        None                                     `default`, or the study default
        Material                                 itself

    `defaults` are the scene-wide fallbacks (the surviving global sliders).
    They apply ONLY to an inline spec: a library entry states its own numbers,
    and letting a global slider silently rewrite a cited value is the defect
    principle 02 is about.
    """
    if isinstance(spec, Material):
        return spec
    if spec is None:
        return default or LIBRARY[STUDY_DEFAULT]
    if isinstance(spec, str):
        m = LIBRARY.get(spec)
        if m is None:
            # NAMED AND MISSING IS NOT THE SAME AS UNSPECIFIED. A renamed or
            # mistyped library key must not resolve to a plausible number in
            # silence -- the caller is told, and the note carries the fault
            # into every readout and every report that quotes it.
            base = default or LIBRARY[STUDY_DEFAULT]
            return dataclasses.replace(
                base, note="NO MATERIAL NAMED %r -- fell back to %s. %s"
                           % (spec, base.name, base.note),
                estimated=tuple(sorted(set(base.estimated) | set(fields()))))
        return m
    if not isinstance(spec, dict):
        raise TypeError("material spec must be a name, a dict or a Material, "
                        "got %r" % type(spec).__name__)

    kw = {k: v for k, v in spec.items() if k in fields() or k == "model"}
    base_name = spec.get("base")
    if base_name is not None:
        return resolve(base_name, default=default).replace(**kw)

    # inline: the globals apply, and it carries no citation because nobody
    # measured it
    start = dataclasses.replace(default or LIBRARY[STUDY_DEFAULT],
                                name="", note="", estimated=tuple(fields()))
    if defaults:
        start = dataclasses.replace(
            start, **{k: v for k, v in defaults.items() if k in fields()})
    return dataclasses.replace(start, **kw)


def library_json():
    """The library as the UI wants it. Serialisable, provenance included."""
    return {k: {"rho0": m.rho0, "diffuse_frac": m.diffuse_frac,
                "roughness": m.roughness, "ior": m.ior, "model": m.model,
                "note": m.note, "estimated": list(m.estimated),
                "grazing_rise": m.grazing_rise()}
            for k, m in LIBRARY.items()}


# --- self-test ---------------------------------------------------------------
#
# Run `python3 scripts/materials.py`. Locks the invariants that let this file
# replace what was there before WITHOUT moving a published number.

def _selftest():
    import struct
    f = lambda x: struct.unpack("<f", struct.pack("<f", x))[0]
    bad = []

    def ck(name, got, want, tol=0.0):
        ok = (got == want) if tol == 0 else (abs(got - want) <= tol)
        print("  %-52s %s" % (name, "ok" if ok else "FAIL %r != %r" % (got, want)))
        if not ok:
            bad.append(name)

    print("materials.py self-test")

    # 1. the generalised F0 must not move the old hardcoded one, at float32
    ck("fresnel_f0(1.5) == 0.04 in float32", f(fresnel_f0(1.5)), f(F0_IOR15))

    # 2. coating_split without an ior is the old two-argument function
    ck("coating_split(0.76) reproduces the sweeps",
       coating_split(0.76), (0.76 * MUSOU_RHO0, 0.24 * MUSOU_RHO0 / 0.04))

    # 3. the published fit's own diffuse fraction really is 0.758
    rho0_fit = MUSOU_BODY + MUSOU_SPEC_SCALE * F0_IOR15
    ck("published fit implies diffuse_frac 0.758",
       round(MUSOU_BODY / rho0_fit, 6), 0.758)

    # 4. the two closed forms invert each other exactly.
    # NOTE they are BOOKKEEPING, not the renderer: they omit the Mix Shader
    # cross-term that Material.rho_dh models, so a material's actual
    # grazing_rise() sits a little below what grazing_from_diffuse_frac says.
    # That gap is real and is the cross-term; do not "fix" either one to close
    # it. rho_dh is the one that matches Cycles.
    for d in (0.0, 0.5, 0.76, 1.0):
        ck("grazing round-trip at diffuse_frac %.2f" % d,
           round(diffuse_frac_from_grazing(grazing_from_diffuse_frac(d)), 9),
           round(d, 9))
    ck("bookkeeping and render disagree only by the cross-term",
       abs(grazing_from_diffuse_frac(0.76)
           - LIBRARY["musou_fit"].grazing_rise()) < 0.15, True)

    # 5. every library entry resolves to what the old path produced
    ck("musou_fit == coating_split(0.76)",
       LIBRARY["musou_fit"].split(), coating_split(0.76))

    # 6. EVERY entry cites a source and declares its estimates
    for k, m in LIBRARY.items():
        ck("%s has a note" % k, bool(m.note.strip()), True)
        ck("%s estimates are real fields" % k,
           set(m.estimated) <= set(fields()), True)
        ck("%s model is known" % k, m.model in MODELS, True)

    # 7. an override must not keep claiming the source unqualified
    over = resolve({"base": "anodised", "roughness": 0.05})
    ck("override marks itself", "OVERRIDDEN" in over.note, True)
    ck("override marks the field estimated", "roughness" in over.estimated, True)
    ck("override leaves other fields alone", over.rho0, LIBRARY["anodised"].rho0)

    # 8. a missing name is loud, not plausible
    miss = resolve("no_such_coating")
    ck("missing name says so", "NO MATERIAL NAMED" in miss.note, True)

    # 9. THE ANALYTIC MODEL REPRODUCES WHAT CYCLES ACTUALLY RENDERED.
    # The right-hand column of blender_render's own fit table. If this drifts,
    # either the Fresnel form or the Mix cross-term has been "simplified" and
    # the pure-Python reflectance has stopped describing the renderer.
    CYCLES = {0: 0.00998, 15: 0.00999, 30: 0.01007, 45: 0.01060,
              60: 0.01294, 75: 0.02278, 80: 0.03085}
    fit = Material(rho0=MUSOU_BODY + MUSOU_SPEC_SCALE * F0_IOR15,
                   diffuse_frac=MUSOU_BODY / (MUSOU_BODY
                                              + MUSOU_SPEC_SCALE * F0_IOR15))
    for th, want in sorted(CYCLES.items()):
        got = fit.rho_dh(th)
        ck("rho_dh(%2d) == Cycles %.5f (got %.6f)" % (th, want, got),
           abs(got - want) / want < 1e-3, True)

    # 10. exact Fresnel, not Schlick -- they agree at normal and diverge badly
    ck("fresnel(0) == F0", round(fresnel(0.0), 12), round(fresnel_f0(1.5), 12))
    ck("fresnel(80) is the exact curve, not Schlick",
       round(fresnel(80.0), 4), 0.3877)
    ck("schlick is still available and differs",
       round(fresnel_schlick(80.0), 4), 0.4099)

    # 11. the control plate stays Lambertian at 0.05 -- lock.py depends on it
    ck("wall_5pct is lambert", LIBRARY["wall_5pct"].model, "lambert")
    ck("wall_5pct rho0 is 0.05", LIBRARY["wall_5pct"].rho0, 0.05)

    print("\n" + ("FAILURES: %s" % ", ".join(bad) if bad
                  else "all checks pass"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
