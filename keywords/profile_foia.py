#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_foia — 정보공개포털 (Info Disclosure Portal (open.go.kr)) 자료·이용·활용구조 프로파일."""
import json
PROFILE = json.loads(r'''
{
 "name_ko": "정보공개포털",
 "name_en": "Info Disclosure Portal (open.go.kr)",
 "category": "domestic",
 "data": {
  "hierarchy": "기관(중앙행정기관·지방자치단체·교육청·공공기관) → 부서 → 결재문서 원문(건) 단위. 세 축: (1)원문정보공개 = 이미 결재·공개 완료된 정부 결재문서 원문 전문, (2)사전정보공표 = 기관이 선제 공표하는 목록·자료, (3)정보공개청구 = 미공개분을 청구번호 단위로 획득. 최소 기술 단위는 결재문서 1건(기안→검토→결재 라인 포함).",
  "classification": "정부기능분류체계(BRM, Business Reference Model)의 정책분야-정책영역-대기능-중기능-소기능-단위과제 계층 + 기관·부서 조직분류. 이관·보존 단계에서는 공공기록물법상 '기록물분류기준표'(단위과제별 보존기간 책정)로 연결. KDC/DDC 같은 도서분류가 아니라 행정 기능분류 체계임.",
  "identifiers": "문서 생산등록번호(등록번호)·기안문서번호, 정보공개청구 시 부여되는 청구접수번호, 원문정보공개 문서별 상세 URL 파라미터 ID. 이관 기록은 국가기록원 관리번호(생산기관코드+연도+일련)와 접점.",
  "metadata_standard": "공공기관의 정보공개에 관한 법률(정보공개법) 공개 항목 규격 + 공공기록물 관리에 관한 법률(공공기록물법) 시행령의 기록관리 메타데이터(국가기록원 NAK 표준, KS X ISO 23081 계열). 표제·생산기관·생산일자·결재정보·보존기간 필드 중심.",
  "scope": "제도상 원문정보공개는 정부3.0(2014) 이후 생산·결재 문서가 중심 → 1860–1960 사료가 원문으로 직접 올라오지는 않는다. 이 시기 발굴에서의 실질 가치는 '정보공개청구' 채널로 각 기관(외교부 외교사료관, 국방부·병무청, 국가기록원 이관분)이 보유한 미공개·비공개 근현대 기록을 열람 요청하는 데 있다. 규모: 전 공공기관 일일 축적 원문 수억 건.",
  "digitization": "원문 첨부는 PDF·HWP(한글)·이미지 스캔. 전문검색은 결재문서 표제 및 본문 텍스트 색인 기반. 상세 원문 다운로드·정보공개청구 결과 교부는 로그인 세션에서 제공."
 },
 "access": {
  "channel": "정보공개포털 open.go.kr/othicInfo/infoList/orginlInfoList.do (원문정보공개). Login-gated → 서버가 대신 페치하지 않으며(server does NOT fetch), 도구는 웹검색/브라우저 핸드오프(web-search/browser handoff)만 반환한다. 미공개 문서는 정보공개청구(정보공개청구)로 요청. 기관별 원문목록은 data.go.kr '원문정보공개' OpenAPI로도 별도 제공.",
  "auth": "포털 자체에는 공개 API 키가 없음(none from portal). 원문 상세 열람·정보공개청구 제출은 회원가입 후 로그인(공동인증서/간편인증) 필수. 우회 데이터 채널인 data.go.kr '원문정보공개' API는 별도 인증키(data.go.kr 서비스키) 필요.",
  "query_syntax": "searchKeyword=<질의> 파라미터로 결재문서 표제 전문검색. 필터: 기관(중앙·지자체·공공기관)·부서·생산기간·분류. 사건명 직접검색보다 기관·부서명 + 결재문서 표제 관용어 조합이 회수율 높음.",
  "response_format": "HTML(JavaScript 렌더 + 로그인 세션 쿠키). keyless JSON 응답 없음. 대체 채널 data.go.kr API는 JSON/XML(페이징 pageNo/numOfRows).",
  "blocking_notes": "로그인 게이트 + JS 렌더 + 세션 쿠키로 서버측 자동 페치 불가 → 브라우저/웹검색 핸드오프. robots 및 rate-limit 준수, 지오블록은 없으나 인증 없이는 상세 접근 차단. 자동화 시 세션 유지·요청 간격 필요.",
  "rights_access": "원문정보공개 목록에 노출된 문서 = 이미 공개결정 완료분 → 열람·활용 가능(공공누리 KOGL 유형 및 개인정보 마스킹 확인). 정부 공문서 상당수는 저작권법 제7조(고시·공고·훈령 등 보호받지 못하는 저작물)에 해당 가능. 미공개·부분공개분은 정보공개청구(청구→원칙 10일 내 결정, 정보공개법 제9조 비공개 사유 가능) 결과에 따라 접근권 결정."
 },
 "use": {
  "mismatch_summary": "언어적 부정합: 결재문서 표제가 행정 관용어·한자어·약어로 위장('~에 관한 건', '~계획(안)', '~지침 시달', '~보고')되어 사건명 직접검색이 실패 → 관용어 슬롯을 기관·부서명과 결합해야 함. 분류학적 부정합: 역사적 사건이 현재 정부기능분류(BRM 단위과제)로 흩어져, 주제 기준이 아닌 기능·조직 기준으로 산재. 기술관행적 부정합: 원문정보공개는 표제 중심이고 본문 요약·주제어(subject)가 빈약해 descriptive 메타데이터가 부족 → 표제어와 결재라인·문서번호로 역추적해야 함.",
  "keyword_ref": "신설 국내 키워드셋 keywords_foia (기관명·부서명·사건명 + 결재문서 표제 관행어: '~에 관한 건/계획/보고/지침/시달/승인/협조요청'). 근현대 사건은 keywords_common의 G-07~G-10(구한말·일제·해방·전후)에서 인물·지명·사건 시드를 가져와 국문·한자 표제어로 변환해 결합.",
  "crossmap_ref": "keywords_nara.RG_MAP (RG↔노획문서 교차결합, 특히 RG 242 '노획 외국 문서', RG 59/84 외교, RG 407 군). 국내축은 정부기능분류(BRM 단위과제) ↔ 국가기록원 기록물분류기준표(생산기관코드) 매핑으로 청구 대상 기관을 특정.",
  "adjacent_mining": "적용 가능(단 로그인 제약). 한 결재문서의 생산등록번호·단위과제·결재라인·선행/후속 관련문서를 실마리로 동일 부서·동일 단위과제의 인접 문서를 역추적. tna_adjacent_mine식 인접 채굴을 국내 결재문서 번호체계에 이식 — 브라우저 핸드오프로 목록 순회.",
  "cross_archive_combos": [
   "국가기록원 노획문서 ↔ NARA RG 242 ↔ 한국사DB HUSAFIK (정보공개청구로 국가기록원 미공개 이관분 확인)",
   "외교부 정보공개청구(외교사료관 이관 근현대 외교문서) ↔ NARA RG 59/84 ↔ 한국사DB 주한미군 문서",
   "국방부·병무청 정보공개청구(병적·부대) ↔ 국가기록원 병적기록 ↔ NARA RG 407 (한국전쟁 부대사)",
   "지자체 정보공개(local_gov_search seoul_opengov) ↔ 서울기록원 seoul_archives_search ↔ 지방사 사건 결재문서 교차"
  ],
  "rights_rule": "1차 판정: 원문정보공개 목록에 노출된 문서는 공개결정 완료 → 열람·활용 가능(공공누리 KOGL 유형·개인정보 마스킹 확인, 정부 공문서는 저작권법 제7조 비보호 가능). 미노출·비공개 표시분은 '미판정' → 정보공개청구 제기 후 결정(공개/부분공개/비공개, 정보공개법 제9조 비공개 사유)으로 확정. judge_rights에는 '공개결정 여부 + 공공누리 유형 + 청구 필요성'을 함께 전달."
 },
 "verify": {
  "accurate": true,
  "notes": [
   "Scope figure overstated: '전 공공기관 일일 축적 원문 수억 건' implies hundreds of millions of documents accumulate DAILY. Hundreds of millions is roughly the cumulative total of 원문정보공개 holdings across all agencies, not a per-day rate. Reword as cumulative total, not daily.",
   "Minor: endpoint host is www.open.go.kr (profile drops the 'www.'); non-material but the working URL in server.py is https://www.open.go.kr/othicInfo/infoList/orginlInfoList.do."
  ],
  "robots": "scrape_plan on https://www.open.go.kr/othicInfo/infoList/orginlInfoList.do returned '판정: robots 미확인(fetch failed)' — robots.txt could not be fetched, so neither allow nor disallow was confirmed. Tool advises opening the URL with an agent browser tool (login/JS-gated) and tabulating results rather than server-side scraping. This is consistent with the profile's blocking_notes/channel claim that the server does not fetch and hands off to browser/web-search."
 }
}
''')
