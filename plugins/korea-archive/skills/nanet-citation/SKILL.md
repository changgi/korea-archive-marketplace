---
name: nanet-citation
description: >
  대한민국 국회도서관 전자도서관(dl.nanet.go.kr) 소장정보를 활용한 논문 참고문헌 및 각주 작성 전문 스킬.
  사용자가 "국회도서관 인용", "nanet 참고문헌", "학위논문 인용형식", "단행본 출처 작성",
  "국회도서관 소장자료 각주", "dl.nanet.go.kr 검색결과 인용", "학술기사 참고문헌 형식",
  "정부간행물 출처" 처럼 국회도서관 자료의 인용 형식이 필요할 때 반드시 이 스킬을 사용할 것.
  dl.nanet.go.kr URL·자료명·저자·발행연도·권호 등을 입력받아
  국내 학술지 표준(APA·한국심리학회·국문학·역사학 방식) 및 Chicago 스타일로
  각주(footnote)와 참고문헌(bibliography) 항목을 자동 생성한다.
  사용자가 URL을 제공하지 않아도 자료명·저자·연도만으로 작성을 도와줄 수 있어야 한다.
---

# 대한민국 국회도서관(dl.nanet.go.kr) 참고문헌 작성 스킬

## 개요

이 스킬은 국회전자도서관(dl.nanet.go.kr)에 수록된 자료를 학술 논문에 인용할 때의
**각주(footnote)** 및 **참고문헌(bibliography)** 형식을 자동으로 작성한다.

---

## 1. 자료 유형 판별 — CN 코드 및 자료유형 분류표

사용자가 제공하는 URL 또는 자료명으로 아래 유형을 자동 판별한다.

| CN 접두어 | 자료 유형 | 예시 |
|----------|----------|------|
| `KDMT`   | 국내 학위논문 (석사·박사) | `KDMT1201319543` |
| `MONO`   | 국내외 단행본 | `MONO1200934972` |
| `NONB`   | 비도서 자료 (보고서·정부간행물·통계자료) | `NONB1201513986` |
| `KINX`   | 국내 학술기사 (학술지 수록 논문) | `KINX2019035429` |
| `FMON`   | 외국 단행본 | `FMON` 시작 |
| `ARTI`   | 국외 학술기사 | `ARTI` 시작 |
| `BOMA`   | 고서·고문헌 | `BOMA` 시작 |
| `SERL`   | 연속간행물·학술지 | `SERL` 시작 |

### URL에서 CN 코드 추출 방법

```
https://dl.nanet.go.kr/SearchDetailView.do?cn=KDMT1201319543
                                                ↑ 이 부분이 CN 코드
```

- URL이 있으면 → `cn=` 이후 값으로 자료유형 자동 판별
- URL이 없으면 → 사용자 제공 정보(학위논문·단행본·학술기사 등)로 유형 판별

---

## 2. 자료 유형별 인용 형식

### ──────────────────────────────────
### 【유형 1】국내 학위논문 (KDMT)
### ──────────────────────────────────

#### 필수 정보
| 필드 | 설명 | 예시 |
|------|------|------|
| 저자명 | 논문 저자 | 홍길동 |
| 논문 제목 | 전체 제목 (부제 포함) | `디지털 기록관리 시스템 연구` |
| 학위 종류 | 석사 or 박사 | 박사 |
| 대학교 및 학과 | 수여 기관 전체명 | 한국대학교 대학원 기록관리학과 |
| 수여 연도 | YYYY.M | 2023.2 |
| 지도교수 | (선택) | 김철수 |
| CN 코드 또는 URL | 국회도서관 식별자 | KDMT2023XXXXX |

#### 국내 학술지 표준 형식 (한국 논문 일반)

**각주:**
```
저자명, 「논문 제목」, 학위논문(석사 or 박사), 대학교 대학원 학과명, YYYY.M, 쪽수.
```

**참고문헌:**
```
저자명. 「논문 제목」. 학위논문(석사 or 박사). 대학교 대학원 학과명, YYYY.
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드), 검색일: YYYY.MM.DD.
```

**예시 (각주):**
```
홍길동, 「공공기관 기록관리 시스템 고도화 방안 연구」, 학위논문(박사),
한국대학교 대학원 기록관리학과, 2023.2, 45쪽.
```

