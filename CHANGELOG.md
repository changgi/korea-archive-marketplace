# Changelog

## 2026-11-22 v1.91.1 — 30곳 전수 실측에서 찾은 결함 3건 교정
- 예제 30선 기획을 위해 30개 수집처를 프로덕션에서 하나씩 실측 → 결함 발견·교정
- **NDL(일본 국립국회도서관)**: 일문·한자 입력(京城府·朝鮮総督府)이 한→일 변환 실패 시 영문 'Korea'로 바뀌어 무관 자료(アーカイブズ…)가 상위 — 한글 입력일 때만 영문 폴백, 부분 변환(京城부) 폐기. 또 `any=`가 광역 일치 후 가나순 정렬로 잡음을 올려 `title=` 우선·0건 시 `any=` 폴백 → '京城府' = 京城府庁(京城名所) 엽서·往十里 육지측량 지도
- **DigitalNZ**: 서버(icn1) 익명 호출 HTTP 403 신규 실측(작업망은 200 — IP 기반). `DNZ_API_KEY`(무료) 설정 시 키 헤더 호출, 미설정 시 원인·복구법·웹 대체 경로를 오류에 명시
- **Europeana**: 결과 링크의 `?utm_…` 추적 꼬리 제거
- 실측 현황(30채널 health): 🟢26 · 🟡nedb(개방파일 인덱스 미설정) · 🔴gallica(BnF 403)·dnz(403)·foia(시간 초과) — 3곳은 기술적 불능, 응답에 웹 대체 경로 안내 유지

## 2026-11-22 v1.91.0 — 공용 파일 판독에 NARA 원본 자동 대조(증거성 강화)
- nedb_search(mode=commons) File 판독: 파일명에 NARA 번호(`… - NARA - 520782.tif`)가 있으면 NARA 카탈로그를 직접 조회해 【NARA 원본 대조】 표시 — 원본 실재·제목·계보(RG › 시리즈)·생산일·소장 번호·Use Restriction → A/C 판정·카탈로그 링크
- 번호가 카탈로그에 없으면 "파일명 번호 오기 가능 — 업로더 라이선스만으로 게재 판단 금지" 경고 (6s·24h 캐시, cross_search 원본확인과 캐시 공유)
- 원본 이미지 링크의 `?utm_…` 추적 꼬리 제거 (cross_search와 동일한 영속 URL)
- 의의: 업로더가 적은 라이선스(2차 정보)를 원 소장처 기록(1차 정보)으로 자동 검증 — 지난 라운드 카드뉴스 이미지 26장 중 Commons 경유분을 손으로 대조하던 절차의 자동화

## 2026-11-22 v1.90.3 — 공공누리 영문 표기("KOGL Type 1") 판독 교정
- 결함(v1.90.2 발견): 권리 판독기가 Commons 등 해외 표기 "KOGL Type 1"·"Korea Open Government License Type 2"를 공공누리로 인식하지 못해 D(확인 필요)로 판정
- 교정: 공공누리 정규식에 `Type`·정식 영문명 허용 — lib/rights.js · kla/ledger.py(2부) 동일 반영
- Commons 모드: PD·CC가 아닌 라이선스는 공용 판정 규칙(judgeRights/auto_rights)으로 재판독 — KOGL 1→A, 2~4→B
- 실측: "KOGL 1"·"KOGL Type 1"·"공공누리 제1유형"→A / "KOGL Type 4"·"…License Type 2"→B / 미표기→D (Node·Python 동일)

## 2026-11-22 v1.90.2 — 카드뉴스 20장을 원본 사진으로 가득 채운 v2로 교체("글보다 이미지로 설득")
- 사용자 요청: "원본 이미지가 가득 차게", "글보다는 이미지로 설득" → 캐러셀 10·단독 10 전면 재제작: 풀블리드·2×2·3×3 모자이크·지면 병치, 글은 제목 2줄+핵심 숫자 1개+출처 1줄
- 원본 사진 26장 확보·권리 실조회: NARA 12(전부 Unrestricted A — 이 도구의 cross_search가 Commons 기증본↔NARA 원본을 `nara·원본확인`으로 묶어 찾음) · 호주 전쟁기념관 7(가평 계곡·227고지·뉴질랜드 제16야포연대, Copyright expired) · 국립중앙도서관 신문 지면 3(황성신문 1907.2.8 4면·대한매일신보 1909.11.9 3면·12.11 2면) · Commons 4(안중근·1906 경복궁·1930년대 경성 "KEIJO" 엽서 — PD / 화성성역의궤 — 공공누리 1유형)
- 존엄·정확성: 포로·묘지·수형자 사진 제외(유관순 카드는 판결 도시 경성 거리를 '참고 이미지'로 명기), 의궤 카드는 '의궤의 모습 예시'로 명기
- 제약 기록: Wikimedia 썸네일이 이 환경 대량 요청을 로봇 정책 429로 제한 — 우회하지 않고 NARA 서버 열람용 GIF 사용
- 도구 결함 발견: judge_rights/commons 판독이 영문 "KOGL Type 1"을 공공누리 제1유형으로 인식하지 못하고 D로 판정 → 다음 라운드 교정 대상
- `docs/promo/sources_images.txt`(26장 전체 대장), 수정용 원본 HTML 2종 갱신, 검수: 20장 전 장 육안(하단 출처·칩 겹침 1차 결함 교정)

## 2026-11-22 v1.90.1 — 예제 10개 추가(총 15선) + 단독 게시물 10개·3주 게시 일정
- 실측 신규 예제 10: ⑥ 안중근 3채널 대조(공훈 1962 대한민국장·인명사전 676·판결문) ⑦ 유관순 판결문(1919.6.30 징역 3년·9.11 상고 기각) ⑧ 신문 OCR '단지동맹' 1907~1910 65건 중 1907년 54건 — 안중근(1909) 이전 유학생 21인 단지동맹 ⑨ TNA "Keijo"(1942 공습 목표·1945 Kyongsong(Keijo;Seoul)) ⑩ 호주 전쟁기념관 044757 저작권 만료 사진 ⑪ 뉴질랜드 국립기록원 Open/Restricted ⑫ 장서각 개건도감의궤 해제 ⑬ 근정전 해설(정도전 작명) ⑭ UN S/2015/799 6개 언어 PDF ⑮ 공개 지문 장부 대조(오늘 값=장부 값)
- 실측에서 약해 뺀 후보 명시: IA 'Keijo' 변형(잡음), JACAR 징용(영문 준비 중), KTV 휴전(현대 영상), Gallica(차단)
- `docs/promo/singles/`: 단독 게시물 카드 10장(하단 "직접 해 보기 👉 프로필 링크", 전 장 육안 검수·빈 하단 3장 보강) + `captions.txt`(게시물별 캡션) + 수정용 원본
- `docs/promo/schedule.md`: 3주 연재 일정(대표 캐러셀 → 반전형 → 인물·현장 → 문화유산·신뢰) · `sources.txt`·`intro.md`에 예제 6~15 반영
- `examples.html`: "예제 6~15" 구간 추가, 홍보 자료 내려받기 5종. 각 소개 페이지·README "예제 15선"

## 2026-11-22 v1.90.0 — 예제 5선 공개 + 인스타그램 카드뉴스·홍보글
- GitHub Pages `docs/examples.html`(korea-archive-mcp): 실측 예제 5선 — ① 같은 기록 묶기(장진호, 9건 중 5건 두 기관 확인) ② 사진 권리 확인(NAID 276537577 A등급) ③ 사진 원본 찾기(흥남 NAID 520782) ④ 옆 번호 훑기(인천 D-DAY 22013~22017) ⑤ 신문 면·단(안중근 대한매일신보) — 각 예제에 "이렇게 말하면·실제 응답·왜 중요한가·직접 해 보기(복사)" + **만드는 과정**(찾기→원본 확인→권리 판정→제작·검수) + **활용 방법**(연구자·기록관·교사·기자·기록관리·일반)
- 카드뉴스 10장(`docs/promo/card_01~10.png`, 1080×1080) — 커버·문제·예제 5·만드는 과정·활용법·CTA. 사진은 NARA 이용 제한 없음(A등급) 2장만, C등급 영상은 장면 미사용. 전 장 육안 검수(도장 위치·작은 글씨 2건 수정)
- 홍보글: `caption.txt`(본문·짧은 버전·해시태그 20+20·게시 전 확인 목록) · `intro.md`(블로그·보도용 소개글) · `sources.txt`(이미지·인용 출처 대장) · `carousel_source.html`(수정용 원본)
- 소개 페이지 2종·README 2종에서 예제 페이지 링크

## 2026-11-22 v1.89.2 — 같은 기록 묶기 회귀 검사를 주간 자동 점검에 편입(지속가능성)
- `health.yml`에 2단계 추가: 실서비스에 골든 2종 실행 — 장진호(NARA×협약기관)·NAID 44175(NARA×인터넷 아카이브) — 묶인 기록 1건 이상 기대
- 판정 3분기: 정상=통과 / 두 채널 다 결과가 있는데 묶인 기록 0건=**실패**(원 사이트 상세 구조·NARA 응답 형식 변경 의심) / 채널 장애·키 부재=경고(판정 보류)
- 검증: 단계 스크립트를 그대로 추출해 프로덕션 실행(장진호 5건·44175 1건 통과) + 가짜 응답으로 실패·보류 경로 확인. 헤더 주석 "21채널"→30채널 정정

## 2026-11-22 v1.89.1 — 원본 확인을 증거로 기록 + 공표물·안내문 현행화
- 수집 기록서(manifest) `evidence`: 원본 확인을 거친 기록은 "NARA 카탈로그 원본 실재 확인(NAID) — 사본 …", 기관 간 병합 기록은 "기관 간 동일 기록 대조(…)"를 기록 단위로 남김
- "같은 기록 묶기"를 공표물 전부에 반영 — README 2종(예시 7번·기능 8번·용어 "원본확인"), 소개 페이지 2종(대화 예시 카드·기능 카드·용어), 사용 안내 국/영(설명 단락), 서버 안내문 HELP_GUIDE(예시 문장) — 웹·모바일 동등성
- 오래된 숫자 정정: 사용 안내 첫 화면 "28개 아카이브(1860~1960)"→"9개국 30개(1860~현대)", FAQ "13개 채널"→30개, HELP_GUIDE 동일 정정

## 2026-11-22 v1.89.0 — 원본 확인(origin resolution): 재게시·재수집본의 NARA 원본을 직접 조회해 실재 증명
- 빈틈: 재게시본에 원본 NAID가 붙어도 그 원본이 같은 검색 결과에 없으면 병합되지 않던 문제(협약기관 NAID 24033·22344·23203·23204, Commons 520782 등)
- cross_search 병합 직후 `resolveOrigins`/`_resolve_origins`: 결과에 없는 sameAs NAID를 NARA 카탈로그에서 직접 조회(최대 4건·6s 상한·24h 캐시) → 응답 NAID가 **정확히 일치할 때만** 원본으로 승격 — NARA 원제목·계보(RG›시리즈)·생산일·원본 파일을 채우고 재게시본 제목은 altTitle 보존, 출처 태그 `nara·원본확인`
- 채널 통계에 `nara원본확인:n` 표시 — 원본 실재 확인이 증거로 남음. NARA_API_KEY 미설정 시 건너뜀
- 오프라인 단위 검사: 일치 시 승격·불일치 응답 시 미적용 2경우 통과

