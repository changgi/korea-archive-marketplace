#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_nara — 미국 국립문서기록관리청 (NARA) (U.S. National Archives and Records Administration (NARA)) 자료·이용·활용구조 프로파일."""
import json
PROFILE = json.loads(r'''
{
 "name_ko": "미국 국립문서기록관리청 (NARA)",
 "name_en": "U.S. National Archives and Records Administration (NARA)",
 "category": "overseas",
 "data": {
  "hierarchy": "연방 출처주의(provenance) 기반 다층 계층: Record Group(RG) → Entry/Series(기술 시리즈) → Subseries → Box(상자) → Folder/File Unit(철) → Item(건). 카탈로그 levelOfDescription은 record group/collection/series/fileUnit/item 값으로 노출되며 ancestors[] 배열로 상위 RG를 역참조. 한국 관련은 RG 59·84·242·319·338·342·389 등 28개 RG에 분산.",
  "classification": "Record Group(RG) 체계 — 출처(생산기관)별 물리적 배열. 국무부 계열은 RG 내부에 Decimal File System(십진분류: 극동/한국 국가코드 접두 795 정치·군사, 895 내정·경제, 695 대외관계)을 중첩. 노획문서는 별도 컬렉션 RG 242(National Archives Collection of Foreign Records Seized). RG는 임의 발명 불가 — 실제 NARA 공인 번호만 사용.",
  "identifiers": "NAID(National Archives Identifier) — 레코드 단위 고유번호, 카탈로그 영구 URL https://catalog.archives.gov/id/{naId}. 병행 식별자: localIdentifier(예 '111-SC-...' 형식의 RG-시리즈 로컬번호), recordGroupNumber(정수), Entry 번호(A1/UD/PI Entry). NAID가 최상위 안정 식별자.",
  "metadata_standard": "DACS(Describing Archives: A Content Standard) 기반 다계층 기술 + Lifecycle Data Requirements Guide. 카탈로그 API v2는 record 객체(title, productionDates[].logicalDate, recordGroupNumber, levelOfDescription, generalRecordsTypes, digitalObjects[], ancestors[])로 정규화된 JSON을 반환. 17 U.S.C. §105에 따라 연방정부 직무저작물은 저작권 없는 퍼블릭도메인.",
  "scope": "1789년 연방정부 수립 이후 전 연방기록. 한국 관련(1860–1960)은 1871년 신미양요·1882년 조미수호통상조약부터 개항기·일제강점기(전전 자료는 Chosen/Tyosen으로 색인)·미군정(USAMGIK 1945–48)·한국전쟁(1950–53)·전후 원조(ECA/USOM)까지. 규모: 수십억 페이지 문서 + 종이 카드 카탈로그 약 750만 장.",
  "digitization": "부분 디지털화. 온라인 자료는 record.digitalObjects[] 존재 여부로 판별(availableOnline). 사진·필름(Signal Corps, Universal Newsreel, RG 242 노획필름)과 국무부 Decimal File 일부는 스캔 제공, 그러나 카드 카탈로그 750만 장 대부분과 다수 시리즈는 미전산화 → 온라인 0건이 자료 부재를 의미하지 않음('미전산화 후보'로 기록)."
 },
 "access": {
  "channel": "NARA Catalog API v2. 엔드포인트: https://catalog.archives.gov/api/v2/records/search . 서버 측 도구 nara_search가 이 엔드포인트를 호출. 응답 본문 경로: body.hits.hits[]._source.record.",
  "auth": "HTTP 헤더 x-api-key = NARA_API_KEY(서버 환경변수에 구성됨). 키는 Catalog_API@nara.gov 발급, 통상 월 약 10,000쿼리 한도. 클라이언트는 키를 직접 다루지 않고 서버가 헤더에 주입.",
  "query_syntax": "GET 쿼리 파라미터: q(전문 검색어), limit(페이지당 건수, 최대 100 권장), page(1부터), recordGroupNumber(RG 정수 필터 — RG 교차 정밀 쿼리 핵심), typeOfMaterials=Moving Images(자료유형 필터), availableOnline=true(온라인 한정). 표기 변형을 OR/병렬 투입: Korea OR Corea OR Chosen OR Tyosen, 지명 Keijo(서울)·Fusan/Pusan·Jinsen(인천)·Heijo(평양)·Genzan(원산)·Chosin(장진). 'Chosen'은 영어 일반어와 충돌하므로 Japan/newsreel/film 등과 AND 조합.",
  "response_format": "JSON. 경로 body.hits.hits[]._source.record. 주요 필드: naId, localIdentifier, title, productionDates[].logicalDate, recordGroupNumber(또는 ancestors[].recordGroupNumber), levelOfDescription, generalRecordsTypes, digitalObjects[]. 총건수 body.hits.total.value. 페이징: page×limit ≥ total 이거나 hits 비면 종료.",
  "blocking_notes": "robots·지오블록 없음(공식 REST API). 실질 제약은 API 키 월간 쿼리 쿼터(약 10,000)와 페이지네이션 부담 — RG 교차 결합 쿼리로 호출 수 억제. 대량 수집 시 요청 간 sleep(~1s) 권장. 카탈로그 미전산화분은 API로 접근 불가(구조적 공백).",
  "rights_access": "17 U.S.C. §105에 따라 미 연방정부 직무저작물은 저작권 없는 퍼블릭도메인 — 원문 열람·다운로드·복제·재배포 자유(디지털화된 범위 내). 단 RG 242 노획 외국문서/노획필름은 미국 정부 직무물이 아니어서 §105 적용 안 됨(권리 지위 불명). 미전산화 원본은 College Park(Archives II) 등 현지 열람 또는 복제 신청 필요."
 },
 "use": {
  "mismatch_summary": "①언어적: 전전(1860–1945) 한국 자료는 Korea가 아니라 Chosen/Tyosen/Corea, 지명은 일제식 로마자 Keijo·Fusan·Jinsen·Heijo로만 색인 — 현대 표기 단일 검색은 0건을 낸다. ②분류학적: 한국은 독립 분류가 없고 출처기관 RG(59·84·242·319·338·342·389 등 28개)와 국무부 Decimal File 795/895 국가코드 속에 숨어 있음 — RG·십진코드를 알아야 열린다. ③기술관행적: 당대 부서 어휘(USAMGIK, KMAG, ATIS, captured enemy documents)로 기술되어 주제어 검색을 회피 → 조직·문서번호 어휘로 접근해야 한다.",
  "keyword_ref": "keywords_nara.py의 NARA 전용 7그룹 — N-01 미군정·원조기관(US_GOV_AGENCIES), N-02 미군 부대(US_MILITARY_UNITS), N-03 미국 인물(US_PEOPLE), N-04 정보기관(US_INTEL), N-05 NARA 특유 시리즈·문서번호(NARA_SERIES: Decimal File 795/895/695, ATIS, captured enemy documents), N-06 조약·협정(US_TREATIES), N-07 미국 소재 한국 특화(US_LIBERATION) + ONLINE_PRIORITY(N-08). 공통 22그룹(keywords_common: G-01~G-22)의 표기변형·전쟁·시대·인물·시각자료 세트와 합산 투입.",
  "crossmap_ref": "keywords_nara.py의 RG_MAP(28개 RG → (기관 설명, 교차 키워드)). Phase 9(P9-rgcross)에서 recordGroupNumber 필터 × 표기변형 키워드로 63개 결합 쿼리를 생성해 정밀도 회복. 핵심 매핑: RG 59/84(국무부·공관 + Korea/Corea/Seoul/Pusan), RG 242(노획문서 + Chosen/Corea), RG 319(G-2 정보 + Korean War), RG 338(육군사령부 + KMAG), RG 342(공군), RG 389(헌병감실 + Korean POW).",
  "adjacent_mining": "부분 적용 가능. TNA식 참조코드 ±N 순회와 달리 NARA는 RG→Entry→Box→Folder 물리 배열이므로, 검증된 시리즈(Entry) 내에서 Box/Folder 인접 순회 및 동일 localIdentifier 접두(예 '111-SC-*') 전수 스캔으로 미색인 인접 항목을 확장. RG 242·Decimal File 795/895는 국가코드 블록 단위 전수 스캔이 유효. 카탈로그 미전산화 시리즈는 finding aid(Entry 목록) 기반 오프라인 인접 추적으로 보완.",
  "cross_archive_combos": [
   "국가기록원 노획문서(RG 242 이관·복본) ↔ NARA RG 242 원본(nara_search + recordGroupNumber=242, Chosen/Corea) ↔ 한국사DB HUSAFIK(주한미군사) — 노획 북한문서·미군정 통치기록 3자 대조",
   "NARA RG 338/554 KMAG·극동사령부 문서 ↔ 국가기록원 미군정 이관철(archives_search) ↔ 전쟁기념관 아카이브(warmemo_search) 한국전쟁 군사기록 교차",
   "NARA RG 59/84 국무부 Decimal File 795.00/895.00 ↔ 한국사DB 근현대 외교문서(nedb_search) ↔ 국립중앙도서관 해외한국관련자료 컬렉션(nlk_search)로 조미조약·개항기 외교 검증",
   "NARA RG 389 Korean POW·RG 319 G-2 ↔ 전쟁기념관 포로·구술(warmemo_search) ↔ 정보공개포털(foia_search) 미공개분 정보공개청구",
   "NARA Signal Corps 사진(RG 111, generalRecordsTypes 사진 / typeOfMaterials=Moving Images 필름) ↔ 국립중앙도서관 코리안메모리·신문아카이브(nlk_search) 시각자료 대조"
  ],
  "rights_rule": "권리 초판 자동 판정: 미 연방정부 직무저작물(RG 59·84·111·208·306·319·338·342 등 미국 정부기관 생산물) → 17 U.S.C. §105 퍼블릭도메인, 등급 B(PD 추정, 공개 가능). Universal Newsreel → 권리 양도 B. 예외: RG 242 노획 외국문서·노획필름 → §105 비적용, 권리 지위 불명 D(공개 금지, 열람·인용만). March of Time 등 편집본 → 기증자 허가 C. 민감 주제(포로·위안부·학살·희생자)는 등급과 별도로 피해자 존엄 윤리기준 문구를 권리 절에 병기. 최종 확정은 judge_rights 도구로 검증."
 },
 "verify": {
  "accurate": true,
  "notes": [
   "Minor: blocking_notes/rights_access state 'robots·지오블록 없음', but a live scrape_plan check of the base catalog URL returned a robots-blocked verdict. Not a structural error (the authenticated Catalog API v2 with x-api-key is not governed by robots.txt), but the 'no robots' claim is contradicted by the site's robots.txt at the crawl level."
  ],
  "robots": "scrape_plan verdict for https://catalog.archives.gov/api/v2/records/search = robots-blocked ('robots 차단 → 브라우저 도구로 열람'); tool advises using the agent browser to open and tabulate results then report_template. Note: access via the official REST API + x-api-key is unaffected by robots.txt."
 }
}
''')
