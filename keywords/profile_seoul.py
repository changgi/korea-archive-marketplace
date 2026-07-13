#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_seoul — 서울기록원·서울정보소통광장·지방기록원 (Seoul Metropolitan Archives / Seoul Open Government (opengov) / Regional Archives (Gyeongnam etc.)) 자료·이용·활용구조 프로파일."""
import json
PROFILE = json.loads(r'''
{
 "name_ko": "서울기록원·서울정보소통광장·지방기록원",
 "name_en": "Seoul Metropolitan Archives / Seoul Open Government (opengov) / Regional Archives (Gyeongnam etc.)",
 "category": "domestic",
 "data": {
  "hierarchy": "이원(二元) 지방기록물 체계. (1) 서울기록원(archives.seoul.go.kr): 다계층 카탈로그 — 컬렉션/시리즈 → 건(RC_ITEM) 단위. 시정 행정기록 + 주제 컬렉션(주요 시정사진·일본군위안부·도시계획·구술기록·행정박물) + 시장 결재문서. (2) 서울정보소통광장(opengov): 생산부서별 결재문서(sanction) — 문서(건) 단위, 조직분류×결재일자. (3) 지방기록원(경남 archives.gyeongnam.go.kr 등): 광역 도정(道政) 기록·구술·행정박물, 국내 최초 광역 지방기록원.",
  "classification": "REAL 스킴: 서울기록원 '시정(市政) 기능분류체계'(정부기능분류 BRM 계열: 대기능-중기능-소기능-단위과제) + 공공기록물 '기록물분류기준표'(단위과제·보존기간·공개구분). 컬렉션은 주제 큐레이션 계층. opengov 결재문서는 생산부서(조직분류)+결재일 정렬 — 별도 주제분류 없음. 지방기록원도 각 시도 기록물분류기준표 준용. (RG·KDC 아님)",
  "identifiers": "서울기록원 카탈로그 관리번호/아이템 ID(regclass=RC_ITEM 단위, collects= 컬렉션 코드). 서울정보소통광장 결재문서 문서번호(URL /sanction/{연속ID}). 지자체 기록관리번호. 국가기록원 생산번호와는 별개 체계 — 상호 매핑표 없음.",
  "metadata_standard": "공공기록물 관리에 관한 법률(공공기록물법) 시행령 기반 기록관리 메타데이터(단위과제·보존기간·공개구분·생산기관). 다계층 기술은 ISAD(G) 계열, 컬렉션 항목은 Dublin Core류 서지. 결재문서는 문서제목·생산부서·기안/결재일·공개여부 필드. 권리표시는 공공누리(KOGL) 유형.",
  "scope": "현대 서울 시정기록 편중이 구조적 특징. 서울정보소통광장 결재문서는 2014~ 원문 전문. 1860–1960 구간(한성부→경성부 원본)은 얕음 — 대한제국·일제강점기 원본 상당수는 국가기록원·일본 소재. 시정사진·구술은 광복 이후 위주. 행정구역·동명 변천(漢城府→京城府→서울特別市)이 시대별 검색어를 좌우.",
  "digitization": "컬렉션 사진·구술·주요 문서는 이미지/미디어 디지털화(서울기록원). 서울정보소통광장 결재문서는 원문(PDF/HTML) 전문 공개. 단, archives.seoul 카탈로그 결과 화면은 JavaScript 렌더 → 서버 원본 HTML에는 검색어별 건수·목록이 없음."
 },
 "access": {
  "channel": "서울기록원 archives.seoul.go.kr/catalog?search_api_fulltext=<질의> (HTML, 결과 JS 렌더) + /catalog/result?regclass=RC_ITEM&search_api_fulltext=<질의> [도구 seoul_archives_search]. 서울정보소통광장 opengov.seoul.go.kr/sanction/list?searchKeyword=<질의> (HTML 결재문서, 서버 페치 가능·질의별 판별) [도구 local_gov_search source=seoul_opengov]. 지방기록원(경남 archives.gyeongnam.go.kr 등) [local_gov_search source=gyeongnam].",
  "auth": "none — 인증키 불요(키리스). 회원가입/로그인 없이 검색·열람.",
  "query_syntax": "전문(full-text) 단일 파라미터. 서울기록원 search_api_fulltext=, 필드필터 regclass=RC_ITEM·collects=<컬렉션>. opengov searchKeyword=. 불리언/정확구 연산자 사실상 미지원 — 한글 색인 중심이라 표기 변형은 질의어 나열로 병렬 투입. 행정구역명은 시대별(漢城府/京城府/서울) 각각 시도.",
  "response_format": "HTML(전용 JSON/RSS API 없음). archives.seoul 결과는 JS 렌더 → 서버 HTML에 검색어별 count 없고, 회신되는 '매칭 컬렉션'은 질의별이 아닌 featured(주요) 컬렉션임에 유의. opengov은 서버 페치가 되고 질의별 결재문서 링크(/sanction/{id})를 실제로 반환. 페이징은 화면 파라미터.",
  "blocking_notes": "지오블록: *.seoul.go.kr 은 Vercel의 비(非)한국 egress를 차단 → 라이브 서버에서 'fetch failed'. 해결: 함수를 서울 리전(icn1)에 핀. robots.txt 라이브 확인(2026-07-13): archives.seoul.go.kr 은 'Disallow: /catalog/ · /search/ · /authority/'(검색 엔드포인트가 robots 상 비허용), opengov.seoul.go.kr 은 'User-agent:* Disallow: /'(전면 차단, /search 명시)이며 ClaudeBot/1.0도 Disallow:/ 그룹에 포함 — 자동수집은 robots 존중해 저빈도·에이전트 열람 원칙으로 제한. archives.seoul 결과 JS 렌더 → cheliped 브라우저 스크래핑 폴백. 과도 요청 회피.",
  "rights_access": "공공누리(KOGL) 유형 표시 확인 후 이용. 서울정보소통광장 결재문서는 공개 결정분 원문 전문 열람·다운로드 가능(미공개분은 open.go.kr 정보공개청구). 시정사진·구술·컬렉션은 항목별 권리(초상권·기증조건) 개별 확인. 일본군위안부 등 민감 컬렉션은 피해자 존엄 고려한 윤리적 사용 기준 적용."
 },
 "use": {
  "mismatch_summary": "①언어적: 동일 장소가 시대별 표기로 분산(漢城府→京城府→서울特別市, Keijo/京城/경성). 단일 현대 지명으로는 일제기 기록 누락 → 3표기 병렬 투입 필수. ②분류학적: 결재문서가 '생산부서'(조직분류) 뒤에 숨음 — 주제 검색으로 안 잡히고 담당부서를 알아야 도달(예 도시계획=도시계획국). 서울기록원은 시정 기능분류/컬렉션 큐레이션 속에 매장. ③기술관행적: 당대 행정 용어·사업명으로 색인(예 '위안부' 대신 사업·부서 명칭, '판자촌 정비' 등) — 현대 학술어와 불일치. 여기에 현대 시정기록 편중이 겹쳐 1860–1960 구간은 0건이 곧 미소장/미전산일 뿐 부재가 아님.",
  "keyword_ref": "국내 신설 keywords_seoul 세트(서울정보소통광장 51종 검증 완료) — 행정구역 변천어(漢城府/京城府/京城/서울特別市)·시정 사업명·부서명·컬렉션 주제어(시정사진·도시계획·위안부·구술). 해외 교차 시 기존 G-/N-/T-/RG 그룹(NARA RG·TNA 부처코드)과 병용.",
  "crossmap_ref": "query_cheatsheet.md의 RG 교차 매핑 표(RG_MAP류): 서울 시정 주제 → 해외 RG로 브리지 — 도시/행정(RG 84 Seoul, RG 554 미군정 USAMGIK)·인물/외교(RG 59 Corea, RG 84)·군사(RG 111/342). 서울기록원↔국가기록원 사이 공식 식별자 매핑표는 없어 주제어·연도·기관명으로 소프트 매칭.",
  "adjacent_mining": "부분 적용. 참조코드 ±N 순회(NARA/TNA식)는 불가(연속 식별자 아님). 대신 (1) opengov 결재문서의 '생산부서' 축으로 인접 확장(같은 부서·인접 결재일 문서 훑기), (2) 서울기록원 컬렉션 단위 전수 스캔(collects= 고정 후 목록 순회)이 등가 기법.",
  "cross_archive_combos": [
   "서울정보소통광장 결재문서(도시계획·정비사업) ↔ 국가기록원 archives.go.kr(중앙 승인문서) ↔ 서울기록원 도시계획 컬렉션 — 시정 의사결정 3중 대조",
   "서울기록원 일본군위안부 컬렉션 ↔ 한국사DB(db.history.go.kr, 慰安婦·위안부 한자병행) ↔ NARA RG 389/RG 331(SCAP)·NARA 노획문서 RG 242 — 국내외 상호검증",
   "국가기록원 노획문서 ↔ NARA RG 242 (Captured Korean/Enemy Documents) ↔ 한국사DB HUSAFIK(주한미군사) — 광복~한국전쟁 구간 표준 3자 검증",
   "서울기록원 주요 시정사진 ↔ NARA RG 111/342 (Keijo/Seoul) ↔ 국립중앙도서관 신문아카이브(1883–1960 고신문) — 경성/서울 도시경관 시계열 대조"
  ],
  "rights_rule": "1차 판정: opengov 공개 결재문서 원문 = 공개확정 계열(공공누리 유형 표시 확인 후 A/B). 서울기록원 시정사진·구술·컬렉션 = 공공누리 유형 미표시 시 허가필요(C)로 보수 처리, 초상권·기증조건 존재 가정. 미공개/비공개 문서 = 지위불명(D), 정보공개청구 경로로만 접근. 민감 컬렉션(위안부 등)은 등급과 별개로 윤리 사용 기준 적용, 공개 전 인간 최종 확인 필수."
 },
 "verify": {
  "accurate": true,
  "notes": [
   "Endpoints all verified against mcp/server.py: seoul_archives_search uses archives.seoul.go.kr/catalog?search_api_fulltext= and /catalog/result?regclass=RC_ITEM&search_api_fulltext= (matches profile); local_gov_search source=seoul_opengov uses opengov.seoul.go.kr/sanction/list?searchKeyword= and returns /sanction/{id} links (matches profile); source=gyeongnam -> archives.gyeongnam.go.kr (matches). Auth=none/keyless correct.",
   "Classification scheme names are real and correctly stated: 정부기능분류(BRM) 대기능-중기능-소기능-단위과제, 공공기록물법 시행령 기록물분류기준표(단위과제/보존기간/공개구분), ISAD(G), Dublin Core, 공공누리(KOGL). Correctly notes it is NOT RG/KDC. NARA RG crossmap codes (RG 59, 84, 111/342, 242, 331, 389, 554) are genuine NARA record groups. No invented schemes found.",
   "Caveat on blocking_notes: the profile presents the archives.seoul robots.txt (Disallow /catalog//search//authority/) and opengov (Disallow: / incl. ClaudeBot) as a live 2026-07-13 confirmation, but those specific directives are NOT verifiable from this environment — scrape_plan against archives.seoul returned 'robots 미확인(fetch failed)', consistent with the profile's own geoblock note (*.seoul.go.kr blocks non-Korea egress). The directives are plausible but were not live-confirmed here."
  ],
  "robots": "archives.seoul.go.kr/catalog: scrape_plan returned '판정: robots 미확인(fetch failed)' — robots.txt could not be fetched from this (non-Korea) egress due to the *.seoul.go.kr geoblock. Tool recommends opening the URL via an agent browser tool and tabulating results (JS-rendered catalog). The profile's specific stated Disallow directives could not be independently live-verified here."
 }
}
''')
