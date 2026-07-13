# korea-archive MCP 서버 — AI 에이전트 장착 가이드

Claude Desktop / Claude Code / Cowork 등 MCP 지원 에이전트에 한국 기록 발굴 도구 **20종**을 장착합니다.

> 이 디렉터리(`mcp/server.py`)는 **개발·로컬 실행용 진입점**입니다. 플러그인/원격 커넥터로 설치하면
> 배포본(`plugins/korea-archive/servers/server.py`, Vercel 호스팅)이 동일한 20개 도구를 제공하므로
> Python 설치가 필요 없습니다. 로컬에서 직접 돌릴 때만 아래 절차를 따르세요.

## 도구 (20종)

**해외 (7)**
| 도구 | 기능 | 키 |
|---|---|---|
| `tna_search` | 영국 TNA Discovery 검색 (참조코드 자동 정확구) | 불요 |
| `tna_adjacent_mine` | 인접 확장(Adaptive Mining) — 승격 후보 발굴 | 불요 |
| `nara_search` | NARA 카탈로그 검색 (RG 교차·영상 한정) | `NARA_API_KEY` |
| `ia_search` / `ia_metadata` | archive.org 검색·아이템 파일 확인 | 불요 |
| `gallica_search` | 프랑스 BnF Gallica (구한말 선교사·외교 문헌) | 불요 |
| `europeana_search` | 유럽 58개국 4,000+ 기관 통합검색 | 데모 키 기본(선택 `EUROPEANA_API_KEY`) |

**국내 (8)** — 서버 사이드 자동 브라우징
| 도구 | 기능 | 키 |
|---|---|---|
| `nedb_search` | 국사편찬위 한국사DB (1차 사료 1,100만+) | 불요 |
| `archives_search` | 국가기록원 OpenAPI | `ARCHIVES_API_KEY`(data.go.kr 15000153) |
| `nlk_search` | 국립중앙도서관 6개 컬렉션 | 선택 `NLK_API_KEY` |
| `seoul_archives_search` | 서울기록원 카탈로그 | 불요 |
| `foia_search` | 정보공개포털(원문정보공개) | 불요 |
| `local_gov_search` | 서울정보소통광장·서울시교육청·경남기록원 | 불요 |
| `warmemo_search` | 전쟁기념관 아카이브 | 불요 |
| `scrape_plan` | robots 확인 + 브라우저 도구 폴백 안내 | 불요 |

**유틸 (5)**
| 도구 | 기능 | 키 |
|---|---|---|
| `query_bank` | 검증된 쿼리 세트 (44그룹·RG·TNA) + 국내 3대 부정합 키워드셋 252종 (`domestic`) | 불요 |
| `judge_rights` | 권리 등급 자동 초기판정 (§30) | 불요 |
| `report_template` | 조사 결과를 HTML 발굴 보고서로 생성 | 불요 |
| `cross_search` | 여러 아카이브 한 쿼리로 동시 교차수집·병합 (상호보완) | 해외 불요 |
| `source_profile` | 기관 자료·이용·활용구조 3층 프로파일 (해외 5+국내 6) | 불요 |

## 설치 (로컬 직접 실행)

```bash
pip install mcp        # (requirements.txt)
```

### Claude Desktop (claude_desktop_config.json)
```json
{
  "mcpServers": {
    "korea-archive": {
      "command": "python",
      "args": ["<설치경로>/korea-archive-project/mcp/server.py"],
      "env": {
        "NARA_API_KEY": "발급키(선택)",
        "EUROPEANA_API_KEY": "발급키(선택)",
        "ARCHIVES_API_KEY": "발급키(선택)",
        "NLK_API_KEY": "발급키(선택)"
      }
    }
  }
}
```

### Claude Code
```bash
claude mcp add korea-archive -- python <설치경로>/korea-archive-project/mcp/server.py
```

## 사용 예 (에이전트에게 그대로 말하기)
- "TNA에서 `FO 371 FK1015` 검색해줘" → tna_search
- "`WO 281/1206` 주변 ±10을 마이닝해서 승격 후보 찾아줘" → tna_adjacent_mine
- "Gallica에서 `Corée missionnaires` 찾아줘" → gallica_search
- "서울정보소통광장에서 위안부 결재문서 찾아줘" → local_gov_search
- "전쟁기념관에서 인천상륙작전 자료 찾아줘" → warmemo_search
- "구한말 쿼리 세트 보여줘" → query_bank("G-07")
- "RG 242 노획필름의 권리 등급은?" → judge_rights

주의: 요청 간격을 존중하고(과속 금지), NARA 키는 월 10,000쿼리 한도입니다.
