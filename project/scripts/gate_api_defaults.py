# -*- coding: utf-8 -*-
"""요청에서 재료 값을 빼먹으면 무엇이 쓰이나.

규칙
----
**재료 값을 안 보내면 그 재료의 값이 쓰여야 한다. 상수가 쓰이면 안 된다.**

재료 값은 `diffuse_frac`, `roughness`, `coating` 이다. 표본 수·광선 수·씨앗·
각도·판 크기는 재료가 아니라 장비 설정이므로 상수 기본값이 맞다. 미쓰바
교차검증의 `lambert_rho` 도 아니다 -- 그건 "두 렌더러가 똑같이 아는 유일한
재료" 로 일부러 고른 시험값이고 코드에 그렇게 적혀 있다.

왜 이 검사가 있나
----------------
2026-08-27, 피라미드 높이를 훑다가 `/api/measure` 를 직접 불러 봤더니

    확산을 안 보냄            0.07863 %
    확산 0.993 (재료 값) 보냄  0.09807 %
    확산 0.76 을 손으로 보냄   0.07863 %   <- 안 보낸 것과 **똑같다**

핸들러가 `req.get("diffuse_frac", 0.76)` 이었다. 0.76 은 2026-08-22 에
버린 가정값이다 (검정 도료 실측 0.99, 무소 0.993). 같은 줄의
`roughness` 는 0.30 이었고 그것도 버린 값이다 (재료가 쓰는 값은 0.1975,
알파 0.039). `/api/rays` 의 거칠기도 같았다.

25 % 틀린 숫자가 아무 경고 없이 나왔다. 화면은 무사했다 -- 화면은
`diffuse_frac: null` 을 **명시해서** 보내고, 키가 있으면 `.get` 의 기본값이
안 쓰인다. 물리는 것은 키를 빼고 부르는 쪽이고, 그게 나였다.

이 검사기가 없었으면 나는 세 번째 땜질을 하고 끝냈을 것이다.

검사 방법
--------
칸마다 세 번 잰다. 빈 채로, 재료 값을 손으로 넣고, 그리고 **일부러 다른
값**을 넣어서. 셋째가 필요한 이유는 앞의 둘이 우연히 같아도 통과해 버리는
검사를 전에 두 번 만들었기 때문이다. 다른 값을 넣었을 때 숫자가 안 움직이면
그 칸은 애초에 연결이 안 된 것이므로 그것도 불합격이다.

    python3 scripts/gate_api_defaults.py        (서버가 떠 있어야 한다)
"""
import os
import sys
import json
import urllib.request

BASE = os.environ.get("SIM", "http://127.0.0.1:8777")
MID = "musou_fit"
FAILED = []

# 이 검사가 쓰는 도형. 작고 빨라야 하고, 재료가 숫자를 확실히 움직여야 한다.
SPEC = {"top": "pyramid",
        "top_params": {"pitch": 4.0, "tip_flat": 0.1, "apex_jitter": 0.0,
                       "tip_drop": 0.0},
        "depth": 22.0, "panel": 40.0, "floor": "none", "margin_depths": 0.2}


def post(path, body, timeout=600):
    r = urllib.request.urlopen(urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}), timeout=timeout)
    return json.loads(r.read())


def material(mid):
    co = json.loads(urllib.request.urlopen(BASE + "/api/coatings",
                                           timeout=30).read())
    return co[mid]


def check(name, fn):
    try:
        ok, note = fn()
    except Exception as exc:
        ok, note = False, "%s: %s" % (type(exc).__name__, str(exc)[:120])
    print("  [%s] %-44s %s%s" % ("PASS" if ok else "FAIL", name, note,
                                 "" if ok else "   <-- 실패"), flush=True)
    if not ok:
        FAILED.append(name)
    return ok


def measure_rho(extra):
    req = dict(spec=SPEC, thetas=[0.0], phis=[0.0], samples=256)
    req.update(extra)
    return post("/api/measure", req)["rho"]["0"]


def form_peak(extra):
    """반짝임. 세 축 중 둘(뭉개기·반짝임)이 이 엔드포인트에서 나온다.

    싸게 재려고 위상 2 · 표본 128 로 부른다. 절대값을 쓰려는 게 아니라
    **같은 조건이 같은 값을 내는가**만 보므로 그걸로 충분하다.
    """
    req = dict(spec=SPEC, thetas=[0.0], n_phase=2, samples=128, beam_w=7.5,
               phis=[0.0])
    req.update(extra)
    return post("/api/form", req, timeout=1200)["peak"]


