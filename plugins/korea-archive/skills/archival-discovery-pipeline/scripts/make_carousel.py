#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
캐러셀 생성기 — 서사 구조 + 레이아웃 다양성

사용법
    python make_carousel.py <사양.json>
    CAROUSEL_OUT=/path/to/out python make_carousel.py <사양.json>

설계 원리
  · 서사 구조 — 질문에서 시작해 결론으로 닫는다
  · 레이아웃 다양성 — 카드마다 다른 구성
  · 타이포 중심 — 큰 문장이 화면을 지배한다
  · 색 규약 — 금색(제목) 청록(원기술) 분홍(문제) 청색(수치) 녹색(확인)

레이아웃 열 가지
  cover bars quote duo full split alert table rights closing

사양 스키마는 references/carousel_design.md 참조.
"""
import os, json
from PIL import Image, ImageDraw, ImageFont
from matplotlib import font_manager as fm

S = 1080
OUT = os.environ.get("CAROUSEL_OUT", "./carousels")
_f = fm.findSystemFonts()
FB = [x for x in _f if "NotoSansCJK" in x and "Bold" in x][0]
FR = [x for x in _f if "NotoSansCJK" in x and "Regular" in x][0]

NAVY = (16, 20, 38); GOLD = (247, 183, 49); WHITE = (245, 247, 252)
GREY = (150, 162, 186); TEAL = (79, 205, 196); ROSE = (255, 107, 157)
GREEN = (123, 196, 127); BLUE = (99, 155, 235); MONO = (176, 190, 214)
BOX = (28, 34, 58); LINE = (88, 102, 132)

RIGHTS = {
    "A": ("A · 공개 확정", BLUE, "권리 확인 완료"),
    "B": ("B · PD 추정", GREEN, "17 U.S.C. §105 — 미 연방 직무저작물"),
    "C": ("C · 허가 필요", GOLD, "기증 조건·이용 약관 확인 요"),
    "D": ("D · 지위 불명", (255, 107, 107), "36 CFR 1254.62 — 공개 금지"),
}

F = lambda n, b=False: ImageFont.truetype(FB if b else FR, n)


def canvas(idx, total, foot):
    im = Image.new("RGB", (S, S), NAVY)
    g = Image.new("RGB", (S, S)); gd = ImageDraw.Draw(g)
    for y in range(S):
        t = y / S
        gd.line([(0, y), (S, y)], fill=(int(16 + 30 * t), int(20 + 20 * t), int(38 + 28 * t)))
    im = Image.blend(im, g, 0.85)
    d = ImageDraw.Draw(im)
    d.line([(S * 0.98, 0), (S * 0.02, S)], fill=(110, 88, 52), width=3)
    d.text((S - 64, 62), f"{idx:02d} / {total:02d}", font=F(24), fill=GREY, anchor="ra")
    d.text((S // 2, S - 54), foot, font=F(20), fill=(105, 118, 145), anchor="ma")
    return im, d


def wrap(d, txt, font, maxw):
    out, line = [], ""
    for ch in txt:
        if ch == "\n":
            out.append(line); line = ""; continue
        if d.textlength(line + ch, font=font) > maxw:
            out.append(line); line = ch
        else:
            line += ch
    out.append(line)
    return out


def body(d, x, y, txt, size=30, color=WHITE, lh=46, maxw=880, bold=False):
    fnt = F(size, bold)
    for l in wrap(d, txt, fnt, maxw):
        d.text((x, y), l, font=fnt, fill=color); y += lh
    return y


def fit(im, path, box):
    p = Image.open(path).convert("RGB")
    x, y, w, h = box
    r = max(w / p.width, h / p.height)
    p = p.resize((int(p.width * r), int(p.height * r)), Image.LANCZOS)
    l = (p.width - w) // 2; t = (p.height - h) // 2
    im.paste(p.crop((l, t, l + w, t + h)), (x, y))
    ImageDraw.Draw(im).rectangle([x, y, x + w, y + h], outline=(92, 106, 136), width=2)


# ─────────────────────────── 레이아웃 ───────────────────────────

def L_cover(im, d, c):
    d.text((88, 196), c["era"], font=F(27, True), fill=GOLD)
    y = body(d, 88, 268, c["title"], size=70, lh=94, bold=True, maxw=900)
    body(d, 88, y + 26, c["sub"], size=29, color=GREY, lh=45)
    d.line([(88, S - 206), (300, S - 206)], fill=GOLD, width=3)
    body(d, 88, S - 182, c["foot_id"], size=25, color=(120, 134, 162), lh=38)


def L_bars(im, d, c):
    y = body(d, 88, 132, c["head"], size=44, color=GOLD, lh=60, bold=True)
    y += 30
    mx = max(v for _, v, _ in c["rows"]) or 1
    for label, v, note in c["rows"]:
        d.text((88, y), label, font=F(29, True), fill=WHITE)
        d.text((S - 88, y), c.get("unit_fmt", "{}건").format(v), font=F(34, True),
               fill=BLUE if v == mx else WHITE, anchor="ra")
        d.text((88, y + 42), note, font=F(22), fill=GREY)
        bw = int((S - 176) * v / mx)
        d.rounded_rectangle([88, y + 76, 88 + max(bw, 8), y + 92], 8,
                            fill=BLUE if v == mx else (72, 92, 140))
        y += 132
    if c.get("tail"):
        body(d, 88, y + 20, c["tail"], size=34, lh=50, bold=True)


def L_quote(im, d, c):
    body(d, 88, 130, c.get("lead", "미 국립기록청의\n원래 기술은 이렇습니다"), size=29, color=GREY, lh=42)
    bh = c.get("box_h", 170)
    d.rounded_rectangle([88, 250, S - 88, 250 + bh], 14, fill=BOX, outline=LINE, width=2)
    body(d, 118, 282, c["orig"], size=26, color=TEAL, lh=40, maxw=830)
    y = 250 + bh + 54
    y = body(d, 88, y, c["punch"], size=48, lh=66, bold=True)
    body(d, 88, y + 28, c["note"], size=27, color=GREY, lh=42)


def L_duo(im, d, c):
    body(d, 88, 130, c["head"], size=40, color=GOLD, lh=54, bold=True)
    w, h = 430, 340
    for i, (p, cap) in enumerate(c["pair"]):
        x = 88 + i * (w + 44)
        fit(im, p, (x, 236, w, h))
        dd = ImageDraw.Draw(im)
        dd.text((x, 236 + h + 18), cap, font=F(25), fill=GREY)
    d2 = ImageDraw.Draw(im)
    y = body(d2, 88, 668, c["punch"], size=38, lh=54, bold=True)
    body(d2, 88, y + 22, c["note"], size=26, color=GREY, lh=40)


def L_full(im, d, c):
    fit(im, c["img"], (88, 150, S - 176, 520))
    d2 = ImageDraw.Draw(im)
    y = body(d2, 88, 706, c["punch"], size=40, lh=56, bold=True)
    body(d2, 88, y + 22, c["note"], size=26, color=GREY, lh=40)


def L_split(im, d, c):
    fit(im, c["img"], (88, 236, 452, 452))
    d2 = ImageDraw.Draw(im)
    body(d2, 88, 140, c["head"], size=36, color=GOLD, lh=50, bold=True)
    x = 578
    y = 246
    for k, v, sub in c["items"]:
        d2.text((x, y), k, font=F(24), fill=GREY); y += 36
        d2.text((x, y), v, font=F(38, True), fill=tuple(c["vcol"]) if c.get("vcol") else ROSE); y += 54
        y = body(d2, x, y, sub, size=23, color=(160, 172, 196), lh=34, maxw=414)
        y += 26
    body(d2, 88, 740, c["punch"], size=36, lh=52, bold=True)


def L_alert(im, d, c):
    body(d, 88, 140, c.get("lead", "그런데"), size=30, color=ROSE, lh=44)
    y = body(d, 88, 196, c["head"], size=46, lh=64, bold=True)
    y += 30
    bh = c.get("box_h", 168)
    d.rounded_rectangle([88, y, S - 88, y + bh], 12, fill=(46, 26, 34),
                        outline=(158, 62, 78), width=2)
    body(d, 118, y + 26, c["box"], size=27, color=(250, 214, 224), lh=42, maxw=830)
    y += bh + 46
    body(d, 88, y, c["note"], size=27, color=GREY, lh=42)


def L_table(im, d, c):
    body(d, 88, 132, "소장 정보", size=40, color=GOLD, lh=54, bold=True)
    y = 232
    for k, v in c["rows"]:
        d.text((88, y), k, font=F(25), fill=GREY)
        ls = wrap(d, v, F(29, True), 620)
        for i, l in enumerate(ls):
            d.text((338, y + i * 40), l, font=F(29, True), fill=WHITE)
        y += 58 + (len(ls) - 1) * 40
    if c.get("note"):
        d.line([(88, S - 292), (300, S - 292)], fill=LINE, width=2)
        body(d, 88, S - 264, c["note"], size=24, color=GREY, lh=38)


def L_rights(im, d, c):
    body(d, 88, 132, "권리 판정 (초판)", size=40, color=GOLD, lh=54, bold=True)
    label, col, basis = RIGHTS[c["grade"]]
    d.rounded_rectangle([88, 226, 88 + 330, 226 + 76], 38, fill=BOX, outline=col, width=3)
    d.text((88 + 165, 226 + 38), label, font=F(33, True), fill=col, anchor="mm")
    y = body(d, 88, 344, basis, size=28, lh=44)
    y = body(d, 88, y + 26, c["note"], size=26, color=GREY, lh=42)
    if c.get("query"):
        y += 16
        d.text((88, y), "재현 쿼리", font=F(26, True), fill=GOLD); y += 44
        d.rounded_rectangle([88, y, S - 88, y + 58], 10, fill=BOX, outline=LINE, width=2)
        body(d, 112, y + 14, c["query"], size=25, color=MONO, lh=34, maxw=840)
    d.line([(88, S - 172), (300, S - 172)], fill=LINE, width=2)
    body(d, 88, S - 148, "자동 초판 — 출판 전 인간 최종 확인 필수", size=23,
         color=(140, 152, 178), lh=36)


def L_closing(im, d, c):
    y = body(d, 88, 150, c["punch"], size=46, color=GOLD, lh=64, bold=True, maxw=900)
    y += 26
    # 확인된 것 (최대 4줄)
    d.text((88, y), "확인된 것", font=F(26, True), fill=GREEN); y += 42
    for l in c["confirmed"].split("\n")[:4]:
        y = body(d, 88, y, l, size=24, lh=34, maxw=880)
    y += 22
    d.text((88, y), "확인하지 못한 것", font=F(26, True), fill=ROSE); y += 42
    for l in c["unconfirmed"].split("\n")[:4]:
        y = body(d, 88, y, l, size=24, color=(226, 200, 210), lh=34, maxw=880)
    d.line([(88, S - 168), (300, S - 168)], fill=GOLD, width=3)
    body(d, 88, S - 144, c["body"], size=24, color=GREY, lh=36)
    d.text((S - 88, S - 96), "Soli Deo Gloria", font=F(21), fill=(96, 108, 134), anchor="ra")


LAYOUTS = dict(cover=L_cover, bars=L_bars, quote=L_quote, duo=L_duo, full=L_full,
               split=L_split, alert=L_alert, table=L_table, rights=L_rights,
               closing=L_closing)


def make(spec):
    os.makedirs(OUT, exist_ok=True)
    sid = spec["id"]
    dirn = os.path.join(OUT, sid); os.makedirs(dirn, exist_ok=True)
    foot = spec.get("foot", "해방기·전쟁기 영상 발굴 · 2026")
    cards = spec["cards"]
    T = len(cards)
    for i, c in enumerate(cards, 1):
        im, d = canvas(i, T, foot)
        LAYOUTS[c["type"]](im, d, c)
        im.save(f"{dirn}/{sid}_{i:02d}.png")
    return dirn, T


if __name__ == "__main__":
    import sys
    specs = json.load(open(sys.argv[1], encoding="utf-8"))
    for s in (specs if isinstance(specs, list) else [specs]):
        d, t = make(s)
        print(f"생성: {os.path.basename(d)} ({t}장)")
