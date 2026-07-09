<<<<<<< HEAD
# 🇰🇷 Korea Archive Project — 해외 소재 한국 영상·기록 발굴 통합 패키지

한국 광복·해방·한국전쟁(1910–1960) 관련 영상·기록물을 전 세계 아카이브에서
**조사 → 발굴 → 확보 → 관리**하는 전 과정을 담은 배포판입니다.
7개 선행 보고서의 통합(v6.5), 600+ 쿼리 코퍼스, 그리고 논문
(송창기 2026, 국가기록원 — F1 0.931 실증 방법론)의 실행 구현을 하나로 묶었습니다.

## 구성

| 디렉토리 | 내용 | 상태 |
|---|---|---|
| `docs/` | 📘 종합 보고서 v6.5 (32섹션·136 아카이브·실행편) · 📗 마스터 쿼리 코퍼스 v1.1 (600+ 쿼리·13섹션) | HTML — 브라우저로 열기 |
| `keywords/` | 계층적 키워드 정본 44그룹 1,943항목 (korea-records-keywords v1.0.0, MIT © Song Chang-Gi) | 공유 라이브러리 |
| `harvester/` | NARA 10단계 파이프라인 + TNA 14레이어 + Adaptive Mining (논문 구현) | ✅ TNA 실수집 1,214건 + 승격후보 73건 동봉 (`results/demo/`) |
| `collector/` | 확보·수집대장(17필드)·권리 자동판정·링크 재검증·대시보드 (보고서 §25~32 구현) | ✅ 시드 17건 대장·대시보드 동봉 (`data/`) |
| `mcp/` | 🔌 MCP 서버 — Claude 등 AI 에이전트에 발굴 도구 장착 | `mcp/README.md` 참조 |
| `skill/` | 🧩 Claude 스킬 — 쿼리 전략·발굴 노하우를 에이전트 지식으로 장착 | `.skill` 파일 설치 |
| `scripts/` | 퀵스타트 | — |

## 5분 퀵스타트 (의존성 없음, Python 3.10+)

```bash
# 1) TNA(영국 국립기록관) 발굴 — 키 불요
cd harvester && python cli.py tna --pilot && python cli.py mine

# 2) 확보·대장 관리 (archive.org)
cd ../collector && python klactl.py seed && python klactl.py verify && python klactl.py dash
#    → data/dashboard.html 을 브라우저로

# 3) NARA (API 키: Catalog_API@nara.gov — 보고서 §31-2 이메일 템플릿)
NARA_API_KEY=... python ../harvester/cli.py nara --moving-images --pilot
```

## 워크플로우

```
docs/ 보고서·코퍼스 (전략·쿼리) ──▶ harvester/ (NARA·TNA 발굴)
                                        │  promoted_series.csv (승격 후보 → 사람 검증)
                                        ▼
                                  collector/ (확보·SHA-256·권리등급·대장·대시보드)
```

## 출처·인용

- 방법론·키워드: 송창기(2026), *An AI-based Systematic Methodology for Discovering and
  Semantically Extracting Korea-related Records from Foreign Archives*, 국가기록원. (`keywords/LICENSE`)
- 보고서·코퍼스·구현 코드: 본 프로젝트 (MIT — `LICENSE`).
- 모든 NAID·참조코드·URL은 2026-07-07 웹 검증 기준 (보고서 §25).

## 운용 3원칙 (요약)

1. **로그 없는 검색 금지** — 모든 쿼리는 자동 기록된다(재현성).
2. **권리 자동판정은 초기판정** — 공개 전 §30 5단계 수동 확정, D등급 공개 금지.
3. **0건 ≠ 부재** — 온라인 미검출은 현장·대행 조사 목록으로 이월(보고서 §27 Phase 1).
=======
# Korea Archive Marketplace

Claude 플러그인 마켓플레이스 — 해외 소재 한국 기록 발굴 도구.

## 사용자 설치 (GitHub 공개 후)
```
/plugin marketplace add <github-사용자명>/korea-archive-marketplace
/plugin install korea-archive@korea-archive-marketplace
```

## 게시자 배포 절차
1. 이 저장소를 GitHub에 공개 리포지토리로 push
2. 위 두 명령을 사용자에게 안내 (Claude Code·Cowork 공통)
3. 플러그인 갱신 시 plugins/korea-archive/ 수정 후 plugin.json·marketplace.json의 version 올리고 push
>>>>>>> 03c5d845ca77a852d711523aeec7dac6dfe6f8b4
