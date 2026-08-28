# -*- coding: utf-8 -*-
"""방이 정해지니 답이 바뀌었다 -- 한글판과 영문판을 한 스크립트로 짓는다.

오늘(2026-08-27) 방 조건을 처음 들었다. 10 x 10 m, 천장 6 m, 프로젝터가
높이 2 m 에서 수평보다 45~60 도 위로 쏜다. 패널은 천장에 붙는다.
그러면 패널이 받는 각도가 30~45 도다. 정면은 이 방에서 안 일어난다.

그런데 오늘까지 이 프로젝트의 카메라는 판 법선에 붙박이였다. 발표된 모든
봉우리가 "판에서 똑바로 나오는 밝기" 였다. 관객이 어디 서 있느냐는 한 번도
안 쟀다.

부호를 반쪽만 읽을 뻔했다
------------------------
`add_stripe` 는 램프를 `(cx, d cos t, z + d sin t)` 에, `setup_camera` 는
카메라를 **글자 그대로 같은 식**으로 놓는다. 그러니 빔 +40 에 관찰자 +40 은
빛이 온 쪽에서 되보는 것이고, 빔 -40 에 관찰자 +40 은 거울 방향이다.
첫 판에서 `-40` 만 읽고 "관객 자리는 어둡다" 고 쓸 뻔했다. `+40` 이 16 배
밝다. 표에 두 부호를 다 싣는다.

읽는 것
    results/comb20/observer_scan_both.json     관찰자 각도별 봉우리, 두 부호
    results/comb20/cell_15_20_depth40.json     셀 9.53 / 15 / 20, 깊이 40
    results/pyramid_height/height_totals.json  피라미드 밑변 50, 높이 훑기
    report/comb/comb_musou_2026-08-22.html     디자인. 이미 있는 체계를 쓴다.
쓰는 것
    report/comb/room_and_observer_2026-08-27.html
    report/comb/room_and_observer_2026-08-27_en.html
"""
import os
import re
import io
import json
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# 두 훑기를 다 읽는다. `observer_scan_both` 이 먼저였고 빔 0/±40 만 봤다.
# `observer_room` 이 이 방이 실제로 쓰는 30/40/45 도를 다 보고 피라미드 높이도
# 셋을 봤다. 정면(빔 0)은 새 훑기에 없으므로 옛 훑기에서만 온다.
OBS = os.path.join(ROOT, "results/comb20/observer_scan_both.json")
ROOMSCAN = os.path.join(ROOT, "results/comb20/observer_room.json")
CELL = os.path.join(ROOT, "results/comb20/cell_15_20_depth40.json")
PYT = os.path.join(ROOT, "results/pyramid_height/height_totals.json")
TIPF = os.path.join(ROOT, "results/pyramid_height/tipflat_50.json")
WIDE = os.path.join(ROOT, "results/pyramid_height/smear_wide.json")
STYLE_FROM = os.path.join(ROOT, "report/comb/comb_musou_2026-08-22.html")
OUT = os.path.join(ROOT, "report/comb/room_and_observer_2026-08-27%s.html")

obs = json.load(open(OBS))
room = json.load(open(ROOMSCAN))
cell = json.load(open(CELL))
pyt = json.load(open(PYT))
tipf = json.load(open(TIPF))
wide = json.load(open(WIDE))

COMB = [r for r in room if r["case"].startswith("벌집")]
COMB0 = [r for r in obs if r["case"].startswith("벌집")]   # 빔 0 이 있는 옛 훑기
# 피라미드 셋. 이름에 높이가 적혀 있으니 그것으로 가른다.
PYRH = [100.0, 175.0, 250.0]
PYR = {h: [r for r in room if r["case"].endswith("높이 %.0f" % h)]
       for h in PYRH}
BEAMS = [30.0, 40.0, 45.0]                # 이 방이 쓰는 빔 각도


def face_deg(h, pitch=50.0):
    """피라미드 옆면이 바닥에서 몇 도로 서나. 마주 보는 두 면의 골 반각은
    90 에서 이것을 뺀 값이다. 되쏨이 얼마나 뾰족한지가 여기 달렸다."""
    return math.degrees(math.atan(h / (pitch / 2.0)))
P250 = next(r for r in pyt if r.get("depth") == 250.0)
FLAT5 = next(r for r in pyt if r["label"].startswith("민판 5"))
C953 = next(r for r in cell if r["pitch"] == 9.53)

ROOM = dict(w=10.0, ceil=6.0, proj=2.0, eye=1.6, el_lo=45.0, el_hi=60.0)
PITCH, DEPTH, INC = 9.53, 40.0, 40.0
REACH = PITCH / math.tan(math.radians(INC))     # 빛이 벽에 닿는 깊이, mm


def pk(row, t):
    return (row.get("peak_by_theta") or {}).get("%+.0f" % t)