## 2026-11-21 v1.88.0 — 동일 기록 연결 3호: 위키미디어 공용(Commons) NARA 기증본
- 실측: Commons 파일명 규칙 2종 — `… - NARA - <NAID>.tif`(`520782` = NARA NAID 520782 흥남 철수 피란민 사진, RG 80 제목 일치) · `NARA <고유번호> …`(127-N-A4501형)
- commons 수집기: 파일명에서 원본 식별자 → `sameAs`(추가 조회 0). 하이픈 위치가 NARA 표기와 다른 `111-SC349027`형은 확정 불가로 제외
- nara 수집기: 고유번호(localIdentifier)를 `lid`로 보존 → 병합기가 NAID와 고유번호 **둘 다로 대조**(실재할 때만 병합)
- 병합기: 원본에 매체가 없으면 재게시본의 원본 파일(media)을 승계
- 오프라인 단위 검사: NARA+Commons+IA 3자 병합·고유번호 병합·매체 승계·근거 없는 연결 미병합 4경우 통과

## 2026-11-21 v1.87.0 — 동일 기록 연결 2호: 인터넷 아카이브 NARA 재게시본
- 실측: IA에 `gov.archives.arc.<숫자>` 식별자 한국 관련 86건 — `gov.archives.arc.44175` = NARA **NAID 44175** "MISCELLANEOUS SCENES KOREAN SOLDIERS"(RG 242 노획 필름) 제목 일치 확인
- ia 수집기: 식별자에서 원본 NAID를 읽어 `sameAs` 부여(**추가 조회 0**) → NARA 결과와 한 건으로 병합
- 병합기: 한 원본에 여러 기관이 연결되면 `sameAs`를 **누적**(`koreanwar:… | ia:…`, 덮어쓰기 금지), `altTitle`은 제목이 다를 때만 보존

## 2026-11-21 v1.86.0 — 기관 간 동일 기록 연결(sameAs): 협약기관 재수집본 ↔ NARA 원본
- 발견: 6·25전쟁 아카이브센터 `2022-US-02-AV-D-00207`의 입수처 링크가 NARA **NAID 22345**와 같은 기록인데, 제목 언어가 달라(한글/영어) 연합검색이 별개로 표시하던 문제
- koreanwar 수집기: 상위 5건 상세 병렬 조회(24h 캐시·6s 상한) → **원본 NAID(sameAs)·생산시기(date 신규)** 확보
- 병합기: sameAs가 다른 레코드 id와 일치하면 **한 건으로 합치고 출처 모두 기록**(진짜 교차확인) + `altTitle`(다른 기관 제목) 보존
- 출력 3종: CSV `sameAs` 열 · KARDA `identifier` 노드 + `SAME_AS` 엣지 · manifest `sameAs`(owl:sameAs)·`altTitle`(dcterms:alternative) · 텍스트 목록 "↔ 동일 기록" 표시

## 2026-11-21 v1.85.3 — README·소개 페이지 가독성 전면 개편(두 저장소)
- 사용자 요청: "가독성이 좋게, 무엇을 할 수 있고 무슨 기능인지 잘 전달되게"
- README 두 개를 **사용자 관점**으로 재구성 — 한 줄 요약 → 이런 분께 → 왜 필요한가 → 설치 → **"이렇게 말해 보세요"(실측 예시 6~7개)** → 찾는 곳 → 기능(쉬운 말) → 신뢰 원칙 → **용어 풀이** → 개발자 정보(접기)
- 전문 용어(partOf·manifest·fixity·인접 채굴)를 쉬운 말로 바꾸고 용어 풀이 표로 분리
- 소개 페이지(`docs/index.html`) 두 개를 **밝은 종이 톤·본문 18px·고대비**로 새로 디자인 — 대화 말풍선+실제 응답 카드, 단계별 시작 안내(주소 복사 버튼), 지역별 기관 카드, 자주 묻는 질문(접기). 데스크톱·모바일(390px) 렌더 검수로 가로 넘침 0
- marketplace: 스킬 11종을 찾기·읽기·만들기·안내 4묶음으로, 각 스킬에 "이럴 때·예시 말하기" 제시. 배지 10종→**11종** 정정, 카드뉴스 설명 3건을 실제 카드 내용에 맞게 정정
- 예시 응답은 이번 세션 실측 결과만 사용(NARA 512건·대한매일신보 3면 3단·NAID 276537577 A등급·22013~22017 연속 필름)

## 2026-11-21 v1.85.2 — marketplace 저장소 꾸미기(사용자 확인 요청 대응)
- README: 배지 6종 센터 히어로(소스30·도구20·스킬10·원장8·서버 링크·MIT), 구 마일스톤(v1.11~15)은 접기, "The 15 archives"→30소스 현행화, cross_search·source_profile 행 현행화(format 4종·health 30채널)
- `docs/index.html` 신설 — GitHub Pages 랜딩(설치 2경로·차별점 4카드·실전 캐러셀 6장·소개 카드 12장 갤러리 — 기존 PNG 재사용). 활성화: Settings → Pages → `main`/`/docs`

## 2026-11-21 v1.85.1 — GitHub README 전면 리뉴얼 + GitHub Pages 랜딩
- korea-archive-mcp README: 13소스 시절 → 현행(30소스·9개국, 배지 6종, 연결표, 연합 검색망 권역표, 현용기록물화 사슬 다이어그램, 도구 20종 표, 감시 4종 표, 배포 상세는 접기)
- `docs/index.html` 신설 — GitHub Pages 랜딩(통계 5종·연결 안내·검색망 칩·사슬 4단계·장치 4종·실물 예제). **활성화는 사용자 액션**: repo Settings → Pages → Deploy from a branch → `main` / `/docs`
- marketplace README 헤더 현행화(15곳→30개 문서고·9개국, v1.85 배너)

## 2026-11-21 v1.85.0 — oldnews 지면 좌표 + 공표물 3종 갱신
- **oldnews 지면 위치 승격**: 목록 응답의 `newsposition`("2면 2단")을 제목에 — 신문 기사 인용의 필수 좌표(신문명·날짜·면·단)가 목록 단계에서 완성
- **공표물 갱신**: help.html·help-en.html 7½절(계층 28채널·media 직링크·데이터-지면 계보 일치 반영), 심사 팩 시연 19→**21선**(NARA 심층 판독 1콜·계층+media 내장 데이터셋), 원장 7→8종
- much·ktv 목록 이미지 탐침은 기지 차단으로 보류(블라인드 구현 금지 — 정직한 설계), oldnews는 이미지 없음을 실측 확인(지면 좌표가 실재 재료)

## 2026-11-21 v1.84.0 — media 공급 확장 + 협약기관 실계층 승격
- **media 공급 3채널 확장**: commons `prop=categories|imageinfo`(1콜 유지 — PD 사진 원본 파일 직링크)·heritage `imageUrl` 방어적 수집·(v1.83 nara와 함께 media 공급 3채널)
- **koreanwar 실계층 승격**: kwParseCards가 이미 추출하던 `상위계층`(사이트 실값)을 수집기가 버리고 있던 것을 교정 — `협약 › <상위계층>` 우선, 기존 id 패턴(수집 Y › CC › MED)은 폴백으로 유지
- **전파물 규칙 media 상속**: 보고서 규칙 4·캐러셀 규칙 3에 "cross_search media 열의 실조회 검증 직링크 우선 소싱" 명시 — 데이터→지면의 이미지 계보 일치

## 2026-11-21 v1.83.0 — NARA 3차: media 파이프라인(다매체×데이터화) + fixity 원장 NARA 등재(지속가능성×증거성)
- **media 필드 파이프라인**: nara 수집기의 디지털 객체 첫 objectUrl → 병합기 보존 → **CSV media 열·KARDA record 노드 media 속성·manifest media(dcterms:hasFormat)** — 발굴 데이터 3종 매체가 원본 매체 직링크를 내장(게재 소싱이 데이터셋 안에서 끝남). 파이프라인은 일반화 — 어느 채널이든 media를 공급하면 운반
- **fixity-watch 8종**: NARA 골든 기록 `nara:276537577`(장진호 해병 5연대 127-N-A4560, Class A Unrestricted) — scope note 지문 `5523be38a3df76a5` 프로덕션 실측으로 원장 선등재. 주간 감시는 **GH 시크릿 NARA_API_KEY 설정 시 자동 활성**(미설정 시 건너뜀 — 소음 없음)
- 보조 골든 실측: naid=535795(나가사키, RG 208)도 scope·지문·Class A 확인(등재는 한국 관련 1종만) — NARA 심층 2차(사용자 지시 "특히 nara 강화" 계속)
- **목록 맥락**: nara_search·cross_search 수집기에 생산일자(`_nara_date` — productionDates logicalDate·year 폴백), 목록 행에 `원본 n점`(digitalObjects 수 — 매체 유무를 목록에서 판별)
- **인접 채굴 맥락**: naid ±N 각 행에 계보 — 중심과 같은 시리즈인지 즉시 판별(시리즈 경계 탐지)
- **판독 심화(judge_rights naid)**: 생산(creators heading·생산일)·**소장단위**(physicalOccurrences.referenceUnits — 열람·복제 청구 좌표)·**디지털 객체 직링크**(첫 objectUrl+유형 — 다매체 제작 직결)
- 필드명은 NARA API v2 문서 기반 다중 폴백 — 배포 후 프로덕션 실측으로 확정

## 2026-11-21 v1.81.0 — 계층 구축 4차(재감사): 잔여 채널 5곳 추가 합류 → 28/30
- nara 교정(v1.80)을 계기로 "재료 부재" 잔여 7채널 전수 재감사 — 5곳에서 재료 실재 확인·구축:
  - **earchive**: 행 하단 스팬 전면 수확 — 사료ID(code)·`국가 › 소장기관`(미국 › 국립문서기록관리청 실측)·**생산기간(날짜 신규 확보)**
  - **nlna**: 토이강 번호 첫 두 세그먼트 = 형성기관 클러스터(2.05 외무부·2.13 국방부 등 9종 사상 + 폴백 `토이강 n.nn`) — 컨테이너 실측
  - **awm**: 상세 캐시에서 `Object type`(Photograph·Film·Firearm — C285584 실측) 승격
  - **ndl**: 이미 추출하던 `<category>` 첫 항목을 series로 승격(자료형·매체)
  - **commons**: list=search → **generator=search + prop=categories 1콜 전환** — 파일 소속 카테고리(큐레이션 계층) 확보
- PART_OF 23→**28채널**. 진짜 잔여 2: foia(차단 중·목록 빈약)·nedb(인덱스 미설정) — 기술적 불능/미설정만 남음
- earchive·nlna 파서는 실측 HTML/JSON로 오프라인 사전 검증(Node·Python 동일 출력 확인)

