# Changelog

## 2026-11-21 v1.42.0
- **`nedb_search(mode='un')` UN 문서 판독**: record URL·recid 투입 시 문서기호(파일명 역산)·발행일·주제(UNBIST)·**요약(abstract)**·언어별 PDF 직링크(영문 우선) — 안보리 결의·보고서 원문을 분석에 바로 투입. 심층 판독 9채널
- **ndl 응답 강화**: 저자·매체 범주(紙/デジタル) 표시 + 429 동시접속 제한을 명시적 오류로(건강 진단 정확도)
- nedb_search 설명 1024자 재축약(판독 모드 10종 수용)

## 2026-11-21 v1.41.0
- **일본 NDL 서치 합류 — cross_search 24소스**: ndlsearch.ndl.go.jp OpenSearch 무키 실측(any= 파라미터) — 조선총독부 간행물·관보·통계연보·도판 축(JACAR 공문서와 상보). 한→일 JA_MAP 우선 변환 재사용. 실측: 朝鮮総督府 8,162건 · 京城 写真 1,983건(凱旋式之図 등)
- health 24채널. HELP·help.html·심사 팩 24소스 동기화. cross_search 설명 1024자 재축약

## 2026-11-21 v1.40.0
- **UN 디지털도서관 합류 — cross_search 23소스**: 보류된 UN Archives(AtoM 챌린지)와 달리 Invenio `of=xm`(MARCXML)이 무키로 열림을 실측 — 안보리 결의·공식문서(S/·A/ 문서기호+제목+날짜+record 딥링크). 한→영 자동 변환. 함정 기록: X-Requested-With 헤더에 빈 응답 — 일반 헤더 필수
- **full_package 1단계에 심층 판독 연계 명시**: 발굴 후 핵심 기록은 판독 8채널로 본문·권리 실확인 — 풀패키지 산출물 품질 직결
- health 23채널. HELP·help.html·심사 팩 23소스 동기화

## 2026-11-21 v1.39.0
- **`nedb_search(mode='jsg')` 장서각 서지·해제 판독**: 청구기호(K2-…)·dataId·URL 투입 시 자료명·청구기호·MF번호·분류 3종(연쇄 앵커 — 단독 매칭은 내비 필터와 혼동)·**해제 전문**(정의·서지사항·체제 및 내용·특성 및 가치·참고문헌, 4,000자 컷) 판독. 실측: K2-3556 개건도감의궤(1776 경모궁 개건) 해제 1,500자
- 심층 판독 8채널 완성 — 고문헌축(jsg 해제·kyujanggak·aks)·근대축(i815·gonghun·jacar)·현대축(ktv·earchive·seoul·commons)

## 2026-11-21 v1.38.0
- **`nedb_search(mode='commons')` 파일 판독**: File URL(또는 File:제목) 투입 시 라이선스(PD/CC → A/B/D 초판정 자동)·작가·**출처(원 소장처 크레딧 — NH·NARA 번호)**·촬영일·설명·원본 해상도 판독. 24h 캐시·도메인 한정. 실측: NH 96379 서울 수복(1950-09-29, 해병대 Ed Barnum 병장 촬영, PD → A)
- 심층 판독 모드 7종 완성(jacar·gonghun·i815·ktv·earchive·commons + seoul 전용도구) — 발굴→판독→권리 실확인 전 구간이 도구 응답 안에서 완결
- nedb_search 설명 1024자 준수 재축약(ci-verify가 검출)

## 2026-11-21 v1.37.0
- **위키미디어 공용 합류 — cross_search 22소스**: 키 불요 검색 API(한→영 자동 변환) — PD 사진·NARA/해군 재수집본의 원 소장처 역추적 창구. 'Seoul 1950' 791건 실측(해군역사센터 NH 시리즈 등). 공유 IP 429 가능성은 health가 상시 실측
- **cross_search 푸터에 심층 판독 이어가기 안내**: 소스 태그→판독 경로 8종([i815]→mode=i815 … [nara]→judge_rights(naid)) — 연합 검색에서 본문 판독까지 끊김 없이
- 해외 확장 재점검 기록: 호주 NAA(Cloudflare)·뉴질랜드 Archives NZ(Incapsula)·LOC(전 JSON 엔드포인트 Cloudflare) 보류, Trove는 무료 키 확보 시 합류 후보
- HELP_GUIDE·help.html·심사 팩 22소스 동기화