# ===================================================================== 말
KO = {
    "lang": "ko", "suffix": "",
    "title": "방이 정해지니 답이 바뀌었다",
    "eyebrow": "2026-08-27 · 방과 관찰자",
    "sub": ("패널이 정면으로 맞을 일이 없다. 그리고 오늘까지 이 프로젝트는 "
            "<b>관객이 어디 서 있는지</b>를 한 번도 안 쟀다. 카메라가 판 "
            "법선에 붙박이였다."),
    "verdict": "결론",
    "v1": ("<b>패널이 받는 각도는 30~45도다.</b> 정면은 이 방에서 안 "
           "일어난다. 지금까지 봐 온 정면 값은 여기서 안 쓰는 값이다."),
    "v2": ("<b>벌집은 어디서나 같고 피라미드는 자리를 탄다.</b> 빔 40도에서 "
           "벌집은 %.4f 에서 %.4f 사이로 붙박이인데, 피라미드는 %.4f 에서 "
           "%.4f 까지 <b>%.1f 배</b> 오르내린다. 벌집이 이기는 자리는 %s, "
           "피라미드가 이기는 자리는 %s다."),
    "v3": ("<b>프로젝터를 세울수록 어두워진다.</b> 60도로 쏘면 패널이 30도로 "
           "맞고, 45도로 쏠 때보다 <b>%.0f %%</b> 어둡다. 모양을 안 바꾸고 "
           "얻는 이득이다."),
    "v4": ("<b>벌집은 평평하고 피라미드는 뾰족하다.</b> 벌집은 관찰자 20도에서 "
           "60도까지 %.3f 근처로 그대로다. 피라미드는 40도에서 되쏘고 "
           "거기서 벗어나면 급히 어두워진다."),
    "v5": ("<b>피라미드 높이를 낮춰도 안 된다.</b> 골이 벌어지면 봉우리는 "
           "낮아지는데 주변이 더 많이 어두워져 오히려 뾰족해진다 "
           "(4.0배에서 7.0배). 그리고 높이 100 은 어느 자리에서 봐도 "
           "높이 250 보다 밝다."),
    "v6": ("<b>끝 평평은 키우는 쪽이 낫다.</b> 0.5 에서 2.0 으로 키우면 네 "
           "각도가 모두 3~5 % 좋아진다. 눌러 찍기 쉬운 쪽으로 가도 손해가 "
           "없다."),
    "v7": ("<b>둘 다 목표를 못 넘었다.</b> 목표가 0.040 인데 프로젝터 쪽 "
           "바닥에서 벌집이 %.1f 배, 피라미드가 %.1f 배 밝다. 모양만으로 "
           "되는 문제가 아닐 수 있다."),
    "h_room": "방",
    "room_cap": "단면 하나. 각도와 거리는 다 계산해서 그렸다.",
    "th_fire": "쏘는 각", "th_run": "천장까지 수평 거리", "th_inc": "패널이 받는 각",
    "h_why": "왜 한쪽만 밝은가",
    "why_cap": ("셀 하나를 옆에서 자른 그림. 각도는 실제 각도다. 포일은 실제 "
                "0.08 mm 인데 보이라고 굵게 그렸다."),
    "why_p": ("빔이 %.0f도로 들어오면 셀 한쪽 벽이 팁에서 <b>%.1f mm</b> "
              "깊이까지 밝아진다. 그 벽의 법선은 관 축과 직각이다. 그래서 "
              "보는 자리에 따라 이렇게 갈린다." % (INC, REACH)),
    "why_a": "빛이 온 쪽에서 보면 밝아진 벽이 그대로 보인다",
    "why_b": "관 축을 똑바로 내려다보면 벽이 옆으로 서서 안 보인다",
    "why_c": "반대쪽에서 보면 밝아진 벽의 뒷면이라 안 보인다",
    "why_after": ("이 셈이 딱 맞아떨어진다. 깊이 %.1f mm 인 밝은 벽 끝에서 "
                  "%.0f도로 올려다보면 가로로 %.2f mm 를 가는데, 그것이 셀 "
                  "너비와 같다. 그러니 <b>밝은 띠 전체가 그 방향에서 정확히 "
                  "다 보인다.</b>" % (REACH, INC, PITCH)),
    "h_obs": "관객이 어디 서 있는지가 답을 바꾼다",
    "obs_p1": ("측정 장비의 카메라가 판 법선에 붙박이였다. "
               "<code>setup_camera</code> 는 처음부터 각도를 받았는데 "
               "<code>run_case</code> 가 0 을 글자 그대로 넘겼다. 그래서 이 "
               "프로젝트가 발표한 모든 봉우리는 <b>판에서 똑바로 나오는 "
               "밝기</b>다. 빔이 몇 도로 들어왔든 상관없이 그렇다."),
    "obs_p2": ("오늘 관찰자 각도를 손잡이로 만들고, 같은 판을 여러 자리에서 "
               "봤다. 부호가 중요하다. 램프와 카메라를 놓는 식이 글자 그대로 "
               "같아서, <b>빔 +40 에 관찰자 +40</b> 은 빛이 온 쪽에서 되보는 "
               "것이고 <b>빔 -40 에 관찰자 +40</b> 은 거울 방향이다."),
    "cond_obs": ("벌집 셀 9.53 · 깊이 40 · 포일 0.08 · 무소 팁 20 mm · "
                 "바닥판 5 %% 페인트 · 표본 %d · 위상 %d. "
                 "값은 봉우리이고 민판 무광 검정이 1.0 이다."),
    "th_obs": "관찰자 각도", "th_same": "빔이 같은 쪽에서", "th_norm": "빔이 정면에서",
    "th_opp": "반대쪽 (거울 방향)", "th_ratio": "같은 쪽 &divide; 반대쪽",
    "th_beam": "빔",
    "ax_x": "관찰자 각도 (판 법선에서, 도)", "ax_y": "봉우리 (민판 = 1.0)",
    "ax_goal": "목표 0.040",
    "curves_note": "벌집은 붙박이고 피라미드는 40도에 봉우리가 선다.",
    "curves_cap": ("빔 40도. 값은 앞 표와 같은 값이다. 세로 눈금은 로그가 "
                   "아니라 그대로다."),
    "groove_lead": ("빔이 40도로 들어와 골 안에서 어디로 가는지 그대로 "
                    "따라간 길이다. 꺾이는 자리는 풀어서 찍었다."),
    "groove_note": ("깊고 좁은 골이 여러 번 튕기며 빛을 들어온 쪽으로 "
                    "되돌린다. 두 번으로는 안 된다."),
    "groove_cap": ("피라미드 골을 옆에서 자른 그림. 밑변 50 고정. "
                   "각도는 실제 각도다."),
    "obs_p4": ("<b>빔이 얕게 올수록 어둡다.</b> 프로젝터를 세워 60도로 쏘면 "
               "패널이 30도로 맞고, 그때가 45도로 쏠 때보다 40 % 어둡다. "
               "프로젝터를 세울 수 있으면 그것만으로 이득이다."),
    "th_comb": "벌집 9.53/40", "th_pyra": "피라미드 높이",
    "th_which": "가장 어두운 것",
    "h_groove": "피라미드 높이 -- 골이 벌어지면 되쏨이 무뎌질까",
    "groove_p": ("밑변 50 에 높이 250 이면 옆면이 바닥에서 84.3도로 서고 "
                 "마주 보는 두 면이 반각 5.7도짜리 좁은 골이 된다. 높이를 "
                 "낮추면 골이 벌어지니 되쏨이 무뎌질 것이라고 봤다. "
                 "빔 40도에서 확인했다."),
    "th_h": "높이", "th_face": "옆면이 바닥에서", "th_groove": "골 반각",
    "th_peak40": "가장 밝은 자리", "th_at60": "관찰자 60도에서",
    "th_sharp": "봉우리 &divide; 골",
    "groove_after": ("<b>추측이 반만 맞았다.</b> 골이 벌어지면 봉우리가 "
                     "낮아지긴 한다 (0.5848 &rarr; 0.4675). 그런데 주변이 "
                     "훨씬 더 많이 어두워져서 봉우리와 골의 비는 4.0배에서 "
                     "7.0배로 오히려 <b>뾰족해진다.</b> 그리고 높이 100 은 "
                     "관찰자 어느 자리에서 봐도 높이 250 보다 밝다. "
                     "<b>높이를 낮추는 것은 답이 아니다.</b>"),
    "h_tip": "끝 평평 -- 키우는 쪽이 낫다",
    "tip_p": ("눌러 찍는 판은 수학적인 점을 못 만든다. 그 평평한 면은 판 "
              "겉면과 나란해서, 벌집에서 포일 테두리가 정면 반사의 51 % 를 "
              "맡았던 자리와 같다. 그래서 키우면 나빠질 줄 알았다."),
    "cond_tip": ("피라미드 밑변 50 · 판 500 · 무소 팁 20 mm · 바탕 5 % "
                 "페인트 · 표본 512 · 면 0/45/90도. 값은 반사 총량이고 "
                 "가장 밝은 면의 값이다."),
    "th_tip": "끝 평평", "th_tiparea": "끝이 차지하는 넓이",
    "th_vs05": "끝 0.5 대비 (40도)",
    "tip_after": ("<b>반대였다. 키울수록 좋아진다.</b> 끝 0.5 에서 2.0 으로 "
                  "키우면 네 각도가 모두 3~5 % 좋아지고, 높이 100 과 250 "
                  "둘 다 그렇다. 끝을 자르면 옆면이 더 가팔라져 빛이 한 번 "
                  "더 튕기기 때문이다. <b>눌러 찍기 쉬운 쪽으로 키워도 "
                  "손해가 없다.</b>"),
    "h_smear": "하한이던 뭉개기를 확정했다",
    "smear_p": ("높이 250 의 뭉개기를 판 500 mm 로 쟀는데 되돌아온 빛을 "
                "담으려면 창이 509 mm 필요했다. 그래서 그 값은 실제 값이 "
                "아니라 <b>하한</b>이었다. 판을 키워 다시 쟀다."),
    "cond_smear": ("피라미드 밑변 50 · 높이 250 · 끝 평평 1.0 · 무소 팁 "
                   "20 mm · 바탕 5 % 페인트 · 위상 8 · 빔 7.5 mm · 표본 512 · "
                   "빔 &plusmn;40도. 빔이 셀보다 작으므로 발표된 다른 뭉개기 "
                   "값과 나란히 놓으면 안 된다."),
    "th_panel": "판", "th_sm": "모양 뭉개기", "th_held": "다 담겼나",
    "th_need": "필요한 창", "yes": "예", "no": "아니오",
    "smear_after": ("<b>%.4f 가 아니라 %.4f 였다. %+.1f %% 밖에 안 올랐다.</b> "
                    "판 500 에서도 거의 다 담고 있었다. 이제 하한이 아니라 "
                    "잰 값이다."),
    "obs_p3": ("<b>빔 칸 셋이 통째로 밝다.</b> 한 자리만 밝은 것이 아니라 "
               "20도에서 60도까지 넓게 밝다. 거울 방향(맨 오른쪽 칸)은 오히려 "
               "어둡다. 벌집은 거울이 아니다."),
    "h_seat": "그래서 관객은 얼마나 밝게 보나",
    "seat_p": ("천장 패널 한 점을 정한다. 프로젝터가 그 점을 %.0f도로 비춘다. "
               "키 %.1f m 인 사람이 그 점에서 바닥으로 얼마나 떨어져 서면 "
               "어느 각도로 보게 되는지 셈한다." % (INC, ROOM["eye"])),
    "th_dist": "패널 아래에서 떨어진 거리", "th_view": "보는 각도",
    "th_bright": "그 자리에서 본 밝기",
    # 숫자를 손으로 적지 않는다. 첫 판에 무소 10 mm 때 값 0.36 을 적어 뒀는데
    # 훑기를 20 mm 로 다시 돌리자 0.13 이 되었고, 글만 옛 숫자로 남았다.
    "seat_after": ("<b>프로젝터와 같은 쪽 바닥 대부분이 밝은 쪽이다.</b> "
                   "민판 무광 검정을 1.0 으로 놓은 값이니 %.3f 은 민판의 "
                   "%.0f 분의 1 을 보는 것이다. 목표는 0.040 이었으니 "
                   "<b>%.1f 배</b> 밝다."),
    "seat_warn": ("한 단면만 쟀다. 관객은 좌우로도 흩어져 있는데 이 훑기는 "
                  "위아래로만 움직였다. 옆으로 벗어나면 얼마나 어두워지는지 "
                  "<b>안 쟀다.</b>"),
    "h_pyr": "피라미드와 나란히 놓으면",
    "pyr_p": ("둘 다 같은 조건에서 같은 방식으로 쟀다. 빔은 40도로 같은 "
              "쪽에서 들어오고, 관객만 자리를 옮긴다."),
    "pyr_after": ("<b>벌집은 평평하고 피라미드는 뾰족하다.</b> 피라미드는 "
                  "40도에서 되쏘고, 그 자리를 벗어나면 급히 어두워진다. "
                  "밑변 50 에 높이 250 이면 옆면이 바닥에서 84도로 거의 "
                  "서 있다. 마주 보는 두 면이 반각 5.7도짜리 <b>깊고 좁은 "
                  "골</b>을 이룬다. 그 안에서 빛이 <b>%d 번</b> 튕기며 조금씩 "
                  "방향을 틀어 들어온 쪽(%+.0f도)으로 나온다."),
    "pyr_after2": ("갈리는 자리가 단순하지 않다. 벌집이 이기는 곳은 %s 이고 "
                   "피라미드가 이기는 곳은 %s 다. 피라미드의 봉우리(40도) "
                   "근처에서는 벌집이 이기고, 그 봉우리에서 벗어난 자리에서는 "
                   "피라미드가 이긴다. <b>관객이 어디 서는지를 정해야 모양이 "
                   "정해진다.</b>"),
    # 이 표에는 두 모양이 같이 들어간다. 그러니 두 조건을 다 적는다.
    # 한쪽만 적으면 읽는 사람이 나머지 줄의 조건을 모른다.
    "cond_pyr": ("벌집 셀 9.53 · 깊이 40 · 포일 0.08 · 판 95.3 mm &nbsp;/&nbsp; "
                 "피라미드 밑변 50 · 높이 250 · 끝 평평 1.0 · 판 200 mm. "
                 "둘 다 무소 팁 20 mm · 나머지 5 %% 페인트 · 빔 40도 · "
                 "표본 %d · 위상 %d. 값은 봉우리이고 민판 무광 검정이 "
                 "1.0 이다."),
    "h_cell": "셀 크기 -- 작을수록 좋다",
    "cond_cell": ("벌집 · 깊이 40 · 포일 0.08 · 무소 팁 20 mm · 바닥판 5 % "
                  "페인트. 값은 반사 총량이고 면 0/45/90도 중 가장 밝은 값."),
    "th_cell": "셀", "th_rim": "테두리 넓이", "th_reach": "40도 빛이 벽에 닿는 깊이",
    "cell_p": ("셀이 크면 테두리는 준다. 그런데도 진다. 깊이 40 에서 바닥 "
               "출구가 넓어져 <b>바닥판이 더 많이 보이기</b> 때문이다."),
    "th_half": "바닥 출구 반각", "th_leak": "바닥에서 곧장 새는 몫",
    "cell_p2": ("그리고 무소가 닿는 깊이가 문제가 된다. 40도 빛이 셀 9.53 "
                "에서는 11.4 mm 에서 벽에 닿으니 팁에서 20 mm 만 뿌려도 다 "
                "덮인다. 셀 20 은 23.8 mm 라 <b>못 덮는다.</b>"),
    "h_rig": "오늘 고친 장비",
    "r1": ("<b>관찰자 각도를 손잡이로 만들었다.</b> "
           "<code>form_buildable.OBS_ELEV</code>, <code>/api/form</code> 의 "
           "<code>obs_elev</code>, 화면의 칸, 그리고 3D 에 카메라를 그린다. "
           "안 보내면 판 법선이라 발표된 값은 안 움직인다 "
           "(<code>gate_observer_angle.py</code> 4항목)."),
    "r2": ("기울여 보면 세로가 <code>cos</code> 만큼 눌린다. 그 축의 mm "
           "환산을 <code>1/cos</code> 로 고쳤다. 안 고쳤으면 비스듬히 본 "
           "뭉개기가 전부 좁게 읽혔을 것이다."),
    "r3": ("<b><code>form</code> 이 돌려주던 봉우리는 항상 0도 값이었다.</b> "
           "40도 빔의 봉우리를 물을 방법이 없었다. "
           "<code>peak_by_theta</code> 를 더했다."),
    "r4": ("<b><code>/api/measure</code> 가 확산을 안 받으면 버린 값 0.76 "
           "을, 거칠기는 버린 0.30 을 썼다.</b> 25 % 틀린 숫자가 조용히 "
           "나왔다. <code>/api/rays</code> 도 같았다. 네 칸 다 고치고 "
           "<code>gate_api_defaults.py</code> 로 막았다. 화면과 배치 "
           "스크립트는 값을 명시해 보내므로 무사했다."),
    "r5": ("보고서를 짓는 스크립트가 서식이 안 풀린 채로 나가면 <b>발행을 "
           "멈춘다.</b> 퍼센트가 두 번 찍히거나 문단이 통째로 빠지는 일이 "
           "세 번 있었는데, 숫자 검사도 태그 검사도 그걸 못 잡았다."),
    "h_open": "안 잰 것",
    "o1": ("<b>좌우로 벗어난 자리를 안 쟀다.</b> 관찰자 훑기가 한 단면 "
           "안에서만 움직였다. 방은 2차원이다."),
    "o2": "30도와 45도로 들어오는 빔의 관찰자 훑기를 안 했다. 40도만 했다.",
    "o3": "셀 6.35 를 30~45도에서 안 쟀다. 셀이 작을수록 좋았으니 더 좋을 수 있다.",
    "o4": ("피라미드 뭉개기를 이 판(200 mm)으로는 못 믿는다. 되돌아온 빛이 "
           "창을 넘친다. 표에 안 실었다."),
    "o5": ("사람 눈에 얼마나 보이는지는 아직 안 쟀다. 여기 숫자는 다 "
           "밝기의 비다."),
    "src": "잰 것", "also": "같은 날 다른 보고서",
    "this": "이 문서를 짓는 스크립트",
}

