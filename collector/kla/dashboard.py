# -*- coding: utf-8 -*-
"""수집 현황 대시보드 — §27 KPI 표 대응. 수집대장 CSV → 자립형 HTML."""
from __future__ import annotations
import html, time

CSS = """body{font-family:'Malgun Gothic',sans-serif;background:#f5f6f9;color:#1e2530;margin:0;line-height:1.6}
.hero{background:linear-gradient(135deg,#0c1a38,#1f3f7a);color:#fff;padding:34px 28px}
.hero h1{margin:0;font-size:22px}.hero p{color:#c6d2e8;margin:6px 0 0;font-size:13px}
main{max-width:1060px;margin:0 auto;padding:20px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:14px 0}
.kpi{background:#fff;border:1px solid #e3e7ee;border-top:3px solid #c8a24a;border-radius:10px;padding:14px;text-align:center}
.kpi .n{font-size:26px;font-weight:900;color:#0f2044;display:block}.kpi .l{font-size:12px;color:#5a6472}
table{width:100%;border-collapse:collapse;background:#fff;font-size:12.5px;margin:12px 0}
th{background:#0f2044;color:#fff;padding:8px;text-align:left}td{padding:7px 8px;border-bottom:1px solid #e3e7ee;vertical-align:top}
tr:nth-child(even) td{background:#f8fafc}
.b{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:99px}
.bA{background:#e6f4ee;color:#1f6b4a}.bB{background:#e8f1fb;color:#1f5a99}.bC{background:#f5ead0;color:#8a6a1e}.bD{background:#fbeaec;color:#a12f3a}
h2{color:#0f2044;font-size:17px;margin:22px 0 8px}"""

def build(ledger, out_path: str):
    s = ledger.stats()
    rc = s["rights"]
    rows = []
    for r in ledger.rows:
        rows.append(f"""<tr><td>{r['collection_id']}</td>
<td><b>{html.escape(r['title_orig'][:60])}</b><br><span style="color:#5a6472">{html.escape(r['title_ko'][:40])}</span></td>
<td>{html.escape(r['rg_series'])}<br>{html.escape(r['local_id'] or r['naid'])}</td>
<td>{r['date_content']}</td>
<td><span class="b b{r['rights_class']}">{r['rights_class']}</span></td>
<td>{r['acq_status']}</td>
<td>{'✅ '+r['checksum'][:10]+'…' if r['checksum'] else '—'}</td>
<td>{r['verified_date'] or '—'}</td>
<td>{'<a href="'+r['access_url']+'">열기</a>' if r['access_url'] else '—'}</td></tr>""")
    doc = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>KLA 수집 대시보드</title><style>{CSS}</style></head><body>
<div class="hero"><h1>🎬 KLA 영상자료 수집 대시보드 — Phase 0</h1>
<p>「글로벌 아카이브 종합 보고서 v6.5」 §27~28 준거 · 생성 {time.strftime('%Y-%m-%d %H:%M')}</p></div><main>
<div class="kpis">
<div class="kpi"><span class="n">{s['total']}</span><span class="l">인벤토리 레코드</span></div>
<div class="kpi"><span class="n">{s['with_file']}</span><span class="l">파일 확보(체크섬)</span></div>
<div class="kpi"><span class="n">{s['verified']}</span><span class="l">링크 검증 완료</span></div>
<div class="kpi"><span class="n">{rc.get('A',0)}/{rc.get('B',0)}</span><span class="l">권리 A/B (공개 가능)</span></div>
<div class="kpi"><span class="n">{rc.get('C',0)}/{rc.get('D',0)}</span><span class="l">권리 C/D (제한·불명)</span></div>
<div class="kpi"><span class="n">0원</span><span class="l">누적 지출 (Phase 0)</span></div>
</div>
<h2>수집대장 (§28 — 17필드 중 핵심 열)</h2>
<table><thead><tr><th>ID</th><th>제목</th><th>RG/식별자</th><th>연대</th><th>권리</th><th>상태</th><th>체크섬</th><th>검증일</th><th>링크</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<p style="color:#5a6472;font-size:12px">권리 등급은 §30 플로의 자동 초기판정이며 최종 확정은 담당자 서면 판정으로 한다. D등급은 공개 금지(내부 연구용).</p>
</main></body></html>"""
    with open(out_path, "w", encoding="utf-8") as f: f.write(doc)
    return out_path
