# SpillSinkSimulator — 새 세션은 여기부터

레이저 공중 영상이 천장에 닿아 생기는 반사를 줄이는 천장 패널을 설계한다.
시뮬레이터(Blender Cycles)로 세 축을 잰다. 작업 폴더는 `project/`.

## 먼저 읽을 것 (이 순서)

1. `project/CONTEXT.md` 맨 위 절 — 가장 최근 상태 요약 (날짜별로 위에 쌓인다)
2. `project/NEXT.md` 맨 아래 절 — 지금 할 일
3. `project/results/FINDINGS_simulator_audit_2026_09_14.md` 끝의 "조치" 절들과 "다음 세션 시작점"
4. 최종 후보 보고서 `project/report/comb/finalists_2026-09-15.html`
   (아티팩트 https://claude.ai/artifact/XAqBDwoMsWMsEUhRj3EMM7 — 다시 올릴 땐 같은 파일 경로로)
5. 과정과 틀린 길은 `project/JOURNAL.md` 맨 아래. 처음 보는 사람은 `project/START_HERE.md`.

## 세 축 (항상 셋 다, 조건과 빔 폭을 같이 적는다)

- **반사 총량** — 되돌아온 빛의 비율. 낮을수록 좋다.
- **모양 뭉개기** — 민판 대비 번진 폭. 높을수록 좋다. 수렴 안 하면 "하한".
- **정면 반짝임** — 2 mm 상자 평균의 최대, 민판 = 1. 낮을수록 좋다.

측정 규약 상수는 전부 `project/scripts/form_metrics.py` 한 곳에 있다. 화면은 `/api/protocol` 로 받는다.
최종 순위 규칙(방 조건 각도)은 보고서 첫머리와 `build_finalists_report.py` 머리글에 있다.

## 사용자와 일하는 규칙 (어기면 크게 혼났던 것)

- **채팅은 쉬운 한국어.** 영어로 넘어가지 않는다.
- **커밋·푸시는 사용자가 "커밋 푸시" 라고 할 때만.** 맥 사본(`* 2.*`)은 커밋에서 뺀다.
- **사용자가 정한 실험 값(판 크기 116/200/500 등)은 못 바꾼다.** 바꿔야 하면 먼저 묻는다.
- **시킨 것만 한다.** "이미 한 건 그대로 두고 더하기만" 이면 기존 결과·보고서·순위 규칙을 건드리지 않는다
  (2026-09-15, 씨앗 두 개만 더하랬는데 보고서 순위 규칙까지 바꿨다가 되돌림).
- **비용·시간을 이유로 일을 빼먹지 않는다.** 빼야 하면 먼저 묻는다 (2026-09-15 "비용따지지 말고 해").
- **코드 쓰기 전에 문제부터 파악한다** ("일단 문제 부터 파악해. 코드 작성하지말고").
- 사실 주장에 근거 표시: [확인: 무엇으로] / [추측] / [모름]. 동의로 답을 시작하지 않는다.
- 큰 값을 "최악" 이라 부르지 않는다 ("가장 밝은"). 새 폴더를 만들지 않는다.
- **결론은 렌더 씨앗 세 개로.** 원래 씨앗 0 + 무작위 2 개. 같은 씨앗 재현이 맞는 것은
  경로가 같다는 증거일 뿐 흔들림 크기가 아니다.
- 사용자가 켜라고 한 장치는 내 편의로 끄지 않는다. 검사기는 아는 답으로 먼저 검증한다.
- 발표 설계 1,643 개 재산출은 돌리지 않는다 (사용자 지시, 2026-09-15. 12 개에서 멈춰 있음).

## 돌리는 법

```
cd project
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python scripts/sim_server.py
# http://127.0.0.1:8777   코드를 고치면 서버를 다시 켠다. 끌 때 mts_worker·cyc_worker 도 같이 끈다.
python3 scripts/gate_dispatch_equivalence.py     # 요청 전달 (렌더 없음)
python3 scripts/gate_finalists_ui_path.py        # 화면 요청 == 보고서 측정 호출 (렌더 없음)
python3 scripts/reproduce_finalists_server.py    # 켜 둔 서버로 보고서 14 행 다시 렌더해 대조
python3 scripts/measure_finalists_seeds.py       # 무작위 씨앗 2 개로 14 행 추가 측정
python3 scripts/build_finalists_report.py        # 보고서 다시 짓기
```

Blender 배치는 `scripts/run_batch.sh` 로 (완료 표시 @@DONE@@ 없으면 실패로 본다).
