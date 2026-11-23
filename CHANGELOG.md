# Changelog

## v2.29.0 — 다매체 확산: 구독·인용·타임라인 (2026-11-23)
- 원장에서 매일 생성: feed.xml(Atom — 새로 발견된 기록 100건, 구독기·자동화로 확산), records.csl.json(Zotero·Mendeley·Pandoc 인용), records.ris(EndNote·RefWorks), timeline.json(연대 × 기관 × 매체 + 대표 기록·IIIF). 매체 유형은 제목·URL 근거(영상·사진·지도·문서).
- 원장 페이지 내려받기 링크·Atom 자동 발견 링크. source_profile('ledger')에 전 형식 안내(웹·모바일에서도 확인), 옛 문구 '검색어·사용자 정보 없음' 정정. Node·Python 패리티, 골든 ledger-media-formats.

## v2.28.0 — 발견 경로: 질의 ↔ 기록 증거 사슬 (2026-11-23)
- 질의 지문 ak(도구+인자, 키 정렬 sha256-16)를 도구 래퍼가 요청 맥락에 실어 발견 기록 묶음(ka:in)과 질의·회신(ka:q) 양쪽에 기록.
- 원장 병합: 기록마다 found_by(자기를 찾은 질의 지문들), docs/data/provenance.json(질의 → 발견 기록 목록·호출 수·회신 판 수), RiC-O prov:wasInformedBy. 원장 페이지 링크.
- 효과: 어떤 질문이 어떤 기록을 찾았고 그때 회신이 무엇이었는지 끝까지 따라갈 수 있음(맥락·증거성). 원격 서버 전용(Python 로컬 플러그인은 원장 없음). 도구 스키마 변경 없음.

## v2.27.0 — 계층·IIIF 없는 기록에 구축 (2026-11-23)
- 원장 기록 중 원 기관 계층이 없는 것(위키미디어 공용·서울기록원·Archives NZ·UN 등 30건)에 파생 계층 `[파생] 유형/주제 › 연대` 구축 — 근거: 서울기록원 유형 표기([기록건·사진])·AIMS 제목 첫 단·UN 문서 유형·파일 매체·연대(date → 제목 연도 → 메타 생산일). 원 기관 partOf와 분리된 partOf_derived 필드.
- IIIF가 없는 기록(244건)에 기록 봉투 브리지 매니페스트를 만들어 iiif_built로 기록(iiif_kind 구분). CSV·JSONL·인기 CSV·RiC-O(rico:hasOrHadInstantiation, 파생 계열은 rico:generalDescription으로 표시) 반영.
- cross_search(sources='ledger')는 원 기관 계층이 없으면 파생 계층을 계열로 표시. Node·Python 패리티, 골든 ledger-derived-hierarchy.

## v2.26.1 — 질의·회신 원문 그대로 축적 (2026-11-23)
- 개인정보 패턴 제거(scrub) 폐지 — 질의 인자·회신 본문을 어떤 가공·삭제 없이 원문 그대로 축적(기록의 원형 보존·증거성). v2.26.0은 회신 본문에도 적용돼 13자리 이상 식별번호 등 기록 원문을 바꿀 수 있었음 → 수정.
- cross_search 안내문: '원문 그대로 공개 누적 원장에 영구 축적 — 공개를 원치 않는 본인 정보는 질의에 넣지 마십시오'. 골든 ledger-query-notice 갱신.

## v2.26.0 — 질의·회신 영구 축적 · 지우지 않는 원장 (2026-11-23)
- 원격 서버: 모든 도구 호출의 질의(개인정보 패턴 자동 제거 — 이메일·휴대전화·주민번호·카드번호·긴 숫자)와 회신 본문(deflate)을 날짜 함 ka:q에 적재 → ledger 워크플로가 docs/data/queries/YYYY-MM.jsonl.gz·index.json으로 영구 병합. 같은 도구·인자·회신이면 횟수만, 회신이 바뀌면 새 판(응답 변화 증거). 자동 검사 호출 제외. 읽기 /api/ledger/<날짜>?kind=q.
- 기준·분류 축적: docs/data/classifications.json — 발견 기록의 계층 경로 전 단계(깊이·처음/마지막·기록 수·기관), 사라진 경로도 보존.
- 지우지 않음: 원장 일별 이력 90일·사용 추이 400일 잘라내기 폐지. 연구원 연구DB는 원 기관에서 사라진 기록을 withdrawn(날짜)로 보존.
- 원장 페이지에 질의·회신 축적 섹션(도구별 호출·최근 질의). cross_search 안내문에 영구 축적·개인정보 주의 고지. 골든 ledger-query-notice.
- Python 로컬 플러그인: 질의 축적 없음(Redis 없음 — 원격 서버 전용). 도구 스키마 변경 없음.

## v2.25.0 — 관련성 감사 자동화 (2026-11-23)
- scripts/relevance_audit.py: 33개 수집처에 골든 질의 → 결과 제목·계열에 검색어 또는 인정 번역어(漢江·朝鮮·Chosin·Hungnam 등)가 최소 1건 있는지, 옛 오답 패턴(Archive-It 크롤링 묶음·한국사DB 메뉴 항목)이 없는지 검사. 0건은 health 담당(관련성 실패로 세지 않음). X-KA-Probe: relevance(원장 적재 제외).
- relevance 워크플로(매주 목 03:23 KST + 수동): 실패 → auto-health 이슈, 통과 → 자동 종료. 첫 실행 실측: 33/33 통과.
- MAINTAINING: 새 수집처는 CASES에, 새 오답 패턴은 JUNK에.

## v2.24.0 — 관련성 감사 · IA 크롤링 묶음 결함 수정 (2026-11-23)
- 관련성 감사: 35개 수집처 골든 질의 결과에 검색어(번역어 포함)가 실제로 들어 있는지 전수 점검 — 한국사DB(v2.23 수정)에 이어 IA 결함 발견. 그 밖의 '검색어 미포함'은 번역·원표기(漢江·朝鮮·朝鮮総督府·Chosin·Hungnam)·본문/목차 일치라 정상 판정.
- 결함 수정(IA): 전체 필드 검색이 Archive-It 웹 크롤링 원자료·라디오 스트림으로 상위를 채움(실측 'Korea' 5건 전부 'Archive-It Crawl Data'). → 제목 범위 + 문서·영상·이미지, 0건이면 web·collection·account 제외, gov.* 원본 우선·youtube- 사본 뒤. 연합검색·ia_search 공통(iaSearch / _ia_search), 고급 문법은 그대로. 실측 'Hungnam' → NARA 사본(428-npc-171·111-adc-8610 — NARA 원본과 자동 병합), '장진호' → DTIC 보고서·C-SPAN.
- 골든 ia-relevance(must_not 'Archive-It Crawl Data'). MAINTAINING에 관련성 감사 절차.

