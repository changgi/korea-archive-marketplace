---
name: korea-archive-discovery
description: 해외 아카이브(NARA·TNA·archive.org·Gallica·Europeana)와 국내 아카이브(국사편찬위 한국사DB·국가기록원·국립중앙도서관·정보공개포털·서울기록원)에서 한국 관련 기록·영상(1860~1960)을 발굴할 때 사용. "한국 관련 자료 찾아줘", "NARA에서 한국 영상 검색", "TNA 한국 문서", "노획 필름", "갈리카/Gallica에서 병인양요·선교사 기록", "유러피아나/Europeana에서 한국 자료", "해방/한국전쟁 영상 발굴", "아카이브 검색 전략" 등의 요청에서 트리거. 검증된 쿼리 전략(표기 변형·RG 교차·TNA 코드·인접 확장·프랑스어 Corée)과 권리 판정 원칙을 제공하고, 조사 결과를 스타일된 HTML 발굴 보고서(발굴 목록 표·재현 쿼리·권리 판정 포함)로 생성한다.
---

# 해외 아카이브 한국 기록 발굴 스킬 (5개 소스: NARA·TNA·archive.org·Gallica·Europeana)

## 핵심 원리 — 구조적 부정합 3차원 (송창기 2026, F1=0.931 실증)
한국 기록은 ①언어적(표기 변형) ②분류학적(RG·부처코드 속에 숨음) ③기술관행적(당대 어휘로 색인)
부정합 때문에 단일 키워드로는 못 찾는다. 아래 순서로 검색하라.

## 검색 실행 규칙

### 1. 표기 변형을 반드시 병렬 투입 (references/query_cheatsheet.md 참조)
- 한국: Korea OR **Corea OR Chosen OR Tyosen** (전전 자료는 후자로만 색인됨)
- 서울=**Keijo**(일제기), 인천=**Jinsen/Chemulpo**, 부산=**Fusan/Pusan**, 평양=**Heijo**,
  원산=**Genzan**, 제주=**Cheju/Quelpart**, 장진호=**Chosin**
- "Chosen"은 영어 일반어와 충돌 — 반드시 newsreel/Japan/film과 AND 조합.

### 2. 넓게 → 좁게 (재현율 먼저, 정밀도 나중)
- 1단계: RG/컬렉션 전수 스캔 (`identifier:111-adc*`, RG 242 전체 등)
- 2단계: RG 교차 정밀 쿼리 (RG 242 + Chosen, RG 389 + "Korean POW")
- 3단계: 사건·인물 정밀 타격 (Inchon landing, "Kim Koo", Heartbreak Ridge)

### 3. TNA는 부처코드 × 어휘 조합으로만 열린다
- FO 371 + FK코드(FK1015 정치·FK1661 선전) / 1906-19년은 中Code10·日Code23
- WO 281(전쟁일지)·CAB 128/129·PREM 8/11·DEFE 4/5
- **인접 확장**: 검증된 참조코드(예 FO 371/84053) 주변 ±15 piece를 순회하면 미발굴 파일이 나온다.

### 4. 0건 ≠ 부재
NARA 카드 카탈로그 750만 장 대부분 미전산화. 온라인 0건은 "미전산화 후보"로 기록하고 종료하지 말 것.

### 5. 권리 판정 (공개 전 필수)
- 미 연방정부 직무물(RG 111/208/306 등) → PD 추정(B) · Universal Newsreel → 권리 양도(B)
- **RG 242 노획필름 → 지위 불명(D), 공개 금지** · March of Time 편집본 → 기증자 허가(C)

