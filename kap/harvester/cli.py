#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""korea-records-harvester CLI — 논문(송창기 2026) 파이프라인 실행 진입점.

사용 예:
  python cli.py tna --pilot                 # TNA 14레이어 파일럿(레이어당 3쿼리)
  python cli.py tna                          # TNA 전체 1,222 쿼리
  python cli.py mine                         # T-12/13 인용 역추적 + 인접 확장 (Adaptive Mining)
  NARA_API_KEY=... python cli.py nara --moving-images --pilot
  ANTHROPIC_API_KEY=... python cli.py extract data/tna_records.jsonl --limit 20
"""
import argparse, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harvester import nara, tna, gallica, europeana
from harvester import extract_llm

def main():
    ap = argparse.ArgumentParser(description="Korea-records harvester (paper implementation)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("nara", help="NARA 10단계 파이프라인 (P1~P9)")
    p.add_argument("--api-key", default=None)
    p.add_argument("--moving-images", action="store_true", help="Moving Images 한정")
    p.add_argument("--online-only", action="store_true")
    p.add_argument("--pilot", action="store_true", help="단계당 5쿼리·1페이지 파일럿")
    p.add_argument("--max-pages", type=int, default=3)

    t = sub.add_parser("tna", help="TNA 14 전략 레이어")
    t.add_argument("--layers", nargs="*", default=None, help="예: T-01 T-04 T-12")
    t.add_argument("--pilot", action="store_true", help="레이어당 3쿼리·1페이지 파일럿")

    m = sub.add_parser("mine", help="T-12/13 인용 역추적 + 인접 확장 (Adaptive Mining)")
    m.add_argument("--range", type=int, default=None, help="인접 반경 (기본 15 — 논문값)")

    g = sub.add_parser("gallica", help="Gallica(BnF) 프랑스어 세트 수집 — 키 불요")
    g.add_argument("--pilot", action="store_true", help="쿼리 5개·1페이지")
    g.add_argument("--max-pages", type=int, default=2)

    u = sub.add_parser("europeana", help="Europeana 다국어 세트 수집 — EUROPEANA_API_KEY")
    u.add_argument("--type", default=None, help="VIDEO|IMAGE|TEXT|SOUND")
    u.add_argument("--pilot", action="store_true")

    e = sub.add_parser("extract", help="LLM 4계층 의미 추출 (출처 격리)")
    e.add_argument("input", help="data/*.jsonl")
    e.add_argument("--limit", type=int, default=None)

    a = ap.parse_args()
    if a.cmd == "nara":
        nara.run(api_key=a.api_key, moving_images_only=a.moving_images,
                 online_only=a.online_only,
                 max_pages=1 if a.pilot else a.max_pages,
                 max_queries_per_phase=5 if a.pilot else None)
    elif a.cmd == "tna":
        tna.run_layers(layers=a.layers,
                       max_queries_per_layer=3 if a.pilot else None,
                       max_pages=1)
    elif a.cmd == "mine":
        from keywords_tna import ADJACENT_RANGE
        tna.adaptive_mine(rng=a.range or ADJACENT_RANGE)
    elif a.cmd == "gallica":
        gallica.run(max_pages=1 if a.pilot else a.max_pages,
                    queries=gallica.FRENCH_QUERIES[:5] if a.pilot else None)
    elif a.cmd == "europeana":
        europeana.run(media_type=a.type, max_pages=1 if a.pilot else 3,
                      queries=europeana.MULTILINGUAL_QUERIES[:5] if a.pilot else None)
    elif a.cmd == "extract":
        extract_llm.run(a.input, limit=a.limit)

if __name__ == "__main__":
    main()