## v2.23.0 — health 🔴 채널 복구: 한국사DB 실검색 · Gallica data.bnf.fr (2026-11-23)
- 결함 수정(한국사DB): 연합검색·nedb_search 통합 모드가 통합검색 페이지(GET)의 **사이트 메뉴**를 결과로 읽어, 무엇을 검색해도 메뉴의 'new' 항목 '헌정사 자료 DB·포로신문보고서' 2건만 나오던 장기 결함(검색어가 응답에 한 번도 없음 — 실측). → 시대별 하위 DB POST로 주요 8개 DB(비변사등록·각사등록·한국독립운동사자료·임시정부자료집·동아일보·자료대한민국사·휴전회담회의록·삼국사기) 병렬 검색, 건수·기록 제목·고정 URL(db.history.go.kr/id/levelId)·날짜(levelId에서), 6h 캐시. 실측 '한강' 2건(메뉴) → 7개 DB 실기록(동아일보 2,407 · 자료대한민국사 290 · 비변사등록 190 · 삼국사기 175 …). 계열 = 한국사DB › 시대 › DB.
- 복구(Gallica): Gallica SRU 403 + BnF 카탈로그 연결 불가(서버·컨테이너 모두 시간 초과) → data.bnf.fr 공식 SPARQL(제목 전문검색 + Gallica 원문 링크) 우선, 0건일 때 카탈로그. 실측 'Corée' 1.3s·8건 전부 Gallica 원문(1868~1952).
- foia(정보공개포털 점검·서울소통광장 시간 초과)는 기관 측 사정 — 표시 유지.
- Node·Python 패리티(Python은 독립 POST 구현 _nedb_live·_bnf_sparql). 골든 nedb-live-subdb·gallica-databnf.

## v2.22.0 — 자동 파이프라인 자기 감시 (2026-11-23)
- 연구원 수집 품질 관문(scripts/nrich_harvest.py): 데이터셋 건수가 지난주의 70% 미만이거나 URL 채움 90% 미만이면(원 기관 열 순서 변경 신호) 그 데이터셋은 지난 색인 유지 + meta.warnings + 종료 코드 3. 가짜 응답 실측: 고고학저널(호) 31→2건·URL 0% → 31건 유지·경고.
- 워크플로 알림: nrich-harvest(경고·실패) · ledger(실패)가 auto-health 이슈를 열고 정상이면 자동 종료. ledger 푸시 전 rebase(자동 커밋 충돌 방지).
- source_profile('health')에 '자동 파이프라인 신선도' — 연구원 색인(9일)·발견 원장(2.5일) 기준 초과 시 🔴, 품질 경고 수 표시. Python 패리티, 골든 health-freshness.

## v2.21.0 — 인물 종합 대조 4채널 (2026-11-23)
- nedb_search(mode='gonghun', '종합:이름')에 4번째 채널 '국립문화유산연구원 연구DB 인물'(금석문 찬·서 · 초상화 · 괘불 화승 · 일기 저자) — 공훈록·인명사전·판결문과 병렬. 독립운동가·조선 인물 모두 한 화면에서 교차.
- 인물 기록 예시는 연대 문자열의 첫 연도로 정렬(문자열 정렬 시 '대한제국'이 '조선'보다 앞서던 문제). 연대는 원 데이터 표기(피장자 시대·건립 시점 혼재 가능) — 생몰년 대조 안내.
- 공용 조회(nrPeople·nrPeopleKeys·nrPeopleLines / _nr_people…)로 '인물:' 모드와 공유. Python 패리티, 골든 person-4ch.

## v2.20.0 — 연구원 인물 색인 · CSV·RiC-O 내보내기 (2026-11-23)
- 인물 색인 docs/data/nrich/people.json(3,740명): 금석문 찬(撰)·서(書)·제액·전액·본문, 초상화 화가, 괘불 화승, 일기 저자를 역할별로 분해(한자 병기, 호환 한자 NFKC 정규화 — 宋時烈 표기 2종 통합, 비신·전면·집자 등 비인명 제외).
- nedb_search(mode='nrich', query='인물:이름') — 역할별 건수·기록 목록(연대 포함). 예: 의겸(義謙) 화승 5건(청곡사 1722 ~ 개암사 1749), 송시열(宋時烈) 찬 109·서 6·서·본문 1 등. 서(書)의 집자(옛 글씨 모아 새김) 가능성 안내. Node·Python 패리티, 골든 nrich-people.
- 데이터 내보내기 docs/data/nrich/export/: 21종 CSV(엑셀 BOM, 메타 열 합집합, IIIF 열) + 인물 있는 4종 RiC-O JSON-LD(기록 › 묶음 계층, 인물=rico:Person, 찬·화가·화승·저자=rico:hasCreator, 서·제액=dct:contributor). 주간 수집 때 함께 갱신(--derived로 파생물만 재생성). 안내 페이지에 링크.

## v2.19.0 — 연구원 IIIF 계층 컬렉션 · KV 구간 불러오기 (2026-11-23)
- 계층 IIIF: 이미지 데이터셋 14종 12,019건을 '데이터셋 › 지역(시·도 정규화)·소장처·분류 › 기록' 정적 컬렉션으로(docs/data/nrich/iiif/index.json · <키>.json · <키>/<묶음>.json, 277개) — 주간 수집 때 함께 생성, 작은 묶음(<3)은 '기타'. 안내 페이지 docs/data/nrich/index.html(묶음마다 KV 링크), 원장 페이지에 링크.
- KV 원 기관 서버 예의: 컬렉션의 매니페스트를 전부 한 번에 받던 것을 처음 48건만, 넘기거나 멀리 있는 기록을 열면 다음 구간을 이어 받도록(동시 6개 유지) — 수천 건 묶음에서 요청 폭주 방지.
- v2.19.1: KV에서 CORS 헤더가 없는 원 기관 정지 이미지(국립문화유산연구원 등)가 '이미지를 열지 못했습니다'로 뜨던 결함 — 한 번 실패하면 CORS 없이 일반 이미지로 다시 연다(표시 전용). 실측: 금석문 › 경상북도 2,200건 묶음에서 25초간 브리지 요청 48건(구간 프리페치), 본 이미지 정상 표시.
- nrich_harvest.py --iiif-only(수집 없이 계층만 재생성). IIIF 안내(IIIF_GUIDE)에 계층 주소.

## v2.18.0 — 연구원 IIIF 브리지 14종으로 확장 (2026-11-23)
- /iiif/nrich/{키}-{번호}: 이미지가 있는 연구DB 데이터셋 전부 — 금석문·초상화·괘불 + 조선시대 개인일기·목간·조선고적도보·고고학저널 유적·공예도설·전통문양·고문헌·향교·석조문화유산·개성 유적·보존과학 분석(+국외문화유산 ov). 원 페이지 주소는 색인(u)에서, 원본·대형 이미지가 있으면 썸네일 제외(최대 24 캔버스, 총수 표기), 공공누리 = 색인 표기 우선·없으면 Open API 개방목록 기본값.
- 이미지 없는 기록은 같은 주소에서 기록 카드(기록 봉투) 매니페스트로 응답 — KV 연속 보기에서 빠지지 않음.
- 연구DB id(ksm:3 등)가 iiifFor·_iiif_for·원장 iiif_for에서 바로 브리지로 연결(URL 패턴 불필요). 골든 nrich-iiif-stone.

## v2.17.0 — 국립문화유산연구원 IIIF 브리지 · 데이터셋별 분할 색인 (2026-11-23)
- /iiif/nrich/{ov-mseq|ksm-n|portrait-n|gwaebul-n}/manifest.json(lib/ka_iiif.js nrich): 국외문화유산·금석문·국가지정 초상화·괘불을 IIIF Presentation 3로 구축 — 원 기관 원본 이미지(file_link, 변경 없이 연결) 캔버스, 상세 항목(시대·연대·유형·재질·크기·소재지·서체·찬자/서자·제작자·지정·소장처 등), 해설(색인)·권리(공공누리 원문)·판독 시각·설명 지문·navDate.
- iiifFor·_iiif_for·원장 iiif_for가 portal.nrich.go.kr 상세 URL을 브리지로 연결 → cross_search(format='iiif'|'manifest')·KV 연속 보기·원장 계층 IIIF에 자동 반영.
- 정적 색인을 데이터셋별 파일(docs/data/nrich/<키>.jsonl)로도 분할 저장(브리지·데이터셋 안 검색이 전체 16MB를 읽지 않게, 성장 대비). nrich-harvest가 함께 갱신. 골든 nrich-iiif-bridge.

