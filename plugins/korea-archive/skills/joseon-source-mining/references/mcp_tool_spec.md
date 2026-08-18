# korea-archive MCP 서버 확장 명세 — 조선 사료 심층 판독 도구 11종

기존 `korea-archive` MCP 서버(`https://korea-archive-mcp.vercel.app/api/mcp`)에
추가할 도구 명세다. 기존 도구(`nedb_search`, `archives_search` 등)가 **검색**에
집중한다면, 아래 도구는 **본문 판독과 제도 재구성**을 담당한다.

구현은 `references/access_recipes.md`의 함수를 그대로 감싸면 된다.

---

## 설계 원칙

1. **좌목 필터를 서버가 한다** — 클라이언트가 601건을 받아 492건을 버리게 하지 않는다
2. **경로 판별을 서버가 한다** — `jlaw` 접두면 `item/level.do`, 아니면 `level.do`
3. **형제 조 스캔을 1급 도구로 둔다** — 가장 자주 놓치는 실수이므로 도구로 승격
4. **부재를 반환값에 담는다** — "0건"이 아니라 "법전 미수록"이라는 판정을 준다
5. **원문 제공 여부를 항상 함께 반환한다** — 인용 가능성 판단에 필수

---

## 1. `joseon_law_search`

법전·편람 조문 검색 (조선시대법령자료).

```json
{
  "name": "joseon_law_search",
  "description": "조선 법전·편람(經國大典·續大典·大典通編·大典會通·六典條例·萬機要覽·受敎輯錄·度支志 등) 조문을 검색한다. 한자 검색이 기본이며 서명·편·조 구조를 함께 반환한다. '경국대전에 OO 조항이 있나', '속대전 舟車', '만기요람 漕轉' 같은 요청에 사용.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query":     {"type": "string", "description": "검색어. 한자 권장(예: 執籌, 添載, 津夫)"},
      "max_results": {"type": "integer", "default": 50, "maximum": 200}
    },
    "required": ["query"]
  }
}
```

**반환**

```json
{
  "total": 22,
  "results": [
    {
      "level_id": "jlawa_101_0060_0010_0020",
      "source": "經國大典",
      "section": "刑典 奴婢決訟定限",
      "excerpt": "永樂甲午年 노비 辨正 시 未産所生 執籌者는…",
      "url": "https://db.history.go.kr/id/jlawa_101_0060_0010_0020",
      "original_text_available": true
    }
  ],
  "note": "법전·편람은 한문 원문이 제공되므로 인용 가능(표점은 DB 형태)"
}
```

---

## 2. `joseon_record_search`

등록류 검색 + **좌목 자동 필터**.

```json
{
  "name": "joseon_record_search",
  "description": "비변사등록 등 등록류를 검색한다. 회의 참석 명단인 座目을 자동으로 걸러 실질 기사만 반환하며, 필터 전후 건수를 함께 알려준다. 검색 건수를 분포 지표로 쓰기 전에 반드시 이 도구를 쓸 것.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query":        {"type": "string"},
      "include_jwamok": {"type": "boolean", "default": false,
                        "description": "true면 座目도 포함"},
      "date_from":    {"type": "string", "description": "YYYY 또는 YYYY-MM-DD"},
      "date_to":      {"type": "string"},
      "max_results":  {"type": "integer", "default": 100}
    },
    "required": ["query"]
  }
}
```

**반환**

```json
{
  "total_hits": 601,
  "jwamok_filtered": 492,
  "substantive": 109,
  "results": [
    {"level_id": "bb_187r_001_01_0710",
     "date": "1798-01-26",
     "title": "舟橋司 船隻의 加載에 대해 논의하는 備邊司의 啓",
     "url": "https://db.history.go.kr/id/bb_187r_001_01_0710"}
  ],
  "warning": "검색 601건 중 492건이 座目입니다. 건수를 주제 중요도 지표로 쓰지 마십시오.",
  "note": "등록류는 국역만 제공됩니다. 한문 인용이 필요하면 원문 열람 경로를 국편에 문의하십시오."
}
```

---

## 3. `joseon_item_read`

본문 조회. 경로 자동 판별.