EN = {
    "lang": "en", "suffix": "_en",
    "title": "The room changed the answer",
    "eyebrow": "2026-08-27 · Room and observer",
    "sub": ("Nothing in this room ever hits the panel head-on. And until "
            "today this project never measured <b>where the audience is "
            "standing</b>. The camera was welded to the panel normal."),
    "verdict": "Verdict",
    "v1": ("<b>The panel is struck at 30 to 45 degrees.</b> Head-on never "
           "happens here. Every head-on figure published so far is a number "
           "this room does not use."),
    "v2": ("<b>The honeycomb is the same everywhere; the pyramid depends on "
           "where you stand.</b> With a 40 degree beam the honeycomb sits "
           "between %.4f and %.4f, while the pyramid swings from %.4f to "
           "%.4f &mdash; <b>%.1f times</b>. The honeycomb wins at %s; the "
           "pyramid wins at %s."),
    "v3": ("<b>Standing the projector up makes it darker.</b> Fire at 60 "
           "degrees and the panel takes 30, which is <b>%.0f %%</b> darker "
           "than firing at 45. That gain costs no change of shape."),
    "v4": ("<b>The honeycomb is flat and the pyramid is peaked.</b> The "
           "honeycomb holds near %.3f from observer 20 degrees to 60. The "
           "pyramid throws light back at 40 and falls away fast."),
    "v5": ("<b>A shorter pyramid does not help.</b> Opening the groove "
           "lowers the peak but drops everything around it further, so it "
           "gets sharper, not blunter (4.0 to 7.0). And height 100 is "
           "brighter than height 250 from every position."),
    "v6": ("<b>A bigger tip flat is better.</b> Going from 0.5 to 2.0 "
           "improves all four angles by 3 to 5 %. Moving toward what "
           "presses easily costs nothing."),
    "v7": ("<b>Neither one clears the target.</b> Against a target of "
           "0.040, on the projector's side of the floor the honeycomb is "
           "%.1f times brighter and the pyramid %.1f times. Shape alone may "
           "not be enough."),
    "h_room": "The room",
    "room_cap": "One cross-section. Every angle and distance is computed.",
    "th_fire": "Firing angle", "th_run": "Horizontal run to the ceiling",
    "th_inc": "Angle the panel receives",
    "h_why": "Why only one side is bright",
    "why_cap": ("One cell cut from the side. Angles are true. The foil is "
                "0.08 mm and is drawn thick so it can be seen."),
    "why_p": ("A beam arriving at %.0f degrees lights one wall of the cell "
              "down to <b>%.1f mm</b> from the mouth. That wall's normal is "
              "perpendicular to the tube axis, so what you see depends on "
              "where you stand." % (INC, REACH)),
    "why_a": "From the side the light came from, the lit wall is in full view",
    "why_b": "Straight down the tube the walls are edge-on and invisible",
    "why_c": "From the far side you face the back of the lit wall",
    "why_after": ("The arithmetic closes exactly. Looking up at %.0f degrees "
                  "from the bottom of the lit strip at %.1f mm travels %.2f "
                  "mm sideways, which is the cell width. So <b>the whole lit "
                  "strip is visible from that direction and no other.</b>"
                  % (INC, REACH, PITCH)),
    "h_obs": "Where the audience stands changes the answer",
    "obs_p1": ("The rig's camera was welded to the panel normal. "
               "<code>setup_camera</code> took an elevation from the start, "
               "but <code>run_case</code> passed a literal zero. So every "
               "peak this project has published is <b>brightness straight "
               "out of the panel</b>, whatever angle the beam arrived at."),
    "obs_p2": ("Today the observer angle became a control and the same panel "
               "was viewed from several places. The sign matters. The lamp "
               "and the camera are placed by literally the same expression, "
               "so <b>beam +40 with observer +40</b> looks back along the "
               "incoming light, and <b>beam -40 with observer +40</b> is the "
               "mirror direction."),
    "cond_obs": ("Honeycomb cell 9.53 · depth 40 · foil 0.08 · Musou 20 mm "
                 "from the tip · 5 %% paint on the backing plate · %d "
                 "samples · %d phases. Values are peaks with a flat matte "
                 "black patch at 1.0."),
    "th_obs": "Observer angle", "th_same": "Beam from the same side",
    "th_norm": "Beam head-on", "th_opp": "Far side (mirror)",
    "th_ratio": "Same side &divide; far side", "th_beam": "Beam",
    "obs_p4": ("<b>A shallower beam is darker.</b> Stand the projector up to "
               "fire at 60 degrees and the panel takes 30, which is 40 % "
               "darker than firing at 45. If the projector can be stood up, "
               "that alone is a gain."),
    "ax_x": "Observer angle (from the panel normal, degrees)",
    "ax_y": "Peak (flat matte black = 1.0)", "ax_goal": "target 0.040",
    "curves_note": ("The honeycomb holds flat; the pyramid peaks at 40 "
                    "degrees."),
    "curves_cap": ("Beam at 40 degrees. Same numbers as the table above. "
                   "The vertical scale is linear, not logarithmic."),
    "groove_lead": ("The path a 40 degree beam actually takes inside the "
                    "groove. Every turning point is solved, not sketched."),
    "groove_note": ("A deep narrow groove bounces light many times and "
                    "sends it back the way it came. Two bounces cannot do "
                    "it."),
    "groove_cap": ("The pyramid groove cut from the side. Base fixed at 50. "
                   "Angles are true."),
    "th_comb": "Honeycomb 9.53/40", "th_pyra": "Pyramid height",
    "th_which": "Darkest",
    "h_groove": "Pyramid height -- does a wider groove blunt the throwback",
    "groove_p": ("Base 50 with height 250 puts the faces at 84.3 degrees "
                 "from the base, so two opposing faces make a groove with a "
                 "half-angle of 5.7 degrees. A shorter pyramid opens that "
                 "groove, which should blunt the throwback. Checked at a "
                 "40 degree beam."),
    "th_h": "Height", "th_face": "Face from the base", "th_groove": "Groove half-angle",
    "th_peak40": "Brightest position", "th_at60": "At observer 60 degrees",
    "th_sharp": "Peak &divide; valley",
    "groove_after": ("<b>Half right.</b> Opening the groove does lower the "
                     "peak (0.5848 &rarr; 0.4675). But everything around it "
                     "drops much further, so peak over valley goes from 4.0 "
                     "to 7.0 &mdash; <b>sharper, not blunter.</b> And height "
                     "100 is brighter than height 250 from every observer "
                     "position. <b>Going shorter is not the answer.</b>"),
    "h_tip": "Tip flat -- bigger is better",
    "tip_p": ("A pressed sheet cannot make a mathematical point. That flat "
              "face is parallel to the panel surface, the same place where "
              "the honeycomb's foil rim carried 51 % of the head-on "
              "reflection. So a bigger tip was expected to hurt."),
    "cond_tip": ("Pyramid base 50 · panel 500 · Musou 20 mm from the tip · "
                 "5 % paint below · 512 samples · planes 0/45/90 degrees. "
                 "Values are total reflectance, the brightest plane."),
    "th_tip": "Tip flat", "th_tiparea": "Area the tip occupies",
    "th_vs05": "Against tip 0.5 (40 deg)",
    "tip_after": ("<b>The opposite. Bigger is better.</b> Going from tip 0.5 "
                  "to 2.0 improves all four angles by 3 to 5 %, at height "
                  "100 and at 250 alike. Truncating the tip steepens the "
                  "faces, so light bounces once more. <b>Enlarging it toward "
                  "what presses easily costs nothing.</b>"),
    "h_smear": "The lower bound on smear is now a measurement",
    "smear_p": ("Smear at height 250 was measured on a 500 mm panel, but "
                "catching the return needed a 509 mm window. That figure was "
                "a <b>lower bound</b>, not the value. Measured again on a "
                "wider panel."),
    "cond_smear": ("Pyramid base 50 · height 250 · tip flat 1.0 · Musou "
                   "20 mm from the tip · 5 % paint below · 8 phases · beam "
                   "7.5 mm · 512 samples · beam at &plusmn;40 degrees. The "
                   "beam is smaller than the cell, so this must not be set "
                   "beside other published smear figures."),
    "th_panel": "Panel", "th_sm": "Smear", "th_held": "Fully caught",
    "th_need": "Window needed", "yes": "yes", "no": "no",
    "smear_after": ("<b>%.4f, not %.4f &mdash; up only %+.1f %%.</b> The 500 "
                    "mm panel was already catching nearly all of it. This is "
                    "now a measurement, not a bound."),
    "obs_p3": ("<b>All three beam columns are bright top to bottom.</b> Not one "
               "position but everything from 20 to 60 degrees. The mirror "
               "direction on the right is dark instead. A honeycomb is not a "
               "mirror."),
    "h_seat": "So how bright does the audience see it",
    "seat_p": ("Fix one point on the ceiling panel. The projector lights it "
               "at %.0f degrees. For a viewer with eyes at %.1f m, this is "
               "how far along the floor they stand and what angle they see."
               % (INC, ROOM["eye"])),
    "th_dist": "Distance out from below the panel", "th_view": "Viewing angle",
    "th_bright": "Brightness seen there",
    "seat_after": ("<b>Most of the floor on the projector's side is the "
                   "bright side.</b> With a flat matte black patch at 1.0, "
                   "%.3f means seeing one %.0f th of a bare painted board. "
                   "The target was 0.040, so this is <b>%.1f times</b> "
                   "brighter."),
    "seat_warn": ("Only one cross-section was measured. The audience also "
                  "spreads left and right, and this scan only moved up and "
                  "down. How much darker it gets off to the side was "
                  "<b>not measured.</b>"),
    "h_pyr": "Side by side with the pyramid",
    "pyr_p": ("Both measured the same way under the same conditions. The "
              "beam arrives at 40 degrees from the same side; only the "
              "viewer moves."),
    "pyr_after": ("<b>The honeycomb is flat and the pyramid is peaked.</b> "
                  "The pyramid throws light back at 40 degrees and falls "
                  "away fast on either side. With base 50 and height 250 "
                  "the faces stand at 84 degrees from the base, so two "
                  "opposing faces make a <b>deep narrow groove</b> with a "
                  "5.7 degree half-angle. Inside it light bounces <b>%d "
                  "times</b>, turning a little each time, and leaves at "
                  "%+.0f degrees &mdash; back the way it came."),
    "pyr_after2": ("The split is not a simple one. The honeycomb wins at "
                   "%s and the pyramid at %s. Near the pyramid's peak at 40 "
                   "degrees the honeycomb wins; away from that peak the "
                   "pyramid does. <b>Where the audience stands decides the "
                   "shape.</b>"),
    "cond_pyr": ("Honeycomb cell 9.53 · depth 40 · foil 0.08 · panel 95.3 mm "
                 "&nbsp;/&nbsp; pyramid base 50 · height 250 · tip flat 1.0 · "
                 "panel 200 mm. Both with Musou 20 mm from the tip · 5 %% "
                 "paint elsewhere · beam at 40 degrees · %d samples · %d "
                 "phases. Values are peaks with a flat matte black patch "
                 "at 1.0."),
    "h_cell": "Cell size -- smaller is better",
    "cond_cell": ("Honeycomb · depth 40 · foil 0.08 · Musou 20 mm from the "
                  "tip · 5 % paint on the backing plate. Values are total "
                  "reflectance, the brightest of the 0/45/90 degree planes."),
    "th_cell": "Cell", "th_rim": "Rim area",
    "th_reach": "Depth a 40 degree beam reaches the wall",
    "cell_p": ("A bigger cell has less rim, and still loses. At depth 40 the "
               "exit at the bottom widens, so <b>more of the backing plate "
               "is in view.</b>"),
    "th_half": "Half-angle of the exit", "th_leak": "Share escaping straight off the floor",
    "cell_p2": ("And the spray stops reaching. At cell 9.53 a 40 degree beam "
                "meets the wall at 11.4 mm, so 20 mm from the tip covers it. "
                "At cell 20 it is 23.8 mm and <b>the spray does not "
                "reach.</b>"),
    "h_rig": "What was fixed in the rig today",
    "r1": ("<b>The observer angle became a control.</b> "
           "<code>form_buildable.OBS_ELEV</code>, <code>obs_elev</code> on "
           "<code>/api/form</code>, a field in the UI, and the camera drawn "
           "into the 3D view. Omit it and the camera sits on the panel "
           "normal, so published figures do not move "
           "(<code>gate_observer_angle.py</code>, 4 items)."),
    "r2": ("Viewed at a tilt the vertical axis compresses by "
           "<code>cos</code>. The mm-per-pixel on that axis is now divided "
           "by <code>cos</code>. Without it every oblique smear would have "
           "read too narrow."),
    "r3": ("<b>The peak <code>form</code> returned was always the zero "
           "degree entry.</b> There was no way to ask for the peak of a 40 "
           "degree beam. <code>peak_by_theta</code> was added."),
    "r4": ("<b><code>/api/measure</code> fell back to the withdrawn diffuse "
           "fraction 0.76 and the withdrawn roughness 0.30.</b> Numbers 25 "
           "% wrong came out quietly. <code>/api/rays</code> did the same. "
           "All four slots are fixed and "
           "<code>gate_api_defaults.py</code> holds them. The UI and the "
           "batch scripts always sent explicit values, so they were safe."),
    "r5": ("A report builder now <b>refuses to publish</b> when a format "
           "marker is left unresolved. A doubled percent sign or a vanished "
           "paragraph slipped through three times, and neither the number "
           "checks nor the tag checks could see them."),
    "h_open": "Not measured",
    "o1": ("<b>Nothing off to the side.</b> The observer scan moved within "
           "one cross-section. The room is two-dimensional."),
    "o2": "No observer scan for beams arriving at 30 or 45 degrees. Only 40.",
    "o3": ("Cell 6.35 at 30 to 45 degrees. Smaller cells won, so it may do "
           "better still."),
    "o4": ("Pyramid smear cannot be trusted on this 200 mm panel. The return "
           "overflows the window. It is left out of the table."),
    "o5": "How visible any of this is to a human eye. These are all ratios.",
    "src": "Measured in", "also": "Other report from the same day",
    "this": "Script that builds this document",
}



