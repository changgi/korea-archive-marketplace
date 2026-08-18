# korea-archive-discovery v2 — 스킬 + MCP 확장 패키지

2026년 8월 「Chosen과 Joseon 사이」 강연 준비 과정에서 **79회 검색 · 20개국 · 1672~2003년**을 실측하며 얻은 방법론을 재현 가능한 형태로 묶은 것.

## 왜 v2인가

기존 `korea-archive-discovery`는 **1860~1960 영상 중심**이었다. 이번 확장으로:

- 시간 범위 **1672~2003** (하멜 표류기 독일어판 ~ 부산항 해도)
- 소장국 **5 → 20개국** (유럽 통합검색·프랑스 국립도서관·각국 식물원 포함)
- 자료 유형에 **표본·훈장·판화·필사 지도** 추가
- **인명 열쇠 전략** — 지명보다 정확한 검색축
- **학명 검색** — 철자가 하나뿐인 유일한 열쇠
- **검색어 성적표** — 실측 30여 건, 건수↔정확도 반비례 규칙
- **열한 번째 벽(음력/양력)** 추가
- **국내외 대조 절차** — 해외부터 뒤지는 실수를 막는 순서
- **기증·사본수집 경로** — 발굴에서 보존으로

## 구성

```
SKILL.md                              스킬 본문 (v2)
references/
  search_scorecard.md                 검색어 성적표 — 실측 30여 건
  person_keys.md                      인명 열쇠 전략 + 색인 구간 지도
  place_and_taxon_keys.md             지명 변형 + 학명(coreana/koreana)
  identifier_decoding.md              식별자 8체계 해독 + 옆 훑기
  eleven_walls.md                     열한 겹의 벽 + 두 가지 사라짐
  european_archives.md                20개국 기관 지도 + 언어별 사전
  crosscheck_protocol.md              대조 순서 + 목록에 올리는 법
  validation_shinmiyangyo.md          검증 사례 — 절차를 그대로 따라간 기록
  query_cheatsheet.md                 (기존 유지)
mcp/
  tools_spec.md                       MCP 도구 명세 (신규 5 + 개선 3)
  korea_archive_tools.py              신규 5종 구현 (순수 파이썬, 테스트 통과)
```

## 설치

### 스킬로 쓰기
```bash
cp -r korea-archive-discovery ~/.claude/skills/
# 또는 플러그인 디렉토리에 배치
```

### MCP 서버에 붙이기
```python
from korea_archive_tools import TOOLS
# TOOLS = {"query_scorecard": ..., "person_key_expand": ...,
#          "decode_identifier": ..., "crosscheck_plan": ...,
#          "preservation_referral": ...}
```
각 도구의 inputSchema는 `mcp/tools_spec.md`에 JSON으로 있다.

동작 확인:
```bash
python3 mcp/korea_archive_tools.py
```

## 신규 MCP 도구 5종

| 도구 | 언제 |
|---|---|
| `query_scorecard` | 검색어를 **넣기 전에** 성적 확인 |
| `person_key_expand` | 인명 → 각국 표기 변형 + 색인 구간 |
| `decode_identifier` | 번호 → 구성 요소 + 인접 탐색 후보 |
| `crosscheck_plan` | 주제 → 국내 먼저 순서의 실행 계획 |
| `preservation_referral` | 미기술 자료 발견 시 → 기증·사본수집 경로 |

## 기존 도구 개선 요청 3건

1. **`europeana_search`** — 입력을 자동 번역하면서 그 사실을 표시하지 않는다(`Corée`→`Korea` 실증). `query_as_submitted` / `query_after_transform` 필드를 추가해야 한다. **정확성 문제다.**
2. **`query_bank`** — 성적표 필드(measured_count·verdict·traps) 추가
3. **`nedb_search`** — HTTP 400 잦음. 실패 시 구조화된 대체 경로 반환

## 검증

만든 뒤 **손대지 않은 주제(신미양요 1871)**로 절차를 그대로 따라가 확인했다.
- 순서를 지키니 **국가기록원이 이미 가진 1871년 사진 20건**을 먼저 만났다
- 2단계 번역본의 **병기 영문 제목**이 3단계 검색어를 줬다
- `Korea 1871 Expedition`(4,054건 무관) → **`Rodgers Colorado Corea`**(전투 당일 항해일지)
- **결함 1건 발견·수정**: 3단계가 한글+영어 혼합 쿼리를 만들던 문제

전체 기록은 `references/validation_shinmiyangyo.md`.

## 이 패키지의 원칙

- **실측만 싣는다.** 추정은 "추정"이라고 쓴다.
- **실패도 싣는다.** 0건 로그가 다음 사람의 시간을 아낀다.
- **자기 조언을 반증한 것도 싣는다.** "도시 이름이 안전하다"는 조언은 부산에서 틀렸다.
- **확인한 것과 제목만 본 것을 구분한다.**

## 재현

`references/search_scorecard.md`의 모든 검색어는 그대로 다시 넣어볼 수 있다. 건수가 달라졌다면 그것 자체가 새 정보다.
