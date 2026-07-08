# -*- coding: utf-8 -*-
"""NARA 10단계 수집 파이프라인 (논문 §4 — 8개 주제 단계로 재현율 확장, Phase 9 RG 교차로 정밀도 회복).

API: NARA Catalog API v2 (x-api-key 필수 — Catalog_API@nara.gov 발급, 월 10,000쿼리).
     엔드포인트·파라미터는 https://catalog.archives.gov/api/v2/api-docs/ 기준.
"""
from __future__ import annotations
import time
import os, sys
_here = os.path.dirname(os.path.abspath(__file__))
for _cand in (os.path.join(os.path.dirname(_here), "keywords"),
              os.path.join(os.path.dirname(os.path.dirname(_here)), "keywords")):
    if os.path.isdir(_cand) and _cand not in sys.path:
        sys.path.insert(0, _cand)

from keywords_common import COMMON_GROUPS          # 22그룹 403
from keywords_nara import NARA_GROUPS, ONLINE_PRIORITY, RG_MAP  # 8그룹 136 + RG 28×63
from .util import http_json, qs, SearchLog, Dedup, jsonl_writer, emit, DATA

API = "https://catalog.archives.gov/api/v2/records/search"
G = {gid: kws for gid, _ko, _en, _dim, kws in COMMON_GROUPS}

# 논문 10단계 편성: Phase 1~8 = 재현율 확장(주제 단계), 9 = RG 교차(정밀도), 10 = 통합
PHASES = [
    ("P1-core",      G["G-01"]),
    ("P2-war",       G["G-02"] + G["G-03"] + G["G-04"] + G["G-05"] + G["G-06"]),
    ("P3-period",    G["G-07"] + G["G-08"] + G["G-09"] + G["G-10"]),
    ("P4-people",    G["G-11"] + G["G-12"]),
    ("P5-society",   G["G-13"] + G["G-14"] + G["G-15"] + G["G-16"]),
    ("P6-indirect",  G["G-17"] + G["G-18"] + G["G-19"]),
    ("P7-visual",    G["G-20"] + G["G-21"] + G["G-22"]),
    ("P8-nara",      sum((kws for _gid, _ko, _en, kws in NARA_GROUPS), []) + ONLINE_PRIORITY),
]

def _extract(hit: dict) -> dict:
    rec = (hit.get("_source") or {}).get("record") or hit.get("record") or hit
    digital = bool(rec.get("digitalObjects"))
    return {
        "src": "NARA",
        "naid": rec.get("naId"),
        "local_id": rec.get("localIdentifier"),
        "title": rec.get("title"),
        "date": (rec.get("productionDates") or [{}])[0].get("logicalDate", "")[:10]
                 if rec.get("productionDates") else "",
        "rg": (rec.get("recordGroupNumber") or
               ((rec.get("ancestors") or [{}])[0].get("recordGroupNumber") if rec.get("ancestors") else None)),
        "level": rec.get("levelOfDescription"),
        "types": rec.get("generalRecordsTypes"),
        "online": "online" if digital else "offline",
        "url": f"https://catalog.archives.gov/id/{rec.get('naId')}" if rec.get("naId") else None,
    }

def _search(api_key: str, params: dict, max_pages: int, sleep: float):
    page = 1
    while page <= max_pages:
        data = http_json(API + "?" + qs({**params, "limit": 100, "page": page}),
                         headers={"x-api-key": api_key})
        hits_obj = ((data.get("body") or {}).get("hits") or data.get("hits") or {})
        hits = hits_obj.get("hits") or []
        total = (hits_obj.get("total") or {})
        total = total.get("value", 0) if isinstance(total, dict) else total
        yield hits, total
        if page * 100 >= (total or 0) or not hits: break
        page += 1; time.sleep(sleep)

def run(api_key: str | None = None, moving_images_only: bool = False,
        online_only: bool = False, max_pages: int = 3, sleep: float = 1.0,
        phases: list[str] | None = None, max_queries_per_phase: int | None = None):
    """Phase 1~9 실행 → data/nara_records.jsonl + data/search_log_nara.csv.
    api_key 미지정 시 환경변수 NARA_API_KEY 사용. max_pages·max_queries_per_phase로 파일럿 조절.
    """
    api_key = api_key or os.environ.get("NARA_API_KEY")
    if not api_key:
        raise SystemExit("NARA_API_KEY 필요 — Catalog_API@nara.gov 로 발급 요청 (본 보고서 §31-2 템플릿)")
    log = SearchLog(os.path.join(DATA, "search_log_nara.csv"))
    out = jsonl_writer(os.path.join(DATA, "nara_records.jsonl"))
    dd = Dedup(); stats = {}
    base = {}
    if moving_images_only: base["typeOfMaterials"] = "Moving Images"
    if online_only: base["availableOnline"] = "true"

    # ── Phase 1~8: 주제 단계 (재현율 확장) ──
    for phase, kws in PHASES:
        if phases and phase not in phases: continue
        n_new_phase = 0
        for kw in (kws[:max_queries_per_phase] if max_queries_per_phase else kws):
            hits_total, n_new = 0, 0
            try:
                for hits, total in _search(api_key, {**base, "q": kw}, max_pages, sleep):
                    hits_total = total
                    for h in hits:
                        rec = _extract(h); rec["phase"] = phase; rec["query"] = kw
                        if dd.is_new(rec): emit(out, rec); n_new += 1
            except Exception as e:
                log.add("NARA", phase, kw, -1, 0, f"ERROR {e}"); continue
            log.add("NARA", phase, kw, hits_total, n_new)
            n_new_phase += n_new; time.sleep(sleep)
        stats[phase] = n_new_phase
        print(f"[{phase}] 신규 {n_new_phase}건")

    # ── Phase 9: RG 교차 (정밀도 회복 — 63 결합 쿼리) ──
    if not phases or "P9-rgcross" in (phases or []):
        n_new_phase = 0
        for rg, (desc, kws) in RG_MAP.items():
            for kw in kws:
                hits_total, n_new = 0, 0
                try:
                    for hits, total in _search(api_key, {**base, "q": kw, "recordGroupNumber": rg},
                                               max_pages, sleep):
                        hits_total = total
                        for h in hits:
                            rec = _extract(h); rec["phase"] = "P9-rgcross"; rec["query"] = f"RG{rg}+{kw}"
                            if dd.is_new(rec): emit(out, rec); n_new += 1
                except Exception as e:
                    log.add("NARA", "P9-rgcross", f"RG{rg}+{kw}", -1, 0, f"ERROR {e}"); continue
                log.add("NARA", "P9-rgcross", f"RG{rg}+{kw}", hits_total, n_new)
                n_new_phase += n_new; time.sleep(sleep)
        stats["P9-rgcross"] = n_new_phase
        print(f"[P9-rgcross] 신규 {n_new_phase}건")

    # ── Phase 10: 통합 보고 ──
    total_new = sum(stats.values())
    print(f"\n[P10] 통합: 고유 레코드 {total_new}건 → data/nara_records.jsonl")
    log.close(); out.close()
    return stats
