#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
korea-archive MCP 서버 확장 — 조선 사료 심층 판독 도구

기존 korea-archive 서버(검색 중심)에 '본문 판독과 제도 재구성' 계층을 더한다.
한강 강배 기록 발굴 조사(2026-08-18)에서 실측 검증된 접근 경로를 구현했다.

설계 원칙
  1. 좌목 필터를 서버가 한다 — 클라이언트가 601건 받아 492건 버리게 하지 않는다
  2. 경로 판별을 서버가 한다 — jlaw*는 item/level.do, 나머지는 level.do
  3. 형제 조 스캔을 1급 도구로 둔다 — 가장 자주 놓치는 실수
  4. 부재를 반환값에 담는다 — "0건"이 아니라 "법전 미수록"이라는 판정
  5. 원문 제공 여부를 항상 함께 반환한다 — 인용 가능성 판단에 필수

이 서버의 가치는 데이터가 아니라 판정에 있다.
"601건"이 아니라 "492건이 좌목입니다"를 준다.

의존: 표준 라이브러리만 사용 (urllib, ssl, gzip, re, html)
"""

import urllib.request
import urllib.parse
import ssl
import gzip
import re
import html
import time
from typing import Optional

# ─────────────────────────────────────────────────────────────
# 공통 HTTP
# ─────────────────────────────────────────────────────────────

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE

_HDR = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 Chrome/124"),
    "Referer": "https://db.history.go.kr/",
    "Content-Type": "application/x-www-form-urlencoded",
}

DB = "https://db.history.go.kr"
SJW = "https://sjw.history.go.kr"
SILLOK = "https://sillok.history.go.kr"
KYU = "https://kyudb.snu.ac.kr"

POLITE_DELAY = 0.4          # 요청 간격
RETRY_WAIT = 20             # 실패 시 대기


def _decode(resp) -> str:
    b = resp.read()
    if resp.headers.get("Content-Encoding") == "gzip":
        b = gzip.decompress(b)
    return b.decode("utf-8", "replace")


def _post(url: str, params: dict, timeout: int = 90, retries: int = 2) -> str:
    data = urllib.parse.urlencode(params).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=_HDR)
            return _decode(urllib.request.urlopen(req, timeout=timeout, context=_CTX))
        except Exception:
            if attempt < retries - 1:
                time.sleep(RETRY_WAIT)
    return ""


def _get(url: str, timeout: int = 90, retries: int = 2) -> str:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=_HDR)
            return _decode(urllib.request.urlopen(req, timeout=timeout, context=_CTX))
        except Exception:
            if attempt < retries - 1:
                time.sleep(RETRY_WAIT)
    return ""


def _strip(s: str) -> str:
    s = re.sub(r"(?s)<script.*?</script>", "", s)
    s = re.sub(r"(?s)<style.*?</style>", "", s)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def _lines(s: str) -> list:
    s = re.sub(r"(?s)<script.*?</script>", "", s)
    s = re.sub(r"(?s)<style.*?</style>", "", s)
    return [l.strip() for l in
            html.unescape(re.sub(r"(?s)<[^>]+>", "\n", s)).split("\n") if l.strip()]


def _url_for(level_id: str) -> str:
    """법령과 등록류는 상세 경로가 다르다. 혼동하면 빈 페이지가 온다."""
    path = "/joseon/item/level.do?levelId=" if level_id.startswith("jlaw") \
           else "/joseon/level.do?levelId="
    return DB + path + level_id


def _cite(level_id: str) -> str:
    return f"{DB}/id/{level_id}"


# ─────────────────────────────────────────────────────────────
# 1. joseon_law_search — 법전·편람 조문 검색
# ─────────────────────────────────────────────────────────────

def joseon_law_search(query: str, max_results: int = 50) -> dict:
    """조선 법전·편람 조문 검색.

    법전·편람은 한문 원문이 제공되므로 인용 가능하다(표점은 DB 형태).
    """
    s = _post(DB + "/search/law/searchResultList.do", {
        "searchItemId": "jlaw", "searchTarget": "jlaw",
        "pageIndex": "1", "pageUnit": str(min(max_results, 200)), "pageSize": "1",
        "orderColumn": "levelId", "orderDir": "ASC",
        "synonym": "off", "chinessChar": "on",     # 한자 검색 필수
        "totalWord": query,
        "titleWord": "", "titleConjunction": "AND",
        "contentsWord": "", "contentsConjunction": "AND",
        "creatorWord": "", "creatorConjunction": "AND",
        "startDate": "", "endDate": "",
    })
    if not s:
        return {"error": "요청 실패", "query": query}

    m = re.search(r"총\s*([\d,]+)건", _strip(s))
    total = int(m.group(1).replace(",", "")) if m else 0

    results = []
    for lid, tt, tx in re.findall(
            r"fnGoItemView\('([^']+)',\s*'\d+'\).*?<ul class=\"tit\">(.*?)</ul>"
            r"\s*<p class=\"tx\">(.*?)</p>", s, flags=re.S):
        parts = [re.sub(r"\s+", "", re.sub("<[^>]+>", "", x))
                 for x in re.findall(r"<li>(.*?)</li>", tt, flags=re.S)]
        results.append({
            "level_id": lid,
            "source": parts[0] if parts else "",
            "section": "·".join(parts[1:]) if len(parts) > 1 else "",
            "excerpt": _strip(tx)[:300],
            "url": _cite(lid),
        })

    out = {
        "query": query,
        "total": total,
        "results": results,
        "original_text_available": True,
        "note": ("법전·편람은 한문 원문이 제공되므로 인용 가능합니다. "
                 "단 표점은 DB 제공 형태이며 교감본과 대조되지 않았습니다."),
    }
    if total == 0:
        out["finding"] = (f"'{query}'는 법전에 수록되어 있지 않습니다. "
                          "법전 밖 관행일 가능성을 검토하고, 등록류·일기류를 조회하십시오.")
    return out


# ─────────────────────────────────────────────────────────────
# 2. joseon_record_search — 등록류 검색 + 좌목 필터
# ─────────────────────────────────────────────────────────────

_JWAMOK = re.compile(r"좌목\s*$")


def joseon_record_search(query: str, include_jwamok: bool = False,
                         max_results: int = 100) -> dict:
    """비변사등록 등 등록류 검색.

    座目(회의 참석 관원 명단)을 자동으로 걸러 실질 기사만 반환한다.
    검색 건수를 주제 중요도 지표로 쓰기 전에 반드시 이 도구를 쓸 것.
    """
    s = _post(DB + "/joseon/search/searchResultList.do", {
        "searchItemId": "bb", "searchTarget": "bb",
        "pageIndex": "1", "pageUnit": str(min(max_results, 200)), "pageSize": "1",
        "orderColumn": "levelId", "orderDir": "ASC",
        "synonym": "off", "chinessChar": "on", "totalWord": query,
        "titleWord": "", "contentsWord": "", "creatorWord": "",
        "startDate": "", "endDate": "",
    })
    if not s:
        return {"error": "요청 실패", "query": query}

    mt = re.search(r"총\s*([\d,]+)건", _strip(s))
    reported_total = int(mt.group(1).replace(",", "")) if mt else 0

    seen, rows = set(), []
    # 결과 항목은 fnGoItemLevel('bb', '<levelId>', '0') 형태로 링크된다
    pat = re.compile(
        r"fnGoItemLevel\('[^']*',\s*'([\w]+)'[^)]*\);[^>]*>(.*?)</a>"
        r"(?:.*?<div class=\"path\">(.*?)</div>)?", re.S)
    for m in pat.finditer(s):
        lid, tt, path = m.group(1), m.group(2), m.group(3) or ""
        if lid in seen:
            continue
        title = _strip(tt)
        if not title:
            continue
        seen.add(lid)
        rows.append({"level_id": lid, "title": title,
                     "volume": _strip(path)[:40],
                     "is_jwamok": bool(_JWAMOK.search(title)),
                     "url": _cite(lid)})

    jwamok = [r for r in rows if r["is_jwamok"]]
    real = [r for r in rows if not r["is_jwamok"]]
    shown = rows if include_jwamok else real
    for r in shown:
        r.pop("is_jwamok", None)

    out = {
        "query": query,
        "total_hits": reported_total or len(rows),
        "page_hits": len(rows),
        "jwamok_filtered": len(jwamok),
        "substantive": len(real),
        "results": shown,
        "note": ("등록류는 국역만 제공됩니다. 한문 인용이 필요하면 "
                 "원문 열람 경로를 국사편찬위원회에 문의하십시오."),
    }
    if jwamok:
        pct = round(len(jwamok) / len(rows) * 100)
        out["warning"] = (
            f"검색 {len(rows)}건 중 {len(jwamok)}건({pct}%)이 座目(회의 참석 명단)입니다. "
            f"실질 기사는 {len(real)}건이며, 검색 건수를 주제 중요도 지표로 쓰지 마십시오.")
    return out


# ─────────────────────────────────────────────────────────────
# 3. joseon_item_read — 본문 조회 (경로 자동 판별)
# ─────────────────────────────────────────────────────────────

def joseon_item_read(level_id: str, max_chars: int = 20000) -> dict:
    """levelId로 본문을 조회한다.

    본문이 비어 있으면 '미공개'인지 '파싱 실패'인지 구분해 반환한다.
    '도달하지 못했다'와 '공개되지 않았다'는 다르고, 후자는 재시도로 해결되지 않는다.
    """
    s = _get(_url_for(level_id))
    if not s:
        return {"level_id": level_id, "body": None,
                "body_status": "not_found", "url": _cite(level_id),
                "note": "요청이 응답하지 않았습니다."}

    lines = _lines(s)

    # 표제 추출
    title = ""
    for l in lines:
        if re.search(r"啓$|傳敎$|事目|節目|條例|大典|要覽|謄錄", l) and 8 < len(l) < 140:
            title = l
            break

    # 본문 시작점
    if level_id.startswith("jlaw"):
        k = lines.index("다음글") + 1 if "다음글" in lines else None
    else:
        k = next((i for i, l in enumerate(lines)
                  if l.startswith("◯") or l.startswith("○")), None)

    if k is None:
        status = "not_published" if title else "parse_failed"
        return {
            "level_id": level_id, "title": title, "body": None,
            "body_status": status, "url": _cite(level_id),
            "note": ("항목은 정상 존재하고 URL도 유효하나 본문(국역·원문)이 "
                     "공개되지 않았습니다. 재시도로 해결되지 않으며, 필요 시 "
                     "국사편찬위원회에 문의하십시오."
                     if status == "not_published"
                     else "본문 영역을 찾지 못했습니다. 페이지 구조 변경 가능성이 있습니다."),
        }

    end = next((i for i, l in enumerate(lines[k:], k)
                if "경기도 과천시" in l or "개인정보" in l), k + 250)
    body = " ".join(lines[k:end])[:max_chars]

    is_law = level_id.startswith("jlaw")
    return {
        "level_id": level_id,
        "title": title,
        "body": body,
        "chars": len(body),
        "body_status": "ok",
        "url": _cite(level_id),
        "original_text": is_law,
        "citation_note": ("한문 원문 제공 — 인용 가능(표점은 DB 형태)"
                          if is_law else
                          "국역만 제공 — 한문 표기를 역구성하면 학술 인용 불가"),
    }


# ─────────────────────────────────────────────────────────────
# 4. ★ joseon_sibling_scan — 형제 조 전수 스캔
# ─────────────────────────────────────────────────────────────

def _head_of(body: str) -> str:
    """조 제목 추출. 본문 첫 어절(한자 2~6자)이 조 이름인 경우가 많다."""
    if not body:
        return "?"
    m = re.match(r"\s*([\u4e00-\u9fff]{2,6})", body)
    return m.group(1) if m else body[:12]


def joseon_sibling_scan(level_id: str, span: int = 12) -> dict:
    """편(編)·조(條) 구조 사료의 형제 조를 전수 조회한다.

    ★ 이 서버에서 가장 중요한 도구다.
    법전·편람 조문을 하나라도 열었다면 반드시 이어서 호출할 것.

    한강 조사에서 이 확인을 건너뛰어 두 사료에서 핵심 조문을 놓쳤다.
    萬機要覽 舟橋 편의 [津路]·[員額], 六典條例 舟橋司 편의 시공 시방·배정 산식이
    전부 이미 열었던 편 안에 있었다.
    """
    m = re.match(r"(.+_)(\d{4})$", level_id)
    if not m:
        return {"error": "형제 조 스캔은 4자리 일련번호로 끝나는 levelId에만 적용됩니다.",
                "level_id": level_id}

    stem = m.group(1)
    asked = int(m.group(2))
    siblings, checked = [], []

    for n in range(1, span + 1):
        lid = f"{stem}{n * 10:04d}"
        checked.append(lid)
        r = joseon_item_read(lid, max_chars=400)
        if r.get("body_status") != "ok":
            time.sleep(POLITE_DELAY)
            continue
        body = r["body"] or ""
        if "조선시대법령자료 메뉴" in body:      # 존재하지 않는 번호
            time.sleep(POLITE_DELAY)
            continue

        # 조 제목 — 본문 첫 어절이 조 이름인 경우가 많다 (津路 / 橋排船…)
        head = _head_of(body)
        siblings.append({
            "level_id": lid,
            "head": head,
            "chars": r.get("chars", 0),
            "preview": body[:180],
            "url": _cite(lid),
            "is_requested": (n * 10 == asked),
        })
        time.sleep(POLITE_DELAY)

    others = [s for s in siblings if not s["is_requested"]]
    out = {
        "requested": level_id,
        "parent": stem.rstrip("_"),
        "siblings": siblings,
        "found": len(siblings),
        "checked": len(checked),
    }
    if others:
        heads = ", ".join(dict.fromkeys(f"[{s['head']}]" for s in others))
        out["alert"] = (f"요청한 조 외에 {len(others)}개가 더 있습니다: {heads}. "
                        "전부 확인하십시오. 총론만 읽고 끝내면 핵심을 놓칩니다.")
    else:
        out["note"] = "형제 조가 확인되지 않았습니다. span을 늘려 재시도할 수 있습니다."
    return out


# ─────────────────────────────────────────────────────────────
# 5. law_presence_matrix — 법전 수록 대조표 (부재의 발견)
# ─────────────────────────────────────────────────────────────

def law_presence_matrix(terms: list) -> dict:
    """여러 어휘의 법전 수록 건수를 나란히 대조한다.

    부재 자체가 발견이다.
    한강 조사에서 강배 어휘 14종을 대조한 결과, 배·사람·나루·삯·창고는
    법전 조문인데 '어느 배에 어느 노선을 줄 것인가'만 법전에 없었다.
    """
    matrix, absent = [], []
    for t in terms[:30]:
        r = joseon_law_search(t, max_results=10)
        total = r.get("total", 0)
        earliest, in_code = "", False
        if r.get("results"):
            sources = [x["source"] for x in r["results"] if x.get("source")]
            for code in ("經國大典", "續大典", "大典通編", "大典會通",
                         "受敎輯錄", "六典條例"):
                if any(code in s for s in sources):
                    earliest, in_code = code, True
                    break
            if not earliest and sources:
                earliest = sources[0]
        row = {"term": t, "count": total, "earliest": earliest, "in_code": in_code}
        if total == 0:
            row["note"] = "법전 미수록"
            absent.append(t)
        elif not in_code:
            row["note"] = f"법전이 아닌 {earliest}에만 수록 — 조문 아닐 수 있음"
            absent.append(t)
        matrix.append(row)
        time.sleep(POLITE_DELAY)

    matrix.sort(key=lambda x: -x["count"])
    out = {"matrix": matrix, "absent": absent}
    if absent:
        out["finding"] = (
            f"{', '.join(absent)}는 법전에 오르지 못했습니다. "
            "제도사를 법전으로만 재구성하면 이 요소는 존재하지 않습니다. "
            "등록류·일기류를 함께 읽으십시오.")
    return out


# ─────────────────────────────────────────────────────────────
# 6. term_origin_trace — 어휘 연원 추적
# ─────────────────────────────────────────────────────────────

_DOMAIN_HINTS = {
    "노비·신분": ["奴婢", "婢", "良賤", "從良"],
    "재산·상속": ["分衿", "衿", "遺書", "文記", "和會"],
    "시험·교육": ["講", "生員", "成均館", "考講", "製述"],
    "형벌·소송": ["刑", "決訟", "杖", "徒", "流"],
    "군사":     ["軍", "兵", "鎭", "營", "戰船"],
    "조운·선박": ["船", "漕", "津", "渡", "水站"],
    "재정·세":  ["稅", "貢", "米", "錢", "貿"],
}


def term_origin_trace(term: str, domain: str = "") -> dict:
    """제도 용어를 법전 전체에 대조해 원래 어느 영역의 용어였는지 추적한다.

    한강 조사에서 執籌는 노비 상속 분할, 抽籤은 강경 시험 용어였고
    18세기에 조운으로 전용된 것을 확인했다.
    용어의 출신을 알면 제도의 성격이 드러난다.
    """
    r = joseon_law_search(term, max_results=100)
    if r.get("total", 0) == 0:
        return {"term": term, "total_in_law": 0,
                "finding": f"'{term}'은 법전에 나타나지 않습니다. "
                           "법전 밖 관행 용어일 수 있습니다."}

    domains, reps = {}, []
    for item in r["results"]:
        blob = (item.get("section", "") + " " + item.get("excerpt", ""))
        matched = []
        for dom, hints in _DOMAIN_HINTS.items():
            if any(h in blob for h in hints):
                matched.append(dom)
                domains[dom] = domains.get(dom, 0) + 1
        if len(reps) < 5:
            reps.append({"source": item.get("source", ""),
                         "section": item.get("section", ""),
                         "excerpt": item.get("excerpt", "")[:200],
                         "domains": matched,
                         "url": item.get("url", "")})

    out = {
        "term": term,
        "total_in_law": r["total"],
        "domains": dict(sorted(domains.items(), key=lambda x: -x[1])),
        "representative": reps,
    }
    if domain:
        hits = domains.get(domain, 0)
        if hits == 0:
            top = next(iter(out["domains"]), "확인 불가")
            out["finding"] = (
                f"'{domain}' 영역 용례가 법전에 0건입니다. "
                f"이 용어는 주로 '{top}' 영역에서 쓰였으며, "
                f"'{domain}'으로 전용된 것으로 보입니다. "
                "전용 시점을 등록류·일기류에서 확인하십시오.")
    return out


# ─────────────────────────────────────────────────────────────
# 7. sjw_search — 승정원일기 (왕대 분포 포함)
# ─────────────────────────────────────────────────────────────

_REIGNS = ["태조", "정종", "태종", "세종", "문종", "단종", "세조", "예종",
           "성종", "연산군", "중종", "인종", "명종", "선조", "광해군", "인조",
           "효종", "현종", "숙종", "경종", "영조", "정조", "순조", "헌종",
           "철종", "고종", "순종"]


def sjw_search(query: str, max_results: int = 50) -> dict:
    """승정원일기를 검색하고 왕대별 분포를 함께 반환한다.

    최초 용례가 통념보다 이르면 제도사 서사가 뒤집힌다.
    執籌船 53건의 영조 2건이 주교사(1790)보다 58년 앞선 1731년 사례였다.
    """
    s = _post(SJW + "/search/searchResultList.do", {
        "searchTerm": query, "searchTermImages": "",
        "topSearchWord": query, "topSearchWord_ime": query,
        "pageUnit": str(min(max_results, 100)), "pageIndex": "1",
        "searchType": "a",
    })
    if not s:
        return {"error": "요청 실패", "query": query}

    t = _strip(s)
    m = re.search(r"검색결과\s*([\d,]+)\s*건", t) or re.search(r"총\s*([\d,]+)\s*건", t)
    total = int(m.group(1).replace(",", "")) if m else 0

    dist = {}
    for reign in _REIGNS:
        mm = re.search(re.escape(reign) + r"\s*\((\d+)\)", t)
        if mm:
            dist[reign] = int(mm.group(1))

    earliest = None
    me = re.search(r"(" + "|".join(_REIGNS) + r")\s*(\d+)년[^\d]{0,12}(\d{4})년", t)
    if me:
        earliest = {"reign": f"{me.group(1)} {me.group(2)}년",
                    "year": int(me.group(3))}

    out = {"query": query, "total": total,
           "reign_distribution": dist, "earliest": earliest}
    if earliest:
        out["alert"] = (
            f"최초 용례가 {earliest['year']}년({earliest['reign']})입니다. "
            "관련 기구·제도의 성립 연대와 대조하십시오. "
            "용어가 기구보다 앞서면 그 기구는 제도를 만든 것이 아니라 인수한 것입니다.")
    return out


# ─────────────────────────────────────────────────────────────
# 8. kyujanggak_search — 목록 + 해제 동시 조회
# ─────────────────────────────────────────────────────────────

def kyujanggak_search(query: str, area: str = "both") -> dict:
    """규장각 검색. 목록과 해제를 모두 조회한다.

    ★ 절목·사목류는 상위 서명 아래 편차(編次)로 들어가 있어
    목록 검색만으로는 나오지 않는다. 舟橋指南이 이 방식으로 발견되었다.
    """
    areas = {"list": [("10", "목록")], "abstract": [("20", "해제")],
             "both": [("10", "목록"), ("20", "해제")]}.get(area, [("10", "목록")])

    khdr = dict(_HDR)
    khdr["Referer"] = KYU + "/"
    out = {"query": query, "sections": {}}

    for code, label in areas:
        data = urllib.parse.urlencode({
            "totalSearchString": query, "searchArea": code}).encode()
        try:
            req = urllib.request.Request(KYU + "/search/search.do",
                                         data=data, headers=khdr)
            page = _decode(urllib.request.urlopen(req, timeout=90, context=_CTX))
        except Exception as e:
            out["sections"][label] = {"error": type(e).__name__}
            time.sleep(POLITE_DELAY)
            continue

        items = []
        for m in re.finditer(r"(奎[\d軸]+)", page):
            code_no = m.group(1)
            if code_no not in [i["call_number"] for i in items]:
                items.append({"call_number": code_no})
        out["sections"][label] = {"count": len(items), "items": items[:30]}
        time.sleep(POLITE_DELAY)

    if area == "both":
        lst = out["sections"].get("목록", {}).get("count", 0)
        abs_ = out["sections"].get("해제", {}).get("count", 0)
        if abs_ > lst:
            out["alert"] = ("해제 검색이 목록보다 많은 자료를 찾았습니다. "
                            "절목·사목류가 상위 서명 아래 편차로 들어가 있을 수 있습니다.")
    out["note"] = ("규장각 자료의 게재는 소장기관 허가 범위 확인이 필요합니다. "
                   "복제 문의 02-880-5316")
    return out


# ─────────────────────────────────────────────────────────────
# 9. kyujanggak_images — 원문 이미지 (item_cd 자동 탐지)
# ─────────────────────────────────────────────────────────────

ITEM_CD_TABLE = {
    "ART": "도설·회화 (예 各船圖本 奎15752)",
    "ETC": "두루마리·축 (예 奎軸12163)",
    "DRR": "등록류 (예 禁營津船謄錄 奎19356)",
    "FND": "재정·사목 (예 均役廳事目 奎17252)",
    "POL": "정책·절목 (예 舟橋指南 奎5485) — 파일명 규칙 상이",
}


def kyujanggak_images(book_cd: str, item_cd: Optional[str] = None,
                      max_pages: int = 60) -> dict:
    """규장각 원문 이미지 URL 목록을 생성한다.

    ★ 첫 이미지를 실제로 받아 패턴을 확정한 뒤 순회한다.
    舟橋指南(POL) 계열은 파일명 규칙이 달라 추정하면 전부 실패한다.
    """
    candidates = [item_cd] if item_cd else list(ITEM_CD_TABLE.keys())
    khdr = dict(_HDR)
    khdr["Referer"] = KYU + "/"

    def try_pattern(icd: str, style: str, n: int) -> Optional[str]:
        fn = (f"{book_cd}_00IH_0001_{n:04d}.jpg" if style == "POL"
              else f"{book_cd}_00_IH_0001_{n:03d}a.jpg")
        url = (f"{KYU}/ImageServlet.do?imgFileNm={fn}"
               f"&path=/data01/stream/{icd}/IMG/{book_cd}/{book_cd}_0001/")
        try:
            req = urllib.request.Request(url, headers=khdr)
            r = urllib.request.urlopen(req, timeout=30, context=_CTX)
            if r.status == 200 and int(r.headers.get("Content-Length", "0")) > 4000:
                return url
        except Exception:
            pass
        return None

    verified_cd, verified_style, first = None, None, None
    for icd in candidates:
        for style in ("POL", "STD"):
            hit = try_pattern(icd, style, 1)
            time.sleep(POLITE_DELAY)
            if hit:
                verified_cd, verified_style, first = icd, style, hit
                break
        if verified_cd:
            break

    if not verified_cd:
        return {"book_cd": book_cd, "pattern_verified": False,
                "item_cd_table": ITEM_CD_TABLE,
                "note": ("패턴을 확정하지 못했습니다. 상세 페이지에서 "
                         "fn_originalImg(item_cd, book_cd) 인자를 확인한 뒤 "
                         "item_cd를 직접 지정하십시오. 추정으로 순회하지 마십시오.")}

    urls = []
    for i in range(1, max_pages + 1):
        fn = (f"{book_cd}_00IH_0001_{i:04d}.jpg" if verified_style == "POL"
              else f"{book_cd}_00_IH_0001_{i:03d}a.jpg")
        urls.append(f"{KYU}/ImageServlet.do?imgFileNm={fn}"
                    f"&path=/data01/stream/{verified_cd}/IMG/{book_cd}/{book_cd}_0001/")

    return {
        "book_cd": book_cd,
        "item_cd": verified_cd,
        "item_cd_meaning": ITEM_CD_TABLE.get(verified_cd, ""),
        "pattern": (f"{book_cd}_00IH_0001_{{n:04d}}.jpg" if verified_style == "POL"
                    else f"{book_cd}_00_IH_0001_{{n:03d}}a.jpg"),
        "pattern_verified": True,
        "first_verified_url": first,
        "urls": urls,
        "count": len(urls),
        "rights": "C",
        "note": ("게재는 소장기관 허가 범위 확인 필요. 복제 문의 02-880-5316. "
                 "목차·범례 지면을 먼저 열어 조사 범위를 좁히십시오."),
    }


# ─────────────────────────────────────────────────────────────
# 10. link_verify — 인용 링크 전수 검증
# ─────────────────────────────────────────────────────────────

def link_verify(level_ids: Optional[list] = None,
                urls: Optional[list] = None) -> dict:
    """인용 링크를 전수 검증한다.

    HTTP 200과 본문 존재를 별개로 판정한다.
    '도달하지 못했다'와 '공개되지 않았다'는 다르고, 후자는 재시도로 해결되지 않는다.
    """
    result = {}

    if level_ids:
        ok, issues = 0, []
        for lid in level_ids:
            r = joseon_item_read(lid, max_chars=100)
            if r.get("body_status") == "ok":
                ok += 1
            else:
                issues.append({"id": lid, "cause": r.get("body_status"),
                               "note": r.get("note", "")})
            time.sleep(0.25)
        result["level_ids"] = {"checked": len(level_ids), "ok": ok,
                               "issues": issues}

    if urls:
        ok, issues = 0, []
        for u in urls:
            clean = html.unescape(u)
            try:
                r = urllib.request.urlopen(
                    urllib.request.Request(clean, headers=_HDR),
                    timeout=25, context=_CTX)
                st = r.status
            except Exception as e:
                st = getattr(e, "code", None) or type(e).__name__
            if st == 200:
                ok += 1
            else:
                if "&amp;" in u:
                    cause, note = "html_entity", "HTML의 &amp; 미해제 — 해제하면 정상"
                elif st == 202:
                    cause, note = "async_202", "비동기 응답(봇 차단 아님)"
                elif isinstance(st, str) and "Timeout" in st:
                    cause, note = "server_slow", "기관 서버 지연 — 시간을 두고 재시도"
                elif st == 400 and re.search(r"search|Result", clean, re.I):
                    cause, note = "post_only", "POST 기반 검색 URL — GET 재현 불가"
                elif st == 404:
                    cause, note = "not_found", "★ 실제 사망 링크 가능성 — 수동 확인"
                else:
                    cause, note = "other", f"코드 {st}"
                issues.append({"url": clean[:100], "cause": cause, "note": note})
            time.sleep(0.15)
        dead = sum(1 for i in issues if i["cause"] == "not_found")
        result["urls"] = {"checked": len(urls), "ok": ok,
                          "issues": issues, "dead_links": dead}
        result["note"] = ("이상 항목 대부분은 조회 방식 문제이며 자료 소멸이 아닙니다. "
                          "not_found만 실제 사망 링크 후보입니다.")
    return result


# ─────────────────────────────────────────────────────────────
# 도구 등록 (MCP 서버에 붙일 때 사용)
# ─────────────────────────────────────────────────────────────

TOOLS = {
    "joseon_law_search": joseon_law_search,
    "joseon_record_search": joseon_record_search,
    "joseon_item_read": joseon_item_read,
    "joseon_sibling_scan": joseon_sibling_scan,
    "law_presence_matrix": law_presence_matrix,
    "term_origin_trace": term_origin_trace,
    "sjw_search": sjw_search,
    "kyujanggak_search": kyujanggak_search,
    "kyujanggak_images": kyujanggak_images,
    "link_verify": link_verify,
}

RECOMMENDED_ORDER = [
    "joseon_law_search      — 법전에 근거가 있는가",
    "joseon_sibling_scan    — ★ 조를 열었으면 반드시 형제 조 확인",
    "law_presence_matrix    — 여러 어휘 대조로 부재를 발견",
    "term_origin_trace      — 핵심 용어의 출신",
    "joseon_record_search   — 실제 운영 기록(좌목 필터)",
    "joseon_item_read       — 본문 판독",
    "sjw_search             — 최초 용례·왕대 분포로 연대 검증",
    "kyujanggak_search      — 원전 소재(목록+해제)",
    "kyujanggak_images      — 원문 이미지",
    "link_verify            — 마무리: 인용 유효성",
]


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n사용 가능한 도구:")
        for name in TOOLS:
            print(f"  {name}")
        print("\n권장 호출 순서:")
        for line in RECOMMENDED_ORDER:
            print(f"  {line}")
        sys.exit(0)

    tool = sys.argv[1]
    if tool not in TOOLS:
        print(f"알 수 없는 도구: {tool}")
        sys.exit(1)
    args = sys.argv[2:]
    kwargs = {}
    if tool in ("law_presence_matrix",):
        kwargs = {"terms": args}
    elif tool == "link_verify":
        kwargs = {"level_ids": args}
    elif args:
        first = args[0]
        key = {"joseon_item_read": "level_id",
               "joseon_sibling_scan": "level_id",
               "kyujanggak_images": "book_cd"}.get(tool, "query")
        kwargs = {key: first}
        if len(args) > 1 and tool == "term_origin_trace":
            kwargs["domain"] = args[1]
    print(json.dumps(TOOLS[tool](**kwargs), ensure_ascii=False, indent=2))
