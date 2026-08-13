#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
발굴 결과 인계 — korea-archive-discovery → 이 파이프라인

사용법
    # 발굴 표(마크다운/CSV/JSON) → 판독 작업 목록으로
    python from_discovery.py <발굴결과> --out <디렉터리>

    # MCP 도구 결과를 붙여넣은 텍스트에서 식별자 추출
    python from_discovery.py --paste "<MCP 응답 텍스트>" --out <디렉터리>

    # 작업 계획만 — 무엇을 먼저 볼지 우선순위를 매긴다
    python from_discovery.py <발굴결과> --plan

두 스킬의 경계
    korea-archive-discovery : 자료를 **찾는다** (5개 소스 검색·쿼리 전략·권리 초판)
    이 파이프라인            : 찾은 자료를 **연다** (실물 검토·판독·재기술·논문·전파)

    발굴 스킬의 산출은 「식별자 · 원제 · 연대 · 소장처 · URL · 권리등급 · 재현쿼리」 표다.
    이 스크립트는 그 표를 받아 판독 작업 목록으로 바꾼다.

우선순위 판정
    발굴 결과가 수십 건이면 무엇부터 열어야 할지 정해야 한다.
    다음 신호가 있는 자료를 앞에 둔다.
      · 표제에 「ETC」·세미콜론 → 원 기술이 숨긴 것이 있다
      · 원제가 지나치게 짧음   → 내용을 알 수 없다
      · 표제에 당대 표기 지명  → 표기 확장의 성과
      · 자매편 번호가 인접     → 계열 복원 가능
      · 권리 D등급             → 게재 불가이나 존재는 기록해야
