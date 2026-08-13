#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
영상 분석 엔진 — 프레임 추출 · 문자 후보 탐지 · 장면 전환 · 판독 지원

사용법
    # ① 전 구간 개관 (가장 먼저)
    python analyze_video.py survey <영상> --out <디렉터리>

    # ② 문자가 있을 만한 지점 자동 탐지
    python analyze_video.py textscan <영상> --out <디렉터리>

    # ③ 특정 시각 고배율 판독 (여러 파라미터로 뽑아 최선을 고름)
    python analyze_video.py zoom <영상> --at 125 --out <디렉터리>
    python analyze_video.py zoom <영상> --at 125 --crop 0.5,0.4,0.25,0.1 --out <디렉터리>

    # ④ 장면 전환 탐지 — 한 릴에 여러 주제가 편집된 경우
    python analyze_video.py scenes <영상> --out <디렉터리>

    # ⑤ 전체 자동 (①②④를 순서대로)
    python analyze_video.py auto <영상> --out <디렉터리>

왜 이 순서인가
    처음부터 확대 프레임을 뽑으면 어디를 확대할지 알 수 없다.
    전 구간을 한 장으로 훑어 문자가 보이는 지점을 먼저 찾고,
    그 구간만 고배율로 다시 뽑아야 판독이 된다.

의존
    ffmpeg · ffprobe · Pillow · numpy
