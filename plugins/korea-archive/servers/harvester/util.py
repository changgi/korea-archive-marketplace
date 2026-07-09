# -*- coding: utf-8 -*-
"""공통 유틸 — HTTP(표준 라이브러리만), 검색 로그, 중복 제거, JSONL 저장."""
from __future__ import annotations
import csv, json, os, time, urllib.parse, urllib.request, urllib.error

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"  # TNA Discovery가 bot형 UA를 403 처리하므로 브라우저형 UA 사용. sleep으로 요청 간격 준수.
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def http_json(url: str, headers: dict | None = None, retries: int = 3, backoff: float = 2.0):
    """GET → JSON. 429/5xx 지수 백오프, 그 외 HTTPError는 (status, body) 반환용 예외 전달."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", **(headers or {})})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(backoff * (attempt + 1)); continue
            raise
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1)); continue
            raise

def qs(params: dict) -> str:
    return urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}, quote_via=urllib.parse.quote)

class SearchLog:
    """§12 검색 로그 표준 서식 — 로그 없는 검색은 수행하지 않은 것으로 간주한다."""
    FIELDS = ["log_id", "ts", "source", "phase_or_layer", "query", "hits", "new_records", "note"]
    def __init__(self, path: str):
        self.path = path; self.n = 0
        new = not os.path.exists(path)
        self.f = open(path, "a", newline="", encoding="utf-8-sig")
        self.w = csv.writer(self.f)
        if new: self.w.writerow(self.FIELDS)
    def add(self, source, phase, query, hits, new_records, note=""):
        self.n += 1
        self.w.writerow([f"Q-{self.n:05d}", time.strftime("%Y-%m-%dT%H:%M:%S"),
                         source, phase, query, hits, new_records, note])
        self.f.flush()
    def close(self): self.f.close()

class Dedup:
    """식별자 3중 키(local_id → naid/tna_id → 제목+연도) 중복 제거 (보고서 §28 규칙)."""
    def __init__(self): self.seen = set()
    def key(self, rec: dict) -> str:
        for k in ("local_id", "naid", "tna_id"):
            v = rec.get(k)
            if v: return f"{k}:{str(v).lower()}"
        return "tt:" + (rec.get("title", "") or "").lower()[:120] + "|" + str(rec.get("date", ""))
    def is_new(self, rec: dict) -> bool:
        k = self.key(rec)
        if k in self.seen: return False
        self.seen.add(k); return True

def jsonl_writer(path: str):
    return open(path, "a", encoding="utf-8")

def emit(f, rec: dict):
    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
