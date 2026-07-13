#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_warmemo — 전쟁기념관 (War Memorial of Korea) 자료·이용·활용구조 프로파일."""
import json
PROFILE = json.loads(r'''
{
 "name_ko": "전쟁기념관",
 "name_en": "War Memorial of Korea",
 "category": "domestic",
 "data": {
  "hierarchy": "박물관형 3~4단계 카테고리 트리(계층=아카이브 fonds/series가 아니라 전시·소장 도메인 분기). 라이브 breadcrumb로 확정된 최상위 4개 도메인 → 중분류 → 소분류 → 유물 건(item): (1)소장자료 > 유물일반·사진/필름·영상/음원·구술자료·인물 (2)전시 > 상설전시(전쟁역사실·6·25전쟁실·국군발전실·해외파병실·기증실 등)·특별전시 (3)연구·교육 > 교육자료 (4)기념관역사 > 행사이야기(추모/개막/기타)·타임라인. 최소 검색·기술 단위 = 유물 등록 건(1건=1 소장품), 철·계열(series) 개념 없음.",
  "classification": "박물관형 소장품(유물) 등록·매체별 자료유형 분류 — 유물일반·사진/필름·영상/음원·구술·인물의 매체(자료유형) 축 + 소장품 등록번호. 근거 법령은 「박물관 및 미술관 진흥법」 소장품 관리 체계. ISAD(G) fonds/series나 NARA RG 같은 출처주의 아카이브 분류가 아님(관건적 부정합 지점). 전시축(상설/특별 전시실)은 별도의 큐레이션 분류로 소장자료 분류와 교차한다.",
  "identifiers": "소장품 관리번호(유물 등록번호)가 내부 식별자. NARA NAID·TNA reference code·ARK 같은 공개 전역 영속식별자(PID)는 통합검색 결과에 노출되지 않음 — 접근 키는 '카테고리 경로 + 키워드'. 상세페이지(item view)는 세션/파라미터 기반이라 안정 인용 URL 확보가 약함.",
  "metadata_standard": "박물관 유물기술(명칭·시대/연대·재질·크기·수량·출처/기증) 중심. 정식 아카이브 기술규칙(ISAD(G)·DACS) 이나 MARC 미적용; 사실상 Dublin Core류 서지필드에 가까움. 권리표시는 공공누리(KOGL) 유형으로 관리. 즉 '기록 기술'이 아니라 '유물 등록' 관행 — 사건·부대 맥락 메타가 얕은 구조.",
  "scope": "근현대 한국 군사사. 1860–1960 창(구한말 병인·신미양요, 의병·독립운동, 국군창설, 6·25전쟁 1950–53, 베트남 파병 전사)이 모두 포함되며 6·25전쟁이 최대 밀도. 규모: 단일어 '인천상륙작전' 1건 검색이 소장자료+전시+기념관역사 전체에서 400건+ 히트(유물일반 115·사진/필름 275 등) — 전체 소장 유물은 수만 건대.",
  "digitization": "부분 디지털화. 유물일반·사진/필름은 썸네일 이미지 surrogate, 영상/음원·구술은 스트리밍 형태로 상세페이지 제공. 원문서(문서 원본) 전량 다운로드 제공은 아님 — 열람·연구용 저해상 위주. 통합검색은 카테고리별 건수(총 N건)까지 서버측 노출, 건별 목록·이미지는 JS 렌더 상세로 진입."
 },
 "access": {
  "channel": "통합검색 엔드포인트: http://archives.warmemo.or.kr/intgsrch/intgsrchArchv.do?MID=UM00045&keyword=<질의> (HTTP 전용 — HTTPS 실패). 서버측에서 카테고리 breadcrumb 'N건' HTML을 스크레이프해 유물일반·사진/필름·영상/음원·구술·전시·인물 등 카테고리별 히트 수를 반환. MCP 도구 warmemo_search가 이 경로를 직접 호출.",
  "auth": "none — 인증키·API키 불필요. 공개 통합검색 GET.",
  "query_syntax": "단일 keyword= 파라미터(URL 인코딩)로 전 카테고리 통합검색. 필드검색·불리언·정확구·기간필터 같은 고급 연산자는 이 엔드포인트에 노출 없음(카테고리 필터는 결과 페이지 내 분기). 한글 질의; 유물명·부대명은 한자 원표기가 색인 정확도를 높임(예: 白馬高地·斷腸의能線).",
  "response_format": "HTML(JSON 아님). 서버 파싱 대상은 total-breadcrumb 카테고리 라벨 + '총 [\\d,]+건' 패턴; 도구는 상위 ~20개 카테고리 건수를 텍스트로 반환. 건별 목록·유물 이미지는 별도 JS 렌더 상세로 페이징.",
  "blocking_notes": "HTTP 전용(HTTPS 요청은 실패) — 반드시 http://로 호출. 통합검색 건수는 서버측 스크레이프로 취득 가능하나, 건별 목록·상세는 JavaScript 렌더라 일반 HTTP로는 빈 목록 → 에이전트 브라우저(cheliped) 2단계(검색창 fill→목록 scrape) 필요. keyless 공개 API 없음. 지오블록 없음(국내 접속 원활); 공개 robots API 미확인 → 질의당 통합검색 1회의 정중한 호출 권장(rate 남용 금지).",
  "rights_access": "전쟁기념관 이용약관 + 공공누리(KOGL) 유형 표시 확인 후 이용. 유물 이미지 복제·상업이용은 기관 별도 협의 대상, 실물 유물 열람은 제한. 노획문서·정부 생산 원본이 재소장된 경우 원 출처(NARA/국가기록원) 권리 규칙이 우선."
 },
 "use": {
  "mismatch_summary": "언어적: 유물명·부대·작전·전투가 한자/한글 혼용 — NARA/TNA의 영문 표제(Inchon landing, White Horse)로는 히트 0, 반드시 한글+한자 원표기(인천상륙작전/仁川上陸作戰, 백마고지/白馬高地)로 질의해야 함(부대·작전·전투 한자 50종 검증셋이 이 간극 메움). 분류학적: 매체 기반 박물관 분류(유물일반/사진/구술/영상)가 출처주의 아카이브 RG/series와 불일치 — 한 사건이 소장자료·전시·기념관역사 여러 카테고리로 흩어져(라이브 예: 16개 카테고리 동시 히트) breadcrumb 전 카테고리 합산이 필수. 기술관행적: '유물 등록' 기술이 명칭·재질 중심이라 사건·부대·작전 맥락 메타가 얕고, 전투/작전 맥락은 전시실 해설·교육자료에 분산 → 검색 재현율이 표제어에 크게 의존.",
  "keyword_ref": "keywords_warmemo (신설 국내 셋 — 부대·작전·전투 한자표기 50종 검증). 공통층 G-02(한국전쟁 일반)·G-03(전투/고지)·G-04(작전명)·G-05(부대)·G-06(포로/실종)의 개념을 한글·한자 형태로 사상해 사용. 인물은 G-11의 한국어 표기 활용.",
  "crossmap_ref": "keywords_nara.py RG_MAP 참조 — 특히 RG 111(육군 통신대 사진, RG_MAP 확장분)·RG 342(공군 사령부, 사진/필름)·RG 242(노획 외국문서). 전쟁기념관 매체 카테고리 → NARA RG 사상: 사진/필름 ↔ RG 111-SC·RG 342-FH, 노획 유물/문서(인공기·삐라·문서) ↔ RG 242, 부대/작전 문서 ↔ RG 338(KMAG)·RG 407.",
  "adjacent_mining": "제한적 적용. TNA류 finding-aid 트리(계열 인접 확장)는 없고 통합검색은 건수만 반환. 대안: (1)단일 키워드의 breadcrumb 카테고리 분포 자체를 인접 주제 신호로 사용(전시실 히트가 곧 관련 주제 클러스터) (2)상세 유물페이지의 관련유물·동일 기증컬렉션 링크는 에이전트 브라우저로 열람해 인접 채굴. RG 계열 인용 역추적은 교차 아카이브(NARA/국가기록원) 쪽에서 수행.",
  "cross_archive_combos": [
   "전쟁기념관 소장자료>사진/필름 ↔ NARA RG 111-SC / RG 342-FH ↔ 한국사DB HUSAFIK — 6·25 전투·부대 사진 원판 대조·촬영일자 확정",
   "전쟁기념관 노획 유물·문서(인공기·삐라·북한 문서) ↔ NARA RG 242 노획 외국문서 ↔ 국가기록원 노획문서 컬렉션 — 3자 대조로 노획 경위·원소장처 확정",
   "전쟁기념관 전투/고지·부대(백마고지·단장의능선·Gloster Hill) ↔ TNA WO 281/WO 308(영연방군) ↔ 국방부 군사편찬연구소 전사 — 참전국 교차 전투 서사 검증",
   "전쟁기념관 구술자료(참전용사) ↔ 국사편찬위 구술사료 ↔ NARA RG 319 G-2 정보보고 — 증언과 당대 정보문서 교차",
   "전쟁기념관 인물(장교·독립운동가) ↔ 한국사DB 인물·독립운동 ↔ NARA RG 242/319 — 구한말~해방기 인물 신원·행적 확인"
  ],
  "rights_rule": "초판(first-pass): 전쟁기념관 소장 유물/사진 이미지는 기관 이용약관 + 공공누리(KOGL) 유형 표시를 먼저 확인 — 표시 없으면 '권리 미상 → 개별 문의'로 보수 판정. 단, 노획문서·정부 생산 원본이 재소장된 항목은 원 출처 규칙 우선(NARA 등 미 연방기록 원본 = Public Domain, 국가기록원 정부문서 = 공공누리 유형 확인). 즉 도메인 사진/유물은 기관 문의, 사건 '원본'은 원 소장처 권리로 승계 판정."
 },
 "verify": {
  "accurate": true,
  "notes": [],
  "robots": "scrape_plan on the base search URL returned \"robots 미확인 (HTTP 404)\" — robots.txt is not served at the site root, so no allow/disallow directive governs the /intgsrch/ search path. This matches the profile's own \"공개 robots API 미확인\" claim. Recommendation: polite single call per query; JS-rendered item lists require the agent browser (cheliped) 2-step."
 }
}
''')
