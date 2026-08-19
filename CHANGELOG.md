# Changelog

## 2026-08-19 v1.16.0
- **웹 서비스 계층**(korea-archive-mcp.vercel.app): 루트 랜딩 · 사용 안내 /help.html(+영문판 /help-en.html) — 갤러리 14유형 55컷·실물 쇼케이스 카드·조사 방법론 절 · **기록잇다** /ingitda.html — 6문서고 연합 즉석 검색(TNA·IA·갈리카·유러피아나·6·25아카이브[한국어 실검색]·NARA) + 문서고별 검증/노이즈 표기 판별 · 실물 예제 /examples/(한강 보고서 4.8MB·조선 강연 풀덱 403장)
- **조선 덱 채굴 자산**: `chosen_joseon_deck.md` — 10층 방법 상세·아홉 나라 검색어 지도·참조코드 전수(TNA 74·NAID 134·Gallica 30 등)·미해결 숙제 5건. query_bank identifiers/persons에 895 코드 지도·성씨 색인 칸 증보
- plugin.json v1.16.0 — 설명·키워드 현행화


## 2026-08-19 v1.15.0
- **조선 사료 심층 판독 통합**(한강 강배 조사 1485~1986 실측 이식): `nedb_search` **9모드** — law(법전·원문 제공 판정)·record(**座目 자동 필터** — "601건이 아니라 492건이 座目")·item(미공개/파싱실패 구분)·**★sibling(형제 조 전수 스캔)**·matrix(법전 수록 대조 — 부재의 발견)·origin(어휘 연원)·sjw(왕대 분포·최초 용례)·kyujanggak(목록+해제 동시+ImageServlet 패턴 지식). `joseon_tools.py` 동봉(표준 라이브러리만)
- **도메인 스킬 통합**: joseon-source-mining(references 6종)·joseon-source-excavation·khdb-citation·nanet-citation·kyujanggak-images·record-annotation·changgi-help + korea-archive-discovery **v2 references 승격**(11벽·식별자 해독·인명 열쇠·교차검증·world_archives 신설)
- **전쟁기념관 OpenAPI 채널 활성**: 발급 토큰 **Referer 바인딩 실측**(korea-archive-mcp.vercel.app) — 호출 헤더 자동 첨부, pageSize 상한 100. 토큰은 `KOREANWAR_API_TOKEN` 환경변수(공개 저장소 커밋 금지)
- **매직 키워드 웹 네이티브화**: MCP **prompts 2종**(full-package·changgi-help) + server instructions · `report_template` kind 8종(**help**·citation·annotation 추가) · 사용 안내 페이지 `/help.html`(갤러리 14섹션·시연 mp4 포함)
- **query_bank 조사 전략 6토픽**: walls·identifiers·persons·crosscheck + **world**(일 JACAR·중 당안관·러 ГАРФ/ГАХК 등 6개국 분류 비교)·**cities**(도시명 계보·1914 경계·로마자 표기법 연대) — 조선 강연 풀덱 채굴분
- selfcheck 원본 반영(`scripts/`) — 8443 판정은 **환경 의존**으로 정정(로컬·Vercel 8443 정상 재실측)

## 2026-08-13 v1.14.0
- **매직 키워드 "풀패키지"**: `report_template(kind='full_package')` — 발굴 조사→실물 수집→매거진 보고서(kind='magazine': 표지·목차·뒷표지·KA 인장·검증 낙관·브랜드 테마 5종)→카드뉴스 8장(kind='carousel' 12규칙)→포스터 시리즈→Canva(kind='canva_prompts' 7종)→**홍보 카드뉴스(실제 지면 캡쳐 쇼케이스)**→**입문 카드뉴스("○○은 처음이지?" 키워드 정복형)**→**메시지형(미장센 문법 — 1장 1메시지·블랙아웃 테제)**→**기록 해설형(점선 영역 판독·메타 표·원판/사본 계보·추정 금지)**→**발표 PPTX(16:9·발표 노트 필수·Canva 편집)**→**시연 영상(GIF/MP4)**→ZIP 패키지+작업 로그+**KARDA 온톨로지**(nodes/edges CSV·basis·confidence) — 산출물 12종 오케스트레이션
- 품질 게이트: CSS 템플릿 전체 포함·핵심 기록 카드 이미지 필수·placeholder 잔존 검사·수치 정합·전 도판 출처·게재윤리 4단계
- 실전 검증 2건: 글로스터 연대(제1호 — TNA 훈장 추천서 원문·65건) · 장진호(제2호 — 3개국 3중 소장 실증·153건)