**예시 (참고문헌):**
```
홍길동. 「공공기관 기록관리 시스템 고도화 방안 연구」. 학위논문(박사).
한국대학교 대학원 기록관리학과, 2023.
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=KDMT2023XXXXX), 검색일: 2026.03.13.
```

#### APA 7판 형식

**참고문헌:**
```
저자성, 이름. (연도). 논문 제목 [학위 종류, 대학교명]. 국회도서관 전자도서관.
https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드
```

**예시:**
```
Hong, G. (2023). A study on the improvement of records management systems in public institutions
[Doctoral dissertation, Korea University]. National Assembly Library of Korea.
https://dl.nanet.go.kr/SearchDetailView.do?cn=KDMT2023XXXXX
```

#### Chicago 형식 (각주)
```
저자명, "논문 제목" (학위논문(박사), 대학교명, 연도), 쪽수.
https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드 (검색일: YYYY년 MM월 DD일).
```

---

### ──────────────────────────────────
### 【유형 2】국내외 단행본 (MONO / FMON)
### ──────────────────────────────────

#### 필수 정보
| 필드 | 설명 |
|------|------|
| 저자명(들) | 단독·공저·편저 구분 |
| 서명(제목) | 부제 포함 전체 제목 |
| 출판지 | 서울, 부산 등 |
| 출판사 | 발행처 전체명 |
| 발행연도 | YYYY |
| 총페이지 또는 인용 쪽수 | |
| 판차 | 2판, 3판 등 (초판이면 생략) |
| CN 코드 / URL | |

#### 국내 학술지 표준 형식

**각주:**
```
저자명, 『서명』 (출판지: 출판사, 연도), 쪽수.
```

**참고문헌:**
```
저자명. 『서명』. 출판지: 출판사, 연도.
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드), 검색일: YYYY.MM.DD.
```

**공저 예시 (각주):**
```
김철수·이영희, 『한국 기록관리학 개론』 (서울: 아카넷, 2022), 105쪽.
```

**편저 예시 (각주):**
```
박지영 편, 『디지털 아카이브의 이해』 (서울: 한울, 2021), 33-45쪽.
```

**참고문헌 예시:**
```
김철수·이영희. 『한국 기록관리학 개론』. 서울: 아카넷, 2022.
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=MONO2022XXXXX), 검색일: 2026.03.13.
```

#### APA 7판 형식

**참고문헌:**
```
저자성, 이니셜. (연도). 서명: 부제. 출판사.
https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드
```

**번역서 예시:**
```
Schellenberg, T. R. (1956). Modern archives: Principles and techniques. University of Chicago Press.
[한국어판: T. R. 셸렌버그, 조경구 역, 『현대 기록학 개론』 (서울: 진리탐구, 2002).]
https://dl.nanet.go.kr/SearchDetailView.do?cn=FMONXXXXX
```

#### Chicago 형식 (각주)
```
저자명, 『서명』 (출판지: 출판사, 연도), 쪽수.
```

---

### ──────────────────────────────────
### 【유형 3】학술기사 (KINX / ARTI)
### ──────────────────────────────────

#### 필수 정보
| 필드 | 설명 |
|------|------|
| 저자명(들) | |
| 논문 제목 | |
| 학술지명 | 『』로 표기 |
| 권(Volume) | |
| 호(Number/Issue) | |
| 발행연도 | |
| 수록 쪽수 | pp. XX-XX |
| DOI 또는 CN 코드 | |

#### 국내 학술지 표준 형식

**각주:**
```
저자명, 「논문 제목」, 『학술지명』 권수 호수 (연도), 쪽수.
```

**참고문헌:**
```
저자명. 「논문 제목」. 『학술지명』 권수 호수 (연도): 쪽수-쪽수.
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드), 검색일: YYYY.MM.DD.
```

**예시 (각주):**
```
이순신, 「공공기록물 관리에 관한 법률 개정 방향」, 『기록학연구』 제75호 (2023), 45-67쪽.
```

**예시 (참고문헌):**
```
이순신. 「공공기록물 관리에 관한 법률 개정 방향」. 『기록학연구』 75 (2023): 45-67.
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=KINX2023XXXXX), 검색일: 2026.03.13.
```

#### APA 7판 형식

