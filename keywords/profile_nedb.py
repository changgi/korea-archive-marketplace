#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_nedb — 국사편찬위원회 한국사데이터베이스 (NEDB (National Institute of Korean History — Korean History Database, db.history.go.kr)) 자료·이용·활용구조 프로파일."""
import json
PROFILE = json.loads(r'''
{
 "name_ko": "국사편찬위원회 한국사데이터베이스",
 "name_en": "NEDB (National Institute of Korean History — Korean History Database, db.history.go.kr)",
 "category": "domestic",
 "data": {
  "hierarchy": "3-level in practice: DB(계열/종) → 자료(권·책·문서·기사 단위) → 항목(기사·건·이미지). Navigated via /item/{db}/main.do (DB 진입) → 목록(searchResultList.do) → 상세 level.do?levelId={ID}. 아카이브식 fonds/series/item 계층이 아니라 편찬물(연대기·문서집·자료집) 단위의 편집 계층이다.",
  "classification": "기록학적 분류체계(RG·ISAD)가 아니라 국편 자체의 '시대별·유형별 DB 분류'. 실제 계열명: (연대기) 조선왕조실록·승정원일기·비변사등록·일성록; (고문서) 각사등록·조선시대 법령자료; (근현대) 한국독립운동사·주한미군사(HUSAFIK)·대한민국임시정부자료; (일제측) 주한일본공사관기록·통감부문서·조선총독부관보·일제감시대상인물카드. 각 DB가 곧 최상위 분류 단위.",
  "identifiers": "통합 식별자 없음 — DB별 개별 ID 체계. 상세는 level.do?levelId={코드}로 접근하며 각 DB가 자체 자료ID(예: 실록 기사ID, 공사관기록 문서번호, 인물카드 관리번호)를 부여. /item/{db}/ 경로의 db 코드가 사실상 DB 식별자. NAID·reference code 같은 국제 표준식별자는 부재.",
  "metadata_standard": "ISAD(G)/DACS/MARC 같은 통일 기술표준 미적용. DB별 편찬 편집표준(표점·교감·국역·해제(解題)) 중심. 자료마다 국역문/원문/이미지 제공 여부가 달라 '국역/원문' 축이 사실상 핵심 메타 구분이며, 같은 검색어라도 국역DB냐 원문DB냐에 따라 결과가 달라진다.",
  "scope": "조선 초기~근현대(1860–1960 전 구간 강함: 개항기 통감부문서·주한일본공사관기록, 일제강점기 관보·인물카드·독립운동사, 해방기 주한미군사 HUSAFIK). 규모 약 117종 DB·1,100만+ 건. 조선왕조실록은 별도 sillok.history.go.kr로 분리 운영.",
  "digitization": "고도 디지털화. 국역+표점 원문 텍스트(연대기 계열)와 원문 이미지 스캔(공사관기록·인물카드·미군사) 병존. 텍스트 전문검색 가능하나 이미지-only 자료는 OCR 미완으로 색인 텍스트(해제·목록)만 검색 대상."
 },
 "access": {
  "channel": "Endpoint: https://db.history.go.kr/search/searchTotalResult.do?searchKeyword= (서버가 /item/{db}/main.do 앵커를 HTML 스크랩). 브라우즈: https://db.history.go.kr/search/searchResultList.do?searchKeywordType=BI&searchKeyword={질의}. MCP 도구 nedb_search가 이 통합검색을 서버측에서 직접 조회.",
  "auth": "none — 인증키·로그인 불필요.",
  "query_syntax": "searchKeyword=질의, searchKeywordType=BI(본문+제목). 인명·기관명은 한자 원표기가 색인 정확도 최상이며 한글·한자 병행 투입 권장(위안부/慰安婦, 경성/京城). DB별 정밀검색·연대 필터는 각 DB 진입 후 자체 검색 UI에서 수행.",
  "response_format": "통합검색은 HTML. 서버 스크랩 결과는 '검색어가 등장하는 DB 종 목록'(매칭 DB명)만 반환 — 건별 리스트나 DB별 카운트가 아니다. 페이징은 searchResultList.do 브라우즈 화면에서 처리.",
  "blocking_notes": "robots.txt는 Yeti·Daum·Googlebot·bingbot만 Allow, User-agent:* 는 Disallow:/ (검색경로 포함) — 일반 UA 서버 스크래핑은 robots 미준수. 준수하려면 브라우저 도구 열람 또는 화이트리스트 UA 협의 필요. 지오블록은 없음(한국 외 IP도 접속되나 robots상 크롤 비허용).",
  "rights_access": "공공 열람 무료. 국역문·해제는 국편 저작물, 원문 이미지는 비상업·출처표시 조건이 일반적이며 상업 이용은 별도 협의. 실록 등 국역 텍스트 재이용 시 출처(국사편찬위원회 한국사데이터베이스) 표기. 공공누리(KOGL) 유형 표시가 없는 자료는 개별 문의 대상."
 },
 "use": {
  "mismatch_summary": "①언어적: 동일 대상이 국역DB에선 한글(위안부·경성), 원문DB에선 한자(慰安婦·京城)·이두·일본식 표기로 색인 → 표기 병렬 투입 없이는 원문 누락. ②분류학적: 하나의 주제가 성격상 여러 DB에 분산(예: 개항기 사건이 주한일본공사관기록·통감부문서·독립운동사에 각기 존재) → 통합검색이 '어느 DB에 있나'만 알려주므로 DB 계열 선택이 곧 분류축. ③기술관행적: 당대 편찬어휘·행정용어(피구금자·요시찰인·비도)로 색인되어 현대어 질의로는 미검출, 일제감시대상인물카드·미군사(HUSAFIK)는 원생산 언어(일본어·영어) 잔재.",
  "keyword_ref": "domestic: 신설 keywords_nedb 세트(언어층 57종(한자 원표기 22종 포함) 검증). 인명·기관·사건의 한글/한자/일본식·영문 이표기를 병렬로 보유. 해외 G-/N-/T-/RG 그룹은 교차검증 단계에서만 참조.",
  "crossmap_ref": "keywords/keywords_nara.py 의 RG_MAP(63) — NEDB 근현대 계열(주한일본공사관기록·조선총독부관보·독립운동사·HUSAFIK)을 NARA Record Group(특히 노획문서 RG 242, 점령기 RG 331/RG 554)과 매핑해 국내 편찬본↔미측 원본을 연결.",
  "adjacent_mining": "부분 적용. NEDB 자체는 인접 확장 finding-aid가 없어(자료ID 규칙성·계열 내 인접 levelId 순회로만 국지적 인접 열람 가능) tna_adjacent_mine식 계층 역추적은 제한적. 대신 '동일 사건 다DB 분산'을 인접축으로 삼아 매칭 DB 전수를 인접 후보로 확장.",
  "cross_archive_combos": [
   "국가기록원 노획문서 ↔ NARA RG 242 ↔ NEDB 주한미군사(HUSAFIK) — 해방기 미군정 문서 3원 대조",
   "NEDB 주한일본공사관기록·통감부문서 ↔ JACAR(일본 아시아역사자료센터) 외무성 기록 ↔ NARA RG 242 노획 일본문서 — 개항기·병합기 일본측 원본 교차",
   "NEDB 일제감시대상인물카드·독립운동사 ↔ 국가기록원 조선총독부 재판/형사 기록 ↔ 국립중앙도서관 대한민국신문아카이브(1883–1960) — 인물 신원·활동 3원 검증",
   "NEDB 조선총독부관보 ↔ 국립중앙도서관 관보 컬렉션 ↔ 국가기록원 총독부 생산문서 — 법령·인사 공시 대조"
  ],
  "rights_rule": "judge_rights 초판 A/B/C/D 적용: 국역·해제 텍스트=국편 저작물(출처표시 재이용)→대체로 B(공개가능추정); 저작권 만료 원문사료(조선~일제기 공문서·1차 사료)→A(공개확정) 근접하나 국편 이미지 재가공권 때문에 상업이용은 C(허가필요)로 하향; 인물카드 등 개인정보 포함 근현대 자료는 지위불명 시 D(공개금지). 어느 경우든 자동 초판이므로 공개 전 인간 최종 확인 필수."
 },
 "verify": {
  "accurate": false,
  "notes": [
   "blocking_notes claims 'robots.txt 사실상 허용' — this is factually wrong. db.history.go.kr/robots.txt is an allowlist: 'Allow: /' is granted ONLY to four named crawlers (Yeti, Daum, Googlebot, bingbot); all other user-agents (User-agent: * → Disallow: /) are blocked from the entire site, including /search/. A generic MCP/HTTP scraper is therefore disallowed, not allowed. The live scrape_plan verdict is 'robots 차단' (blocked → use browser tool), contradicting the profile."
  ],
  "robots": "Blocked for generic agents. Live scrape_plan on https://db.history.go.kr/search/searchTotalResult.do returned 판정: 'robots 차단 → 브라우저 도구로 열람'. Direct fetch of /robots.txt confirms: Allow:/ only for Yeti, Daum, Googlebot, bingbot; User-agent:* Disallow:/ (whole site incl. /search/). So a non-whitelisted scraper is disallowed."
 }
}
''')
