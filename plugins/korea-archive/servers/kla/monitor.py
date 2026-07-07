# -*- coding: utf-8 -*-
"""§27 4주차·§32 주간 모니터링 — 컬렉션 신규 업로드 감지 → 후보 목록."""
from __future__ import annotations
import time
from .ia import search
from .seeds import SWEEP_COLLECTIONS

def run(since: str | None = None, rows=50) -> list[dict]:
    since = since or time.strftime("%Y-%m-01")
    out = []
    for col in SWEEP_COLLECTIONS:
        q = f"collection:{col} AND (korea OR korean OR chosen OR seoul) AND addeddate:[{since} TO null]"
        try:
            docs = (search(q, rows=rows).get("response") or {}).get("docs") or []
        except Exception as e:
            print(f"  [{col}] ERROR {e}"); continue
        for d in docs:
            out.append({"collection": col, "identifier": d.get("identifier"),
                        "title": d.get("title"), "addeddate": d.get("addeddate")})
        print(f"  [{col}] {since} 이후 신규 {len(docs)}건")
        time.sleep(0.8)
    return out