**참고문헌:**
```
저자성, 이니셜. (연도). 논문 제목. 학술지명, 권(호), 시작쪽-끝쪽.
https://doi.org/XXXXXXX  또는  https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드
```

**예시:**
```
Lee, S. (2023). Directions for revision of the Public Records Management Act. 
Journal of Records Management & Archives Society of Korea, 75, 45-67.
https://dl.nanet.go.kr/SearchDetailView.do?cn=KINX2023XXXXX
```

---

### ──────────────────────────────────
### 【유형 4】비도서 자료 — 보고서·정부간행물 (NONB)
### ──────────────────────────────────

#### 하위 유형 판별
- **정부간행물**: 중앙행정기관, 지방자치단체, 국회 발간 자료
- **연구보고서**: 국책연구기관(KRIVET, KDI, KIPA, NARS 등) 발간 자료
- **통계자료**: 통계청, 각 부처 통계
- **회의자료·백서**: 공청회 자료집, 연보, 백서

#### 국내 학술지 표준 형식

**정부간행물 각주:**
```
[발행기관명], 『보고서 제목』 (발행연도), 쪽수.
```

**정부간행물 참고문헌:**
```
[발행기관명]. 『보고서 제목』. 발행지: 발행기관, 발행연도.
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드), 검색일: YYYY.MM.DD.
```

**연구보고서 각주:**
```
저자명, 『연구보고서 제목』, 보고서 번호 (발행기관, 발행연도), 쪽수.
```

**연구보고서 참고문헌:**
```
저자명. 『연구보고서 제목』. 보고서 번호. 발행지: 발행기관, 발행연도.
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=NONBXXXXX), 검색일: YYYY.MM.DD.
```

**예시 (정부간행물 각주):**
```
행정안전부, 『2023 행정안전부 기록관리 연보』 (2024), 25쪽.
```

**예시 (연구보고서 각주):**
```
박민아·최재영, 『공공기관 기록관리 실태조사 연구』, NARS 현안보고서 제752호
(국회입법조사처, 2022), 33쪽.
```

#### APA 7판 형식

**정부보고서:**
```
발행기관명. (연도). 보고서 제목 (보고서 번호). 발행기관.
https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드
```

**예시:**
```
Ministry of the Interior and Safety. (2024). 2023 records management yearbook.
Ministry of the Interior and Safety.
https://dl.nanet.go.kr/SearchDetailView.do?cn=NONBXXXXX
```

---

### ──────────────────────────────────
### 【유형 5】연속간행물·학술지 (SERL)
### ──────────────────────────────────

#### 국내 학술지 표준 형식

**참고문헌 (전체 학술지 권호):**
```
『학술지명』 권 호 (연도). 발행기관.
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드), 검색일: YYYY.MM.DD.
```

---

### ──────────────────────────────────
### 【유형 6】고서·고문헌 (BOMA)
### ──────────────────────────────────

#### 국내 학술지 표준 형식

**각주:**
```
『서명』 권호, 편목명.
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드), 검색일: YYYY.MM.DD.
```

**참고문헌:**
```
『서명』. 소장기관: 국회도서관. 청구기호: XXX.
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드), 검색일: YYYY.MM.DD.
```

---

## 3. 검색 URL 패턴 — 인용에 활용

### 소장정보 검색
```
https://dl.nanet.go.kr/SearchList.do?searchType=SIMPLE&query=검색어
```

### 자료 상세 페이지 (인용 URL로 사용)
```
https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드
```

### 검색 필터 파라미터
| 파라미터 | 값 | 설명 |
|---------|-----|------|
| `searchType` | `SIMPLE` / `EXPERT` | 기본/전문 검색 |
| `query` | 검색어 | URL 인코딩 |
| `searchField` | `ALL` / `TITLE` / `AUTHOR` / `PUBLISHER` / `SUBJECT` | 검색 필드 |
| `materialType` | `MONO` / `KDMT` / `KINX` / `NONB` | 자료유형 필터 |

---

## 4. 자료 제공 시 처리 흐름

```
사용자 입력
    │
    ├── dl.nanet.go.kr URL 제공
    │       └── cn= 파라미터로 CN코드 추출
    │               └── CN 접두어로 자료유형 판별
    │
    ├── 자료명·저자·연도만 제공
    │       └── 자료유형 질문 후 판별
    │               (학위논문 / 단행본 / 학술기사 / 보고서 중 하나)
    │
    └── 복수 자료 목록 제공
            └── 각 자료별 유형 판별 → 일괄 참고문헌 생성
```