## 국내 아카이브 교차검증 (한국사DB · 국가기록원) + cheliped 스크래핑
해외에서 발굴한 기록은 국내 1차 사료와 교차검증한다. references/domestic_sources.md 참조.
- **한국사DB**(db.history.go.kr, 도구 nedb_search): 1,100만+ 건. 검색이 JS 렌더 → cheliped 브라우저 스크래핑.
- **국가기록원**(archives.go.kr, 도구 archives_search): OpenAPI(RSS) — data.go.kr 무료키(ARCHIVES_API_KEY). 키 없으면 cheliped 폴백.
- **국립중앙도서관**(nl.go.kr, 도구 nlk_search): 6개 컬렉션(주제별·신문아카이브·관보·전시·코리안메모리·해외한국관련자료) collection 파라미터로 라우팅. 통합 OpenAPI(NLK_API_KEY) 또는 cheliped. 신문아카이브 고신문(1883-1960)은 저작권 만료·자유이용.
- **정보공개포털**(open.go.kr, 도구 foia_search): 원문정보공개·정보공개청구 — cheliped 2단계. 미공개 문서는 정보공개청구로 요청.
- **서울기록원**(archives.seoul.go.kr, 도구 seoul_archives_search): 서울시 지방기록물 — 전문검색 URL + cheliped. 지역사 필수 교차 소스.
- **지방 정보공개·기록원**(도구 local_gov_search): source='seoul_opengov'(서울정보소통광장 결재문서)·'sen'(서울시교육청)·'gyeongnam'(경상남도기록원). 결재문서 원문·지방기록물 — cheliped. 지역사 발굴 핵심.
- **전쟁기념관 아카이브**(archives.warmemo.or.kr, 도구 warmemo_search): 한국전쟁·군사사 기록·사진·구술 — cheliped 2단계. 해외 한국전쟁 기록과 교차검증.
- **robots 차단·JS 렌더 사이트**: 도구 scrape_plan(url)이 robots를 판정하고 cheliped-skills 실행 명령을 생성.
  국내 수집기(nedb_search·archives_search·nlk_search·seoul_archives_search·warmemo_search·local_gov_search)는 이제 서버가 각 사이트를 직접 조회해 실제 결과(항목·건수·매칭 DB/컬렉션)를 반환한다. 서버 페치가 안 되는 사이트(정보공개포털·서울교육청·경남기록원)는 scrape_plan/agent 안내에 따라 에이전트의 브라우저 도구로 열어 읽는다. 키가 필요한데 없는 기관(국가기록원 ARCHIVES_API_KEY·국립중앙도서관 NLK_API_KEY)은 도구가 '웹검색으로 결과를 가져와 정리하라'는 지시를 반환하므로, 에이전트는 WebSearch로 결과를 수집해 표로 제시한다(v1.10).
  스크래핑 시 이용약관·저작권을 준수하고 과도한 요청을 피할 것.

## MCP 도구가 있으면 (korea-archive 서버)
tna_search → tna_adjacent_mine → nara_search(RG 교차) → ia_search → gallica_search(프랑스어) → europeana_search → nedb_search(한국사DB)·archives_search(국가기록원)·nlk_search(국립중앙도서관)·foia_search(정보공개포털)·seoul_archives_search(서울기록원)·local_gov_search(지방 정보공개·기록원)·warmemo_search(전쟁기념관) 국내 교차검증 → scrape_plan(cheliped 폴백) → judge_rights → report_template(HTML) 순.
없으면 위 규칙대로 웹 검색·카탈로그 직접 조회로 수행.

## 산출 형식
발굴 결과는 반드시: 식별자(NAID/참조코드) · 원제 · 연대 · 소장처 · URL · 권리등급 초판 · 검색쿼리(재현용)를 표로 보고.

## HTML 발굴 보고서 생성 (마무리 단계 — 기본 산출물)
조사가 끝나면 표 요약에서 멈추지 말고 **HTML 보고서 파일**을 생성한다(사용자가 다른 형식을 지정하지 않는 한).
골격은 이 스킬 폴더의 `report_template.html`을 그대로 사용하거나, MCP 도구 `report_template`을 호출해 얻는다.

작성 규칙 11가지:
1. 파일명: `[주제영문]_records_[연도범위].html` (예: comfort_women_pow_records_1944.html)
2. header: "[주제] — 자료 발굴 보고" + meta(작성일 · 대상 시기 · 대상 아카이브)
3. highlight 박스: 가장 중요한 발굴 1건 요약 (식별자·경위·구성·연구사적 의의)
4. 표① 문서 사료 / 표② 사진·영상 사료(없으면 생략): 식별자·원제 / 연대 / 소장처·청구정보(RG·Entry·Box) /
   관련 내용 / 바로가기(원문→해제→카탈로그 검색 순, 모두 target="_blank") / 권리초판 배지
   (b-A 공개확정 · b-B 공개가능추정 · b-C 허가필요 · b-D 지위불명·공개금지)
5. 재현용 검색 쿼리 표: 목적 / `쿼리` / URL 인코딩된 실행 링크 — 실제 실행해 본 쿼리만 기재
6. '⚠ 0건 ≠ 부재' note: 해당 RG·시리즈의 미전산화 수준 + 인접 상자(Box ±2)·피스(참조코드 ±15) 추가 조사 권고
7. 종합 색인·최신 연구 목록(ul.src): 관련 데이터베이스·색인·최신 논문
8. 권리 판정 절: 법적 근거(17 U.S.C. §105 · 36 CFR 1254.62 · Crown copyright/OGL · domaine public)와 함께
   등급 설명 + '출판 전 인간 최종 확인 필수' + D등급 공개 금지 명시
9. footer: 방법론 한 줄 + '모든 링크는 [날짜] 기준 접속 확인됨'
10. 링크는 도구 호출·열람으로 실재 확인한 URL만 — 추정 URL 절대 금지
11. 민감 주제(위안부·포로·학살·희생자 등)는 피해자 존엄을 고려한 윤리적 사용 기준 문구를 권리 절에 포함
