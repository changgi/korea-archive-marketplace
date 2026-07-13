#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_nlk — 국립중앙도서관 (National Library of Korea (NLK)) 자료·이용·활용구조 프로파일."""
import json
PROFILE = json.loads(r'''
{
 "name_ko": "국립중앙도서관",
 "name_en": "National Library of Korea (NLK)",
 "category": "domestic",
 "data": {
  "hierarchy": "도서관형 서지 단위(자료 1건 = MARC record/item) 중심 — 아카이브식 fonds/series 계층이 아니라 컬렉션(collection) → 자료유형(type_name: 도서·고문헌·신문·관보·전자자료·비도서) → 개별 서지레코드 → 소장본(권·호)·디지털 원문(권차/호차/면 단위). 대한민국신문아카이브는 제호(신문 108종) → 발행일자(호) → 지면(면) → 기사(article) 단위로 다시 계층화되어 기사 단위 검색이 가능. 컬렉션 라우팅: total(전체 소장자료)·subject(주제별컬렉션 N20103)·newspaper(신문아카이브)·gwanbo(관보 N20301)·exhibit(온라인전시 N20104)·koreanmemory(코리안메모리)·overseas(해외 한국관련자료 N20401).",
  "classification": "KDC(한국십진분류, Korean Decimal Classification) 주분류 + DDC 병용 · 주제명표목표(NLK Subject Headings, 국립중앙도서관 주제명표목) 통제어휘 · 고문헌은 사부분류(경사자집) 및 KDC 병기 · 신문아카이브는 제호 원표기(한자/일본어/옛한글) 색인체계. 실재 스킴만: KDC·DDC·주제명표목·사부분류.",
  "identifiers": "서지 제어번호(NLK control number, 통합검색 상세 org_link의 식별자) · KORMARC 001 제어번호 · ISBN/ISSN(근현대 간행물) · 청구기호(KDC 기반) · 고신문은 제호코드+발행일자+면번호 조합 기사ID · 관보는 호수·발행일 기반. NAID·reference code 같은 아카이브 참조코드 체계는 없음(도서관 식별자 체계).",
  "metadata_standard": "KORMARC(한국문헌자동화목록형식, MARC21 기반 국가표준) 서지기술 · 디지털/OpenAPI 노출은 Dublin Core 계열 경량 필드(title_info·type_name·pub_info·pub_year_info·org_link) · 주제색인은 주제명표목표. 신문 기사는 기사 메타(제호·일자·면·기사명)+본문 OCR 텍스트. ISAD(G)/DACS(아카이브 다층기술규칙)는 적용되지 않음.",
  "scope": "시대: 고문헌(전근대)부터 현대까지 전 시대. Korea-records 1860–1960 핵심 사료층: 대한민국신문아카이브 1883–1960(고신문 108종·기사 약 868만 건, 제호 원표기+본문 OCR) · 관보(대한제국·통감부·조선총독부·미군정·대한민국) · 해외 한국관련자료 · 고문헌. 규모: 국가대표도서관 전체 소장 수천만 건 규모의 통합검색(srchTarget=total) 대상.",
  "digitization": "디지털화 수준 이원적: (1) 신문아카이브·관보·일부 고문헌·주제별컬렉션은 원문 이미지+OCR 전문(全文) 제공(기사·지면 단위 열람/검색 가능), (2) 그 외 다수 소장자료는 서지레코드만 온라인·원문은 관내열람/협약관(디지털열람실) 한정. OpenAPI는 서지 메타+org_link(상세·원문 링크)만 반환하며 원문 바이너리는 미제공."
 },
 "access": {
  "channel": "통합 OpenAPI(GET/XML): https://www.nl.go.kr/NL/search/openApi/search.do?key=<NLK_API_KEY>&apiType=xml&srchTarget=total&kwd=<질의>&pageSize=<n>&pageNum=1 . MCP 도구 nlk_search(query, collection, max_results)로 호출. 중요: API는 collection 인자와 무관하게 항상 srchTarget=total(전체 카탈로그)을 검색한다 — collection은 브라우즈/열람 URL만 바꾼다(total·subject·newspaper·gwanbo·exhibit·koreanmemory·overseas). 컬렉션별 정밀검색은 반환된 열람 URL(예 신문아카이브 nl.go.kr/newspaper/search_list.do?keyword=)로 별도 수행.",
  "auth": "env key: NLK_API_KEY (www.nl.go.kr Open API 신청 발급). 현재 키 설정 완료 — 키 있으면 서버가 OpenAPI 자동검색, 없으면 브라우저 열람 URL + cheliped 폴백 반환.",
  "query_syntax": "핵심 파라미터 kwd(질의어), srchTarget=total(고정), apiType=xml, pageSize(최대 50), pageNum. 자유어 검색 — 표기 변형은 OR가 아니라 개별 질의로 반복 투입(한자/일본어/옛한글 원표기 포함). 필드 세분(제목/저자/발행처)·연도범위 필터는 OpenAPI 파라미터로 제한적이므로 정밀 필터는 열람 URL(웹 검색 UI)에서 수행. 신문아카이브 기사 전문검색은 newspaper 열람 URL의 keyword= 사용.",
  "response_format": "XML. <total>(총건수) + 반복 <item> 요소: title_info(제목)·type_name(자료유형)·pub_info(발행처/저자)·pub_year_info(발행연도)·org_link(상세/원문 링크, '/' 시작 시 https://www.nl.go.kr 접두). 페이징은 pageNum/pageSize. 오류 시 <error>/<msg>. JSON은 apiType 변경으로 가능하나 본 채널은 xml 고정.",
  "blocking_notes": "OpenAPI 채널은 robots/JS렌더 무관(서버-투-서버 XML). 단 웹 열람/브라우즈 UI(신문아카이브·코리안메모리·전시·상세페이지)는 JavaScript 렌더 → 일반 HTTP는 빈 목록이므로 cheliped 브라우저 스크래핑 필요. rate-limit: 발급키 일일 호출한도 존재(초과 시 <error>), pageSize≤50. 지오블록 없음(국내외 접근 가능). 원문 이미지 뷰어는 세션/뷰어 기반이라 직접 URL 수집 제한.",
  "rights_access": "신문아카이브 고신문(1883–1960)은 저작권 만료 — 출처표기 시 자유이용(PD). 관보(정부 저작물)도 사실상 자유이용이나 재현물 이용조건 확인. 그 외 디지털화 자료·고문헌 이미지는 개별 권리·공공누리(KOGL) 유형 확인 필요, 다수는 관내열람/협약 전제. OpenAPI는 메타+링크만 제공하므로 원문 대량수집은 뷰어 접근권·이용약관 확인 후."
 },
 "use": {
  "mismatch_summary": "① 언어적: 최강으로 나타남 — 고신문 제호·기사가 당대 원표기(한자·일본어·옛한글)로 색인되어 현대 한글/영문 질의로는 미검. 예 '조선일보'는 문제없으나 '大韓每日申報'·'皇城新聞'·통감부기 일본어 표기·옛한글 표제는 원표기로만 걸림. 국문·한자·영문(NLK는 해외자료라 로마자 Chosen/Corea도) 병렬 반복 투입 필수. ② 분류학적: KDC/주제명표목 축과 사건·인물 축의 불일치 — 특정 사건이 KDC 주제분류(예 역사 900번대) 밑에 흩어져 단일 주제어로 포괄 안 됨. ③ 기술관행적: 서지레벨 기술이 당대 간행물명·발행처 기준이라 사건명이 표제에 없으면 서지검색에서 누락 → 신문아카이브 본문 OCR 전문검색으로 우회.",
  "keyword_ref": "keywords_nlk (국내용 신설 세트). 국문/한자/원표기 축으로 재구성 — 해외 공통 G-그룹(keywords_common의 G-01~G-22)과 NARA/TNA 로마자 표기를 대응(cross-lingual pairing): 예 G-07 구한말↔대한제국·개항·을사조약·한자 인명, G-08 일제강점기↔독립운동·삼일운동·총독부·위안부(慰安婦) 한자병기, G-11 인물 로마자(Kim Koo)↔김구/金九. 신문아카이브 검색 시 제호 원표기 리스트를 keyword로 사용.",
  "crossmap_ref": "KDC/주제명표목 ↔ NARA RG_MAP(keywords_nara.RG_MAP) 및 TNA 부처코드 간 개념 교차매핑. 예: 관보·총독부 자료 ↔ RG 242(노획 외국문서, Chosen)·RG 260(SCAP); 미군정·해방기 신문 ↔ RG 332/338(주한미군·KMAG); 외교 ↔ RG 59/84(국무부·공관). 신문아카이브 기사는 사건 축으로 RG 111/342(영상·항공사진) 발굴의 국내 1차 대조군.",
  "adjacent_mining": "가능(형태 변형). NARA RG piece 순회나 TNA 참조코드 ±15 piece식 인접확장과 달리, NLK는 (a) 신문아카이브에서 특정 제호×발행일 범위를 이웃 일자로 순회(사건 전후 지면 스캔), (b) 동일 KDC 청구기호 대역 브라우즈로 인접 서지 발굴, (c) org_link 상세페이지의 관련자료·동일주제명표목 링크 역추적. 참조코드 인용 역추적은 도서관 식별자 특성상 약하므로 제호·일자·주제명표목 축으로 대체.",
  "cross_archive_combos": [
   "신문아카이브 고신문(사건 국내 당대 보도) ↔ NARA RG 242 노획문서/RG 111 영상 ↔ 국사편찬위 한국사DB(nedb_search) 근현대신문·HUSAFIK — 동일 사건 3축 교차검증",
   "국립중앙도서관 관보(총독부·미군정 공포) ↔ 국가기록원(archives_search) 정부생산문서 ↔ NARA RG 260 SCAP — 법령·인사 공식기록 대조",
   "해외 한국관련자료(overseas 컬렉션 서지) ↔ NARA RG 59/84 국무부·공관 ↔ TNA FO 371(FK코드) — 해외소재 원본의 국내 서지 확인",
   "신문아카이브 인물기사(원표기 인명) ↔ 한국사DB 인명 한자검색 ↔ NARA RG 319 G-2 인물파일 — 인물 신원·활동 교차",
   "고신문 의병·독립운동 보도 ↔ 한국사DB 독립운동 DB ↔ 국가기록원 판결문·수형기록 — 사건-인물-처벌 연결"
  ],
  "rights_rule": "1차 자동초판(judge_rights/ledger.auto_rights 계열): 신문아카이브 고신문(1883–1960) = A/PD 상당(저작권 만료, 출처표기 자유이용). 관보 등 정부저작물 = 자유이용 추정하되 재현물 이용조건·공공누리 유형 확인. 그 외 디지털화 자료·고문헌 이미지·현대 간행물 = D(지위 불명) 초판 → 공공누리(KOGL) 유형/개별 권리·관내열람 여부 수동 확인 후 등급 확정. 최종 확정은 사람이 서면 근거로 수행."
 },
 "verify": {
  "accurate": true,
  "notes": [
   "Minor imprecision (not material): profile states the OpenAPI is always called with srchTarget=total for any collection and 'collection only changes the browse URL.' In server.py only total/subject/gwanbo/overseas (api_ok=True) trigger the server-side OpenAPI call; newspaper/exhibit/koreanmemory (api_ok=False) never hit the API and return a browse/열람 URL only. Endpoint, auth, field names, and classification schemes (KDC, DDC, 주제명표목표, 사부분류, KORMARC) are all correct."
  ],
  "robots": "Allowed. scrape_plan on https://www.nl.go.kr/NL/contents/search.do?srchTarget=total&kwd=... returned 'robots 허용(단 JS 렌더면 브라우저 필요)' — robots permits access but the web browse UI is JS-rendered so a browser tool is needed; the server-to-server OpenAPI XML channel is unaffected by robots/JS."
 }
}
''')