## 2026-08-04 v1.13.0
- **insta-carousel 스킬 신설**: 발굴조사 결과를 인스타그램 캐러셀 카드뉴스(1080×1080 PNG)로 제작하는 원스톱 파이프라인
  - 발굴조사 방법론 내장(`references/discovery.md`): 표기 변형 병렬 투입 → 교차검색 → **인접 채굴(식별번호 ±5~15)** → 공개 상태 🟢🟡🔴 3단계 실검색 판정 → 메타데이터 검증("제목만 믿으면 틀린다")
  - 실물 이미지 소싱 플레이북(`references/image-sourcing.md`): 위키미디어 Commons API·archive.org `.thumbs` 프레임 추출(ffmpeg 불요)·헤드리스 크롬 카탈로그 캡처 + 라이선스 4단계 판정표 + **이미지별 출처 대장(sources.txt) 의무화**(원 소장처+식별번호가 본 출처, 사본처는 부기)
  - 검증된 디자인 시스템(`assets/card_styles.html`): 고대비 팔레트, 파노라마 필름스트립·부채꼴 스택·지도 여정·인물 카드·빅넘버 등 레이아웃 아키타입(`references/layouts.md`) — 하단 안전영역(.col)으로 페이지번호 겹침 구조적 방지
  - 렌더 스크립트(`scripts/make_carousel.py`): {{img:...}} 토큰 base64 임베드 → 카드 분리 → 헤드리스 크롬/엣지 PNG 캡처 → 크기 검증, `--only N` 부분 재렌더·`--expect N` 장수 보증·`--size` 세로형
  - 후킹형 캡션 가이드(`references/copywriting.md`): 한 줄 한 호흡 리듬·훅 공식 4종·표준 출처 표기 형식
  - 8·15 광복 81주년 7부작+번외편(총 9종, 85장) 실전 제작으로 검증된 워크플로

## 2026-07-30 v1.12.0
- **6·25전쟁 아카이브센터**(koreanwar.or.kr:8443, 전쟁기념관재단 — **MOU 협약기관**) TNA식 구조화 도구 신설:
  - `koreanwar_search`: 통합검색(viewType=archive 완전 목록·pageSize 10/20/50) — 결과카드에서 archRfcd·생산기관·상위계층 파싱, **상위계층의 NARA Record Group 자동 추출 → nara_search 역추적 링크**. 서버측 필터 실측 검증: 생산연도 범위·수집구분(수집/기증/구입/기탁/제작/이관/차입). `scope='battle'`이면 전투정보 DB(개전 초기 69전투 — TNA WO 281·NARA RG 407 교차검증 앵커). `KOREANWAR_API_TOKEN` 승인 시 OpenAPI(pbrcList.do) 공식 메타 채널(KOGL·이용조건·저작권 필드) 자동 병행 — 신청·승인 대기 중에도 검색은 키 없이 동작
  - `koreanwar_item`: 건별 메타(생산처·생산시기·입수처·열람 및 이용조건) — NARA 재수집본은 **입수처 링크가 catalog.archives.gov NAID 직결**(실측: 2022-US-02-AV-D-00207 → NAID 22345). `radius=1~8`이면 archRfcd 말미 일련번호 ±N 인접 채굴(실측: 00207 장진호 → 00206 맥아더 연포비행장·00208 F-86 김포; 정중한 3건 배치 병렬)
- `cross_search`에 koreanwar 채널 합류(키 불요) · `source_profile('koreanwar')` 3층 프로파일 + **상세검색 코드표 전체 수록**(자료유형 13종·수집구분 8종·자료연대·열람/이용조건·확장자 — 실측 추출)
- **PlayMCP 개발가이드 준수(2026.06.12판)**: 도구 24→**20개 통합**(`ia_metadata`→`ia_search`의 identifier 모드, `local_gov_search`→`foia_search`의 source 파라미터, koreanwar 4→2) · 원격 서버 전 도구 **annotations**(title·readOnlyHint·destructiveHint·openWorldHint·idempotentHint) · description 서비스명(Korea Archive 코리아 아카이브) 병기+1024자 이내 · 인접 채굴 배치 병렬화(p99 응답성)
- 협약 준수: 모든 요청에 프로그램 식별 UA(`KoreaArchiveMCP … MOU partner integration`) + 정중한 호출 간격