def groove_path(h, inc_deg=40.0, pitch=50.0, maxb=80):
    """골 안에서 거울 반사를 그대로 따라간다. 그린 길이 곧 푼 길이다.

    좌표는 골 안에서만 쓴다. 꼭짓점이 원점, u 는 골 축을 따라 입구 쪽으로,
    v 는 그 직각이다. 벽 두 개는 `|v| = u tan(g)` 이고 g 는 골 반각이다.

    **왜 이걸 짜야 했나.** 처음에 "두 번 튕긴 빛이 온 길로 되돌아 나간다"
    고 적었다. 두 번 튕기면 방향이 골 반각의 네 배만큼 돌아간다. 높이 250 은
    그게 22.8 도라 되돌아가는 것과 한참 멀다. **그 말은 틀렸다.**

    실제로 따라가 보니 높이 250 은 **열 번** 튕기고 들어온 쪽으로 나온다.
    깊고 좁은 골이 빛을 가둔 채 조금씩 방향을 돌리는 것이다. 높이 100 은
    다섯 번 튕기고 반대쪽으로 빠진다. 되쏨은 골이 좁아서가 아니라
    **깊고 좁아 여러 번 튕기기 때문**이다.

    돌려주는 것: (점들, 튕긴 횟수, 나간 각도). 점은 (u, v) 이고 단위는 mm.
    """
    g = math.radians(90.0 - face_deg(h, pitch))
    tg = math.tan(g)
    t = math.radians(inc_deg)
    p0 = (h, h * tg)                         # 입구 위쪽 모서리
    d = (-math.cos(t), -math.sin(t))
    pts = [p0]
    n = 0
    for _ in range(maxb):
        best = None
        for sgn in (1.0, -1.0):
            den = d[1] - sgn * tg * d[0]
            if abs(den) < 1e-12:
                continue
            s = (sgn * tg * p0[0] - p0[1]) / den
            if s > 1e-7:
                q = (p0[0] + s * d[0], p0[1] + s * d[1])
                if q[0] > 0 and (best is None or s < best[0]):
                    best = (s, q, sgn)
        if best is None:
            break
        s, q, sgn = best
        if q[0] > h:                         # 입구를 넘어 나갔다
            break
        p0 = q
        pts.append(q)
        nx, ny = math.sin(g), -math.cos(g) * sgn
        dot = d[0] * nx + d[1] * ny
        d = (d[0] - 2 * dot * nx, d[1] - 2 * dot * ny)
        n += 1
    if d[0] > 1e-9:                          # 입구 밖으로 뻗는 선분 하나
        s = (h - p0[0]) / d[0]
        pts.append((p0[0] + s * d[0], p0[1] + s * d[1]))
    out = math.degrees(math.atan2(-d[1], d[0]))
    return pts, n, out