def rays_stats(extra):
    """`/api/rays` 는 자기가 쓴 값을 `stats` 에 되돌려 준다.

    처음에는 되돌아온 에너지를 재려고 했는데 응답 칸 이름을 잘못 짚어서
    검사기가 엉뚱한 이유로 실패했다. 그런데 이 엔드포인트는 훨씬 나은 것을
    준다 -- **무엇을 썼는지 자기가 말한다.** 숫자로 에둘러 재는 것보다
    직접 읽는 쪽이 짧고 확실하다.
    """
    req = dict(spec=SPEC, theta=0.0, phi=0.0, n_rays=60, max_bounces=12,
               mode="fitted", seed=23)
    req.update(extra)
    return post("/api/rays", req)["stats"]


def three_way(label, run, field, mine, wrong):
    """빈 채로 / 재료 값 / 일부러 다른 값. 앞의 둘은 같고 셋째는 달라야 한다."""
    a = run({})
    b = run({field: mine})
    c = run({field: wrong})
    same = abs(a - b) <= max(abs(b), 1e-12) * 1e-6
    moves = abs(c - b) > max(abs(b), 1e-12) * 1e-3
    if not moves:
        return (False, "%s: 다른 값을 넣어도 안 움직인다 (%.6g) -- "
                       "연결 자체가 끊겼다" % (label, c))
    if not same:
        return (False, "%s: 빈 채로 %.6g, 재료 값 %.6g -- %.1f %% 틀리다"
                % (label, a, b, 100.0 * abs(a - b) / abs(b)))
    return (True, "%s: 빈 채 = 재료 값 %.6g · 다른 값은 %.6g 로 움직임"
            % (label, b, c))


if __name__ == "__main__":
    print("요청에서 재료 값을 빼먹었을 때 -- %s\n" % BASE, flush=True)
    m = material(MID)
    print("  기준 재료 %s : 반사율 %.3f %% · 확산 %.4f · 거칠기 %.4f\n"
          % (MID, 100 * m["rho0"], m["df"], m["rough"]), flush=True)

    print("/api/measure", flush=True)
    check("확산 비율", lambda: three_way(
        "diffuse_frac", lambda e: measure_rho(dict(e, coating=MID)),
        "diffuse_frac", m["df"], 0.76))
    check("거칠기", lambda: three_way(
        "roughness", lambda e: measure_rho(dict(e, coating=MID)),
        "roughness", m["rough"], 0.30))

    # 2026-08-27, 사용자가 물었다: "정면 반짝임도 확산이 제대로 반영 안 된 거
    # 아니냐". 맞는 의심이었다 -- 첫 판 검사기가 `/api/measure` 와 `/api/rays`
    # 만 보고 `/api/form` 을 안 봤다. 세 축 중 두 축이 이쪽에서 나온다.
    print("/api/form  (뭉개기와 반짝임이 나오는 곳)", flush=True)
    check("확산 비율", lambda: three_way(
        "diffuse_frac", lambda e: form_peak(dict(e, coating=MID)),
        "diffuse_frac", m["df"], 0.76))
    check("거칠기", lambda: three_way(
        "roughness", lambda e: form_peak(dict(e, coating=MID)),
        "roughness", m["rough"], 0.30))

    print("/api/rays  (자기가 쓴 값을 stats 로 되돌려 준다)", flush=True)

    def rays_used(field, extra):
        return rays_stats(dict(extra, rho=m["rho0"]))[field]

    def rays_check(field, mine):
        empty = rays_used(field, {})
        if empty is None:
            return False, "%s: 안 보내면 값이 없다" % field
        if abs(float(empty) - float(mine)) > abs(float(mine)) * 1e-6:
            return (False, "%s: 안 보내면 %.6g 를 쓴다. 재료 값은 %.6g"
                    % (field, empty, mine))
        sent = rays_used(field, {field: mine * 0.5})
        if abs(float(sent) - float(mine) * 0.5) > abs(float(mine)) * 1e-6:
            return (False, "%s: 보낸 값이 안 먹는다 (%.6g 보냈는데 %.6g)"
                    % (field, mine * 0.5, sent))
        return True, "%s: 안 보내면 재료 값 %.6g 를 쓴다" % (field, empty)

    check("거칠기", lambda: rays_check("roughness", m["rough"]))
    check("확산 비율", lambda: rays_check("diffuse_frac", m["df"]))

    print("\n%d 항목 중 %d 실패" % (6, len(FAILED)), flush=True)
    if FAILED:
        print("실패한 칸: %s" % ", ".join(FAILED), flush=True)
    print("@@DONE@@", flush=True)
    sys.exit(1 if FAILED else 0)