```json
{
  "name": "joseon_item_read",
  "description": "levelId로 조문·기사 본문을 조회한다. 법령(jlaw*)과 등록류를 자동 판별해 올바른 경로로 접근한다. 본문이 비어 있으면 '미공개'인지 '파싱 실패'인지 구분해 반환한다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "level_id":  {"type": "string"},
      "max_chars": {"type": "integer", "default": 20000}
    },
    "required": ["level_id"]
  }
}
```

**반환**

```json
{
  "level_id": "bb_200r_001_03_0200",
  "title": "湖南 三漕倉 漕軍의 身布代錢을 舟橋司로 보내도록 할 것을 청하는 備邊司의 啓",
  "body": null,
  "body_status": "not_published",
  "url": "https://db.history.go.kr/id/bb_200r_001_03_0200",
  "note": "항목은 정상 존재하고 URL도 유효하나 본문(국역·원문)이 공개되지 않았습니다. 재시도로 해결되지 않으며, 필요 시 국사편찬위원회에 문의하십시오."
}
```

`body_status` 값: `ok` · `not_published` · `parse_failed` · `not_found`

**이 구분이 이 도구의 존재 이유다.** '도달하지 못했다'와 '공개되지 않았다'는 다르다.

---

## 4. ★ `joseon_sibling_scan`

**형제 조 전수 스캔.** 이 서버에서 가장 중요한 도구.

```json
{
  "name": "joseon_sibling_scan",
  "description": "편(編)·조(條) 구조 사료에서 형제 조를 전수 조회한다. 총론만 읽고 끝내는 실수를 방지하는 도구로, 법전·편람 조문을 하나라도 열었다면 반드시 이어서 호출할 것. 萬機要覽 舟橋 편에서 [津路]·[員額]이, 六典條例 舟橋司 편에서 시공 시방·배정 산식이 이 방식으로 발견되었다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "level_id": {"type": "string", "description": "이미 확인한 조의 levelId"},
      "span":     {"type": "integer", "default": 12,
                   "description": "조회할 형제 조 개수"}
    },
    "required": ["level_id"]
  }
}
```

**반환**

```json
{
  "parent": "jlawb_400_0050_0090",
  "siblings": [
    {"level_id": "…_0010", "head": "總例",   "chars": 890,  "preview": "…"},
    {"level_id": "…_0020", "head": "津路",   "chars": 96,   "preview": "宣陵·靖陵…竝鷺梁"},
    {"level_id": "…_0030", "head": "舟橋船", "chars": 640,  "preview": "橋排船三十八隻…"},
    {"level_id": "…_0040", "head": "員額",   "chars": 210,  "preview": "都監官一員…"}
  ],
  "found": 4,
  "note": "요청한 조 외에 3개가 더 있습니다. 전부 확인하십시오."
}
```

---

## 5. `kyujanggak_search`

규장각 검색 — **목록과 해제를 동시에**.

```json
{
  "name": "kyujanggak_search",
  "description": "서울대 규장각한국학연구원 소장 자료를 검색한다. 목록(searchArea=10)과 해제(searchArea=20)를 동시에 조회하는데, 절목·사목류는 상위 서명 아래 편차로 들어가 목록 검색만으로는 나오지 않기 때문이다. 舟橋指南이 이 방식으로 발견되었다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string"},
      "area":  {"type": "string", "enum": ["both", "list", "abstract"],
                "default": "both"}
    },
    "required": ["query"]
  }
}
```

**반환** — 청구기호 · 서명 · 책수/장수 · 판본 · 크기 · 마이크로필름 번호 ·
**원문 이미지 제공 여부** · `item_cd`(이미지 수집에 필요)

---

## 6. `kyujanggak_images`

원문 이미지 수집. **item_cd 자동 탐지**.

```json
{
  "name": "kyujanggak_images",
  "description": "규장각 원문 이미지 URL을 생성한다. item_cd(ART·ETC·DRR·FND·POL)를 자동 탐지하고, 첫 이미지를 실제로 받아 파일명 패턴을 확정한 뒤 전체 목록을 반환한다. 舟橋指南(POL) 계열은 파일명 규칙이 달라 추정하면 실패한다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "book_cd":   {"type": "string", "description": "예 GK05485"},
      "item_cd":   {"type": "string", "description": "생략 시 자동 탐지"},
      "max_pages": {"type": "integer", "default": 60}
    },
    "required": ["book_cd"]
  }
}
```