## 2026-07-13 v1.11.0
- **cross_search** (신규 도구): 여러 아카이브(tna·ia·gallica·europeana·nara·archives·nlk·nedb)를 한 쿼리로 **동시 교차수집**해 병합·중복제거, 출처 태그(복수 출처=교차확인) — 상호보완 동시수집
- **source_profile** (신규 도구): 전 기관(해외 5+국내 6)의 **자료구조·이용구조·활용구조** 3층 프로파일 (이용구조는 실제 엔드포인트 추출, robots는 live 검증)
- **국내 3대 부정합 키워드셋** (신규): 국사편찬위·국가기록원·국립중앙도서관·서울기록원·전쟁기념관 — 언어적/분류학적/기술관행적 부정합 대응, 라이브 도구로 **실측 검증한 252종** + 분류 교차매핑 + 관행 노트 (`keywords_<기관>.py`), query_bank로 노출
- **nlk 이중채널**: 전체 소장자료 ⊕ 자료유형(category) 정밀 채널 동시 수집·병합
- **nedb 합법 수집**: db.history.go.kr는 robots가 크롤러 차단 → data.go.kr **공식 개방파일(KOGL)** 을 인덱싱(`scripts/ingest-opendata.mjs`)해 검색(`NEDB_INDEX_URL`) — 라이브 스크래핑 없음
- **지오블록 우회**: seoul.go.kr의 해외 IP 차단 대응 — Vercel 함수 리전 Seoul(icn1) 고정 + robustFetch(타임아웃·재시도·프록시 폴백)
- HTML 분석 리포트 `docs/source_profiles.html` (전 기관 3층 프로파일)

## 2026-07-10 v1.10.1
- fix: 국가기록원 OpenAPI 엔드포인트 수정 + 국립중앙도서관(NLK) 파서 견고화 — 두 기관 모두 실제 결과 반환

## 2026-07-10 v1.10.0
- 키가 없는 국내 소스는 dead-end 대신 에이전트 WebSearch로 핸드오프
- docs: README 18개 도구·국내 소스·자동 브라우징 반영, 18장 카드 갤러리, SKILL 웹검색 노트

## 2026-07-10 v1.9.0
- 국내 도구 서버 사이드 자동 브라우징 — 각 사이트를 직접 페치·파싱해 실제 결과 반환

## 2026-07-10 v1.8.0
- 전쟁기념관 아카이브 추가 (`warmemo_search`)

## 2026-07-10 v1.7.0
- 지방 정보공개·기록원 추가 (`local_gov_search`: 서울정보소통광장·서울시교육청·경상남도기록원)

## 2026-07-09 (국내 아카이브 도입, v1.3~v1.6)
- 국사편찬위 한국사DB(`nedb_search`)·국가기록원(`archives_search`)·국립중앙도서관(`nlk_search`) 추가
- cheliped 브라우저 스크래핑 폴백(`scrape_plan`)·HTML 발굴 보고서(`report_template`) 추가

## 2026-07-09 v1.2.1
- Europeana 공용 데모 키 폴백 — 키 없이 즉시 작동

## 2026-07-09 v1.2
- 플러그인이 기본으로 원격 서버(Vercel)에 연결 — Python 설치 등 요구사항 제로

## 2026-07-09 v1.1 / v1.1.1
- Gallica·Europeana 추가(도구 9종), 이중언어 README, 8장 카드 갤러리
- 스킬 설명에 Gallica·Europeana 트리거 반영

## 2026-07-07 v1.0 (초판 배포)
- docs: 보고서 v6.0→v6.5 (7개 선행 보고서 통합, 실행편 §25~32, 웹 검증, 논문 통합)
- docs: 마스터 쿼리 코퍼스 v1.0→v1.1 (600+ 쿼리 12체계 + 논문 프레임워크 §13)
- harvester v0.2: NARA 10단계·TNA 14레이어·Adaptive Mining — TNA 실수집 1,214건, 승격후보 73건
- collector v0.1: 수집대장 17필드·권리 자동판정·링크 재검증(15/17 OK)·대시보드
- mcp v0.1 / skill v0.1: AI 에이전트 장착판
