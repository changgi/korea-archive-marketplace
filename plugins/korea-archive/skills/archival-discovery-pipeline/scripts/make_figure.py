#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
논문용 산출물 생성기 — 도판 패널 · 통계 도표 · 인용 형식

사용법
    python make_figure.py panel <사양.json> --out fig.png
    python make_figure.py stats <데이터.json> --out fig.png
    python make_figure.py cite  <메타.json>

도판은 예쁜 사진이 아니라 논거다.
무엇을 보여야 하는지 먼저 정하고 프레임을 고른다.
"""
import argparse, json, os, sys
from matplotlib import font_manager as fm

_f = fm.findSystemFonts()
FB = [x for x in _f if "NotoSansCJK" in x and "Bold" in x][0]
FR = [x for x in _f if "NotoSansCJK" in x and "Regular" in x][0]
INK = (20, 30, 60); SUB = (95, 110, 135); EDGE = (175, 186, 202)


# ── 도판 패널 ─────────────────────────────────────────────

def panel(spec, out, height=370, gap=20):
    """
    사양:
      {"items":[{"img":"a.jpg","title":"슬레이트 (0:12)","note":"DATE 4/30/48"}, ...]}
    """
    from PIL import Image, ImageDraw, ImageFont
    items = spec["items"]
    T = ImageFont.truetype(FB, 24)
    N = ImageFont.truetype(FR, 19)

    ims = []
    for it in items:
        if not os.path.exists(it["img"]):
            print(f"파일 없음: {it['img']}", file=sys.stderr); sys.exit(1)
        im = Image.open(it["img"]).convert("RGB")
        ims.append(im.resize((int(im.width * height / im.height), height), Image.LANCZOS))

    W = sum(i.width for i in ims) + gap * (len(ims) - 1) + gap * 2
    H = height + gap * 2 + 64
    c = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(c)
    x = gap
    for im, it in zip(ims, items):
        c.paste(im, (x, gap))
        d.rectangle([x, gap, x + im.width, gap + height], outline=EDGE, width=1)
        cx = x + im.width // 2
        d.text((cx, height + gap + 12), it["title"], font=T, fill=INK, anchor="ma")
        if it.get("note"):
            d.text((cx, height + gap + 42), it["note"], font=N, fill=SUB, anchor="ma")
        x += im.width + gap
    c.save(out, quality=92)
    print(f"도판 패널: {out}  ({c.width}×{c.height})")
    print()
    print("캡션에 반드시 담을 것:")
    print("  ① 식별자와 확정된 날짜·장소")
    print("  ② 무엇이 보이는가")
    print("  ③ 무엇을 판정하지 않았는가")
    print("  ④ 게재 제한을 적용했다면 그 사실")
    return out


# ── 통계 도표 ─────────────────────────────────────────────

def stats(data, out):
    """
    데이터:
      {"연도별":{"1945":7,...}, "계열별":{"의전":11,...},
       "확정유형":{"슬레이트":10,...}, "게재판정":{"게재 가능":49,...}}
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FRp = fm.FontProperties(fname=FR); FBp = fm.FontProperties(fname=FB)

    panels = [(k, v) for k, v in data.items() if isinstance(v, dict) and v]
    if not panels:
        print("표시할 데이터가 없습니다.", file=sys.stderr); sys.exit(1)
    n = len(panels)
    rows = (n + 1) // 2
    fig = plt.figure(figsize=(13, 4.3 * rows), dpi=140)
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(rows, 2, hspace=.42, wspace=.28)

    PAL = ["#2E5395", "#4A7BC8", "#F7B731", "#7BC47F", "#FF6B9D"]
    for i, (title, vals) in enumerate(panels):
        ax = fig.add_subplot(gs[i // 2, i % 2])
        ks = list(vals.keys()); vs = [vals[k] for k in ks]
        horiz = len(ks) > 5 or max((len(str(k)) for k in ks), default=0) > 6
        col = PAL[i % len(PAL)]
        if horiz:
            ax.barh(range(len(ks))[::-1], vs, color=col)
            ax.set_yticks(range(len(ks))[::-1])
            ax.set_yticklabels(ks, fontproperties=FRp, fontsize=10)
            for j, v in enumerate(vs):
                ax.text(v + max(vs) * .015, len(ks) - 1 - j, str(v), va="center",
                        fontproperties=FBp, fontsize=10, color="#17365D")
            ax.set_xlim(0, max(vs) * 1.18)
        else:
            ax.bar(range(len(ks)), vs, color=col)
            ax.set_xticks(range(len(ks)))
            for j, v in enumerate(vs):
                ax.text(j, v + max(vs) * .02, str(v), ha="center",
                        fontproperties=FBp, fontsize=11, color="#17365D")
            ax.set_xticklabels(ks, fontproperties=FRp, fontsize=10)
        ax.set_title(title, fontproperties=FBp, fontsize=14, color="#17365D", pad=10)
        ax.spines[["top", "right"]].set_visible(False)

    plt.savefig(out, bbox_inches="tight", facecolor="white")
    print(f"통계 도표: {out}  (패널 {n}개)")
    return out


# ── 인용 형식 ─────────────────────────────────────────────

def cite(meta):
    """
    메타:
      {"title":"...","date":"1948","rg":"RG 111-ADC","id":"111-ADC-7115",
       "naid":"20887","repo":"National Archives...","url":"...","accessed":"2026-08-11",
       "correction":"카탈로그는 ... 슬레이트에 ... 판독된다."}
    """
    m = meta
    parts = [f'"{m["title"]}," {m.get("date","n.d.")}']
    if m.get("rg"):
        parts.append(m["rg"])
    parts.append(m["id"])
    if m.get("naid"):
        parts.append(f'NAID {m["naid"]}')
    parts.append(m.get("repo", "National Archives and Records Administration, College Park, MD"))
    line = ", ".join(parts) + "."
    print("■ 인용 형식\n")
    print(f"  {line}")
    if m.get("url"):
        print(f'  재공개: {m["url"]} (조회 {m.get("accessed","")}).')
    if m.get("correction"):
        print("\n■ 정정 각주\n")
        print(f'  각주) {m["correction"]}')
    print("\n■ 확인 사항")
    print("  · 조회 일자를 반드시 명기하십시오 — 재공개 상태는 변합니다")
    print("  · 원 기술과 다른 사실을 밝혔다면 근거를 각주로 남기십시오")
    return line


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("panel"); p1.add_argument("spec"); p1.add_argument("--out", required=True)
    p1.add_argument("--height", type=int, default=370)
    p2 = sub.add_parser("stats"); p2.add_argument("data"); p2.add_argument("--out", required=True)
    p3 = sub.add_parser("cite"); p3.add_argument("meta")
    a = ap.parse_args()

    d = json.load(open(getattr(a, "spec", None) or getattr(a, "data", None)
                       or a.meta, encoding="utf-8"))
    if a.cmd == "panel":
        panel(d, a.out, height=a.height)
    elif a.cmd == "stats":
        stats(d, a.out)
    else:
        cite(d)


if __name__ == "__main__":
    main()
