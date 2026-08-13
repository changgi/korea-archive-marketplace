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
- **지방 정보공개·기록원**(도구 foia_search에 통합): source='seoul_opengov'(서울정보소통광장 결재문서)·'sen'(서울시교육청)·'gyeongnam'(경상남도기록원)·'open_go'(정보공개포털, 기본). 결재문서 원문·지방기록물 — cheliped. 지역사 발굴 핵심.
- **전쟁기념관 아카이브**(archives.warmemo.or.kr, 도구 warmemo_search): 한국전쟁·군사사 기록·사진·구술 — cheliped 2단계. 해외 한국전쟁 기록과 교차검증.
- **6·25전쟁 아카이브센터**(koreanwar.or.kr:8443, 전쟁기념관재단 — **협약기관**, 도구 koreanwar_search[scope=archive|battle]·koreanwar_item[radius=인접채굴]): 55,000+ 건. NARA RG 111/342 미군 시청각 원본의 **한글 재기술본**이라 한글 키워드로 해외 원본 발굴 가능 — 상위계층 breadcrumb에서 RG를 추출해 nara_search 역추적, 상세페이지 입수처 링크는 catalog.archives.gov NAID 직결. 생산연도·수집구분(수집/기증 등) 서버측 필터, archRfcd 일련번호 ±N 인접 채굴, 전투정보 DB(개전 초기 69전투). OpenAPI(KOREANWAR_API_TOKEN 승인 시)로 KOGL 권리 메타 병행. 자료유형·연대·이용조건 코드표는 source_profile('koreanwar') 참조.
- **robots 차단·JS 렌더 사이트**: 도구 scrape_plan(url)이 robots를 판정하고 cheliped-skills 실행 명령을 생성.
  국내 수집기(nedb_search·archives_search·nlk_search·seoul_archives_search·warmemo_search·foia_search·koreanwar_search)는 이제 서버가 각 사이트를 직접 조회해 실제 결과(항목·건수·매칭 DB/컬렉션)를 반환한다. 서버 페치가 안 되는 사이트(정보공개포털·서울교육청·경남기록원)는 scrape_plan/agent 안내에 따라 에이전트의 브라우저 도구로 열어 읽는다. 키가 필요한데 없는 기관(국가기록원 ARCHIVES_API_KEY·국립중앙도서관 NLK_API_KEY)은 도구가 '웹검색으로 결과를 가져와 정리하라'는 지시를 반환하므로, 에이전트는 WebSearch로 결과를 수집해 표로 제시한다(v1.10).
  스크래핑 시 이용약관·저작권을 준수하고 과도한 요청을 피할 것.

## MCP 도구가 있으면 (korea-archive 서버)
tna_search → tna_adjacent_mine → nara_search(RG 교차) → ia_search → gallica_search(프랑스어) → europeana_search → nedb_search(한국사DB)·archives_search(국가기록원)·nlk_search(국립중앙도서관)·foia_search(정보공개포털+지방 정보공개·기록원)·seoul_archives_search(서울기록원)·warmemo_search(전쟁기념관)·koreanwar_search→koreanwar_item(6·25전쟁 아카이브센터 — 한글로 NARA 원본 발굴·NAID 직결·radius 인접 채굴) 국내 교차검증 → scrape_plan(cheliped 폴백) → judge_rights → report_template(HTML) 순.
없으면 위 규칙대로 웹 검색·카탈로그 직접 조회로 수행.

## 산출 형식
발굴 결과는 반드시: 식별자(NAID/참조코드) · 원제 · 연대 · 소장처 · URL · 권리등급 초판 · 검색쿼리(재현용)를 표로 보고.

## HTML 발굴 보고서 생성 (마무리 단계 — 기본 산출물)
조사가 끝나면 표 요약에서 멈추지 말고 **HTML 보고서 파일**을 생성한다(사용자가 다른 형식을 지정하지 않는 한).
골격은 이 스킬 폴더의 `report_template.html`을 그대로 사용하거나, MCP 도구 `report_template`을 호출해 얻는다.

보고서는 **잡지·저널급 편집 지면**으로 만든다 — 텍스트 표만 가득한 문서 금지. 작성 규칙 17가지:
1. 파일명: `[주제영문]_records_[연도범위].html` (예: comfort_women_pow_records_1944.html)
2. 지면 구조(잡지형): masthead → kicker → 표제(h1) → standfirst → byline(기관 chip) → 목차 →
   히어로 figure → Ⅰ서사 → Ⅱ핵심 기록 카드 → Ⅲ영상 필름스트립 → Ⅳ전수 목록 표 → Ⅴ재현 쿼리 → Ⅵ권리·게재 윤리 → 출처 총람 → footer