"""
import argparse, json, os, re, sys, csv

# 발굴 표에서 뽑아낼 열 이름 후보
COLS = {
    "id": ["식별자", "identifier", "id", "참조코드", "reference"],
    "naid": ["naid", "NAID"],
    "title": ["원제", "표제", "title", "제목"],
    "date": ["연대", "date", "날짜", "연도"],
    "repo": ["소장처", "repository", "소장", "기관"],
    "url": ["url", "링크", "바로가기"],
    "rights": ["권리", "rights", "권리등급", "등급"],
    "query": ["쿼리", "query", "검색어", "재현쿼리"],
}

# 원 기술이 무언가를 숨기고 있다는 신호
HIDE_SIGNALS = [
    (r"\bETC\b", 30, "「ETC」 — 표제가 가린 내용이 있다"),
    (r";", 20, "세미콜론 — 두 번째 주제가 있다"),
    (r"\bVARIOUS\b|\bMISCELLANEOUS\b", 25, "「여러 주제」 — 내용 불명"),
    (r"\bSCENES?\b\s*$", 10, "「장면」으로 끝남 — 구체성 없음"),
]

# 당대 표기 — 표기 확장으로 찾은 자료임을 뜻한다
OLD_FORMS = {
    "SAISHU": "제주", "QUELPART": "제주", "KEIJO": "서울", "KYONGSONG": "경성",
    "FUSAN": "부산", "PUSAN": "부산", "JINSEN": "인천", "CHEMULPO": "제물포",
    "KAIJO": "개성", "HEIJO": "평양", "TAIKYU": "대구", "GENZAN": "원산",
    "CHOSEN": "조선", "TYOSEN": "조선", "COREA": "한국", "CORÉE": "한국",
}


def norm_key(k):
    k = str(k).strip().lower()
    for std, alts in COLS.items():
        if any(a.lower() == k for a in alts):
            return std
    return None


def from_markdown(text):
    """마크다운 표를 읽는다 — 발굴 스킬의 기본 산출 형식"""
    rows, header = [], None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r"[-: ]+", c) for c in cells):
            continue
        if header is None:
            header = [norm_key(c) for c in cells]
            continue
        d = {}
        for k, v in zip(header, cells):
            if k and v:
                d[k] = re.sub(r"\*\*|`|\[|\]\(.*?\)", "", v).strip()
        if d.get("id") or d.get("title"):
            rows.append(d)
    return rows


def from_paste(text):
    """MCP 도구 응답에서 식별자와 표제를 뽑는다"""
    rows = []
    # - [NAID 19187] TITLE | 111-ADC-5388 | https://...
    for m in re.finditer(r"\[NAID\s*(\d+)\]\s*([^|]+?)\s*\|\s*([\w\-\.]+)\s*\|\s*(\S+)", text):
        rows.append(dict(naid=m.group(1), title=m.group(2).strip(),
                         id=m.group(3).strip(), url=m.group(4).strip()))
    # - [CO 537/3482] Title (1948) https://...
    for m in re.finditer(r"\[([A-Z]{2,}[\w\s/\-]+)\]\s*([^(]+?)\s*\((\d{4}[^)]*)\)\s*(\S+)", text):
        rows.append(dict(id=m.group(1).strip(), title=m.group(2).strip(),
                         date=m.group(3).strip(), url=m.group(4).strip()))
    # identifier: 111-adc-5388 형식
    if not rows:
        for m in re.finditer(r"\b(\d{3}-[a-zA-Z]{2,4}-[\w\-]+)\b", text):
            rows.append(dict(id=m.group(1)))
    # 중복 제거
    seen, out = set(), []
    for r in rows:
        k = r.get("id") or r.get("naid")
        if k and k not in seen:
            seen.add(k); out.append(r)
    return out


def score(row):
    """판독 우선순위 — 높을수록 먼저 연다"""
    t = (row.get("title") or "").upper()
    s, why = 0, []

    for pat, pts, msg in HIDE_SIGNALS:
        if re.search(pat, t):
            s += pts; why.append(msg)

    found = [v for k, v in OLD_FORMS.items() if k in t]
    if found:
        s += 15; why.append(f"당대 표기 — {' · '.join(sorted(set(found)))}")

    words = len(re.findall(r"[A-Z가-힣]{2,}", t))
    if words and words <= 4:
        s += 12; why.append(f"표제가 짧다 ({words}단어) — 내용 불명")

    if row.get("naid"):
        s += 5
    if (row.get("rights") or "").upper().startswith("D"):
        s -= 40; why.append("권리 D등급 — 게재 불가 (존재만 기록)")
    if row.get("url"):
        s += 8; why.append("URL 확보 — 즉시 열람 가능")

    return s, why


def to_reading_stub(row):
    """판독 JSON 골격 — 열어보기 전 상태"""
    return {
        "id": row.get("id", ""),
        "naid": row.get("naid", ""),
        "title_original": row.get("title", ""),
        "title_ko": "",                       # 재기술 후 채운다
        "repository": row.get("repo", ""),
        "record_group": "",
        "duration_sec": 0,
        "source_url": row.get("url", ""),
        "discovery_query": row.get("query", ""),   # 재현 쿼리 — 발굴 스킬에서 인계
        "date": {"value": row.get("date", ""), "basis": "카탈로그", "confidence": "부분"},
        "readings": [],
        "entities": {"places": [], "agents": [], "units": [], "events": []},
        "unconfirmed": ["실물 미검토 — 아래 항목은 카탈로그 기준"],
        "publication": {"tier": 1, "reason": ""},
        "rights": {"grade": (row.get("rights") or "B")[:1].upper(),
                   "basis": "발굴 스킬 초판 — 재확인 요"},
        "relations": [],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?")
    ap.add_argument("--paste")
    ap.add_argument("--out", default=".")
    ap.add_argument("--plan", action="store_true")
    a = ap.parse_args()

    if a.paste:
        rows = from_paste(a.paste)
    elif a.src:
        txt = open(a.src, encoding="utf-8").read()
        if a.src.endswith(".json"):
            d = json.loads(txt)
            rows = d if isinstance(d, list) else [d]
        elif a.src.endswith(".csv"):
            rows = []
            for r in csv.DictReader(open(a.src, encoding="utf-8-sig")):
                rows.append({norm_key(k) or k: v for k, v in r.items()})
        else:
            rows = from_markdown(txt) or from_paste(txt)
    else:
        ap.error("발굴 결과 파일 또는 --paste 가 필요합니다")

    if not rows:
        print("발굴 결과를 읽지 못했습니다.", file=sys.stderr)
        print("표 형식(마크다운·CSV·JSON) 또는 MCP 응답 텍스트를 넣으십시오.", file=sys.stderr)
        sys.exit(1)

    ranked = sorted(((score(r), r) for r in rows), key=lambda x: -x[0][0])

    print("=" * 68)
    print(f"  발굴 {len(rows)}건 인계 — 판독 우선순위")
    print("=" * 68)
    for (s, why), r in ranked:
        tag = "★★★" if s >= 40 else "★★" if s >= 20 else "★" if s > 0 else "  "
        print(f"\n{tag} [{s:>3}] {r.get('id','(식별자 없음)')}")
        if r.get("title"):
            print(f"        {r['title'][:64]}")
        for w in why:
            print(f"        · {w}")

    if a.plan:
        return

    os.makedirs(a.out, exist_ok=True)
    stubs = [to_reading_stub(r) for _, r in ranked]
    p = os.path.join(a.out, "reading_queue.json")
    json.dump(stubs, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("\n" + "=" * 68)
    print(f"  판독 대기열: {p}  ({len(stubs)}건)")
    print("=" * 68)
    print("""
다음 순서로 진행하십시오.

  ① 실물 확보 후 분석
     python scripts/analyze_video.py auto <영상> --out <디렉터리>

  ② 판독 — VLM 교차검증 (references/vlm_reading.md)
     python scripts/analyze_image.py --identify "<판독한 문자열>"

  ③ reading_queue.json 의 해당 항목을 채운다
     readings · entities · unconfirmed · date.confidence

  ④ 게재 판정 (references/publication_ethics.md)
     publication.tier 를 1~4로

  ⑤ 메타데이터·온톨로지
     python scripts/make_metadata.py build reading_queue.json --out <디렉터리>

⚠ 인계된 권리 등급은 발굴 스킬의 자동 초판입니다.
   실물을 본 뒤 반드시 재확인하십시오.
   특히 D등급(노획 기록)은 화면을 일절 게재하지 않습니다.
""")


if __name__ == "__main__":
    main()
