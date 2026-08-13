#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
산출물 정합 검사

사용법
    python check_consistency.py <산출물 디렉터리>
    python check_consistency.py ./outputs --carousels carousels --promo 홍보글.md

왜 필요한가
    산출물이 늘어나면 수치가 문서마다 갈린다.
    캐러셀을 20건에서 50건으로 늘렸는데 어느 문서는 20건으로 남아 있는 식이다.
    사람 눈으로는 잘 보이지 않고, 대외 발신물에서 이런 어긋남이 나오면 신뢰를 잃는다.

검사를 만들 때
    절반의 노력은 「무엇을 잡지 않을지」에 든다.
    작업 일지의 과거 수치, 금지 표현 목록 자체, base64 안의 우연한 문자열 —
    이런 것들이 오탐으로 잡히면 검사 자체가 무시된다.
"""
import argparse, os, re, sys, glob, zipfile

OK, BAD, WARN = "OK", "!!", "??"
_res = []


def note(lv, msg):
    _res.append((lv, msg))
    print(f"  {lv} {msg}")


def head(t):
    print(f"\n▣ {t}\n" + "─" * 68)


def doc_text(p):
    """문서에서 검사 가능한 텍스트를 뽑는다. base64는 제거."""
    try:
        if p.endswith((".md", ".txt", ".html")):
            t = open(p, encoding="utf-8", errors="ignore").read()
        elif p.endswith(".docx"):
            t = re.sub("<[^>]+>", " ",
                       zipfile.ZipFile(p).read("word/document.xml").decode("utf-8", "ignore"))
        else:
            return ""
    except Exception:
        return ""
    # base64 임베드 이미지는 우연히 NaN·TODO 같은 문자열을 포함한다
    return re.sub(r"data:image/[a-z]+;base64,[A-Za-z0-9+/=]+", "", t)


# ── 1. 캐러셀 실측 대 문서 표기 ──────────────────────────
def check_carousel(root, cdir, logs):
    head("캐러셀 실측 대 문서 표기")
    cpath = os.path.join(root, cdir)
    if not os.path.isdir(cpath):
        note(WARN, f"{cdir} 없음 — 건너뜀"); return
    dirs = [d for d in os.listdir(cpath) if os.path.isdir(os.path.join(cpath, d))]
    pngs = sum(len([f for f in os.listdir(os.path.join(cpath, d)) if f.endswith(".png")])
               for d in dirs)
    note(OK, f"실측 — {len(dirs)}건 · {pngs}장")
    bad = []
    for f in sorted(os.listdir(root)):
        if not f.endswith((".md", ".html")) or f in logs:
            continue
        t = doc_text(os.path.join(root, f))
        for a, b in re.findall(r"(\d+)\s*건\s*[·]\s*(\d+)\s*장", t):
            if (int(a), int(b)) != (len(dirs), pngs):
                bad.append((f, f"{a}건 {b}장"))
    if bad:
        for f, v in sorted(set(bad)):
            note(BAD, f"{f} — {v}로 적혀 있으나 실측은 {len(dirs)}건 {pngs}장")
    else:
        note(OK, "수를 언급한 모든 문서가 실측과 일치")


# ── 2. 대외 발신물의 사실 근거 ───────────────────────────
BANNED = ["최초 공개", "단독 발굴", "충격", "경악", "소름"]


def check_promo(root, promo, sources):
    head("대외 발신물의 사실 근거·금지 표현")
    p = os.path.join(root, promo)
    if not os.path.exists(p):
        note(WARN, f"{promo} 없음 — 건너뜀"); return
    h = doc_text(p)
    src = "".join(doc_text(os.path.join(root, s)) for s in sources
                  if os.path.exists(os.path.join(root, s)))

    # 고유명사·판독 문구가 자료 문서에 있는가
    # 대문자 연속 3자 이상, 한자 2자 이상을 후보로 삼는다
    cands = set(re.findall(r"\b[A-Z][A-Z0-9\s\.\-]{4,30}\b", h))
    cands |= set(re.findall(r"[\u4e00-\u9fff]{2,8}", h))
    cands = {c.strip() for c in cands if len(c.strip()) > 3}
    ungrounded = sorted(c for c in cands if src and c not in src)[:8]
    if ungrounded:
        note(WARN, f"자료 문서에서 확인되지 않은 표기(확인 요): {ungrounded}")
    else:
        note(OK, "고유명사·판독 문구가 모두 자료 문서에 근거")

    # 금지 표현 — 「쓰지 않을 표현」 목록 절은 제외
    cut = re.split(r"절대 쓰지 않을 표현|금지 사항|금지 표현", h)[0]
    used = [b for b in BANNED if b in cut]
    if used:
        note(BAD, f"금지 표현 사용: {used}")
    else:
        note(OK, "금지 표현 없음")

    # 회차마다 「확인하지 못한 것」이 있는가
    posts = len(re.findall(r"^##\s*[①-⑧]-\d", h, re.M)) + \
            len(re.findall(r"^##\s*[Ⓐ-Ⓒ]", h, re.M))
    warns = h.count("⚠️")
    if posts and warns < posts:
        note(BAD, f"회차 {posts}건 중 미확인 표기는 {warns}건에만 있음")
    elif posts:
        note(OK, f"회차 {posts}건 · 미확인 표기 {warns}건 — 누락 없음")


# ── 3. 문서 내부 참조 ────────────────────────────────────
def td_probe(t):
    """이 문서가 표를 자체 정의하는가"""
    return bool(re.findall(r"표\s*\d+\.", t))


def check_refs(root, logs):
    head("문서 내부 참조 (그림·표 번호)")
    for f in sorted(os.listdir(root)):
        if not f.endswith((".md", ".html")) or f in logs:
            continue
        t = doc_text(os.path.join(root, f))
        if "그림" not in t and "표 " not in t:
            continue
        fd = {int(m) for m in re.findall(r"그림\s*(\d+)\.", t)}
        # 본문에 그림을 하나도 싣지 않는 문서(체크리스트·현황·지시서·색인)는
        # 다른 문서의 그림을 언급만 하는 것이므로 대조 대상이 아니다.
        # 판정: 캡션(「그림 N.」)이 없거나, 실제 이미지 태그가 없으면 언급 전용.
        # 「논문_그림20_비교.png」 같은 파일명이 캡션으로 오인되지 않게
        # 앞이 공백이나 줄머리인 경우만 캡션으로 센다.
        fd = {int(m) for m in re.findall(r"(?:^|[\s>])그림\s*(\d+)\.", t, re.M)}
        has_img = bool(re.search(r"<img|!\[", t))
        if not fd and (not td_probe(t) or not has_img):
            note(OK, f"{f} — 도판 미수록 문서 (참조 언급만)")
            continue
        fr = {int(m) for m in re.findall(r"그림\s*(\d+)(?!\.)", t)}
        td = {int(m) for m in re.findall(r"표\s*(\d+)\.", t)}
        tr = {int(m) for m in re.findall(r"표\s*(\d+)(?!\.)", t)}
        miss = sorted(fr - fd) + sorted(tr - td)
        if miss:
            note(BAD, f"{f} — 정의되지 않은 그림·표 참조: {miss}")
        else:
            note(OK, f"{f} — 참조 일치")


# ── 4. 빌드 흔적 ─────────────────────────────────────────
JUNK = ["undefined", "NaN", "[object", "TODO", "DUMMY", "{{"]
JUNK_DOC = ["<b>", "</b>", "<br>", "<span"]


def check_junk(root):
    head("빌드 흔적·미치환 문자열")
    found = []
    for f in sorted(os.listdir(root)):
        p = os.path.join(root, f)
        if not os.path.isfile(p):
            continue
        t = doc_text(p)
        if not t:
            continue
        # HTML의 <script> 블록에는 NaN·undefined가 정상 코드로 등장한다.
        if f.endswith(".html"):
            t = re.sub(r"<script[\s\S]*?</script>", "", t, flags=re.I)
        for k in JUNK:
            if k in t:
                found.append((f, k))
        # 워드 문서에 HTML 태그가 문자로 인쇄되는 사고가 있다.
        # HTML 파일에서는 <b>가 정상 마크업이므로 제외한다.
        if f.endswith((".docx", ".pptx")):
            for k in JUNK_DOC:
                if k in t:
                    found.append((f, k))
    if found:
        for f, k in sorted(set(found)):
            note(BAD, f"{f} — 「{k}」")
    else:
        note(OK, "미치환 문자열 없음")


# ── 5. 게재 제한 대상 보호 ───────────────────────────────
def check_restricted(root, cdir, restricted):
    head("게재 제한 대상 보호")
    if not restricted:
        note(WARN, "제한 목록 미지정 — 건너뜀 (--restricted 로 지정)"); return
    cpath = os.path.join(root, cdir)
    leaked = []
    if os.path.isdir(cpath):
        for r in restricted:
            hits = glob.glob(os.path.join(cpath, f"*{r}*"))
            if hits:
                leaked.append((r, [os.path.basename(h) for h in hits]))
    if leaked:
        for r, h in leaked:
            note(BAD, f"제한 대상 {r} 의 캐러셀이 존재: {h}")
    else:
        note(OK, f"제한 대상 {len(restricted)}건 — 전파물에 포함되지 않음")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="산출물 디렉터리")
    ap.add_argument("--carousels", default="carousels")
    ap.add_argument("--promo", default="홍보글_전문.md")
    ap.add_argument("--sources", nargs="*", default=[],
                    help="사실 근거가 되는 자료 문서들")
    ap.add_argument("--logs", nargs="*", default=[],
                    help="작업 일지 — 과거 수치가 정상이므로 대조 제외")
    ap.add_argument("--restricted", nargs="*", default=[],
                    help="게재 제한 대상 식별자")
    a = ap.parse_args()

    logs = set(a.logs)
    print("=" * 68)
    print("  산출물 정합 검사")
    print("=" * 68)

    check_carousel(a.root, a.carousels, logs)
    check_promo(a.root, a.promo, a.sources)
    check_refs(a.root, logs)
    check_junk(a.root)
    check_restricted(a.root, a.carousels, a.restricted)

    bad = sum(1 for lv, _ in _res if lv == BAD)
    print("\n" + "=" * 68)
    if bad:
        print(f"  [!] 조치가 필요한 항목 {bad}건")
    else:
        print("  [OK] 검사 통과. 남은 것은 사람이 판단할 몫입니다.")
    print("=" * 68)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