## 2026-11-21 v1.36.0
- **서울기록원 기록 단위 실체화 + 상세 판독**: 컬렉션명 매칭에 그치던 채널을 /catalog/result 서버 렌더 역공학으로 승격 — 시리즈(제목+/aggregation 딥링크)·사진 기록건(/item 딥링크)·컬렉션 카드 3유형 수확. `seoul_archives_search`에 상세 URL 투입 시 심층 판독(스키마 불변 오버로드): **식별번호(RG-SR-IT)·기술계층·법적지위·이용조건**(judge_rights 투입 — "제한없음+원본 협의 필요" 같은 기록 단위 권리 실문구)·기술 본문. 실측: 한강주변 도로신설 공사(RG5-SR90-IT2399)
- 함정 기록: Python _clean은 태그 무공백 결합 — 경계 정규식 \s* 필수(Node와 차이)

## 2026-11-21 v1.35.0
- **국편 전자사료관 세션 상세 역공학 해제 → `nedb_search(mode='earchive')`**: '상세 딥링크 없음(세션 기반)'으로 보류했던 상세 열람을 해제 — fnGoCatalogView가 catalogId가 아닌 **검색 폼+searchPosition 재제출** 설계임을 확인, 쿠키 유지 2단 POST로 상세 판독('키워드|순번' 입력). 열람조건·이용조건(권리 문구 — judge_rights 투입)·등록번호·사료건 ID 추출. 심층 판독 모드 4종(i815·gonghun·ktv·earchive)
- 평문 매칭이 내비게이션 '열람·이용조건' 메뉴와 혼동되는 함정 발견 → row-box HTML 앵커로 교정(명세 기록)

## 2026-11-21 v1.34.0
- **`nedb_search(mode='ktv')` 영상 판독 모드**: ehistory view URL 투입 시 대한뉴스·기록영상의 제목·제작연도·상영시간·출처·해설 전문 판독(24h 캐시·도메인 한정). 키워드면 목록. KOGL 출처 고지 자동 — 심층 판독 모드 3종 완성(i815·gonghun·ktv)
- **foia fail-fast**: opengov 장기 차단으로 재시도 포함 21초를 태우던 수집기를 단발 6초로 — health·연합 탐침 시간 보호, 복구 시 자동 정상화
- 기지 🔴 재진단: opengov(연결 리셋)·gallica(BnF 403) 지속, open.go.kr 본체는 세션+txId SPA로 브라우저 전용 판정 유지

## 2026-11-21 v1.33.0
- **`nedb_search(mode='i815')` 상세 판독 모드**: v1.32 목록 실체화에 이어 "발굴→분석" 다리 완성 — query=키워드면 실체화 목록, detail.do URL이면 **자료 본문 판독**(당대 신문기사: 신문명·발행일·생산정보+기사 전문 / 독립운동가 자료: 복명서 등 번역 전문 4,000자). 24h TTL 캐시 · i815 도메인 한정(임의 URL 페치 방지). 실측: 신한국보 1910-03-15 '공판 후의 안중근 씨' 전문
- 새 도구 없이 기존 모드 확장(PlayMCP 20개 준수). 독립운동 3채널 완성: i815 신문·자료 판독 + gonghun 공훈록 판독 + jacar 일본 측 메타

