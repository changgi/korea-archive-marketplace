# 🇰🇷 Korea Archive — Claude Plugin Marketplace

**국내외 14곳의 아카이브에 흩어진 한국 관련 기록(1860–1960)을 클로드에서 한 대화로 발굴합니다.**
**Discover Korea-related records scattered across 14 archives — worldwide and in Korea — from a single Claude conversation.**

[English](#english) · [한국어](#한국어) · [Gallery / 카드뉴스](#gallery--카드뉴스)

```
/plugin marketplace add changgi/korea-archive-marketplace
/plugin install korea-archive@korea-archive-marketplace
```

웹·모바일(클로드 웹앱)은 MCP 커넥터로 연결: 설정 → 커넥터 → 커스텀 커넥터 추가 →
`https://korea-archive-mcp.vercel.app/api/mcp`

> **v1.11** — `cross_search`(여러 아카이브 동시 교차수집·병합) · `source_profile`(기관 자료·이용·활용구조 프로파일) · 국내 3대 부정합 검증 키워드셋 252종 · nlk 이중채널 · nedb 공식 개방파일(KOGL) 수집. **총 20개 도구.**

---

## English

### Why this exists

Millions of records about Korea sit in foreign archives (NARA, TNA, archive.org, Gallica, Europeana) **and** in Korean institutions — but a large share is effectively *undiscoverable* with ordinary search. The reason is a **structural mismatch**: records were cataloged in the vocabulary of their era.

Searching **"Seoul"** misses most colonial-period material, because in 1910–1945 the city was indexed as **"Keijo"**. Busan was *Fusan*, Incheon *Jinsen*/*Chemulpo*, and Korea itself often *Chosen*, *Tyosen*, or *Corea*. Korean sites add a second wall — JavaScript, logins, and API keys — that blocks automated collection.

This plugin packages a **peer-validated discovery methodology** — Song (2026): Recall 93.0%, Precision 93.3%, F1 = 0.931 — into 20 tools Claude uses automatically, now spanning both overseas and domestic archives.

### The 14 archives / 20 tools

**Overseas (5)**

| Tool | Source |
|---|---|
| `tna_search` | U.K. National Archives (Discovery) — no key. Reference codes auto-quoted. |
| `tna_adjacent_mine` | *Adaptive Mining* — crawl piece numbers around a verified reference to surface uncatalogued files. |
| `nara_search` | U.S. NARA catalog, Record Group cross-filter (free `NARA_API_KEY`). |
| `ia_search` / `ia_metadata` | archive.org search + file/size inspection before download. |
| `gallica_search` | Bibliothèque nationale de France — no key. Late-Joseon French missionary & diplomatic sources. |
| `europeana_search` | 4,000+ institutions in 58 countries. Works out of the box (shared demo key); `EUROPEANA_API_KEY` for heavy use. |

**Domestic / 국내 (9)** — server-side auto-browse; keyless institutions hand off to the agent's web search.

| Tool | Source |
|---|---|
| `nedb_search` | 국사편찬위 한국사데이터베이스 — 11M+ primary sources (Sillok, Seungjeongwon, POW reports…). |
| `archives_search` | 국가기록원 (OpenAPI, RSS) — free `ARCHIVES_API_KEY` from data.go.kr (15000153). |
| `nlk_search` | 국립중앙도서관 — 6 collections incl. 대한민국신문아카이브 (1883–1960 old newspapers, PD). `NLK_API_KEY` optional. |
| `seoul_archives_search` | 서울기록원 — Seoul municipal records / photos / oral histories. |
| `foia_search` | 정보공개포털 (open.go.kr) — released decision documents & FOIA requests. |
| `local_gov_search` | 서울정보소통광장 (city decision documents) · 서울시교육청 · 경상남도기록원. |
| `warmemo_search` | 전쟁기념관 아카이브 — Korean War / military-history records, photos, oral histories. |

**Utility (across all)**

| Tool | Purpose |
|---|---|
| `query_bank` | 1,943 validated keywords + **국내 3대 부정합 키워드셋 252종** (`domestic`, per-institution). |
| `judge_rights` | First-pass rights triage A/B/C/D with legal basis. |
| `scrape_plan` | robots check + browser-tool guidance for JS/blocked sites. |
| `report_template` | Turn finished findings into a styled HTML discovery report (tables · reproducible queries · rights). |
| `cross_search` | **여러 아카이브를 한 쿼리로 동시 교차수집·병합** (상호보완). 출처 태그 — 복수 출처 = 교차확인. |
| `source_profile` | **기관 자료구조·이용구조·활용구조** 프로파일 (해외 5 + 국내 6). 발굴 전략 수립용. |

Plus the **skill** `korea-archive-discovery`: search strategy Claude applies automatically (spelling variants, broad→narrow phasing, TNA codes, adjacent mining, domestic cross-check, rights triage, HTML report).

### Auto-browsing (v1.9–v1.10)

Korean sites are JS-rendered or login-gated. The domestic tools now **fetch and parse each site server-side**, returning real results:
- 서울정보소통광장 → the actual decision-document list (title + link)
- 전쟁기념관 → hit counts by category
- 한국사DB → which DBs contain the term · 서울기록원 → matching collections
- 국가기록원 / 국립중앙도서관 → OpenAPI results when a key is set

When a source needs a key that isn't set, the tool **instructs Claude to gather the results via web search** instead of dead-ending.

### Optional server keys (env vars)

`NARA_API_KEY` · `EUROPEANA_API_KEY` · `ARCHIVES_API_KEY` (data.go.kr 15000153) · `NLK_API_KEY` (www.nl.go.kr Open API). All optional — most tools work without any key.

---

## 한국어

### 왜 필요한가

미국 NARA, 영국 TNA, archive.org, 프랑스 Gallica, 유럽 Europeana — 그리고 국내 기관에 우리 근현대사 기록이 수백만 건 잠들어 있지만, 상당수는 일반 검색으로는 **찾을 수 없습니다**. 기록이 당대의 언어로 색인됐기 때문입니다(구조적 부정합).

**"Seoul"**로 검색하면 식민기 자료 대부분을 놓칩니다 — 1910~45년 서울은 **"Keijo"**로 색인됐으니까요. 부산은 *Fusan*, 인천은 *Jinsen·Chemulpo*, 한국은 *Chosen·Corea*. 국내 사이트는 자바스크립트·로그인·API 키라는 두 번째 벽까지 있습니다.

이 플러그인은 검증된 발굴 방법론(송창기 2026, F1 = 0.931)을 클로드가 자동으로 쓰는 **20개 도구**로 담았고, 이제 해외와 국내 아카이브를 모두 아우릅니다(여러 아카이브 동시 교차수집·기관 프로파일 포함).

### 자동 브라우징 (v1.9–v1.10)

국내 사이트는 JS·로그인 기반이라, 국내 도구가 **서버에서 각 사이트를 직접 조회·파싱해 실제 결과**를 돌려줍니다(서울정보소통광장=결재문서 목록, 전쟁기념관=카테고리별 건수, 한국사DB=매칭 DB, 서울기록원=매칭 컬렉션, 국가기록원·국립중앙도서관=키 설정 시 OpenAPI). 키가 없는 기관은 **클로드가 웹검색으로 결과를 가져오도록 지시**합니다.

### 설치

- **플러그인**(데스크탑·Claude Code):
  ```
  /plugin marketplace add changgi/korea-archive-marketplace
  /plugin install korea-archive@korea-archive-marketplace
  ```
- **MCP 커넥터**(웹·모바일): 설정 → 커넥터 → 커스텀 커넥터 추가 → `https://korea-archive-mcp.vercel.app/api/mcp`

### 사용 예

- "서울정보소통광장에서 위안부 결재문서 찾아줘" → 서울시 결재문서 원문 목록
- "전쟁기념관에서 인천상륙작전 자료 찾아줘" → 카테고리별 건수
- "Gallica에서 한국은행 찾아줘" → 표기 6종 총 273건
- "찾은 결과 HTML 보고서로 만들어줘" → 표·재현쿼리·권리등급 보고서

라이선스: MIT · 방법론: 공업연구사 송창기.

---

## Gallery / 카드뉴스

능력·국내 소스·자동 브라우징·실전(라이브)·설치를 담은 카드 18장 (`docs/cards/`).

| | | |
|---|---|---|
| ![01](docs/cards/card_01.png) | ![02](docs/cards/card_02.png) | ![03](docs/cards/card_03.png) |
| ![04](docs/cards/card_04.png) | ![05](docs/cards/card_05.png) | ![06](docs/cards/card_06.png) |
| ![07](docs/cards/card_07.png) | ![08](docs/cards/card_08.png) | ![09](docs/cards/card_09.png) |
| ![10](docs/cards/card_10.png) | ![11](docs/cards/card_11.png) | ![12](docs/cards/card_12.png) |
| ![13](docs/cards/card_13.png) | ![14](docs/cards/card_14.png) | ![15](docs/cards/card_15.png) |
| ![16](docs/cards/card_16.png) | ![17](docs/cards/card_17.png) | ![18](docs/cards/card_18.png) |

01 표지 · 02 문제 · 03 능력 4층 · 04 해외 5곳 · 05 국내 9곳(NEW) · 06 자동 브라우징(NEW) · 07~11 실전 LIVE · 12 옛 표기 · 13 권리판정 · 14 플러그인 설치 · 15 MCP 커넥터 · 16 당신 차례 · 17 소개 · 18 GitHub.
