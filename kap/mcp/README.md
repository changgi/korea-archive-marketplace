# korea-archive MCP 서버 — AI 에이전트 장착 가이드

Claude Desktop / Claude Code / Cowork 등 MCP 지원 에이전트에 한국 기록 발굴 도구 7종을 장착합니다.

## 도구
| 도구 | 기능 | 키 |
|---|---|---|
| `tna_search` | 영국 TNA Discovery 검색 (참조코드 자동 정확구) | 불요 |
| `tna_adjacent_mine` | 인접 확장(Adaptive Mining) — 승격 후보 발굴 | 불요 |
| `nara_search` | NARA 카탈로그 검색 (RG 교차·영상 한정) | `NARA_API_KEY` |
| `ia_search` / `ia_metadata` | archive.org 검색·아이템 파일 확인 | 불요 |
| `query_bank` | 검증된 쿼리 세트 조회 (44그룹·RG 매핑·TNA 레이어) | 불요 |
| `judge_rights` | 권리 등급 자동 초기판정 (§30) | 불요 |

## 설치

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
      "env": { "NARA_API_KEY": "발급키(선택)" }
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
- "구한말 쿼리 세트 보여줘" → query_bank("G-07")
- "RG 242 노획필름의 권리 등급은?" → judge_rights

주의: 요청 간격을 존중하고(과속 금지), NARA 키는 월 10,000쿼리 한도입니다.