## 2026-11-20 v1.32.0
- **i815(독립기념관) 목록 실체화**: '신문자료 234건' 집계 신호에 그치던 채널을 실제 자료 발굴 채널로 승격 — 최대 카테고리 목록을 파싱해 자료 제목+**GET 딥링크**(구분별 detail.do — contentsFrm 역공학: 독립운동가/선교사/신문/미주흥사단/임시정부/의병/마이크로필름)를 상위에 제시, 나머지 카테고리는 집계 신호 유지. 실측: 안중근 → 신한국보 1910-03-15 '공판 후의 안중근 씨' 기사 전문 딥링크
- **nlk 6h TTL 캐시**(마커 <item>) — 실측 7.7s 최저속 축 완화. Python urllib 비ASCII URL 거부 교정(quote)
- health.yml 주석 21채널 현행화

## 2026-11-20 v1.31.2
- **사용자 대면 지식 동기화(제1원칙)**: `HELP_GUIDE`(창기창기 도움말) 15개→**21개 아카이브** 전 기관 명시 + 신기능 예시(공훈록 판독·naid 권리 실확인·mode 안내) — 웹·모바일 사용자가 도구 응답으로 최신 기능 인지
- help.html·help-en.html 21곳으로 갱신 · PlayMCP 심사 대응 팩 v1.31 전면 개정(시연 질의 12선 — gonghun 심층 판독·naid 실확인·21채널 health·성능 절 추가)

## 2026-11-20 v1.31.0
- **`nedb_search(mode='gonghun')` 심층 판독 모드**: 공훈전자사료관을 신호 채널(cross_search)에서 분석 채널로 승격 — query=이름이면 목록(mngNo), 숫자(mngNo)면 **공적조서·공훈록 본문 판독**(이명·생몰일 base64 디코드·본적·포상년도/훈격·공적개요 한글병기·공훈록 전문 4,000자 + 수록정보). 24h TTL 캐시. 실측: 안중근 3150 → 이명 安應七·공훈록 8권(1990) 전문
- 새 도구 없이 기존 모드 확장(PlayMCP 20개 준수). "발굴→분석" 다리: 웹·모바일 사용자도 공훈록 본문을 도구 응답으로 분석 가능(제1원칙)

## 2026-11-20 v1.30.0
- **공훈전자사료관 복구 → cross_search `gonghun` 합류(21소스)**: 과거 '사이트 오류' 보류였던 e-gonghun.mpva.go.kr 가 복구된 것을 재점검에서 확인 — 키 없는 GET 검색(독립유공자 공훈록 인명 채널)·상세 딥링크(mngNo — 공적조서·공훈록·묘소·현충시설 한 페이지) 역공학. base64 성명 디코드·한자명·생몰년·운동계열·포상년도·포상훈격 파싱. 실측: 안중근(1962 대한민국장)·유관순(2019/1962)·윤봉길
- health 21채널. 같은 재점검에서 kdemo(검색 오류)·UN Archives(JS 챌린지)는 보류 지속 확인

## 2026-11-20 v1.29.0
- **규장각(kyudb) 성능**: 목록·해제 2회 POST 병렬화 + 6h TTL 캐시(결과 있을 때만 — 奎 마커 검증). 실측 10.2s로 12s 타임박스에 근접해 cross_search에서 간헐 탈락하던 위험 해소
- **Python health 병렬화**: 20채널 탐침을 스레드풀(≤8)로 — 순차 합산 수십 초 → Node Promise.all과 동작 패리티. 채널별 ms 표시 유지
- **nara_search 권리 라인에 NAID 실확인 연계 안내**: RG 초판정 아래 `judge_rights(naid=<NAID>)` 실확인 경로 명시 — 웹·모바일 사용자도 응답 규칙으로 신기능 인지(제1원칙)

## 2026-11-20 v1.28.0
- **`judge_rights(naid=…)` NARA 실확인 자동판정**: 카탈로그 v2에서 해당 레코드의 Use Restriction 필드를 실제 조회해 자동판정 — `Unrestricted` 실확인 시 **A 확정**(기존 "확인 시 A 상향" 수동 규칙의 자동화), `Restricted` 계열은 C, 미기재는 RG 초판정 유지. RG 번호는 레코드 ancestors에서 자동 추출. 키 미설정·조회 실패 시 폴백 안내
- **health 채널별 응답시간(ms)**: 20채널 골든 질의 각 행에 실측 응답시간 표시 — 느려지는 채널(타임박스 근접)을 수치로 조기 발견
- i815 독립운동가 인명사전(search.i815.or.kr/dictionary)은 연결 리셋·HTTP 500으로 보류 기록