# ================================================================= 그림 1
def fig_room(L):
    """설치된 모습. 방을 옆에서 자른 단면 하나에 있을 것을 다 넣는다.

    말해야 하는 것이 넷이다.
      1  프로젝터가 어디에 어떻게 놓이나 (높이 2 m, 수평보다 45~60 도 위로)
      2  패널이 어디 붙나 (천장 6 m). 그래서 30~45 도로 맞는다.
      3  밝게 되돌아가는 쪽은 빛이 온 쪽 -- 프로젝터가 서 있는 바닥이다.
      4  관객 상당수가 바로 그 쪽에 서 있다.
    글자가 서로 겹쳐 못 읽은 판이 두 번 있었다. 각도 글자는 오른쪽 빈 칸에
    세우고 가는 안내선으로 닿는 자리를 가리킨다.
    """
    ko = L["lang"] == "ko"
    W, H = 920, 520
    mx, cy, fy = 74.0, 74.0, 400.0
    sx = (W - mx - 46.0) / ROOM["w"]
    sy = (fy - cy) / ROOM["ceil"]
    rw = ROOM["w"] * sx
    o = ['<svg viewBox="0 0 %d %d" width="100%%" style="height:auto" '
         'font-family="var(--kr)">' % (W, H)]
    o.append('<rect width="%d" height="%d" fill="#f4f1eb"/>' % (W, H))

    # ---- 천장에 붙은 패널. 셀이 있다는 것이 보이게 톱니로 그린다.
    o.append('<rect x="%.0f" y="%.0f" width="%.0f" height="9" fill="#2b2b2b"/>'
             % (mx, cy - 19, rw))
    d = ["M %.1f %.1f" % (mx, cy - 10)]
    for _ in range(int(rw // 11)):
        d.append("l 5.5 9 l 5.5 -9")
    o.append('<path d="%s" fill="none" stroke="#4a463f" stroke-width="1.6"/>'
             % " ".join(d))
    o.append('<text x="%.0f" y="%.0f" font-size="13" font-weight="700" '
             'fill="#c8401c">%s</text>'
             % (mx, cy - 27,
                "천장에 붙인 패널" if ko else "panels on the ceiling"))
    o.append('<text x="%.0f" y="%.0f" font-size="11" fill="#8a8378" '
             'text-anchor="end">%s</text>'
             % (mx + rw, cy - 27,
                (("천장 %.0f m · 방 %.0f x %.0f m" if ko else
                  "ceiling %.0f m · room %.0f x %.0f m")
                 % (ROOM["ceil"], ROOM["w"], ROOM["w"]))))

    o.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="#b9b2a6" '
             'stroke-width="2"/>' % (mx, fy, mx + rw, fy))

    # ---- 높이 자
    o.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="#cfc8bb" '
             'stroke-width="1"/>' % (mx - 26, cy, mx - 26, fy))
    for yy, lab in ((cy, "%.0f m" % ROOM["ceil"]),
                    (fy - ROOM["proj"] * sy, "%.0f m" % ROOM["proj"]),
                    (fy, "0")):
        o.append('<line x1="%.0f" y1="%.1f" x2="%.0f" y2="%.1f" '
                 'stroke="#cfc8bb" stroke-width="1"/>'
                 % (mx - 31, yy, mx - 21, yy))
        o.append('<text x="%.0f" y="%.1f" font-size="10" fill="#8a8378" '
                 'text-anchor="end" font-family="var(--mono)">%s</text>'
                 % (mx - 35, yy + 3, lab))

    # ---- 프로젝터. 받침대 위에 얹고 몸통은 쏘는 각으로 기울인다.
    px = mx + 1.0 * sx
    py = fy - ROOM["proj"] * sy
    o.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" fill="#c7cfda"/>'
             % (px - 14, fy, px + 14, fy, px, py + 8))
    o.append('<g transform="rotate(-52 %.1f %.1f)">'
             '<rect x="%.1f" y="%.1f" width="36" height="16" rx="3" '
             'fill="#1e5fa8"/>'
             '<rect x="%.1f" y="%.1f" width="7" height="10" rx="1.5" '
             'fill="#8fb4dd"/></g>'
             % (px, py, px - 12, py - 8, px + 20, py - 5))
    o.append('<text x="%.0f" y="%.0f" font-size="12" fill="#1e5fa8" '
             'font-weight="700" text-anchor="middle">%s</text>'
             % (px, fy + 18, "프로젝터" if ko else "projector"))
    o.append('<text x="%.0f" y="%.0f" font-size="11" fill="#1e5fa8" '
             'text-anchor="middle">%s</text>'
             % (px, fy + 32,
                ("높이 %.0f m" if ko else "%.0f m up") % ROOM["proj"]))

    # ---- 두 빔. 글자는 오른쪽 빈 칸에 세우고 안내선으로 가리킨다.
    rise = ROOM["ceil"] - ROOM["proj"]
    LX = mx + 5.9 * sx
    hits = {}
    for el, col, ly in ((ROOM["el_hi"], "#e0a44e", cy + 42),
                        (ROOM["el_lo"], "#c8401c", cy + 100)):
        run = rise / math.tan(math.radians(el))
        hx = px + run * sx
        hits[el] = hx
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                 'stroke-width="2.5"/>' % (px, py, hx, cy, col))
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                 'stroke-width="1" stroke-dasharray="3 3" opacity="0.85"/>'
                 % (hx, cy, hx, cy + 32, col))
        o.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f" fill="none" '
                 'stroke="%s" stroke-width="1" opacity="0.55"/>'
                 % (hx, cy + 32, hx, ly - 4, LX - 8, ly - 4, col))
        o.append('<text x="%.1f" y="%.1f" font-size="12" fill="%s" '
                 'font-weight="700">%s</text>'
                 % (LX, ly, col,
                    (("%.0f도로 쏘면 패널은 %.0f도로 맞는다" if ko else
                      "fire at %.0f&deg;, the panel takes %.0f&deg;")
                     % (el, 90.0 - el))))
        o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#8a8378">%s</text>'
                 % (LX, ly + 15,
                    (("프로젝터에서 %.1f m 앞. 점선이 판 법선." if ko else
                      "%.1f m out. Dashes are the panel normal.") % run)))

    # ---- 공중 이미지. 두 빔 사이 허공에 뜬다.
    imx = (px + hits[ROOM["el_lo"]]) / 2.0 - 22.0
    imy = (py + cy) / 2.0 + 34.0
    o.append('<ellipse cx="%.1f" cy="%.1f" rx="48" ry="27" fill="#e8c15a" '
             'opacity="0.32"/>' % (imx, imy))
    o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#a8760c" '
             'font-weight="700" text-anchor="middle">%s</text>'
             % (imx, imy + 4, "공중 이미지" if ko else "mid-air image"))

    # ---- 되돌아오는 빛. 온 길 그대로라 빔 위에 겹치므로 살짝 띄운다.
    h45 = hits[ROOM["el_lo"]]
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#5f7a2c" '
             'stroke-width="2" stroke-dasharray="7 4" '
             'transform="translate(12,9)"/>' % (h45, cy + 3, px + 18, py - 3))
    o.append('<text x="%.1f" y="%.1f" font-size="12" fill="#5f7a2c" '
             'font-weight="700">%s</text>'
             % (mx + 3.6 * sx, fy - 190,
                "되돌아오는 빛은 온 길 그대로다" if ko else
                "the return runs back the way it came"))
    o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#7a8a5a">%s</text>'
             % (mx + 3.6 * sx, fy - 175,
                "프로젝터가 서 있는 바닥이 밝은 쪽이다" if ko else
                "the projector's floor is the bright side"))

    # ---- 관객 둘. 하나는 밝은 쪽, 하나는 지나친 쪽.
    for frac, tone, note in (
            (3.4, "#c8401c",
             "프로젝터와 같은 쪽" if ko else "same side as the projector"),
            (9.0, "#6b6b6b",
             "패널을 지나친 쪽" if ko else "past the panel")):
        ax = mx + frac * sx
        ay = fy - ROOM["eye"] * sy
        o.append('<circle cx="%.1f" cy="%.1f" r="6" fill="%s"/>'
                 % (ax, ay - 7, tone))
        o.append('<path d="M %.1f %.1f L %.1f %.1f M %.1f %.1f L %.1f %.1f '
                 'M %.1f %.1f L %.1f %.1f" stroke="%s" stroke-width="2.6" '
                 'fill="none"/>'
                 % (ax, ay - 1, ax, ay + 16, ax, ay + 16, ax - 6, fy,
                    ax, ay + 16, ax + 6, fy, tone))
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                 'stroke-width="1.3" stroke-dasharray="2 4" opacity="0.75"/>'
                 % (ax, ay - 11, h45, cy + 3, tone))
        o.append('<text x="%.1f" y="%.1f" font-size="12" fill="%s" '
                 'font-weight="700" text-anchor="middle">%s</text>'
                 % (ax, fy + 18, tone, "관객" if ko else "audience"))
        o.append('<text x="%.1f" y="%.1f" font-size="11" fill="%s" '
                 'text-anchor="middle">%s</text>' % (ax, fy + 32, tone, note))

    # ---- 가로 자
    o.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="#cfc8bb" '
             'stroke-width="1"/>' % (mx, fy + 48, mx + rw, fy + 48))
    o.append('<text x="%.1f" y="%.0f" font-size="10" fill="#8a8378" '
             'text-anchor="middle" font-family="var(--mono)">%.0f m</text>'
             % (mx + rw / 2, fy + 45, ROOM["w"]))

    o.append('<text x="%.0f" y="%d" font-size="13" font-weight="700" '
             'fill="#c8401c">%s</text>'
             % (mx, H - 26,
                "패널이 받는 각도는 30~45도. 정면은 이 방에 없다." if ko else
                "The panel takes 30 to 45 degrees. Head-on is not in this room."))
    o.append('<text x="%.0f" y="%d" font-size="11" fill="#8a8378">%s</text>'
             % (mx, H - 10,
                "정면이 되려면 프로젝터가 천장 바로 밑에 있어야 하는데, 그러면 "
                "빔이 위로 안 가고 공중 이미지가 안 생긴다." if ko else
                "Head-on would need the projector directly under the ceiling, "
                "and then the beam never goes up and there is no mid-air image."))
    o.append('</svg>')
    return "\n".join(o)


