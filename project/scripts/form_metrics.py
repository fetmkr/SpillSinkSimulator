"""The form metrics, as pure arithmetic on an image. No renderer, no bpy.

Extracted from `form_buildable.py` unchanged so that a SECOND renderer can be
scored by the identical code. That is the whole point: if Mitsuba reimplemented
`rms_width` and disagreed with Cycles, the disagreement could be in the
statistic rather than in the light transport, and the cross-check would prove
nothing. Both codes now produce an image and hand it to these functions.

`form_buildable.py` imports from here rather than defining its own copies, so
there is one definition and it cannot drift.

THE PROTOCOL CONSTANTS LIVE HERE TOO (2026-09-15). `SAMPLES`, `N_PHASE`,
`MM_PER_PX`, `SPREAD_DEG`, the peak statistic and the beam-position rule used to
be defined in `form_buildable`, which imports `bpy`. A server started in plain
Python could therefore not read its own defaults: `/api/form` with the Mitsuba
renderer died on `No module named 'bpy'` the moment it asked for `N_PHASE`
(code review of d3dbe5b, reproduced). This module opens without Blender, so
both launch modes and both renderers read the same values from here.
`form_buildable` re-exports them, so `FB.SAMPLES` still names the same thing.
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
# 넓이에 걸쳐 상쇄된다. 그래서 봉우리를 읽는 축(`SAMPLES`) 보다 적게 써도 된다.
#
# **64 라는 숫자에는 아직 근거가 없다.** 화면 코드에 2026-08-24 부터 그냥
# 적혀 있었고, 얼마면 되는지 잰 적이 없다. 사다리 검사를 아직 안 만들었다.
# 여기 옮겨 놓은 것은 값을 정한 것이 아니라 값이 사는 자리를 정한 것이다.
#
# 2026-09-15: 256 으로 올린다. 최종 후보 측정(measure_finalists.py)이 256 으로
# 쟀고, 사용자가 그 값을 화면에서 같은 기준으로 다시 내 보기로 했다. 화면과
# 보고서가 다른 빛줄기로 재면 검증이 아니다. **256 도 사다리로 정한 값은 아니다**
# -- 총량 축 사다리는 아직 없다.
RHO_SAMPLES = 256

# ---- 방 조건 (2026-09-15) ----------------------------------------------------
# 천장 6 m, 프로젝터 높이 2 m 에서 45~60 도 위로 (room-decides-the-angles). 패널이
# 받는 빔은 30~45 도, 관객은 0~60 도에서 본다. 최종 후보 보고서와 시뮬레이터
# 화면이 **이 목록 하나**를 읽는다. 여기 말고 다른 곳에 각도를 적지 않는다.
ROOM_TOTAL_THETAS = (0.0, 20.0, 30.0, 40.0, 45.0, -20.0, -40.0)   # 총량 입사각
ROOM_TOTAL_PHIS = (0.0, 45.0)                                     # 총량 방위
FORM_THETAS = (-40.0, 0.0, 30.0, 40.0)    # 뭉개기·반짝임 빔 각도. +-40 은 뭉개기 정의
FORM_PHIS = (0.0,)                        # 뭉개기·반짝임 방위. 화면 버튼도 이것만 잰다
ROOM_OBSERVERS = (0.0, 20.0, 40.0, 60.0)  # 관객 각도 (화면에서는 하나씩 고른다)
# 스치는 각 (2026-09-18). 천장이 6 m 가 아니라 3.5 m 라 빔이 천장에 맞는 각이
# 45~78 도다. 위 목록은 0~45 뿐이라 방의 대부분을 못 잰다. 이 목록은 **규약이 아니고
# 순위에도 안 들어간다** -- 화면의 "스치는 각도까지 재기" 칸과 스크립트가 요청에만 더한다.
# 처음에 55·65·75 셋만 적었다가 "70 도가 왜 빠졌냐" 로 걸렸다. 근거 있는 선택이 아니었다.
# 5 도 간격으로 채운다. 화면·추적기·측정 스크립트가 전부 이 하나를 읽는다.
GRAZE_THETAS = (55.0, 60.0, 65.0, 70.0, 75.0, -55.0, -60.0, -65.0, -70.0, -75.0)
# 순위를 매길 때 보는 부분집합
RANK_TOTAL_THETAS = (30.0, 40.0, 45.0, -40.0)
RANK_BEAMS = (-40.0, 30.0, 40.0)          # -40 은 프로젝터 반대편 관객 (거울 방향)
RANK_OBSERVERS = (20.0, 40.0, 60.0)

# 두 렌더러를 맞대 볼 때 쓰는 빛줄기 수. 2026-08-28 까지 Mitsuba 쪽은 256,
# Cycles 쪽은 512 로 **서로 다르게** 돌고 있었다. 같은 값을 견주는 자리에서
# 조건이 다르면 그 차이를 "렌더러가 다르다" 로 읽게 된다. 하나로 묶는다.
RHO_XCHECK_SAMPLES = 512

# 빛줄기(표본) 수. 512 는 최대값을 쓰던 시절의 값이다 -- 최대값이 잡음을
# 신호로 읽으니 잡음을 없애야 했다. p99 로 바꾸면 그 이유가 사라진다.
# 실측: 모양 셋 x 각도 넷, 열두 경우에서 p99 가 4~16 개부터 512 개 값과
# 1 % 안에서 같았다 (`gate_sample_budget.py`). 뭉개기는 4 개에서도 1 % 안.
# 16 으로 둔다. 그보다 낮추면 어두운 자리에서 p99 도 흔들리기 시작한다.
#
# **2026-09-14 감사: 그 근거 실험은 지금 광원과 다르다.** `gate_sample_budget`
# 은 SPREAD 1.0 도(지금 0.05 도)로 돌았고, 코팅 상수가 cfg 의 엉뚱한 칸에 들어가
# 옛 무소 상수로 렌더됐다. 16 이 모자란다는 증거는 아니지만, 16 이 충분하다는
# 근거도 지금 조건에서는 없다.
#
# **2026-09-15: 실제 경로로 다시 쟀고, 16 은 모자란다.** `gate_sample_budget.py`
# (results/comb20/sample_budget_v2.json): 모양 셋 x 각도 넷 = 열두 경우, 씨앗 둘,
# 참값은 256 두 씨앗 평균. 판정 "참값과 1 % 안, 두 씨앗 차 1 % 안, 열두 경우 전부".
#
#     뭉개기   8 부터 충분 (모든 경우 0.3 % 안)
#     p99     64
#     box     256 만 통과. 16 에서 벌집 9.53/40 빔 40 관찰 0 이 +4.55 %,
#             피라미드 50/250 관찰 60 이 -1.37 %, 벌집 30/30 이 -1.23 % (씨앗 차 1.28 %).
#             64 에서도 벌집 정면이 +1.84 %.
#     max     256
#
# 정면 반짝임을 box 로 읽으므로 box 가 요구하는 256 으로 올린다. 어두운 정면
# (벌집 정면)에서 잡음이 봉우리를 위로 끌어올린다 -- 최대값이 잡음을 신호로 읽는
# 것과 같은 꼴이 box 에도 작게 남는다. 256 이 참값에서 얼마나 떨어져 있는지는
# 모른다 [모름: 256 보다 위를 안 쟀다. 벌집 정면이 64 -> 256 에서 1.8 % 움직였다].
SAMPLES = 256

# Sampling density in mm per pixel, held FIXED so the instrument does not
# change with the sample (see the note in form_buildable.run_case). Set to 0 to
# restore the pre-2026-08-20 behaviour of a constant pixel count, which is what
# every published number was measured with.
MM_PER_PX = 0.215

# The stripe lamp's angular spread. 0.05 deg is near-collimated.
SPREAD_DEG = 0.05

N_PHASE = 16                     # stripe positions across one pitch

# HOW THE PEAK IS READ.
#
# 2026-08-28: it used to be the MAXIMUM of the profile. A maximum picked out of a
# noisy estimate is biased HIGH -- picking the largest of many noisy values picks
# the ones the noise helped (Efron 2011; Forde 2023 for the ranking form). We
# measured it: splitting a render in two, finding the position in image A and
# reading image B (Kriegeskorte 2009), the maximum read 2.6 % high on the darkest
# case and up to 9x high looking head-on at a deep pyramid. The 99th percentile
# matched the split-sample value to within 1 % everywhere, from 4 spp upward.
# Pawlus 2023 calls maximum height "not a stable parameter"; Radiance's evalglare
# groups and averages each glare source instead of taking a point maximum.
#
# 2026-09-15: **p99 is not a peak either.** It is the value at the 99th
# percentile POSITION of the array, and the array's length is set by the panel
# height: padding the same profile with zeros moves that position. Measured with
# the project's own `recentre`: one narrow bright return (7 px at 1.0 inside a
# 35 px beam at 0.1) reads 1.0 at 465 samples and 0.1 at 931 -- ten times darker
# because the panel got bigger (results/audit_2026_09_14/arithmetic_probe.json).
# And it averages over X first, so a point glint is diluted by the window width.
#
# `box` is the new default: the brightest mean over a FIXED PHYSICAL square of
# PEAK_BOX_MM on a side, read from the 2D window before any averaging. It does
# not depend on how much dark panel surrounds the return, and averaging a
# box rather than taking one pixel keeps most of the noise out of the maximum
# (2 mm at 0.215 mm/px is ~9 x 9 = 81 pixels).
#
# WHY 2 mm. A person resolves about one arc-minute. The audience stands 6 to
# 10 m from a ceiling panel (`room-decides-the-angles`): 1 arcmin is 1.7 mm at
# 6 m and 2.9 mm at 10 m. A bright patch smaller than that is not seen as a
# patch, it is averaged with its surroundings by the eye. [추측: 1 arcmin 은
# 교과서 값이고 레이저 반점의 눈부심 문턱은 따로 잰 적이 없다.]
#
# `p99` and `max` stay available to reproduce published figures, and every run
# records all three. THE HEAD-ON TARGET 0.040 WAS SET ON `max`; it does not
# carry over to `box` and has to be re-measured on the reference sample.
PEAK_STAT = "box"                # "box", "p99" or "max"
PEAK_PCT = 99.0
PEAK_BOX_MM = 2.0

# BEAM POSITIONS (2026-08-28). `uniform` walks one pitch in equal steps: the
# trapezoid rule on a periodic function, which is the best way to average one.
# It is still the wrong thing to do here, for a physical reason: equal steps
# land on the same features every time, and a real laser does not respect our
# grid. On the base-50 pyramid at 512 spp, beam 40 deg, read head-on, one pitch
# spans 0.00116 in the valley to 0.02645 near the apex, 22.7x. `sobol` fills the
# gaps rather than repeating a lattice, needs neither periodicity nor
# smoothness, and is bounded at 2.72x plain Monte Carlo in the worst case
# (Owen 2023). Keep `uniform` for reproducing a published figure.
BEAM_POS = "sobol"               # "sobol" or "uniform"

# Two successive windows whose smear differs by less than this are "stable".
SMEAR_TOL = 0.02


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


# --- the peak -----------------------------------------------------------------

def box_max_2d(lum, bx, bz):
    """Largest mean over any bz-by-bx box of a 2D array, by summed-area table.
    A box larger than the array is clipped to the array."""
    lum = np.asarray(lum, dtype=np.float64)
    nz, nx = lum.shape
    if nz == 0 or nx == 0:
        return float("nan")
    bx = int(min(max(1, bx), nx))
    bz = int(min(max(1, bz), nz))
    S = np.zeros((nz + 1, nx + 1))
    S[1:, 1:] = lum.cumsum(axis=0).cumsum(axis=1)
    tot = S[bz:, bx:] - S[:-bz, bx:] - S[bz:, :-bx] + S[:-bz, :-bx]
    return float(tot.max() / (bx * bz))


def box_max_1d(prof, mm_per_px, box_mm=None):
    """The same statistic on a 1D profile: the largest mean over a run of
    `box_mm`. Independent of zero padding by construction."""
    box_mm = PEAK_BOX_MM if box_mm is None else box_mm
    p = np.asarray(prof, dtype=np.float64)
    b = int(min(max(1, round(box_mm / mm_per_px)), p.size))
    c = np.concatenate([[0.0], p.cumsum()])
    return float((c[b:] - c[:-b]).max() / b)


def window_lum(arr, win):
    x0, x1, z0, z1 = win
    return arr[int(z0):int(z1), int(x0):int(x1), :].mean(axis=2)


def peak_stats(arr, win, prof, mm_x, mm_z, box_mm=None):
    """Every peak statistic of one frame, so a run records all of them.

        box   brightest PEAK_BOX_MM square, from the 2D window   (the default)
        p99   99th percentile of the recentred 1D profile        (2026-08-28)
        max   maximum of the recentred 1D profile                (before that)

    `prof` must be the SAME recentred profile the old code read, so `p99` and
    `max` reproduce published values exactly."""
    box_mm = PEAK_BOX_MM if box_mm is None else box_mm
    bx = round(box_mm / mm_x)
    bz = round(box_mm / mm_z)
    return {"box": box_max_2d(window_lum(arr, win), bx, bz),
            "p99": float(np.percentile(prof, PEAK_PCT)),
            "max": float(np.max(prof)),
            "box_px": [int(max(1, bx)), int(max(1, bz))]}


def peak_ratio(stats_panel, stats_ctrl, stat=None):
    stat = stat or PEAK_STAT
    b = stats_ctrl[stat]
    return (stats_panel[stat] / b) if b > 0 else float("nan")


# --- the smear ladder -----------------------------------------------------------

def smear_ladder(windows_mm, profs_panel, profs_ctrl, mm_per_px, tol=None):
    """Read smear through widening windows and decide whether it is final.

    THE RULE UNTIL 2026-09-14 stopped at the FIRST pair of neighbouring windows
    that agreed within 2 % and reported that value. Windows computed further
    out were ignored even when they disagreed. Reproduced with the real
    functions: a return with 72.7 % in a 0.8 mm core and 27.3 % at +-34 mm reads
    1.00 at 24 and 48 mm and 22.22 at 96 and 100 mm; the old rule passed it at
    48 mm as 1.00 (results/audit_2026_09_14/arithmetic_probe.json).

    THE RULE NOW
      value      the WIDEST window. Every window is already computed from the
                 same frames, so the widest costs nothing.
      stable     the last two windows agree within `tol`.
      edge       share of the widest profile's second moment lying in the outer
                 10 % of its half-width. Light still arriving at the edge of
                 the face means the return is wider than the sample and the
                 rms is a lower bound, however stable the last step looked.
      converged  stable AND edge share <= tol.

    Also recorded, so the change can be audited on real data:
      first_agreement   what the old rule would have picked
      reversed          the old rule said converged and the widest window
                        disagrees with its value by more than `tol`
      band_*            energy and second-moment share added by the last step

    WHAT IT STILL CANNOT SEE. Light that leaves the face entirely. If the
    ladder's widest window is 48 mm and the tail lands at 68 mm, nothing inside
    the frame carries it and this reads converged at 1.00. The sample has to
    be large enough to hold the return; `sim_server`'s auto-grow uses
    `window_needed_mm` for that, and it too is computed from light the frame
    caught. Only a larger sample, or a physical measurement, closes it.
    """
    tol = SMEAR_TOL if tol is None else tol
    curve = []
    for h, p, c in zip(windows_mm, profs_panel, profs_ctrl):
        rp, rc = rms_width(p, mm_per_px), rms_width(c, mm_per_px)
        curve.append({"window_mm": float(h), "rms_mm": rp,
                      "rms_control_mm": rc,
                      "smear": (rp / rc) if rc and rc == rc else None})

    first = None
    for i in range(1, len(curve)):
        a, b = curve[i - 1]["smear"], curve[i]["smear"]
        if a and b and abs(b - a) / b <= tol:
            first = i
            break

    last = curve[-1]
    prev = curve[-2] if len(curve) > 1 else None
    stable = bool(prev and prev["smear"] and last["smear"]
                  and abs(last["smear"] - prev["smear"]) / last["smear"] <= tol)
    ctrl_stable = bool(prev and prev["rms_control_mm"] and last["rms_control_mm"]
                       and abs(last["rms_control_mm"] - prev["rms_control_mm"])
                       / last["rms_control_mm"] <= tol)

    p = np.asarray(profs_panel[-1], dtype=np.float64)
    tot = p.sum()
    diag = {"band_energy": None, "band_moment": None, "edge_energy": None,
            "edge_moment": None}
    if tot > 1e-20:
        z = (np.arange(p.size) - p.size / 2.0) * mm_per_px
        w = p / tot
        cz = float((z * w).sum())
        d = np.abs(z - cz)
        m2 = d * d * w
        m2t = float(m2.sum()) or 1e-30
        half_last = float(windows_mm[-1]) / 2.0
        half_prev = float(windows_mm[-2]) / 2.0 if len(windows_mm) > 1 else 0.0
        band = d > half_prev
        edge = d > 0.9 * half_last
        diag = {"band_energy": float(w[band].sum()),
                "band_moment": float(m2[band].sum() / m2t),
                "edge_energy": float(w[edge].sum()),
                "edge_moment": float(m2[edge].sum() / m2t)}
    edge_ok = diag["edge_moment"] is not None and diag["edge_moment"] <= tol
    converged = bool(stable and edge_ok)

    fa = curve[first] if first is not None else None
    reversed_ = bool(fa and fa["smear"] and last["smear"]
                     and abs(last["smear"] - fa["smear"]) / last["smear"] > tol)
    return {"curve": curve, "value": last, "converged": converged,
            "stable": stable, "control_stable": ctrl_stable,
            "edge_ok": bool(edge_ok), "tol": tol,
            "first_agreement": fa, "first_agreement_reversed": reversed_,
            **diag}