---

## 5. 인용 스타일별 선택 가이드

| 분야 | 권장 스타일 | 근거 |
|------|-----------|------|
| 역사학·인문학 | 국내 학술지 표준 (각주 방식) | 『기록학연구』, 『역사학보』 등 준용 |
| 사회과학·행정학 | APA 7판 | 『한국행정학보』, 『정부학연구』 등 준용 |
| 법학 | 국내 법학 각주 방식 | 『법학연구』, 『공법연구』 등 준용 |
| 이공계 | APA 7판 | 국제 논문 기준 |
| 도서관·기록학 | 국내 표준 or APA | 『한국도서관정보학회지』, 『기록학연구』 |
| 국제 학술지 투고 | APA 7판 또는 Chicago | 학술지 투고 규정 확인 필수 |

---

## 6. 입력 정보 부족 시 처리 원칙

| 부족한 정보 | 처리 방법 |
|-----------|---------|
| URL 없음 | `검색일:` 항목 생략 또는 "검색 필요" 표시 후 검색 URL 제공 |
| 쪽수 없음 | 각주에서 쪽수 생략, 참고문헌은 총면수 미기재로 처리 |
| 출판지 없음 | 출판사명만으로 대처 (예: "서울" 생략) |
| 판차 불명 | 초판으로 추정 처리 (명시적 표기 없음) |
| 공저자 3인 이상 | 각주: 첫 저자 외 (2인 이상 공저시) `외 N인` / 참고문헌: 전원 기재 |
| CN코드 없음 | URL 생략, 검색 경로 안내: `https://dl.nanet.go.kr/SearchList.do?query=제목` |

---

## 7. 특수 케이스 처리

### 7-1. 번역서
**각주:**
```
원저자명 지음, 역자명 옮김, 『번역 서명』 (출판지: 출판사, 번역연도), 쪽수.
```

**참고문헌:**
```
원저자 성, 이름. (원저 출판연도). 원저 서명. [한국어판: 역자명 옮김. 『번역 서명』.
출판지: 출판사, 번역연도.]
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드), 검색일: YYYY.MM.DD.
```

### 7-2. 국회·입법 자료

국회 발간 자료는 NONB 유형으로 처리하되, 발행기관을 정확히 명시한다.

**각주:**
```
국회입법조사처, 「보고서 제목」, 『현안분석』 제XXX호 (2023), 쪽수.
```

**참고문헌:**
```
국회입법조사처. 「보고서 제목」. 『현안분석』 제XXX호. 서울: 국회입법조사처, 2023.
대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=NONBXXXXX), 검색일: 2026.03.13.
```

### 7-3. 공동 저자 표기 규칙

| 스타일 | 2인 | 3인 이상 (각주) | 3인 이상 (참고문헌) |
|-------|-----|--------------|----------------|
| 국내 표준 | 홍길동·이순신 | 홍길동 외 | 홍길동·이순신·박영수 |
| APA 7판 | Hong & Lee | Hong et al. | Hong, G., Lee, S., & Park, Y. |
| Chicago | 홍길동과 이순신 | 홍길동 외 | 홍길동, 이순신, 박영수 |

### 7-4. 온라인 원문 제공 여부 구분

국회도서관 자료 중 원문 제공 여부가 다르므로 주석 구분:

- **원문 제공 (전자자료)**: URL 인용 가능, `검색일:` 명시
- **원문 미제공 (관내열람)**: "원문은 국회도서관 방문 열람" 부기 권장
- **외부 구독 DB 연계**: 해당 DB 명칭 병기 (예: DBpia, KISS 등)

---

## 8. 완성 참고문헌 예시 — 종합

### 국내 학술지 표준 (역사학·인문학 논문 참고문헌 목록)