"""
import argparse, os, re, subprocess, sys, json, glob

# ── 기본 도구 ─────────────────────────────────────────────

def probe(path):
    """길이·해상도·트랙 구성"""
    def q(entries, stream=False):
        cmd = ["ffprobe", "-v", "error", "-show_entries", entries,
               "-of", "csv=p=0", path]
        if stream:
            cmd[4:4] = ["-select_streams", "v:0"]
        return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()

    dur = q("format=duration").split("\n")[0]
    wh = q("stream=width,height", stream=True).split("\n")[0]
    types = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "stream=codec_type", "-of", "csv=p=0", path],
                           capture_output=True, text=True).stdout.split()
    try:
        d = int(float(dur))
    except ValueError:
        d = 0
    return dict(duration=d, size=wh, has_audio="audio" in types,
                streams=sorted(set(types)))


def grab(path, t, out, scale=520, crop=None, eq=None, sharp=False):
    vf = []
    if crop:
        w, h, x, y = crop
        vf.append(f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y}")
    vf.append(f"scale={scale}:-1")
    if eq:
        vf.append(f"eq=contrast={eq}")
    if sharp:
        vf.append("unsharp=5:5:1.0")
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", path,
                        "-vf", ",".join(vf), "-frames:v", "1", out, "-y"],
                       capture_output=True)
    return os.path.exists(out) and os.path.getsize(out) > 1000


def sec_label(t):
    return f"{int(t)//60}:{int(t)%60:02d}"


# ── ① 전 구간 개관 ────────────────────────────────────────

def cmd_survey(a):
    info = probe(a.video)
    d = info["duration"]
    if not d:
        print("영상 길이를 읽지 못했습니다.", file=sys.stderr); sys.exit(1)
    os.makedirs(a.out, exist_ok=True)

    n = a.n
    step = max(1, d // (n + 1))
    made = []
    for i in range(1, n + 1):
        t = step * i
        if t >= d:
            break
        p = os.path.join(a.out, f"t{t}.jpg")
        if grab(a.video, t, p):
            made.append((t, p))

    g = make_grid(made, os.path.join(a.out, "_survey.jpg"), cols=a.cols)
    print(f"길이 {d//60}분 {d%60}초 · {info['size']} · "
          f"{'유성' if info['has_audio'] else '무성'}")
    print(f"프레임 {len(made)}장 · 그리드: {g}")
    print()
    print("다음: 그리드를 보고 문자가 보이는 지점을 찾으십시오.")
    print("      자동 탐지를 원하면 textscan 을 쓰십시오.")
    return info


def make_grid(pairs, out, cols=4, cap=1600):
    from PIL import Image, ImageDraw, ImageFont
    from matplotlib import font_manager as fm
    fb = [x for x in fm.findSystemFonts() if "NotoSansCJK" in x and "Bold" in x]
    F = ImageFont.truetype(fb[0], 19) if fb else ImageFont.load_default()
    if not pairs:
        return None
    ims = [Image.open(p) for _, p in pairs]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    c = Image.new("RGB", (w * cols, (h + 26) * rows), "white")
    d = ImageDraw.Draw(c)
    for i, (im, (t, _)) in enumerate(zip(ims, pairs)):
        x, y = (i % cols) * w, (i // cols) * (h + 26)
        c.paste(im, (x, y))
        d.text((x + 6, y + h + 2), sec_label(t), font=F, fill=(20, 30, 60))
    if c.width > cap:
        r = cap / c.width
        c = c.resize((cap, int(c.height * r)), Image.LANCZOS)
    c.save(out, quality=88)
    return out


# ── ② 문자 후보 탐지 ──────────────────────────────────────
# 슬레이트·표지판은 「고대비 + 규칙적 엣지」로 나타난다.
# 이 특성을 점수화해 상위 구간만 추린다.

def text_score(path):
    from PIL import Image
    import numpy as np
    im = Image.open(path).convert("L")
    a = np.asarray(im, dtype=float)
    if a.size == 0:
        return 0.0
    # 국소 대비 — 인접 화소 차이의 절대값
    gx = np.abs(np.diff(a, axis=1)).mean()
    gy = np.abs(np.diff(a, axis=0)).mean()
    edge = (gx + gy) / 2
    # 명암 분리도 — 문자는 밝은 배경에 어두운 획(또는 반대)
    hi = (a > a.mean() + a.std()).mean()
    lo = (a < a.mean() - a.std()).mean()
    sep = min(hi, lo) * 2
    # 밝기 극단은 감점 (암전·백화 구간 배제)
    m = a.mean()
    penal = 1.0 if 30 < m < 225 else 0.25
    return round(edge * (0.5 + sep) * penal, 2)


def cmd_textscan(a):
    d = probe(a.video)["duration"]
    os.makedirs(a.out, exist_ok=True)
    tmp = os.path.join(a.out, "_scan")
    os.makedirs(tmp, exist_ok=True)

    # 촘촘히 훑는다 — 슬레이트는 몇 초만 노출된다
    step = max(1, d // a.samples)
    scored = []
    for t in range(2, d, step):
        p = os.path.join(tmp, f"s{t}.jpg")
        if grab(a.video, t, p, scale=420):
            scored.append((text_score(p), t, p))
    scored.sort(reverse=True)

    top = scored[:a.top]
    print(f"문자 후보 상위 {len(top)}개 지점\n")
    print(f"  {'점수':>7}  {'시각':>7}   비고")
    for s, t, _ in top:
        hint = "슬레이트 가능" if s > 18 else "표지·간판 가능" if s > 12 else ""
        print(f"  {s:>7.1f}  {sec_label(t):>7}   {hint}")

    g = make_grid([(t, p) for _, t, p in top],
                  os.path.join(a.out, "_textscan.jpg"), cols=4)
    print(f"\n후보 그리드: {g}")
    print("\n다음: 판독할 지점을 골라 zoom 을 쓰십시오.")
    print(f"      예) python {os.path.basename(__file__)} zoom {a.video} "
          f"--at {top[0][1] if top else 0} --out {a.out}")

    json.dump([{"t": t, "score": s} for s, t, _ in top],
              open(os.path.join(a.out, "textscan.json"), "w"), indent=1)
    return top


# ── ③ 고배율 판독 ─────────────────────────────────────────
# 같은 지점을 여러 파라미터로 뽑아 가장 선명한 것을 고른다.
# 필름 자료는 프레임마다 흔들림·초점이 달라 한 장만으로는 판독이 안 된다.

def cmd_zoom(a):
    os.makedirs(a.out, exist_ok=True)
    crop = tuple(float(v) for v in a.crop.split(",")) if a.crop else None
    cands = []
    for off in (-2, -1, 0, 1, 2):
        for eq in (1.0, 1.25, 1.45):
            t = max(0, a.at + off)
            p = os.path.join(a.out, f"z{int(t)}_{eq}.jpg")
            if grab(a.video, t, p, scale=a.scale, crop=crop, eq=eq, sharp=True):
                cands.append((text_score(p), t, eq, p))
    if not cands:
        print("추출 실패", file=sys.stderr); sys.exit(1)
    cands.sort(reverse=True)
    best = cands[0]
    out = os.path.join(a.out, f"read_{int(a.at)}.jpg")
    os.replace(best[3], out)
    # 나머지 후보 정리
    for _, _, _, p in cands[1:]:
        if os.path.exists(p):
            os.remove(p)
    print(f"판독용 프레임: {out}")
    print(f"  선택 조건: {sec_label(best[1])} · 대비 {best[2]} · 점수 {best[0]}")
    print()
    print("이 이미지를 직접 보고 판독하십시오.")
    print("판독이 안 되면 --crop 으로 영역을 좁히거나 --scale 을 높이십시오.")
    return out


# ── ④ 장면 전환 탐지 ──────────────────────────────────────
# 한 릴에 여러 주제가 편집된 경우가 많다.
# 표제의 「ETC」나 세미콜론 뒤가 여기서 드러난다.

def cmd_scenes(a):
    from PIL import Image
    import numpy as np
    d = probe(a.video)["duration"]
    os.makedirs(a.out, exist_ok=True)
    tmp = os.path.join(a.out, "_sc")
    os.makedirs(tmp, exist_ok=True)

    step = max(1, d // a.samples)
    prev, cuts = None, []
    for t in range(1, d, step):
        p = os.path.join(tmp, f"c{t}.jpg")
        if not grab(a.video, t, p, scale=160):
            continue
        cur = np.asarray(Image.open(p).convert("L").resize((64, 64)), dtype=float)
        if prev is not None:
            diff = np.abs(cur - prev).mean()
            cuts.append((diff, t, p))
        prev = cur

    if not cuts:
        print("전환 탐지 실패"); return []
    vals = [c[0] for c in cuts]
    thr = np.mean(vals) + 1.2 * np.std(vals)
    marks = [(dv, t, p) for dv, t, p in cuts if dv > thr]

    print(f"장면 전환 후보 {len(marks)}개 (임계 {thr:.1f})\n")
    for dv, t, _ in marks:
        print(f"  {sec_label(t):>7}   차이 {dv:.1f}")

    if marks:
        g = make_grid([(t, p) for _, t, p in marks],
                      os.path.join(a.out, "_scenes.jpg"), cols=4)
        print(f"\n전환 지점 그리드: {g}")
        print("\n⚠ 표제에 「ETC」나 세미콜론이 있다면,")
        print("  전환 지점 이후가 원 기술에 없는 내용일 수 있습니다.")
    json.dump([{"t": t, "diff": round(dv, 1)} for dv, t, _ in marks],
              open(os.path.join(a.out, "scenes.json"), "w"), indent=1)
    return marks


# ── ⑤ 자동 ───────────────────────────────────────────────

def cmd_auto(a):
    print("=" * 62); print("  ① 전 구간 개관"); print("=" * 62)
    info = cmd_survey(a)
    print("\n" + "=" * 62); print("  ② 문자 후보 탐지"); print("=" * 62)
    top = cmd_textscan(a)
    print("\n" + "=" * 62); print("  ③ 장면 전환 탐지"); print("=" * 62)
    marks = cmd_scenes(a)

    rep = dict(video=os.path.basename(a.video), duration=info["duration"],
               sound="유성" if info["has_audio"] else "무성",
               size=info["size"],
               text_candidates=[{"t": t, "score": s} for s, t, _ in top],
               scene_cuts=[{"t": t, "diff": round(dv, 1)} for dv, t, _ in marks])
    jp = os.path.join(a.out, "analysis.json")
    json.dump(rep, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("\n" + "=" * 62)
    print("  다음 할 일")
    print("=" * 62)
    print(f"  · _survey.jpg 로 전체를 훑으십시오")
    print(f"  · _textscan.jpg 에서 판독할 지점을 고르십시오")
    if marks:
        print(f"  · 전환 {len(marks)}곳 — 표제에 없는 내용이 있는지 확인하십시오")
    print(f"  · 분석 요약: {jp}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("survey", "textscan", "zoom", "scenes", "auto"):
        p = sub.add_parser(name)
        p.add_argument("video")
        p.add_argument("--out", required=True)
        p.add_argument("--n", type=int, default=12)
        p.add_argument("--cols", type=int, default=4)
        p.add_argument("--samples", type=int, default=60)
        p.add_argument("--top", type=int, default=8)
        p.add_argument("--at", type=float, default=0)
        p.add_argument("--crop")
        p.add_argument("--scale", type=int, default=1050)
    a = ap.parse_args()
    dict(survey=cmd_survey, textscan=cmd_textscan, zoom=cmd_zoom,
         scenes=cmd_scenes, auto=cmd_auto)[a.cmd](a)


if __name__ == "__main__":
    main()
