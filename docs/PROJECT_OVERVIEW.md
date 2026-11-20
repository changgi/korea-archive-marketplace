# 코리아 아카이브 — 프로젝트 갈무리 (현황 브리핑)

> 작성: 2026-11-17 · 기준 버전 v1.16.0 · 라이선스 MIT · 방법론 송창기(2026)
> 이 문서는 "지금까지 만든 것"의 구조·기능·쓰임새·성능과 다음 작업을 한곳에 정리한 스냅샷이다.
> 수치는 **논문 지표 / 코드 실측 / 실전 사례**를 구분해 표기한다.

## 0. 한 줄 정의

국내외 **15개 아카이브**에 당대 어휘로 색인돼 일반 검색으로는 나오지 않는 한국 근현대 기록
(1860–1960, 조선 사료 1485~)을 **클로드 한 대화로 발굴 → 판독 → 산출물화**하는
**MCP 도구 20종 + 스킬 11종**의 플러그인 / 원격 커넥터.

사용자 접점 두 가지:
- **플러그인** (데스크탑·Claude Code): `/plugin install korea-archive@korea-archive-marketplace`
- **원격 MCP 커넥터** (웹·모바일): `https://korea-archive-mcp.vercel.app/api/mcp`

---

## 1. 구조 (System & Repo)

### 두 저장소 패리티
| 저장소 | 성격 | 핵심 |
|---|---|---|
| **`korea-archive-marketplace`** (이 저장소) | Python 플러그인 + 마켓플레이스 | 캐노니컬 서버 `plugins/korea-archive/servers/server.py` (20도구, stdio) |
| **`korea-archive-mcp`** (자매 저장소) | Node / Vercel 원격 서버 (리전 icn1) | 웹·모바일 커넥터 + 웹 서비스(/help·/ingitda) |

두 서버는 **도구·공유상수(`_TOPICS` 다국어 변환, 보고서 규칙) 패리티**를 유지해야 한다.
현재 양쪽 `server.py` 모두 20도구로 동기화됨(커밋 `e8e7a21`로 `mcp/server.py` 현행화 완료).

### 5개 레이어
| 레이어 | 위치 | 역할 |
|---|---|---|
| MCP 서버 | `servers/server.py` (+벤더 `harvester`/`keywords`/`kla`, `joseon_tools.py`) | 20도구 실행 엔진 |
| 지식 코퍼스 | `keywords/` (`keywords_*`·`profile_*`·`profiles.py`) | `query_bank`·`source_profile`의 단일 진실원 |
| 연구 파이프라인 CLI | `harvester/`(논문 10단계·14레이어), `collector/`(수집대장·권리판정·대시보드) | 배치 발굴·대장 관리 |
| 스킬 11종 | `plugins/korea-archive/skills/` | 로컬 전용 노하우 (발굴→판독→제작) |
| 점검 | `scripts/selfcheck.py`·`selfcheck_ext.py` | 기관 사이트 개편 시 접근경로 회귀 탐지 |

### 설계 제1원칙
**"지식은 서버로, 실행은 환경별 경로로."** 스킬(로컬 전용)에만 노하우를 두면 웹에 없으므로,
반드시 MCP 도구(`report_template` kind, MCP prompts)로도 노출한다.
**PlayMCP 제약**: 도구 ≤20개(이미 상한 — 새 기능은 enum 모드로 확장), 응답 ≤24KB.

---

## 2. 기능 (도구 20종)

**해외 6** `tna_search` · `tna_adjacent_mine`(인접 채굴) · `nara_search`(RG 교차) · `ia_search` · `gallica_search` · `europeana_search`
**국내 9** `nedb_search`(한국사DB·**9모드**) · `archives_search` · `nlk_search` · `seoul_archives_search` · `foia_search` · `warmemo_search` · `koreanwar_search`/`koreanwar_item`(6·25 아카이브센터 — **MOU 협약기관**) · `scrape_plan`
**유틸 5** `query_bank` · `judge_rights`(권리 A/B/C/D) · `report_template`(**kind 8종**) · `cross_search`(동시 교차수집) · `source_profile`(기관 프로파일)

