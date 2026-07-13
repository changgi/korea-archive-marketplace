#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_tna — 영국 국립기록관 (TNA Discovery) (The National Archives (UK) — Discovery) 자료·이용·활용구조 프로파일."""
import json
PROFILE = json.loads(r'''
{
 "name_ko": "영국 국립기록관 (TNA Discovery)",
 "name_en": "The National Archives (UK) — Discovery",
 "category": "overseas",
 "data": {
  "hierarchy": "5단계 위계: department(부처, lettercode) → division/series(문서군 시리즈) → subseries → piece(철, 대출·열람 단위) → item(건). 실무 핵심은 series→piece→item. 예: FO 371(series) / 84053(piece) / 개별 문서(item). 한국 자료는 특정 series 아래에 분산되며, 1906–1919 FO 371 한국 파일은 中 Code 10·日 Code 23 하위분류에, 1920년 이후는 FK 등록코드(FK1015 정치, FK1661 선전) 아래에 놓인다.",
  "classification": "TNA 부처 문자코드 체계(lettercode / department code): FO(Foreign Office 외무부), WO(War Office 육군부), ADM(Admiralty 해군부), AIR(Air Ministry 공군부), CAB(Cabinet 내각), CO(Colonial Office 식민지부), DO(Dominions Office 자치령부), FCO(Foreign & Commonwealth Office, 1968-), PREM(Prime Minister's Office 수상실), DEFE(Ministry of Defence 국방부), CN·WORK(사진·공공건물). 각 lettercode 하위에 series 번호가 부여됨(FO 371, WO 281 등). 실제 존재 스킴이며 임의 명명 아님.",
  "identifiers": "Reference code(참조코드) 체계: lettercode + series번호 + '/' + piece번호(+ '/' item). 정규형 /^[A-Z]+ \\d+\\/\\d+$/ 예: 'FO 371/84053', 'WO 281/1206', 'CAB 128/17'. 카탈로그 레코드 단위로는 Discovery 내부 GUID(record id, details/r/{id} URL)가 병존. 등록코드(FK1015 등)는 series 내부 부가 분류로 검색어에 활용.",
  "metadata_standard": "국제 표준 ISAD(G) 기반 다층 기술(General International Standard Archival Description). 레코드 필드: reference, title, description, coveringDates, department, context(계층 맥락), heldBy(소장처). Discovery는 TNA 소장 기록뿐 아니라 영국 전역 2,500여 아카이브의 기술정보를 통합(union catalogue)하므로 heldBy로 소장처 구분 필요.",
  "scope": "1860–1960 한국 관련 발굴 대상 시기 전체를 포괄. 구한말(FO 17·46·262·483 공관·확인문서), 일제강점기(FO 371 병합 전후), 한국전쟁(WO 281 전쟁일지·CAB·DEFE·PREM 정책문서), 전후·현대(FCO 1968-). 전체 소장 규모는 1,100만+ 기록물, Discovery 통합 카탈로그는 수천만 기술항목. 한국 직접 관련은 수천~수만 건 규모로 series에 분산.",
  "digitization": "혼합. 다수는 카탈로그 기술정보(메타데이터)만 온라인 제공되고 원문은 미디지털화 상태로 Kew 열람실 방문 또는 유료 copy 주문 필요. 일부 series·piece는 스캔 PDF가 Discovery details 페이지에서 다운로드 가능(다수 유료, 일부 무료 공개). 사진·지도(CN, WORK)는 부분 디지털화."
 },
 "access": {
  "channel": "Discovery 검색 API. Endpoint: https://discovery.nationalarchives.gov.uk/API/search/records — 파라미터 sps.searchQuery(검색어), sps.resultsPageSize(페이지당 건수), sps.page(페이지 번호). MCP 도구 tna_search가 이 엔드포인트를 래핑하며, tna_adjacent_mine이 reference 주변 piece 번호를 ±radius 순회. 레코드 상세는 https://discovery.nationalarchives.gov.uk/details/r/{id}.",
  "auth": "none — API 키 불요. 공개 접근.",
  "query_syntax": "sps.searchQuery에 전문(full-text) 검색어 투입. /^[A-Z]+ \\d+\\/\\d+$/ 에 매칭되는 참조코드(예 'FO 371/84053')는 자동으로 큰따옴표 정확구 처리되어 해당 piece를 정밀 조준. 일반 키워드는 그대로 투입('Korea armistice', 'FO 371 FK1015', 'WO 281 Glosters'). lettercode+series 접두('FO 371 Korea')로 series 범위 좁히기 가능. Discovery UI에서는 covering date·department·held-by·closure status 패싯 필터 제공.",
  "response_format": "JSON. 최상위 records[] (방어적 파싱: records/Records), count(총건수), 각 레코드에 id/reference/title/description/coveringDates/department/context/heldBy. 페이징은 sps.page + sps.resultsPageSize(최대 100 권장)로 순회; page*pageSize ≥ count면 종료.",
  "blocking_notes": "공개 API·키 불요로 서버측 fetch가 실제 결과 반환(dead-end 없음). 명시적 rate-limit 문서는 없으나 예의상 요청 간 sleep(수집기 기본 1.0–1.2초) 적용. 지오블록 없음. robots.txt는 API 경로 접근을 막지 않으나(검색 API는 프로그램 접근 용도) 대량 크롤 시 간격 준수 권장. 응답 필드 대소문자·존재 여부가 레코드 종류마다 달라 방어적 파싱 필수.",
  "rights_access": "Crown copyright. 대부분의 정부 생산 기록은 Open Government Licence(OGL) 하에 재이용 가능(출처표시 조건). 단 메타데이터 접근과 원문 재이용은 별개: 미디지털화 원문은 Kew 열람 또는 유료 사본 주문 필요, 일부 디지털 스캔은 유료 다운로드. 30년(현행 20년 이관)·closure 규정으로 일부 근현대 파일은 폐쇄(closed) 또는 부분 편집(retained) 상태일 수 있어 details 페이지의 closure status·access conditions 확인 필수."
 },
 "use": {
  "mismatch_summary": "언어적 부정합: 영국 외교문서는 'Korea'와 함께 구표기 'Corea/Corean'을 20세기까지 지속 사용하고, 일제기 문서는 'Chosen'(조선의 일본식 로마자)을 병용 — 단일 'Korea' 검색은 상당량을 누락. 분류학적 부정합: 한국은 독립 series가 없고 中 Code 10(FO 371 중국)·日 Code 23(일본)·공관문서(FO 17/46/262)·영연방 경유(CO/DO) 등 '제3국 경유' 분류에 흩어져, 주제 검색으로는 계층 위치를 예측할 수 없음. 기술관행적 부정합: ISAD(G) 상위 series 기술은 개괄적이어서 piece/item 제목에 'Korea'가 없어도 내용상 한국 관련인 경우가 많아(Far East·38th parallel·Panmunjom 등 맥락어) 인접 확장·인용 역추적 없이는 발굴 불가.",
  "keyword_ref": "해외 기존 세트 사용: 공통 G-01~G-22 + TNA 전용 14 전략 레이어 T-01~T-14(1,222 쿼리, 고유 1,210). direct(T-01~03,14)는 G-01/G-02~06/G-07~10/G-20을 영국군·외교 관행어로 재가중, code(T-04~09)는 TNA_DEPT_CODES × core6 어휘 조합, indirect(T-10~11)는 G-17 맥락어 + 영연방 경유, citation(T-12~13)은 CITATION_SEEDS 22건 + piece ±ADJACENT_RANGE. NARA 교차 시 N-/RG 그룹 병용.",
  "crossmap_ref": "query_bank 'RG' 그룹(NARA 28개 Record Group 교차 매핑) + query_cheatsheet 'NARA RG 교차'절. TNA lettercode↔NARA RG 대응 예: FO 371/공관문서 ↔ RG 59(국무부)·RG 84(재외공관 Seoul), WO 281 전쟁일지 ↔ RG 407·RG 338(미 육군 작전기록), 일제기 Chosen ↔ RG 242(노획 외국문서). 동일 사건을 영·미 양측 lettercode/RG로 이중 조준.",
  "adjacent_mining": "적용 가능 — 핵심 기법. tna_adjacent_mine(reference, radius)이 검증된 참조코드(예 FO 371/84053) 주변 piece를 ±radius 순회하며 title+description을 korea_score(korea/corea/chosen/seoul/panmunjom 등 어휘 카운트)로 채점, score≥1이고 local_id가 동일 series 접두인 레코드를 ★승격후보로 제시. T-12 인용 시드 22건(Farrar-Hockley·Yasamee&Hamilton·Shaw) → T-13 인접 확장으로 series 발굴(논문 214 series·승격률 93% 대응). 승격 후보는 수동 검증 후 정식 편입.",
  "cross_archive_combos": [
   "한국전쟁 영국군 전투(임진강·Glosters): TNA WO 281/CAB 128 ↔ NARA RG 407·RG 338(미8군 작전기록) ↔ 한국사DB HUSAFIK(주한미군사) 및 국방부 군사편찬연구소 전사 — 3자 교차로 작전 사실·날짜 확정",
   "일제강점기 조선 관련: TNA FO 371 'Chosen/Corea' ↔ NARA RG 242 노획문서(Chosen) ↔ 국가기록원 조선총독부 기록 — 동일 사건의 영·미·조선총독부 3원 대조",
   "구한말 조약·공관: TNA FO 17/FO 46/FO 262/FO 483(Confidential Print) ↔ NARA RG 59(국무부 Corea) ↔ 한국사DB 구한국외교문서 — 조약 체결 정황 교차검증",
   "정전회담: TNA FO 371 Panmunjom·armistice ↔ NARA RG 59/RG 218(합참) ↔ 국사편찬위 한국사DB 정전협정 문서군",
   "노획문서 계보: 국가기록원 노획문서 ↔ NARA RG 242 ↔ TNA 영연방(CO 1030/DO 35) 경유 극동 정보보고 — 문서 이동·출처 계보 추적"
  ],
  "rights_rule": "초판(first-pass) 판정: Crown copyright 기록은 OGL 적용 시 출처표시로 재이용 가능(초판 통과), 단 (1) closure status가 open이고 (2) 원문 디지털 사본을 합법 취득했으며 (3) 제3자 저작권(사진가·사기업 문서 등) 미포함일 때만 자동 통과. 폐쇄·retained·유료 스캔·비OGL 제3자 권리는 보류(judge_rights 도구로 정밀 판정). 근거 법령은 Crown copyright/OGL, 미국 교차분은 17 U.S.C. §105·36 CFR 1254.62. 모든 판정은 출판 전 인간 최종 확인 필수, D등급(폐쇄/편집)은 공개 금지."
 },
 "verify": {
  "accurate": true,
  "notes": [
   "'CN·WORK(사진·공공건물)': WORK=Office of Works/public buildings is correct, but CN is not a photographs lettercode (CN=Contributions Agency). TNA has no single dedicated photographs lettercode — photos are dispersed (e.g. COPY 1, INF). Mislabel, minor.",
   "Post-1920 'FK' registry codes (FK1015 political / FK1661 propaganda): the FO 371 registry country-code scheme is genuine (China Code 10, Japan Code 23 are documented), but these specific FK sub-codes are unverified and should be treated as illustrative rather than confirmed.",
   "Core facts all correct: endpoint /API/search/records with sps.searchQuery/sps.resultsPageSize/sps.page, auth=none, details/r/{id}, reference-code format, ISAD(G), lettercodes FO/WO/ADM/AIR/CAB/CO/DO/FCO/PREM/DEFE, NARA RG cross-maps (RG 59/84/407/338/242/218), OGL/Crown copyright, 17 U.S.C. §105, 36 CFR 1254.62."
  ],
  "robots": "Live scrape_plan check: UI search path /results/r?_q=Korea is robots-BLOCKED (verdict: browser tool required); API path /API/search/records?sps.searchQuery=Korea is robots-ALLOWED. Confirms profile's blocking_notes — robots.txt permits programmatic API access while restricting the browse UI. Server-side fetch of the API returns real results (no dead-end)."
 }
}
''')
