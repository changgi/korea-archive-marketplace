# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
문서는 한국어, 코드·도구명·식별자는 영어다.

## 이 저장소는 무엇인가

**Claude 플러그인 마켓플레이스** `korea-archive-marketplace`. 국내외 **15개 아카이브**에 흩어진 한국
관련 기록(1860–1960)을 한 대화로 발굴하는 **`korea-archive` 플러그인**(MCP 도구 20종 + 스킬)을
배포한다. 검증된 발굴 방법론(송창기 2026, Recall 93.0%·Precision 93.3%·F1 0.931)을 클로드가
자동으로 쓰는 도구로 담았다.

사용자 접점은 두 가지: **플러그인**(데스크탑·Claude Code, `/plugin install korea-archive@korea-archive-marketplace`)과
**원격 MCP 커넥터**(웹·모바일, `https://korea-archive-mcp.vercel.app/api/mcp`).

### 두 저장소 — 파이프라인 패리티 (먼저 이해할 것)

- **이 저장소(`korea-archive-marketplace`)** = 파이썬 플러그인 + 마켓플레이스. `plugins/korea-archive/servers/server.py`가
  캐노니컬 **20도구** stdio 서버다.
- **자매 저장소(`korea-archive-mcp`)** = Vercel에 배포되는 **Node 원격 서버**(위 커넥터 URL, 리전 icn1).
  이 저장소에는 Node 코드가 없다.

두 서버는 **항상 도구·동작 패리티**를 유지해야 한다. 한쪽 도구의 스키마·응답 규칙·공유 상수(`_TOPICS`
다국어 변환, 보고서 규칙 등)를 바꾸면 반드시 다른 쪽에도 반영한다. 파이썬 쪽은 커밋 전 `py_compile` 통과를
확인한다.

## 제1원칙 — 웹·모바일 동등성: "지식은 서버로, 실행은 환경별 경로로"

Claude Code 스킬(`plugins/korea-archive/skills/`)은 **로컬 전용**이다. 웹·모바일 사용자는 MCP 도구
응답만 받는다. 따라서 새 기능·노하우를 만들 때마다:

1. **지식(규칙·템플릿·디자인 시스템·프롬프트)은 반드시 MCP 도구로도 노출한다** — 스킬에만 넣으면 웹에서는
   존재하지 않는 기능이다. 예: `report_template`의 `kind` 모드(report/magazine/carousel/canva_prompts/full_package/help/citation/annotation),
   매직 키워드 "풀패키지"·"창기창기"는 MCP **prompts**(`full-package`·`changgi-help`)로도 노출됨.
2. **로컬 실행 의존 단계(헤드리스 크롬·파이썬 스크립트·파일 생성)는 웹 대체 경로를 도구 응답 규칙에 명시한다**
   (예: 캐러셀 렌더 — 로컬=렌더 스크립트, 웹=아티팩트 미리보기 또는 Canva 커넥터 생성→PNG 내보내기).
3. 스킬을 수정하면 같은 내용의 서버 상수도 갱신한다(스킬-서버 패리티).

## PlayMCP 제약 (위반 시 심사 반려)

- 도구 **20개 이하** — 이미 상한. 새 기능은 새 도구가 아니라 **기존 도구의 파라미터 모드(enum)로 확장**한다.
  선례: `ia_metadata`→`ia_search(identifier=)`, `local_gov_search`→`foia_search(source=)`,
  보고서 종류→`report_template(kind=)`, 조선 사료 심층 판독→`nedb_search(mode=)` 9모드, 6·25 전투정보→`koreanwar_search(scope=)`.
- 도구 응답 **24KB 이하** — 텍스트 페이로드 증보 시 UTF-8 **바이트** 실측 필수(한글 3B/자).
- 전 도구 description에 서비스명 포함 + annotations(read-only) — server.tool 래퍼가 일괄 적용(SVC 상수 유지).
- 도구 스키마·description 변경 후에는 PlayMCP 콘솔 **"정보 불러오기"** 재실행을 사용자에게 안내.

## 핵심 도메인 개념 — 구조적 부정합

한국 기록은 당대 어휘로 색인돼 단일 키워드로는 못 찾는다. 세 차원(설계 전반을 좌우):

1. **언어적** — 표기 변형. 서울=**Keijo**(1910–45), 부산=*Fusan*, 인천=*Jinsen/Chemulpo*,
   한국=*Chosen/Corea/Tyosen*. 검색은 당대 표기를 병렬 투입한다.
2. **분류학적** — 레코드 그룹·부처코드 속에 숨음(NARA RG 242, TNA `FO 371`+FK코드). 넓게(재현율)→RG 교차(정밀도).
3. **기술관행적** — "0건 ≠ 부재." NARA 카드 750만 장 미전산화. 0건은 "미전산화 후보"로 기록하고 인접 채굴(piece ±15, box ±2).

### 다국어 → 색인 언어 자동 변환 (`server.py::_TOPICS`)