## v2.16.0 — 연구DB 21종 30,647건 · 데이터셋 안 검색 (2026-11-23)
- 연구원 Open API 10종 추가 수집(정규화 필드 실측): 공예도설 31 · 한국의 전통문양 1,296 · 고문헌 조사목록 729 · 향교 건축 108 · 석조문화유산 518 · 한국고고학저널(호) 31 · 제철유적 65 · 영산강유역 지석묘 1,368 · 보존과학연구(분석) 29 · 문화유산 전통재료(문헌 용례, 원문 한문 포함) 2,098 → 색인 21종 30,647건.
- nedb_search(mode='nrich', query='ksm:광개토') — 데이터셋 키 + 키워드 = 그 데이터셋 안에서만 검색(번호면 기록 판독). 키: ksm·portrait·gwaebul·diary·mokgan·jcbib·jcphoto·dict·arch·koguryo·gaesong·design·pattern·oldbook·hyanggyo·stone·journal·iron·dolmen·assay·material. Python 패리티. 골든 nrich-db-scoped·nrich-db-material.

## v2.15.0 — 국립문화유산연구원 연구DB 11종 정적 색인 (2026-11-23)
- 연구원 범용 Open API(키워드 검색 없음) 11종을 주 1회 공식 API로 전체 수집 → docs/data/nrich_db.jsonl(24,374건, 정규화: 명칭·이칭·연대·소재/소장·해설 150자·부가 메타·공공누리·원 기관 URL). 금석문 6,557 · 초상화(국가지정) 112 · 괘불 64 · 조선시대 개인일기 1,431 · 목간 512 · 일제강점기 고적조사 문헌목록 1,006 · 조선고적도보 15 · 한국고고학사전 13,995 · 고고학저널 유적 601 · 고구려 유적 65 · 개성 문화유적 16.
- cross_search(sources=nrich): 색인을 함께 검색(명칭 일치 우선) — 계층 국립문화유산연구원 › 연구DB › 데이터셋 › 지역/소장처. nedb_search(mode='nrich', query='ksm:3' 등 연구DB id) → 전체 필드·원 기관 상세 URL. 목록 출력에 '연구DB n건'.
- 실측: 색인 적재 0.27s·검색 0.08~0.11s(원 기관 요청 0). API 실측 사항 — firstindex=시작 행·recordcountperpage=끝 행(명세와 다름), 공식 End Point(http).
- v2.15.1: 배포 직후 골든 실패 교정 — 연합검색 첫 호출에서 11.7MB 색인 적재가 수집기 제한(≈12s)을 넘겨 nrich 결과 전체(국외문화유산·보고서 포함)가 비던 결함. 색인 다운로드는 별도 40s 타임아웃·단일 적재 공유, 연합검색은 최대 3.5s만 기다리고 나머지 결과 먼저. 골든 nrich-db-search는 끝까지 기다리는 nedb_search 목록으로, 연합검색 확인은 nrich-db-in-cross(warn).
- nrich-harvest 워크플로(매주 수 02:41 KST, 0건이면 기존 유지). 원장 심층 보강이 연구DB id를 사용. 골든 nrich-db-search·nrich-db-detail·nrich-db-portrait. Python 패리티.

## v2.14.0 — 국외 소재 교차확인·속도·안내 정리 (2026-11-23)
- 교차확인: cross_search가 국외소재문화유산재단(okchf)·국립문화유산연구원(nrich)의 '명칭(괄호·한자·기호 제거)+소장처(별칭 대영박물관=영국박물관 등)' 동일 기록을 한 건으로 묶음 — 출처 둘 다 표기(복수 출처=교차확인), sameAs=다른 DB URL, 채널 요약에 '국외 교차확인 n건'. 같은 기관 안 중복·보고서는 묶지 않음. Node·Python 단위 실측 동일.
- 계층구조도에 '국외 소장처 교차 보기'(국가 › 소장처별 재단·연구원 수록 수, 두 기관 모두=◎) + overseas_holders.csv.
- 속도·예의: okchf 통합검색·보고서 검색, nrich 국외문화유산 목록·발간자료 API 응답 6시간 캐시(실측 nrich 10.9s — 반복 질의 즉시).
- 안내 정리: 결과 끝 '심층 판독 이어가기'의 koreanwar_item(archRfcd) → ref_code, [okchf]·[nrich] 추가(Node·Python). 골든 deep-hint-footer.

## v2.13.0 — 국립문화유산연구원 국가유산 지식이음 합류 (2026-11-23)
- 새 수집처 nrich: cross_search(sources=nrich|all) — 국외문화유산 DB(12,569건 — 명칭·시대·소장처·국가, 계층 국외문화유산 › 국가 › 소장처) + 발간자료 공식 Open API(무키 — 보고서명·발행년도·연구분야·형태·초록·목차·공공누리 유형·표지, 계층 발간자료 › 연구분야).
- 심층 판독 nedb_search(mode='nrich'): 'ov:번호'·국외문화유산 상세 URL → 소장처(영문명·코드)·시대·수량·한글/한자/원어 명칭·규격·재질·저작권자·이용범위·이미지 / 'rep:번호'·보고서 URL → 서지·초록·목차·본문 지문·표지 / '보고서:키워드' → 보고서 목록. 국외소재문화유산 조사 현황(1992~, nrich.go.kr menuIdx=336) 안내. okchf와 교차확인 권장.
- 원장: 심층 보강(DEEP)·계층구조도 기관명. 썸네일 게재 규칙 보강 — 변경금지(공공누리 3·4유형·CC ND)는 카드 자르기·축소가 원형 변경이므로 링크만.
- 골든 nrich-collect·nrich-overseas-detail·nrich-report-detail. Python 패리티(저장 응답으로 목록·상세·API 판독 실측).
- ⚠ nedb_search mode enum에 nrich 추가 — PlayMCP 콘솔 '정보 불러오기' 재실행 필요.

## v2.12.0 — 재단 조사보고서·원장 계층구조도 (2026-11-23)
- 국외소재문화유산재단 발간자료(조사보고서 56종) 합류: cross_search(okchf)가 보고서 게시판(제목+목차)을 함께 검색해 '[조사보고서]'(계층 발간자료 › 조사보고서)로 묶음. nedb_search(mode='okchf', query='보고서:키워드')=보고서 목록, 보고서 URL·'pub:N'=서지(발간연도·저자·출판사)·목차 전문(논고·필자·쪽수)·목차 지문. 제목의 보이지 않는 문자(U+200B) 제거. 골든 okchf-reports·okchf-report-toc. Python 패리티.
- 발견 누적 원장 계층구조도: docs/data/tree.html(기관 › 계열 › … › 기록 접이식 트리, 단계별 건수, 계열 미상 붉은색, 노드마다 'KV로 보기')·tree.json·hierarchy.json(IIIF 중첩 컬렉션)·h/<기관>.json. 실측(사본): 200건 · 기관 28곳 · 1단계 75 · 2단계 110 · 3단계 12 · 6단계 3 · 계열 미상 20.

