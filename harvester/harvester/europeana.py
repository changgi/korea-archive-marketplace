# -*- coding: utf-8 -*-
"""Europeana 배치 수집기 — Search API(무료 키: apis.europeana.eu → EUROPEANA_API_KEY).
다국어 쿼리 세트(확장층) × TYPE 필터, cursor 페이지네이션."""
from __future__ import annotations
import json, os, time, urllib.parse, urllib.request
from .util import UA, SearchLog, Dedup, jsonl_writer, emit, DATA

API = "https://api.europeana.eu/record/v2/search.json"

MULTILINGUAL_QUERIES = [
    "Korea", '"Corée"', '"Korea-Krieg"',                 # 영·불·독
    '"guerra di Corea"', '"guerra de Corea"',            # 이·스
    '"Koreakriget"', '"Korea-oorlog"', '"Kore Savaşı"',  # 스웨덴·네덜란드·터키
    '"Seoul" OR "Séoul"', '"Panmunjom"', '"Inchon" OR "Incheon"',
    '"Chosen" AND (Japan OR Japon)',                     # 전전 표기
]

def _search(key: str, query: str, cursor: str = "*", rows: int = 100,
            media_type: str | None = None):
    params = {"wskey": key, "query": query, "rows": rows, "cursor": cursor,
              "profile": "standard"}
    if media_type: params["qf"] = f"TYPE:{media_type.upper()}"
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())

def _extract(it: dict, query: str) -> dict:
    return {"src": "Europeana", "local_id": it.get("id"),
            "title": str((it.get("title") or ["?"])[0])[:300],
            "date": str((it.get("year") or [""])[0]),
            "type": it.get("type"),
            "provider": str((it.get("dataProvider") or [""])[0])[:80],
            "country": str((it.get("country") or [""])[0]),
            "rights": str((it.get("rights") or [""])[0])[:80],
            "query": query, "url": it.get("guid")}

def run(media_type: str | None = None, max_pages: int = 3, sleep: float = 1.0,
        queries: list[str] | None = None):
    key = os.environ.get("EUROPEANA_API_KEY")
    if not key:
        raise SystemExit("EUROPEANA_API_KEY 필요 — https://apis.europeana.eu/ 에서 무료 발급")
    log = SearchLog(os.path.join(DATA, "search_log_europeana.csv"))
    out = jsonl_writer(os.path.join(DATA, "europeana_records.jsonl"))
    dd = Dedup(); total_new = 0
    for q in (queries or MULTILINGUAL_QUERIES):
        hits_total, n_new, cursor = 0, 0, "*"
        try:
            for _p in range(max_pages):
                data = _search(key, q, cursor=cursor, media_type=media_type)
                hits_total = data.get("totalResults", 0)
                for it in data.get("items") or []:
                    r = _extract(it, q)
                    if dd.is_new(r): emit(out, r); n_new += 1
                cursor = data.get("nextCursor")
                if not cursor: break
                time.sleep(sleep)
        except Exception as e:
            log.add("Europeana", media_type or "ALL", q, -1, 0, f"ERROR {e}"); continue
        log.add("Europeana", media_type or "ALL", q, hits_total, n_new)
        total_new += n_new; time.sleep(sleep)
        print(f"[Europeana] {q} — 전체 {hits_total} / 신규 {n_new}", flush=True)
    print(f"[Europeana] 완료 — 고유 {total_new}건 → data/europeana_records.jsonl")
    log.close(); out.close()
    return total_new
