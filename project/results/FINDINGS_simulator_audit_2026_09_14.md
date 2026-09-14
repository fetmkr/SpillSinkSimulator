**SpillSinkSimulator 검토 — 2026-09-14**

현재 구현은 형상을 탐색하고 가설을 만드는 연구 도구로 가치가 있다. 그러나 실물 반사율·관객 방향 밝기·형상 순위를 확정하는 도구로 쓰기에는 중요한 오류가 남아 있다. 핵심은 렌더러의 연산 정밀도보다, 요청한 실험이 실제로 실행되는지, 재료 모델이 논문과 같은 물리량을 표현하는지, 후처리가 의도한 성능을 측정하는지다.

이번 조사는 기존 프로그램과 재료 파일을 수정하지 않았다. 읽은 코드의 해시는 [metadata.json](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/results/audit_2026_09_14/metadata.json>)에 저장했다. 과거 결과 전체를 다시 렌더하거나 모든 형상의 순위를 재산정하지는 않았다. 따라서 아래 수치는 명시한 재현 조건의 결과이며, 모든 패널에 적용할 보정 계수가 아니다.

**1. 조사 범위와 재현 자료**

현재 정본인 `sim/index.html`, `sim_server.py`, `cyc_worker.py`, `blender_render.py`, `form_buildable.py`, `form_metrics.py`, `rig_v2.py`, Mitsuba 경로와 광선 표시 경로, 재료 JSON, 관련 검증 스크립트를 대조했다. 기존 JOURNAL·CONTEXT·검토 기록은 과거에 수정한 문제를 새 문제로 보고하지 않기 위한 자료로 사용했다. `* 2.*` 사본을 현재 프로그램으로 취급하지 않았다.

레퍼런스 폴더의 PDF 28개를 확인했다. 27개는 텍스트를 추출할 수 있었고, `papers_method/veach_chapter3.pdf`는 실제로는 197바이트짜리 404 HTML이다. 모든 논문을 동등한 깊이로 검토한 것은 아니다. 실제 재료값과 계산법의 근거인 Filip & Vávra, Kaster, Marshall/DePoy 2014, Schmidt 2018, Ngan 2005의 관련 본문·수식·한계를 우선 읽었다. Filip 그림 6은 페이지 전체와 확대한 도표를 직접 확인했다. RF·태양전지·생물 구조 논문의 결과를 현재 mm급 패널의 검증 데이터로 사용하지 않았다.

- [render_probe.py](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/results/audit_2026_09_14/render_probe.py>) / [실행 결과](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/results/audit_2026_09_14/render_probe.json>): Blender 5.1.2 CPU, 실제 코팅 노드 사용, 17개 평판 렌더. 재료 앞면 법선을 +Y로 확인. 균일 환경 256 spp, 광원·관측자 교환 128 spp 및 1024 spp. 같은 화면의 5% Lambertian 대조판으로 입사 코사인과 광원 세기를 정규화했다.
- [arithmetic_probe.py](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/results/audit_2026_09_14/arithmetic_probe.py>) / [실행 결과](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/results/audit_2026_09_14/arithmetic_probe.json>): 실제 `recentre`, `rms_width`, TIS 계산 함수 및 현재 수렴 판정 로직으로 만든 합성 반례. 합성 반례를 실제 패널 측정이라고 해석하면 안 된다.
- [dispatch_probe.py](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/results/audit_2026_09_14/dispatch_probe.py>) / [실행 결과](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/results/audit_2026_09_14/dispatch_probe.json>): 원본 `cyc_worker.main()`을 실행하고 목적 함수에 도착한 인자를 기록했다. HTTP 전체 통합 검사가 아닌, 실제 워커의 인자 전달 검사다.

**2. [P1, 재현] 독립 실행 모드에서 관측자·코팅 설정이 버려진다**

위치: [cyc_worker.py:47](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts/cyc_worker.py:47>), [cyc_worker.py:61](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts/cyc_worker.py:61>). Blender 안에서 실행되는 경로는 [sim_server.py:139](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts/sim_server.py:139>)에 있다.