## 2026-11-21 v1.80.0 — NARA 집중 강화(사용자 지시): 계층 합류 23채널 + 판독 지문
- **nara 목록 계층 합류**: 카탈로그 API `ancestors` 실존 확인(judge_rights 기존 코드가 RG 추출에 사용 중) → `naraChain`/`_nara_chain` 공용 헬퍼 — "RG n › 시리즈" 체인을 cross_search 수집기 series·nara_search 목록 행(계보:)·karda/csv/manifest partOf(`NARA › RG n › …`)에 일괄 주입. v1.79의 "잔여 8" 중 nara는 재료가 실재했음을 교정 — **23/30채널**
- **judge_rights(naid) 판독 심화**: ① 계보 전 층 체인(RG›시리즈›파일단위, 각 층 NAID = 상·하위 항행 좌표) ② 【범위·내용】 scope note 발췌 + **본문 지문(sha256-16)** — 지문 채널 9→10 ③ 인접 채굴 안내 푸터. DEEP_READ.nara(judge_rights 재현 호출문)의 증거 사슬이 계보·지문까지 상속
- 3사본 패리티(route.js·server.py·mcp/server.py) + ci-verify·ci-parity 통과 — 계층 구축 3차(최종): partOf 22채널
- **jsg 四部 분류**(청구기호 K1~K4 = 經·史·子·集 — K2-3556 史部 실측 정합)·**kyudb 소장 문고**(제목 청구기호 접두: 奎 규장각도서·古 고도서·想白 상백문고·一簑 일사문고)
- 목록 레벨 계층 구축 **완결**: 22/30채널. 잔여 8(nara·commons·awm·nlna·ndl·earchive·foia·nedb)은 응답에 재료 부재 — 상세 판독 단계 제공이 정직한 설계
- v1.78.1 재실측: archives 전 레코드 유일 키 + 같은 파일 낱건(진주 재건 사진첩 1~13)이 파일 번호로 자연 군집(인접 채굴 구조 가시화)

## 2026-11-21 v1.78.0 — 계층 구축 2차: partOf 20채널
- 5채널 추가 구축: **archives(생산기관 — 출처주의 핵심!)**·i815(자료 카테고리)·ktv(제호 — 대한뉴스/리버티뉴스/문화영화)·seoul(ISAD 기술단위 — series/item/aggregation)·nlk(자료유형)
- 30채널 중 **20채널이 목록 레벨 계층** 보유 — 나머지 10(nara·commons·kyudb·jsg·awm·nlna·ndl·earchive·foia·nedb)은 목록 재료 부재로 상세 판독 단계 제공(정직한 설계)

## 2026-11-21 v1.77.0 — 계층정보 구축(사용자 지시: "없는 것들은 구축한다") — partOf 15채널
- 목록에 명시 계층이 없던 6채널에 **의미적 계층을 도출·구축**: gonghun(운동계열 — 3.1운동·의열투쟁 군집)·indy(판결기관 — 법원별 군집)·heritage(지정 종목 — 국보/보물/사적)·un(문서기호 시리즈 — S/RES·A/… )·gallica(ark 유형 — btv 도판/bpt6k 인쇄본/bd6t 정기간행물)·much(아카이브 카테고리 — URL 세그먼트)
- partOf 9→**15채널** — manifest·karda·csv 전부에 반영(기존 파이프라인 재사용)

## 2026-11-21 v1.76.0 — 다매체×맥락: 지면 계보=데이터 partOf 일치 조항
- 보고서 규칙 7(.prov 계보 — 시리즈 층은 partOf 값 그대로, 수기 재구성 금지)·규칙 8(전수 표에 계보 열)·카드뉴스 규칙 4(출처 캡션에 '기관 › 시리즈' 병기) — **전파물의 계보 서술이 데이터와 어긋날 수 없는 구조**. 4축 교차(다매체×맥락×데이터화) 마감

## 2026-11-21 v1.75.0 — partOf 9채널 + csv 계층 컬럼
- **tna**(참조번호 시리즈 — 'WO 281' 등 레코드그룹)·**europeana**(dataProvider 원 소장기관) 승격
- **csv에 partOf 컬럼** — 표 분석에서도 계층 필터·피벗 가능(다매체×맥락 교차). 데이터화 3종 전부에 계층 탑재 완료

## 2026-11-21 v1.74.0 — partOf 7채널
- **dnz**(기관 › 컬렉션 — 'Alexander Turnbull Library › TAPUHI')·**ia**(Internet Archive 컬렉션 — fl[]=collection 추가 수집: 'CSPAN3'·'prelinger' 등) 계층 승격 — 해외 양대 집계·미러 채널의 수집 맥락이 그래프 군집으로

## 2026-11-21 v1.73.0 — partOf 5채널 확대
- **oldnews(신문명)·aks(문중>지역 분류)** 계층 노출 — 당대 기사가 '신문 › 대한매일신보', 고문서 소장처가 '고문서 › 문중>충청남도' 시리즈 노드 아래 묶임. karda 그래프에서 **같은 신문·같은 문중 기록이 토폴로지로 군집**

## 2026-11-21 v1.72.0 (데이터화×맥락 — 상위 계층 partOf)
- **PART_OF 추출기**: NZ(Series 명+parentId — collectMerged가 series 필드 보존하도록 확장)·koreanwar(식별자 분해: 수집연도›국가›매체 — '2022-US-02-AV-D-00329'→'수집 2022 › US › AV-D')·JACAR(소장관 코드: A=국립공문서관·B=외무성 외교사료관·C=방위성 방위연구소)
- manifest 레코드에 `partOf`, karda 그래프에 **series 노드(type:'series')+PART_OF 엣지** — 기록이 어느 수집·시리즈·소장관 아래 있는지가 데이터 구조로

## 2026-11-21 v1.71.0 (사용자 4축 지시 — 맥락·증거성·데이터화·다매체 강화)
- **맥락**: manifest heldBy를 채널키→{id, 기관 정식명, 국가}로 격상 — 30채널 ARCHIVE_META 상수(karda archive 노드에도 동일 주입)
- **증거성**: 레코드별 `deepRead`(심층 판독 재현 호출문 — 15채널 매핑) — 발굴→판독 증거 사슬이 기록 내장
- **데이터화**: karda 그래프 archive 노드에 정식명·country — 그래프 단독으로도 기관 식별
- **다매체**: csv에 `node` 컬럼(선두) — csv·karda·manifest 3종 산출물이 **동일 키로 조인**(매체 간 변환의 연결고리 통일)

## 2026-11-21 v1.69.0 — `nedb_search(mode='nzarch')` Archives NZ 상세 판독
- R번호 투입 → 연합 검색이 버리던 entity 전체 메타 판독: 제목·기술계층·형태·연대·소장·**시리즈(parentId)·생산 기관·접근 상태·열람 방법(READING_ROOM 등)** — NZ 기록은 메타가 본문이므로 **메타 지문(sha256-16)** 발급(기술 개정 감지, 감시 가능 7번째 채널 후보). 간헐 차단 시 브라우저 안내. 판독 14채널
- v1.68.1: fixity-watch 원장 6종 확장(판결문·UN — GH 2차 실행 녹색)

## 2026-11-21 v1.68.0 (현용기록물화 8단계 — 개정 감시 기관화)
- **fixity-watch.yml**: 골든 기록 4종(인명사전 614·장서각 K2-3556·국가유산 근정전·공훈록 3536)의 본문 지문을 주간 재계산해 `docs/fixity-ledger.json` 원장과 대조 — **불일치=원문 개정 발생을 자동 알림**하고 원장에 개정 이력(from/to) 축적. 서버 판독과 동일 알고리즘 이식, **3종 지문 완전 일치 실측**(8f250d38·a46e5177·4adc8e6c)으로 검증. 지문 기능이 "비교 원장+자동 감시"를 얻어 산 기능이 됨 — 지속가능성의 실행 기관

## 2026-11-21 v1.67.0 (현용기록물화 7단계 — 내장 무결성·지문 8채널)
- **매니페스트 `recordsFixity` 내장**: records 배열 JSON의 sha256을 매니페스트 **내부 필드**로(자기참조 없음) — 응답 푸터의 전체 fixity와 달리 **JSON만 단독 전파돼도 무결성 검증이 따라감**
- **본문 지문 6→8채널**: KTV 대한뉴스 해설·UN 문서 요약에도 판독 시점 sha256-16 — 전문 판독 채널 전부 커버

## 2026-11-21 v1.66.0 (현용기록물화 6단계 — 지문 전면화·국제 공표)
- **본문 지문 확대(3→6채널)**: 장서각 해제(jsg)·국가유산 해설(heritage 양 분기)·판결문 사건개요+주문(indy)에도 판독 시점 sha256-16 — 전문 판독 채널 전반에서 원문 개정 감지 일관화
- **help-en 7½절 신설**: Produce/Datafy/Disseminate/Sustain — records-continuum 사슬 영문 공표(국제 상호운용)

## 2026-11-21 v1.65.0 (현용기록물화 5단계 — 고정성 fixity)
- **매니페스트 fixity**: 응답에 JSON 바이트의 sha256 지문 표기 — 전파·보관본 대조로 변조/손상 검증(OAIS 고정성 요소)
- **판독 본문 지문**: 인명사전 상세('사전:번호')·공훈록 상세(mngNo)에 판독 시점 전문의 sha256-16 표기 — **재판독 지문 불일치=원문 개정 발생** 감지(인용 검증·개정 이력 추적의 실질 장치, 본문은 이미 수신한 상태라 비용 0)

## 2026-11-21 v1.64.0 (현용기록물화 4단계 — 보존 패키지·발견성)
- **풀패키지 9단계 신설 — 보존 패키지(SIP)**: manifest.json을 ZIP 최상위에 동봉, 보고서 부록(규칙 19)·sources.txt·karda 산출물이 전부 동일 매니페스트를 참조 — **패키지 전체가 하나의 기록 단위(RecordSet)**로 등재·재검증. 재가공·전파 시 manifest.json 동반이 원칙(품질 게이트에 추가)
- HELP 안내에 '데이터화 3종'(csv·karda·manifest) 노출 — 웹 사용자 발견성

## 2026-11-21 v1.63.0 (현용기록물화 3단계 — 전파 매체에 증거성 상속)
- **보고서 규칙 19 신설**: 모든 발굴 보고서 끝에 매니페스트 JSON `<details>` 부록 필수 — provenance·heldBy·영속 식별자가 **보고서를 떠나 전파되어도 따라감**. 카드뉴스·포스터 2차 매체는 sources.txt에 매니페스트 identifier(kad-…)+재현 호출문 1줄 명기 — 어떤 매개로 변환돼도 원 발굴로 복귀 가능(의제의 "퍼져갈 수 있도록"을 증거성 유지 조건으로 충족)
- v1.62 프로덕션 재실측: JSON-LD @context·node 키 정상, commons 교정 성과 — '유관순'에 초상+**일제감시대상인물카드** 합류 확인

