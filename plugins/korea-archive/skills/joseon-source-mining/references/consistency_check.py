#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
산출물 정합 점검기 (consistency_check.py)

긴 조사·보고 작업을 여러 회차에 걸쳐 키울 때, 새 발견이 뒤에서 늘어나는 동안
앞 지면·부속 산출물이 그대로 남는 문제를 잡기 위한 도구.

한강 강배 기록 발굴 조사(2026-08-18)에서 정합이 여덟 차례 깨졌고,
그때마다 '확인했다'고 적었으나 실제로 대조하지 않은 것이 원인이었다.
그래서 확인을 사람 판단이 아니라 키워드 대조로 바꾼다.

사용법
  python3 consistency_check.py                 # 기본 프로파일로 점검
  python3 consistency_check.py --add 執籌 1731  # 키워드 추가 점검

원리
  ① 보고서 본문에서 '핵심 어휘'를 정하고
  ② 각 부속 산출물에 그 어휘가 실제로 들어 있는지 전문 검색하고
  ③ 빠진 곳을 표로 출력한다.
  판단하지 않는다. 있는지 없는지만 본다.
"""
import os, sys, re, glob, zipfile, io

BASE = "/mnt/user-data/outputs"

# ── 점검 대상: (표시명, 경로 또는 glob) ────────────────────────────
TARGETS = [
    ("보고서 본문",   "hanriver_boats_records_1485_1986.html"),
    ("발표자료",      "hanriver_boats_briefing.pptx"),
    ("캡션(SNS)",     "caption.txt"),
    ("온톨로지 노드", "karda_nodes.csv"),
    ("전거대장",      "sources.txt"),
    ("매니페스트",    "manifest.txt"),
    ("교안",          "교안_지워진기록을읽는법.html"),
    ("근거대조표",    "규제의유예_근거대조표.html"),
    ("카드뉴스",      "hanriver_carousel_8cards.html"),
    ("포스터",        "hanriver_posters_5.html"),
    ("입문카드",      "hanriver_intro_6cards.html"),
    ("메시지카드",    "hanriver_message_8cards.html"),
    ("기록해설",      "hanriver_annotate_5.html"),
    ("유예카드",      "hanriver_deferral_6cards.html"),
]

# ── 보고서 내부 구역: (표시명, 시작 문자열, 끝 문자열) ─────────────
SECTIONS = [
    ("Ⅰ 요약박스",  "이 보고서가 도달한 곳", "</div>"),
    ("Ⅶ 정책활용",  "정책·자문 활용 설계",   "전시 기획"),
    ("Ⅷ 전시기획",  "ZONE 0",               "도슨트 대본"),
    ("Ⅸ 도슨트",    "도슨트 대본",           "실행 체크리스트"),
    ("Ⅹ 체크리스트","실행 체크리스트",       "후속 조사"),
]

# ── 기본 프로파일: 이 조사의 핵심 어휘 ─────────────────────────────
PROFILE = {
    "1767 형량표":  ["1767", "금고"],
    "규제의 유예":  ["유예"],
    "執籌 배정":    ["執籌"],
    "1731 선행":    ["1731"],
    "量船尺":       ["量船尺", "把"],
    "八江":         ["八江"],
    "배다리 시공":  ["시공", "牽馬鐵"],
    "戰漕船 통용":  ["戰船"],
    "1882 혁파":    ["1882"],
    "묵말(墨抹)":   ["墨抹", "묵말"],
}


def read_any(path):
    """텍스트·HTML·CSV는 그대로, pptx는 XML에서 문자열 추출."""
    p = os.path.join(BASE, path)
    if not os.path.exists(p):
        return None
    if p.endswith(".pptx"):
        buf = []
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                if n.startswith("ppt/slides/slide") and n.endswith(".xml"):
                    x = z.read(n).decode("utf-8", "replace")
                    buf.append(re.sub(r"<[^>]+>", " ", x))
                if n.startswith("ppt/notesSlides/") and n.endswith(".xml"):
                    x = z.read(n).decode("utf-8", "replace")
                    buf.append(re.sub(r"<[^>]+>", " ", x))
        return " ".join(buf)
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return open(p, encoding=enc).read()
        except Exception:
            continue
    return ""


def slice_section(html, start, end):
    i = html.find(start)
    if i < 0:
        return ""
    j = html.find(end, i + len(start))
    return html[i:j] if j > i else html[i:i + 30000]


def hit(text, keys):
    """키워드 중 하나라도 있으면 True."""
    return any(k in text for k in keys)


def main():
    extra = []
    if "--add" in sys.argv:
        extra = sys.argv[sys.argv.index("--add") + 1:]
    profile = dict(PROFILE)
    for k in extra:
        profile[f"(추가) {k}"] = [k]

    print("=" * 78)
    print("산출물 정합 점검  ·  " + BASE)
    print("=" * 78)

    # 1) 산출물별 점검
    cache = {}
    print("\n[1] 산출물별 핵심 어휘 수록 여부\n")
    header = "산출물".ljust(14) + "".join(n[:9].ljust(11) for n in profile)
    print(header)
    print("-" * len(header))
    missing = []
    for name, path in TARGETS:
        t = read_any(path)
        if t is None:
            print(name.ljust(14) + "  ✗ 파일 없음: " + path)
            continue
        cache[name] = t
        row = name.ljust(14)
        for label, keys in profile.items():
            ok = hit(t, keys)
            row += ("O" if ok else "·").ljust(11)
            if not ok:
                missing.append((name, label))
        print(row)

    # 2) 보고서 내부 구역 점검
    rep = cache.get("보고서 본문", "")
    if rep:
        print("\n[2] 보고서 내부 구역별 수록 여부\n")
        print(header.replace("산출물", "구역  "))
        print("-" * len(header))
        for sname, s, e in SECTIONS:
            seg = slice_section(rep, s, e)
            if not seg:
                print(sname.ljust(14) + "  ✗ 구역 미검출")
                continue
            row = sname.ljust(14)
            for label, keys in profile.items():
                ok = hit(seg, keys)
                row += ("O" if ok else "·").ljust(11)
                if not ok:
                    missing.append((f"보고서/{sname}", label))
            print(row)

    # 3) 수치 정합 (같은 수치가 여러 곳에 흩어질 때)
    print("\n[3] 수치 표기 대조\n")
    NUM = {
        "자기 정정 횟수": r"(세|네|다섯|여섯) 차례 (?:스스로를 )?자기? ?정정|자기 정정을? 거[쳤친]",
        "Ⅻ절 항목수":    r"Ⅻ절[^0-9]{0,12}(\d+)\s*항목",
        "온톨로지 노드":  r"노드\s*(\d+)",
        "전파물 장수":    r"전파물\s*\*{0,2}(\d+)장",
        "발표자료 장수":  r"발표자료\s*\*{0,2}(\d+)장",
    }
    for label, pat in NUM.items():
        found = {}
        for name, t in cache.items():
            v = set(m.group(0)[:24] for m in re.finditer(pat, t))
            if v:
                found[name] = v
        if not found:
            continue
        vals = set()
        for v in found.values():
            vals |= v
        # 이력 표기(→ · 확장 · 초판 등)가 있는 파일은 여러 값이 정상이다
        HIST = ("매니페스트", "작업로그", "전거대장")
        real = {k: v for k, v in found.items() if k not in HIST}
        rvals = set()
        for v in real.values():
            rvals |= v
        flag = "  ⚠ 표기 불일치" if len(rvals) > 1 else ""
        if len(vals) > 1 and not flag:
            flag = "  (이력 표기 파일에만 복수값 — 정상)"
        print(f"  {label}{flag}")
        for name, v in found.items():
            print(f"    · {name}: {' / '.join(sorted(v))[:70]}")

    # 4) 결과
    print("\n" + "=" * 78)
    if missing:
        print(f"미수록 {len(missing)}건\n")
        by = {}
        for n, l in missing:
            by.setdefault(n, []).append(l)
        for n, ls in by.items():
            print(f"  {n}: {', '.join(ls)}")
        print("\n※ 미수록이 곧 오류는 아니다. 산출물의 성격상 담지 않는 것이 맞을 수 있다.")
        print("   이 표는 '판단하라'는 목록이지 '고쳐라'는 목록이 아니다.")
    else:
        print("전 산출물에 핵심 어휘가 수록되어 있다.")
    print("=" * 78)


if __name__ == "__main__":
    main()
