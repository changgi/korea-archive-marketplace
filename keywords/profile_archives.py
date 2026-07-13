#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_archives — 국가기록원 (National Archives of Korea (NAK)) 자료·이용·활용구조 프로파일."""
import json
PROFILE = json.loads(r'''
{
 "name_ko": "국가기록원",
 "name_en": "National Archives of Korea (NAK)",
 "category": "domestic",
 "data": {
  "hierarchy": "다층 편철 계층: 생산기관(fonds급) → 처리과(부서) → 기록물철(철, file/series급) → 기록물건(건, item/piece급). 각 건은 관리번호로 개별 식별. 대량은 정부수립 이후 행정기록이나, 조선총독부기록·노획문서 등 1860–1960 코어 컬렉션이 별도 컬렉션군으로 편성됨.",
  "classification": "이중 분류체계: (1) 기록물분류기준표 — 대분류·중분류·소분류의 3단 업무기능 분류(2004~ 정부기능분류 BRM으로 전환·연동); (2) 정부기능분류체계(BRM, Business Reference Model) — 정책분야·정책영역·대기능·중기능·소기능의 기능분류. 컬렉션 단위로는 조선총독부기록물·행정박물·시청각·개인/단체 기증기록 등 유형별 편성. (실존 스킴만 표기 — 임의 명칭 없음)",
  "identifiers": "관리번호(생산기관코드 + 등록/편철 일련번호)가 핵심 식별자. 철 단위 분류번호 + 건 단위 관리번호 2층 구조. OpenAPI 응답에서는 각 item의 link(상세 열람 URL)가 사실상의 영구 참조 역할. 조선총독부기록은 별도 문서번호(총독부 문서철 번호) 병용.",
  "metadata_standard": "공공기록물 관리에 관한 법률(공공기록물법) 및 시행령의 기록물 등록·기술 규칙에 기반. 국제표준 ISAD(G) 다계층 기술 원칙을 참조한 기록물 기술(생산기관·생산연도·보존기간·공개구분 필수 요소). OpenAPI 노출 필드: title, prod_year(생산연도), prod_name(생산기관), is_open(공개여부), link.",
  "scope": "시대: 후기(구한말)~현대 행정기록 중심. 코어 컬렉션 조선총독부기록(1910–1945), 관보, 정부수립문서(1948~), 독립운동판결문, 노획문서가 1860–1960 발굴 범위에 직접 대응. 규모: 국가 최대 공공기록 보존기관(수백만 건 단위), 다만 1860–1910 개항기 자료는 상대적으로 희소.",
  "digitization": "부분 디지털화. 국가기록포털(archives.go.kr)에서 원문 이미지/PDF 뷰어 제공(관보·판결문·조선총독부기록 상당수 원문 DB화). is_open=0(비공개) 항목은 목록만 노출되고 원문은 정보공개청구 대상. OpenAPI는 메타데이터 + 열람 link 반환(원문 파일 직접 다운로드 API는 아님)."
 },
 "access": {
  "channel": "정식 OpenAPI(RSS/XML): https://apis.data.go.kr/1741050/openapi/searcharc?serviceKey=<ARCHIVES_API_KEY>&query=&start=&limit= (data.go.kr 서비스 15000153 '나라기록물정보 서비스'). MCP 도구 archives_search가 서버측에서 호출. 포털 폴백/원문 열람: https://www.archives.go.kr/next/newsearch/listSubjectDescription.do?query=<검색어> 및 archives.go.kr.",
  "auth": "data.go.kr 발급 무료 서비스키 필요. 환경변수 ARCHIVES_API_KEY(15000153)로 설정. Encoding키는 그대로, Decoding키는 URL 인코딩하여 serviceKey에 전달. 키 미설정 시 archives_search는 포털 열람 URL로 핸드오프.",
  "query_syntax": "파라미터: query(검색어, URL 인코딩), start(시작 오프셋, 1-base), limit(건수, 서버측 max 50 캡). 필드 지정/불리언 연산자는 미노출 — 단일 키워드 전문검색. 공개구분·생산기관 필터는 응답 후 is_open/prod_name 기준 클라이언트측 필터로 처리. 한자 정확구(예: 朝鮮總督府) 그대로 질의 가능.",
  "response_format": "XML/RSS. 최상위 <total>(총건수) + 반복 <item>{title, prod_year, prod_name, is_open(1=공개/0=비공개), link}. 페이징은 start/limit 조합. 오류 시 <searchError>/<message> 또는 <returnReasonCode>.",
  "blocking_notes": "data.go.kr 공통 트래픽 제한(일일 호출 쿼터, 키 등급별) 적용 — 대량 수집은 start 페이징 + 백오프 권장. 서버측 limit 50 캡. 지오블록 없음(국내 서비스이나 해외 접근 가능). robots: OpenAPI는 계약 API라 robots 무관하나 포털 직접 스크레이핑은 archives.go.kr robots·JS 렌더 제약을 받으므로 OpenAPI 우선.",
  "rights_access": "라이선스: 공공누리(KOGL) 유형 확인 후 이용 — 유형별(제1~4유형) 출처표시·상업이용·변형 조건 상이. is_open=1(공개) 항목은 원문 열람/복제 가능, is_open=0(비공개) 항목은 목록만 제공되며 원문은 정보공개청구(정보공개포털 foia) 대상. 조선총독부기록·관보·독립운동판결문 등 1945 이전·연대 경과분은 대체로 자유이용에 근접(권리 초판 판정은 judge_rights로 확정)."
 },
 "use": {
  "mismatch_summary": "3대 부정합이 국가기록원에서 나타나는 양상 — (1) 언어적: 국내 국문/한자 기술 중심이라 해외기관의 로마자 표기(Chosen, Corea, Keijo, Fusan)와 불일치. 코어 컬렉션은 원문이 일본어/한자(朝鮮總督府)이므로 국문 라벨·한자 원어·로마자 3중 질의 필요. (2) 분류학적: 기록물분류기준표/BRM의 '업무기능' 축은 해외기관의 출처주의(RG/fonds) 축과 교차하지 않음 — 노획문서가 국내에서는 컬렉션 유형으로, NARA에서는 RG 242(압수 외국문서)로 재편성됨. (3) 기술관행적: is_open/prod_name/prod_year의 얕은 필드만 노출되어 ISAD(G) 다계층 맥락(상위 철·생산배경)이 API에 안 실림 → 상세 link 파싱으로 보강.",
  "keyword_ref": "국내 신설 keywords_archives 세트 사용. 핵심 검증 시드: 한자 원어(朝鮮總督府 — 77건 검증, 官報, 判決文, 獨立運動, 鹵獲文書/노획문서), 국문(조선총독부, 관보, 정부수립, 독립운동판결문), 로마자 브릿지(Chosen Government-General, Keijo). 해외 교차 시 keywords_common G-08(COLONIAL: Governor-General Korea, Keijo, Chosen), G-09(LIBERATION), G-11(인물)과 결합.",
  "crossmap_ref": "keywords_nara.RG_MAP을 크로스맵 기준으로 사용. 최우선 매핑: 국가기록원 노획문서 ↔ NARA RG 242(National Archives Collection of Foreign Records Seized). 부차: 조선총독부/미군정 행정 ↔ RG 331/RG 554(FECOM)·RG 260(SCAP), 정부수립·외교문서 ↔ RG 59/RG 84. 국가기록원 자체에는 RG 번호가 없으므로 '컬렉션 유형 → RG 번호'로 단방향 브릿지.",
  "adjacent_mining": "가능하나 간접. OpenAPI는 인접 참조번호 순회(tna_adjacent_mine식 reference±radius)를 직접 지원하지 않음. 대신 (a) 동일 prod_name(생산기관)+인접 prod_year로 재질의해 같은 철의 인접 건을 근사 수집, (b) 상세 link 페이지에서 상위 기록물철 번호를 추출해 철 단위 재검색하는 2단 방식으로 인접 채굴 구현. 노획문서→NARA 이관분은 NARA RG 242에서 tna/NARA 인접 채굴로 확장.",
  "cross_archive_combos": [
   "국가기록원 노획문서(鹵獲文書) ↔ NARA RG 242 (nara_search, 압수 북한/조선문서) ↔ 한국사DB HUSAFIK(주한미군사, nedb_search) — 3자 대조로 노획문서 출처·이관 경로 검증",
   "국가기록원 조선총독부기록(朝鮮總督府) ↔ 국사편찬위 한국사DB(조선총독부관보/직원록) ↔ 국립중앙도서관 관보 컬렉션(nlk_search gwanbo) — 식민지 행정문서 상호보완",
   "국가기록원 독립운동판결문(判決文) ↔ 한국사DB 독립운동 판결문/삼일운동 DB ↔ NARA RG 84 영사보고 — 사건 교차 확인",
   "국가기록원 정부수립문서(1948) ↔ NARA RG 59/RG 84(USAMGIK·주한미대사관) ↔ TNA FO 371 Korea(tna_search) — 정부수립기 외교 3자 검증"
  ],
  "rights_rule": "권리 초판(first-pass) 판정 규칙: (1) prod_year ≤ 1945(연대 경과·조선총독부/관보/판결문) → 사실상 자유이용 후보 → judge_rights로 확정; (2) is_open=1 이고 공공누리 유형 표시 → 유형(1~4)별 조건 적용 후 이용; (3) is_open=0(비공개) → 원문 이용 불가, 정보공개청구(foia_search) 경로로 전환. 기본값은 '공공누리 유형 확인 후 이용', 불확정 시 judge_rights(archive='국가기록원')로 최종 판정."
 },
 "verify": {
  "accurate": true,
  "notes": [
   "Minor (utilization_structure crossmap only, not the verified data/access structures): profile writes 'RG 260(SCAP)' — SCAP is more precisely NARA RG 331; RG 260 = US Occupation Headquarters WWII (holds USAMGIK/OMGUS). RG 242, RG 331, RG 554(FECOM), RG 59/RG 84 mappings are all correct."
  ],
  "robots": "robots 허용(Allowed) for https://www.archives.go.kr/next/newsearch/listSubjectDescription.do?query=... via scrape_plan. Verdict notes the portal is JS-rendered, so a browser tool is advised for scraping; the profile's guidance to prefer the OpenAPI (contract API, robots-irrelevant) over portal scraping is consistent with this."
 }
}
''')
