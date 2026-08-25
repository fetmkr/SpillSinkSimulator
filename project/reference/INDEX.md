# reference/ — 남이 잰 것들

이 프로젝트는 **직접 재지 않고 남이 잰 값을 찾아 쓴다.** 그 원본이 여기 있다.

PDF 자체는 git 에 안 들어간다 (`.gitignore`, 남의 저작물이라서). **이 목록은
들어간다.** 파일이 없어져도 여기 적힌 것으로 다시 받을 수 있고, 무엇보다
**우리가 각 논문에서 정확히 무엇을 가져왔는지**가 여기 적혀 있다.

2026-08-25 기준 19 편. 전부 첫 쪽을 열어 확인했다.

---

## papers/ — 검정 재료와 빛

| 파일 | 무엇 | 우리가 가져온 것 |
|---|---|---|
| `HowDarkIsDark_2601.05094.pdf` | Filip & Vávra, *How Dark is Dark? A Reflectance and Scattering Analysis of Black Materials*. arXiv:2601.05094. 11쪽 | **5도 원뿔 TIS.** 이걸 우리 BSDF 로 역산해서 무광 검정의 거칠기 창 0.012~0.089 를 얻었다. [[roughness-decides-the-flash]] 의 근거 |
| `DePoy2014_BlackMaterials_1407.8265.pdf` | DePoy 외 (Texas A&M), *Characterization of the Reflectivity of Various Black Materials*. arXiv:1407.8265. 8쪽 | **그림 6, 재료 36 종의 정반사 비율.** 도료·테이프·식모·펠트가 전부 0.2 % 아래. 한때 이 그림의 퍼센트 축을 분수로 읽어 100 배 틀렸다 |
| `TAMU2018_BlackMaterialsII.pdf` | Schmidt 외, *Characterization of the Reflectivity of Various Black Materials II*. 8쪽 | 위 논문의 후속. 정반사 0.07~0.59 % 로 위 결과를 뒷받침 |
| `Shirsekar2019_Z302_BRDF_thesis.pdf` | Shirsekar, *Bidirectional Reflectance Measurements of Low-Reflectivity Optical Coating Z302*. 학위논문 74쪽 | 검정 도료의 BRDF 를 각도별로 실제로 잰 것. 로브 모양의 기준 |
| `Zeng2019_LowReflectance_NASA.pdf` | Zeng 외 (NASA GSFC), *Optical studies of low reflectance coatings*. 10쪽 | 우주용 초저반사 도료의 반사율. 우리 재료표의 상한 감각 |
| `Aeroglaze_Z306_datasheet.pdf` | Aeroglaze Z306 무광 검정 폴리우레탄 제품 자료. 3쪽 | 실제로 파는 도료의 공표 반사율 |
| `Ngan2005_BRDF_models_MERL_TR2005-151.pdf` | Ngan, Durand, Matusik, *Experimental Analysis of BRDF Models*. MERL TR2005-151 (EGSR 2005). 13쪽 | **MERL 실측 BRDF 100 종에 모델 일곱을 맞춘 값.** `paint-black` 이 Ward a = 0.0367, Cook-Torrance m = 0.0392. 우리가 쓰는 α 0.039 를 **관계없는 방법으로** 확인해 준 것 |
| `Kaster2025_anechoic_2507.05152.pdf` | Kaster (Carl Zeiss), *Macroscopic Structural Light Absorbers*. arXiv:2507.05152. 12쪽 | 그의 0.65 배가 대부분 30.6 % 평면 캡 때문임을 재현. `results/FINDINGS_kaster.md` |
| `Davis2020_butterfly_ultrablack_NatComm.pdf` | Davis, Nijhout & Johnsen, *Diverse nanostructures underlie thin ultra-black scales in butterflies*. Nat Commun 2020. 7쪽 | 생물이 만든 초검정 구조. 우리 규모(mm)와 파장 규모가 달라 직접은 못 쓰고, "구조로 검게 만든다" 의 상한 사례 |
| `Mouchet2024_IR_absorbers_nature_2404.18169.pdf` | Mouchet, *Infrared absorbers inspired by nature*. arXiv:2404.18169. 25쪽 | 자연이 만든 적외선 흡수 구조 총설 |