## v2.11.0 — 국외소재문화유산재단 합류 (2026-11-23)
- 새 수집처 okchf(국외소재문화유산재단 대국민 아카이브): cross_search(sources=okchf|all) — 통합검색으로 국외문화유산(6천여 건)·사진아카이브(1,800여 건) 수집, 계층 = 국외소재문화유산재단 › 유형 › 소장국가 › 소장처, 썸네일(media).
- 심층 판독 nedb_search(mode='okchf'): 상세 URL 또는 'relic:ID'·'relic_gls:ID' → 소장국가·소장처·소장처 관리번호·시대·재질·크기·수량·소장경위·출판정보·조사기관·소장처 홈페이지·설명 전문·본문 지문(sha256-16)·이미지 목록·원문 뷰어. 키워드는 목록(전체 건수). 발간 보고서 게시판 안내.
- 접근·권리 표시: robots.txt 전체 Disallow(발굴 우선 원칙 — 표시 대상), 정직 UA·요청 최소·상세 24h 캐시. 소장기관과 공개 협의된 정보 — 이미지·설명 게재는 이용조건 확인 후(허가 전 링크만).
- 연결: INST·PART_OF·DEEP_READ·QUICK_PROFILES·health 골든 질의(불화)·원장 심층 보강(DEEP)·골든 okchf-collect·okchf-detail. Python 패리티(저장 HTML로 목록·상세 판독 실측).
- v2.11.1: 상세 제목의 빈 한자명 칸 '· ·' 정리, 설명 끝 화면 버튼 글자 '더보기' 제거, 프로파일 이름표 중복 정리(프로덕션 실측). 골든 okchf-photo-detail.
- ⚠ nedb_search mode enum에 okchf 추가 — PlayMCP 콘솔 '정보 불러오기' 재실행 필요.

## v2.10.0 — 원장 심층 판독 보강: 판결문·공적조서·신문·UN·6·25아카이브·서울기록원 (2026-11-23)
- 매니페스트 없는 출처(i815·indy·gonghun·jacar·oldnews·un·jsg·ktv·koreanwar·seoul)는 원장 병합 때 우리 서버의 심층 판독 도구(nedb_search 모드·koreanwar_item·seoul_archives_search)를 그대로 호출 → 주요 내용(사건개요·공적개요·기사 본문·주제어)·메타정보(죄명·주문·생몰·발행일·생산처·이용조건 등)·본문 지문(sha256-16)·원문 뷰어. 파서 중복 없음(서버 한 곳, 골든 검사). 호출문 deep_call 보존(재현성). X-KA-Probe: ledger로 적재 제외.
- 실측(사본): 9개 출처 40건 전부 보강 성공.
- 결함 수정: 심층 판독 안내(DEEP_READ)의 6·25아카이브 호출문이 존재하지 않는 인자 archRfcd를 안내 → ref_code(Node·Python). 골든 deep-read-koreanwar-arg.

## v2.9.0 — 국가기록원 기록 보강·계층 구축 (2026-11-23)
- 원장 병합 때 매니페스트가 없는 국가기록원 기록은 공개 상세 페이지를 1회 판독(정직 UA·하루 상한 공유) → 메타정보(상위 철·생산기관·관리번호·생산연도·문서유형·기록물형태·매체유형·보존기간·공개구분·서고정보·페이지·발간번호·서비스권자·기록물계열)·주요 내용(기술 메타데이터 요약)·권리 안내.
- 계층 구축: 기록물계열·상위 철이 있으면 partOf = '국가기록원 › 기록물계열 › 상위 철'(원래 값은 partOf_src 보존). 간행물처럼 철=건이면 계층으로 쓰지 않음. 실측 40건 중 35건 보강·8건 실제 상위 철 계층.
- 보강 실패 재시도 7일 → 다음 날. 기록 카드 자리 문구 '원본 이미지 없음(기록 카드)'.

## v2.8.0 — 원장에 주요 내용·썸네일·메타정보 / 국가기록원 빈 페이지 링크 수정 (2026-11-23)
- 결함 수정: 국가기록원 상세 링크가 API 원문의 &amp;를 그대로 담아 클릭 시 빈 페이지(실측 40건 전부) → &amp; 해제·https 정규화(Node archLink·Python _arch_link — 연합 수집·archives_search 목록 모두). 원장은 병합 때 소급 정규화(clean_url), 제목·계열의 HTML 엔티티도 해제. 골든 archives-partof에 must_not.
- 원장 보강: 병합 때 기관 IIIF·우리 브리지 매니페스트를 하루 상한(기본 80)·순차 판독 → summary(주요 내용)·meta(메타정보 8항목)·rights·thumb. CSV·popular.csv·JSON-LD(rico:scopeAndContent)에 반영. 실측: 매니페스트 있는 기록 38건 보강, 썸네일 26건·요약 21건.
- 원장 페이지: 표 → 모바일 카드(썸네일·출처·연대·식별자·계열 칩·주요 내용·메타정보 펼치기·활용 정보·원 기관/KV/IIIF 링크).
- 게재윤리: 썸네일은 재이용 가능 표시(PD·CC·NoC·공공누리·저작권 만료)·NARA·우리 갤러리·우리 카드만, 포로·사망자·묘지·수형자 관련은 링크만.
- 링크 점검(원장 123건, 순차·정직 UA): 대부분 200. 응답 없음(규장각·6·25아카이브·독립기념관 일부)·봇 확인(Europeana 403·TNA/UN 202)은 서버 환경 접근 문제로 표시만(우회 안 함).

## v2.7.0 — 원장 활용 집계: 여러 번 발견된 기록은 활용 컬럼으로 (2026-11-23)
- 중복 처리 시 새 줄 대신 활용 컬럼 갱신: seen·seen_7d·seen_30d·days_total(발견된 날 수)·days(날짜별 90일 이력)·formats(활용 형식 text/csv/iiif/manifest/karda)·max_cross(교차확인 기관 수)·trend(신규/↑/→/↓)·score·rank.
- 점수 = 최근 30일×2 + 전체 발견 + 발견 일수×3 + 교차확인 가중 — 반짝 검색보다 꾸준히 활용되는 기록이 위로.
- 산출 추가: popular.csv(자주 활용 TOP 200)·usage.json(일별 검색 묶음·발견·신규, 형식별 누계 — 400일 보관). index.html에 TOP 30·일별 활용 표. discovered.csv에 활용 컬럼.
- 서버: 적재 묶음에 출력 형식(f) 기록. 자동 검사(golden.py·health.yml)는 X-KA-Probe 헤더 → 적재 제외(활용 집계 오염 방지, AsyncLocalStorage 요청 맥락).
- sources='ledger': 활용 순위순, 제목 앞에 [출처 · 발견 n회 · 7일 m · k일 · 첫 날짜 · 활용 r위]. Python 패리티.

## v2.6.0 — 누적 원장을 다시 검색 수집처로 (2026-11-23)
- cross_search(sources='ledger'): 사용자들이 이미 발굴한 기록(docs/data/discovered.jsonl, 1h 캐시)을 검색 — 원 출처·계열·발견 횟수·처음 발견일 표시, 많이 발견된 순. 'all'에는 넣지 않음(원 기관 결과와 중복·교차확인 오인 방지). 원장에서 다시 찾은 기록은 재적재하지 않음.
- v2.6.1: 발견 횟수·처음 발견일을 제목 앞 대괄호로 — 긴 제목에서 잘리지 않게(실측 결함).
- source_profile 간이 프로파일 ledger. Python 패리티, 골든 ledger-source.