# ================================================================= 그림 2
def fig_cell(L):
    """셀 하나를 옆에서 자른다. 빛과 세 시선을 같이 그린다.

    이 그림의 값어치는 **각도가 진짜 각도**라는 데 있다. 밝은 벽의 끝에서
    40 도로 올려다본 선이 셀 반대쪽 입구를 정확히 스치고 나간다. 그게
    "빛이 온 쪽에서만 밝은 벽 전체가 보인다" 는 말의 그림이다. 좌표를 손으로
    찍었으면 이 성질이 안 맞았을 것이고, 그림이 설명을 못 했을 것이다.
    """
    ko = L["lang"] == "ko"
    S = 10.5                                    # mm 당 화소
    # 폭은 그림이 실제로 쓰는 만큼만. 920 이었을 때 오른쪽 3분의 1 이
    # 통째로 비었다.
    W, H = 740, 790
    # y0 는 셀 입구. 위로 눈 셋과 그 숫자가 올라가므로 210 을 비워 둔다.
    # 첫 판은 120 이어서 숫자가 그림 위로 잘려 나갔다.
    x0, y0 = 270.0, 210.0                       # 첫 벽 왼쪽, 입구
    cw, cd = PITCH * S, DEPTH * S
    tw = max(4.0, 0.08 * S * 12)                # 포일. 굵게 그린다고 캡션에 적었다.
    lit = REACH * S
    o = ['<svg viewBox="0 0 %d %d" width="100%%" style="height:auto" '
         'font-family="var(--kr)">' % (W, H)]
    o.append('<rect width="%d" height="%d" fill="#f4f1eb"/>' % (W, H))

    # 바닥판과 벽 셋 (셀 두 개)
    o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
             'fill="#3b3a36"/>' % (x0, y0 + cd, 2 * cw + tw, 14))
    o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#8a8378">%s</text>'
             % (x0, y0 + cd + 30,
                "바닥판 · 5 % 페인트" if ko else "backing plate · 5 % paint"))
    for i in range(3):
        wx = x0 + i * cw
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                 'fill="#6e6a60"/>' % (wx, y0, tw, cd))
    # 밝아진 면은 **하나**다. 그린 빔이 오른쪽 셀로 들어가 왼쪽 벽에 닿으니,
    # 그 벽의 오른쪽 면만 밝다. 첫 판에서는 오른쪽 벽까지 노랗게 칠했는데,
    # 그 면은 옆 셀에서 들어온 빛이 맡는 자리라 이 그림에 없는 이야기였다.
    # 벽 전체를 칠하면 어느 면인지 안 보이므로 얇은 띠로 면만 칠한다.
    o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
             'fill="#e8c15a"/>' % (x0 + cw + tw, y0, 5.0, lit))

    # 무소가 닿는 깊이
    my = y0 + 20.0 * S
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#4a7fb5" '
             'stroke-width="1.2" stroke-dasharray="5 4"/>'
             % (x0 - 34, my, x0 + 2 * cw + tw + 30, my))
    o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#4a7fb5" '
             'text-anchor="end">%s</text>'
             % (x0 - 40, my + 4, "무소 20 mm" if ko else "Musou 20 mm"))

    # 밝은 깊이 표시
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#c8901c" '
             'stroke-width="1.2"/>' % (x0 - 34, y0 + lit, x0 - 6, y0 + lit))
    o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#a8760c" '
             'text-anchor="end">%s</text>'
             % (x0 - 40, y0 + lit + 4,
                ("빛이 닿는 끝 %.1f mm" if ko else "light stops at %.1f mm") % REACH))

    # 들어오는 빔과 세 시선.
    #
    # 눈 A 는 **빔이 온 길 위에** 놓는다. 자리를 따로 잡은 게 아니라, 밝은 벽
    # 아래 끝에서 40 도로 올려다본 선이 셀 반대쪽 입구를 정확히 스치고 나가서
    # 그 길이 곧 빔이 들어온 길이기 때문이다. 그림에서 두 선이 겹치는 것이
    # 우연이 아니라 이 보고서가 하려는 말 그 자체다.
    t = math.radians(INC)
    STAND = 120.0                               # 입구에서 눈까지 세로 거리
    bx2, by2 = x0 + cw + tw, y0 + lit           # 밝은 벽 아래 끝
    bx0, by0 = x0 + 2 * cw + math.tan(t) * STAND, y0 - STAND
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#c8401c" '
             'stroke-width="2.5"/>' % (bx0, by0, bx2, by2))
    # 빛이 가는 쪽을 화살로 찍는다. 눈과 같은 자리라 방향이 헷갈릴 수 있다.
    mxp, myp = (bx0 + bx2) / 2.0, (by0 + by2) / 2.0
    o.append('<path d="M %.1f %.1f l %.1f %.1f l %.1f %.1f z" fill="#c8401c"/>'
             % (mxp, myp, 7.0, -3.0, -1.0, 9.0))
    # 글자는 셀 입구 위 빈 자리에. 가운데에 뒀더니 벽에 걸쳤다.
    lx, ly2 = bx0 + 0.30 * (bx2 - bx0), by0 + 0.30 * (by2 - by0)
    o.append('<text x="%.1f" y="%.1f" font-size="12" fill="#c8401c" '
             'font-weight="700" text-anchor="end">%s</text>'
             % (lx - 10, ly2 + 4,
                ("빔 %.0f도" if ko else "beam %.0f&deg;") % INC))

    def eye(ex, ey, label, val, col, from_pt, dashed=True):
        if dashed:
            o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                     'stroke="%s" stroke-width="1.8" stroke-dasharray="6 4"/>'
                     % (from_pt[0], from_pt[1], ex, ey, col))
        o.append('<circle cx="%.1f" cy="%.1f" r="9" fill="#f4f1eb" stroke="%s" '
                 'stroke-width="2"/>' % (ex, ey, col))
        o.append('<circle cx="%.1f" cy="%.1f" r="3.4" fill="%s"/>' % (ex, ey, col))
        o.append('<text x="%.1f" y="%.1f" font-size="12" fill="%s" '
                 'font-weight="700" text-anchor="middle">%s</text>'
                 % (ex, ey - 20, col, label))
        o.append('<text x="%.1f" y="%.1f" font-size="17" fill="%s" '
                 'font-weight="800" text-anchor="middle" '
                 'font-family="var(--mono)">%s</text>' % (ex, ey - 38, col, val))

    rA = COMB[[r["obs_elev"] for r in COMB].index(40.0)]
    r0 = COMB[[r["obs_elev"] for r in COMB].index(0.0)]
    vA, vB, vC = pk(rA, 40.0), pk(r0, 40.0), pk(rA, -40.0)

    # A 같은 쪽. 빔이 시작하는 바로 그 자리다. 그래서 안내선을 안 그린다.
    eye(bx0, by0, "같은 쪽" if ko else "same side", "%.4f" % vA, "#c8401c",
        None, dashed=False)
    # B 정면. 같은 셀의 관 축을 똑바로 내려다보면 바닥판만 보인다.
    bxm = x0 + cw + tw + cw * 0.5
    eye(bxm, y0 - STAND, "정면" if ko else "head-on", "%.4f" % vB, "#4a7fb5",
        (bxm, y0 + cd))
    # C 반대쪽. **같은 셀**의 오른쪽 벽면을 본다. 밝지 않은 면이다.
    # 첫 판에서는 옆 셀 벽을 가리켰다. 같은 셀 안에서 견줘야 말이 된다.
    cxp = x0 + 2 * cw
    eye(cxp - math.tan(t) * (lit + STAND), y0 - STAND,
        "반대쪽" if ko else "far side", "%.4f" % vC, "#6b6b6b",
        (cxp, y0 + lit))

    for i, (txt, col) in enumerate(((L["why_a"], "#c8401c"),
                                    (L["why_b"], "#4a7fb5"),
                                    (L["why_c"], "#6b6b6b"))):
        yy = H - 74 + i * 19
        o.append('<rect x="%.0f" y="%.0f" width="11" height="11" fill="%s"/>'
                 % (60, yy - 9, col))
        o.append('<text x="%.0f" y="%.0f" font-size="12" fill="#3b3a36">%s</text>'
                 % (78, yy, txt))
    o.append('</svg>')
    return "\n".join(o)



# ================================================================= 그림 3
def fig_curves(L):
    """관객 자리별 밝기를 곡선 넷으로. 이 보고서의 그림 한 장이다.

    표만 보면 "벌집이 평평하고 피라미드가 뾰족하다" 가 안 읽힌다. 숫자 스물넷을
    눈으로 훑어야 알 수 있는 것을 선 넷이 한 번에 보여준다.

    세로축은 눈금을 로그로 안 쓴다. 값이 0.067 에서 0.585 까지라 열 배가 안 되고,
    로그를 쓰면 "평평함" 이 실제보다 심하게 눌려 보인다. 목표선 0.040 은 축
    아래쪽에 붙지만 그것이 사실이다 -- 넷 다 목표에서 한참 멀다.
    """
    ko = L["lang"] == "ko"
    W, H = 900, 500
    ml, mr, mt, mb = 74.0, 210.0, 40.0, 92.0
    pw, ph = W - ml - mr, H - mt - mb
    xs = [r["obs_elev"] for r in COMB]
    x0, x1 = min(xs), max(xs)
    series = [(L["th_comb"], "#c8401c", 3.0,
               [(r["obs_elev"], pk(r, 40.0)) for r in COMB])]
    for h, col in zip(PYRH, ("#7a9a3a", "#4a7fb5", "#8a5fa8")):
        series.append(("%s %.0f" % (L["th_pyra"], h), col, 2.0,
                       [(r["obs_elev"], pk(r, 40.0)) for r in PYR[h]]))
    ymax = max(v for _, _, _, pts in series for _, v in pts) * 1.08

    def X(a):
        return ml + (a - x0) / (x1 - x0) * pw

    def Y(v):
        return mt + ph - (v / ymax) * ph

    o = ['<svg viewBox="0 0 %d %d" width="100%%" style="height:auto" '
         'font-family="var(--kr)">' % (W, H)]
    o.append('<rect width="%d" height="%d" fill="#f4f1eb"/>' % (W, H))
    # 눈금
    step = 0.1
    v = 0.0
    while v <= ymax:
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                 'stroke="#ded8cc"/>' % (ml, Y(v), ml + pw, Y(v)))
        o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#8a8378" '
                 'text-anchor="end" font-family="var(--mono)">%.1f</text>'
                 % (ml - 8, Y(v) + 4, v))
        v += step
    for a in xs:
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                 'stroke="#ded8cc" stroke-dasharray="2 4"/>'
                 % (X(a), mt, X(a), mt + ph))
        o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#8a8378" '
                 'text-anchor="middle" font-family="var(--mono)">%.0f</text>'
                 % (X(a), mt + ph + 18, a))
    o.append('<text x="%.1f" y="%.1f" font-size="12" fill="#3b3a36" '
             'text-anchor="middle" font-weight="700">%s</text>'
             % (ml + pw / 2, mt + ph + 40, L["ax_x"]))
    o.append('<text x="%.1f" y="%.1f" font-size="12" fill="#3b3a36" '
             'font-weight="700" transform="rotate(-90 %.1f %.1f)" '
             'text-anchor="middle">%s</text>'
             % (22, mt + ph / 2, 22, mt + ph / 2, L["ax_y"]))
    # 목표선
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#5f7a2c" '
             'stroke-width="1.6" stroke-dasharray="8 5"/>'
             % (ml, Y(0.040), ml + pw, Y(0.040)))
    o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#5f7a2c" '
             'font-weight="700">%s</text>' % (ml + 6, Y(0.040) - 6, L["ax_goal"]))
    # 곡선
    ends = []
    for name, col, wdt, pts in series:
        pts = [(a, v) for a, v in pts if v is not None]
        d = " ".join("%s %.1f %.1f" % ("M" if i == 0 else "L", X(a), Y(v))
                     for i, (a, v) in enumerate(pts))
        o.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.1f" '
                 'stroke-linejoin="round"/>' % (d, col, wdt))
        for a, v in pts:
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>'
                     % (X(a), Y(v), 4.0 if wdt > 2.5 else 3.0, col))
        la, lv = pts[-1]
        ends.append([Y(lv), X(la), name, col])

    # 이름은 선 끝에 붙인다. 범례를 따로 두면 눈이 왔다 갔다 한다. 다만 끝값이
    # 가까우면 글자가 겹치므로 위아래로 밀어낸다 -- 벌집과 피라미드 100 이
    # 실제로 겹쳐서 둘 다 못 읽었다.
    ends.sort()
    for i in range(1, len(ends)):
        if ends[i][0] - ends[i - 1][0] < 17.0:
            ends[i][0] = ends[i - 1][0] + 17.0
    for ly, lx, name, col in ends:
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                 'stroke-width="1" opacity="0.6"/>'
                 % (lx + 4, Y(0) - (Y(0) - ly), lx + 8, ly, col))
        o.append('<text x="%.1f" y="%.1f" font-size="12" fill="%s" '
                 'font-weight="700">%s</text>' % (lx + 12, ly + 4, col, name))
    o.append('<text x="%.0f" y="%d" font-size="12" font-weight="700" '
             'fill="#c8401c">%s</text>' % (ml, H - 14, L["curves_note"]))
    o.append('</svg>')
    return "\n".join(o)