**못 받은 것 (유료)**

- Davis 외, *Ultra-black Camouflage in Deep-Sea Fishes*. Current Biology 2020,
  doi:10.1016/j.cub.2020.06.044. 심해어 16 종이 480 nm 에서 0.5 % 미만을
  되돌린다. Cell Press 유료.

## papers_rf/ — 전파를 흡수·반사하는 형상 (2026-08-25)

빛과 같은 문제인데 파장이 만 배 크다. 그래서 저쪽 수법 대부분은 우리에게
안 넘어온다. 자세히는 `JOURNAL.md` 2026-08-25 항목.

| 파일 | 무엇 | 우리가 가져온 것 |
|---|---|---|
| `SciRep2025_ultrabroadband_MMA.pdf` | Zhang 외, *Ultrabroadband microwave metamaterial absorber with dielectric lossy layer*. Sci Rep 15:12547 (2025). 13쪽 | PLA 3D 프린트 주기 구조(주기 17 mm)의 **옆벽에 저항 잉크**. 4.4~60 GHz 에서 90 % 이상, 상대 대역 173 %, **45 도에서도 평균 95 %**. 옆벽 칠하는 높이가 조절 손잡이라는 점이 우리 "몇 mm 까지 칠하나" 와 같은 질문 |
| `SciRep2025_coding_metasurface_RCS.pdf` | Ullah 외, *Polarization-controlled coding metasurface with phase cancellation and diffusion for enhanced RCS reduction*. Sci Rep (2025). 17쪽 | 위상 0/1 을 바둑판으로 배치해 반사파를 흩는다. 2 비트가 12~19.3 GHz 에서 20 dB. **흡수가 아니라 방향 바꾸기** — 우리 "모양 뭉개기" 축에 대응 |
| `IntechOpen2026_RAM_metasurfaces_design.pdf` | *Radar-Absorbing Materials, Metamaterials, and Metasurfaces: Design Methods, Considerations, and Best Practices*. IntechOpen 2026. 42쪽 | 설계 방법 총설. 형상별 dB 비교는 없다 |
| `ACES_ANN_pyramidal.pdf` | Agatonović 외, *Application of ANNs in Evaluation of Microwave Pyramidal Absorber Performance*. ACES Journal. 8쪽 | 피라미드 흡수체의 **입사각 의존**. 0~90 도에서 반사가 -55 dB 에서 0 dB 까지 오른다 — 우리 판이 40 도에서 나빠지는 것과 같은 방향 |

**못 받은 것**

- *The prospect of using hollow pyramidal microwave absorbers for 5G anechoic
  chamber applications: A review*. J Appl Phys 136, 230701 (2024). AIP 가
  403 으로 막는다. 검색 요약으로만 봤다: 피라미드는 높은 주파수, 쐐기는 낮은
  주파수에 유리하고 쐐기가 뒤로 튕기는 게 적다. 속 빈 것보다 꽉 찬 것이 낫다.
  **원문을 못 읽었으므로 이 문장들은 [추측] 취급한다.**

**웹 자료 (논문 아님, 링크만)**

- 무반향실 설계 규칙 — 피라미드 높이 ≥ 가장 낮은 주파수의 파장, 밑변 ≥ 그
  절반, 끝 폭 < 가장 높은 주파수 파장의 절반, 흡수재 ≥ 파장의 4 분의 1.
  <https://www.signalintegrityjournal.com/articles/51-basic-rules-for-anechoic-chamber-design-part-one-rf-absorber-approximations>

## papers_solar/ — 뒤집힌 피라미드 (2026-08-25)

사용자가 "역으로 뒤집힌 피라미드, 지금 피라미드의 몰드 형태" 를 물어서 찾은
것들. **결론: 저쪽에서 좋은 이유가 우리한테는 나쁜 이유다.** 파인 홈은 빛을
온 쪽으로 되돌려 보내는데(직각 두 면이 코너 리플렉터), 태양전지는 그 되돌아온
빛을 다시 흡수하니 이득이고 우리는 그게 없애야 할 것이다. 우리 실측으로
모양 뭉개기가 1.4589 에서 1.0676 으로 무너졌다.

