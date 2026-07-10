# 국내 아카이브 소스 (한국사DB · 국가기록원)

해외 소스로 발굴한 기록을 국내 1차 사료와 교차검증할 때 사용한다.

## 1. 국사편찬위원회 한국사데이터베이스 — db.history.go.kr  (도구: nedb_search)
- 규모: 117종·1,100만+ 건 (조선왕조실록·승정원일기·일제강점기·독립운동·근현대 신문).
- 성격: 검색 결과가 **JavaScript로 렌더** → 일반 HTTP 요청은 빈 목록. robots.txt는 사실상 허용.
- 수집법: **cheliped-skills 브라우저 스크래핑**(아래 참조)으로 목록→상세(level.do) 순회.
- 검색 URL: `https://db.history.go.kr/search/searchResultList.do?searchKeyword=<질의>&searchKeywordType=BI`
- 표기 팁: 인명·기관명은 **한자 원표기**가 색인 정확도 높음. 한글·한자 병행(慰安婦·위안부).

## 2. 국가기록원 국가기록포털 — archives.go.kr  (도구: archives_search)
- 정식 OpenAPI: `https://search.archives.go.kr/openapi/search.arc` (RSS/XML, 일 1,000건).
- 인증키: data.go.kr **'나라기록물정보 서비스'(데이터 15000153)** 무료 신청 → 환경변수 `ARCHIVES_API_KEY`.
- 키 없으면 nedb와 동일하게 브라우저 열기 URL + cheliped 폴백 반환.
- 권리: 공공누리(KOGL) 유형 확인 후 이용. 노획문서·생산기관 코드는 상세 페이지에서 확인.

## 권리 판정 참고 (국내)
- 정부 생산 공문서: 공공누리 제1~4유형 표시 확인. 표시 없으면 개별 문의.
- 국사편찬위 원문 이미지: 비상업·출처표시 조건이 일반적. 상업 이용은 별도 협의.


## 3. 국립중앙도서관 디지털 컬렉션 — nl.go.kr  (도구: nlk_search)
통합 OpenAPI: `https://www.nl.go.kr/NL/search/openApi/search.do?key=<키>&apiType=xml&srchTarget=total&kwd=<질의>`
(www.nl.go.kr Open API 신청 → 환경변수 `NLK_API_KEY`). collection 파라미터로 라우팅:
- **total** 전체 소장자료 · **subject** 주제별컬렉션(N20103) · **gwanbo** 관보(N20301) · **overseas** 해외 한국관련자료(N20401)
  → 키 있으면 OpenAPI 자동 검색, 없으면 브라우저+cheliped.
- **newspaper** 대한민국신문아카이브(nl.go.kr/newspaper) — 1883–1960 고신문 108종·기사 868만. **저작권 만료, 출처표기 시 자유이용**. JS 사이트 → cheliped.
- **exhibit** 전시컬렉션(온라인전시, N20104) · **koreanmemory** 코리안메모리 — 서사형 큐레이션 → 브라우징+cheliped.
- 권리: 신문아카이브 고신문=PD. 그 외 디지털화 자료는 개별 권리·공공누리 유형 확인.


## 4. 정보공개포털 — open.go.kr  (도구: foia_search)
정부기관 **원문정보공개**(공개된 결재문서 원문 전문검색)·사전정보공표·정보공개청구 사례.
로그인·JS 포털 → keyless API 없음. cheliped 2단계(검색창 fill→목록 scrape).
미공개 문서는 포털에서 **정보공개청구**로 직접 요청 가능(발굴의 마지막 카드).
기관별 원문목록은 data.go.kr '원문정보공개' API로도 제공.

## 5. 서울기록원 — archives.seoul.go.kr  (도구: seoul_archives_search)
서울시 행정기록·시정사진·구술·시장 결재문서 등 **지방기록물**. 카탈로그가 JS 렌더 →
전문검색 URL `?search_api_fulltext=<질의>` + cheliped 스크래핑. 저작권은 공공누리(KOGL) 유형 확인.
※ 지방기록물(서울·부산·경남 등)은 국가기록원과 별개 체계 — 지역사 발굴 시 필수 교차 소스.


## 6. 지방 정보공개·기록원 (도구: local_gov_search — source 라우팅)
지역사·특정 지자체 사건 발굴 시 결재문서 원문과 지방기록물이 결정적. 모두 JS 포털 → cheliped.
- **seoul_opengov** 서울정보소통광장(opengov.seoul.go.kr/sanction) — 서울시 결재문서 원문공개(2014~). 직접검색 `?srch_all=`.
- **sen** 서울시교육청 정보공개(open.sen.go.kr, '열린 서울교육') — 원문정보공개 결재문서·사전정보공표. 미공개분은 정보공개청구.
- **gyeongnam** 경상남도기록원(archives.gyeongnam.go.kr) — 국내 최초 광역 지방기록원. 경남도정 기록·구술·행정박물.
- 확장: 다른 지자체 정보공개도 동일 패턴(scrape_plan(url) 또는 cheliped 2단계)으로 수집 가능.


## 7. 전쟁기념관 아카이브 — archives.warmemo.or.kr  (도구: warmemo_search)
한국전쟁·근현대 군사사 기록·사진·유물·구술·문서. 6·25 참전·전투·부대 국내 소장 사료.
keyless API 없는 JS 포털 → cheliped 2단계(검색창 fill→목록). 해외(NARA RG 111/342·TNA WO)와
교차검증 시 강력. 저작권은 전쟁기념관 이용약관·공공누리 유형 확인.
