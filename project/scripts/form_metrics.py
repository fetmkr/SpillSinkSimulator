"""The form metrics, as pure arithmetic on an image. No renderer, no bpy.

Extracted from `form_buildable.py` unchanged so that a SECOND renderer can be
scored by the identical code. That is the whole point: if Mitsuba reimplemented
`rms_width` and disagreed with Cycles, the disagreement could be in the
statistic rather than in the light transport, and the cross-check would prove
nothing. Both codes now produce an image and hand it to these four functions.

`form_buildable.py` imports from here rather than defining its own copies, so
there is one definition and it cannot drift.
"""

import numpy as np


def z_profile(arr, win):
    """Collapse a window to a 1D profile along Z by averaging over X and RGB."""
    x0, x1, z0, z1 = win
    sub = arr[int(z0):int(z1), int(x0):int(x1), :].mean(axis=2)
    return sub.mean(axis=1)


def recentre(prof, n):
    """Re-window `prof` to `n` samples about its centroid.

    The stripe lands wherever the phase put it; comparing widths requires a
    common origin, and the centroid is the one the rms is measured about
    anyway.
    """
    idx = np.arange(prof.size, dtype=np.float64)
    tot = prof.sum()
    c = float((idx * prof).sum() / tot) if tot > 1e-20 else prof.size / 2.0
    out = np.zeros(n)
    lo = int(round(c)) - n // 2
    for i in range(n):
        j = lo + i
        if 0 <= j < prof.size:
            out[i] = prof[j]
    return out


def rms_width(prof, mm_per_px):
    """Metric 02: the rms spread of the returned line, in mm."""
    tot = prof.sum()
    if tot <= 1e-20:
        return float("nan")
    z = (np.arange(prof.size) - prof.size / 2.0) * mm_per_px
    w = prof / tot
    c = float((z * w).sum())
    return float(np.sqrt(max(float(((z - c) ** 2 * w).sum()), 0.0)))


def mtf_at(prof, mm_per_px, periods):
    """Metric 07, supporting only: |FFT| at the named spatial periods."""
    p = prof - prof.min()
    if p.sum() <= 1e-20:
        return {"mtf_%dmm" % int(q): float("nan") for q in periods}
    f = np.fft.rfft(p)
    freqs = np.fft.rfftfreq(p.size, d=mm_per_px)
    out = {}
    for q in periods:
        k = int(np.argmin(np.abs(freqs - 1.0 / q)))
        out["mtf_%dmm" % int(q)] = float(np.abs(f[k]) / np.abs(f[0]))
    return out