# ================================================================= 그림 4
def fig_groove(L):
    """골을 눕혀 그리고, 빛이 실제로 간 길을 그대로 그린다.

    세워 그렸더니 높이 250 짜리가 폭 46 화소짜리 바늘구멍이 되어 길이 안
    보였다. 눕히면 긴 축이 가로로 가서 열 번 튕기는 길이 다 보인다.
    각도는 실제 각도이고, 꺾이는 자리는 `groove_path` 가 푼 자리 그대로다.
    """
    ko = L["lang"] == "ko"
    W = 900
    rows = [100.0, 250.0]
    BH = 170.0
    H = int(44 + len(rows) * BH + 44)
    o = ['<svg viewBox="0 0 %d %d" width="100%%" style="height:auto" '
         'font-family="var(--kr)">' % (W, H)]
    o.append('<rect width="%d" height="%d" fill="#f4f1eb"/>' % (W, H))
    ax0, axw = 150.0, 600.0
    S = axw / max(rows)                      # 두 칸을 같은 자로 그린다

    for k, h in enumerate(rows):
        cy = 50.0 + k * BH + BH * 0.5
        g = 90.0 - face_deg(h)
        tg = math.tan(math.radians(g))
        mouth = ax0 + h * S
        halfv = h * tg * S
        for sgn in (1.0, -1.0):
            o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                     'stroke="#6e6a60" stroke-width="3"/>'
                     % (ax0, cy, mouth, cy - sgn * halfv))
        o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                 'stroke="#c9c2b4" stroke-width="1" stroke-dasharray="4 5"/>'
                 % (ax0, cy, mouth + 34, cy))
        o.append('<text x="%.1f" y="%.1f" font-size="11" fill="#8a8378">%s</text>'
                 % (mouth + 40, cy + 4, "골 축" if ko else "groove axis"))

        pts, n, out = groove_path(h)
        d = " ".join("%s %.1f %.1f" % ("M" if i == 0 else "L",
                                       ax0 + u * S, cy - v * S)
                     for i, (u, v) in enumerate(pts))
        o.append('<path d="%s" fill="none" stroke="#c8401c" '
                 'stroke-width="2" stroke-linejoin="round"/>' % d)
        for u, v in pts[1:-1]:
            o.append('<circle cx="%.1f" cy="%.1f" r="2.6" fill="#c8401c"/>'
                     % (ax0 + u * S, cy - v * S))
        o.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="none" '
                 'stroke="#c8401c" stroke-width="2"/>'
                 % (ax0 + pts[0][0] * S, cy - pts[0][1] * S))
        o.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="#5f7a2c"/>'
                 % (ax0 + pts[-1][0] * S, cy - pts[-1][1] * S))

        o.append('<text x="14" y="%.1f" font-size="13" fill="#3b3a36" '
                 'font-weight="700">%s</text>'
                 % (cy - 20, ("높이 %.0f mm" if ko else "height %.0f mm") % h))
        o.append('<text x="14" y="%.1f" font-size="11" fill="#8a8378">%s</text>'
                 % (cy - 2, (("골 반각 %.1f도" if ko else
                              "groove half-angle %.1f&deg;") % g)))
        o.append('<text x="14" y="%.1f" font-size="12" fill="#c8401c" '
                 'font-weight="700">%s</text>'
                 % (cy + 18, (("%d 번 튕긴다" if ko else "%d bounces") % n)))
        o.append('<text x="14" y="%.1f" font-size="12" fill="#5f7a2c" '
                 'font-weight="700">%s</text>'
                 % (cy + 35,
                    (("나간 각 %+.0f도" if ko else "exits at %+.0f&deg;") % out)))
    o.append('<text x="14" y="28" font-size="12" fill="#3b3a36">%s</text>'
             % L["groove_lead"])
    o.append('<text x="14" y="%d" font-size="12" font-weight="700" '
             'fill="#c8401c">%s</text>' % (H - 14, L["groove_note"]))
    o.append('</svg>')
    return "\n".join(o)


# ================================================================= 짓기
style = re.search(r"<style>(.*?)</style>",
                  io.open(STYLE_FROM, encoding="utf-8").read(), re.S).group(1)
NP = COMB[0]["n_phase"]
NS = COMB[0]["samples"]