`python3 scripts/sim_server.py`로 띄운 서버는 측정을 `cyc_worker.py`에 넘긴다. 그런데 워커의 `form` 분기는 spec, thetas, n_phase, samples, beam_w만 전달한다. 다음 설정은 전부 사라진다: coating, deep_coating, paint_depth, floor_coating, diffuse_frac, roughness, slot_df, slot_rough, phis, mm_per_px, obs_elev.

예를 들어 5% 검정 도료, 내부 아노다이징, 도장 깊이 15 mm, 관찰각 40°, 해상도 0.05 mm/px로 요청해도 목적 함수에는 이 값들이 도착하지 않는다. 기본 Musou, 관찰각 0°, 기본 해상도로 계산하게 된다. `measure` 분기도 방위각·바닥 코팅·슬롯별 재료 설정을 버린다. Blender 안에서 서버를 시작한 경로에는 이 인자들이 전달된다. README의 ‘두 실행 모드가 같은 숫자’라는 주장을 현재의 모든 손잡이에 적용할 수 없다.

영향: 사용자가 화면에서 바꾼 관객 위치나 도장이 계산에 반영되지 않는 경우다. 형태와 밝기 사이 비교는 물론 두 서버 실행 방식 사이의 비교도 틀릴 수 있다.

수정 방향: 워커와 내부 실행이 동일한 요청 해석 함수를 사용하도록 합치고, 기본값이 아닌 모든 입력을 넣은 실행 모드 간 동등성 검사를 둔다. 응답에는 요청값과 별도로 실제 해석된 실험 조건을 기록한다.

**3. [P1, 실제 렌더] 코팅의 상호성 위반으로 총반사량 계산의 전제가 깨진다**

위치: [blender_render.py:407](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts/blender_render.py:407>), 깊이별 코팅도 [blender_render.py:370](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts/blender_render.py:370>)에 같은 구성을 사용한다.

