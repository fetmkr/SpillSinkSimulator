"""점멸 누적 측정: 켜짐/꺼짐 프레임 차분으로 약한 반사를 꺼낸다.

사용법:
    1) 레이저에 켜짐/꺼짐이 반복되는 패턴을 띄운다 (예: 1초 켜고 1초 끄기).
    2) 삼각대에 폰을 고정하고 노출/초점/화이트밸런스를 수동 고정해서
       몇 분 동영상을 찍는다. 렌즈 앞에 레이저 파장 필터가 있으면 더 좋다.
    3) 동영상을 프레임 폴더로 푼다:
           ffmpeg -i video.mp4 -vf fps=10 frames/f%05d.png
    4) 이 스크립트를 돌린다:
           python3 scripts/stack_frames.py frames/ out/

원리. 방 조명과 카메라 노이즈는 켜짐 프레임과 꺼짐 프레임에 똑같이
들어 있다. 밝기 합으로 프레임을 켜짐/꺼짐 두 무리로 나누고, 각 무리를
평균한 뒤 빼면 레이저가 만든 빛만 남는다. N 프레임을 쌓으면 노이즈는
루트 N 분의 1로 줄어서, 주변광보다 백 배 천 배 약한 반사도 숫자가 된다.
전파 망원경이 은하 수소 신호를 쌓는 것과 같은 수법이다.

출력:
    out/diff.png      차분 영상 (레이저 성분만, 8비트로 정규화)
    out/diff.npy      차분 영상 원본 float (정량 분석용)
    out/report.txt    프레임 수, 문턱, 평균 밝기, 상위 백분위 값

반사율로 바꾸려면: 같은 조건으로 기준 표면(반사율을 아는 흰 판이나
회색 카드)을 한 번 더 찍어 diff.npy 비율을 낸다. 두 촬영의 노출이
같아야 하므로 반드시 수동 노출로 고정할 것.

배경 빼기, 필수. 레이저가 켜지면 방 전체가 조금 밝아지고(스필이 방을
비춘다), 그 성분은 차분에 고르게 남는다. 합성 검증에서 확인:
전역 깜빡임 1.5를 섞자 목표값 0.8이 2.30으로 읽혔고, 근처 빈 영역
값 1.51을 빼니 0.79로 복원됐다. 그러므로 항상 목표 영역 평균에서
같은 프레임의 근처 비목표 영역 평균을 빼서 쓴다. diff.npy를 열어
두 영역을 지정해 빼는 한 줄이면 된다.
"""

import sys
import os
import glob

import numpy as np
from PIL import Image


def load_lum(path):
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)
    return a.mean(axis=2)


def main(frames_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = sorted(glob.glob(os.path.join(frames_dir, "*.png"))
                   + glob.glob(os.path.join(frames_dir, "*.jpg")))
    if len(paths) < 10:
        print("프레임이 %d장뿐입니다. 최소 10장, 권장 수백 장." % len(paths))
        return 1

    sums = []
    for p in paths:
        sums.append(load_lum(p).mean())
    sums = np.array(sums)
    thr = (sums.max() + sums.min()) / 2.0
    on_paths = [p for p, s in zip(paths, sums) if s >= thr]
    off_paths = [p for p, s in zip(paths, sums) if s < thr]
    if not on_paths or not off_paths:
        print("켜짐/꺼짐이 안 갈립니다. 점멸 패턴과 프레임 속도를 확인하세요.")
        return 1

    def stack(group):
        acc = None
        for p in group:
            f = load_lum(p)
            acc = f if acc is None else acc + f
        return acc / len(group)

    on = stack(on_paths)
    off = stack(off_paths)
    diff = on - off
    diff = np.clip(diff, 0, None)

    np.save(os.path.join(out_dir, "diff.npy"), diff)
    v99 = np.percentile(diff, 99.9)
    vis = np.clip(diff / v99 * 255.0, 0, 255).astype(np.uint8) \
        if v99 > 0 else diff.astype(np.uint8)
    Image.fromarray(vis).save(os.path.join(out_dir, "diff.png"))

    with open(os.path.join(out_dir, "report.txt"), "w") as fh:
        fh.write("frames total %d  on %d  off %d  threshold %.3f\n"
                 % (len(paths), len(on_paths), len(off_paths), thr))
        fh.write("diff mean %.6f  p99 %.6f  p99.9 %.6f  max %.6f\n"
                 % (diff.mean(), np.percentile(diff, 99),
                    v99, diff.max()))
        fh.write("noise floor (off-group frame-to-frame rms of the mean): "
                 "shrinks as 1/sqrt(N); with N=%d expect ~%.4f of one "
                 "frame's noise\n"
                 % (len(off_paths), 1.0 / max(1, len(off_paths)) ** 0.5))
    print("frames %d (on %d / off %d)  ->  %s"
          % (len(paths), len(on_paths), len(off_paths), out_dir))
    print("diff mean %.4f  p99.9 %.4f" % (diff.mean(), v99))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python3 scripts/stack_frames.py <frames_dir> <out_dir>")
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