각 아카이브는 자기 색인 언어로만 검색된다(TNA·NARA·IA·Europeana=영어, Gallica=프랑스어). `_TOPICS`
사전이 한·일·중·러·스·독·베트남·힌디·히브리·아랍 등 어떤 언어 질의도 대상 색인 언어로 변환하고
(`_to_index_lang`/`_ko_en`), 라틴 밖 문자를 제거한 뒤 한국 앵커가 없으면 "Korea"/"Corée"를 덧붙인다.
실측 효과: IA 장진호 1건 → "Chosin Reservoir" 139건. **주의**: 당대 표기(Corea·Chosen 등)는 일부러
변환하지 않는다 — 강제 치환하면 표기-변형 방법론이 무력화된다.

## 저장소 구조 & 벤더링 (중요)

도구 코드가 **두 곳**에 있다:

- **`plugins/korea-archive/servers/server.py`** — 캐노니컬 20도구 서버. `servers/{harvester,keywords,kla}/`는
  최상위 패키지의 **벤더 복사본**(플러그인 자립용; `.mcp.local.json.example`가 stdio로 구동).
  `servers/joseon_tools.py`는 조선 사료 판독 보조(표준 라이브러리). **도구 동작을 바꾸면 여기서 고치고
  벤더 복사본을 최상위와 동기화한다.**
- **`mcp/server.py`** — 최상위 `harvester/`·`keywords/`·`collector/`를 `sys.path`로 당겨 쓰는 개발용 서버.
- **`harvester/`** — 논문 파이프라인 CLI(`cli.py`): TNA 14레이어·NARA 10단계·인접 채굴·Gallica·Europeana·LLM 추출. 표준 라이브러리(단 `extract_llm.py` 제외).
- **`collector/`** — `klactl.py` + `kla/`: 수집대장(17필드)·권리 자동판정(`ledger.auto_rights`)·링크 재검증·모니터링·HTML 대시보드.
- **`keywords/`** — 검증된 쿼리 코퍼스. 기관 중립층 `keywords_common.py`(G-그룹)·`keywords_nara.py`(N-그룹·`RG_MAP`)·`keywords_tna.py`(14레이어),
  그리고 기관별 `keywords_{archives,nedb,nlk,seoul,warmemo}.py`와 `profile_*.py`+`profiles.py`(→ `source_profile` 도구). `query_bank`의 단일 진실원.
- **`plugins/korea-archive/skills/`** — 스킬 묶음(로컬 전용). 아래 "스킬" 절 참조. `skill/`(최상위)은 옛 단일 복사본.
- **`.claude-plugin/marketplace.json`** — 마켓플레이스 매니페스트. **`docs/`** — 생성 산출물(보고서·carousel·pptx·source_profiles). **`scripts/`** — quickstart·selfcheck.

## 20개 MCP 도구

**해외(6)**: `tna_search` · `tna_adjacent_mine`(인접 채굴) · `nara_search`(RG 교차) · `ia_search`(검색+`identifier` 메타 통합) · `gallica_search` · `europeana_search`
**국내(9)**: `nedb_search`(한국사DB·9모드) · `archives_search`(국가기록원) · `nlk_search`(국립중앙도서관·6컬렉션) · `seoul_archives_search`(서울기록원) · `foia_search`(정보공개포털+지방 정보공개·기록원 `source=`) · `warmemo_search`(전쟁기념관) · `koreanwar_search`(6·25 아카이브센터 — **협약기관** MOU; `scope=battle`, OpenAPI `KOREANWAR_API_TOKEN`) · `koreanwar_item`(건별 메타 + NARA NAID 직결 + `radius` 인접 채굴) · `scrape_plan`(폴백)
**유틸(5)**: `query_bank` · `judge_rights` · `report_template`(`kind` 다중 모드) · `cross_search`(동시 교차수집·병합) · `source_profile`(기관 프로파일 — 해외5+국내6)

국내 도구는 **서버 사이드 fetch·파싱**으로 실제 결과를 반환하고, 키가 없거나 막힌 사이트는 `_agent_browse`로
"에이전트가 WebSearch/브라우저로 결과를 수집해 표로 제시하라"는 지시를 돌려준다(`scrape_plan`이 robots 판정).

## 권리 등급 판정 (`kla/ledger.py::auto_rights`)

`judge_rights`·대장 공통. `rg_series`/`archive`/`title`로 4등급 반환:
- **B(공개 가능 추정)** — 미 연방 직무물 `RG 111/208/306/342/428/127`(17 U.S.C. §105; 카탈로그 Use Restriction "Unrestricted"면 **A**로 상향)·Universal Newsreel(`200-UN`).
- **C(허가 필요)** — 한국 저작권자(`KOFA`·`KBS`).
- **D(지위 불명 — 공개 금지)** — `RG 242` 노획문서(원산국 권리 잔존, 36 CFR 1254.62) 및 미매칭 기본값.

자동 초판일 뿐 — 공개 전 사람이 보고서 §30 5단계로 확정한다. D등급 공개 금지.

## 명령

빌드·테스트 스위트 없음. 파이썬 3.10+ 표준 라이브러리(단 `mcp` 패키지, `ANTHROPIC_API_KEY` 의존 LLM 추출 제외).

