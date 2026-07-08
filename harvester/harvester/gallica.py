# -*- coding: utf-8 -*-
"""Gallica(BnF) 배치 수집기 — SRU API(키 불요), 프랑스어 쿼리 세트.

프랑스어 세트는 논문 정본(keywords/) 외부의 확장층이다(구한말 프랑스 사료 특화).
병인양요(1866)·선교사·외교 문헌을 포괄한다.
"""
from __future__ import annotations
import os, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from .util import UA, SearchLog, Dedup, jsonl_writer, emit, DATA

SRU = "https://gallica.bnf.fr/SRU"
NS = {"srw": "http://www.loc.gov/zing/srw/", "dc": "http://purl.org/dc/elements/1.1/"}

# 확장층: 프랑스어 쿼리 세트 (F-01 직접 / F-02 사건 / F-03 인물·기관 / F-04 시각자료)
FRENCH_QUERIES = [
    # F-01 직접
    '"Corée"', '"Coréens"', '"la Corée"', '"Séoul"', '"Tchosen"',
    '"presqu\'île de Corée"', '"royaume de Corée"',
    # F-02 사건
    '"expédition de Corée"',                      # 병인양요 1866
    '"guerre de Corée"',                          # 한국전쟁
    '"martyrs de Corée"',                         # 천주교 순교
    '"Corée" "guerre russo-japonaise"',
    '"annexion" "Corée"',                         # 병합
    '"armistice" "Corée"', '"Panmunjom"',
    # F-03 인물·기관
    '"missionnaires" "Corée"',                    # 파리외방전교회
    '"Missions étrangères" "Corée"',
    '"bataillon français" "Corée"',               # 프랑스 대대 (몽클라르)
    '"Mgr" "Corée"',                              # 주교 문헌
    # F-04 지명 변형
    '"Fusan"', '"Chemulpo"', '"Gensan" "Corée"', '"Quelpaert"',   # 제주=Quelpaert(프)
]

def _sru(query: str, start: int = 1, rows: int = 50):
    q = urllib.parse.quote(f"gallica all {query}")
    url = (f"{SRU}?operation=searchRetrieve&version=1.2&query={q}"
           f"&startRecord={start}&maximumRecords={rows}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return ET.fromstring(r.read().decode("utf-8", "replace"))

def _extract(rec, query: str) -> dict:
    def g(tag):
        e = rec.find(f".//dc:{tag}", NS)
        return (e.text or "").strip() if e is not None and e.text else ""
    ident = g("identifier")
    return {"src": "Gallica", "local_id": ident.rsplit("/", 1)[-1] if "ark:" in ident else ident,
            "title": g("title")[:300], "date": g("date"), "type": g("type"),
            "lang": g("language"), "query": query, "url": ident}

def run(max_pages: int = 2, rows: int = 50, sleep: float = 1.0,
        queries: list[str] | None = None, date_max: str = "1965"):
    """프랑스어 세트 실행 → data/gallica_records.jsonl + search_log_gallica.csv.
    date_max: 연대 상한 문자열 비교로 현대 출판물 잡음 감소(빈 연도는 유지)."""
    log = SearchLog(os.path.join(DATA, "search_log_gallica.csv"))
    out = jsonl_writer(os.path.join(DATA, "gallica_records.jsonl"))
    dd = Dedup(); total_new = 0
    for q in (queries or FRENCH_QUERIES):
        hits_total, n_new, start = 0, 0, 1
        try:
            for _p in range(max_pages):
                root = _sru(q, start=start, rows=rows)
                n = root.find(".//srw:numberOfRecords", NS)
                hits_total = int(n.text) if n is not None and n.text else 0
                recs = root.findall(".//srw:record", NS)
                for rec in recs:
                    r = _extract(rec, q)
                    y = (r.get("date") or "")[:4]
                    if y.isdigit() and y > date_max: continue
                    if dd.is_new(r): emit(out, r); n_new += 1
                start += rows
                if start > hits_total or not recs: break
                time.sleep(sleep)
        except Exception as e:
            log.add("Gallica", "F-set", q, -1, 0, f"ERROR {e}"); continue
        log.add("Gallica", "F-set", q, hits_total, n_new)
        total_new += n_new; time.sleep(sleep)
        print(f"[Gallica] {q} — 전체 {hits_total} / 신규 {n_new}", flush=True)
    print(f"[Gallica] 완료 — 고유 {total_new}건 → data/gallica_records.jsonl")
    log.close(); out.close()
    return total_new
