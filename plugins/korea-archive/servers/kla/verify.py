# -*- coding: utf-8 -*-
"""§25/§32 링크 분기 재검증 — access_url 생존 + (archive.org면) 제목 대조 → verified_date 갱신."""
from __future__ import annotations
import re, time, urllib.request
from .ia import UA, metadata

def check(url: str, timeout=25) -> tuple[str, str]:
    """(판정, 비고) — OK / WARN / FAIL"""
    try:
        m = re.match(r"https?://archive\.org/details/([^/?#]+)", url or "")
        if m:
            md = metadata(m.group(1))
            if md.get("metadata"):
                return "OK", (md["metadata"].get("title") or "")[:80]
            return "FAIL", "metadata 없음(아이템 소멸?)"
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return ("OK" if r.status == 200 else "WARN"), f"HTTP {r.status}"
    except Exception as e:
        return "FAIL", f"{type(e).__name__}: {e}"[:90]

def run(ledger, sleep=0.6, limit=None) -> dict:
    today = time.strftime("%Y-%m-%d"); res = {"OK":0,"WARN":0,"FAIL":0}
    n = 0
    for r in ledger.rows:
        if not r.get("access_url"): continue
        if r.get("verified_date") == today: continue   # 오늘 검증분 스킵(재개 가능)
        if f"[검증{today}] FAIL" in (r.get("rights_note") or ""): continue  # 오늘 FAIL도 스킵(수동 확인 대상)
        if limit and n >= limit: break
        v, note = check(r["access_url"]); n += 1; res[v] += 1
        if v == "OK": r["verified_date"] = today
        else: r["rights_note"] = (r.get("rights_note","") + f" | [검증{today}] {v}: {note}")[:500]
        print(f"  {v:4} {r['collection_id']} {r['access_url'][:60]} — {note[:60]}", flush=True)
        ledger.save()   # 항목별 즉시 저장(§32 — 기록되지 않은 작업은 없었던 작업)
        time.sleep(sleep)
    return res