```bash
# 엔드투엔드 스모크 (TNA 파일럿 → 시드 대장 → 검증 → 대시보드)
bash scripts/quickstart.sh

# 접근 경로 회귀 점검 (기관 사이트 개편 시 문서가 조용히 낡는 것을 잡음)
python scripts/selfcheck.py            # 한국사DB·규장각  (--quick / --json)
python scripts/selfcheck_ext.py        # 해외·국내 discovery v2 경로

# harvester (harvester/ 에서 실행)
python cli.py tna --pilot              # 레이어당 3쿼리, 키 불요
python cli.py tna                       # 전체 14레이어 1,222쿼리 (수 시간, sleep 준수)
python cli.py mine                      # 인접 채굴 (인용 역추적 + 인접 확장)
python cli.py gallica --pilot
EUROPEANA_API_KEY=... python cli.py europeana --type VIDEO
NARA_API_KEY=... python cli.py nara --moving-images --pilot
ANTHROPIC_API_KEY=... python cli.py extract data/tna_records.jsonl --limit 50

# collector (collector/ 에서 실행)
python klactl.py seed                   # 검증 시드 등록 + 권리 자동초판
python klactl.py fetch --max-mb 500     # 원본 다운로드 + SHA-256
python klactl.py verify                 # 링크 재검증 → verified_date
python klactl.py dash                   # → data/dashboard.html

# MCP 서버 로컬 구동
pip install mcp
python plugins/korea-archive/servers/server.py   # 캐노니컬 20도구 서버 (stdio)
```

선택 환경변수(대부분 키 없이 동작): `NARA_API_KEY` · `EUROPEANA_API_KEY`(없으면 공용 `api2demo`) ·
`ARCHIVES_API_KEY`(data.go.kr 15000153) · `NLK_API_KEY` · `KOREANWAR_API_TOKEN`(Referer 바인딩 — 공개 커밋 금지) · `ANTHROPIC_API_KEY`.

## 배포·검증 절차 (서버 변경 시)

1. 이 저장소(파이썬) 변경 → `py_compile` 통과 확인. 자매 Node 저장소에 동일 도구/상수 반영 → `node --check`.
2. 공유 상수(`_TOPICS` 다국어 변환·보고서 규칙 등)는 양쪽 **반드시 동일**.
3. 두 저장소 커밋·푸시 — 자매 저장소 main 푸시 시 Vercel 자동 배포(icn1); 중요 변경은 배포 READY까지 확인.
4. 도구 스키마·description 변경 후 PlayMCP "정보 불러오기" 재실행 안내.

## 콘텐츠 신뢰 원칙 (도구 응답·산출물 공통)

- 실물 기록만 — AI 생성 인물·역사 장면 금지. Canva 등 생성 AI 사용 시 실물 자산 강제 + 생성 후 한국어 환각 문구 전수 교정.
- 링크·수치·훈격은 도구 호출·API 원문으로 실확인한 것만. 정정 시 정정 이력 명기.
- 협약기관(KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터) 기록은 출처 표기 필수. 게재윤리 4단계(포로·사망자 존엄) 적용.
- 발굴 마무리 기본 산출물은 **HTML 보고서**(`report_template`) — 표·재현 쿼리·권리 배지·"0건 ≠ 부재" 주석·민감 주제 윤리 문구.

## 스킬 (`plugins/korea-archive/skills/`, 로컬 전용)

- **`korea-archive-discovery`** — 발굴 전략을 클로드가 자동 적용(표기 변형·RG 교차·TNA 코드·인접 채굴·국내 교차검증·권리판정·HTML 보고서). v2 references(11벽·식별자 해독·인명 열쇠·world_archives 등).
- **`archival-discovery-pipeline`** — 발굴이 식별자·URL을 확보한 **다음**을 잇는다: 프레임 단위 영상/이미지 분석·문자영역 OCR+VLM 교차판독·당대 지명/부대 식별·재기술·게재윤리 4단계·RiC-O/CIDOC-CRM 온톨로지·KARDA 노드엣지·논문 도판·정합 검사. "발굴이 찾고, 파이프라인이 읽는다."
- **`insta-carousel`** · **`korea-full-package`** — 발굴 결과를 카드뉴스/풀패키지(산출물 12종)로 제작.
- 조선 사료 도메인: **`joseon-source-mining`** · **`joseon-source-excavation`** · **`kyujanggak-images`** · **`khdb-citation`** · **`nanet-citation`** · **`record-annotation`** · **`changgi-help`**.

## 버전 관리

버전 문자열이 `.claude-plugin/marketplace.json`(마켓플레이스+플러그인 항목)과 `plugins/korea-archive/.claude-plugin/plugin.json`,
그리고 README·CHANGELOG에 중복된다. 함께 올리고 `CHANGELOG.md` 항목을 추가한다.
**현재 불일치 주의**: `plugin.json`·CHANGELOG는 **v1.16.0**인데 `marketplace.json`은 **1.13.0**으로 뒤처져 있다 — 다음 변경 시 정렬할 것.