## 2026-11-20 v1.27.0
- **연합 검색 성능·견고성**: 소스별 **12초 타임박스**(Node Promise.race / Python fut.result) — 차단 대기 소스(갈리카 등)가 전체 'all' 호출을 끌던 실측 21.7초 병목 해소 · AWM 상세·JACAR 메타 **24시간 TTL 캐시**(마커 검증 — 캐시 히트 실측 1.2s→0.36s)
- **`query_bank(topic='allies')`**: 한국전 참전·지원 22개국 발굴 지도 — 보유 소스 직행(미·영·호·네덜란드·프) vs 대체 경로(캐나다=영연방 교차, 터키=RG 407) 매핑, 부대 고유명 열쇠(Kagnew·PEFTOK·Jutlandia·NORMASH·60th Para Field Ambulance 등)

## 2026-11-20 v1.26.0
- **네덜란드 국립문서보관소 합류 — cross_search 20소스**: SPA 셸 뒤의 공개 JSON API(zvt…/api/search/eads)를 Playwright 역추적으로 확보(키 불요). 'Korea' 243건 — 주한 네덜란드 대사관(2.05.202)·한국전 파견부대(2.13.56) 문서군 직행
- **AWM 심화**: 상세 파싱에 권리 자동 태그(저작권 만료 → `권리:PD`)·Conflict 기간(date) — 해외 소스 권리 표시 1호
- 뉴질랜드 Papers Past는 Incapsula 게이트로 보류 기록

## 2026-11-20 v1.25.0
- **호주 전쟁기념관(AWM) 합류 — cross_search 19소스**: 검색 모자이크(SSR C-id)→상세 병렬 2단 수집으로 제목·수장번호 확보(실측: Kapyong → 가평 계곡 1952 항공 조망 147844·파노라마 HOBJ3143~45). 한국전 영연방 축 신설
- **캐나다·독일·UN 접근 판정 기록**(docs/overseas-expansion-spec.md): LAC=Cloudflare Turnstile 차단(대안: AWM·TNA 교차), UN=자체 JS 챌린지(AtoM — 완화 시 즉시 합류 가능), 독일=DDB 무료 API 키 확보 시 `ddb` 합류 경로 + Europeana가 독일권 기집계

## 2026-11-20 v1.24.0
- **장서각 XHR 재역공학 성공 → cross_search 18소스** — Playwright 실브라우저로 실제 사용자 플로를 재현해, 검색 파라미터의 실형식이 **`q=query|<검색어>`**(필드 접두 필수)임을 확정. 플레인 `q`·`query`는 조용히 무시되고 전체 열람(1,349,451건)을 반환하는 함정(네트워크 캡처로 XHR 부재까지 확증). curl 서버사이드 재현·<em> 하이라이트 분절 제목 견고 파싱 — 의궤 33,805건(종묘의궤 K2 청구기호), 호적(ANC 고문서 중초) 직행 링크 실측

## 2026-11-20 v1.23.0
- **JACAR 강화(전용 모드 승격)**: `nedb_search(mode='jacar')` — 한→일 **JA_MAP 48항목**(16→48: 전투·지명·인물·사건) 우선 변환 검색 · 레퍼런스코드 **메타 직행**(Title·생산자·이미지 수·기밀등급 파싱) · **인접 채굴 ±span×100**(簿冊 내 건 번호 간격 100 실측 — ±1·±10은 404). 실측: B04014056900(국제연맹 탈퇴 관계, 58면, Top Secret) ± 같은 簿冊 연속건 / 징용→徴用 검색
- **규장각 강화**: cross_search에 `kyudb` 소스 합류(17소스) — 기존 목록+해제 POST 코어 재사용, 奎 청구기호 신호 채널
- **장서각·민주화운동 오픈아카이브 보류 기록**: 장서각은 검색이 비공개 XHR(청구기호 직행 /dir/view?dataId=JSG_…만 확보), kdemo는 개편 중 오류 — 명세에 재점검 대상으로 기록