```
【단행본】
김철수. 『한국 기록관리법제 연구』. 서울: 아카넷, 2022.
    대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=MONO2022XXXXX), 검색일: 2026.03.13.

【학위논문】
이영희. 「공공기관 기록관리 실태에 관한 연구」. 학위논문(박사). 한국대학교 대학원 기록관리학과, 2021.
    대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=KDMT2021XXXXX), 검색일: 2026.03.13.

【학술기사】
박민아. 「전자기록 보존 정책의 국제 동향」. 『기록학연구』 72 (2022): 3-45.
    대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=KINX2022XXXXX), 검색일: 2026.03.13.

【정부보고서】
행정안전부. 『2023 국가기록관리 백서』. 서울: 행정안전부, 2024.
    대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=NONB2024XXXXX), 검색일: 2026.03.13.

【번역서】
셸렌버그, T. R. 조경구 옮김. 『현대 기록학 개론』. 서울: 진리탐구, 2002.
    대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=MONO2002XXXXX), 검색일: 2026.03.13.
```

### APA 7판 (사회과학·행정학 논문 참고문헌 목록)

```
Kim, C. (2022). A study on Korean records management legislation. Akanet.
    https://dl.nanet.go.kr/SearchDetailView.do?cn=MONO2022XXXXX

Lee, Y. (2021). A study on records management practices in public institutions
    [Doctoral dissertation, Korea University]. National Assembly Library of Korea.
    https://dl.nanet.go.kr/SearchDetailView.do?cn=KDMT2021XXXXX

Park, M. (2022). International trends in electronic records preservation policy.
    Journal of Records Management & Archives Society of Korea, 72, 3-45.
    https://dl.nanet.go.kr/SearchDetailView.do?cn=KINX2022XXXXX

Ministry of the Interior and Safety. (2024). 2023 national records management white paper.
    Ministry of the Interior and Safety.
    https://dl.nanet.go.kr/SearchDetailView.do?cn=NONB2024XXXXX
```

---

## 9. 검색 안내 — 사용자 직접 검색 가이드

사용자가 아직 자료를 찾지 못한 경우, 아래 검색 경로를 함께 안내한다.

### 검색 방법별 URL

| 검색 유형 | URL |
|---------|-----|
| 자료명 검색 | `https://dl.nanet.go.kr/SearchList.do?searchType=SIMPLE&searchField=TITLE&query=제목` |
| 저자 검색 | `https://dl.nanet.go.kr/SearchList.do?searchType=SIMPLE&searchField=AUTHOR&query=저자명` |
| 학위논문만 검색 | `https://dl.nanet.go.kr/SearchList.do?searchType=SIMPLE&materialType=KDMT&query=검색어` |
| 단행본만 검색 | `https://dl.nanet.go.kr/SearchList.do?searchType=SIMPLE&materialType=MONO&query=검색어` |
| 학술기사만 검색 | `https://dl.nanet.go.kr/SearchList.do?searchType=SIMPLE&materialType=KINX&query=검색어` |

---

## 10. 각주-참고문헌 연결 규칙

논문에서 동일 자료를 반복 인용 시:

| 상황 | 각주 처리 |
|------|---------|
| 첫 인용 | 완전 각주 형식 |
| 같은 주석 내 직전 인용과 동일 | `위의 책`, `위의 글`, `위의 논문`, 쪽수. |
| 이전 주석의 동일 자료 | `홍길동, 앞의 책`, 쪽수. 또는 `홍길동, 앞의 글`, 쪽수. |
| APA에서 재인용 | 저자, 연도, 쪽수 형식 그대로 유지 |

---

## 11. 스킬 사용 시 Claude의 처리 절차

1. **입력 파악**: URL / 자료명 / 저자 / 연도 / 자료유형 등 확인
2. **CN코드 분석**: URL이 있으면 `cn=` 이후 접두어로 자료유형 자동 판별
3. **부족 정보 확인**: 필수 필드 누락 시 질문 (한 번에 묶어서)
4. **스타일 선택**: 사용자가 명시하지 않으면 자료 분야에 맞는 스타일 추천
5. **형식 생성**: 각주 + 참고문헌 동시 생성 (기본)
6. **검색 URL 제공**: CN코드가 없을 경우 국회도서관 검색 경로 함께 안내

---

## 12. 검색일(accessed date) 처리 규칙

- **온라인 원문 제공 자료**: 검색일 반드시 명시 (`검색일: YYYY.MM.DD.`)
- **실물 자료 (관내 열람)**: 검색일 생략 가능, 소장 청구기호 대신 기재 가능
- **기본 검색일**: 사용자가 미제공 시 → 오늘 날짜(2026.03.13.) 적용
