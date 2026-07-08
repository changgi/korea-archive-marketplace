#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""klactl — kla-collector CLI (보고서 §27 Phase 0 자동화)

  python klactl.py seed                 # §25 검증 시드 17건 대장 등록(§30 권리 자동초판)
  python klactl.py fetch [--max-mb 80] [--limit N]   # archive.org 원본 다운로드+SHA-256
  python klactl.py verify [--limit N]   # §32 링크 재검증 → verified_date
  python klactl.py monitor [--since YYYY-MM-DD]      # 신규 업로드 감지
  python klactl.py dash                 # HTML 대시보드 생성
  python klactl.py stats
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kla.ledger import Ledger
from kla import seeds as S, ia, verify as V, monitor as M, dashboard as D

BASE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(BASE, "data", "ledger.csv")
MASTERS = os.path.join(BASE, "data", "masters")

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("seed"); sub.add_parser("stats"); sub.add_parser("dash")
    f = sub.add_parser("fetch"); f.add_argument("--max-mb", type=int, default=80); f.add_argument("--limit", type=int, default=None)
    v = sub.add_parser("verify"); v.add_argument("--limit", type=int, default=None)
    m = sub.add_parser("monitor"); m.add_argument("--since", default=None)
    a = ap.parse_args()
    os.makedirs(MASTERS, exist_ok=True)
    led = Ledger(LEDGER)

    if a.cmd == "seed":
        n = 0
        for s in S.SEEDS:
            url = (f"https://archive.org/details/{s['ia_id']}" if s.get("ia_id")
                   else f"https://catalog.archives.gov/id/{s['naid']}")
            rec = {k: v for k, v in s.items() if k not in ("ia_id","rights_note_extra")}
            rec["access_url"] = url
            r = led.add(rec)
            if r:
                if s.get("rights_note_extra"): r["rights_note"] += " | " + s["rights_note_extra"]
                n += 1
        # ia_id 매핑 별도 저장
        import json
        json.dump({s["local_id"] if s.get("local_id") else s.get("naid"): s.get("ia_id")
                   for s in S.SEEDS}, open(os.path.join(BASE,"data","ia_map.json"),"w"))
        led.save(); print(f"시드 등록 {n}건 (총 {len(led.rows)}건) → data/ledger.csv")

    elif a.cmd == "fetch":
        import json
        iam = json.load(open(os.path.join(BASE,"data","ia_map.json")))
        done = 0
        for r in led.rows:
            if a.limit and done >= a.limit: break
            if r["file_path"]: continue
            ia_id = iam.get(r["local_id"]) or iam.get(r["naid"])
            if not ia_id: continue
            print(f"⬇ {r['collection_id']} {ia_id} …", flush=True)
            try:
                res = ia.download(ia_id, r, MASTERS, max_bytes=a.max_mb*1024*1024)
            except Exception as e:
                print(f"   ERROR {e}"); continue
            if not res: print("   원본 영상 파일 없음"); continue
            if res.get("skipped"):
                r["acq_status"] = "발주(대용량 보류)"
                print(f"   보류: {res['name']} {res['size']/1e6:.0f}MB > --max-mb")
            else:
                r["file_path"] = os.path.relpath(res["path"], BASE)
                r["checksum"] = res["sha256"]; r["acq_status"] = "QC대기"
                print(f"   저장 {res['size']/1e6:.1f}MB sha256={res['sha256'][:12]}…")
            done += 1; led.save(); time.sleep(0.8)
        led.save(); print("완료")

    elif a.cmd == "verify":
        res = V.run(led, limit=a.limit); led.save(); print("검증 결과:", res)
    elif a.cmd == "monitor":
        hits = M.run(since=a.since)
        for h in hits[:15]: print("  🆕", h["identifier"], "|", (h["title"] or "")[:60])
    elif a.cmd == "dash":
        p = D.build(led, os.path.join(BASE, "data", "dashboard.html")); print("→", p)
    elif a.cmd == "stats":
        print(led.stats())

if __name__ == "__main__":
    main()
