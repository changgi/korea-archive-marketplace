# korea-archive (Claude plugin) — v1.10

해외 5곳 + 국내 9곳, 총 **18개 도구**로 한국 관련 기록(1860–1960)을 발굴하는 클로드 플러그인.

## 도구

**해외** `tna_search` · `tna_adjacent_mine` · `nara_search` · `ia_search` · `ia_metadata` · `gallica_search` · `europeana_search`
**국내** `nedb_search`(한국사DB) · `archives_search`(국가기록원) · `nlk_search`(국립중앙도서관 6컬렉션) · `seoul_archives_search`(서울기록원) · `foia_search`(정보공개포털) · `local_gov_search`(서울정보소통광장·서울교육청·경남기록원) · `warmemo_search`(전쟁기념관)
**유틸** `query_bank`(1,943 키워드) · `judge_rights`(A~D 권리) · `scrape_plan` · `report_template`(HTML 보고서)
**스킬** `korea-archive-discovery` — 표기 변형·RG 교차·인접 마이닝·국내 교차검증·권리판정·HTML 보고서 전략을 자동 적용.

## 자동 브라우징 (v1.9–v1.10)

국내 사이트(JS·로그인)는 서버가 직접 조회·파싱해 실제 결과를 반환한다. 키가 필요한데 없는 기관은
클로드가 웹검색으로 결과를 가져오도록 지시한다.

## 연결 방식

- 기본은 원격 MCP 서버(`.mcp.json`의 `https://korea-archive-mcp.vercel.app/api/mcp`) — 설치 즉시 동작.
- 로컬 실행을 원하면 `.mcp.local.json.example`를 참고해 `servers/server.py`를 stdio로 구동(`pip install mcp`).

## 선택 환경변수

`NARA_API_KEY` · `EUROPEANA_API_KEY` · `ARCHIVES_API_KEY`(data.go.kr 15000153) · `NLK_API_KEY`(www.nl.go.kr Open API). 모두 선택.

라이선스 MIT · 공업연구사 송창기.