## v2.5.0 — 발견 누적 원장: 사용자가 발굴한 기록이 유실되지 않게 매일 무료 누적 (2026-11-23)
- 서버(lib/ledger.js): cross_search가 끝나면 발견 기록(출처·제목·연대·식별자·URL·계열·매체·sameAs)만 Upstash Redis 날짜 함 ka:in:YYYY-MM-DD에 적재(3일 보관). 검색어·사용자 정보는 저장하지 않음. 미설정·한도 초과면 적재만 생략(검색 영향 없음). 응답에 누적 안내 한 줄.
- 공개 읽기 /api/ledger/{YYYY-MM-DD}?start=&n= — 쓰기·삭제 경로 없음(GitHub Secrets 불필요).
- ledger 워크플로(매일 00:17 KST, scripts/ledger_merge.py): 중복 제거·병합 → docs/data/ discovered.jsonl·csv(엑셀 BOM)·jsonld(RiC-O·PROV 첫 발견)·collection.json(IIIF 최근 300건 → KV 연속 열람)·stats.json·index.html. 기록마다 처음/마지막 발견·발견 횟수. git 커밋 이력 = 발견의 증거.
- source_profile('health') 설정 상태에 LEDGER_REDIS. 골든 ledger-kept. Python 플러그인(로컬)은 서버 저장소가 없어 적재하지 않음(원격 커넥터 사용 시 누적).

## v2.4.0 — 검색 결과 CSV 파일 내려받기 (2026-11-22)
- cross_search(format='csv') 응답 끝에 📥 내려받기 링크: https://korea-archive-mcp.vercel.app/export/csv/<token>.csv — 토큰=CSV 본문 raw deflate+base64url(서버 저장 없음, 링크가 곧 파일). 엑셀 한글 깨짐 방지 BOM, 파일명 korea-archive_<질의>_<날짜>.csv. 웹·모바일에서도 파일로 저장 가능(제1원칙).
- 응답 24KB·URL 12,000자를 넘으면 링크 생략 안내. Python 패리티(토큰 상호 해독 실측), 골든 csv-download.
- v2.3.1: 한국사DB 계열 접두 중복(한국사DB › 한국사DB) 제거.

## v2.3.0 — 계열 미상 보강 (2026-11-22)
- 국가기록원(archives): 생산기관이 없는 기록은 링크 유형으로 계열 부여 — '국가기록원 › 기록건 | 기록물철 | 기록정보콘텐츠' (실측: 60건 중 10건이 계열 미상이었음).
- 한국사DB(nedb) 실시간 수집: 자료군(DB명)을 계열로 — '한국사DB › …' (실측: 4건 전부 계열 미상이었음).
- 독립기념관(i815) 집계 신호 줄에도 카테고리 계열.
- CSV partOf·KARDA·manifest·기록 봉투 계층('기관 › 계열 › 기록')에 반영 — 기록 봉투의 '(계열 미상)' 구축 표시가 줄어든다. Python 패리티, 골든 케이스 archives-partof·nedb-partof.

## v2.2.0 — 분류 계층·결과 계층 (2026-11-22)
- 규장각(kyudb): 사부분류(史部 › 政法類 › 度支 › 賦稅 …)를 계열(series)로 — 조선 기록이 '규장각도서(奎) › 史部 › 政法類 …' 분류 계층을 갖는다(CSV partOf·KARDA·manifest·기록 봉투 계층에 반영).
- cross_search format='iiif': 결과를 '기관 › 계열' 하위 컬렉션(내장 inline)으로 묶어 계층 부여(계열 2개 이상일 때) — KV 링크 하나로 계열 머리말과 함께 연속 열람.
- KV: 링크에 내장된 하위 컬렉션(inline)도 펼침. Python 패리티.

## v2.1.0 — TNA 실제 계층 IIIF · 하위 기록 펼치기 (2026-11-22)
- /iiif/tna/{C-id}/manifest.json(lib/tna_iiif.js): Discovery parentId를 따라 실제 계보(부서 › 분과 › 시리즈 › 피스) 복원 → metadata·partOf, 참조번호·기간·소장·법적 지위·공개 상태·이전 참조·기술 지문·판독 시각, 기록 카드 캔버스(디지털 사본은 rendering 안내).
- /iiif/tna/{C-id}/collection.json: 하위 기록 — 하위 계층은 컬렉션, 말단은 기록 봉투(토큰에 제목·참조·기간·계보 봉인 → 추가 요청 없이 열림). 부모 캐시로 컬렉션 1회 = TNA 2~8요청.
- 도구: tna_search 결과 끝에 계층·IIIF 주소, cross_search format='iiif'·'manifest'가 TNA를 브리지로(기록 봉투 대신 실제 계층) — 패리티.
- KV: 하위 컬렉션 자동 펼치기 상한 30(기관 서버 예의) — 나머지는 폴더로 남겨 누를 때 연다.

## v2.0.0 — 기록 봉투 IIIF: IIIF가 없는 모든 기록을 IIIF로 구축 (2026-11-22)
- /iiif/rec/{token}/manifest.json·card.svg·record.jsonld(lib/rec_iiif.js) — 토큰=발견한 기록의 봉인된 기술(출처·식별자·연대·계열·원 기관 URL·원본 매체·발견 질의·발견 시각), raw deflate+base64url, 서버 저장 없음·불변 캐시.
  계층 구축('기관 › 계열 › 기록' — 원 기관 계층이 없으면 구축 표시), 증거성(발견 경로·시각·봉투 지문 sha256-16), 원본 이미지가 있으면 그 이미지·없으면 기록 카드(실제 기술 메타데이터만), RiC-O+PROV(발견 행위=prov:Activity).