### 핵심 메커니즘
1. **구조적 부정합 대응** — ①언어(Keijo·Fusan·Chosen 표기변형 병렬) ②분류(RG·FO 371 코드 교차) ③기술관행("0건 ≠ 부재" → 인접 채굴).
2. **다국어 자동 변환 `_TOPICS`** — 한·일·중·러·아랍 등 어떤 언어 질의도 대상 아카이브 색인어(영/불)로 변환.
3. **조선 사료 심층판독 (nedb 9모드)** — 법전 조문·座目 필터·★형제 조 전수·법전 수록 대조·어휘 연원·승정원일기·규장각.
4. **매직 키워드(웹 네이티브)** — "○○ 풀패키지로 만들어줘" → 산출물 12종 자동 / "창기창기 도와줘" → 사용 안내.

### 발굴 → 판독 핸드오프 (스킬)
`korea-archive-discovery`(찾기) → `archival-discovery-pipeline`(실물 열기: 프레임분석·OCR+VLM·재기술·게재윤리·RiC-O/KARDA 온톨로지) → `insta-carousel`/`korea-full-package`(제작).
도메인 스킬: `joseon-source-mining`·`joseon-source-excavation`·`kyujanggak-images`·`khdb-citation`·`nanet-citation`·`record-annotation`·`changgi-help`. **(디스크 실측 11종)**

---

## 3. 쓰임새

- **연구자** — 해외 흩어진 사료를 당대 표기로 발굴 + 국내 1차사료 교차검증 + 논문 도판·인용.
- **아카이브·전시** — 발굴 → 권리판정 → 매거진 보고서·전시 도판·기록 해설 카드.
- **교육·대중화** — 카드뉴스(1080²)·입문형·메시지형·시연 영상.
- **저널리즘·SNS** — 실물 기록 기반(AI 생성 인물·장면 금지)의 신뢰 가능한 콘텐츠.
- **웹 서비스** — `/ingitda.html`(6문서고 연합 즉석검색)·`/help.html`.

---

## 4. 성능 (근거 등급 구분)

| 등급 | 내용 |
|---|---|
| **논문** | Recall 93.0% · Precision 93.3% · **F1 0.931** (송창기 2026 방법론 검증) |
| **코드 실측** | 다국어 변환: IA 장진호 1→139건, Gallica 병인양요 0→5,853건 · nedb 座目 필터 601→492건 |
| **실전 3편** | 글로스터 연대(TNA 65건) · 장진호(3개국 3중소장 153건) · 한강 강배(1485–1986) · 6·25 아카이브센터 55,000+건 |
| **안전망** | `selfcheck`/`selfcheck_ext`가 2026-08-18 실측 기준으로 기관 사이트 개편 탐지 |
| **⚠️ 미비** | 이 코드로 재현율·정밀도를 자동 측정하는 **벤치마크 하니스 없음**. 빌드·테스트 스위트·CI도 전무 |

---

## 5. 현재 상태 & 발견된 드리프트

세 숫자(버전·아카이브 수·스킬 수)가 파일마다 어긋나 있다:

| 파일 | 버전 | 아카이브 | 스킬 | 상태 |
|---|---|---|---|---|
| `marketplace.json` | **1.13.0** | 14 (해외5/국내9) | — | 낡음 |
| `plugin.json` | 1.16.0 | 15 (해외6/국내10) | 10종 | 스킬수 불일치 |
| `CHANGELOG.md` | v1.16.0 | — | — | 기준 |
| 실제 디스크 | — | 15 | **11종** | 사실 |

추가: **PR #1**(CLAUDE.md 현행화)은 open draft — 충돌 없음, 머지 대기.

---

## 6. 다음 작업 (우선순위 로드맵)

### P0 — 지금 바로, 저비용 고효과
1. `marketplace.json` 정렬 — 버전 1.13.0 → **1.16.0**, 아카이브 14 → 15, 설명 현행화.
2. 스킬 수 표기 통일 — `plugin.json` "10종" → **11종** (또는 실제 목록 재확정).
3. **PR #1 머지** (또는 ready for review 전환) — 문서 현행화 확정.

### P1 — 지속 신뢰성
4. **CI 신설(GitHub Action)** — `selfcheck_ext.py` 주간 실행으로 접근경로 rot 자동 감지(현재 자동 감시 전무).
5. **두 저장소 패리티 자동 점검** — 도구 수·`_TOPICS`·보고서 규칙 diff.

### P2 — 성능 근거 강화
6. **재현 가능한 벤치마크 하니스** — 고정 쿼리셋 → 재현율/정밀도 자동 측정으로 "F1 0.931"을 코드 근거로 승격.
7. **24KB 응답 상한 자동 테스트** — UTF-8 바이트 실측.

### P3 — 확장
8. 아카이브 확장 — `_TOPICS`/world_archives에 일본 JACAR·중국 당안관·러 ГАРФ 등 추가국 반영.