## 2026-11-19 v1.22.0
- **독립기념관·KTV e영상역사관 합류(cross_search 16소스)** — i815: GET 실측(★searchMenu 필수 — 누락 시 500), 카테고리 집계+직행 링크 신호 채널(임시정부·독립운동가 자료·신문자료 등) · ktv: ehistory /search는 iframe 셸, 실체는 ktv.go.kr 통합검색 GET — 대한뉴스·기록영상 딥링크 파싱(판문점 2,641건)
- **JACAR 한→일 출력 사전(16항)**: 朝鮮総督府 등 일본어 질의가 영어와 다른 결과축을 여는 것을 실측 — jacar 수집기에 한→일 우선 적용
- 헬스체크 16채널. 접근 명세: docs/i815-ktv-access-spec.md

## 2026-11-19 v1.21.0
- **국편 전자사료관 합류(cross_search 14소스)** — archive.history.go.kr POST 검색 실측·역공학(`allSearchQuery` 폼, `fnGoCatalogView`+title 파싱, 사료ID 추출). NARA 수집 사료 원문 창구: '노획' → AUS005 노획 무기·물자 영상 실측. 상세 딥링크는 세션 기반이라 사료ID 표기(docs/earchive-gonghun-access-spec.md)
- **공훈전자사료관 보류 기록**: 사이트가 자체 오류 상태 — 공공데이터포털 15157239 API 경로를 대안으로 명세(키 확보 시 합류)

## 2026-11-19 v1.20.0
- **일본 JACAR 합류(cross_search 13소스)** — 아시아역사자료센터(공문서관·외무성 외교사료관·방위연구소) GET 검색을 전수 실측해 연합 검색·헬스체크에 투입. ★핵심 발견: 검색어 파라미터는 `kw`(`keyword`류는 조용히 무시되고 기본 목록 반환 — 서로 다른 키워드 대조 검증으로 적발). 레퍼런스코드 직행(`/das/meta[-en]/<코드>`)·계층 브라우징·연대/기관 필터 폼까지 docs/jacar-access-spec.md에 명세화(전용 도구 승격은 심사 후 슬롯 재편 시)
- **help.html·help-en.html 현행화**: 아카이브 16곳+(JACAR·한국고문서자료관), 방법론 그리드에 연대 필터·권리는 표시·인접 채굴 4기관·표기 변형 자동 팬아웃, 예시에 명성황후 편지 38건 실증, FAQ에 채널 상태 점검

## 2026-11-19 v1.19.1
- **문서 현행화**: README(양 저장소)·HELP_GUIDE(창기창기 안내)·mcp/README 도구 표 — v1.17~1.19 신기능(연대 필터·인접 채굴 4기관·cross_search 13소스·variants·csv·health·KOGL·exhibit·24KB 가드) 전면 반영. README에 발굴 우선 원칙 명시
- **TTL 캐시**: 전투정보 목록(warList)·AKS 분류 트리 6시간 인메모리 캐시(웜 인스턴스) — 오류 응답은 캐시하지 않음
- **PlayMCP 심사 대응 팩**: docs/playmcp-review-pack.md — 제약 준수 요약·반려 해소 증빙·실측 시연 질의 10선·채널 상태