## 2026-11-21 v1.62.0 (현용기록물화 2단계)
- **매니페스트 JSON-LD 격상**: `@context`(Dublin Core dcterms + **RiC-O rico:** 용어 매핑 — RecordSet/Record·hasOrHadHolder·hasRecordSetMember) — 기관 기록관리시스템·링크드데이터와 상호운용 가능한 직렬화
- **매니페스트↔karda 그래프 키 공유**: manifest 레코드에 `node`(=karda 노드 id), karda 레코드 노드에 `identifier`(원 식별자) — 같은 발굴의 두 데이터화 산출물이 동일 키로 상호 참조(매체 간 일관성)
- **commons 인명 질의 교정**: TOPICS 미등재 한국어가 'Korea' 단독으로 뭉개지는 손실 실측('유관순'→일반 Korea 파일) → commons는 한국어 네이티브 검색 가능하므로 앵커 단독 수렴 시 원질의 유지 — '유관순'→Ryu Gwan-sun.jpg·**일제감시대상인물카드** 직결 확인
- **발굴 수집기록 매니페스트 — `cross_search(format='manifest')`** (사용자 제안: "맥락·증거성 갖는 현용기록물로 생산, 데이터화→다매체 전파, 지속가능성"): 발굴 행위 자체를 ISAD(G)·RiC 지향 기록으로 생산 — ①증거성=provenance 블록(질의·소스·수집시각·**재현 호출문**·채널 통계), ②맥락=heldBy(소장기관, 복수=교차확인)·영속 식별자, ③데이터화=표준 지향 JSON(기록관리시스템·KARDA 등재용), ④다매체 변환 사슬 안내(보고서·카드뉴스·karda 그래프·CSV), ⑤지속가능성=영속 식별자 우선 인용(URL 부패 대비)+health 주간 감시. 레코드 30건 상한(24KB 내)
- **KARDA 온톨로지 서버화 — `cross_search(format='karda')`**: 로컬 스킬(archival-discovery-pipeline) 전용이던 노드·엣지 생성 지식을 서버 출력으로(제1원칙 — 웹·모바일 동등성). topic·archive·record 3층 노드 + FOUND/HELD_BY 엣지 JSON — 복수 HELD_BY=기관 교차확인이 그래프에서 보임. 레코드 30건 상한(24KB 가드 내), Gephi·Neo4j·vis.js 직투입. 인물 그래프는 '종합:이름'과 결합 안내
- v1.59.0: nzarch 폴백 R번호(id) 매칭(라이브 차단 중 재조회 0건 방지), PROJECT_OVERVIEW v1.58 전면 갱신, LOC 전 경로 차단 재확인(보류 유지)

## 2026-11-21 v1.58.1
- **nzarch 이중화 완성(프로덕션 실측 교정 2건)**: ① 0건 응답엔 hits 키가 없음(totalHits로 스트림 판별) ② icn1은 **간헐 Incapsula**(health 🟢 1.5s 직결 성공 vs 분 단위 차단 교차) → **nz-harvest.yml**(주간 화 07:07, GH 수확 136건→public/nz-index.json 커밋→배포) + 수집기 폴백('·주간인덱스' 투명 표기). 실측: '한국전쟁' 5건(Kayforce·전쟁일지 DAK1-7, Open/Restricted 권리 태그)
- 함정 2건 추가: untracked 파일에 git diff --quiet '변경 없음' 오판(add 후 --cached로), 봇월 쿠키 워밍업은 시도 금지(공개 경로 발견으로 해결)

## 2026-11-21 v1.58.0
- **Archives NZ(뉴질랜드 국립기록원) 합류 — cross_search 30소스**: 사용자 요청("합류 가능하도록 다른 방법을")을 GH 러너 역공학 10차로 완결. 수확 경로: 인라인 설정의 프록시 경로 노출(3차) → /local-rest 공개 JAX-RS 확인(4차) → **헤드리스 크롬 실입력으로 연합검색 XHR 포획**(8차: `GET /federated-search/customers/aims/search?q=&size=&isFuzzy=true&sourceId=aims-archive`) → **평문 GET 200 판정**(9차 — 8차의 401은 경로 착오, 보호 우회 불필요) → 단건 스키마 확정(10차: SSE 프레임 JSON — entity.name·id(R번호)·resultDate·**accessStatus 권리 표시**·series). 'Korea' 1,356건 실측
- 교훈 축적: YAML 블록 스칼라 안 heredoc 종결자 함정(들여쓰기로 미종결 — base64 임베드로 회피), 80KB 단일행 grep 교착(6차 행), 봇 보호 우회(쿠키 워밍업)는 시도하지 않음 — 공개 경로 발견으로 해결
- retry-blocked: NZ 관찰 블록 제거(합류 완료, 6곳), nz-probe 워크플로 삭제(탐사 종료). health 30채널, help 30곳
- **DigitalNZ 합류 — cross_search 29소스**: 뉴질랜드 국가 집계 API(api.digitalnz.org/v3, 무키 JSON 익명 호출 실측) — **직접 차단이던 Papers Past(한국 관련 18,725건)를 우회 복구**, 터닝불도서관(TAPUHI 사진)·Te Papa·오클랜드박물관 등 NZ 30+기관 동시 커버. content_partner·primary_collection 태그로 기관 식별. health 29채널(골든 'Korean War')
- **인물 종합 대조 — `nedb_search(mode='gonghun', '종합:이름')`**: 레시피 ①의 도구화 — 공훈록(mngNo·훈격)+인명사전(사전:id·운동계열)+판결문(주문·URL) 3채널 병렬 1회 호출, 한자명·생몰 대조로 동명이인 분리 가이드. 스키마 불변(쿼리 오버로드)
- **Archives NZ 본체 역공학 착수(사용자 요청)**: DigitalNZ에 Archives NZ 소장기록 부재 실측(DIA=관보뿐) → GH 러너(유일하게 Incapsula 통과)를 원격 실험실로 쓰는 일회성 탐사 워크플로(nz-probe.yml) — SPA XHR/JSON 엔드포인트 추출, Adlib wwwopac 후보 탐침. 직결 불가 시 GH 주간 수확→정적 인덱스 폴백 설계
- **dclean 확장 엔티티 디코드**: 인명사전 전기에 &amp;lsquo;·&amp;middot; 리터럴 노출 — Node만 기본 5종 처리(Python html.unescape 비대칭). 인용부호·가운뎃점·수치참조 추가, 프로덕션 재실측 정상
- **retry-blocked 2차 실행 수렴**: LAC(403)·UN AtoM(마커) 오탐 제거 확인. Archives NZ는 GH IP에 실페이지 서빙 확인 — 단 Arena JS SPA+개발망 Incapsula로 합류 불능이므로 **관찰 전용**(비발화) 전환, 주간 false alarm 제거

## 2026-11-21 v1.56.0
- **한국독립운동인명사전 합류 — `nedb_search(mode='i815', '사전:…')`**: retry-blocked 1차 실행이 감지한 복구 중 유일한 진짜(4건 중 3건은 오탐 — 아래). '사전:이름'=검색(이름·한자·운동계열·주요활동·항목번호), '사전:번호'=상세(기본정보 — 생몰·본관·이명·출신지·포상훈격 + **전기 전문** 3,200자 컷). detail.do는 폼 파라미터 5종 전체 필수(id만으론 500) — searchResult.do?searchType=all&searchWord= 확정. 공공저작물(출처 표기) 고지 내장. 실측: 유관순(614) — 이명 冠順·대한민국장(2019)·전기 4,092자
- **retry-blocked 탐침 오탐 교정**: 1차 실행 실측 교훈 반영 — curl은 403에도 exit 0이므로 **HTTP 코드 실측**(-w %{http_code}) 추가, 마커를 차단 페이지에 없는 문자열로 강화(UN AtoM 'search-result' — JS 챌린지의 URL 에코 'informationobject' 오탐 제거 · LAC 'Library and Archives Canada' — 403 보안확인 페이지 오탐 제거 · NZ 'Archives New Zealand' — Incapsula 오탐 제거). i815 인명사전은 합류로 목록 제외(7곳)
- 레시피 ① 인물에 '사전:이름' 편입(gonghun과 상보 — 공훈록=공적, 인명사전=학술 전기)
- **보류 소스 복구 자동 감지(retry-blocked.yml)**: 보류 8곳(kdemo·LOC·NAA·Archives NZ·Papers Past·LAC·UN AtoM·i815 인명사전)을 주간 탐침 — 200+마커로 복구 판정(차단 페이지 오탐 방지), 감지 시 워크플로 실패 알림으로 합류 검토 착수. 공훈전자사료관(v1.30)·역사박물관(v1.47) '재점검→당일 합류' 전례의 자동화

## 2026-11-21 v1.54.1
- **지식 마감 동기화**: 레시피 ⑤ 도시·공간사(heritage 해설·much 실물 편입)·⑥ 소싱(much 공공누리 자동판정·heritage) 갱신 — 판독 13채널 완전체 기준. 심사 팩 시연 19선(+국가유산 해설)
- **28소스 'all' 연합 성능 실측**: '한국전쟁' 전수 — **12.4초**(타임박스 상한 수렴), 25채널 수확·병합 64건, 실패 3채널(— 표시: gallica 기지·foia 기지·ndl 콜드/429)

## 2026-11-21 v1.54.0
- **국가유산 상세 판독 완결**: 명세로 남겼던 재역공학 열쇠(목록 XML 원값 캡처) 실행 — 기관 asno가 cpno 표기와 다른 **13자리 원값**('00'+지정4+'0000000')임을 실측 확정. 목록이 복합 id(kdcd-asno-ctcd)를 보존하고 상세가 원값 직행, cpno 입력도 역산 후보로 동작. 실측: 근정전 — 시대(1867 중건)·해설 전문(정도전 작명·다포식·12지신상…) 판독 성공. 판독 13채널 완전체

## 2026-11-21 v1.53.0
- **`nedb_search(mode='heritage')` 국가유산 판독**: ccbaCpno(13자리) 투입 시 cpno를 종목·시도·지정번호로 분해해 무키 상세 API(SearchKindOpenapiDt) 호출 — 명칭(한자)·종목·소유/관리·시대·소재·**해설 전문**(3,500자 컷) 판독. 심층 판독 13채널
- 작업망 차단 지속 — 검증된 fix-forward 사이클(icn1 실측 판정)로 배포

## 2026-11-21 v1.52.0
- **국가유산포털 합류 — cross_search 28소스**: 국가유산청 OpenAPI(무키 XML — SearchKindOpenapiList) — 명칭(한자)·종목(국보/보물/사적)·소재지·ccbaCpno 딥링크. 이 작업망에서는 차단이나 **배포 전 icn1 도달성을 기존 scrape_plan 도구로 원격 실측**(robots 허용 확인) 후 fix-forward 합류 — 프로덕션 health가 최종 판정
- health 28채널(골든 질의 '숭례문'). 문서 28소스 동기화. cross_search 설명 1024자 재축약

## 2026-11-21 v1.51.1
- **통합 정리 2차**: 27채널 전수 health 실측 스냅샷(🟢24 — 신규 6소스 전부 녹색·🟡1·🔴기지2, 응답 중앙값 ~1.1s)으로 문서 고정 — 심사 팩 v1.51(시연 18선: 당대 신문 3단·판결문 완주·박물관 KOGL 자동 추가, 판독 12채널 절), 종합 현황 문서 v1.51(판독 표 12행·권리 4연결)

## 2026-11-21 v1.51.0
- **`nedb_search(mode='indy')` 판결문 판독**: 상세 URL 투입 시 이름(한자)·당시나이·본적/주소·판결기관·죄명·주문·**사건개요**(판결문 요지)·**원문 뷰어 직링크**(archiveEventId 역산) 판독. 게재윤리(수형 사실 존엄) 고지 자동. 심층 판독 12채널
- 실측: 유관순 — 당시 18세·충남 천안군 동면 용두리·소요/보안법위반·사건개요·원문 뷰어