- cross_search format='iiif': 'IIIF 없음'이 사라짐 — 나머지 기록 전부 기록 봉투로. 검색 결과 전체를 KV 한 링크로(kv.html#c=<압축 컬렉션>). format='manifest': 모든 기록에 iiif 필드. Python 패리티(토큰 상호 해독 실측).
- KV: #c= 압축 컬렉션 열기(DecompressionStream), 주소 갱신 시 해시 보존.

## v1.99.0 — IIIF 브리지 2: 국가유산·역사박물관·AWM·위키미디어 (2026-11-22)
- 공개 엔드포인트 /iiif/{heritage|much|awm|commons}/{id}/manifest.json(lib/ka_iiif.js · app/iiif/[src]/[...p]) — 기관 표시 권리 문구 원문·판독 시각·설명 지문·원 기관 homepage·navDate, 이미지 크기 판독(Range) 후 캔버스.
  heritage=종목·지정번호·시대·소유·소재·해설+이미지 목록 API · much=명칭(꺾쇠 원문 보존)·국적/시대·분류·재질·작가·크기·공공누리 유형 · awm=수장번호·생산일·장소·PD 표시(rights PDM) · commons=라이선스 URL→rights·작가·원본 rendering.
- 요청은 정직한 식별자(KoreaArchiveMCP UA)로만 — 브라우저 위장 금지 원칙(CLAUDE.md) 적용.
- 도구: nedb_search heritage·much 상세에 IIIF·KV 주소, cross_search format='iiif'·'manifest'(iiif 필드)에 브리지 합류 — 패리티. 갤러리 캔버스 58장에 원 기관 브리지 seeAlso.

## v1.98.0 — 맥락·증거성·데이터화·다매체: NARA→IIIF 브리지 + 갤러리 계층 (2026-11-22)
- NARA→IIIF 브리지(공개 엔드포인트): /iiif/nara/{NAID}/manifest.json — 계보(ancestors) metadata + partOf(상위 컬렉션), 판독 시각·범위·내용 기술 sha256-16·이용/접근 제한 원문·소장단위·rights(NoC-US/UND), navDate, 표시 이미지=캔버스(Range 128KB로 크기 판독)·TIFF/PDF/영상=rendering. /collection.json=시리즈·파일단위 하위 기록(계보 대조 확인분만) · /record.jsonld=RiC-O. IIIF 검증기 okay(매니페스트 2·컬렉션 1).
- nara_search(naid, output='iiif') · cross_search format='iiif'/'manifest'에 NARA 브리지·기관 IIIF 주소(iiif 필드) — 패리티.
- 갤러리 IIIF: hierarchy.json(최상위 › 부 16 › 시리즈 129 › 이미지 800) · 매니페스트 partOf · 캔버스 seeAlso(출처 대장)·sha256 고정성·navDate·권리 근거·NARA 원 계보(브리지 RiC-O에서 81건). 데이터 내보내기 records.csv·records.jsonld(RiC-O·PROV·owl:sameAs).
- KV: 중첩 컬렉션(계층) 펼쳐 연속 보기, 기본값=hierarchy.json, 목록에 부 머리말. NARA 시리즈 컬렉션도 연속 열람(실측 100기록 117장).

## v1.97.3 — KV 전체 연속 보기 · 이름 통일 (2026-11-22)
- KV (Korea Archive Viewer): 컬렉션을 열면 모든 기록의 장 목록을 미리 받아(동시 6) 한 줄로 이음 — ‹ ›·← →·자동 넘김이 기록(챕터) 경계를 넘어 다음·이전 기록으로 계속, 아래 썸네일 띠 = 전체(기록 경계 번호), '전체 n / 800' 표시, 마지막 장에서만 멈춤. 이전엔 한 기록 안에서만 넘어감.
- 이름 통일: 'KA 뷰어' 표기 제거 → KV (Korea Archive Viewer). 안내(kind='iiif')·format='iiif' 안내 갱신(패리티).

## v1.97.2 — 자체 IIIF 뷰어 KV(KA 뷰어, Korea Archive Viewer) (2026-11-22)
- GitHub Pages kv.html: 어떤 기관의 IIIF든(Presentation 2·3 매니페스트·컬렉션·중첩 컬렉션) 여는 자체 뷰어 — IIIF Image API 딥줌(서비스 없으면 정지 이미지), 컬렉션 목록·거르기, 메타데이터·권리·출처·원 기관 링크 패널, ⧉ 두 창 나란히 비교(Mirador식), 자동 넘김(컬렉션이면 다음 기록으로 이어짐), 회전·전체 화면·공유 링크(?manifest=&canvas=&compare=&collection=), 드래그&드롭, 모바일.
- IIIF 갤러리: 시리즈·확대 화면에 'KV로 열기', 전체를 KV·Mirador·Universal Viewer로 열기(컬렉션 — 실측 정상).
- report_template(kind='iiif')·cross_search format='iiif' 안내에 KV 주소 추가(웹·모바일 동등성).

## v1.97.1 — 우리 IIIF 갤러리 자동 수집 (2026-11-22)
- cross_search sources='gallery'(31번째 채널): 30곳 탐방·100선 실물 기록 800장(권리 확인·출처 대장 완비)을 연합 검색에 합류 — Pages index.json 6h 캐시, 한·영 검색어, 결과는 딥줌 딥링크(iiif.html#sNNN/k)·이미지 직링크(media).
- format='iiif': 갤러리 결과는 시리즈 매니페스트(iiif/m/sNNN.json)를 컬렉션에 포함. source_profile 간이 프로파일·health 골든 질의('흥남') 추가.
- 갤러리 자동 갱신: 100선 build_series.py가 빌드 끝에 build_iiif.py 자동 실행. CI check-docs가 출처 대장 대비 갤러리 최신성 검사(갱신 누락 시 실패).

## v1.97.0 — 도구에 IIIF 연속 이미지 뷰 (2026-11-22)
- cross_search format='iiif': 결과 중 기관 IIIF가 있는 기록(Internet Archive·Europeana·Gallica·NDL)의 원 매니페스트를 IIIF Presentation 3 Collection으로, 위키미디어 공용 이미지는 imageinfo 1회 조회로 정지 이미지 Manifest로 — IIIF 미제공 기록은 원 기관 링크 목록. 24KB 상한(매니페스트 30·이미지 12).
- report_template(kind='iiif'): 공개 갤러리(iiif.html·collection.json·all.json) 사용법, 기관별 IIIF 주소 규칙(실측), 권리 3단계(1600px·공공누리 제4유형 원본 무변경·링크 전용), Presentation 3 최소 구조·검증기, v2/v3 매니페스트·컬렉션을 한 줄로 이어 넘기는 OpenSeadragon 뷰어 골격(아티팩트용).
- 웹·모바일 동등성: 로컬 build_iiif.py와 같은 결과를 도구 응답만으로 재현.

## v1.96.9 — 전체 기록 IIIF 갤러리 (2026-11-22)
- GitHub Pages iiif.html: 30곳 탐방·100선 실물 기록 이미지 800장(129 시리즈)을 격자·연속 스크롤·딥줌(OpenSeadragon)으로 — 확대 화면에서 기록을 가로질러 이어 넘김, 주소 #s070/3 딥링크.
- IIIF Presentation 3.0: iiif/collection.json + 시리즈별 매니페스트(m/sNNN.json) — Mirador·Universal Viewer 바로 열기. 권리: 재이용 가능분 긴 변 1600px · 공공누리 제4유형 원본 무변경 · 웹 캡처·이용 허가 필요분은 원 기관 링크만.
- report_template(kind=help) 안내에 예제 갤러리·IIIF 갤러리 주소 추가(웹·모바일 동등성).

## v1.96.8 — 원본 찾기 보강 (2026-11-22)
- nlk_search: category 미지정 시 '고문헌' 채널 자동 병행 — 현대 영인·번역본이 상위를 채워 원본 고서(예: 1797 오륜행실도)가 묻히던 문제.
- NDL(cross_search ndl): 디지털화 자료에 dl.ndl.go.jp PID가 응답에 있으면 함께 표시·링크(권리·IIIF 원본 확인의 열쇠 — 재조회로 429를 부르던 단계 축소).
- 장서각 의궤(ARC_…) 상세: '해제내용 … 【정의】' 형식 해제를 판독(이전엔 해제 누락) + 간행년(왕력)·판사항. MF번호 끝 쉼표 정리.

## v1.96.7 — 검색 결과 보완 4종 (2026-11-22)
- 규장각(nedb_search mode=kyujanggak·cross_search kyudb): 奎 번호만 나오던 결과를 행 단위로 판독 — 서명(한자·한글)·편저자·간행년대·사부분류, 해제 검색은 해제 요지까지. Python 수집기가 sections 형태 불일치로 항상 0건이던 결함도 교정.
- KTV 목록: 검색어 강조 <span>에서 제목이 잘리던 결함('역사와 함께한'·'[2040호]') — 제목 전체 + 제작일 + 요지.
- 서울기록원: 목록에 제목이 없는 기록건(사진) 행 — 상세 페이지 제목으로 보강(최대 6건 병렬).
- TNA: 단어 전부 일치·어형 그대로인 Discovery 특성 — 다어절 질의는 표기 변형(Korean↔Korea · prisoners of war↔POW)·일반어 제거 질의를 병행해 합치고 ⟨변형⟩ 표시('Korean War prisoners' 41건 → 'Korea POW' 216건 실측).

## v1.96.6 — 장서각 판독 보강 (2026-11-22)
- nedb_search(mode=jsg): 고문서 상세 URL(`dataId=ANC_…`, `%2B`/`+` 포함)도 상세 판독 — 소장·집성·형태·출판 메타 + 이미지 이용 문의처. 이전엔 0건.
- 해제 본문에 인명마다 끼던 링크 라벨 "한국역대인물" 제거. MF번호 공란일 때 '유형분류'가 MF로 잡히던 결함 교정.
- 장서각 병렬 호출 간헐 403 — 같은 요청을 0.9s·1.8s 늦춰 최대 3회 재시도 후 보고(우회 아님).

## 2026-11-22 v1.96.5 — 100선 Ⅹ부 보고 반영
- JACAR: 일문·한자 입력이 영문 'Korea'로 바뀌어 전후 무관 기록이 나오던 결함 → 한글 없는 입력·한→일 사상은 일본어 검색(/aj/search)으로, 일본어 표제·연대(明治…年)·일본어 메타 링크 반환(실측 '日韓協約' → 「韓国併合ニ関スル閣議決定書・其三」 明治42~43年)
- NDL: 당대+일반 두 질의 합이 소스 타임박스(12s)를 넘어 채널이 '—'로 실패(프로덕션 '金剛山' 실측) → 당대 질의 5s 상한·결과 충분하면 일반 질의 생략
- UN: 문서기호 입력(A/RES/…·S/RES/…)은 기호 필드(191) 검색 + 정확 일치 우선 정렬(Invenio 191은 접두 일치 — 정확 검색 불가 실측, 미검출 시 주제어+연도 재검색 권장)
- 100선 Ⅹ부 061~069 완성(070은 NDL 429로 보류)

## 2026-11-22 v1.96.4 — 100선 Ⅺ·XV부 보고 반영
- source_profile: 상세 프로파일 없는 18곳(jacar·earchive·awm·nlna·dnz·nzarch·commons·un·ndl·i815·gonghun·ktv·oldnews·much·indy·heritage·kyudb·jsg·aks)에 간이 프로파일(검색 경로·상세 판독·권리) — "프로파일 없음" 해소
- 신문아카이브: 띄어쓴 다어절 질의 0건이면 가장 긴 단어로 완화 재검색(실측 '독립신문 창간' 0건)
- nedb_search(mode=commons): 퍼센트 인코딩된 File URL(File%3A…) 허용
- nedb_search(mode=ktv): 사진 상세 URL은 '사진 판독' — 공공누리 유형·원본 이미지 경로 표시(영상 판독에도 유형 표기)
- archives_search: API 정상 0건을 'API 오류'로 표기하던 문제 교정
- judge_rights 인접 채굴 안내를 실제 호출 가능한 형식(nara_search(query='', naid, radius))으로
- 100선 Ⅺ부(071~080)·XV부(111~120) 완성

## 2026-11-22 v1.96.3 — 100선 Ⅷ·Ⅸ·XIV부 보고 반영
- 공공누리 4유형 표시 원칙 강화(제작 킷·30선 생성기): 원본 위에 글·그라데이션·테두리·블러 배경을 얹지 않음 — 이미지 영역과 글 영역 분리, 모음 라벨은 이미지 아래, 사실·CTA 배경은 단색. 30선 24·25·26·28·07·08·11과 100선 해당 시리즈 재렌더
- Gallica 폴백: BnF 카탈로그 'all' 질의가 0건이면 핵심어 2개로 완화(실측 'Corée 1866 expédition'·'Souvenir de Séoul' 0건→복구), 그래도 0건이면 그 사실을 명시
- Europeana: 결과에 원본 이미지 직링크(edmIsShownBy) 추가, Náprstek(esbirky) 부패 링크 → /predmet/{id} 교정
- 국가유산 원본 이미지 링크 https 정규화 · AWM 결과 상한 5→10
- 100선 Ⅷ부(041~050)·Ⅸ부(051~060)·XIV부(101~110) 완성

## 2026-11-22 v1.96.2 — 100선 제작 에이전트 보고 반영(도구 결함 6건)
- 안내 문구 정리: "에이전트 지시: 이 메시지를 그대로 사용자에게 전달하지 마세요…"가 도구 응답 속 숨은 지시로 오인됨 → 중립 안내("다음 단계: 공식 검색 URL을 열어 표로 정리") — 전 채널 공통
- judge_rights·nara_search: naid 문자열 입력 허용(숫자로 변환)
- judge_rights(naid): 첫 객체(작은 GIF 등) 대신 최선 원본(TIFF>JPG/영상>PDF, 큰 파일)·용량 표시
- koreanwar_item: 입수처 NAID가 시리즈·파일 단위면 경고(예: 530707 = 111-SC 시리즈 전체), NARA 링크가 없으면 대조 필요 안내
- 한국사DB POST: 'terminated(UND_ERR_RES_CONTENT_LENGTH_MISMATCH)' 간헐 실측 → 3회·백오프·재시도 비압축 요청
- 스킬 analyze_video.py: 비정방 화소(SAR 10:11·8:9) 보정 — NARA SD 영상 프레임 10% 늘어남 해소(합성 영상 실측 800×587)
- 100선 Ⅶ부(031~040)·Ⅻ부(081~090) 완성

## 2026-11-22 v1.96.1 — 영상 특집 제작에서 나온 결함 2건
- ia_search(identifier=없는 id)가 "Title: undefined"를 내던 문제 → "항목 없음" 명시
- NARA 디지털 사본 유무 명시: nara_search 목록에 "디지털 사본 없음", judge_rights(naid)에 "디지털 사본 없음 — 디지털 객체 미등록(medialz도 HTML만 반환)" — 정전협정 조인 영상(NAID 76586) 등에서 실측
- 100선 탐방 XVI부 "영상으로 읽는 기록"(121~130): NARA 영상 10편 × 장면 해설 카드 2장

## 2026-11-22 v1.96.0 — NDL 검색 관련도: 당대 자료 우선
- '朝鮮総督府' 같은 다빈도 표제어는 8,162건 일치 후 표제 가나순이라 무관 자료(アジアの社会…)가 상위 — 당대 자료(until=1945) 질의를 순차 병행하고, 검색어(신·구자체 정규화: 總→総 등)를 표제에 포함한 것부터 정렬·중복 제거
- 실측: 1927 「安東材の課税案…朝鮮総督府再び提出する」 · 1919-11-03 「陰謀団一網打尽 : 朝鮮総督府発表」(大阪毎日新聞) …
- NDL 동시접속 429 실측 → 두 질의는 순차, 두 번째 실패 시 첫 결과로 진행

## 2026-11-22 v1.95.0 — 국가유산·역사박물관 원본 이미지 직링크
- 30곳 탐방에서 미해결로 남은 두 곳(22 국가유산·26 역사박물관): 결과의 media(원본 이미지)가 비어 있어 원본을 찾을 수 없던 결함
- nedb_search mode=heritage 상세(복합 id·ccbaCpno): 상세 API imageUrl + 이미지 목록 API(SearchImageOpenapi)로 【원본 이미지 n점】(설명 포함) 반환
- nedb_search mode=much 상세(idnbr): 소장품 페이지의 원본 이미지 직링크 반환(UI 이미지 제외)

## 2026-11-22 v1.94.0 — KTV e영상역사관 검색 품질: 최신순 독점 해소
- 30곳 탐방 제작 중 발견: '대한뉴스'·'새마을운동' 검색 상위가 2020년대 대통령 영상으로 채워짐 — 사이트 기본 정렬이 최신순이고 sort 파라미터(GET·POST)는 무효로 실측
- 기록 탭(ehistoryStleSe) 실측: DH 대한뉴스 · MH 문화영화 · DK 미공개 대한뉴스 · BK 정부기록사진집 · PT 국가기록사진 · DT 대통령 기록영상
- 탭별 병렬 조회 → 교차 병합, 대통령 기록영상은 뒤로 · 결과마다 [탭 이름] 표시(cross_search ktv 채널·nedb_search mode=ktv 공통, Node·Python 동일)
- 실측 '새마을운동': [1845호] 새봄맞이(대한뉴스) · 1960년대 우리나라(문화영화) · [1585호](미공개 대한뉴스) · 정부기록 사진집 10 - 농촌 …

## 2026-11-22 v1.93.1 — 배포 실측 교정 2건
- 프로덕션 health에서 nedb·foia 채널 `dclean is not defined` 실측 — v1.93 모듈 범위 코드가 도구 범위 함수를 참조. 모듈 범위 정리 함수로 교정
- Gallica 폴백: BnF 카탈로그를 사진·도판(doctype i) 질의와 병행 → 디지털화된 Gallica 원본(Guerre de Corée·32 phot. de Corée 1880-1896 등)이 상위

## 2026-11-22 v1.93.0 — 30곳 탐방 캐러셀 세트 + 막힌 수집처 교정 + 영상 장면 분석
- 사용자 요청: 모든 수집처가 나오는 30개 시리즈, 원본 이미지로 가득, 설명 이미지, 막힌 곳은 기능을 고쳐 반드시 수집, 시리즈별 인스타 캐러셀+소개글 세트, 영상 장면 해설 이미지
- **Gallica 교정**: gallica.bnf.fr 서버 403 시 BnF 공식 카탈로그 SRU(catalogue.bnf.fr) 폴백 — UNIMARC 표제·연대·수량·Gallica 원문 ark, 디지털화 자료 우선(gallica_search·cross_search 공통)
- **한국사DB 교정**: 개방파일 인덱스 미설정 시 연합검색 nedb 채널이 통합검색을 실시간 조회(0건 고정 해소)
- **정보공개 교정**: 정보공개포털 원문정보 메뉴 점검(2026-11-12~) 실측 감지 → 점검 상태·기간과 정보공개청구·대체 검색 경로 안내, 서울정보소통광장 연결 실패 사유 명시
- **영상 장면 분석(신규)**: `ia_search(identifier)` 영상이면 IA 시각 코드 프레임·mp4·NARA NAID 반환(웹·모바일 경로) · `report_template(kind=video)` 장면 해설 규칙 · 스킬 `analyze_video.py keyscenes`(ffmpeg 장면 전환 → 장면별 최선명 프레임, 리더·암전 제외) — 흥남 필름 2편 실측(전환 89→13장면, 73→10장면)
- **KTV 권리 문구 정정**: "KTV=공공누리" → 페이지 표시 확인(영상 페이지 무표시 다수 — KTV 나누리 이용 신청)
- **캐러셀 세트**: docs/promo/series30v2 — 30개 시리즈 × 4~7장(총 152장) + 시리즈별 소개글, 원본 이미지 150여 장(ledger.json에 권리 근거·보이는 사실), series.html에 세트 연결
- 권리·윤리: 공공누리 4유형 원형 유지, 허가 대상(장서각·규장각·독립기념관 스크랩·역사박물관 원본) 미게재, 개인 주소 흐림, 포로·묘지·수형자 사진 제외, 기관 방화벽·봇 차단·429 우회 안 함
- ⚠ report_template kind에 video 추가 — PlayMCP "정보 불러오기" 필요

## 2026-11-22 v1.92.0 — 예제 시리즈 「30곳 문서고 탐방」: 수집처 30곳 전부를 한 곳씩
- 사용자 요청: "모든 수집처가 다 나오도록 예제를 풍부하게 30개 시리즈로" → 30개 수집처마다 맞춤 질문 1개 + 프로덕션 실제 호출 결과(목록 → 심층 판독 연쇄)로 예제 30선
- 6부 구성: Ⅰ 전쟁의 기록(NARA·협약기관·AWM·Archives NZ·네덜란드·UN) · Ⅱ 개항과 대한제국(TNA·Gallica·Europeana·신문아카이브·한국사DB·Commons) · Ⅲ 독립운동(판결문·공훈록·독립기념관·JACAR·전자사료관·NDL) · Ⅳ 조선의 기록문화(장서각·규장각·고문서자료관·국가유산·국립중앙도서관) · Ⅴ 현대 한국(국가기록원·KTV·역사박물관·서울기록원·정보공개) · Ⅵ 세계의 집계 창구(인터넷 아카이브·DigitalNZ)
- 카드 31장(표지+30, 1080×1080): 권리 실확인 원본 이미지 11장(NARA Unrestricted·AWM PD·1908 신문 지면·공공누리 1유형·Commons PD) + 이미지 없는 19곳은 실제 조회 필드로만 만든 '기록 카드' — AI 이미지 0장, 참고 이미지는 사진 위에 명기, 전 장 육안 검수
- docs/series.html(Pages 30선 페이지 — 질문 복사·원문 링크·카드 PNG) · promo/series30: captions.txt(30개+해시태그) · schedule.md(30일 일정) · sources.txt(호출·원문·권리 대장) · series.json(단일 원천) · gen_cards/gen_page/gen_text.py(재생성)
- 솔직한 현황 명시: Gallica(BnF 403)·정보공개(시간 초과)는 대체 경로 응답 자체를 예제로, 한국사DB는 전용 판독 도구 결과로
- 도구: 병합 결과의 sameAs 표기 교정 — 여러 기관이 묶인 행은 "↔ 원본" 대신 "↔ 함께 묶인 기록"(IA 사본을 원본으로 오표기하던 문제)

## 2026-11-22 v1.91.2 — 인터넷 아카이브 사본 ↔ NARA 원본을 고유번호로 묶기
- 30곳 실측 중 발견: '흥남' 연합검색에 IA `428-npc-171` "EVACUATION OF HUNGNAM KOREA"와 NARA NAID 75393이 따로 나옴 — NARA 원본 디지털 객체가 `…/428-npc-171.mp4`(같은 번호)
- IA 식별자가 NARA 고유번호형(`428-npc-171`·`111-adc-8610`)이면 sameAs `NARA 428-NPC-171`, NARA 결과는 디지털 객체 파일명으로도 색인 → 한 건으로 병합(`[nara+ia]`)
- 기존 `gov.archives.arc.<NAID>` 규칙과 병행 · Node·Python 동일
- 참고: DigitalNZ는 재실측에서 정상 응답 복귀(403은 일시 차단) — v1.91.1 키 경로는 재발 대비로 유지

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
