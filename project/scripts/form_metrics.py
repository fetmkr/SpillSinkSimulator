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


# 재는 창을 판 가장자리에서 얼마나 안쪽으로 들이는가. 가로는 20 %, 세로는
# 30 % 다. 세로를 더 깎는 것은 날개가 판 밖으로 넘어가기 때문이다.
#
# 이 두 숫자가 2026-08-28 까지 네 파일에 따로 적혀 있었다 -- `blender_render`,
# `mts_form`, `crosscheck_mitsuba`, 그리고 `mts_worker` 는 0.0 을 넣었다.
# 한 군데만 고치면 Cycles 와 Mitsuba 가 서로 다른 넓이를 재고, 그 차이를
# 빛 계산의 차이로 읽게 된다. 그래서 이 파일이 사는 이유(하나만 적어 둔다)에
# 창 크기도 같이 넣는다.
#
# **20 % / 30 % 자체에는 아직 근거가 없다.** 왜 이 값이어야 하는지 잰 적이
# 없다. 정본을 한 곳으로 모으는 것과 값을 고르는 것은 별개의 일이고,
# 여기서는 앞의 것만 한다.
MEAS_INSET_X = 0.20
MEAS_INSET_Z = 0.30

# 재는 빔의 너비. 실제로 벽에 맺히는 굵기다 (LaserCube Ultra MK2, 던지는
# 거리 3-6 m 에서 5-10 mm, 그 가운데를 잡았다). 사용자가 2026-08-16 에
# 정했다 -- "빔 2mm 쓰지마. 기본을 5-10mm". 2.0 으로 낸 옛 숫자와 견주려면
# 부르는 쪽이 STRIPE_W 를 직접 넣어야 한다.
#
# 이 숫자도 `form_buildable`, `mts_form`, `sim_server` 세 군데에 따로 적혀
# 있었다. Cycles 는 7.5, Mitsuba 는 2.0 을 써서 두 렌더러가 서로 다른 실험을
# 하고 있던 적이 있다 (2026-08-20 에 잡았다). 여기 하나만 둔다.
STRIPE_W = 7.5

# 반사 총량을 잴 때 화소마다 쏘는 빛줄기 수. 총량은 넓이 평균이라 잡음이
# 넓이에 걸쳐 상쇄된다. 그래서 봉우리를 읽는 축(`form_buildable.SAMPLES`)
# 보다 적게 써도 된다.
#
# **64 라는 숫자에는 아직 근거가 없다.** 화면 코드에 2026-08-24 부터 그냥
# 적혀 있었고, 얼마면 되는지 잰 적이 없다. 사다리 검사를 아직 안 만들었다.
# 여기 옮겨 놓은 것은 값을 정한 것이 아니라 값이 사는 자리를 정한 것이다.
RHO_SAMPLES = 64

# 두 렌더러를 맞대 볼 때 쓰는 빛줄기 수. 2026-08-28 까지 Mitsuba 쪽은 256,
# Cycles 쪽은 512 로 **서로 다르게** 돌고 있었다. 같은 값을 견주는 자리에서
# 조건이 다르면 그 차이를 "렌더러가 다르다" 로 읽게 된다. 하나로 묶는다.
RHO_XCHECK_SAMPLES = 512


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
