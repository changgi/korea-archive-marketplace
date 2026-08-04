#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_koreanwar — 6·25전쟁 아카이브센터 (KOREAN WAR ARCHIVES — 정식 명칭, 전쟁기념관재단·협약기관) 자료·이용·활용구조 프로파일."""

PROFILE = {
 "name_ko": "6·25전쟁 아카이브센터",
 "name_en": "KOREAN WAR ARCHIVES",
 "category": "domestic",
 "data": {
  "hierarchy": "6·25전쟁(1950–53) 특화 디지털 아카이브 — 전쟁기념관재단 운영. 3축 탐색 구조: (1)시기별 1950~1953 연도 컬렉션(13,600건+) (2)장소별 국내 도(道)+해외 지역 (3)인물별 군인(35,128)·정부(6,452)·민간인(27,168). 분류체계는 depth1~depth6 6단계 트리(예: 수집 > 미국 > 국립문서기록관리청(NARA) > Record Group 111 > Moving Images… > 하위) — 즉 출처주의 계층을 유지한 채 재수집한 구조. 최소 단위 = 아카이브 자료 건(archRfcd 1건) + 도서자료(bookId). 총 55,206건 규모.",
  "classification": "이중 분류: ① 출처 기반 depth 트리(수집국가→기관→RG/시리즈→하위) — NARA·해외 기관 원 계층을 보존 ② 매체 기반 자료유형(문서·지도·사진·필름·음원·구술·유물·홍보물). 전투정보는 별도 축(/warList.do 전투정보 검색). 상세검색 코드체계(실측 추출): 자료유형 detailClSystCd 13종 — 공문서 00000001·사문서 00000049·명부/도면/지도 00000061·도서/간행물 00000078·이미지/소리 00000100·제복/표지 00000144·훈장/메달 00000202·무기/장비 00000209·탄약 00000311·예술 00000331·홍보/기념 00000350·기타 00000368. 수집구분 depth1 8종 — 수집 00001041·기증 00001042·기타 00001047·구입 00001054·기탁 00001073·제작 00001125·이관 00001179·차입 00001410 (depth2~5는 AJAX 동적). 자료연대 detaildtaage — 03 광복이전(~1945.8.14)·04 광복이후(1945.8.15~49)·05 1950년대·06~13 이후 연대·01 연도미상·02 전체시기. 파일확장자 detailFileExt 16종(jpg·pdf·hwp·tif·mp4·mp3·mov 등).",
  "identifiers": "아카이브 참조코드 archRfcd가 공개 영속 식별자 — 형식 [수집연도]-[국가]-[일련]-[매체]-[구분]-[번호] 예: 2022-US-02-AV-D-00207 (2022 수집·미국·AV=시청각·D·207). 상세 URL /searchDetail.do?archRfcd=<코드> 로 안정 인용 가능(전쟁기념관 본관 아카이브의 세션 기반 URL 약점을 해소). 도서자료는 /searchDetail-book.do?bookId=<n>.",
  "metadata_standard": "OpenAPI 기준 30+ 필드: sj(제목)·engSj(영문제목)·spln(원어명칭)·stmt(설명)·prdcPrsn(생산자)·prdcPlce(생산장소)·prdcBegnDtm/EdDtm(생산일)·prdcNat1/2(생산국)·obtnPlce/Se(입수)·cstdLc(보관위치)·useCnd(이용조건)·kogl(공공누리유형)·cpyrYn(저작권)·olinYn(원문온라인)·depth1Nm~6Nm(분류)·gthrNm(수집처). 한·영 병기 제목 + 원 출처 계층 보존 — 사실상 ISAD(G)형 다계층 기술에 근접(전쟁기념관 본관의 '유물 등록'형 기술보다 아카이브적).",
  "scope": "6·25전쟁 1950–53 집중(전사(前史)·정전 이후 일부 포함). 문서·지도·사진·필름·음원·구술·유물·홍보물 약 55,206건. NARA RG 111(통신대 영상)·RG 342 등 미군 시청각 기록의 한국어 재기술본이 최대 밀도 — 해외 원본을 한글 제목·해설로 검색 가능한 유일급 창구.",
  "digitization": "높음 — 시청각 자료 썸네일+스트리밍, olinYn 필드로 원문 온라인 제공 여부 명시. 검색 결과가 서버측 HTML로 렌더되어(JS 불요) 자동 수집 친화적. 상세페이지 dt/dd 실측 필드: 아카이브 참조코드·생산처/생산자·생산시기·입수처·입수처 링크(NARA 재수집본이면 catalog.archives.gov/id/<NAID> 원본 직결 — 실측: 2022-US-02-AV-D-00207 → NAID 22345)·열람 및 이용조건(예: 전체열람/해당없음). 전투정보 DB(/warList.do)는 현재 개전 초기 '북한군의 남침과 방어작전(1950.6.25~9.14)' 단계 69개 전투 수록(확장 중) — 이후 시기 전투는 미수록(0건 ≠ 부재).",
 },
 "access": {
  "channel": "① 통합검색 GET https://www.koreanwar.or.kr:8443/search.do?keyword=<질의>&viewType=archive&page=<n> — 서버측 렌더 HTML, totalCount+결과카드(제목·archRfcd·생산기관·상위계층) 파싱. viewType=archive가 완전 목록(10건/페이지·페이징 정상, 실측); viewType=all은 미리보기(아카이브 3+도서 2). 상세검색 폼 /search.do?detailYn=Y 필드 중 서버측 GET 반영 실측: 생산시기 연도범위(detailPrdcBegnYYYY/EdYYYY — 철수 778→1950년 401)·수집구분(depth1 코드 — 철수 778→수집 633·기증 104)·pageSize(10/20/50)가 동작; detailArchRfcd·detailKeyword·detailPrdc·detailGthrCdNm·detailClSystCd·detaildtaage·detailUseCnd·detailOtp·detailFileExt는 GET 미반영(JS 세션 전용 — 코드값을 브라우저 상세검색 폼에 입력해 사용). 전투정보 /warList.do(warNm 서버필터는 JS측 — 전체 목록을 받아 로컬 필터해야 함, koreanwar_search(scope=battle)가 자동 처리). ② OpenAPI GET https://www.koreanwar.or.kr:8443/openapi/pbrcList.do?token=<토큰>&page=<n>&pageSize=<≤100> — JSON, 공개 소장자료 전체 목록(키워드 파라미터 없음 → 페이지 순회+클라이언트측 필터). MCP 도구 koreanwar_search가 ①을 기본, 토큰 설정 시 ②를 병행.",
  "auth": "통합검색: 없음(공개 GET). OpenAPI: 토큰(token)+IP 화이트리스트 이중 인증 — Q&A 게시판 'API 문의'로 신청 → 관리자 승인 후 토큰·허용 IP 등록. 서버 환경변수 KOREANWAR_API_TOKEN 설정 시 즉시 활성(승인 전에는 resultCode=FAIL).",
  "query_syntax": "keyword= 단일 파라미터 전문검색(URL 인코딩) + viewType=archive&page= 페이징. 한글 질의 기본 — 미군 시청각 원본도 한글 재기술 제목으로 히트(예: '장진호' → 제1해병사단 철수 기록영상, 86건). 서버측 추가 필터는 생산연도 범위(detailYn=Y&detailPrdcBegnYYYY&detailPrdcEdYYYY)만 유효 — 참조코드·생산처·입수처 필터는 브라우저 상세검색 폼 전용. OpenAPI는 검색 구문 없음(목록+페이징만).",
  "response_format": "통합검색: HTML(result-card 구조 — totalCount, /searchDetail.do?archRfcd= 링크, 생산기관/생산자, 상위계층 breadcrumb). OpenAPI: JSON {resultCode(OK/FAIL/ERROR)·resultMsg·totalCount·page·pageSize·list[30+필드]}.",
  "blocking_notes": "HTTPS 8443 포트(비표준 — URL에 :8443 필수). robots.txt 미제공(404) → 금지 지시 부재; 질의당 1~2회의 정중한 호출 권장, 대량 크롤링은 OpenAPI 이용약관상 제한 명시. OpenAPI는 IP 등록제라 서버 배포 IP가 바뀌면 재등록 필요 — 고정 egress IP 확보가 관건.",
  "rights_access": "OpenAPI 응답의 kogl(공공누리 유형)·useCnd(이용조건)·cpyrYn(저작권 여부) 필드로 건별 권리 명시 — 국내 아카이브 중 권리 메타 최상급. 열람조건 detailUseCnd 코드: 01 전체열람·02 목록열람·03 관내열람. 이용조건 detailOtp 코드(공공누리+국외 구분): 09 자유이용(국내)·01~04 KOGL 제1~4유형(국내)·05 보류·06 해당없음·11 열람전용(국내) / 07 자유이용(국외)·08 제한이용(국외)·10 열람전용(국외) — 국외자료(NARA 재수집본 등)는 별도 3단계 체계. 출처 표기 필수(미표기 시 이용 제한). 단 미군 생산 원본(NARA RG 111 등)의 재수집본은 원본 자체가 US PD(17 U.S.C. §105)이므로 원 출처 규칙 우선 판정.",
 },
 "use": {
  "mismatch_summary": "언어적: 이 아카이브가 곧 해소 장치 — NARA 영문 원제(1st Marine Division, Koto-ri)를 한글 재기술(장진호 지역에서 고토리로 철수하는 제1해병사단)로 검색 가능. 역방향 부정합 주의: 한글로만 질의하면 영문 원제 전용 건 누락 → engSj 필드 대비 영·한 병렬 질의. 분류학적: depth 트리가 NARA RG를 보존하므로 RG 교차맵(keywords_nara RG_MAP)이 그대로 통용 — 상위계층 breadcrumb의 'Record Group N'을 추출해 NARA 원본 역추적. 기술관행적: 수집연도 기반 archRfcd(2022-US-…)는 생산연도가 아님 — 연대 필터는 prdcBegnDtm/상세검색 생산일 범위로.",
  "keyword_ref": "keywords_warmemo(부대·작전·전투 한자표기 50종) + 공통층 G-02(한국전쟁)·G-03(전투/고지)·G-04(작전명)·G-05(부대)·G-06(포로/실종)을 한글 형태로 투입. '장진호·백마고지·흥남철수·인천상륙' 등 전투/지명 한글 키워드가 최고 재현율.",
  "crossmap_ref": "keywords_nara.py RG_MAP 직결 — 상위계층에 RG 번호가 명시되므로 사상 불요: RG 111-SC(통신대 영상·사진) ↔ 시청각 AV 건, RG 342(공군) ↔ 항공 필름, RG 242(노획문서) ↔ 노획 자료. 검색 결과의 breadcrumb에서 RG를 읽어 nara_search(record_group=N)로 원본 확인.",
  "adjacent_mining": "archRfcd 말미 일련번호 ±N 순회로 동일 시리즈 인접 건 채굴 가능(예: 2022-US-02-AV-D-00207 → 00200~00215 — 실측: 00207·00215·00127이 모두 장진호 관련). 상세페이지 depth 링크로 동일 RG/시리즈 전체 열람. OpenAPI 목록은 등록順이라 페이지 순회 = 수집 컬렉션 단위 브라우징.",
  "cross_archive_combos": [
   "6·25아카이브 AV 건(한글 재기술) ↔ NARA RG 111/342 원본(catalog.archives.gov) — 한글로 발굴 후 영문 원제·NAID 확정, 원본 고해상 입수",
   "6·25아카이브 전투정보(/warList.do) ↔ TNA WO 281/308(영연방군 전투일지) ↔ 국방부 군사편찬연구소 — 전투 서사 3자 교차",
   "6·25아카이브 노획 자료 ↔ NARA RG 242 ↔ 국사편찬위 한국사DB 노획문서 — 노획 경위·원소장처 확정",
   "6·25아카이브 구술·민간인 기록 ↔ 전쟁기념관 구술자료 ↔ 국사편찬위 구술사료 — 증언 교차 검증",
   "6·25아카이브 사진 ↔ 국가기록원 정부기록사진집 ↔ NARA RG 111-SC — 촬영일·촬영자 확정",
  ],
  "rights_rule": "초판(first-pass): OpenAPI kogl 필드가 있으면 공공누리 유형 그대로 적용(제1유형=B급 상당). kogl 부재·cpyrYn=Y면 C(허락 필요)로 보수 판정. 미군 생산 원본의 재수집본(depth에 NARA 명시)은 원본 US PD 규칙 우선 — 단 한글 재기술문(해설 텍스트)은 아카이브센터 저작물이므로 별도. 출처 표기는 전 등급 필수.",
 },
 "verify": {
  "accurate": True,
  "notes": [],
  "robots": "robots.txt 미제공(HTTP 404, 2026-07-30 실측) — /search.do 경로에 대한 금지 지시 없음. 검색 결과는 서버측 렌더 HTML로 파싱 확인(장진호 → 총 86건, 흥남철수 → 78건, result-card 구조). OpenAPI 파라미터 표(token·page·pageSize)와 30+ 응답 필드는 /link/openapi.do 공식 문서에서 실측. 협약(MOU) 기관 — 요청 시 프로그램 식별 UA 사용·정중한 호출 준수.",
 },
}
