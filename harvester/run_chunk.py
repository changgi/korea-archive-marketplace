#!/usr/bin/env python3
"""재개 가능 청크 러너 — 호출당 BUDGET초 실행 후 종료, 검색 로그로 이어달리기."""
import sys, os, csv, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harvester.tna as t
DEMO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "demo")
t.DATA = DEMO
BUDGET = 30

# ── 작업 계획: T-01 전체 + T-04 앞 15 + T-12 전체 + 마이닝(21시드 ±1) ──
import keywords_tna as K
plan = []
for lid, stype, qs_ in K.generate():
    if lid == "T-01": plan += [("L", lid, q) for q in qs_]
    if lid == "T-04": plan += [("L", lid, q) for q in qs_[:15]]
    if lid == "T-12": plan += [("L", lid, q) for q in qs_]
import re
for seed, src in K.CITATION_SEEDS:
    m = re.match(r"([A-Z]+ \d+)/(\d+)", seed)
    if not m: continue
    s, p = m.group(1), int(m.group(2))
    for i in range(p-1, p+2):
        plan.append(("M", seed, f"{s}/{i}"))

# ── 완료 목록 로드 ──
done = set()
lp = os.path.join(DEMO, "search_log_tna.csv")
if os.path.exists(lp):
    for row in csv.DictReader(open(lp, encoding="utf-8-sig")):
        if row["hits"] != "-1": done.add((row["phase_or_layer"], row["query"]))

todo = [(k, a, q) for k, a, q in plan
        if ((a if k=="L" else "T-13-mine"), q) not in done]
print(f"계획 {len(plan)} | 완료 {len(plan)-len(todo)} | 남음 {len(todo)}", flush=True)
if not todo:
    print("ALL-DONE"); sys.exit(0)

from harvester.util import SearchLog, Dedup, jsonl_writer, emit
log = SearchLog(lp)
out = jsonl_writer(os.path.join(DEMO, "tna_records.jsonl"))
mout = jsonl_writer(os.path.join(DEMO, "tna_mined.jsonl"))
pf = open(os.path.join(DEMO, "promoted_series.csv"), "a", newline="", encoding="utf-8-sig")
pw = csv.writer(pf)
if os.path.getsize(os.path.join(DEMO, "promoted_series.csv")) == 0:
    pw.writerow(["reference","score","title","seed","url"])

# 전역 dedup: 기존 jsonl 재적재
dd = Dedup()
for f in ("tna_records.jsonl", "tna_mined.jsonl"):
    fp = os.path.join(DEMO, f)
    if os.path.exists(fp):
        for line in open(fp, encoding="utf-8"):
            try: dd.is_new(json.loads(line))
            except Exception: pass

t0 = time.time(); n_done = 0
for kind, a, q in todo:
    if time.time() - t0 > BUDGET: break
    try:
        if kind == "L":
            hits_total, n_new = 0, 0
            for recs, total in t._search(f'"{q}"' if a == "T-12" else q, max_pages=1, sleep=0.4):
                hits_total = total
                for r in recs:
                    rec = t._extract(r, a, q)
                    if dd.is_new(rec): emit(out, rec); n_new += 1
            log.add("TNA", a, q, hits_total, n_new)
        else:
            hits_total, n_new = 0, 0
            for recs, total in t._search(f'"{q}"', max_pages=1, sleep=0.4):
                hits_total = total
                for r in recs:
                    rec = t._extract(r, "T-13-mine", q); rec["seed"] = a
                    if not dd.is_new(rec): continue
                    sc = t.korea_score(rec["title"] + " " + rec.get("description","")); rec["korea_score"] = sc
                    emit(mout, rec); n_new += 1
                    if sc >= 1 and (rec["local_id"] or "").startswith(q.split("/")[0]):
                        pw.writerow([rec["local_id"], sc, rec["title"][:180], a, rec["url"]]); pf.flush()
            log.add("TNA", "T-13-mine", q, hits_total, n_new, f"seed={a}")
    except Exception as e:
        log.add("TNA", a if kind=="L" else "T-13-mine", q, -1, 0, f"ERROR {e}")
    n_done += 1
    time.sleep(0.4)
print(f"이번 청크 처리 {n_done} | 경과 {time.time()-t0:.0f}s", flush=True)
log.close(); out.close(); mout.close(); pf.close()
