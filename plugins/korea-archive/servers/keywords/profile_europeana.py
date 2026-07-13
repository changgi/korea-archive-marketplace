#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_europeana — 유로피아나 (Europeana) 자료·이용·활용구조 프로파일."""
import json
PROFILE = json.loads(r'''
{
 "name_ko": "유로피아나",
 "name_en": "Europeana",
 "category": "overseas",
 "data": {
  "hierarchy": "계층형 아카이브(fonds/series)가 아니라 애그리게이션 그래프. 실제 4단: (1)Aggregator(국가·도메인 애그리게이터, 예: national aggregator·domain aggregator) → (2)dataProvider(원소장처 = 실제 소장기관, 예: University Library of Genova) → (3)dataset/edmDatasetName(제공 데이터셋, 예: 446_CulturaItalia_InternetCulturale) → (4)item = CHO(Cultural Heritage Object, 아이템 단위). 각 item은 EDM 구조로 edm:ProvidedCHO(지적 대상) + ore:Aggregation(집합) + edm:WebResource(디지털 표현)로 구성. 철·건 같은 기록학 계층은 없고 전부 아이템 레벨 평면 색인 — 원소장처의 원 계층은 dataProvider 필드로만 흔적이 남는다.",
  "classification": "Europeana Data Model(EDM) — RDF 기반 데이터·메타 모델(실명). 단일 주제분류표는 없음. 매체 분류는 DCMI Type 기반 TYPE facet(IMAGE/TEXT/VIDEO/SOUND/3D). 주제·인물·장소·시대는 Europeana Entity Collection(edm:concept/agent/place/timespan, SKOS)로 부분 연결되나 제공기관마다 상이. 권리는 표준 14종 값(RightsStatements.org + Creative Commons/CC0/PD) 통제어휘.",
  "identifiers": "europeana record ID = /{datasetId}/{localId} 형식(필드 'id', 예: /446_.../GE38007296). 포털 접근용 guid(URL). 원문 접근은 edm:isShownAt(제공기관 상세페이지)·edm:isShownBy(미디어 파일)·edm:preview(썸네일 프록시). 원소장처 고유 식별자는 localId 안에 원기관 OAI ID(oai:...)로 내장.",
  "metadata_standard": "EDM(Europeana Data Model). 기반 어휘: Dublin Core / DC Terms, ORE(Object Reuse and Exchange), SKOS, RDF. 제공기관의 원 표준(MARC·ISAD(G)·LIDO·EAD 등)을 EDM으로 크로스워크한 결과 — 즉 아카이브의 ISAD(G) 계층은 유입 시 아이템 레벨 DC로 평탄화됨. 필드는 다국어 배열(dcTitleLangAware 등 LangAware 구조).",
  "scope": "58개국 4,000+ 제공기관, 5,000만+ 문화유산 객체(도서관·박물관·기록관·시청각). 시대는 유럽 문화유산 전 시기. 한국(1860–1960) 관련 부분집합은 '유럽 소재' 한국 자료 — 구한말 선교사·외교 사진, 지도(예: Carte de la Corée 1754), 일제기 자료, 한국전쟁기 유럽 참전국·뉴스릴·방송. 실측: 'Corée'+TYPE:IMAGE = 4,704건(2026-07 데모키 조회).",
  "digitization": "100% 디지털화 전제 — Europeana는 디지털 표현(최소 썸네일)이 있는 객체만 색인. 다만 해상도·다운로드 가부·미디어 호스팅은 dataProvider 도메인(edm:isShownBy)에 종속돼 편차 큼. 메타데이터+썸네일은 Europeana가 CC0로 재배포, 원 고해상 파일은 원소장처 권리에 따름."
 },
 "access": {
  "channel": "Search API — https://api.europeana.eu/record/v2/search.json (JSON). 파라미터: wskey, query, rows, profile=standard, qf=TYPE:VIDEO|IMAGE|TEXT|SOUND. 심층 페이징은 cursor=* → nextCursor. 아이템 상세는 Record API(/record/v2/{id}.json), 엔티티는 Entity API.",
  "auth": "wskey 필수 — EUROPEANA_API_KEY(apis.europeana.eu 무료 발급, 통상 일 10,000 req) 또는 공유 데모키 'api2demo'. 데모키는 키 없이 즉시 작동하나 공유 스로틀(응답의 requestNumber로 소진 추적).",
  "query_syntax": "query = Apache Solr/Lucene 문법 — 불리언(AND/OR/NOT), 정확구는 큰따옴표(\"Corée\"), 필드 검색(proxy_dc_title:, who:, where:, when:, YEAR:). 필터는 qf 파라미터 반복: qf=TYPE:IMAGE, qf=COUNTRY:France, qf=YEAR:1900, qf=DATA_PROVIDER:\"...\", qf=RIGHTS:*creativecommons*, reusability=open|restricted. 다국어 배열 색인이라 언어 변형을 OR로 병렬.",
  "response_format": "JSON. 최상위: success·totalResults·itemsCount·nextCursor·items[]. 각 item: id·guid·title[]·year[]·dataProvider[]·country[]·type·rights[]·edmIsShownAt[]·edmIsShownBy[]·edmPreview[]·dcLanguage[]·edmConceptLabel[] 등(대부분 배열, LangAware 변형 포함). profile=standard로 핵심 필드, rich/facets로 확장.",
  "blocking_notes": "공개 REST JSON API — 로봇/JS렌더/지오블록 없음. api.europeana.eu에는 robots.txt 없음(302, 크롤 대상이 아닌 API). 제약은 wskey 레이트리밋뿐: 데모키 api2demo는 공유·스로틀되므로 대량 조회 시 개인 무료키 권장. 주의: edm:isShownBy 실제 미디어는 dataProvider 도메인(예: internetculturale.it)에 호스팅 — 그쪽은 hotlink 차단·robots가 걸릴 수 있어 원문 다운로드는 개별 확인.",
  "rights_access": "메타데이터·썸네일: Europeana가 CC0로 재배포(자유). 원 디지털 객체: 아이템별 표준 edm:rights 1개(RightsStatements.org 12종 + CC 라이선스 + CC0/Public Domain Mark) — 값이 필드로 명시되므로 기계 판정 가능. reusability=open이면 재사용 자유군. 원문 열람·복제는 isShownAt의 원소장처 조건을 따름 — 같은 한국 자료라도 제공기관별로 권리가 상이(핵심 리스크)."
 },
 "use": {
  "mismatch_summary": "(1)언어적: 최대 병목. 다국어 애그리게이터라 한국이 Corée(불)·Corea(이/스)·Coreia(포)·Korea/Korea-Krieg(독)·Kore(터)·Корея(러) 등으로 흩어짐 — 단일 'Korea' 질의는 대량 누락. 실측 'Corée'만으로 IMAGE 4,704건. (2)분류학적: RG·fonds 없이 아이템 레벨 평면 색인 + TYPE facet뿐 → 기록군 단위 전수가 불가, dataProvider/COUNTRY/YEAR facet으로 우회해 원소장처를 역추적해야 함. (3)기술관행적: 제공기관 원표준을 EDM으로 평탄화하면서 제목·연대·주제가 원기관 언어·표기로 그대로 유입(dcTitleLangAware의 def/언어 배열) → 표제가 'Carte de la Corée'처럼 원어이고 연대(edmTimespanLabel)·주제(edmConcept)가 기관별 로컬 시소러스 값이라 일관 검색이 어렵다.",
  "keyword_ref": "해외 소스이므로 공통 G-그룹 재사용이 1차: G-01(핵심 직접)·G-07(구한말)·G-08(일제강점기)·G-19(Corea 구표기 복합)·G-20(시각자료). 여기에 Europeana 특유의 다국어 확장층 = harvester/harvester/europeana.py의 MULTILINGUAL_QUERIES(Corée·Korea-Krieg·guerra di Corea·guerra de Corea·Koreakriget·Korea-oorlog·Kore Savaşı·Séoul·Panmunjom·Chosen AND Japan)를 병렬로 사용. G-11/G-12 인명·지명은 원어 로마자 변형(Séoul·Fusan·Jinsen)과 함께 투입.",
  "crossmap_ref": "고정 RG_MAP은 없음(기록군 부재). 대신 facet 크로스맵으로 대체: qf=DATA_PROVIDER(원소장처) × qf=COUNTRY × qf=YEAR를 keywords_nara.py의 RG_MAP·keywords_tna.py의 시리즈 코드와 연결 — 예: Europeana COUNTRY:France 사진 → Gallica/BnF 원본 및 NARA RG 242 대응 확인, COUNTRY:United Kingdom → TNA WO/FO 계열 대조.",
  "adjacent_mining": "인접상자·참조코드 ±N 방식(NARA/TNA식)은 적용 불가 — 아이템 레벨이라 인접 물리 단위 개념이 없음. 대체 인접마이닝: 동일 edmDatasetName 전수 순회, 동일 dataProvider의 다른 아이템, 그리고 edm:concept/agent/place 엔티티(Entity API)로 인접 주제 확장. 인용 역추적은 dcCreator·edmIsShownAt 원기관 카탈로그로 넘어가 그쪽에서 수행.",
  "cross_archive_combos": [
   "Europeana COUNTRY:France + 'Corée missionnaires' 사진 ↔ Gallica(gallica_search 'Corée') 원본 ↔ 한국사DB(nedb_search) 선교·개항 기록으로 3중 확인",
   "Europeana 'Korea-Krieg'/'Welt im Film Korea' 뉴스릴 ↔ NARA RG 242 노획·공보 영상 ↔ 국가기록원(archives_search) 및 한국사DB HUSAFIK 대조",
   "Europeana COUNTRY:United Kingdom 한국전쟁 자료 ↔ TNA(tna_search) WO 281/FO 371 계열 ↔ 전쟁기념관(warmemo_search) 영연방군 기록",
   "Europeana 지도(TYPE:IMAGE 'Carte de la Corée') ↔ 국립중앙도서관(nlk_search) 고지도 컬렉션 ↔ 원소장처(edmIsShownAt) 카탈로그"
  ],
  "rights_rule": "권리 초판은 아이템의 edm:rights 값으로 1차 기계 판정: CC0/Public Domain Mark → b-A(공개확정), CC-BY/CC-BY-SA·reusability=open → b-B(공개가능추정, 출처표시 조건), In Copyright·부속 라이선스 없음 → b-C(허가필요, 원소장처 문의), rights 필드 없음/불명 → b-D(지위불명, 공개 금지). 단 Europeana 값은 '메타데이터+썸네일' 권리와 '원 객체' 권리가 다를 수 있으므로 최종은 isShownAt 원소장처 조건으로 승격 확인, D등급 및 민감주제(위안부·포로·희생자)는 출판 전 인간 최종 확인 필수."
 },
 "verify": {
  "accurate": true,
  "notes": [
   "Minor internal inconsistency on rights vocabulary count: data_structure/classification says '표준 14종' while rights_rule/rights_access correctly say 'RightsStatements.org 12종 + CC'. RightsStatements.org publishes 12 standardized statements; the '14종' figure is an overcount (the total varies once CC/CC0/PDM are added, so no single fixed count is strictly accurate). Not material — the model, endpoints, and auth are all correct.",
   "Demo key note: 'api2demo' is described as immediately working keyless; in practice Europeana has been phasing shared demo keys toward deprecation, and the actual harvester (europeana.py) requires a real EUROPEANA_API_KEY and does not fall back to api2demo. The demo-key claim is plausible but not exercised by the codebase."
  ],
  "robots": "Live-checked via scrape_plan on https://api.europeana.eu/record/v2/search.json — verdict: robots ALLOWED (crawl permitted; advisory to avoid excessive requests). Consistent with the profile's blocking_notes claim that the REST JSON API is not robots-restricted; access is gated only by wskey rate limits."
 }
}
''')
