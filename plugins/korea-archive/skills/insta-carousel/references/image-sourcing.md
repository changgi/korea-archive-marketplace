# 실물 이미지 소싱 플레이북

캐러셀의 신뢰는 실물 이미지에서 나온다. 사용자가 사진을 주지 않아도, 주제가 실존
대상이라면 아래 경로에서 라이선스 안전한 실물을 능동적으로 발굴하라.

## 1. 소스별 요령

### 위키미디어 공용 (1순위 — 검색·라이선스·고해상 삼박자)
```bash
# 검색 (한국어·영어 병행, srnamespace=6 = 파일)
https://commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=6&srlimit=8&format=json&srsearch=<쿼리>
# URL + 라이선스 + 설명 (여러 파일 | 구분 일괄)
...action=query&prop=imageinfo&iiprop=url|extmetadata&format=json&titles=File:...|File:...
```
- **다운로드는 반드시 API가 준 정확한 URL로** (경로 해시를 추측하면 404)
- **레이트리밋 대응**: 브라우저 User-Agent + Referer 헤더, 파일당 sleep 4~8초.
  HTML이 내려오면 차단된 것 — 간격 늘려 재시도
- PDF 문서는 `iiurlwidth=1000`을 주면 1쪽 썸네일 JPG URL(thumburl)을 얻는다
  (관보·헌법 같은 문서 스캔을 이미지로 쓸 때)
- 인물 초상: 위키피디아 REST `https://ko.wikipedia.org/api/rest_v1/page/summary/<이름>`
  의 originalimage가 지름길

### archive.org (필름·영상의 실제 프레임)
```bash
https://archive.org/metadata/<identifier>   # 파일 목록
```
- 영상 아이템의 `<id>.thumbs/*.jpg`가 **ffmpeg 없이 얻는 실제 프레임들**이다
  (수백 MB mp4를 받을 필요 없음). 6~8장 받아 최고의 컷을 고른다
- 검색: `identifier:111-adc*` 같은 고급 문법으로 시리즈 전수 확인 가능

### JS 렌더 사이트의 실물 캡처 (카탈로그 카드·검색결과 화면)
```bash
chrome --headless=new --window-size=1280,900 --virtual-time-budget=15000 --screenshot=out.png <URL>
```
- `--virtual-time-budget`이 핵심 — JS 렌더를 기다린다
- 카탈로그 페이지 스크린샷은 "기록이 실존한다"는 증거 이미지로 강력하다

### 기관 사이트 직접 수집
- User-Agent 없으면 에러 페이지를 주는 곳이 많다 — 항상 브라우저 UA 지정
- 세션 쿠키 필요한 곳: 목록 페이지를 쿠키 자르(-c)로 받고 같은 자르(-b)+Referer로 파일 요청

## 2. 라이선스 판정 (게시 가능성)

| 판정 | 기준 | 조치 |
|---|---|---|
| 자유 게시 | 미 연방정부 저작물(17 U.S.C. §105), 저작권 만료(한국: 1963년 이전 공표 사진 등), 법령·관보·공문서(저작권법 제7조) | 출처 표기 후 게시 |
| 조건부 | 공공누리 1유형(출처표시), CC BY/BY-SA(저작자 표기, SA는 명시) | 카드에 조건 이행 표기 — **크레딧 삭제 금지를 체크리스트에 명시** |
| 확인 필요 | 공공누리 유형 미표기, 기관 소장 기증자료 | 카드에 출처는 넣되 납품 시 "게시 전 기관 확인" 안내 필수 |
| 사용 금지 | 라이선스 불명, 지위 불명(노획물 등) | 텍스트·그래픽 카드로 대체 |

- extmetadata의 LicenseShortName·Artist를 반드시 읽는다. CC 계열은 저작자명까지 확보
- **거른다**: 워터마크 박힌 사본, 현대의 2차창작(팝아트 초상 등), 저해상(<300px, 단 작은 인셋은 가능)
- 기관 정식 명칭은 사이트 `<title>`로 확인 (통칭을 쓰면 정정 요청이 온다)

## 3. 후처리

- Pillow로 정규화: `thumbnail((1000,1000))` + JPEG q85 → 템플릿에서 `{{img:...|maxdim=760|q=72}}`
- GIF/PNG/TIFF-EXIF도 `Image.open().convert('RGB')`로 JPEG 통일
- 큰 스캔은 DecompressionBomb 경고가 떠도 thumbnail 후 저장하면 문제없다

## 4. 출처 대장 (`sources.txt`) — 소싱과 동시에 기록

이미지를 받는 **즉시** 한 줄씩 기록한다 (나중에 몰아 쓰면 반드시 빠진다).
납품물에 포함 — 사용자가 출처 문의를 받았을 때 근거가 되고, 카드·캡션의 출처 문구가
전부 이 대장에서 나온다.

형식 (이미지 1장 = 1블록):
```
[파일명] cover.jpg
  기관: 미국 국립문서기록관리청 (NARA)          ← 정식 명칭
  식별: RG 111, 111-ADC-5280 (NAID 12345)      ← 식별번호 전부
  원본: https://catalog.archives.gov/id/12345   ← 원 소장처 URL
  사본: https://archive.org/details/111-adc-5280 ← 실제 내려받은 곳
  라이선스: 퍼블릭 도메인 (17 U.S.C. §105)
  확인일: 2026-08-04
  카드: 1, 4                                   ← 사용된 카드 번호
```
- 카드 캡션에는 이 대장의 축약형을 쓴다: `출처: NARA RG 111, 111-ADC-5280 (퍼블릭 도메인)`
- 식별번호를 아는데 "위키미디어 공용"이라고만 쓰는 것은 부정확한 출처다 —
  사본처(위키미디어)가 아니라 **원 소장처+식별번호가 본 출처**, 사본처는 부기

## 5. 이미지가 정말 없을 때

- 없는 것 자체를 콘텐츠로: 카탈로그 스크린샷("기록은 실존한다"), 문서 스캔, 지도·타임라인 등
  자체 그래픽. "사진 대신 기록으로 남은" 프레이밍이 오히려 강한 카드가 되기도 한다
- 절대 하지 말 것: 무관한 이미지 갖다 붙이기, AI 생성 이미지를 실물처럼 제시하기