| 파일 | 무엇 | 우리가 가져온 것 |
|---|---|---|
| `NanoscaleResLett2018_inverted_pyramid_20p19_cell.pdf` | *Fabrication of 20.19% Efficient Single-Crystalline Silicon Solar Cell with Inverted Pyramid Microstructure*. 8쪽 | 뒤집힌 피라미드로 만든 셀의 실제 효율 |
| `NanoscaleResLett2020_inverted_pyramid_PERC.pdf` | *High-Efficiency Silicon Inverted Pyramid-Based Passivated Emitter and Rear Cells*. 9쪽 | 같은 계열, 뒤집힌 구조의 이득 |
| `Nanomaterials2021_inverted_pyramid_morphology.pdf` | Gao 외, *Inverted Pyramid Morphology Control by Acid Modification*. 5쪽 | 뒤집힌 피라미드를 실제로 만드는 방법(산 식각) |

**못 받은 것 (유료)**

- *Comparison of random upright pyramids and inverted pyramid photonic crystals
  in thin crystalline silicon solar cells*. Solar Energy 2023,
  doi:10.1016/j.solener.2023.03.049. **선 피라미드 12~14 %, 뒤집힌 것 7 % 미만**
  (400~1000 nm 가중 반사율). 이 숫자를 `geom_floor._build_pyramid_inv` 주석에
  인용했다. Elsevier 유료 — 검색 요약으로만 봤다.
- *Ray tracing of inverted pyramids for light-trapping in thin crystalline
  silicon*. Optik 2020. 유료.

## datasheets/ — 만드는 쪽

| 파일 | 무엇 | 우리가 가져온 것 |
|---|---|---|
| `Hexcel_HexWeb_CRIII_datasheet.pdf` | Hexcel HexWeb CR III 알루미늄 벌집 규격서. 6쪽 | 3/8 인치 셀의 밀도 등급 표 |
| `Hexcel_3-8-5052-001_matweb.pdf` | HexWeb CR III **3/8-5052-.001** 개별 자료. 2쪽 | **규격 표기가 "셀 크기 – 합금 – 포일 두께"** 이고 3/8 인치(9.53 mm) 셀에 포일 0.001 인치(**0.0254 mm**)가 카탈로그 품목. 우리가 쓰던 0.08 mm 가 오히려 두꺼운 축임을 이걸로 확인했다 |

**웹 자료 (링크만)**

- Corex 벌집 제조 공정 — 포일에 표면 처리를 **붙이기 전에** 한다.
  <https://corex-honeycomb.com/products-and-services/aluminium-honeycomb-manufacturing/>
- Valence, e-coat 대 powder coat — 전착도장은 막힌 구멍·안쪽 공간까지 균일,
  두께 25~50 µm. <https://www.valencesurfacetech.com/the-news/e-coat-vs-powder-coat/>
- Xometry, 흑색 아노다이징 두께 10~25 µm 이고 절반이 알루미늄을 파먹으며 자란다.
  <https://www.xometry.com/resources/machining/black-anodizing/>
- 코디어라이트 벌집 담금 코팅 — 1 mm 관에 길이 100 mm(100 대 1)를 담가서
  30 µm 로 균일하게. <https://www.sciencedirect.com/science/article/abs/pii/S0272884216308343>

## 이 폴더의 나머지

| 파일 | 무엇 |
|---|---|
| `SUMMARY.md` | 논문에서 뽑은 값들을 한자리에 모은 것. 숫자를 쓸 때는 여기가 먼저다 |
| `HONEYCOMB_SPECS.md` | 벌집 규격 정리 (셀 크기, 포일, 밀도) |

---

## 다시 받는 법

arXiv 번호가 있으면 `https://arxiv.org/pdf/<번호>`.
PMC 번호가 있으면 `https://europepmc.org/articles/<PMCxxxxxxx>?pdf=render`
(PMC 직접 링크는 막힌다).
받은 뒤에는 **첫 쪽을 열어 제목을 확인할 것** — 0 바이트나 HTML 오류 쪽을
PDF 이름으로 저장해 놓은 적이 있다 — Kaster 논문이 0 바이트로 앉아 있었다.
