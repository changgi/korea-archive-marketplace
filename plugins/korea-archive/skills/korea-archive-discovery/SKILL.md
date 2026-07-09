---
name: korea-archive-discovery
description: 해외 아카이브(NARA·TNA·archive.org 등)에서 한국 관련 기록·영상(1860~1960)을 발굴할 때 사용. "한국 관련 자료 찾아줘", "NARA에서 한국 영상 검색", "TNA 한국 문서", "노획 필름", "해방/한국전쟁 영상 발굴", "아카이브 검색 전략" 등의 요청에서 트리거. 검증된 쿼리 전략(표기 변형·RG 교차·TNA 코드·인접 확장)과 권리 판정 원칙을 제공한다.
---

# 해외 아카이브 한국 기록 발굴 스킬

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

## MCP 도구가 있으면 (korea-archive 서버)
tna_search → tna_adjacent_mine → nara_search(RG 교차) → ia_search → gallica_search(프랑스어) → europeana_search → judge_rights 순으로 사용.
없으면 위 규칙대로 웹 검색·카탈로그 직접 조회로 수행.

## 산출 형식
발굴 결과는 반드시: 식별자(NAID/참조코드) · 원제 · 연대 · 소장처 · URL · 권리등급 초판 · 검색쿼리(재현용)를 표로 보고.