**반환**

```json
{
  "book_cd": "GK05485",
  "item_cd": "POL",
  "pattern": "GK05485_00IH_0001_{n:04d}.jpg",
  "pattern_verified": true,
  "urls": ["https://kyudb.snu.ac.kr/ImageServlet.do?…"],
  "count": 40,
  "rights": "C",
  "note": "게재는 소장기관 허가 범위 확인 필요. 복제 문의 02-880-5316"
}
```

---

## 7. `sjw_search`

승정원일기 검색 — **왕대 분포를 함께 반환**.

```json
{
  "name": "sjw_search",
  "description": "승정원일기를 검색하고 왕대별 분포를 함께 반환한다. 최초 용례가 통념보다 이르면 제도사 서사가 뒤집히므로, 분포의 앞쪽 왕대를 반드시 확인할 것. 執籌船 53건의 영조 2건이 주교사(1790)보다 58년 앞선 1731년 사례였다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query":       {"type": "string"},
      "max_results": {"type": "integer", "default": 50}
    },
    "required": ["query"]
  }
}
```

**반환**

```json
{
  "total": 53,
  "reign_distribution": {"영조": 2, "정조": 3, "순조": 19,
                          "헌종": 8, "철종": 6, "고종": 15},
  "earliest": {"reign": "영조 7년", "year": 1731, "date": "1731-06-20"},
  "results": [],
  "alert": "최초 용례가 1731년입니다. 관련 기구·제도의 성립 연대와 대조하십시오."
}
```

---

## 8. `term_origin_trace`

**어휘 연원 추적** — 제도 용어가 원래 무엇을 가리키던 말인가.

```json
{
  "name": "term_origin_trace",
  "description": "제도 용어를 법전 전체에 대조해 원래 어느 영역의 용어였는지 추적한다. 執籌는 노비 상속 분할, 抽籤은 강경 시험 용어였고 18세기에 조운으로 전용되었다. 용어의 출신을 알면 제도의 성격이 드러난다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "term":   {"type": "string"},
      "domain": {"type": "string",
                 "description": "현재 쓰이는 영역(예: 조운, 선박). 이 영역 밖의 용례를 찾는다"}
    },
    "required": ["term"]
  }
}
```

**반환**

```json
{
  "term": "執籌",
  "total_in_law": 22,
  "domains": {
    "노비 소송": 18,
    "재산 분할": 4,
    "선박·조운": 0
  },
  "representative": [
    {"source": "受敎輯錄(1543) 刑典 文記",
     "text": "부모가 나누지 않은 노비를 자녀들이 和會執籌 分衿",
     "gloss": "모여 산가지를 잡아 몫을 나눔"}
  ],
  "finding": "선박·조운 용례가 법전에 0건입니다. 이 용어는 다른 영역에서 전용되었습니다."
}
```

---

## 9. `law_presence_matrix`

**법전 수록 여부 대조표** — 부재를 데이터로 만든다.

```json
{
  "name": "law_presence_matrix",
  "description": "여러 어휘의 법전 수록 건수를 나란히 대조해 어떤 요소가 법전 밖에 있었는지 드러낸다. 부재 자체가 발견이다. 강배 어휘 14종을 대조한 결과 배·사람·나루·삯·창고는 법전 조문인데 '어느 배에 어느 노선을 줄 것인가'만 법전에 없었다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "terms": {"type": "array", "items": {"type": "string"}, "maxItems": 30}
    },
    "required": ["terms"]
  }
}
```

**반환**

```json
{
  "matrix": [
    {"term": "船價",   "count": 182, "earliest": "續大典",   "in_code": true},
    {"term": "津夫",   "count": 105, "earliest": "經國大典", "in_code": true},
    {"term": "執籌船", "count": 1,   "earliest": "度支志",   "in_code": false,
     "note": "『度支志』 「事實」은 사례·경위 편목이며 법조문이 아님"}
  ],
  "absent": ["執籌船"],
  "finding": "執籌船은 법전에 오르지 못한 관행입니다. 제도사를 법전으로만 재구성하면 존재하지 않습니다."
}
```

---

## 10. `link_verify`

인용 링크 전수 검증 — **200과 본문 존재를 분리**.

