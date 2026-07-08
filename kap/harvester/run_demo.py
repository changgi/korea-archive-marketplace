#!/usr/bin/env python3
# 실전 데모: T-01(핵심 직접 19쿼리 전체) + T-04(FO 371 코드 레이어 전체) + T-12(인용 시드)
# + Adaptive Mining 21시드 ±3 — 산출물은 data/demo/ 에 격리
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harvester.tna as t
DEMO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "demo")
t.DATA = DEMO  # 산출 디렉토리 오버라이드

print("=== 1) TNA 레이어 실수집: T-01 + T-04 + T-12 ===", flush=True)
stats = t.run_layers(layers=["T-01", "T-04", "T-12"], max_pages=1, sleep=0.7)
print("레이어 통계:", stats, flush=True)

print("\n=== 2) Adaptive Mining: 21개 시드 전체, 인접 ±3 ===", flush=True)
n = t.adaptive_mine(rng=2, sleep=0.7)
print("승격 후보:", n, flush=True)

# 3) 집계
recs = [json.loads(l) for l in open(os.path.join(DEMO, "tna_records.jsonl"), encoding="utf-8")]
mined = [json.loads(l) for l in open(os.path.join(DEMO, "tna_mined.jsonl"), encoding="utf-8")]
from collections import Counter
print("\n=== 집계 ===", flush=True)
print("레이어 수집 고유 레코드:", len(recs))
print("부처(department) 분포:", Counter(r.get("department") for r in recs).most_common(8))
print("마이닝 순회 레코드:", len(mined))
print("완료 시각:", time.strftime("%H:%M:%S"), flush=True)
