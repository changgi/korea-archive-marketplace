# korea-archive MCP — 도구 확장 명세 v2

기존 20개 도구(archives_search·cross_search·europeana_search·gallica_search·ia_search·judge_rights·nara_search·nedb_search·nlk_search·query_bank·report_template·tna_search·tna_adjacent_mine 등)에 **더할 것**과 **고칠 것**.

---

## 신규 도구 5종

### 1. `query_scorecard` — 검색어 성적표 조회
검색어를 넣기 **전에** 그 검색어가 쓸 만한지 알려준다.

```json
{
  "name": "query_scorecard",
  "description": "검색어의 실측 성적(건수·정확도·함정)을 조회한다. 새 검색어를 넣기 전에 먼저 호출하면 노이즈를 피할 수 있다. 유사 검색어의 개선안도 제안한다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "확인할 검색어"},
      "source": {"type": "string", "enum": ["europeana","gallica","nara","tna","domestic","any"], "default": "any"}
    },
    "required": ["query"]
  }
}
```
**반환**: `{verdict: "good"|"noisy"|"zero"|"unknown", count, traps[], better_alternatives[], rationale}`

**핵심 로직**
- 사전 등재 검색어는 실측치 반환
- 미등재면 규칙 기반 판정:
  - 단어 4개 이상 → `zero` 경고
  - 나라 이름 단독(`Corea`·`Korea`) → `noisy`, 도시 이름 대안 제시
  - 일반명사(`album`·`photograph`·`document`) 포함 → `noisy`
  - 학명+인명 혼합 → `zero` 경고
  - 인명 2개 이상 → `zero` 경고, "하나씩" 안내

---

### 2. `person_key_expand` — 인명 열쇠 확장
한 이름을 넣으면 **각국 표기 변형 + 관련 색인 구간**을 돌려준다.

```json
{
  "name": "person_key_expand",
  "description": "인명을 넣으면 각국 표기 변형과 해당 아카이브의 인물 색인 구간을 반환한다. 한국인 이름은 로마자 변형(Lee/Yi/Rhee 등)을, 서양인 이름은 학명 종소명 형태(fauriei 등)를 포함한다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "type": {"type": "string", "enum": ["korean","western","auto"], "default": "auto"}
    },
    "required": ["name"]
  }
}
```
**반환**: `{variants[], index_cells[{naid, range, institution}], caveats[], suggested_queries[]}`

**내장 데이터**
- 성씨 변형표 (이=Lee·Yi·Rhee·Ri·Li, 김=Kim·Gim, 박=Park·Pak·Bak…)
- Index to Personalities 구간 매핑 (NAID 109921404~109921751)
- Personalities 알파벳 색인 (NAID 102702358~102702418)
- 채집자 종소명 + **정확도 경고**(oldhamii는 대만분 다수 등)

---

### 3. `decode_identifier` — 식별자 해독
번호를 넣으면 무슨 뜻인지 + **옆에 뭐가 있을지** 알려준다.

```json
{
  "name": "decode_identifier",
  "description": "아카이브 식별자(NARA 참조코드·NAID·TNA 참조코드·Gallica ark·표본번호 등)를 해독해 구성 요소와 인접 탐색 후보를 반환한다. 한 건을 찾은 뒤 서랍 전체를 여는 데 사용한다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "identifier": {"type": "string"},
      "system": {"type": "string", "enum": ["auto","nara_ref","naid","tna","gallica_ark","specimen","decimal"], "default": "auto"}
    },
    "required": ["identifier"]
  }
}
```
**반환**: `{system, parts[{segment, meaning}], neighbors[], strategy, warnings[]}`

**핵심 로직**
- `127-GR-223-A164360` → 기록군/시리즈/주제묶음/낱건 분해 + **224·225 제안**
- NAID → **±1과 ±3 모두** 후보 생성 (계열마다 간격이 다르므로)
- `btv1b`/`bpt6k` → 도판·필사 / 인쇄본 판정
- `FO 881/9951X` → **X 접미어 = Missing at transfer 경고** + 남은 짝 제안
- `895.xx` → 주제 코드 표 조회 + **894 경계 넘김 경고**
- `E00677904` → 기관 약자 + 연속 번호 후보

---

### 4. `crosscheck_plan` — 대조 계획 생성
주제를 넣으면 **국내 먼저 → 해외** 순서의 실행 계획을 만든다.

```json
{
  "name": "crosscheck_plan",
  "description": "조사 주제를 넣으면 국내 연구사 → 번역본 확인 → 해외 원본 → 국내 원사료 대조 순서의 실행 계획과 각 단계의 구체적 검색어를 생성한다. 해외부터 뒤지는 실수를 막는다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "topic": {"type": "string"},
      "period": {"type": "string", "description": "예: 1866, 1900s, 조선후기"},
      "known_sources": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["topic"]
  }
}
```
**반환**: `{steps[{order, action, queries[], targets[], why}], calendar_warning, domestic_holdings[]}`

**반드시 포함**: 1896.1.1 이전 주제면 **음력/양력 경고**를 항상 붙인다.

---

### 5. `preservation_referral` — 목록에 올리기 안내
미기술 자료를 만났을 때 어디로 연결할지 알려준다.

```json
{
  "name": "preservation_referral",
  "description": "목록에 없는 자료(개인 소장·미기증)를 발견했을 때 기증·사본수집 경로와 연락처를 안내한다. 기증하지 않고 사본만 남기는 방법을 우선 제시한다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "material_type": {"type": "string", "description": "예: 필사본 일기, 사진첩, 편지"},
      "period": {"type": "string"},
      "owner_willing_to_donate": {"type": "boolean", "default": false}
    },
    "required": ["material_type"]
  }
}
```
**반환**: `{primary_route, institutions[{name, contact, accepts, method}], copy_collection_note, checklist[]}`

**핵심**: `owner_willing_to_donate=false`여도 **사본수집** 경로를 제시할 것. 이게 이 도구의 존재 이유다.

---

## 기존 도구 개선 3건

### `query_bank` 확장
현재 "validated discovery keywords" 반환. 여기에 **성적표 필드**를 추가한다.
```
{keyword, source, measured_count, verdict, traps[], date_measured}
```
`search_scorecard.md`의 30여 건을 시드로 적재.

### `europeana_search` — 자동 번역 표시 ★
현재 입력을 임의 변환하면서 **변환 사실을 결과에 표시하지 않는다**(`Corée` → `Korea` 실증).
→ 반환에 반드시 포함:
```
{query_as_submitted, query_after_transform, transform_applied: bool}
```
**이건 정확성 문제다.** 사용자가 프랑스어로 찾는다고 믿는데 영어로 검색되고 있다.

### `nedb_search` — 실패 처리
HTTP 400이 잦다. 실패 시 현재는 에이전트 지시문을 반환하는데, **공식 검색 URL과 함께 "대체 경로" 구조화 응답**으로 바꾸는 편이 낫다.

---

## 권장 호출 순서

```
crosscheck_plan(주제)            ← 순서부터 잡는다
  → query_scorecard(검색어)      ← 넣기 전에 확인
  → nlk_search / archives_search ← 국내 먼저
  → europeana_search / gallica_search / nara_search / tna_search
  → decode_identifier(찾은 번호)  ← 서랍 열기
  → person_key_expand(발견한 인명) ← 컬렉션 전체로
  → cross_search(국내 대조)
  → judge_rights → report_template
  → preservation_referral (미기술 자료 발견 시)
```