```json
{
  "name": "link_verify",
  "description": "보고서가 인용한 levelId와 URL을 전수 조회해 유효성을 검증한다. HTTP 200과 본문 존재를 별개로 판정하며, 이상 항목은 원인(엔티티 미해제·비동기 응답·POST 전용·서버 지연·본문 미공개)까지 분류한다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "level_ids": {"type": "array", "items": {"type": "string"}},
      "urls":      {"type": "array", "items": {"type": "string"}}
    }
  }
}
```

**반환**

```json
{
  "level_ids": {"checked": 45, "ok": 44,
                "issues": [{"id": "bb_200r_001_03_0200",
                            "http": 200, "body": false,
                            "cause": "not_published"}]},
  "urls": {"checked": 71, "ok": 65,
           "issues": [
             {"cause": "html_entity", "count": 3,
              "note": "&amp; 미해제. 해제 후 정상"},
             {"cause": "async_202", "count": 1, "note": "TNA 비동기 응답"},
             {"cause": "server_slow", "count": 6, "note": ":8443 포트 지연"},
             {"cause": "post_only", "count": 1, "note": "검색 URL은 GET 재현 불가"}
           ]},
  "dead_links": 0,
  "note": "이상 11건은 전부 조회 방식 문제이며 자료 소멸이 아닙니다."
}
```

---

## 11. `consistency_audit`

산출물 정합 점검.

```json
{
  "name": "consistency_audit",
  "description": "여러 산출물에 핵심 어휘가 실제로 수록되었는지 매트릭스로 점검하고 수치 표기 불일치를 찾는다. 긴 조사를 여러 회차로 키울 때 앞 지면과 부속 산출물이 뒤처지는 문제를 잡는다. 판단하지 않고 유무만 보며, 출력의 '미수록'은 오류 목록이 아니라 판단 목록이다.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "artifacts": {"type": "array",
                    "items": {"type": "object",
                              "properties": {"name": {"type": "string"},
                                             "content": {"type": "string"}}}},
      "keywords":  {"type": "array", "items": {"type": "string"}},
      "numeric_patterns": {"type": "array", "items": {"type": "string"},
                           "description": "여러 파일에 나타나는 수치의 정규식"}
    },
    "required": ["artifacts", "keywords"]
  }
}
```

**반환** — 매트릭스 · 미수록 목록 · 수치 불일치 · 그리고 반드시 이 문구:

> 미수록이 곧 오류는 아닙니다. 산출물의 성격상 담지 않는 것이 맞을 수 있습니다.
> 이 표는 '판단하라'는 목록이지 '고쳐라'는 목록이 아닙니다.

---

## 도구 호출 순서 (권장)

```
1. joseon_law_search          법전에 근거가 있는가
2. joseon_sibling_scan        ★ 조를 열었으면 반드시 형제 조 확인
3. law_presence_matrix        여러 어휘 대조 — 부재를 발견
4. term_origin_trace          핵심 용어의 출신
5. joseon_record_search       실제 운영 기록(좌목 필터)
6. joseon_item_read           본문 판독 (배치)
7. sjw_search                 최초 용례·왕대 분포 — 연대 검증
8. kyujanggak_search          원전 소재 확인 (목록+해제)
9. kyujanggak_images          원문 이미지
10. link_verify               마무리 — 인용 유효성
11. consistency_audit         마무리 — 산출물 정합
```

**2번을 건너뛰면 조사의 절반을 놓친다.** 한강 조사에서 두 번 놓쳤다.

---

## 서버 측 구현 메모

- 모든 요청은 **POST**다. GET으로 구현하면 404/400이 난다
- 한자 검색은 `chinessChar=on` 필수
- 요청 간격 **0.4초 이상**, 실패 시 20초 후 1회 재시도
- 규장각은 `web_fetch`류에서 ROBOTS_DISALLOWED가 나지만 **서버 직접 요청은 200**
- `joseon_sibling_scan`은 조회가 최대 12회이므로 **응답 지연을 감안**해 타임아웃을 넉넉히
- 반환 JSON에 `note`/`warning`/`alert`를 적극 사용한다. **이 서버의 가치는
  데이터가 아니라 판정에 있다** — "601건"이 아니라 "492건이 좌목입니다"를 준다