## 2026-11-19 v1.19.0
- **국내 연대 필터**: `archives_search`·`nlk_search`에 year_from/year_to — API가 연대 파라미터를 지원하지 않으므로 상위 50건 내 후처리 필터로 구현하고 라벨에 '후처리' 명시 (koreanwar는 기존 서버사이드 필터 유지)
- **인접 채굴 일반화**: `nara_search(naid, radius)` — NAID ±N을 naIds 콤마 목록 **한 호출**로 일괄 조회(NARA 공식 문서 기반, 사진 ±3·색인 ±1 간격 지식 안내) · `ia_search(identifier, radius)` — 일련번호 말미 숫자 ±N 존재 확인(실측: 111-adc-10076±2 → 4건 실존). TNA·koreanwar에 이어 4기관째
- **`cross_search(format='csv')`**: 병합 결과를 sources,title,date,id,url CSV 블록으로 — 스프레드시트·KARDA 온톨로지·통계 분석 직투입("자료로써 분석할 수 있게")
- **`report_template(kind='exhibit')`**: 고문서 전시형 산출물 규칙+HTML 골격 — aks-archive-harvester 스킬 ④매개 단계의 서버판(전시 페이지·카드 1080×1350·학습지 A4·게시 문구, 추정 금지 캡션 규칙, AKS 출처 고지). 제1원칙(웹·모바일 동등성) 잔여 공백 해소

## 2026-11-18 v1.18.1
- **응답 24KB 공통 가드**: server.tool 래퍼(Node)·등록 후 일괄 래핑(Python, mcp<2 전제)에 UTF-8 바이트 실측 트렁케이션(여유 23,800B) — PlayMCP 한도를 도구별 수동 slice가 아니라 구조적으로 보장. 절단 시 분할 조회(page·max_results) 안내 부착
- **CI 자동화(GitHub Actions)**: 양 저장소 `verify`(push·PR마다 node --check·py_compile·도구 20종·설명 1024자·TOPICS 컴파일·3사본 패리티 diff·런타임 등록) + mcp 저장소 `health`(주간 프로덕션 13채널 골든 질의 실측 — 🔴 3채널 이상이면 실패 알림). 수동 검증 체계의 자동화 — Gallica류 무증상 장애 재발 방지

## 2026-11-18 v1.18.0
- **소스 헬스체크**: `source_profile(institution='health')` — 13채널 골든 질의 일괄 실측(🟢건수/🟡연결만/🔴실패) + 서버 키·인덱스 설정 상태. 발굴 우선 원칙의 전제("깨짐을 스스로 발견한다") 도구화
- **warmemo 복구(신 플랫폼 폴백)**: 전쟁기념관 구 통합검색(archives.warmemo.or.kr)이 개편으로 결과 구조 소멸(실측) → 0건 시 동일 재단 6·25전쟁 아카이브센터(koreanwar.or.kr, 협약기관) 검색으로 자동 대체 + 개편 사실 명시
- **권리 힌트 자동 표시**: judge_rights에 **공공누리(KOGL) 제1~4유형 자동 판정** 추가(kla/ledger.py 양 사본) · Europeana 건별 rights(CC/InC) 표시 · archive.org 건별 licenseurl 표시 · NARA record_group 지정 시 권리 초판정 라인 자동 부착 — "발굴 우선, 권리는 표시"의 자동화
- **표기 변형 자동 팬아웃**: `cross_search(variants=True)` — 당대 표기(Corean·Corea·Chosen·Keijo·Fusan·Chemulpo·Gensan·Heijo·Quelpaert·Taikyu) 최대 2종을 해외 4채널(tna·ia·nara·europeana)에 자동 병렬 투입, 채널 태그에 변형 표시(예 ia·Corean) — query_bank '열한 겹의 벽' 지식의 도구화

## 2026-11-18 v1.17.2
- **cross_search 소스 13종**: 사용자 결정으로 `seoul`(서울기록원 컬렉션)·`foia`(서울정보소통광장 결재문서 원문) 합류 — 각 전용 도구(seoul_archives_search·foia_search)와 동일 접근 경로 재사용. open.go.kr 본체(브라우저 전용)는 전용 도구 경로 유지
- Gallica 차단 감지 우아한 성능저하(v1.17.1 후속): BnF가 서버 IP 자동 조회를 403 차단(실측) — SRU XML이 아니면 차단 사실·대체 경로(웹 검색/브라우저)를 명시 반환, 연대 필터는 dc.date(BnF 공식 색인)+후처리 폴백으로 교정
- TNA 연대 필터 0건 시 '연대 미상 기록 제외' 안내

