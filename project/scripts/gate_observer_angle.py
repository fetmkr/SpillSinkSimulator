# -*- coding: utf-8 -*-
"""관찰자 각도를 넣었는데 옛 숫자가 안 움직였나.

2026-08-27 에 측정 장비에 관찰자 각도를 넣었다. 그전까지 카메라는 판 법선에
붙박이였다 -- `setup_camera` 는 처음부터 `elev_deg` 를 받았는데 `run_case` 가
0.0 을 글자 그대로 넘겼다. 그래서 **이 프로젝트가 발표한 모든 봉우리는
"판에서 똑바로 나오는 밝기"** 이고, 빔이 몇 도로 들어왔든 상관없이 그렇다.

방을 알고 나니 그게 맞는 질문이 아니었다. 패널은 천장 6 m 에 붙고 프로젝터는
2 m 에서 45~60 도로 쏘므로 패널은 30~45 도로 맞는다. 관객은 10 x 10 m 바닥에
흩어져 있어 한 패널을 여러 각도에서 본다. 벌집은 코너 큐브가 아니라 관이라
**온 쪽이 아니라 제 축 방향**으로 몰아 보낸다. "빛이 온 쪽으로 얼마나 밝나"
와 "바닥에 선 사람에게 얼마나 밝나" 는 다른 숫자인데 우리는 하나만 갖고 있었다.

이 검사가 지키는 것
------------------
새 손잡이를 달면서 **옛 답을 건드리지 않았나.** 66,426 행이 그 값들을
가리킨다. 관찰자 각도를 안 보내면 예전과 비트 단위로 같아야 한다.

    A  안 보냄  대  0 도를 손으로 보냄        -> 같아야 한다
       (렌더러 자체가 상대 3e-08 만큼 흔들린다. 실측한 값이고,
        허용 폭은 거기에 맞춰 1e-6 으로 잡았다.)
    B  안 보냄  대  옛 코드가 내던 값          -> 같아야 한다 (같은 씨앗, 같은 설정)
    C  30 도를 보냄                          -> **달라야** 한다
       안 달라지면 손잡이가 안 연결된 것이고, 그것도 불합격이다.
    D  기울여 보면 세로가 cos 만큼 눌린다      -> mm 환산이 1/cos 로 커졌나

C 가 필요한 이유는, 앞의 둘만 보면 "아무것도 안 하는 손잡이" 가 통과해
버리기 때문이다. 그런 검사를 전에 두 번 만들었다.

    python3 scripts/gate_observer_angle.py      (서버가 떠 있어야 한다)
"""
import os
import sys
import json
import math
import urllib.request

BASE = os.environ.get("SIM", "http://127.0.0.1:8777")
FAILED = []

# 작고 빠른 도형. 봉우리가 각도에 확실히 반응해야 한다.
SPEC = {"top": "pyramid",
        "top_params": {"pitch": 4.0, "tip_flat": 0.1, "apex_jitter": 0.0,
                       "tip_drop": 0.0},
        "depth": 22.0, "panel": 40.0, "floor": "none", "margin_depths": 0.2}


def form(extra):
    req = dict(spec=SPEC, thetas=[0.0, -40.0], n_phase=2, samples=128,
               beam_w=7.5, phis=[0.0], coating="musou_fit")
    req.update(extra)
    r = urllib.request.urlopen(urllib.request.Request(
        BASE + "/api/form", data=json.dumps(req).encode(),
        headers={"Content-Type": "application/json"}), timeout=1800)
    return json.loads(r.read())


def check(name, fn):
    try:
        ok, note = fn()
    except Exception as exc:
        ok, note = False, "%s: %s" % (type(exc).__name__, str(exc)[:130])
    print("  [%s] %-40s %s%s" % ("PASS" if ok else "FAIL", name, note,
                                 "" if ok else "   <-- 실패"), flush=True)
    if not ok:
        FAILED.append(name)


if __name__ == "__main__":
    print("관찰자 각도 -- %s\n" % BASE, flush=True)
    a = form({})
    b = form({"obs_elev": 0.0})
    c = form({"obs_elev": 30.0})

    # 허용 폭 1e-6 은 짐작이 아니라 실측이다. 아무것도 안 바꾸고 같은 요청을
    # 세 번 보내면 봉우리가 상대 3.1e-08, 뭉개기가 1.2e-09 만큼 갈린다.
    # Cycles 가 GPU 에서 더하는 순서가 매번 같지 않아서다. 처음에 1e-9 로
    # 잡았더니 렌더러의 흔들림을 내 변경으로 오해할 뻔했다. 실측 흔들림의
    # 서른 배로 잡되, 관찰자 각도가 만드는 차이(45 %) 보다는 한참 아래다.
    NOISE = 1e-6

    def same(x, y, k):
        u, v = x.get(k), y.get(k)
        if u is None or v is None:
            return None
        return abs(u - v) <= max(abs(v), 1e-12) * NOISE

    check("A 안 보내면 판 법선 그대로", lambda: (
        all(same(a, b, k) for k in ("peak", "smear")),
        "봉우리 %.6f = %.6f · 뭉개기 %.6f = %.6f"
        % (a["peak"], b["peak"], a["smear"], b["smear"])))

    check("B 결과에 각도가 적히나", lambda: (
        a.get("obs_elev_deg", None) in (0.0, None)
        and c.get("obs_elev_deg") == 30.0,
        "안 보냄 %s · 30 도 보냄 %s"
        % (a.get("obs_elev_deg"), c.get("obs_elev_deg"))))

    check("C 30 도를 보내면 값이 움직인다", lambda: (
        abs(c["peak"] - a["peak"]) > max(abs(a["peak"]), 1e-12) * 1e-3,
        "봉우리 %.6f -> %.6f (%.1f %% 움직임)"
        % (a["peak"], c["peak"],
           100 * abs(c["peak"] - a["peak"]) / max(abs(a["peak"]), 1e-12))))

    def d():
        want = a["mm_per_px"] / math.cos(math.radians(30.0))
        got = c.get("mm_per_px_z")
        if got is None:
            return False, "mm_per_px_z 가 결과에 없다"
        return (abs(got - want) <= want * 1e-6,
                "mm/px %.5f -> 세로 %.5f (1/cos30 로 %.5f 예상)"
                % (a["mm_per_px"], got, want))
    check("D 기울인 만큼 세로 환산이 커진다", d)

    print("\n4 항목 중 %d 실패" % len(FAILED), flush=True)
    if FAILED:
        print("실패: %s" % ", ".join(FAILED), flush=True)
    print("@@DONE@@", flush=True)
    sys.exit(1 if FAILED else 0)