현재 재료는 표면 법선과 경로 방향으로 계산한 Fresnel을 Diffuse/Glossy 혼합 비율로 사용한다. Blender 공식 설명에서도 Fresnel 노드는 법선과 보는 방향에 의존한다. 따라서 이 혼합의 가중치는 광원과 관측자를 교환했을 때 일반적으로 같지 않다. 표준 미세면 BRDF의 Fresnel은 미세면의 반각 벡터에 대해 계산한다. [Blender Fresnel 문서](https://docs.blender.org/manual/en/5.0/render/shader_nodes/input/fresnel.html), [PBRT 미세면 모델](https://www.pbr-book.org/3ed-2018/Reflection_Models/Microfacet_Models)

이를 추측에 그치지 않고 현재 코팅으로 확인했다. 같은 평판에서 광원 80°·관측자 -65°와 광원 -65°·관측자 80°를 비교했다. 각도는 패널 법선 기준 부호 있는 각도다. BRDF는 대조판으로 입사 코사인을 제거한 값이다.

| 재료 | 처음 BRDF, sr⁻¹ | 방향 교환 후 | 교환 후 / 처음 |
|---|---:|---:|---:|
| 현재 musou_fit, 128 spp | 0.00415701 | 0.00646398 | **1.55496** |
| 현재 musou_fit, 1024 spp | 0.00415702 | 0.00646393 | **1.55494** |
| 초기 fitted 상수, roughness 0.30 | 0.101364 | 0.342853 | **3.38241** |
| Lambertian 대조 | 0.00318310 | 0.00318309 | **0.9999965** |

물리적인 상호성을 가진 수동 재료라면 이 방향 교환에서 BRDF가 같아야 한다. 현재 모델의 55.5% 차이는 샘플 수를 8배로 늘려도 유지됐다. 이 차이를 모든 패널의 반사율 오차 55.5%로 해석해서는 안 된다. ‘필요한 대칭성이 깨져 있다’는 직접적인 검증 결과다.

`hemi_view`는 균일 환경에서 한 방향으로 나오는 밝기를 읽고, 상호성을 이용해 그 방향에서 입사한 빔의 반구 전체 반사율이라고 부른다. 현재 코팅에서는 이 변환이 정당화되지 않는다. 특히 피라미드 옆면·벌집 벽처럼 국소 입사각이 큰 곳의 해석에 영향을 줄 수 있다.

기존 [validate_physics.py:110](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts/validate_physics.py:110>)의 ‘reciprocity’ 검사는 균일 환경의 한 방향 응답과 단일 광원의 정면 응답을 비교한다. 이것은 광원과 검출기를 교환하는 검사가 아니며, 일반 BRDF에서 두 값이 같아야 할 이유도 없다. Mitsuba 교차검증 역시 Lambertian만 사용하므로 이 코팅 문제를 발견하지 못한다.

수정 방향: 에너지 보존과 상호성을 만족하는 BRDF에 실측 각도 데이터를 함께 맞춘다. 직접 입사시킨 빛을 반구 전체에서 합산하는 별도 검증과 방향 교환 검사를 추가한다. 기존 재료를 새 이름으로 버전 관리하고 재료 교체 전후 결과를 분리한다.

**4. [P1, 원문 대조·렌더] 현재 Musou 값은 인용한 논문의 각도 곡선을 재현하지 않는다**

원문은 Filip & Vávra, *How Dark is Dark?*, 로컬 arXiv v1이다. 식 (1)은 주어진 입사 방향의 BRDF를 출사 반구에 적분한 THR, 식 (3)은 정반사 방향의 반각 5° 원뿔 밖으로 나간 비율 TIS다. 측정은 비편광 LED와 RGB 카메라, 가시광 범위이며 BRDF는 상대 단위로 보고한다. 레이저 세 파장의 개별 물성표는 아니다. :codex-file-citation{path="/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/reference/papers/HowDarkIsDark_2601.05094.pdf" purpose="source"}

첫째, [musou_fit.json:44](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/material/musou_fit.json:44>)은 정면 TIS를 0.985~0.995로 읽어 df=0.993을 정한다. 그러나 그림 6의 주황색 Musou 곡선에서 **0° TIS는 약 0.96**이고, 약 0.99는 15~60° 부근이다. 원시 수치표가 없어 0.96은 도표 판독값이지만, 설정의 구간과 다른 것은 명확하다. 이 값을 곧바로 다른 df 한 개로 대체하면 또 다른 과잉 추론이 된다. THR·TIS·로브 형상을 함께 다시 맞춰야 한다.

둘째, 문서의 ‘5° 원뿔 안 1.5% 이하이므로 전체 광택 몫 0.74% 이하’도 성립하지 않는다. 광택 로브 전체가 그 원뿔 안에 들어간다고 추가 가정해야 가능한 한계다. 넓은 광택 로브는 원뿔 밖으로도 나간다. 프로젝트 자신의 `inside_cone` 함수에서도 df=0.94, α=0.20이면 TIS=0.99013이고, df=0.90, α=0.25이면 TIS=0.99020이다. 둘 다 프로젝트가 주장한 TIS 구간에 들어가지만 df≥0.9926을 만족하지 않는다. 이 반례의 숫자는 근사 GGX 원뿔 모델 내부에서의 계산이며 해당 도료의 참값이라는 뜻이 아니다.

셋째, df를 0.76 부근에서 0.993으로 올리며 Fresnel 항을 약 35분의 1로 줄였지만, 입사각 곡선에 대한 재보정이 없다. 실제 현재 shader로 균일 환경 평판을 읽으면:

| 각도 | 프로젝트가 논문에서 읽은 THR 목표 | 현재 평판 hemi_view | 목표 대비 |
|---|---:|---:|---:|
| 0° | 1.00% | 0.99794% | -0.21% |
| 60° | 1.43% | 1.00644% | **-29.6%** |
| 80° | 3.18% | 1.05805% | **-66.7%** |

이는 우선 ‘현재 프로그램 출력이 자신이 선언한 교정 목표를 재현하지 않는다’는 증거다. 3절의 상호성 문제 때문에 이 hemi_view를 물리적인 입사 THR 자체라고 확정할 수는 없다. 초기 9.5% fitting 잔차를 현재 재료의 정확도라고 쓰는 것은 잘못이다.

수정 방향: 도표 판독값을 입사각과 함께 별도 데이터 파일에 저장하고 원문 그림을 검수한다. 총량만 맞춘 모델·TIS만 맞춘 모델을 따로 채택하지 말고 다각도 BRDF를 공동 적합한다. `measured`는 실제 시료/파장/도포법이 일치하는 값에 한정하고, 다른 재료에서 빌린 값은 `analogue`, 적합값은 `fitted`로 구분한다.

**5. [P1, 합성 반례] p99가 좁은 반사를 지우고 판 크기에 따라 달라진다**

위치: [form_buildable.py:448](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts/form_buildable.py:448>), [form_metrics.py:62](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts/form_metrics.py:62>). 먼저 X 방향과 RGB를 평균해 1D 프로파일을 만들고, 이를 0으로 채운 `nwin` 길이 배열로 옮긴 뒤 p99를 구한다. `nwin`은 판 높이에 따라 증가한다.

같은 프로파일에 폭 35픽셀·높이 0.1의 빔, 그 안에 폭 7픽셀·높이 1.0의 밝은 부분을 두었다. 대조 빔은 같은 폭 35픽셀·높이 1.0이다. 신호와 광원은 그대로 두고 배열 길이만 바꿨다.

| 배열 길이 | 실제 최대값 비 | 현재 p99 비 |
|---:|---:|---:|
| 465, 약 100 mm / 0.215 mm/px | 1.0 | **1.0** |
| 931, 약 200 mm / 0.215 mm/px | 1.0 | **0.1** |

판의 빈 공간만 커졌는데 밝은 반사가 10배 작아진다. p99는 통계값으로서 틀린 계산은 아니다. 하지만 ‘최대 밝기’의 대용으로 쓰고 판 크기가 다른 결과를 비교할 때는 잘못된 판단을 만든다. 더 좁은 반사는 작은 판에서도 지워진다. X 평균 역시 국소 점 반사를 낮출 수 있다.

[sim/index.html:493](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/sim/index.html:493>)의 목표 0.040은 예전 최대값에서 온 값이다. 현재 p99를 그 문턱에 그대로 대입하는 것은 통계량이 다른 비교다.

수정 방향: 관측 거리와 수광 범위에 맞는 고정된 공간/각도 분해능에서 밝기를 정의한다. 좁은 밝은 반사를 평가하려면 독립 샘플로 위치 선택·세기 추정을 분리하거나 고정 크기 구역의 최대 평균을 사용하고, p99는 보조값으로 명시한다. 새 정의에서 목표와 과거 결과를 다시 산출한다.

**6. [P1, 합성 반례] 뭉개짐 수렴 판정이 큰 꼬리를 누락해도 합격한다**

위치: [form_buildable.py:478](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts/form_buildable.py:478>).

현재는 창을 넓히는 도중 두 인접 창에서 smear가 2% 이내이면 즉시 `converged=True`로 멈춘다. 이미 더 넓은 창에서 계산한 값이 달라도 무시한다. 중심에 에너지 72.7%, ±34 mm에 나머지 27.3%가 있는 분포로 재현했다.

| 창 폭 | 관측 RMS | 포함 에너지 | 대조판 대비 smear |
|---:|---:|---:|---:|
| 24 mm | 0.800 mm | 72.7% | 1.00 |
| 48 mm | 0.800 mm | 72.7% | 1.00 |
| 96 mm | 17.780 mm | 100% | 22.22 |
| 100 mm | 17.780 mm | 100% | 22.22 |

현재 코드는 48 mm에서 합격하고 1.00을 선택한다. 창을 96 mm까지 열면 22.22인데도 ‘퍼지지 않는 구조’로 오판하는 셈이다. 기존 감사 문서에 이 유형의 분포가 이미 기록되어 있지만, 수렴 종료 조건은 여전히 그 반례를 통과시키지 못한다. HTTP의 자동 판 확대도 `converged=True`를 믿고 멈추므로 구제하지 못한다.

수정 방향: 가장 넓은 창까지 계산된 값의 안정성을 확인하고, 이후 창에서 값이 다시 움직이면 앞선 수렴을 취소한다. 가장자리 에너지뿐 아니라 2차 모멘트의 잔여 기여도도 검사한다. z90만으로 창을 정하면 10% 미만의 먼 꼬리가 RMS를 크게 바꾸는 경우를 놓칠 수 있다.

**7. [P2, 코드 대조] 16 spp의 근거 실험이 현재 광원·코팅과 다르다**

[gate_sample_budget.py:96](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts/gate_sample_budget.py:96>)은 SPREAD=1.0°이고 현재 `form_buildable.SPREAD_DEG`는 0.05°다. 광원이 900 mm 떨어져 있으므로 전체 벌어짐의 기하학적 폭은 각각 대략 15.7 mm와 0.79 mm다. 실제 강도 프로파일의 FWHM과 같은 숫자는 아니지만, 광원이 다른 것은 분명하다.

또 같은 스크립트의 cfg는 `_coat()` 값을 최상위에 update하지만 `build_scene`는 코팅 상수를 cfg['coating']에서 읽는다. 이 검사는 paint_depth=20을 지정하므로 3D 형상에는 `make_depth_split`이 적용된다. 비어 있는 cfg['coating'] 때문에 상부는 현재 df=0.993에서 구한 상수가 아니라 초기 MUSOU_BODY/MUSOU_SPEC_SCALE을 사용한다. 따라서 이 실험을 현재 코팅의 검증으로 볼 수 없다. 반복 렌더도 시드를 바꾸지 않아 독립 오차 추정이 되지 않는다. 최근 수렴 결과가 있다는 사실만으로 모든 패널·각도·코팅에 16 spp가 충분하다고 일반화할 수 없다.

수정 방향: 실제 실행 경로의 장면 구성을 그대로 재사용하고, 광원·재료·측정 창·통계량을 결과에 기록한다. 독립 시드로 검증하며, 밝기 차이가 불확실성보다 작은 후보는 동률 또는 미확정으로 처리한다. 이번 조사에서 16 spp가 언제나 부족하다고 입증한 것은 아니다. 현재 근거 검사가 그 일반화를 뒷받침하지 못한다는 지적이다.

**8. [P2, 코드 대조] 광선 그림의 fitted는 측정기의 fitted와 다른 모델이다**

위치: [raytrace_viz.py:226](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts/raytrace_viz.py:226>), [sim_server.py:2923](</Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts/sim_server.py:2923>).

광선 표시기는 매 반사마다 일정한 rho를 곱하고, 일정한 df로 확산/정반사를 고른다. 정반사 폭은 GGX가 아닌 임의 방향 흔들기로 만든다. Fresnel의 각도 변화와 상부/내부/바닥 재료 구분도 이 경로에는 없다. 렌더는 이와 다른 노드 재료를 쓴다. 따라서 광선 그림은 형상과 대략적인 경로를 설명하는 도구로 사용할 수 있지만, 그림의 탈출 비율·rho_est로 Cycles 코팅 측정이 맞다고 검증할 수는 없다. 특히 부분 도장된 벌집의 에너지 분배를 이 그림으로 설명하면 오해하기 쉽다.

수정 방향: 그림에 실제 모델의 범위를 표시하거나, 수치 검증에 쓸 때는 같은 BRDF와 재료 구분을 구현한다. 2D 정반사 그림도 별도의 시각화이며 3D 확산계의 정량 검증이 아니다.

**9. 논문에서 가져올 수 있는 범위와 실물에 대한 한계**

Kaster 논문은 5% 반사율, Lambertian 85% + Gaussian 15%, FWHM 25°, 555 nm·비편광의 가정으로 형상 간 차이를 비교했다. 광원에서 출발한 광선을 반구 수신기에 모으며, 현재 프로젝트와 동일한 재료/계측기가 아니다. 논문 자체도 실물을 만들거나 측정하지 않았고, 실제 최적화에는 BRDF 교정과 더 촘촘한 각도 검사가 필요하다고 명시한다. 따라서 Kaster와 비슷한 경향이 나온다는 것만으로 실제 패널의 정확도가 보장되지 않는다. 특히 그 논문도 전방 산란 감소와 후방 산란 증가의 교환 관계를 지적한다. :codex-file-citation{path="/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/reference/papers/Kaster2025_anechoic_2507.05152.pdf" purpose="source"}

Marshall/DePoy 2014 및 Schmidt 2018의 좁은 검출기로 잰 정반사 몫은 전체 GGX 로브의 적분값과 동일하지 않다. 2018 논문은 검출기 거리가 달라지며 수광하는 로브 몫과 값이 달라졌다고 직접 설명한다. 시료의 재료·표면 처리·파장도 현재 도료와 일치하지 않는다. 이 수치를 현재 재료의 df로 바로 고정하는 것은 검증된 변환이 아니다. :codex-file-citation{path="/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/reference/papers/DePoy2014_BlackMaterials_1407.8265.pdf" purpose="source"} :codex-file-citation{path="/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/reference/papers/TAMU2018_BlackMaterialsII.pdf" purpose="source"}

Ngan 2005는 서로 다른 BRDF 모델이 같은 시료를 얼마나 잘 설명하는지 비교한다. Ward와 Cook–Torrance 계수의 숫자가 비슷하다는 이유로 그 값을 GGX α와 동일시할 수 없다. 분포와 파라미터의 정의가 다르다. 로컬 본문은 상세 파라미터가 보충자료에 있다고 명시하지만, 해당 보충자료는 폴더에 없었다. 따라서 material/_sources.json의 0.0367/0.0392 자체를 이번 조사에서 원표와 대조 확인하지 못했다. `wall_5pct`의 roughness를 실제 사용할 도료에서 직접 측정한 값으로 표시하는 것은 과하다. :codex-file-citation{path="/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/reference/papers/Ngan2005_BRDF_models_MERL_TR2005-151.pdf" purpose="source"}

추가 적용 한계는 다음과 같다.

- 445/520/635 nm의 레이저를 계산해도 현재 재료는 회색 RGB 상수를 쓴다. 스펙트럼·측정 BSDF 표가 있어도 로더는 사용하지 않는다고 출력한다. 색별 성능을 현재 값에서 단정할 수 없다.
- 편광, 간섭·스페클, 파동 효과, 코팅의 미세구조와 도포 불균일은 명시적으로 모델링하지 않는다. mm급 거시 형상 탐색에 기하광학을 쓰는 것은 타당하지만 나노 구조나 실제 레이저의 국소 밝기까지 같은 정확도로 예측하는 것은 별개다.
- 제조 팁 반경, 도막 두께, 이음새, 표면 거칠기·방향성, 오염이 바뀌면 특히 좁은 반사의 세기와 방향이 달라질 수 있다. 이상적인 메시에 대한 결과는 그 제작 편차의 검증이 아니다.
- `hemi_view`의 균일 조사 총량과 유한 폭 빔·특정 위치의 밝기는 별개의 성능이다. 한 선의 응답으로 모든 그림을 컨볼루션하려면 선형성 외에 위치 불변성도 필요하다. 불규칙 구조와 위상 의존성이 큰 배열에는 단일 평균 LSF만으로 개별 문자 가독성을 확정할 수 없다.
- 관객 한 방향의 결과로 관객 전체를 대표하면 안 된다. 현재 코드에 관측각 손잡이는 있지만, 위 2절의 전달 오류와 좁은 각도 봉우리를 놓치는 샘플링은 따로 해결해야 한다.

**10. 어떻게 만들어졌는가에 대한 의견**

구성은 `형상 파라미터 → Python 메시 생성 → HTTP 요청 → Cycles 장면 → 선형 EXR → 지표 → 웹 화면/보고서`다. 구조별 생성기가 분리되어 있고, 같은 형상에서 제작용 STL/STEP도 뽑는다. 2D/3D 광선 그림은 설명용, Mitsuba는 주로 Lambertian 조건의 외부 교차검증 역할이다. 논문 한 편을 그대로 구현한 시뮬레이터라기보다는, 여러 논문의 구조 아이디어·재료 자료를 조합하고 시행착오를 거치며 확장한 연구 도구다.

좋은 선택도 구체적이다. 숫자를 표시용 PNG가 아니라 선형 EXR에서 읽고, 디노이즈·클램핑을 끄며, 같은 화면에 대조판을 둔다. 총반사량·형태·방향 밝기를 분리해 본다. 제조 최소 피처를 고려하고, 폐기한 결론과 원인을 보존하며, 다른 렌더러와 해석식을 붙인 점은 문제를 추적하는 데 실제 도움이 된다. 코드와 기록이 있어 이번 오류들도 재현할 수 있었다.

가장 약한 부분은 변경 관리와 검증의 범위다. 동일한 입력이 내부 서버와 subprocess에서 다르게 전달되고, 검증 스크립트가 실제 실험과 다른 장면을 만들며, 측정 통계량이 바뀌어도 기존 목표가 남아 있다. 오래된 주석의 ‘검증됨’, ‘정확히 같다’, ‘이 값밖에 없다’는 문장이 현 코드의 보증처럼 읽히기도 한다. 많은 검사가 존재하는 것과 핵심 물리 전제가 검증된 것은 다르다.

권장 순서는 다음과 같다.

1. 요청 전달을 한 경로로 합치고 실행 조건을 모두 기록한다. 이것은 입력을 믿을 수 있게 만드는 비교적 작은 소프트웨어 수정이다.
2. 상호성을 만족하는 재료 모델과 논문의 다각도 데이터를 맞춘다. 논문 판독값·실측·추정을 구분하고 재료에 버전/해시를 붙인다.
3. p99와 최대 밝기를 구분하고 수렴 종료를 바로잡은 뒤 목표값을 새 통계량으로 다시 정한다.
4. 대표 평판·벌집·피라미드만 골라 독립 시드, 관측각, 해상도, 창 크기, 빔 위치를 바꿔 재검증한다. 전체 형상 탐색을 먼저 늘릴 필요는 없다.
5. 실제 도포법으로 만든 평판의 BRDF/총반사율과 대표 구조 시편의 총량·각도별 밝기를 측정해 예측과 비교한다. 물성 적합에 사용하지 않은 각도와 시편을 남겨 검증해야 한다.

이 순서 전에는 현재 숫자를 ‘가정한 모델에서 얻은 탐색 결과’로 읽는 것이 적절하다. 위 결함이 있다고 모든 형상 아이디어가 무효가 되는 것은 아니다. 다만 어느 설계가 실제로 몇 배 더 어둡고, 어느 자리에서 그림이 사라지는지는 다시 확인해야 한다.

**재현 방법**

저장소 루트에서 아래 스크립트를 실행한다. 앞의 두 개는 numpy가 있는 Python을 사용한다. 마지막은 로컬 Blender가 필요하며 CPU로 작은 평판만 렌더한다. 운영 중인 서버를 실행하거나 기존 측정 결과를 덮어쓰지 않고, 이 감사 폴더의 결과 JSON만 다시 쓴다.

```text
python3 project/results/audit_2026_09_14/arithmetic_probe.py
python3 project/results/audit_2026_09_14/dispatch_probe.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --threads 6 --python-exit-code 77 --python project/results/audit_2026_09_14/render_probe.py
```
