# -*- coding: utf-8 -*-
"""TNA Discovery 수집 — 14 전략 레이어(T-01~T-14) + 인용 역추적(T-12)·인접 확장(T-13, Adaptive Mining).

API: TNA Discovery API (공개, 키 불요) — https://discovery.nationalarchives.gov.uk/API/
     search:  /API/search/records?sps.searchQuery=...&sps.resultsPageSize=...&sps.page=...
응답 필드는 방어적으로 파싱한다(records[].reference/title/id 등).
"""
from __future__ import annotations
import re, time
import os, sys
_here = os.path.dirname(os.path.abspath(__file__))
for _cand in (os.path.join(os.path.dirname(_here), "keywords"),
              os.path.join(os.path.dirname(os.path.dirname(_here)), "keywords")):
    if os.path.isdir(_cand) and _cand not in sys.path:
        sys.path.insert(0, _cand)

from keywords_tna import generate, CITATION_SEEDS, ADJACENT_RANGE, TNA_DEPT_CODES
from keywords_common import COMMON_GROUPS
from .util import http_json, qs, SearchLog, Dedup, jsonl_writer, emit, DATA

API = "https://discovery.nationalarchives.gov.uk/API/search/records"

# 한국 관련성 판정 어휘 (Adaptive Mining 승격 후보 스코어링용) — 공통 그룹에서 소문자 집합 구성
_KW = set()
for _gid, _ko, _en, _dim, kws in COMMON_GROUPS:
    for k in kws:
        _KW.update(w for w in k.lower().split() if len(w) > 3)
_KW |= {"korea", "korean", "corea", "corean", "chosen", "seoul", "pusan", "panmunjom", "inchon"}

def korea_score(text: str) -> int:
    t = (text or "").lower()
    return sum(1 for w in ("korea", "korean", "corea", "corean", "chosen", "seoul",
                            "pusan", "panmunjom", "inchon", "pyongyang", "armistice"
                            ) if w in t)

def _records(data: dict):
    return data.get("records") or data.get("Records") or []

def _count(data: dict):
    return data.get("count") or data.get("Count") or 0

def _extract(r: dict, layer: str, query: str) -> dict:
    return {
        "src": "TNA", "tna_id": r.get("id") or r.get("Id"),
        "local_id": r.get("reference") or r.get("Reference"),
        "title": re.sub(r"<[^>]+>", "", (r.get("title") or r.get("Title")
                        or r.get("description") or r.get("Description") or ""))[:300],
        "description": re.sub(r"<[^>]+>", "", (r.get("description") or ""))[:600],
        "department": r.get("department"), "context": (r.get("context") or "")[:200],
        "date": r.get("coveringDates") or r.get("CoveringDates") or "",
        "held_by": (r.get("heldBy") or r.get("HeldBy") or [None])[0]
                    if isinstance(r.get("heldBy") or r.get("HeldBy"), list)
                    else (r.get("heldBy") or r.get("HeldBy")),
        "layer": layer, "query": query,
        "url": f"https://discovery.nationalarchives.gov.uk/details/r/{r.get('id') or r.get('Id')}"
               if (r.get("id") or r.get("Id")) else None,
    }

def _search(query: str, page_size: int = 100, max_pages: int = 2, sleep: float = 1.0):
    page = 1
    while page <= max_pages:
        data = http_json(API + "?" + qs({"sps.searchQuery": query,
                                          "sps.resultsPageSize": page_size,
                                          "sps.page": page}))
        recs, total = _records(data), _count(data)
        yield recs, total
        if page * page_size >= (total or 0) or not recs: break
        page += 1; time.sleep(sleep)

def run_layers(layers: list[str] | None = None, max_queries_per_layer: int | None = None,
               max_pages: int = 1, sleep: float = 1.2):
    """T-01~T-14 레이어 쿼리 실행 → data/tna_records.jsonl + data/search_log_tna.csv."""
    log = SearchLog(os.path.join(DATA, "search_log_tna.csv"))
    out = jsonl_writer(os.path.join(DATA, "tna_records.jsonl"))
    dd = Dedup(); stats = {}
    for layer_id, stype, queries in generate():
        if layers and layer_id not in layers: continue
        n_new_layer = 0
        for q in (queries[:max_queries_per_layer] if max_queries_per_layer else queries):
            hits_total, n_new = 0, 0
            try:
                for recs, total in _search(q, max_pages=max_pages, sleep=sleep):
                    hits_total = total
                    for r in recs:
                        rec = _extract(r, layer_id, q)
                        if dd.is_new(rec): emit(out, rec); n_new += 1
            except Exception as e:
                log.add("TNA", layer_id, q, -1, 0, f"ERROR {e}"); continue
            log.add("TNA", layer_id, q, hits_total, n_new)
            n_new_layer += n_new; time.sleep(sleep)
        stats[layer_id] = n_new_layer
        print(f"[{layer_id}/{stype}] 신규 {n_new_layer}건")
    log.close(); out.close()
    return stats

def adaptive_mine(rng: int = ADJACENT_RANGE, sleep: float = 1.2,
                  promote_threshold: int = 1):
    """T-12 시드 22건 → T-13 인접 확장(piece ± rng) 순회 → 한국 관련성 스코어로 승격 후보 산출.
    산출: data/tna_mined.jsonl(전체) + data/promoted_series.csv(승격 후보 — 논문 승격률 93.0% 대응 수동 검증 대상).
    """
    import csv
    log = SearchLog(os.path.join(DATA, "search_log_tna.csv"))
    out = jsonl_writer(os.path.join(DATA, "tna_mined.jsonl"))
    pf = open(os.path.join(DATA, "promoted_series.csv"), "w", newline="", encoding="utf-8-sig")
    pw = csv.writer(pf); pw.writerow(["reference", "score", "title", "seed", "url"])
    dd = Dedup(); n_promoted = 0
    for seed_ref, source in CITATION_SEEDS:
        m = re.match(r"([A-Z]+ \d+)/(\d+)", seed_ref)
        if not m: continue
        series, piece = m.group(1), int(m.group(2))
        for p in range(piece - rng, piece + rng + 1):
            ref = f"{series}/{p}"
            hits_total, n_new = 0, 0
            try:
                for recs, total in _search(f'"{ref}"', max_pages=1, sleep=sleep):
                    hits_total = total
                    for r in recs:
                        rec = _extract(r, "T-13-mine", ref); rec["seed"] = seed_ref
                        if not dd.is_new(rec): continue
                        sc = korea_score(rec["title"]); rec["korea_score"] = sc
                        emit(out, rec); n_new += 1
                        if sc >= promote_threshold and (rec["local_id"] or "").startswith(series):
                            pw.writerow([rec["local_id"], sc, rec["title"][:180], seed_ref, rec["url"]])
                            n_promoted += 1
            except Exception as e:
                log.add("TNA", "T-13-mine", ref, -1, 0, f"ERROR {e}"); continue
            log.add("TNA", "T-13-mine", ref, hits_total, n_new, f"seed={seed_ref}")
            time.sleep(sleep)
    print(f"[Adaptive Mining] 승격 후보 {n_promoted}건 → data/promoted_series.csv (수동 검증 후 정식 편입 — 논문 3단계 승격 관리)")
    log.close(); out.close(); pf.close()
    return n_promoted
