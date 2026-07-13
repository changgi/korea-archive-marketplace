#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile_gallica — 프랑스 국립도서관 Gallica (Gallica (Bibliothèque nationale de France)) 자료·이용·활용구조 프로파일."""
import json
PROFILE = json.loads(r'''
{
 "name_ko": "프랑스 국립도서관 Gallica",
 "name_en": "Gallica (Bibliothèque nationale de France)",
 "category": "overseas",
 "data": {
  "hierarchy": "도서관형 디지털 컬렉션 — 아카이브식 fonds/series 계층이 아니라 개별 디지털 문서(document numérisé) 단위의 평면 레코드. 단, 발행물은 títre(제목) → fascicule/numéro(개별 호) → vue(페이지 이미지) 3단으로 묶이고, 필사본은 BnF 부서 소장 volume/pièce 단위. 실질 발굴 단위는 périodique의 '호(fascicule)'와 monographie의 '권'.",
  "classification": "단일 아카이브 분류체계 없음. (1) 소장 출처 = BnF 부서(Manuscrits, Estampes et photographie, Cartes et plans, Arsenal) + 제휴기관(bibliothèques partenaires) (2) BnF cote(청구기호=shelfmark)로 물리 배가 (3) 검색면에서는 dc.type 문서유형(monographie·périodique/fascicule·image·carte·manuscrit·partition·enregistrement sonore·objet)으로 구분. 주제 분류(한국 전용 클래스)는 부재.",
  "identifiers": "ark:/12148/ (Archival Resource Key, BnF 네임스페이스 12148) = 각 디지털 문서의 영구 식별자 겸 URL 기반; 물리 원본은 BnF cote(청구기호). SRU 레코드는 ark를 dc:identifier로 반환.",
  "metadata_standard": "Dublin Core(비한정 oai_dc: 15요소) — SRU/OAI-PMH 노출. 표현/이미지 계층은 IIIF Presentation API(manifest) + IIIF Image API. 필사본 상세기술은 BnF Archives et manuscrits(EAD 기반 BAM)로 연계. 레코드 자체는 얕은 DC(제목·저자·날짜·유형·언어·권리)여서 기사/편지 단위 색인은 없음.",
  "scope": "중세 필사본~20세기 초·중반; 한국(1860–1960) 사료는 구한말 프랑스 선교(파리외방전교회 MEP)·외교·삽화신문 중심. 전체 규모 약 1,000만+ 디지털 문서. 한국 직접 관련은 소량이나 périodique 전문(OCR) 안에 산재.",
  "digitization": "100% 디지털화(정의상 디지털도서관) — 인쇄물은 전문 OCR(mode texte) 제공으로 본문 검색 가능, 도판·필사본·지도는 고해상 이미지(IIIF, 다운로드/줌). 다수가 domaine public로 원본 열람·다운로드 개방."
 },
 "access": {
  "channel": "SRU 1.2 엔드포인트 https://gallica.bnf.fr/SRU (operation=searchRetrieve&version=1.2). CQL 질의 형식 'gallica all \"<q>\"'. 병행: OAI-PMH, IIIF(문서 표현), 웹 UI gallica.bnf.fr.",
  "auth": "none — 키·토큰·계정 불요. 공개 API.",
  "query_syntax": "CQL. 기본 만능 색인 gallica all \"<q>\"(메타데이터+전문 통합). 정밀화: dc.title all / dc.creator all / dc.type all \"fascicule|monographie|image\" / dc.language all \"kor|fre\" / dc.date, 발행물 전문은 text/ocr 색인, 근접·불리언(and/or/prox) 지원. 프랑스어 정확구는 큰따옴표로 감싸 구동. 서버측 필터로 유형·언어·날짜 결합 권장.",
  "response_format": "XML — SRW searchRetrieveResponse(srw: 네임스페이스), numberOfRecords + recordData 안에 oai_dc(dc:) 레코드. 페이징은 startRecord + maximumRecords(요청당 최대 50). 이미지/전문은 별도 ark URL·IIIF manifest로 취득.",
  "blocking_notes": "robots·지오블록 사실상 없음(SRU 공개, 전 세계 접근). 키 없음. 과도 요청 시 예의적 rate-limit 권장(순차·백오프); 대량 수확은 OAI-PMH가 적합. UA 헤더 지정 권장. 일부 저작권 잔존 자료는 레코드는 검색되나 전문/다운로드가 'consultable sur place' 등으로 제한될 수 있음.",
  "rights_access": "자료별 권리표시 상속: 'domaine public'(공유마당) 자료는 열람·다운로드·연구 이용 자유, 재이용은 비상업 무료/상업은 BnF 조건(licence) 준수. 저작권 잔존(대략 20세기 중반 이후 신문·저작물)은 온라인 열람 제한 또는 권리 확인 필요. ark URL은 영구 인용 가능."
 },
 "use": {
  "mismatch_summary": "언어적: 'Korea'로는 거의 안 잡힘 — 프랑스어 표기 Corée·Coréens·Coréen(ne), 역사 표기 Tchosen/Tchosön(조선), Royaume ermite, guerre de Corée가 필수이며 도시명도 프랑스식 Séoul·Fusan(부산)·Gensan(원산)·Ping-Yang(평양)·Chemulpo(제물포)로 갈린다(프랑스식 전사: ou=u, tch=ch). 분류학적: 한국 전용 주제 클래스가 없어 구한말 자료가 'Extrême-Orient'·'Asie orientale'·중국/일본 인접 항목에 흡수됨; dc.type은 주제가 아닌 형태 축이라 주제검색이 무력 → gallica all 전문검색으로 우회. 기술관행적: DC가 얕아 관련 내용이 périodique '호'나 선교 서한집 '권' 내부(기사·편지 단위)에 묻혀 레코드 표면에 안 드러남 → OCR 전문 질의로만 표면화된다.",
  "keyword_ref": "신설 keywords_gallica(프랑스어 변형셋) 우선 — Corée·Coréens·Tchosen·Royaume ermite·guerre de Corée·Séoul·Fusan·Gensan·Ping-Yang·Chemulpo·missionnaires+Corée·Missions Étrangères de Paris·martyrs de Corée·Bataillon français de Corée(ONU). 공통 영어셋(keywords_common의 CORE·PREMODERN·PEOPLE_KOREAN·DIPLOMATIC·HUMANITARIAN)과 교차 대응시켜 개념 동치 유지; 순수 영어 G-/N-/T-/RG 그룹은 Gallica에서 직접 저효율이므로 프랑스어 매핑을 거쳐 사용.",
  "crossmap_ref": "RG_MAP 비적용(도서관형·RG 없음). 대신 dc.type(문서유형)+발행물 제목 기반 매핑을 사용: 선교 périodique(Annales de la Propagation de la Foi·Les Missions catholiques) → 주제상 NARA RG 59/한국교회사, guerre de Corée 프랑스 신문 → NARA RG 242/319 및 SHD와 주제 교차. NARA RG_MAP과는 '한국 개념 ↔ RG' 축에서 개념 매핑으로만 연결.",
  "adjacent_mining": "부분 적용 — NARA식 공식 인접레코드 API는 없으나, périodique 제목(arkPress/발행물 계층) 아래 특정 날짜 전후 fascicule를 연속 열람(호-단위 인접 채굴)하고 IIIF manifest의 vue 시퀀스로 한 호 내 기사 인접을 훑는 방식으로 구현 가능. 한 사건(예: 병인양요·을미사변·구한말 사절)의 프랑스 언론 보도는 인접 호 스캔이 효과적.",
  "cross_archive_combos": [
   "Gallica 선교 périodique(Missions Étrangères de Paris·Annales/Missions catholiques, martyrs de Corée) ↔ 한국사DB 근현대·한국교회사연구소 ↔ 파리 MEP 문서고 — 구한말 선교·박해 사료 3자 대조",
   "Gallica guerre de Corée 프랑스 신문 보도 ↔ 국가기록원 노획문서/NARA RG 242 ↔ 한국사DB HUSAFIK — 한국전쟁 서사 교차검증",
   "Gallica '프랑스 대대(Bataillon français de l'ONU en Corée)' 언론·삽화 ↔ SHD(Service historique de la Défense) ↔ 국방부 군사편찬연구소 — 프랑스 유엔군 참전 기록 대조",
   "Gallica 삽화신문 구한말 도판(Le Monde illustré·Le Petit Journal, Séoul/Fusan 판화·사진) ↔ 국립중앙박물관·국사편찬위 ↔ 서양인 수집 사진컬렉션 — 시각사료 출처·연대 교차"
  ],
  "rights_rule": "1차 판정: 문서의 명시 권리표시 우선 — 'domaine public' 태그 또는 1900년 이전 간행물 = 공개(A, 열람·다운로드·연구 자유, 상업 재이용은 BnF licence 확인). 1900–1960 신문·저작물은 자동 공개로 보지 말고 per-item 권리표시·저자 사후 70년 기준 재확인(B/C 보류); 온라인 열람 제한(consultable sur place)·저작권 잔존 표시 자료는 D 취급으로 공개 금지 후 수동 확정."
 },
 "verify": {
  "accurate": true,
  "notes": [],
  "robots": "Allowed. scrape_plan on https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2&query=gallica all \"Corée\" returned robots 허용 (permitted); note JS-rendered UI pages may need a browser tool, but the SRU/XML API itself is directly fetchable. Matches the profile's blocking_notes (no robots/geoblock, no key, polite rate-limit advised)."
 }
}
''')