## 2026-11-18 v1.17.1
- **연대 필터·페이지네이션 표준화(해외 5종)**: `tna_search`·`ia_search`·`gallica_search`·`europeana_search`에 `year_from`/`year_to`(연대 범위)와 `page`, `nara_search`에 `page` 추가. 전 문법 실측 검증 — TNA `sps.dateFrom/To`(Korea 13,533→1950~51 한정 2,553건), IA `date:[A TO B]`+page, Europeana `YEAR:[A TO B]` 열린 범위(*)·다중 qf. Gallica `gallicapublication_date` CQL·startRecord(배포 서버 검증)
- **cross_search 소스 11종으로 확대**: `warmemo`(전쟁기념관 — 카테고리 건수 신호 채널)·`aks`(한국고문서자료관 소장처 172곳 — 내장 카탈로그, 네트워크 0) 합류. 서울기록원·정보공개포털은 robots 실측(`archives.seoul.go.kr/robots.txt` Disallow `/catalog/`) 확인으로 기존 설계대로 미포함 유지
- harvester/tna.py `_search`에 `start_page`·`date_from`·`date_to` 옵션 (하위호환)

## 2026-11-17 v1.17.0
- **한국고문서자료관(AKS) 서버 노출** — 제1원칙(웹·모바일 동등성) 이행: `nedb_search` **mode='aks'** 신설. 소장처 **172곳 내장 카탈로그**(2026-11-17 treeAjax 전수 실측) 이름 검색 → 분류 트리 → 문서 목록(예: 동춘당 송준길가 교령류 266건) → 건별 면수·UCI·썸네일(imgnode)까지 라이브 조회. 이미지 일괄 수집은 로컬 전용(aks-archive-harvester 스킬 — DZI 타일 복원)·웹은 뷰어 열람으로 대체 경로 명시. 전 경로 라이브 검증 완료(도구 수 20 유지 — enum 모드 흡수)
- **6·25 후기 단계 전투 앵커 16건**: `koreanwar_search(scope=battle)` — 기관 전투 DB(개전 초기 69건)에 미수록인 인천상륙·장진호·청천강·흥남·지평리·임진강(글로스터)·가평·피의 능선·단장의 능선·백마고지·저격능선·폭찹힐·금성·정전협정 등을 서버 큐레이션 앵커(통설 전사 시기 + TNA WO 281·NARA RG 관 교차검색어)로 보완. "기관 DB 아님" 명시·수치/전과 주장 없음
- **다국어 주제 사전(TOPICS) 43→85항목**: 후기 전투(지평리·가평·백마고지 상세·금성 등)·지명(원산·대구·개성·철원·금강산·독도)·개항기~해방 인물·사건(명성황후·고종·안중근·김구·3·1운동·위안부·강제동원·광복군·임시정부·동학·의병·을사조약·아관파천·헤이그 특사·제주 4·3·여순·신탁통치·미군정) — 한자·일·중·러 입력 패턴 병행, Gallica용 프랑스어 사상 확충(지평리=프랑스대대 등)
- **의존성 고정**: `mcp>=1.0,<2` (mcp 2.x의 FastMCP 제거로 임포트 실패 — 2026-11-13 실측)
- 11월 반영분 소급 기록: **koreanwar_search·koreanwar_item**(6·25전쟁 아카이브센터 협약기관 — 통합검색+전투정보, NARA NAID 역추적, radius 인접 채굴, 도구 20개 통합: ia_metadata→ia_search·local_gov_search→foia_search) · 한국어→영/프 자동 변환으로 PlayMCP 반려 사유 해소(갈리카 병인양요 0→5,853건) · 매직 키워드 영문 슬러그 인식·cross_search 선두 배치 · mcp/server.py 개발용 진입점 배포본 동기화
- Node(route.js) ↔ Python(배포본·개발용) 3사본 패리티: py_compile·node --check·런타임 등록 20종·TOPICS 85 패턴 컴파일 전수 통과

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
