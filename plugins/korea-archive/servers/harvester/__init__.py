# -*- coding: utf-8 -*-
"""korea-records-harvester — 논문(송창기 2026) 방법론의 실행 구현.

구성 (논문 대응):
  nara.py        §4 10단계 수집 파이프라인 (Phase 1~8 재현율 확장, Phase 9 RG 교차 정밀도 회복, Phase 10 통합)
  tna.py         §3.5 TNA 14 전략 레이어 + T-12/13 인용 역추적·인접 확장 (Adaptive Mining 입력)
  extract_llm.py §6 LLM 4계층 의미 추출 (출처 격리 프롬프트 체제)
  util.py        검색 로그(재현성)·중복 제거·HTTP 클라이언트

키워드 정본: ../keywords/ (korea-records-keywords v1.0.0, MIT — 송창기, 국가기록원)
"""
__version__ = "0.1.0"
