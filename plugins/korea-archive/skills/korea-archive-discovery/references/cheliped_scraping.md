# cheliped-skills 브라우저 스크래핑 (robots 차단·JS 렌더 폴백)

API가 없거나 robots가 막았거나 화면이 JavaScript로 렌더되는 사이트(한국사DB 등)는
브라우저를 실제로 구동해 DOM을 관찰·스크래핑한다. 도구 `scrape_plan(url)`이 명령을 만들어 준다.

## 도구
- **cheliped-skills** (MIT) — github.com/tykimos/cheliped-skills
- browser 스킬: Chrome DevTools Protocol(CDP) 기반. 모든 상호작용 요소에 번호 id를 부여한
  LLM 친화 'Agent DOM'을 노출 → observe / click / fill / screenshot / scrape.

## 설치
```
git clone https://github.com/tykimos/cheliped-skills
cd cheliped-skills/browser/scripts && npm install && npm run build
```

## 실행 패턴
```
# 1) 페이지 열고 관찰 (요소 번호 확인)
node cheliped-cli.mjs '[{"cmd":"goto","args":["<URL>"]},{"cmd":"observe"}]'
# 2) 검색어 입력 + 버튼 클릭
node cheliped-cli.mjs '[{"cmd":"fill","args":[3,"위안부"]},{"cmd":"click","args":[4]},{"cmd":"observe"}]'
# 3) 목록 스크래핑 + 다음 페이지
node cheliped-cli.mjs '[{"cmd":"scrape"},{"cmd":"click","args":[12]},{"cmd":"scrape"}]'
```

## 판정 규칙
1. 먼저 `scrape_plan(url)`로 robots.txt를 확인 — Disallow에 걸리면 브라우저 스크래핑만 사용.
2. robots 허용이어도 목록이 비면 JS 렌더 → 브라우저 스크래핑.
3. 스크래핑 결과도 반드시: 식별자·제목·연대·URL·권리등급 표로 정리 후 report_template로 HTML화.
4. 과도한 요청 금지 — 지연을 두고, 대량 수집은 사이트 이용약관·저작권을 준수.