## 2026-11-21 v1.50.0
- **독립운동판결문 테마관 합류 — cross_search 27소스**: 국가기록원 theme.archives.go.kr/next/indy GET 역공학 — 이름(한자)·판결기관·판결날짜·**주문(형량)**+상세 딥링크. gonghun 수형기록의 '판결문' 항목을 원문 창구로 직결(레시피 ① 갱신). 실측: 유관순 2건(경성복심법원 1919-06-30 징역3년·상고기각) — gonghun 수형기록과 정합 확인
- HELP·심사 팩 '판독 9채널'→11채널 현행화, 문서 27소스 동기화. Python HELP 작은따옴표 함정 재발(oldnews \'본문:\')을 py_compile이 검출·교정

## 2026-11-21 v1.49.0
- **신문 본문검색 연대 한정 — `'본문:키워드|1905-1910'`**: 서버 faceted 페이로드는 연결을 거부(실측) → 상위 30건 후처리 필터 + **연도 분포 요약**(by_issuedYear 상위 6) 자동 표시. 실측: '본문:의병|1907-1907' — 전체 4,028건 분포(1908:982·1907:908…) 중 1907년 지방소식(적성 감악산 의병 200명 양주 내습 등) 발췌만 정렬
- 함정 기록: facetedType/facetedData JSON은 서버가 빈 응답으로 연결 종료 — 후처리 필터가 안전 경로

## 2026-11-21 v1.48.0
- **`nedb_search(mode='much')` 소장품 판독**: idnbr·URL 투입 시 소장품번호·재질·작가·크기·**공공누리 유형 실문구 → judge_rights 자동 초판정**(제4유형→B 즉시)·설명 본문(서지 상세) 판독. 기록 단위 KOGL 자동판정이 박물관 실물로 확장 — 권리 자동화 4번째 연결. 심층 판독 11채널
- 실측: 한박21084 「판문점의 비사」(1953 평문사 한국전쟁 소설) — 제4유형→B·설명 전문

## 2026-11-21 v1.47.0
- **대한민국역사박물관 근현대사아카이브 합류 — cross_search 26소스**: '검색 경로 미확정' 보류를 당일 해제 — POST /search.do(searchQuery) 서버 렌더 역공학. 근현대 **소장품 실물**(포스터·간행물·피켓 등) 제목·자료연대·idnbr 딥링크 + 카테고리 집계 보충. 실측: '판문점' 소장품 25건(판문점의 비사·미루나무 작전 포스터·1969년 잡지)
- health 26채널. 문서 26소스 동기화. cross_search 설명 1024자 재축약

## 2026-11-21 v1.46.0
- **신문아카이브 OCR 본문검색 — `mode='oldnews'`에 '본문:키워드'**: search_bodytext.do 역공학 — 색인어에 없는 표현·인용구까지 **국한문 OCR 원문 발췌**로 발굴. 실측: '본문:단지동맹' 65건 — 1907년 학동 단지·고종 하사금 환수·청년동지회 단지동맹 등 색인 밖 기사 발췌 원문
- recipes ① 인물 레시피에 oldnews(본문 검색 포함) 편입

## 2026-11-21 v1.45.0
- **`nedb_search(mode='oldnews')` 신문 기사 판독**: CNTS ID·URL 투입 시 news_detail.do JSON 역공학 — 기사제목·신문명(한자)·발행일·**색인어 전체**(기사 내용 재구성 수준 — 안중근 공판 기사 25색인어 실측)·KSH 주제어·**관련기사 연쇄**(재판 보도 날짜순 추적)·원소장처. 본문은 이미지 원문(뷰어 안내). 심층 판독 10채널
- 실측: CNTS-00095729484(대한매일신보 1910-02-15 안중근씨공판) → 색인어 26개·관련 공판 기사 5건 연쇄

## 2026-11-21 v1.44.0
- **대한민국신문아카이브 합류 — cross_search 25소스**: 국립중앙도서관 신문아카이브(nl.go.kr/newspaper)의 POST JSON 검색(search_newspaper.do)을 역공학 — 1883~1960 신문(공립신보·신한민보·황성신문 등) **기사 단위 전문 검색**: 기사제목·신문명·발행일·CNTS 딥링크·원소장처 메타. 실측: '의병' 7,512건(1908~09 공립신보·신한민보 기사). i815 신문자료(독립기념관 소장분)와 상보하는 신문 전수 축
- health 25채널. HELP·help.html·심사 팩 25소스 동기화
- 재점검 기록: 역사박물관 근현대사아카이브(archive.much.go.kr)는 검색 경로 미확정 — 후보 유지

## 2026-11-21 v1.43.0
- **`query_bank(topic='recipes')` 발굴 완주 레시피 6종**: 이 세션에서 실측으로 확립한 주제 유형별 발굴→판독→권리 순서를 서버 지식화(제1원칙) — ①인물(gonghun 이명 확보→i815 재검색→jacar) ②한국전쟁(협약→naid 실확인→un PDF) ③조선 고문헌(law→sibling→jsg 해제) ④일제강점기(ndl⇄jacar 상보) ⑤도시사(seoul→ktv) ⑥이미지 소싱(commons PD→A). 공통 원칙 4개조 포함

## 2026-11-21 v1.42.1
- **통합 정리**: HELP_GUIDE에 심층 판독 9채널 안내·예시 3종(장서각 해제·UN PDF·1910년 기사) — 웹 사용자 완주 경로 완결. 심사 팩 v1.42(시연 15선 — jsg·commons·un 판독 추가, 판독 체계 절 신설). 종합 현황 문서 PROJECT_OVERVIEW_2026-11-21.md(24소스·판독 9채널·권리 3축·보류 지도·사용자 액션 체크리스트)

## 2026-11-21 v1.42.0
- **`nedb_search(mode='un')` UN 문서 판독**: record URL·recid 투입 시 문서기호(파일명 역산)·발행일·주제(UNBIST)·**요약(abstract)**·언어별 PDF 직링크(영문 우선) — 안보리 결의·보고서 원문을 분석에 바로 투입. 심층 판독 9채널
- **ndl 응답 강화**: 저자·매체 범주(紙/デジタル) 표시 + 429 동시접속 제한을 명시적 오류로(건강 진단 정확도)
- nedb_search 설명 1024자 재축약(판독 모드 10종 수용)

## 2026-11-21 v1.41.0
- **일본 NDL 서치 합류 — cross_search 24소스**: ndlsearch.ndl.go.jp OpenSearch 무키 실측(any= 파라미터) — 조선총독부 간행물·관보·통계연보·도판 축(JACAR 공문서와 상보). 한→일 JA_MAP 우선 변환 재사용. 실측: 朝鮮総督府 8,162건 · 京城 写真 1,983건(凱旋式之図 등)
- health 24채널. HELP·help.html·심사 팩 24소스 동기화. cross_search 설명 1024자 재축약

## 2026-11-21 v1.40.0
- **UN 디지털도서관 합류 — cross_search 23소스**: 보류된 UN Archives(AtoM 챌린지)와 달리 Invenio `of=xm`(MARCXML)이 무키로 열림을 실측 — 안보리 결의·공식문서(S/·A/ 문서기호+제목+날짜+record 딥링크). 한→영 자동 변환. 함정 기록: X-Requested-With 헤더에 빈 응답 — 일반 헤더 필수
- **full_package 1단계에 심층 판독 연계 명시**: 발굴 후 핵심 기록은 판독 8채널로 본문·권리 실확인 — 풀패키지 산출물 품질 직결
- health 23채널. HELP·help.html·심사 팩 23소스 동기화

## 2026-11-21 v1.39.0
- **`nedb_search(mode='jsg')` 장서각 서지·해제 판독**: 청구기호(K2-…)·dataId·URL 투입 시 자료명·청구기호·MF번호·분류 3종(연쇄 앵커 — 단독 매칭은 내비 필터와 혼동)·**해제 전문**(정의·서지사항·체제 및 내용·특성 및 가치·참고문헌, 4,000자 컷) 판독. 실측: K2-3556 개건도감의궤(1776 경모궁 개건) 해제 1,500자
- 심층 판독 8채널 완성 — 고문헌축(jsg 해제·kyujanggak·aks)·근대축(i815·gonghun·jacar)·현대축(ktv·earchive·seoul·commons)

## 2026-11-21 v1.38.0
- **`nedb_search(mode='commons')` 파일 판독**: File URL(또는 File:제목) 투입 시 라이선스(PD/CC → A/B/D 초판정 자동)·작가·**출처(원 소장처 크레딧 — NH·NARA 번호)**·촬영일·설명·원본 해상도 판독. 24h 캐시·도메인 한정. 실측: NH 96379 서울 수복(1950-09-29, 해병대 Ed Barnum 병장 촬영, PD → A)
- 심층 판독 모드 7종 완성(jacar·gonghun·i815·ktv·earchive·commons + seoul 전용도구) — 발굴→판독→권리 실확인 전 구간이 도구 응답 안에서 완결
- nedb_search 설명 1024자 준수 재축약(ci-verify가 검출)

## 2026-11-21 v1.37.0
- **위키미디어 공용 합류 — cross_search 22소스**: 키 불요 검색 API(한→영 자동 변환) — PD 사진·NARA/해군 재수집본의 원 소장처 역추적 창구. 'Seoul 1950' 791건 실측(해군역사센터 NH 시리즈 등). 공유 IP 429 가능성은 health가 상시 실측
- **cross_search 푸터에 심층 판독 이어가기 안내**: 소스 태그→판독 경로 8종([i815]→mode=i815 … [nara]→judge_rights(naid)) — 연합 검색에서 본문 판독까지 끊김 없이
- 해외 확장 재점검 기록: 호주 NAA(Cloudflare)·뉴질랜드 Archives NZ(Incapsula)·LOC(전 JSON 엔드포인트 Cloudflare) 보류, Trove는 무료 키 확보 시 합류 후보
- HELP_GUIDE·help.html·심사 팩 22소스 동기화

## 2026-11-21 v1.36.0
- **서울기록원 기록 단위 실체화 + 상세 판독**: 컬렉션명 매칭에 그치던 채널을 /catalog/result 서버 렌더 역공학으로 승격 — 시리즈(제목+/aggregation 딥링크)·사진 기록건(/item 딥링크)·컬렉션 카드 3유형 수확. `seoul_archives_search`에 상세 URL 투입 시 심층 판독(스키마 불변 오버로드): **식별번호(RG-SR-IT)·기술계층·법적지위·이용조건**(judge_rights 투입 — "제한없음+원본 협의 필요" 같은 기록 단위 권리 실문구)·기술 본문. 실측: 한강주변 도로신설 공사(RG5-SR90-IT2399)
- 함정 기록: Python _clean은 태그 무공백 결합 — 경계 정규식 \s* 필수(Node와 차이)

## 2026-11-21 v1.35.0
- **국편 전자사료관 세션 상세 역공학 해제 → `nedb_search(mode='earchive')`**: '상세 딥링크 없음(세션 기반)'으로 보류했던 상세 열람을 해제 — fnGoCatalogView가 catalogId가 아닌 **검색 폼+searchPosition 재제출** 설계임을 확인, 쿠키 유지 2단 POST로 상세 판독('키워드|순번' 입력). 열람조건·이용조건(권리 문구 — judge_rights 투입)·등록번호·사료건 ID 추출. 심층 판독 모드 4종(i815·gonghun·ktv·earchive)
- 평문 매칭이 내비게이션 '열람·이용조건' 메뉴와 혼동되는 함정 발견 → row-box HTML 앵커로 교정(명세 기록)

## 2026-11-21 v1.34.0
- **`nedb_search(mode='ktv')` 영상 판독 모드**: ehistory view URL 투입 시 대한뉴스·기록영상의 제목·제작연도·상영시간·출처·해설 전문 판독(24h 캐시·도메인 한정). 키워드면 목록. KOGL 출처 고지 자동 — 심층 판독 모드 3종 완성(i815·gonghun·ktv)
- **foia fail-fast**: opengov 장기 차단으로 재시도 포함 21초를 태우던 수집기를 단발 6초로 — health·연합 탐침 시간 보호, 복구 시 자동 정상화
- 기지 🔴 재진단: opengov(연결 리셋)·gallica(BnF 403) 지속, open.go.kr 본체는 세션+txId SPA로 브라우저 전용 판정 유지

## 2026-11-21 v1.33.0
- **`nedb_search(mode='i815')` 상세 판독 모드**: v1.32 목록 실체화에 이어 "발굴→분석" 다리 완성 — query=키워드면 실체화 목록, detail.do URL이면 **자료 본문 판독**(당대 신문기사: 신문명·발행일·생산정보+기사 전문 / 독립운동가 자료: 복명서 등 번역 전문 4,000자). 24h TTL 캐시 · i815 도메인 한정(임의 URL 페치 방지). 실측: 신한국보 1910-03-15 '공판 후의 안중근 씨' 전문
- 새 도구 없이 기존 모드 확장(PlayMCP 20개 준수). 독립운동 3채널 완성: i815 신문·자료 판독 + gonghun 공훈록 판독 + jacar 일본 측 메타

## 2026-11-20 v1.32.0
- **i815(독립기념관) 목록 실체화**: '신문자료 234건' 집계 신호에 그치던 채널을 실제 자료 발굴 채널로 승격 — 최대 카테고리 목록을 파싱해 자료 제목+**GET 딥링크**(구분별 detail.do — contentsFrm 역공학: 독립운동가/선교사/신문/미주흥사단/임시정부/의병/마이크로필름)를 상위에 제시, 나머지 카테고리는 집계 신호 유지. 실측: 안중근 → 신한국보 1910-03-15 '공판 후의 안중근 씨' 기사 전문 딥링크
- **nlk 6h TTL 캐시**(마커 <item>) — 실측 7.7s 최저속 축 완화. Python urllib 비ASCII URL 거부 교정(quote)
- health.yml 주석 21채널 현행화

## 2026-11-20 v1.31.2
- **사용자 대면 지식 동기화(제1원칙)**: `HELP_GUIDE`(창기창기 도움말) 15개→**21개 아카이브** 전 기관 명시 + 신기능 예시(공훈록 판독·naid 권리 실확인·mode 안내) — 웹·모바일 사용자가 도구 응답으로 최신 기능 인지
- help.html·help-en.html 21곳으로 갱신 · PlayMCP 심사 대응 팩 v1.31 전면 개정(시연 질의 12선 — gonghun 심층 판독·naid 실확인·21채널 health·성능 절 추가)

## 2026-11-20 v1.31.0
- **`nedb_search(mode='gonghun')` 심층 판독 모드**: 공훈전자사료관을 신호 채널(cross_search)에서 분석 채널로 승격 — query=이름이면 목록(mngNo), 숫자(mngNo)면 **공적조서·공훈록 본문 판독**(이명·생몰일 base64 디코드·본적·포상년도/훈격·공적개요 한글병기·공훈록 전문 4,000자 + 수록정보). 24h TTL 캐시. 실측: 안중근 3150 → 이명 安應七·공훈록 8권(1990) 전문
- 새 도구 없이 기존 모드 확장(PlayMCP 20개 준수). "발굴→분석" 다리: 웹·모바일 사용자도 공훈록 본문을 도구 응답으로 분석 가능(제1원칙)

## 2026-11-20 v1.30.0
- **공훈전자사료관 복구 → cross_search `gonghun` 합류(21소스)**: 과거 '사이트 오류' 보류였던 e-gonghun.mpva.go.kr 가 복구된 것을 재점검에서 확인 — 키 없는 GET 검색(독립유공자 공훈록 인명 채널)·상세 딥링크(mngNo — 공적조서·공훈록·묘소·현충시설 한 페이지) 역공학. base64 성명 디코드·한자명·생몰년·운동계열·포상년도·포상훈격 파싱. 실측: 안중근(1962 대한민국장)·유관순(2019/1962)·윤봉길
- health 21채널. 같은 재점검에서 kdemo(검색 오류)·UN Archives(JS 챌린지)는 보류 지속 확인

## 2026-11-20 v1.29.0
- **규장각(kyudb) 성능**: 목록·해제 2회 POST 병렬화 + 6h TTL 캐시(결과 있을 때만 — 奎 마커 검증). 실측 10.2s로 12s 타임박스에 근접해 cross_search에서 간헐 탈락하던 위험 해소
- **Python health 병렬화**: 20채널 탐침을 스레드풀(≤8)로 — 순차 합산 수십 초 → Node Promise.all과 동작 패리티. 채널별 ms 표시 유지
- **nara_search 권리 라인에 NAID 실확인 연계 안내**: RG 초판정 아래 `judge_rights(naid=<NAID>)` 실확인 경로 명시 — 웹·모바일 사용자도 응답 규칙으로 신기능 인지(제1원칙)

## 2026-11-20 v1.28.0
- **`judge_rights(naid=…)` NARA 실확인 자동판정**: 카탈로그 v2에서 해당 레코드의 Use Restriction 필드를 실제 조회해 자동판정 — `Unrestricted` 실확인 시 **A 확정**(기존 "확인 시 A 상향" 수동 규칙의 자동화), `Restricted` 계열은 C, 미기재는 RG 초판정 유지. RG 번호는 레코드 ancestors에서 자동 추출. 키 미설정·조회 실패 시 폴백 안내
- **health 채널별 응답시간(ms)**: 20채널 골든 질의 각 행에 실측 응답시간 표시 — 느려지는 채널(타임박스 근접)을 수치로 조기 발견
- i815 독립운동가 인명사전(search.i815.or.kr/dictionary)은 연결 리셋·HTTP 500으로 보류 기록

## 2026-11-20 v1.27.0
- **연합 검색 성능·견고성**: 소스별 **12초 타임박스**(Node Promise.race / Python fut.result) — 차단 대기 소스(갈리카 등)가 전체 'all' 호출을 끌던 실측 21.7초 병목 해소 · AWM 상세·JACAR 메타 **24시간 TTL 캐시**(마커 검증 — 캐시 히트 실측 1.2s→0.36s)
- **`query_bank(topic='allies')`**: 한국전 참전·지원 22개국 발굴 지도 — 보유 소스 직행(미·영·호·네덜란드·프) vs 대체 경로(캐나다=영연방 교차, 터키=RG 407) 매핑, 부대 고유명 열쇠(Kagnew·PEFTOK·Jutlandia·NORMASH·60th Para Field Ambulance 등)

## 2026-11-20 v1.26.0
- **네덜란드 국립문서보관소 합류 — cross_search 20소스**: SPA 셸 뒤의 공개 JSON API(zvt…/api/search/eads)를 Playwright 역추적으로 확보(키 불요). 'Korea' 243건 — 주한 네덜란드 대사관(2.05.202)·한국전 파견부대(2.13.56) 문서군 직행
- **AWM 심화**: 상세 파싱에 권리 자동 태그(저작권 만료 → `권리:PD`)·Conflict 기간(date) — 해외 소스 권리 표시 1호
- 뉴질랜드 Papers Past는 Incapsula 게이트로 보류 기록

## 2026-11-20 v1.25.0
- **호주 전쟁기념관(AWM) 합류 — cross_search 19소스**: 검색 모자이크(SSR C-id)→상세 병렬 2단 수집으로 제목·수장번호 확보(실측: Kapyong → 가평 계곡 1952 항공 조망 147844·파노라마 HOBJ3143~45). 한국전 영연방 축 신설
- **캐나다·독일·UN 접근 판정 기록**(docs/overseas-expansion-spec.md): LAC=Cloudflare Turnstile 차단(대안: AWM·TNA 교차), UN=자체 JS 챌린지(AtoM — 완화 시 즉시 합류 가능), 독일=DDB 무료 API 키 확보 시 `ddb` 합류 경로 + Europeana가 독일권 기집계

## 2026-11-20 v1.24.0
- **장서각 XHR 재역공학 성공 → cross_search 18소스** — Playwright 실브라우저로 실제 사용자 플로를 재현해, 검색 파라미터의 실형식이 **`q=query|<검색어>`**(필드 접두 필수)임을 확정. 플레인 `q`·`query`는 조용히 무시되고 전체 열람(1,349,451건)을 반환하는 함정(네트워크 캡처로 XHR 부재까지 확증). curl 서버사이드 재현·<em> 하이라이트 분절 제목 견고 파싱 — 의궤 33,805건(종묘의궤 K2 청구기호), 호적(ANC 고문서 중초) 직행 링크 실측

## 2026-11-20 v1.23.0
- **JACAR 강화(전용 모드 승격)**: `nedb_search(mode='jacar')` — 한→일 **JA_MAP 48항목**(16→48: 전투·지명·인물·사건) 우선 변환 검색 · 레퍼런스코드 **메타 직행**(Title·생산자·이미지 수·기밀등급 파싱) · **인접 채굴 ±span×100**(簿冊 내 건 번호 간격 100 실측 — ±1·±10은 404). 실측: B04014056900(국제연맹 탈퇴 관계, 58면, Top Secret) ± 같은 簿冊 연속건 / 징용→徴用 검색
- **규장각 강화**: cross_search에 `kyudb` 소스 합류(17소스) — 기존 목록+해제 POST 코어 재사용, 奎 청구기호 신호 채널
- **장서각·민주화운동 오픈아카이브 보류 기록**: 장서각은 검색이 비공개 XHR(청구기호 직행 /dir/view?dataId=JSG_…만 확보), kdemo는 개편 중 오류 — 명세에 재점검 대상으로 기록

## 2026-11-19 v1.22.0
- **독립기념관·KTV e영상역사관 합류(cross_search 16소스)** — i815: GET 실측(★searchMenu 필수 — 누락 시 500), 카테고리 집계+직행 링크 신호 채널(임시정부·독립운동가 자료·신문자료 등) · ktv: ehistory /search는 iframe 셸, 실체는 ktv.go.kr 통합검색 GET — 대한뉴스·기록영상 딥링크 파싱(판문점 2,641건)
- **JACAR 한→일 출력 사전(16항)**: 朝鮮総督府 등 일본어 질의가 영어와 다른 결과축을 여는 것을 실측 — jacar 수집기에 한→일 우선 적용
- 헬스체크 16채널. 접근 명세: docs/i815-ktv-access-spec.md

## 2026-11-19 v1.21.0
- **국편 전자사료관 합류(cross_search 14소스)** — archive.history.go.kr POST 검색 실측·역공학(`allSearchQuery` 폼, `fnGoCatalogView`+title 파싱, 사료ID 추출). NARA 수집 사료 원문 창구: '노획' → AUS005 노획 무기·물자 영상 실측. 상세 딥링크는 세션 기반이라 사료ID 표기(docs/earchive-gonghun-access-spec.md)
- **공훈전자사료관 보류 기록**: 사이트가 자체 오류 상태 — 공공데이터포털 15157239 API 경로를 대안으로 명세(키 확보 시 합류)

## 2026-11-19 v1.20.0
- **일본 JACAR 합류(cross_search 13소스)** — 아시아역사자료센터(공문서관·외무성 외교사료관·방위연구소) GET 검색을 전수 실측해 연합 검색·헬스체크에 투입. ★핵심 발견: 검색어 파라미터는 `kw`(`keyword`류는 조용히 무시되고 기본 목록 반환 — 서로 다른 키워드 대조 검증으로 적발). 레퍼런스코드 직행(`/das/meta[-en]/<코드>`)·계층 브라우징·연대/기관 필터 폼까지 docs/jacar-access-spec.md에 명세화(전용 도구 승격은 심사 후 슬롯 재편 시)
- **help.html·help-en.html 현행화**: 아카이브 16곳+(JACAR·한국고문서자료관), 방법론 그리드에 연대 필터·권리는 표시·인접 채굴 4기관·표기 변형 자동 팬아웃, 예시에 명성황후 편지 38건 실증, FAQ에 채널 상태 점검

## 2026-11-19 v1.19.1
- **문서 현행화**: README(양 저장소)·HELP_GUIDE(창기창기 안내)·mcp/README 도구 표 — v1.17~1.19 신기능(연대 필터·인접 채굴 4기관·cross_search 13소스·variants·csv·health·KOGL·exhibit·24KB 가드) 전면 반영. README에 발굴 우선 원칙 명시
- **TTL 캐시**: 전투정보 목록(warList)·AKS 분류 트리 6시간 인메모리 캐시(웜 인스턴스) — 오류 응답은 캐시하지 않음
- **PlayMCP 심사 대응 팩**: docs/playmcp-review-pack.md — 제약 준수 요약·반려 해소 증빙·실측 시연 질의 10선·채널 상태

## 2026-11-19 v1.19.0
- **국내 연대 필터**: `archives_search`·`nlk_search`에 year_from/year_to — API가 연대 파라미터를 지원하지 않으므로 상위 50건 내 후처리 필터로 구현하고 라벨에 '후처리' 명시 (koreanwar는 기존 서버사이드 필터 유지)
- **인접 채굴 일반화**: `nara_search(naid, radius)` — NAID ±N을 naIds 콤마 목록 **한 호출**로 일괄 조회(NARA 공식 문서 기반, 사진 ±3·색인 ±1 간격 지식 안내) · `ia_search(identifier, radius)` — 일련번호 말미 숫자 ±N 존재 확인(실측: 111-adc-10076±2 → 4건 실존). TNA·koreanwar에 이어 4기관째
- **`cross_search(format='csv')`**: 병합 결과를 sources,title,date,id,url CSV 블록으로 — 스프레드시트·KARDA 온톨로지·통계 분석 직투입("자료로써 분석할 수 있게")
- **`report_template(kind='exhibit')`**: 고문서 전시형 산출물 규칙+HTML 골격 — aks-archive-harvester 스킬 ④매개 단계의 서버판(전시 페이지·카드 1080×1350·학습지 A4·게시 문구, 추정 금지 캡션 규칙, AKS 출처 고지). 제1원칙(웹·모바일 동등성) 잔여 공백 해소

## 2026-11-18 v1.18.1
- **응답 24KB 공통 가드**: server.tool 래퍼(Node)·등록 후 일괄 래핑(Python, mcp<2 전제)에 UTF-8 바이트 실측 트렁케이션(여유 23,800B) — PlayMCP 한도를 도구별 수동 slice가 아니라 구조적으로 보장. 절단 시 분할 조회(page·max_results) 안내 부착
- **CI 자동화(GitHub Actions)**: 양 저장소 `verify`(push·PR마다 node --check·py_compile·도구 20종·설명 1024자·TOPICS 컴파일·3사본 패리티 diff·런타임 등록) + mcp 저장소 `health`(주간 프로덕션 13채널 골든 질의 실측 — 🔴 3채널 이상이면 실패 알림). 수동 검증 체계의 자동화 — Gallica류 무증상 장애 재발 방지

## 2026-11-18 v1.18.0
- **소스 헬스체크**: `source_profile(institution='health')` — 13채널 골든 질의 일괄 실측(🟢건수/🟡연결만/🔴실패) + 서버 키·인덱스 설정 상태. 발굴 우선 원칙의 전제("깨짐을 스스로 발견한다") 도구화
- **warmemo 복구(신 플랫폼 폴백)**: 전쟁기념관 구 통합검색(archives.warmemo.or.kr)이 개편으로 결과 구조 소멸(실측) → 0건 시 동일 재단 6·25전쟁 아카이브센터(koreanwar.or.kr, 협약기관) 검색으로 자동 대체 + 개편 사실 명시
- **권리 힌트 자동 표시**: judge_rights에 **공공누리(KOGL) 제1~4유형 자동 판정** 추가(kla/ledger.py 양 사본) · Europeana 건별 rights(CC/InC) 표시 · archive.org 건별 licenseurl 표시 · NARA record_group 지정 시 권리 초판정 라인 자동 부착 — "발굴 우선, 권리는 표시"의 자동화
- **표기 변형 자동 팬아웃**: `cross_search(variants=True)` — 당대 표기(Corean·Corea·Chosen·Keijo·Fusan·Chemulpo·Gensan·Heijo·Quelpaert·Taikyu) 최대 2종을 해외 4채널(tna·ia·nara·europeana)에 자동 병렬 투입, 채널 태그에 변형 표시(예 ia·Corean) — query_bank '열한 겹의 벽' 지식의 도구화

## 2026-11-18 v1.17.2
- **cross_search 소스 13종**: 사용자 결정으로 `seoul`(서울기록원 컬렉션)·`foia`(서울정보소통광장 결재문서 원문) 합류 — 각 전용 도구(seoul_archives_search·foia_search)와 동일 접근 경로 재사용. open.go.kr 본체(브라우저 전용)는 전용 도구 경로 유지
- Gallica 차단 감지 우아한 성능저하(v1.17.1 후속): BnF가 서버 IP 자동 조회를 403 차단(실측) — SRU XML이 아니면 차단 사실·대체 경로(웹 검색/브라우저)를 명시 반환, 연대 필터는 dc.date(BnF 공식 색인)+후처리 폴백으로 교정
- TNA 연대 필터 0건 시 '연대 미상 기록 제외' 안내

## 2026-11-18 v1.17.1
- **연대 필터·페이지네이션 표준화(해외 5종)**: `tna_search`·`ia_search`·`gallica_search`·`europeana_search`에 `year_from`/`year_to`(연대 범위)와 `page`, `nara_search`에 `page` 추가. 전 문법 실측 검증 — TNA `sps.dateFrom/To`(Korea 13,533→1950~51 한정 2,553건), IA `date:[A TO B]`+page, Europeana `YEAR:[A TO B]` 열린 범위(*)·다중 qf. Gallica `gallicapublication_date` CQL·startRecord(배포 서버 검증)
- **cross_search 소스 11종으로 확대**: `warmemo`(전쟁기념관 — 카테고리 건수 신호 채널)·`aks`(한국고문서자료관 소장처 172곳 — 내장 카탈로그, 네트워크 0) 합류. 서울기록원·정보공개포털은 robots 실측(`archives.seoul.go.kr/robots.txt` Disallow `/catalog/`) 확인으로 기존 설계대로 미포함 유지
- harvester/tna.py `_search`에 `start_page`·`date_from`·`date_to` 옵션 (하위호환)

## 2026-11-17 v1.17.0
- **한국고문서자료관(AKS) 서버 노출** — 제1원칙(웹·모바일 동등성) 이행: `nedb_search` **mode='aks'** 신설. 소장처 **172곳 내장 카탈로그**(2026-11-17 treeAjax 전수 실측) 이름 검색 → 분류 트리 → 문서 목록(예: 동춘당 송준길가 교령류 266건) → 건별 면수·UCI·썸네일(imgnode)까지 라이브 조회. 이미지 일괄 수집은 로컬 전용(aks-archive-harvester 스킬 — DZI 타일 복원)·웹은 뷰어 열람으로 대체 경로 명시. 전 경로 라이브 검증 완료(도구 수 20 유지 — enum 모드 흡수)
- **6·25 후기 단계 전투 앵커 16건**: `koreanwar_search(scope=battle)` — 기관 전투 DB(개전 초기 69건)에 미수록인 인천상륙·장진호·청천강·흥남·지평리·임진강(글로스터)·가평·피의 능선·단장의 능선·백마고지·저격능선·폭찹힐·금성·정전협정 등을 서버 큐레이션 앵커(통설 전사 시기 + TNA WO 281·NARA RG 관 교차검색어)로 보완. "기관 DB 아님" 명시·수치/전과 주장 없음
- **다국어 주제 사전(TOPICS) 43→85항목**: 후기 전투(지평리·가평·백마고지 상세·금성 등)·지명(원산·대구·개성·철원·금강산·독도)·개항기~해방 인물·사건(명성황후·고종·안중근·김구·3·1운동·위안부·강제동원·광복군·임시정부·동학·의병·을사조약·아관파천·헤이그 특사·제주 4·3·여순·신탁통치·미군정) — 한자·일·중·러 입력 패턴 병행, Gallica용 프랑스어 사상 확충(지평리=프랑스대대 등)
- **의존성 고정**: `mcp>=1.0,<2` (mcp 2.x의 FastMCP 제거로 임포트 실패 — 2026-11-13 실측)
- 11월 반영분 소급 기록: **koreanwar_search·koreanwar_item**(6·25전쟁 아카이브센터 협약기관 — 통합검색+전투정보, NARA NAID 역추적, radius 인접 채굴, 도구 20개 통합: ia_metadata→ia_search·local_gov_search→foia_search) · 한국어→영/프 자동 변환으로 PlayMCP 반려 사유 해소(갈리카 병인양요 0→5,853건) · 매직 키워드 영문 슬러그 인식·cross_search 선두 배치 · mcp/server.py 개발용 진입점 배포본 동기화
- Node(route.js) ↔ Python(배포본·개발용) 3사본 패리티: py_compile·node --check·런타임 등록 20종·TOPICS 85 패턴 컴파일 전수 통과

## 2026-08-19 v1.16.0
- **웹 서비스 계층**(korea-archive-mcp.vercel.app): 루트 랜딩 · 사용 안내 /help.html(+영문판 /help-en.html) — 갤러리 14유형 55컷·실물 쇼케이스 카드·조사 방법론 절 · **기록잇다** /ingitda.html — 6문서고 연합 즉석 검색(TNA·IA·갈리카·유러피아나·6·25아카이브[한국어 실검색]·NARA) + 문서고별 검증/노이즈 표기 판별 · 실물 예제 /examples/(한강 보고서 4.8MB·조선 강연 풀덱 403장)
- **조선 덱 채굴 자산**: `chosen_joseon_deck.md` — 10층 방법 상세·아홉 나라 검색어 지도·참조코드 전수(TNA 74·NAID 134·Gallica 30 등)·미해결 숙제 5건. query_bank identifiers/persons에 895 코드 지도·성씨 색인 칸 증보
- plugin.json v1.16.0 — 설명·키워드 현행화


## 2026-08-19 v1.15.0
- **조선 사료 심층 판독 통합**(한강 강배 조사 1485~1986 실측 이식): `nedb_search` **9모드** — law(법전·원문 제공 판정)·record(**座目 자동 필터** — "601건이 아니라 492건이 座目")·item(미공개/파싱실패 구분)·**★sibling(형제 조 전수 스캔)**·matrix(법전 수록 대조 — 부재의 발견)·origin(어휘 연원)·sjw(왕대 분포·최초 용례)·kyujanggak(목록+해제 동시+ImageServlet 패턴 지식). `joseon_tools.py` 동봉(표준 라이브러리만)
- **도메인 스킬 통합**: joseon-source-mining(references 6종)·joseon-source-excavation·khdb-citation·nanet-citation·kyujanggak-images·record-annotation·changgi-help + korea-archive-discovery **v2 references 승격**(11벽·식별자 해독·인명 열쇠·교차검증·world_archives 신설)
- **전쟁기념관 OpenAPI 채널 활성**: 발급 토큰 **Referer 바인딩 실측**(korea-archive-mcp.vercel.app) — 호출 헤더 자동 첨부, pageSize 상한 100. 토큰은 `KOREANWAR_API_TOKEN` 환경변수(공개 저장소 커밋 금지)
- **매직 키워드 웹 네이티브화**: MCP **prompts 2종**(full-package·changgi-help) + server instructions · `report_template` kind 8종(**help**·citation·annotation 추가) · 사용 안내 페이지 `/help.html`(갤러리 14섹션·시연 mp4 포함)
- **query_bank 조사 전략 6토픽**: walls·identifiers·persons·crosscheck + **world**(일 JACAR·중 당안관·러 ГАРФ/ГАХК 등 6개국 분류 비교)·**cities**(도시명 계보·1914 경계·로마자 표기법 연대) — 조선 강연 풀덱 채굴분
- selfcheck 원본 반영(`scripts/`) — 8443 판정은 **환경 의존**으로 정정(로컬·Vercel 8443 정상 재실측)

## 2026-08-13 v1.14.0
- **매직 키워드 "풀패키지"**: `report_template(kind='full_package')` — 발굴 조사→실물 수집→매거진 보고서(kind='magazine': 표지·목차·뒷표지·KA 인장·검증 낙관·브랜드 테마 5종)→카드뉴스 8장(kind='carousel' 12규칙)→포스터 시리즈→Canva(kind='canva_prompts' 7종)→**홍보 카드뉴스(실제 지면 캡쳐 쇼케이스)**→**입문 카드뉴스("○○은 처음이지?" 키워드 정복형)**→**메시지형(미장센 문법 — 1장 1메시지·블랙아웃 테제)**→**기록 해설형(점선 영역 판독·메타 표·원판/사본 계보·추정 금지)**→**발표 PPTX(16:9·발표 노트 필수·Canva 편집)**→**시연 영상(GIF/MP4)**→ZIP 패키지+작업 로그+**KARDA 온톨로지**(nodes/edges CSV·basis·confidence) — 산출물 12종 오케스트레이션
- 품질 게이트: CSS 템플릿 전체 포함·핵심 기록 카드 이미지 필수·placeholder 잔존 검사·수치 정합·전 도판 출처·게재윤리 4단계
- 실전 검증 2건: 글로스터 연대(제1호 — TNA 훈장 추천서 원문·65건) · 장진호(제2호 — 3개국 3중 소장 실증·153건)


## 2026-08-04 v1.13.0
- **insta-carousel 스킬 신설**: 발굴조사 결과를 인스타그램 캐러셀 카드뉴스(1080×1080 PNG)로 제작하는 원스톱 파이프라인
  - 발굴조사 방법론 내장(`references/discovery.md`): 표기 변형 병렬 투입 → 교차검색 → **인접 채굴(식별번호 ±5~15)** → 공개 상태 🟢🟡🔴 3단계 실검색 판정 → 메타데이터 검증("제목만 믿으면 틀린다")
  - 실물 이미지 소싱 플레이북(`references/image-sourcing.md`): 위키미디어 Commons API·archive.org `.thumbs` 프레임 추출(ffmpeg 불요)·헤드리스 크롬 카탈로그 캡처 + 라이선스 4단계 판정표 + **이미지별 출처 대장(sources.txt) 의무화**(원 소장처+식별번호가 본 출처, 사본처는 부기)
  - 검증된 디자인 시스템(`assets/card_styles.html`): 고대비 팔레트, 파노라마 필름스트립·부채꼴 스택·지도 여정·인물 카드·빅넘버 등 레이아웃 아키타입(`references/layouts.md`) — 하단 안전영역(.col)으로 페이지번호 겹침 구조적 방지
  - 렌더 스크립트(`scripts/make_carousel.py`): {{img:...}} 토큰 base64 임베드 → 카드 분리 → 헤드리스 크롬/엣지 PNG 캡처 → 크기 검증, `--only N` 부분 재렌더·`--expect N` 장수 보증·`--size` 세로형
  - 후킹형 캡션 가이드(`references/copywriting.md`): 한 줄 한 호흡 리듬·훅 공식 4종·표준 출처 표기 형식
  - 8·15 광복 81주년 7부작+번외편(총 9종, 85장) 실전 제작으로 검증된 워크플로

## 2026-07-30 v1.12.0
- **6·25전쟁 아카이브센터**(koreanwar.or.kr:8443, 전쟁기념관재단 — **MOU 협약기관**) TNA식 구조화 도구 신설:
  - `koreanwar_search`: 통합검색(viewType=archive 완전 목록·pageSize 10/20/50) — 결과카드에서 archRfcd·생산기관·상위계층 파싱, **상위계층의 NARA Record Group 자동 추출 → nara_search 역추적 링크**. 서버측 필터 실측 검증: 생산연도 범위·수집구분(수집/기증/구입/기탁/제작/이관/차입). `scope='battle'`이면 전투정보 DB(개전 초기 69전투 — TNA WO 281·NARA RG 407 교차검증 앵커). `KOREANWAR_API_TOKEN` 승인 시 OpenAPI(pbrcList.do) 공식 메타 채널(KOGL·이용조건·저작권 필드) 자동 병행 — 신청·승인 대기 중에도 검색은 키 없이 동작
  - `koreanwar_item`: 건별 메타(생산처·생산시기·입수처·열람 및 이용조건) — NARA 재수집본은 **입수처 링크가 catalog.archives.gov NAID 직결**(실측: 2022-US-02-AV-D-00207 → NAID 22345). `radius=1~8`이면 archRfcd 말미 일련번호 ±N 인접 채굴(실측: 00207 장진호 → 00206 맥아더 연포비행장·00208 F-86 김포; 정중한 3건 배치 병렬)
- `cross_search`에 koreanwar 채널 합류(키 불요) · `source_profile('koreanwar')` 3층 프로파일 + **상세검색 코드표 전체 수록**(자료유형 13종·수집구분 8종·자료연대·열람/이용조건·확장자 — 실측 추출)
- **PlayMCP 개발가이드 준수(2026.06.12판)**: 도구 24→**20개 통합**(`ia_metadata`→`ia_search`의 identifier 모드, `local_gov_search`→`foia_search`의 source 파라미터, koreanwar 4→2) · 원격 서버 전 도구 **annotations**(title·readOnlyHint·destructiveHint·openWorldHint·idempotentHint) · description 서비스명(Korea Archive 코리아 아카이브) 병기+1024자 이내 · 인접 채굴 배치 병렬화(p99 응답성)
- 협약 준수: 모든 요청에 프로그램 식별 UA(`KoreaArchiveMCP … MOU partner integration`) + 정중한 호출 간격

## 2026-07-13 v1.11.0
- **cross_search** (신규 도구): 여러 아카이브(tna·ia·gallica·europeana·nara·archives·nlk·nedb)를 한 쿼리로 **동시 교차수집**해 병합·중복제거, 출처 태그(복수 출처=교차확인) — 상호보완 동시수집
- **source_profile** (신규 도구): 전 기관(해외 5+국내 6)의 **자료구조·이용구조·활용구조** 3층 프로파일 (이용구조는 실제 엔드포인트 추출, robots는 live 검증)
- **국내 3대 부정합 키워드셋** (신규): 국사편찬위·국가기록원·국립중앙도서관·서울기록원·전쟁기념관 — 언어적/분류학적/기술관행적 부정합 대응, 라이브 도구로 **실측 검증한 252종** + 분류 교차매핑 + 관행 노트 (`keywords_<기관>.py`), query_bank로 노출
- **nlk 이중채널**: 전체 소장자료 ⊕ 자료유형(category) 정밀 채널 동시 수집·병합
- **nedb 합법 수집**: db.history.go.kr는 robots가 크롤러 차단 → data.go.kr **공식 개방파일(KOGL)** 을 인덱싱(`scripts/ingest-opendata.mjs`)해 검색(`NEDB_INDEX_URL`) — 라이브 스크래핑 없음
- **지오블록 우회**: seoul.go.kr의 해외 IP 차단 대응 — Vercel 함수 리전 Seoul(icn1) 고정 + robustFetch(타임아웃·재시도·프록시 폴백)
- HTML 분석 리포트 `docs/source_profiles.html` (전 기관 3층 프로파일)

## 2026-07-10 v1.10.1
- fix: 국가기록원 OpenAPI 엔드포인트 수정 + 국립중앙도서관(NLK) 파서 견고화 — 두 기관 모두 실제 결과 반환

## 2026-07-10 v1.10.0
- 키가 없는 국내 소스는 dead-end 대신 에이전트 WebSearch로 핸드오프
- docs: README 18개 도구·국내 소스·자동 브라우징 반영, 18장 카드 갤러리, SKILL 웹검색 노트

## 2026-07-10 v1.9.0
- 국내 도구 서버 사이드 자동 브라우징 — 각 사이트를 직접 페치·파싱해 실제 결과 반환

## 2026-07-10 v1.8.0
- 전쟁기념관 아카이브 추가 (`warmemo_search`)

## 2026-07-10 v1.7.0
- 지방 정보공개·기록원 추가 (`local_gov_search`: 서울정보소통광장·서울시교육청·경상남도기록원)

## 2026-07-09 (국내 아카이브 도입, v1.3~v1.6)
- 국사편찬위 한국사DB(`nedb_search`)·국가기록원(`archives_search`)·국립중앙도서관(`nlk_search`) 추가
- cheliped 브라우저 스크래핑 폴백(`scrape_plan`)·HTML 발굴 보고서(`report_template`) 추가

## 2026-07-09 v1.2.1
- Europeana 공용 데모 키 폴백 — 키 없이 즉시 작동

## 2026-07-09 v1.2
- 플러그인이 기본으로 원격 서버(Vercel)에 연결 — Python 설치 등 요구사항 제로

## 2026-07-09 v1.1 / v1.1.1
- Gallica·Europeana 추가(도구 9종), 이중언어 README, 8장 카드 갤러리
- 스킬 설명에 Gallica·Europeana 트리거 반영

## 2026-07-07 v1.0 (초판 배포)
- docs: 보고서 v6.0→v6.5 (7개 선행 보고서 통합, 실행편 §25~32, 웹 검증, 논문 통합)
- docs: 마스터 쿼리 코퍼스 v1.0→v1.1 (600+ 쿼리 12체계 + 논문 프레임워크 §13)
- harvester v0.2: NARA 10단계·TNA 14레이어·Adaptive Mining — TNA 실수집 1,214건, 승격후보 73건
- collector v0.1: 수집대장 17필드·권리 자동판정·링크 재검증(15/17 OK)·대시보드
- mcp v0.1 / skill v0.1: AI 에이전트 장착판
