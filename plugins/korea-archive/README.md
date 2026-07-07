# korea-archive 플러그인

해외 아카이브에서 한국 관련 기록·영상(1860~1960)을 발굴하는 Claude 플러그인.
학술 검증된 방법론(송창기 2026, 국가기록원 — Recall 93.0%, F1 0.931) 기반.

## 포함 구성
- **스킬 `korea-archive-discovery`** — 표기 변형(Keijo·Fusan·Chosin…), 넓게→좁게 전략,
  TNA 부처코드·인접 확장, 권리 판정 5원칙, 쿼리 치트시트.
- **MCP 서버 `korea-archive`** — 도구 7종:
  `tna_search` `tna_adjacent_mine` `nara_search` `ia_search` `ia_metadata` `query_bank` `judge_rights`

## 요구사항
- Python 3.10+ 및 `pip install mcp`
- (선택) NARA 검색용 API 키 — Catalog_API@nara.gov 에 이름·이메일로 무료 발급 요청 후
  `.mcp.json`의 `NARA_API_KEY` 또는 환경변수로 설정. TNA·archive.org·쿼리뱅크·권리판정은 키 없이 동작.

## 사용 예
- "TNA에서 FO 371 FK1015 검색해줘"
- "FO 371/84053 주변 ±10 마이닝해서 승격 후보 찾아줘"
- "구한말(G-07) 쿼리 세트 보여줘"
- "RG 242 노획필름 권리 등급 판정해줘"

## 데이터 출처·라이선스
MIT. 키워드 정본: korea-records-keywords v1.0.0 (MIT © 2026 Song, Chang-Gi — 국가기록원).
검색 요청 간격을 존중하고, NARA 키는 월 10,000쿼리 한도를 지키십시오.
권리 자동판정은 초기판정입니다 — 공개 전 수동 확정 필수, D등급 공개 금지.
