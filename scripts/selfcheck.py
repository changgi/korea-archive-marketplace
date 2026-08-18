#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selfcheck.py — 접근 경로 회귀 점검기

이 전집의 스킬 문서는 **2026-08-18 실측**을 기준으로 쓰였다.
기관 사이트가 개편되면 문서가 조용히 낡는다 — 그리고 그것을 알아채는 것은
보통 한창 조사 중일 때다.

이 스크립트는 문서에 적힌 접근 경로가 지금도 유효한지 한 번에 확인한다.

    python selfcheck.py              # 전체
    python selfcheck.py --quick      # 이미지 다운로드 생략(빠름)
    python selfcheck.py --json

설계 원칙은 이 전집의 다른 도구와 같다 — **판정한다.**
"실패 3건"이 아니라 "규장각 목록 파서가 깨졌다. SKILL.md 3-1절을 고쳐라"라고 말한다.

표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
DELAY = 0.5


def post(url: str, form: dict, referer: str | None = None, timeout: int = 45) -> str:
    body = urllib.parse.urlencode(form, encoding="utf-8").encode()
    req = urllib.request.Request(url, data=body, headers={
        "User-Agent": UA, "Referer": referer or url,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read().decode("utf-8", "replace")


def get_bytes(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Referer": "https://kyudb.snu.ac.kr/pf01/rendererImg.do"})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read()


# ---------------------------------------------------------------------------
# 점검 항목 — 각 항목은 (이름, 실행함수, 고칠 곳) 세 쌍이다.
# "고칠 곳"이 있어야 실패가 작업 지시가 된다.
# ---------------------------------------------------------------------------

KHDB = "https://db.history.go.kr"
KYU = "https://kyudb.snu.ac.kr"


def c_khdb_distribution():
    """한국사DB 분포 파싱 — 좌측 메뉴의 DB별 건수"""
    html = post(f"{KHDB}/joseon/search/searchResultList.do",
                {"searchItemId": "bb", "totalWord": "舟橋", "chinessChar": "on"})
    rows = re.findall(
        r"fnGoSearchResultItem\('([a-z0-9_]+)'\);\s*return false;\">\s*([^<(]+?)\s*\((\d[\d,]*)\)",
        html)
    if len(rows) < 3:
        return False, f"분포 항목 {len(rows)}건 — 3건 미만이면 패턴 변경", None
    names = " · ".join(f"{n.strip()} {c}" for _, n, c in rows[:4])
    return True, names, None


def c_khdb_items():
    """한국사DB 항목 파싱 — levelId 링크"""
    html = post(f"{KHDB}/joseon/search/searchResultList.do",
                {"searchItemId": "bb", "totalWord": "添載", "chinessChar": "on"})
    ids = re.findall(r"fnGoItemLevel\('([^']+)',\s*'([^']+)'", html)
    if not ids:
        return False, "항목 0건 — fnGoItemLevel 패턴이 바뀌었다", None
    return True, f"{len(ids)}건 · 예: {ids[0][1]}", None


def c_khdb_law():
    """법령DB — searchItemId=jlaw (초판의 /search/law/ 경로는 404였다)"""
    html = post(f"{KHDB}/joseon/search/searchResultList.do",
                {"searchItemId": "jlaw", "totalWord": "舟橋", "chinessChar": "on"})
    ids = re.findall(r"fnGoItemLevel\('jlaw',\s*'([^']+)'", html)
    if not ids:
        return False, "법령 항목 0건", None
    return True, f"{len(ids)}건 · 예: {ids[0]}", None


def c_khdb_citation():
    """인용 URL 형식 — db.history.go.kr/id/<levelId>"""
    html = post(f"{KHDB}/joseon/search/searchResultList.do",
                {"searchItemId": "bb", "totalWord": "添載", "chinessChar": "on"})
    ids = re.findall(r"fnGoItemLevel\('bb',\s*'([^']+)'", html)
    if not ids:
        return False, "levelId를 얻지 못해 확인 불가", None
    url = f"{KHDB}/id/{ids[0]}"
    try:
        body = get_bytes(url, timeout=40)
    except Exception as e:
        return False, f"{url} — {repr(e)[:60]}", None
    if len(body) < 2000:
        return False, f"응답 {len(body)}바이트 — 비공개 범위이거나 형식 변경", None
    return True, f"{url} ({len(body):,}B)", None


def c_kyu_search():
    """규장각 목록 검색 파서"""
    html = post(f"{KYU}/search/search.do",
                {"totalSearchString": "各船圖本", "searchArea": "10"})
    blocks = html.split('<div class="schli"')[1:]
    codes = re.findall(r"fn_totalSearchResultView\('[^']*','[^']*','[^']*',\s*'([^']+)'", html)
    if not blocks or not codes:
        return False, "결과 블록 0건 — schli / fn_totalSearchResultView 패턴 변경", None
    imgs = html.count("fn_originalImg(")
    return True, f"{len(blocks)}건 · 원문 {imgs}건 · 예: {codes[0]}", None


def c_kyu_haeje():
    """규장각 해제 검색 (searchArea=20)"""
    html = post(f"{KYU}/search/search.do",
                {"totalSearchString": "均役廳事目", "searchArea": "20"})
    blocks = html.split('<div class="schli"')[1:]
    if not blocks:
        return False, "해제 결과 0건 — searchArea=20 동작 확인 필요", None
    return True, f"{len(blocks)}건", None


def c_kyu_resolve():
    """규장각 item_cd 해석 — 렌더러 응답의 저장 경로"""
    html = post(f"{KYU}/pf01/rendererImg.do",
                {"item_cd": "item_cd", "book_cd": "GK15752_00",
                 "vol_no": "", "page_no": "", "imgFileNm": "",
                 "tbl_conts_seq": "", "mokNm": "", "add_page_no": ""},
                referer=f"{KYU}/search/search.do")
    m = re.search(r"/data\d+/stream/([A-Z]+)/IMG/", html)
    if not m:
        return False, "저장 경로 미검출 — 리터럴 'item_cd' 역산이 막혔을 수 있다", None
    if m.group(1) != "ART":
        return True, f"item_cd={m.group(1)} (문서는 ART로 기록 — 확인 필요)", None
    return True, f"item_cd={m.group(1)}", None


def c_kyu_pagelist():
    """규장각 면 목록 JSON — 파일명 조립 불가의 유일한 해법"""
    txt = post(f"{KYU}/pf01/viewImgList.do",
               {"item_cd": "ART", "book_cd": "GK15752_00",
                "vol_no": "0001", "page_no": ""},
               referer=f"{KYU}/pf01/rendererImg.do")
    try:
        lst = json.loads(txt).get("list", [])
    except json.JSONDecodeError:
        return False, "JSON 파싱 실패 — 응답 형식 변경", None
    if not lst:
        return False, "면 목록 0건", None
    return True, f"{len(lst)}면 · 첫 파일 {lst[0]['FILE_NM']}", None


def c_kyu_download():
    """규장각 실제 다운로드 — path는 파일 전체 경로여야 한다"""
    txt = post(f"{KYU}/pf01/viewImgList.do",
               {"item_cd": "ART", "book_cd": "GK15752_00",
                "vol_no": "0001", "page_no": ""},
               referer=f"{KYU}/pf01/rendererImg.do")
    lst = json.loads(txt).get("list", [])
    if not lst:
        return False, "면 목록을 얻지 못해 확인 불가", None
    fn = lst[1]["FILE_NM"] if len(lst) > 1 else lst[0]["FILE_NM"]
    full = f"/data01/stream/ART/IMG/GK15752_00/GK15752_00_0001/{fn}"
    url = (f"{KYU}/ImageServlet.do?imgFileNm={urllib.parse.quote(fn)}"
           f"&path={urllib.parse.quote(full)}")
    raw = get_bytes(url)
    if raw[:3] != b"\xff\xd8\xff":
        return False, (f"JPEG이 아니다 ({len(raw)}바이트). "
                       "path가 디렉터리로 처리되면 200 OK·0바이트가 된다"), None
    # 해상도
    i, size = 2, None
    while i < len(raw) - 9:
        if raw[i] != 0xFF:
            i += 1
            continue
        m = raw[i + 1]
        if m in range(0xC0, 0xCF) and m not in (0xC4, 0xC8, 0xCC):
            import struct
            h, w = struct.unpack(">HH", raw[i + 5:i + 9])
            size = (w, h)
            break
        import struct
        i += 2 + struct.unpack(">H", raw[i + 2:i + 4])[0]
    return True, f"{fn} · {size[0]}×{size[1]} · {len(raw):,}B" if size else f"{len(raw):,}B", None


CHECKS = [
    ("한국사DB 분포 파싱", c_khdb_distribution,
     "joseon-source-excavation/references/endpoints.md §1-2"),
    ("한국사DB 항목 파싱", c_khdb_items,
     "joseon-source-excavation/references/endpoints.md §1-2"),
    ("한국사DB 법령(jlaw)", c_khdb_law,
     "joseon-source-excavation/references/endpoints.md §1-2 · mcp/tools/joseon.ts"),
    ("한국사DB 인용 URL", c_khdb_citation,
     "joseon-source-excavation/references/endpoints.md §1-3"),
    ("규장각 목록 검색", c_kyu_search,
     "kyujanggak-images/references/pipeline.md ① · mcp/tools/kyujanggak_tools.py kyu_search"),
    ("규장각 해제 검색", c_kyu_haeje,
     "kyujanggak-images/references/pipeline.md ①"),
    ("규장각 item_cd 해석", c_kyu_resolve,
     "kyujanggak-images/references/pipeline.md ② · kyu_resolve"),
    ("규장각 면 목록", c_kyu_pagelist,
     "kyujanggak-images/references/pipeline.md ③ · kyu_pagelist"),
    ("규장각 실제 다운로드", c_kyu_download,
     "kyujanggak-images/references/pipeline.md ④ · kyu_image_url"),
]

QUICK_SKIP = {"규장각 실제 다운로드"}


def main() -> int:
    ap = argparse.ArgumentParser(description="접근 경로 회귀 점검기")
    ap.add_argument("--quick", action="store_true", help="이미지 다운로드 생략")
    ap.add_argument("--json", dest="as_json", action="store_true")
    a = ap.parse_args()

    print("=" * 72)
    print("  접근 경로 회귀 점검  |  기준: 2026-08-18 실측")
    print("=" * 72 + "\n")

    results = []
    for name, fn, where in CHECKS:
        if a.quick and name in QUICK_SKIP:
            print(f"  ·  {name:<22} 생략 (--quick)")
            continue
        t0 = time.time()
        try:
            ok, detail, _ = fn()
        except Exception as e:
            ok, detail = False, f"예외: {repr(e)[:90]}"
        dt = time.time() - t0
        mark = "OK " if ok else "✕  "
        print(f"  {mark}{name:<22} {detail}   ({dt:.1f}s)")
        if not ok:
            print(f"      → 고칠 곳: {where}")
        results.append({"check": name, "ok": ok, "detail": detail, "fix": where})
        time.sleep(DELAY)

    n_bad = sum(1 for r in results if not r["ok"])
    print("\n" + "-" * 72)
    if n_bad == 0:
        print(f"  {len(results)}항목 전부 통과 — 문서의 접근 경로가 지금도 유효하다.")
    else:
        print(f"  {len(results)}항목 중 {n_bad}건 실패.")
        print("\n  실패가 곧 사이트 개편은 아니다. 순서대로 배제할 것:")
        print("    ① 네트워크·방화벽 (다른 항목도 함께 실패했는가)")
        print("    ② 일시 장애 (몇 분 뒤 재시도)")
        print("    ③ 마크업 변경 (위 '고칠 곳'의 패턴표를 갱신)")
        print("\n  ※ 특히 '규장각 실제 다운로드'만 실패하면 path 파라미터 문제다.")
        print("     200 OK에 0바이트가 돌아오는 조용한 실패이므로 예외로는 안 잡힌다.")
    print("-" * 72)

    if a.as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if n_bad else 0


if __name__ == "__main__":
    sys.exit(main())
