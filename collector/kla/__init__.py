# -*- coding: utf-8 -*-
"""kla-collector — 「한국 광복·해방·한국전쟁 영상자료 글로벌 아카이브 종합 보고서 v6.5」
실행편(§25~32)의 코드 구현. Phase 0(무예산 즉시실행)을 자동화한다.

모듈 ↔ 보고서 대응:
  ledger.py   §28 수집대장 17필드 + 3중 키 중복 방지 + §30 권리 등급 자동 초기판정
  seeds.py    §25 검증 완료 시드 영상 (2026.7 링크 전수검증 통과분)
  ia.py       §27 Phase 0 — archive.org 메타데이터·검색·원본 다운로드·SHA-256
  naracat.py  NARA 카탈로그 공개 페이지 메타 등록 (API 키 없이 가능한 범위)
  verify.py   §25/§32 링크 분기 재검증 (verified_date 갱신)
  monitor.py  §27 주간 모니터링 — 신규 업로드 감지
  dashboard.py 수집 현황 HTML 대시보드 (§27 KPI 표 대응)
"""
__version__ = "0.1.0"
