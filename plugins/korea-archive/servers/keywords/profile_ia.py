#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_ia — 인터넷 아카이브 (Internet Archive (archive.org)) 자료·이용·활용구조 프로파일."""
import json
PROFILE = json.loads(r'''
{
 "name_ko": "인터넷 아카이브",
 "name_en": "Internet Archive (archive.org)",
 "category": "overseas",
 "data": {
  "hierarchy": "3계층 논리 모델: collection(컬렉션) → item(개별 자료, 고유 identifier) → files(item 내부 파일들: 원본 + 파생본). 전통 아카이브의 fonds/series 계층이 아니라 플랫 아이템 풀 위에 다대다 collection 태그가 얹히는 구조 — 한 item이 복수 collection에 소속될 수 있고, collection도 하위 collection을 가질 수 있음. 기술 단위는 item 하나(예: 뉴스릴 1편, 스캔 도서 1권).",
  "classification": "엄격한 표준 분류체계 없음. 실제 조직축은 (1) collection 식별자(예: universal_newsreels, prelinger, us_national_archives 미러 등), (2) mediatype 팩싯(movies·texts·audio·image·software·web·data·collection), (3) 업로더가 부여한 subject/topic 태그. 도서 자료는 일부 openlibrary_subject / DDC(Dewey)·LCC·LCCN 필드가 산발적으로 채워지나 전수 적용 아님 — 통제어휘가 아닌 사용자 생성 메타데이터가 지배적.",
  "identifiers": "item 단위 전역 고유 identifier(URL 슬러그, archive.org/details/{identifier}) — 안정적 영구 식별자. 파생 도서에는 openlibrary OLID·ISBN·LCCN·OCLC 상호참조가 metadata에 담기기도 함. 파일 단위는 item 내부 name으로 식별.",
  "metadata_standard": "단일 아카이브 기술표준(ISAD(G)/DACS) 미채택. 자체 IA metadata 스키마(JSON, _meta.xml/_files.xml 기반) — Dublin Core에 근사한 필드(title·creator·date·subject·description·language·collection·mediatype·licenseurl·rights·publicdate·uploader). Lucene 색인 필드로 identifier·collection·mediatype·date·title·subject·year 등 노출.",
  "scope": "주제·시대 무제한(1996~ 웹 아카이브 포함, 디지털화된 인쇄물은 15~20세기 광범). 한국(1860–1960) 관련은 미국 발 뉴스릴 컬렉션(universal_newsreels 등), Prelinger, 미 정부기관 미러, A/V Geeks 업로드, 스캔 도서·잡지에 산재. 총 수억 아이템 규모지만 한국·1860–1960 교집합은 소수·비정형 분포.",
  "digitization": "전부 디지털 네이티브/디지털화 완료 자료만 존재(태생적 100% 온라인). item마다 원본 파일 + 파생본(예: MPEG4·OGV·썸네일, 도서는 PDF·EPUB·DjVu·OCR 텍스트·JP2 zip) 즉시 다운로드 가능(권리 허용 시). ia_metadata로 원본 포맷·바이트 크기 사전 확인 가능."
 },
 "access": {
  "channel": "검색: https://archive.org/advancedsearch.php (Lucene 쿼리 q, 반환필드 fl[], rows 페이지크기, output=json). 아이템 상세/파일: ia_metadata = https://archive.org/metadata/{identifier} (전체 metadata + original 파일 목록 w/ 크기 + licenseurl/rights). 다운로드: https://archive.org/download/{identifier}/{file}.",
  "auth": "none — API 키·인증 불필요. 익명 공개 접근.",
  "query_syntax": "Lucene 문법: field:value, AND/OR/NOT, 괄호 그룹, 따옴표 정확구, 와일드카드(identifier:111-adc*), 범위(date:[1860-01-01 TO 1960-12-31] 또는 year:[1860 TO 1960]). 핵심 필터 collection:, mediatype:(movies|texts|audio|image), subject:. 표기변형 OR 확장 필수: (korea OR chosen OR keijo OR corea). fl[]로 identifier,title,date,collection,mediatype,licenseurl 등 선택 반환. sort[]=date/downloads 등.",
  "response_format": "JSON(output=json): response.docs 배열(요청 fl 필드), response.numFound 총건수. 페이징은 rows + page 파라미터(또는 대량은 scraping API archive.org/services/search/v1/scrape 사용). ia_metadata는 단일 JSON(metadata 객체 + files 배열, 각 파일 name·format·size·md5).",
  "blocking_notes": "robots.txt는 advancedsearch/metadata API 경로를 차단하지 않음(공개 API). API 키 불요이나 공정사용 rate limit 존재 — 고빈도 시 429/일시 차단, 요청 간 간격·재시도 백오프 권장. JS 렌더 불요(순수 JSON). 지오블록 없음. 대량 수집은 scrape API 또는 cursor 방식 사용, advancedsearch의 deep paging(높은 page)엔 성능 제약.",
  "rights_access": "item별 상이 — Public Domain(미 정부 제작물, 저작권 만료 인쇄물) 다수는 원본 즉시 다운로드/복제 자유. 그러나 도서·영상 일부는 대출 전용(lending, DRM) 또는 rights/licenseurl에 제한 명시. 권리 판정은 반드시 ia_metadata의 licenseurl·rights·possible-copyright-status 필드로 개별 확인 후 다운로드."
 },
 "use": {
  "mismatch_summary": "언어적: 한국 자료가 영어 표제 + 일제기 일본식 로마자(Chosen·Tyosen·Keijo)·구미 구식표기(Corea)로 산재 — 단일 'Korea' 검색은 대량 누락. 'Chosen'은 영어 일반어(chosen)와 충돌해 반드시 newsreel·film·Japan·Keijo 등과 AND 조합 필요. 분류학적: 통제어휘 부재로 정식 분류코드 대신 업로더 collection/subject 태그에 의존 — 같은 주제가 여러 collection에 흩어지거나 태그 누락. 기술관행적: 메타데이터 품질이 업로더마다 불균질(date·creator 결측, 자유서술형 description), OCR 오식으로 도서 전문검색 노이즈. 따라서 표기변형 OR-확장 × mediatype/collection 팩싯 결합이 발굴의 핵심.",
  "keyword_ref": "해외 키워드셋 재사용: keywords_common의 CORE(Korea/Corea/Chosen/Choson…), WAR_* 그룹 + 일제기 표기변형(Chosen·Tyosen·Keijo·Government-General of Chosen). NARA 모듈(keywords_nara)의 RG 242 노획 필름 어휘(Chosen newsreel, Nihon News/日本ニュース, Nippon Eiga Korea)를 IA collection/mediatype 필터와 교차 적용. 신규 keywords_ia 셋은 IA 특유의 collection ID(universal_newsreels, prelinger 등)·identifier 접두(111-adc*)·mediatype 팩싯을 어휘로 포함.",
  "crossmap_ref": "RG_MAP류 분류 교차매핑 참조 — IA에는 고유 RG 개념이 없으므로, IA의 collection/subject를 NARA Record Group(특히 RG 242 노획문서·필름, RG 111 Signal Corps, RG 208 OWI)에 역매핑하는 crossmap 테이블을 경유. NARA에서 확인한 RG 시리즈 번호(예: 242-MID-J)를 IA identifier/title 검색어로 재투입하는 방식.",
  "adjacent_mining": "적용 가능 — item의 collection 소속을 축으로 인접 확장: 한 관련 아이템의 collection(예: universal_newsreels)을 collection: 팩싯으로 전수 스캔하면 동일 출처의 미기술 인접 아이템 발굴. identifier 접두 패턴(identifier:111-adc*) 와일드카드로 A/V Geeks 업로드 시리즈 전체 훑기. 도서는 openlibrary/creator 상호참조로 인접 판본 추적.",
  "cross_archive_combos": [
   "IA universal_newsreels/Prelinger 뉴스릴 ↔ NARA RG 242·RG 111 노획/신호대 필름 카탈로그 ↔ 국사편찬위 한국사DB로 사건·인물 대조 검증",
   "IA에서 발굴한 조선총독부(Government-General of Chosen) 홍보영상 ↔ JACAR 引揚げ·朝鮮 문서 ↔ 국가기록원 일제강점기 기록으로 제작·행정 맥락 교차확인",
   "IA 스캔 도서/잡지(texts, Chosen·Keijo) ↔ 국립중앙도서관 NARA 수집본(OWI·USDA) ↔ 한국사DB HUSAFIK로 미군정기 서사 대조",
   "IA 노획 일본 뉴스릴(Nihon News/日本ニュース) ↔ 국가기록원 노획문서 ↔ NARA RG 242 3자 교차 검증으로 원본 계보·중복본 식별"
  ],
  "rights_rule": "1차 판정 규칙: ia_metadata의 licenseurl → rights → possible-copyright-status 순으로 확인. licenseurl이 CC/PD이거나 미 연방정부 제작물(Public Domain)이면 원본 다운로드·복제 가능으로 초판정. licenseurl 부재+rights 제한 문구 또는 lending(대출 전용) collection이면 '접근 제한, 원문 열람만'으로 보수 판정하고 다운로드 보류 — 표시 부재를 자동 PD로 간주 금지, 개별 metadata 미확인 시 '미상'."
 },
 "verify": {
  "accurate": true,
  "notes": [],
  "robots": "Fetched via scrape_plan for https://archive.org/advancedsearch.php — verdict: robots ALLOWED (허용). advancedsearch/metadata API paths are not disallowed; public JSON API, no auth/key required. Matches the profile's blocking_notes claim."
 }
}
''')