def build(L):
    ko = L["lang"] == "ko"
    o = io.StringIO()
    o.write('<!doctype html><html lang="%s"><head><meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<title>%s</title>\n' % (L["lang"], L["title"]))
    o.write('<style>%s\n.fig{background:#f4f1eb;border:1px solid var(--line);'
            'border-radius:3px;padding:12px;overflow-x:auto}\n'
            '.tag{font-family:var(--mono);font-size:11px;color:var(--muted);'
            'letter-spacing:.06em}\nul{margin:0;padding-left:20px;max-width:66ch}\n'
            'li{margin:5px 0}\na{color:var(--cy)}\ntd.hot{color:var(--bad);'
            'font-weight:700}\ntd.dim{color:var(--muted)}\n'
            '</style></head><body>\n<div class="wrap">\n' % style)
    o.write('<header><div class="eyebrow">%s</div>\n<h1>%s</h1>\n'
            '<p class="sub">%s</p></header>\n'
            % (L["eyebrow"], L["title"], L["sub"]))

    # 결론
    # 결론에 들어가는 숫자를 손으로 안 적는다. 앞서 무소 10 mm 때 값을
    # 적어 두고 훑기를 20 mm 로 다시 돌린 적이 있다. 글만 옛 숫자로 남았다.
    def at(rows, oe, th):
        return pk(next(r for r in rows if r["obs_elev"] == oe), th)

    P250 = PYR[250.0]
    # 관찰자 20~60 도에서 빔 30 도와 45 도의 평균. 한 자리만 보면 우연에
    # 기댄다.
    seats = [r for r in COMB if r["obs_elev"] >= 20]
    m30 = sum(pk(r, 30.0) for r in seats) / len(seats)
    m45 = sum(pk(r, 45.0) for r in seats) / len(seats)
    c_flat = sum(pk(r, 40.0) for r in seats) / len(seats)
    c_top = max(pk(r, 40.0) for r in seats)
    p_top = max(pk(r, 40.0) for r in P250 if r["obs_elev"] > 0)
    # 어느 자리에서 누가 이기나. **세지 말고 데이터에서 뽑는다** -- 처음에
    # "피라미드가 이기는 곳은 50~60 도뿐" 이라고 적었는데 20 도에서도 이긴다.
    byp = {r["obs_elev"]: pk(r, 40.0) for r in P250}
    cwin, pwin = [], []
    for r in COMB:
        oe = r["obs_elev"]
        if oe not in byp:
            continue
        (cwin if pk(r, 40.0) < byp[oe] else pwin).append(oe)
    deg = "도" if ko else "&deg;"
    j = lambda xs: ", ".join("%.0f%s" % (x, deg) for x in xs) or "-"
    cvals = [pk(r, 40.0) for r in COMB if r["obs_elev"] >= 20]
    pvals = [v for k, v in byp.items() if k >= 20]
    fill = {"v2": (min(cvals), max(cvals), min(pvals), max(pvals),
                   max(pvals) / min(pvals), j(cwin), j(pwin)),
            "v3": (100 * (1 - m30 / m45),),
            "v4": (c_flat,),
            "v7": (c_top / 0.040, p_top / 0.040)}
    o.write('<section><div class="card verdict ok">'
            '<h2 style="margin:0">%s</h2>\n<ul>\n' % L["verdict"])
    for k in ("v1", "v2", "v3", "v4", "v5", "v6", "v7"):
        o.write('<li>%s</li>\n' % (L[k] % fill[k] if k in fill else L[k]))
    o.write('</ul></div></section>\n')

    # 방
    o.write('<section><h2>%s</h2>\n' % L["h_room"])
    o.write('<figure><div class="fig">%s</div>\n'
            '<figcaption class="tag">%s</figcaption></figure>\n'
            % (fig_room(L), L["room_cap"]))
    o.write('<div class="scroll"><table><thead><tr><th>%s</th><th>%s</th>'
            '<th>%s</th></tr></thead><tbody>\n'
            % (L["th_fire"], L["th_run"], L["th_inc"]))
    rise = ROOM["ceil"] - ROOM["proj"]
    for el in (45.0, 50.0, 55.0, 60.0):
        o.write('<tr><td>%.0f&deg;</td><td class="n">%.2f m</td>'
                '<td class="n"><b>%.0f&deg;</b></td></tr>\n'
                % (el, rise / math.tan(math.radians(el)), 90.0 - el))
    o.write('</tbody></table></div></section>\n')

    # 왜 한쪽만 밝은가
    o.write('<section><h2>%s</h2>\n<p>%s</p>\n' % (L["h_why"], L["why_p"]))
    o.write('<figure><div class="fig">%s</div>\n'
            '<figcaption class="tag">%s</figcaption></figure>\n'
            % (fig_cell(L), L["why_cap"]))
    o.write('<p>%s</p></section>\n' % L["why_after"])

    # 관찰자 훑기
    o.write('<section><h2>%s</h2>\n<p>%s</p>\n<p>%s</p>\n'
            % (L["h_obs"], L["obs_p1"], L["obs_p2"]))
    o.write('<p class="tag">%s</p>\n' % (L["cond_obs"] % (NS, NP)))
    # 이 방이 쓰는 빔 각도 셋을 한 표에. 맨 오른쪽은 반대쪽(거울 방향).
    o.write('<div class="scroll"><table><thead><tr><th>%s</th>' % L["th_obs"])
    for b in BEAMS:
        o.write('<th>%s %.0f&deg;</th>' % (L["th_beam"], b))
    o.write('<th>%s</th></tr></thead><tbody>\n' % L["th_opp"])
    for r in COMB:
        o.write('<tr><td>%.0f&deg;</td>' % r["obs_elev"])
        for b in BEAMS:
            v = pk(r, b)
            o.write('<td class="%s">%.4f</td>'
                    % ("hot" if v > 0.05 else "n", v))
        o.write('<td class="n">%.4f</td></tr>\n' % pk(r, -40.0))
    o.write('</tbody></table></div>\n<p>%s</p>\n<p>%s</p></section>\n'
            % (L["obs_p3"], L["obs_p4"]))

    # 관객 자리
    o.write('<section><h2>%s</h2>\n<p>%s</p>\n' % (L["h_seat"], L["seat_p"]))
    o.write('<p class="tag">%s</p>\n' % (L["cond_obs"] % (NS, NP)))
    o.write('<div class="scroll"><table><thead><tr><th>%s</th><th>%s</th>'
            '<th>%s</th></tr></thead><tbody>\n'
            % (L["th_dist"], L["th_view"], L["th_bright"]))
    drop = ROOM["ceil"] - ROOM["eye"]
    for r in COMB:
        v = pk(r, 40.0)
        dh = drop * math.tan(math.radians(r["obs_elev"]))
        hot = ' class="hot"' if v > 0.05 else ' class="n"'
        o.write('<tr><td class="n">%.2f m</td><td class="n">%.0f&deg;</td>'
                '<td%s>%.4f</td></tr>\n' % (dh, r["obs_elev"], hot, v))
    # 표에서 가장 밝은 자리를 그대로 문장에 넣는다.
    top = max(pk(r, 40.0) for r in COMB if r["obs_elev"] > 0)
    o.write('</tbody></table></div>\n<p>%s</p>\n'
            '<p class="tag">%s</p></section>\n'
            % (L["seat_after"] % (top, 1.0 / top, top / 0.040),
               L["seat_warn"]))

    # 네 모양을 한 표에. 나란히 놓아야 어느 쪽이 어두운지 보인다.
    byo = {h: {r["obs_elev"]: r for r in PYR[h]} for h in PYRH}
    o.write('<section><h2>%s</h2>\n<p>%s</p>\n' % (L["h_pyr"], L["pyr_p"]))
    o.write('<p class="tag">%s</p>\n' % (L["cond_pyr"] % (NS, NP)))
    o.write('<div class="scroll"><table><thead><tr><th>%s</th><th>%s</th>'
            % (L["th_obs"], L["th_comb"]))
    for h in PYRH:
        o.write('<th>%s %.0f</th>' % (L["th_pyra"], h))
    o.write('<th>%s</th></tr></thead><tbody>\n' % L["th_which"])
    for r in COMB:
        oe = r["obs_elev"]
        vals = [("comb", pk(r, 40.0))]
        for h in PYRH:
            pr = byo[h].get(oe)
            vals.append(("pyr%.0f" % h, pk(pr, 40.0) if pr else None))
        got = [(k, v) for k, v in vals if v is not None]
        best = min(got, key=lambda kv: kv[1])
        name = L["th_comb"] if best[0] == "comb" \
            else "%s %s" % (L["th_pyra"], best[0][3:])
        o.write('<tr><td>%.0f&deg;</td>' % oe)
        for k, v in vals:
            if v is None:
                o.write('<td class="n">&middot;</td>')
                continue
            o.write('<td class="%s">%.4f</td>'
                    % ("pick" if k == best[0] else
                       ("hot" if v > 0.30 else "n"), v))
        o.write('<td class="n">%s</td></tr>\n' % name)
    o.write('</tbody></table></div>\n')
    o.write('<figure><div class="fig">%s</div>\n'
            '<figcaption class="tag">%s</figcaption></figure>\n'
            % (fig_curves(L), L["curves_cap"]))
    _, nb, outd = groove_path(250.0)
    o.write('<p>%s</p>\n<p>%s</p></section>\n'
            % (L["pyr_after"] % (nb, outd),
               L["pyr_after2"] % (j(cwin), j(pwin))))

    # 높이를 낮추면 골이 벌어진다. 되쏨이 무뎌지나 -- 이번 훑기의 요점.
    o.write('<section><h2>%s</h2>\n<p>%s</p>\n' % (L["h_groove"], L["groove_p"]))
    o.write('<p class="tag">%s</p>\n' % (L["cond_pyr"] % (NS, NP)))
    o.write('<div class="scroll"><table><thead><tr><th>%s</th><th>%s</th>'
            '<th>%s</th><th>%s</th><th>%s</th><th>%s</th>'
            '</tr></thead><tbody>\n'
            % (L["th_h"], L["th_face"], L["th_groove"], L["th_peak40"],
               L["th_at60"], L["th_sharp"]))
    for h in PYRH:
        rows40 = [(r["obs_elev"], pk(r, 40.0)) for r in PYR[h]]
        rows40 = [(a, b) for a, b in rows40 if b is not None]
        peak = max(rows40, key=lambda kv: kv[1])
        v60 = dict(rows40).get(60.0)
        lo = min(v for a, v in rows40 if a > 0)
        f = face_deg(h)
        o.write('<tr><td>%.0f mm</td><td class="n">%.1f&deg;</td>'
                '<td class="n">%.1f&deg;</td><td class="hot">%.4f</td>'
                '<td class="n">%.4f</td><td class="n">%.1f&times;</td></tr>\n'
                % (h, f, 90.0 - f, peak[1], v60, peak[1] / lo))
    o.write('</tbody></table></div>\n')
    o.write('<figure><div class="fig">%s</div>\n'
            '<figcaption class="tag">%s</figcaption></figure>\n'
            % (fig_groove(L), L["groove_cap"]))
    o.write('<p>%s</p></section>\n' % L["groove_after"])

    # 끝 평평 -- 눌러 찍을 수 있느냐가 걸린 자리다.
    o.write('<section><h2>%s</h2>\n<p>%s</p>\n' % (L["h_tip"], L["tip_p"]))
    o.write('<p class="tag">%s</p>\n' % L["cond_tip"])
    o.write('<div class="scroll"><table><thead><tr><th>%s</th><th>%s</th>'
            '<th>%s</th>' % (L["th_h"], L["th_tip"], L["th_tiparea"]))
    for k in ("0", "30", "40", "45"):
        o.write('<th>%s&deg;</th>' % k)
    o.write('<th>%s</th></tr></thead><tbody>\n' % L["th_vs05"])
    for h in (100.0, 250.0):
        base = next(r for r in tipf if r["depth"] == h and r["tip_flat"] == 0.5)
        for r in [x for x in tipf if x["depth"] == h]:
            o.write('<tr%s><td>%.0f mm</td><td>%.1f mm</td>'
                    '<td class="n">%.3f %s</td>'
                    % (' class="pick"' if r["tip_flat"] == 2.0 else "",
                       h, r["tip_flat"], 100 * r["tip_area_frac"], "%"))
            for k in ("0", "30", "40", "45"):
                o.write('<td class="n">%.5f %s</td>' % (100 * r["total"][k], "%"))
            d = 100 * (r["total"]["40"] / base["total"]["40"] - 1)
            o.write('<td class="n">%s</td></tr>\n'
                    % ("&mdash;" if r["tip_flat"] == 0.5 else "%+.1f %%" % d))
    o.write('</tbody></table></div>\n<p>%s</p></section>\n' % L["tip_after"])

    # 하한이던 뭉개기를 확정했다.
    o.write('<section><h2>%s</h2>\n<p>%s</p>\n' % (L["h_smear"], L["smear_p"]))
    o.write('<p class="tag">%s</p>\n' % L["cond_smear"])
    o.write('<div class="scroll"><table><thead><tr><th>%s</th><th>%s</th>'
            '<th>%s</th><th>%s</th></tr></thead><tbody>\n'
            % (L["th_panel"], L["th_sm"], L["th_held"], L["th_need"]))
    for r in wide:
        ok = bool(r["smear_converged"])
        o.write('<tr%s><td>%.0f mm</td><td class="n">%.4f</td>'
                '<td class="%s">%s</td><td class="n">%.0f mm</td></tr>\n'
                % (' class="pick"' if ok else "", r["panel"], r["smear"],
                   "n" if ok else "hot",
                   L["yes"] if ok else L["no"], r["window_needed_mm"] or 0))
    o.write('</tbody></table></div>\n<p>%s</p></section>\n'
            % (L["smear_after"] % (wide[0]["smear"], wide[-1]["smear"],
                                   100 * (wide[-1]["smear"] / wide[0]["smear"]
                                          - 1))))

    # 셀 크기
    o.write('<section><h2>%s</h2>\n<p class="tag">%s</p>\n'
            % (L["h_cell"], L["cond_cell"]))
    o.write('<div class="scroll"><table><thead><tr><th>%s</th>' % L["th_cell"])
    for k in ("0", "20", "30", "40", "45"):
        o.write('<th>%s&deg;</th>' % k)
    o.write('<th>%s</th><th>%s</th></tr></thead><tbody>\n'
            % (L["th_rim"], L["th_reach"]))
    for r in cell:
        pick = ' class="pick"' if r["pitch"] == 9.53 else ""
        o.write('<tr%s><td>%.2f mm</td>' % (pick, r["pitch"]))
        for k in ("0", "20", "30", "40", "45"):
            o.write('<td class="n">%.4f %s</td>' % (100 * r["total"][k], "%"))
        o.write('<td class="n">%.2f %s</td><td class="n">%.1f mm</td></tr>\n'
                % (100 * r["rim_fraction"], "%", r["reach_40deg_mm"]))
    o.write('</tbody></table></div>\n<p>%s</p>\n' % L["cell_p"])
    o.write('<div class="scroll"><table><thead><tr><th>%s</th><th>%s</th>'
            '<th>%s</th></tr></thead><tbody>\n'
            % (L["th_cell"], L["th_half"], L["th_leak"]))
    for p in (9.53, 15.0, 20.0):
        half = math.degrees(math.atan((p / 2.0) / DEPTH))
        o.write('<tr><td>%.2f mm</td><td class="n">%.1f&deg;</td>'
                '<td class="n">%.2f %s</td></tr>\n'
                % (p, half, 100 * math.sin(math.radians(half)) ** 2, "%"))
    o.write('</tbody></table></div>\n<p>%s</p></section>\n' % L["cell_p2"])

    # 장비, 안 잰 것
    for head, keys in ((L["h_rig"], ("r1", "r2", "r3", "r4", "r5")),
                       (L["h_open"], ("o1", "o2", "o3", "o4", "o5"))):
        o.write('<section><h2>%s</h2><ul>\n' % head)
        for k in keys:
            o.write('<li>%s</li>\n' % L[k])
        o.write('</ul></section>\n')

    o.write('<section><p class="tag">%s: '
            '<code>results/comb20/observer_scan_both.json</code> · '
            '<code>cell_15_20_depth40.json</code> · '
            '<code>results/pyramid_height/height_totals.json</code>. '
            '%s: <code>scripts/build_room_report.py</code>. '
            '%s: <code>report/comb/pyramid_height_2026-08-27.html</code>'
            '</p></section>\n' % (L["src"], L["this"], L["also"]))
    o.write('</div></body></html>\n')
    return o.getvalue()


for L in (KO, EN):
    html = build(L)
    # 쓰기 **전에** 본다. 서식 인자 없는 o.write 안의 %% 는 안 줄어들고 화면에
    # 두 개가 그대로 찍힌다. 안 끼워진 %s 는 문단을 통째로 날린다. 둘 다
    # 숫자 검사도 태그 검사도 못 잡고 눈으로만 보인다. 그래서 여기서 막는다.
    bad = [ln.strip()[:90] for ln in html.split("\n")
           if "%%" in ln or "%s" in ln or "%.4f" in ln]
    if bad:
        for ln in bad:
            print("남은 서식: %s" % ln)
        raise SystemExit("서식이 안 풀렸다 -- 발행 안 함")
    path = OUT % L["suffix"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, "w", encoding="utf-8").write(html)
    print("%s  (%d 바이트)" % (path, len(html)))
print("@@DONE@@")