3. 서사 우선: 발굴 경위·의미를 에세이로 서술(드롭캡 리드 문단, 풀인용 1개 이상). 문단이 실물을 설명하면
   그 문단 옆에 인라인 도판(.fig-inline 플로트) 배치 — 잡지처럼 글과 그림이 같은 화면에. 문체는 담백·구체 —
   과장어(놀라운·혁신적 등)와 AI투 금지
4. 실물 이미지 필수: 게재 가능(권리 A/B + 게재윤리 1·2단계) 기록은 기관 공개 원본에서 수집해 base64로 임베드 —
   히어로 1장 + 핵심 기록마다, 기관 공개 컷은 전량 수록(.sheet 콘택트시트·컷별 라벨). 비식별(블러)판 우선 사용.
   이미지는 max-width:100% 자동 축소 — 본문 삽입 시 논문·잡지 도판처럼 문단 폭에 맞춘다.
   한 장도 못 실으면 그 사유를 권리 절에 명기
5. 모든 이미지에 figcaption + credit 필수: "출처: 기관 정식명(국가) · 식별자 · 촬영자/생산자 · 원본 링크"
6. 영상 기록은 필름스트립: 장면 전환마다 프레임을 충분히 추출(권장 8~16장)해 타임코드+한 줄 설명으로 —
   표제가 가린 장면(ETC 뒤)을 드러내 원본을 직접 보고 싶게. 끝에 "▶ 원본 영상 보기 — [기관] 카탈로그" CTA
7. 핵심 기록 3~6건은 카드(.record)로: 이미지 + 제목(원제 병기) + 출처 계보(국가→기관→RG→상자→식별자) + 요약 + 버튼 + 권리 배지
8. 전수 목록 표(부록형): 식별자·원제 / 연대 / 소장처·청구정보(RG·Entry·Box) / 내용 / 바로가기(원문→해제→카탈로그) /
   권리초판 배지(b-A 공개확정 · b-B 공개가능추정 · b-C 허가필요 · b-D 지위불명·공개금지)
9. 출처 명시(전 지면): byline·본문에 기관 chip(국기+정식명 — 🇺🇸 NARA · 🇬🇧 TNA · 🇫🇷 BnF Gallica · 🇰🇷 KOREAN WAR ARCHIVES 등),
   말미 .sources에 인용 기관 총람(국기·정식명·청구정보·이용조건·링크)
10. 재현용 검색 쿼리(details 접이식): 목적 / `쿼리` / URL 인코딩 실행 링크 — 실제 실행해 본 쿼리만.
    '⚠ 0건 ≠ 부재' note(인접 상자 ±2·피스 ±15 권고) 포함
11. 종합 색인·최신 연구 목록(ul.src)
12. 권리 절: 법적 근거(17 U.S.C. §105 · 36 CFR 1254.62 · Crown/OGL · domaine public · KOGL) + '출판 전 인간 최종 확인 필수' +
    D등급 공개 금지. 민감 주제(위안부·포로·학살·희생자)는 피해자 존엄 문구와 게재윤리 4단계 적용
13. 링크·수치는 도구 호출로 실재 확인한 것만 — 추정 URL 절대 금지, footer에 '모든 링크 [날짜] 접속 확인'
14. 연표·지도·관계도는 인라인 svg 직접 작성 가능. 외부 리소스 금지 — 단일 HTML 파일 자기완결
15. 인쇄 대응: @media print 유지 — 그대로 출판물처럼 인쇄 가능해야 한다
16. 링크 신뢰장치: 주요 링크는 대상 페이지 캡쳐본(헤드리스 브라우저 스크린샷)을 figure+credit(갈무리 일자)로
    임베드해 링크 내용이 실재함을 보인다. 자동화 차단(WAF 등) 시 그 사실을 명기하고 카탈로그 API 기술 원문
    인용표로 대체. 훈격·날짜·건수 등 핵심 사실은 API/원문 대조 후 '검증 기록'으로 수록(정정 이력 포함)
17. 카드뉴스 병행: 보고서와 함께 캐러셀(기본 8장, 1080×1080 — insta-carousel 스킬 또는 MCP 도구
    report_template(kind='carousel'))을 제작하고 보고서 말미 '카드뉴스' 절에 .cards-grid로 임베드 —
    무크롭 전체 노출 + 카드별 figcaption, 잘림·겹침 금지. 커버는 히어로와 같은 실물, 검증 노트·따라하기 카드
    포함, 출처 대장 공유. PNG 원본·caption.txt·sources.txt를 보고서와 함께 납품
