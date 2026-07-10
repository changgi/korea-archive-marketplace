#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""korea-archive MCP 서버 — 해외 한국 기록 발굴 도구를 AI 에이전트에 장착.

도구: tna_search · tna_adjacent_mine · nara_search · ia_search · ia_metadata
      query_bank · judge_rights · report_template
      nedb_search(한국사DB) · archives_search(국가기록원) · scrape_plan(cheliped 폴백) · nlk_search(국립중앙도서관) · foia_search(정보공개포털) · seoul_archives_search(서울기록원) · local_gov_search(지방 정보공개·기록원) · warmemo_search(전쟁기념관)
설치·연결 방법은 README.md 참조. 표준 의존성: pip install mcp
"""
from __future__ import annotations
import json, os, re, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for p in (_HERE, os.path.join(_HERE, "keywords")):
    if p not in sys.path: sys.path.insert(0, p)

from mcp.server.fastmcp import FastMCP
from harvester import tna as T
from harvester.util import http_json, qs
from kla.ledger import auto_rights
import keywords_common as KC
import keywords_nara as KN
import keywords_tna as KT

mcp = FastMCP("korea-archive")

def _fmt(recs: list[dict], limit: int) -> str:
    out = []
    for r in recs[:limit]:
        out.append(f"- [{r.get('local_id') or r.get('naid') or '?'}] {r.get('title','')[:110]}"
                   f" ({r.get('date','')}) {r.get('url','')}")
    return "\n".join(out) or "(0건)"

@mcp.tool()
def tna_search(query: str, max_results: int = 20) -> str:
    """영국 국립기록관(TNA) Discovery에서 한국 관련 기록 검색. 참조코드('FO 371/84053')는
    자동으로 정확구 처리. 예: 'Korea armistice', 'FO 371 FK1015', 'WO 281 Glosters'"""
    q = f'"{query}"' if re.match(r"^[A-Z]+ \d+/\d+$", query.strip()) else query
    recs = []
    for batch, total in T._search(q, page_size=min(max_results, 100), max_pages=1, sleep=0):
        recs += [T._extract(r, "mcp", query) for r in batch]
    return f"TNA 검색 '{query}' — 총 {total}건 중 {len(recs[:max_results])}건:\n" + _fmt(recs, max_results)

@mcp.tool()
def tna_adjacent_mine(reference: str, radius: int = 5) -> str:
    """인용 역추적·인접 확장(Adaptive Mining): 참조코드(예 'FO 371/84053') 주변 piece를
    순회하며 한국 관련 파일을 스코어링해 승격 후보를 찾는다. (논문 T-13, 214개 시리즈 발견 기법)"""
    m = re.match(r"([A-Z]+ \d+)/(\d+)", reference.strip())
    if not m: return "참조코드 형식 오류 — 예: FO 371/84053"
    series, piece = m.group(1), int(m.group(2))
    lines = []
    for p in range(piece - radius, piece + radius + 1):
        ref = f"{series}/{p}"
        try:
            for batch, _t in T._search(f'"{ref}"', page_size=5, max_pages=1, sleep=0):
                for r in batch:
                    rec = T._extract(r, "mine", ref)
                    if not (rec.get("local_id") or "").startswith(series): continue
                    sc = T.korea_score((rec.get("title") or "") + " " + (rec.get("description") or ""))
                    mark = "★승격후보" if sc >= 1 else "  "
                    lines.append(f"{mark} {rec['local_id']} | score={sc} | {rec['title'][:90]}")
        except Exception as e:
            lines.append(f"   {ref} | ERROR {e}")
    return f"인접 확장 {series}/{piece}±{radius}:\n" + "\n".join(lines[:60])

@mcp.tool()
def nara_search(query: str, record_group: int | None = None,
                moving_images_only: bool = False, max_results: int = 20) -> str:
    """미국 NARA 카탈로그 검색 (환경변수 NARA_API_KEY 필요 — Catalog_API@nara.gov 발급).
    record_group으로 RG 교차 정밀검색(예: 242), moving_images_only로 영상 한정."""
    key = os.environ.get("NARA_API_KEY")
    if not key: return "NARA_API_KEY 미설정 — Catalog_API@nara.gov 로 무료 발급(이름+이메일)."
    params = {"q": query, "limit": min(max_results, 100), "page": 1}
    if record_group: params["recordGroupNumber"] = record_group
    if moving_images_only: params["typeOfMaterials"] = "Moving Images"
    data = http_json("https://catalog.archives.gov/api/v2/records/search?" + qs(params),
                     headers={"x-api-key": key})
    hits = ((data.get("body") or {}).get("hits") or {})
    rows = []
    for h in (hits.get("hits") or [])[:max_results]:
        rec = (h.get("_source") or {}).get("record") or {}
        rows.append(f"- [NAID {rec.get('naId')}] {rec.get('title','')[:100]} "
                    f"| {rec.get('localIdentifier','')} | https://catalog.archives.gov/id/{rec.get('naId')}")
    total = hits.get("total", {}); total = total.get("value") if isinstance(total, dict) else total
    return f"NARA '{query}'" + (f" (RG {record_group})" if record_group else "") + f" — 총 {total}건:\n" + ("\n".join(rows) or "(0건)")

@mcp.tool()
def ia_search(query: str, max_results: int = 15) -> str:
    """archive.org 고급 검색. 예: 'identifier:111-adc*', 'collection:universal_newsreels AND korea',
    'mediatype:movies AND (keijo OR chosen)'"""
    import urllib.parse
    data = http_json("https://archive.org/advancedsearch.php?q=" + urllib.parse.quote(query) +
                     f"&fl[]=identifier&fl[]=title&fl[]=date&rows={max_results}&output=json")
    docs = (data.get("response") or {}).get("docs") or []
    nf = (data.get("response") or {}).get("numFound")
    return f"archive.org '{query}' — 총 {nf}건:\n" + "\n".join(
        f"- {d.get('identifier')} | {str(d.get('title'))[:90]} | https://archive.org/details/{d.get('identifier')}"
        for d in docs) if docs else f"archive.org '{query}' — 0건"

@mcp.tool()
def ia_metadata(identifier: str) -> str:
    """archive.org 아이템 메타데이터·파일 목록 확인 (다운로드 전 원본 파일·크기 파악)."""
    data = http_json(f"https://archive.org/metadata/{identifier}")
    md = data.get("metadata") or {}
    files = [f for f in (data.get("files") or []) if f.get("source") == "original"][:10]
    return (f"제목: {md.get('title')}\n설명: {str(md.get('description'))[:300]}\n"
            f"연대: {md.get('date')} | 라이선스: {md.get('licenseurl') or md.get('rights') or '표기 없음'}\n"
            "원본 파일:\n" + "\n".join(f"- {f['name']} ({int(f.get('size',0))/1e6:.1f}MB)" for f in files))

@mcp.tool()
def query_bank(topic: str = "list") -> str:
    """검증된 한국 기록 발굴 쿼리 세트 조회. topic: 'list'(그룹 목록) 또는 그룹ID
    (예 'G-07' 구한말, 'G-08' 일제강점기, 'G-17' 간접키워드, 'N-05' NARA 시리즈, 'RG' 교차매핑, 'TNA' 레이어)"""
    if topic == "list":
        lines = [f"{gid}: {ko} ({len(kws)}개)" for gid, ko, _en, _d, kws in KC.COMMON_GROUPS]
        lines += [f"{gid}: {ko} ({len(kws)}개)" for gid, ko, _en, kws in KN.NARA_GROUPS]
        lines += ["RG: NARA 28개 Record Group 교차 매핑", "TNA: 14 전략 레이어 (1,222 쿼리)"]
        return "쿼리 뱅크 그룹:\n" + "\n".join(lines)
    for gid, ko, _en, _d, kws in KC.COMMON_GROUPS:
        if gid == topic: return f"{gid} {ko}:\n" + "\n".join(f"- {k}" for k in kws)
    for gid, ko, _en, kws in KN.NARA_GROUPS:
        if gid == topic: return f"{gid} {ko}:\n" + "\n".join(f"- {k}" for k in kws)
    if topic.upper() == "RG":
        return "NARA RG 교차 매핑:\n" + "\n".join(
            f"- RG {rg}: {d} → {', '.join(kws)}" for rg, (d, kws) in KN.RG_MAP.items())
    if topic.upper() == "TNA":
        return "TNA 레이어:\n" + "\n".join(
            f"- {lid} ({st}) {len(qs_)}쿼리 — 예: {qs_[0]}" for lid, st, qs_ in KT.generate())
    return "해당 그룹 없음 — topic='list'로 목록 확인"

@mcp.tool()
def judge_rights(rg_series: str, title: str = "", archive: str = "") -> str:
    """권리 등급 자동 초기판정 (보고서 §30 플로 1~3단계). A/B=공개가능, C=허가필요, D=지위불명.
    ※ 최종 확정은 사람이 §30 5단계로 서면 판정할 것."""
    cls, note = auto_rights({"rg_series": rg_series, "title_orig": title, "archive": archive})
    return f"등급: {cls}\n근거: {note}\n※ 자동 초기판정 — 공개 전 수동 확정 필수, D등급 공개 금지"


@mcp.tool()
def gallica_search(query: str, max_results: int = 15) -> str:
    """프랑스 국립도서관 Gallica 검색 (SRU API, 키 불요). 프랑스어 키워드 사용 —
    'Corée'(한국), 'guerre de Corée'(한국전쟁), 'Séoul', 'Tchosen'. 구한말 프랑스
    선교사·외교 문헌과 사진의 보고. 예: gallica_search('Corée missionnaires')"""
    import urllib.parse, urllib.request, xml.etree.ElementTree as ET
    q = urllib.parse.quote(f'gallica all "{query}"' if '"' not in query else f'gallica all {query}')
    url = (f"https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2"
           f"&query={q}&maximumRecords={min(max_results,50)}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        root = ET.fromstring(r.read().decode("utf-8", "replace"))
    ns = {"srw": "http://www.loc.gov/zing/srw/", "dc": "http://purl.org/dc/elements/1.1/"}
    total = root.find(".//srw:numberOfRecords", ns)
    lines = []
    for rec in root.findall(".//srw:record", ns)[:max_results]:
        def g(tag):
            e = rec.find(f".//dc:{tag}", ns)
            return (e.text or "").strip() if e is not None and e.text else ""
        lines.append(f"- {g('title')[:100]} ({g('date')}) [{g('type')[:20]}] {g('identifier')}")
    return (f"Gallica '{query}' — 총 {total.text if total is not None else '?'}건:\n"
            + ("\n".join(lines) or "(0건)")
            + "\n팁: 프랑스어 변형 — Corée·Coréens·Séoul·Fusan·guerre de Corée·Tchosen")

@mcp.tool()
def europeana_search(query: str, max_results: int = 15, media_type: str | None = None) -> str:
    """유럽 문화유산 통합 검색 Europeana (58개국 4,000+ 기관). 키 없이 즉시 작동(공용 데모 키) —
    대량 사용 시 apis.europeana.eu 무료 키를 EUROPEANA_API_KEY로.
    media_type: 'VIDEO'|'IMAGE'|'TEXT'|'SOUND'. 예: europeana_search('Corée', media_type='IMAGE')"""
    import urllib.parse, json as _json, urllib.request
    key = os.environ.get("EUROPEANA_API_KEY") or "api2demo"
    demo = not os.environ.get("EUROPEANA_API_KEY")
    params = {"wskey": key, "query": query, "rows": min(max_results, 50), "profile": "standard"}
    if media_type: params["qf"] = f"TYPE:{media_type.upper()}"
    url = "https://api.europeana.eu/record/v2/search.json?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = _json.loads(r.read().decode())
    items = data.get("items") or []
    lines = []
    for it in items[:max_results]:
        title = (it.get("title") or ["?"])[0]
        year = (it.get("year") or [""])[0]
        prov = (it.get("dataProvider") or [""])[0]
        lines.append(f"- {str(title)[:90]} ({year}) — {str(prov)[:40]} | {it.get('guid','')}")
    return (f"Europeana '{query}'" + (f" [{media_type}]" if media_type else "")
            + f" — 총 {data.get('totalResults')}건:\n" + ("\n".join(lines) or "(0건)")
            + "\n팁: 다국어 병행 — Corée(불)·Korea-Krieg(독)·Corea(이/스)")



REPORT_RULES = """HTML 발굴 보고서 작성 규칙 (11가지)
1. 파일명: [주제영문]_records_[연도범위].html — 조사 완료 시 기본 산출물로 생성
2. header: "[주제] — 자료 발굴 보고" + meta(작성일 · 대상 시기 · 대상 아카이브)
3. highlight 박스: 가장 중요한 발굴 1건 요약 (식별자·경위·구성·연구사적 의의)
4. 표① 문서 사료 / 표② 사진·영상 사료: 식별자·원제 / 연대 / 소장처·청구정보(RG·Entry·Box) / 관련 내용 / 바로가기(원문→해제→카탈로그 순, target=_blank) / 권리초판 배지(b-A 공개확정 · b-B 공개가능추정 · b-C 허가필요 · b-D 지위불명)
5. 재현용 검색 쿼리 표: 목적 / 쿼리 / URL 인코딩된 실행 링크 — 실제 실행해 본 쿼리만
6. '0건 ≠ 부재' note: 미전산화 수준 설명 + 인접 상자(Box ±2)·피스(참조코드 ±15) 추가 조사 권고
7. 종합 색인·최신 연구 목록 (ul.src)
8. 권리 판정 절: 법적 근거(17 U.S.C. §105 · 36 CFR 1254.62 · Crown/OGL · domaine public) + '출판 전 인간 최종 확인 필수' + D등급 공개 금지
9. footer: 방법론 한 줄 + '모든 링크는 [날짜] 기준 접속 확인됨'
10. 링크는 도구 호출·열람으로 실재 확인한 URL만 기재 — 추정 URL 금지
11. 민감 주제(위안부·포로·학살·희생자)는 피해자 존엄·윤리적 사용 문구를 권리 절에 포함"""

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{제목}} — 자료 발굴 보고</title>
<style>
  :root{
    --ink:#1a1d23; --sub:#5a6070; --line:#e3e5ea; --bg:#f7f8fa;
    --accent:#8a3033; --accent-soft:#f7eeee; --card:#ffffff;
  }
  *{box-sizing:border-box;}
  body{margin:0; font-family:'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif; color:var(--ink); background:var(--bg); line-height:1.65;}
  .wrap{max-width:1000px; margin:0 auto; padding:40px 24px 80px;}
  header{border-bottom:3px solid var(--accent); padding-bottom:20px; margin-bottom:32px;}
  h1{font-size:26px; margin:0 0 8px;}
  .meta{color:var(--sub); font-size:14px;}
  h2{font-size:20px; margin:40px 0 12px; padding-left:12px; border-left:4px solid var(--accent);}
  p{margin:10px 0;}
  .highlight{background:var(--accent-soft); border:1px solid #e8d5d5; border-radius:10px; padding:18px 20px; margin:20px 0;}
  .highlight strong{color:var(--accent);}
  table{width:100%; border-collapse:collapse; background:var(--card); font-size:14px; margin:16px 0; border:1px solid var(--line);}
  th{background:#2d3340; color:#fff; padding:10px 12px; text-align:left; font-weight:600; white-space:nowrap;}
  td{padding:10px 12px; border-top:1px solid var(--line); vertical-align:top;}
  tr:nth-child(even) td{background:#fafbfc;}
  a{color:#1d5fa8; text-decoration:none; border-bottom:1px dotted #9ab6d6;}
  a:hover{color:var(--accent); border-bottom-color:var(--accent);}
  .badge{display:inline-block; padding:2px 8px; border-radius:20px; font-size:12px; font-weight:700; white-space:nowrap;}
  .b-A{background:#e3f0fb; color:#1d5fa8; border:1px solid #b9d4ee;}
  .b-B{background:#e6f2e6; color:#2c6e2f; border:1px solid #bcd9bd;}
  .b-C{background:#fff3df; color:#9a6b15; border:1px solid #ead9b0;}
  .b-D{background:#fbe7e7; color:#a33333; border:1px solid #e6bcbc;}
  code{background:#eef0f4; padding:2px 6px; border-radius:4px; font-size:13px; font-family:Consolas,Menlo,monospace;}
  .note{background:#fff8e6; border:1px solid #eadfb8; border-radius:10px; padding:14px 18px; margin:16px 0; font-size:14px;}
  ul.src{columns:1; padding-left:20px; font-size:14px;}
  ul.src li{margin:6px 0;}
  .small{font-size:13px; color:var(--sub);}
  footer{margin-top:48px; padding-top:16px; border-top:1px solid var(--line); font-size:12px; color:var(--sub);}
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>{{제목}} — 자료 발굴 보고</h1>
  <div class="meta">작성일: {{작성일}} · 대상 시기: {{대상시기}} · 대상 아카이브: {{아카이브 목록}}</div>
</header>

<div class="highlight">
  <p><strong>핵심 발굴</strong> — {{가장 중요한 발굴 1건: 식별자·원제·경위·구성·연구사적 의의를 문단으로 요약}}</p>
</div>

<h2>1. 발굴 문서 목록 (문서 사료)</h2>
<table>
  <thead>
    <tr><th>#</th><th>식별자 · 원제</th><th>연대</th><th>소장처 / 청구정보</th><th>관련 내용</th><th>바로가기</th><th>권리초판</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td><strong>{{원제}}</strong><br><span class="small">{{생산기관·시리즈}}</span></td>
      <td>{{연대}}</td>
      <td>{{소장처}} <strong>{{RG/참조코드}}</strong>{{, Entry·Box 등}}</td>
      <td>{{한국 관련 핵심 내용}}</td>
      <td><a href="{{원문URL}}" target="_blank">원문</a><br><a href="{{해제URL}}" target="_blank">해제</a><br><a href="{{카탈로그검색URL}}" target="_blank">카탈로그 검색</a></td>
      <td><span class="badge b-B">B · PD 추정</span></td>
    </tr>
    <!-- 행 반복. 권리 배지: b-A(공개 확정)·b-B(공개 가능 추정)·b-C(허가 필요)·b-D(지위 불명·공개 금지) -->
  </tbody>
</table>

<h2>2. 사진 · 영상 사료</h2>
<!-- 사진·영상이 없으면 이 절 전체 삭제 -->
<table>
  <thead>
    <tr><th>#</th><th>식별자</th><th>연대</th><th>촬영자/생산자</th><th>내용</th><th>바로가기</th><th>권리초판</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>P1</td>
      <td><strong>{{예: 111-SC-000000}}</strong><br><span class="small">{{소장처·RG}}</span></td>
      <td>{{연대}}</td>
      <td>{{촬영자}}</td>
      <td>{{내용}}</td>
      <td><a href="{{URL}}" target="_blank">{{링크명}}</a></td>
      <td><span class="badge b-B">B</span></td>
    </tr>
  </tbody>
</table>

<h2>3. 재현용 검색 쿼리</h2>
<p>{{카탈로그명·링크}}에서 아래 쿼리로 재현할 수 있습니다. 전전(戰前) 자료 표기 규칙상
<code>Korea</code> 외에 <code>Chosen</code> · <code>Corea</code> 등 당대 표기를 병렬 투입하십시오.</p>
<table>
  <thead><tr><th>목적</th><th>쿼리</th><th>실행 링크</th></tr></thead>
  <tbody>
    <tr><td>{{목적}}</td><td><code>{{쿼리}}</code></td><td><a href="{{URL인코딩된 검색URL}}" target="_blank">검색 실행</a></td></tr>
    <!-- 행 반복: 실제 실행해 본 쿼리만 기재 -->
  </tbody>
</table>

<div class="note">
  <strong>⚠ 0건 ≠ 부재.</strong> {{미전산화 상황 설명 — 해당 RG/시리즈의 전산화 수준, 인접 상자·피스(예: Box NNN±2, 참조코드 ±15) 추가 조사 권고, 현지 열람·복사 대행 안내}}
</div>

<h2>4. 종합 색인 · 최신 연구</h2>
<ul class="src">
  <li><a href="{{URL}}" target="_blank">{{색인·데이터베이스·연구 제목}}</a> — {{한 줄 설명}}</li>
  <!-- 항목 반복 -->
</ul>

<h2>5. 권리 등급 판정 (초판)</h2>
<p>{{판정 요약: 근거 법령(17 U.S.C. §105 연방 직무저작물, 36 CFR 1254.62, Crown copyright/OGL,
domaine public 등)과 함께 표별 등급 설명}}.
자동 초판이므로 <strong>출판 전 인간 최종 확인 필수</strong>이며, <span class="badge b-D">D등급</span>은 공개 금지입니다.
{{민감 주제(위안부·포로·학살 등)인 경우: 피해자·생존자의 존엄을 고려한 윤리적 사용 기준 검토 문구 필수}}</p>

<footer>
  발굴 방법론: 해외 아카이브 한국 기록 발굴 스킬(표기 변형 병렬 투입 · RG 교차 검색 · 인접 확장 · 권리 초판 판정) 기반 ·
  본 보고서의 모든 링크는 {{확인일}} 기준 접속 확인됨.
</footer>

</div>
</body>
</html>
"""


@mcp.tool()
def report_template() -> str:
    """발굴 조사를 마친 뒤 결과를 HTML 보고서로 만들 때 호출 (조사 마무리 단계의 기본 산출물).
    보고서 골격(HTML/CSS 템플릿)과 11가지 작성 규칙을 반환한다. {{플레이스홀더}}를 검증된
    발굴 결과로 채워 [주제영문]_records_[연도범위].html 파일로 저장할 것."""
    return REPORT_RULES + "\n\n===== HTML TEMPLATE ({{플레이스홀더}}를 채울 것) =====\n" + REPORT_TEMPLATE


# ══════════ 국내 아카이브 수집기 — 자동 브라우징(서버 사이드 fetch·파싱) v1.9.0 ══════════
import urllib.parse as _up, urllib.request as _ur, html as _html

_UA_KO = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"


def _http_text(url, timeout=15):
    req = _ur.Request(url, headers={"User-Agent": _UA_KO, "Accept": "*/*",
                                    "X-Requested-With": "XMLHttpRequest"})
    with _ur.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _clean(s):
    return _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s))).strip()


def _browse(url):
    return f"\n열어보기: {url}"


def _agent_browse(name, query, url, why="이 기관은 자동 페치가 제한적입니다"):
    return (f"{name} '{query}' — {why}.\n"
            f"➤ 에이전트 지시: 이 메시지를 그대로 사용자에게 전달하지 마세요. 대신 당신의 웹 검색(WebSearch)으로 "
            f"'{query}'를 이 기관에서 찾거나, 아래 공식 검색 URL을 열람해 상위 결과(제목·연대·링크)를 정리한 뒤 "
            f"사용자에게 표로 제시하세요. 결과가 있으면 report_template으로 HTML 보고서화도 가능합니다.\n"
            f"공식 검색: {url}")


@mcp.tool()
def nedb_search(query: str, db: str = "", max_results: int = 15) -> str:
    """국사편찬위원회 한국사데이터베이스(db.history.go.kr) 통합검색을 서버에서 직접 조회. 검색어가
    등장하는 DB(조선왕조실록·승정원일기·포로신문보고서·독립운동사 등) 목록과 열람 URL을 반환한다.
    조선~근현대 1차 사료 1,100만+ 건. 인명·기관명은 한자 원표기가 색인 정확도 높음."""
    browse = "https://db.history.go.kr/search/searchResultList.do?searchKeywordType=BI&searchKeyword=" + _up.quote(query)
    api = "https://db.history.go.kr/search/searchTotalResult.do?searchKeyword=" + _up.quote(query)
    try:
        b = _http_text(api, 15)
        dbs, seen = [], set()
        for code, inner in re.findall(r'href="/item/(\w+)/main\.do"[^>]*>(.*?)</a>', b, re.S):
            nm = _clean(inner)
            if nm and nm not in seen:
                seen.add(nm); dbs.append(nm)
        if dbs:
            return (f"한국사DB '{query}' — 검색어가 등장하는 DB {len(dbs)}종:\n"
                    + "\n".join("- " + d for d in dbs[:max_results]) + _browse(browse)
                    + "\n각 DB에서 문서 단위로 열람. 한자 원표기 병행 검색 권장.")
        return _agent_browse("한국사DB", query, browse, "통합검색에서 매칭 DB 미검출")
    except Exception as e:
        return _agent_browse("한국사DB", query, browse, f"자동조회 실패({e})")


@mcp.tool()
def archives_search(query: str, max_results: int = 10) -> str:
    """국가기록원 국가기록포털(archives.go.kr). 정식 OpenAPI(RSS) — data.go.kr '나라기록물정보 서비스'
    (15000153) 무료 키를 환경변수 ARCHIVES_API_KEY로 설정하면 서버가 자동 검색해 결과를 반환한다.
    키가 없으면 포털 열람 URL을 반환. 노획문서·정부기록. 공공누리(KOGL) 유형 확인 후 이용."""
    key = os.environ.get("ARCHIVES_API_KEY")
    portal = "https://www.archives.go.kr/next/newsearch/listSubjectDescription.do?query=" + _up.quote(query)
    if key:
        api = ("https://search.archives.go.kr/openapi/search.arc?serviceKey=" + _up.quote(key)
               + "&query=" + _up.quote(query) + f"&start=1&limit={min(max_results, 50)}")
        try:
            xml = _http_text(api, 20)
            if "searchError" not in xml:
                def t(bl, x):
                    m = re.search(rf"<{x}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{x}>", bl, re.S)
                    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
                tot = t(xml, "totalCount") or t(xml, "totalResults") or "?"
                items = re.findall(r"<item>(.*?)</item>", xml, re.S)
                lines = [f"- {t(i,'title')[:90]} ({t(i,'produceYear') or t(i,'pubDate')[:16]}) {t(i,'link')}"
                         for i in items[:max_results]]
                return f"국가기록원 '{query}' — 총 {tot}건:\n" + ("\n".join(lines) or "(0건)") + "\n공공누리 유형 확인 후 이용."
            m = re.search(r"<message>(.*?)</message>", xml, re.S)
            return f"국가기록원 API 오류: {m.group(1).strip() if m else '?'} — 키·쿼터 확인." + _browse(portal)
        except Exception as e:
            return f"국가기록원 API 오류({e})." + _browse(portal)
    return _agent_browse("국가기록원", query, portal,
                         "OpenAPI 키(ARCHIVES_API_KEY, data.go.kr 15000153) 미설정")


@mcp.tool()
def nlk_search(query: str, collection: str = "total", max_results: int = 15) -> str:
    """국립중앙도서관(nl.go.kr) 디지털 컬렉션 검색. collection: 'total'(전체 소장자료)·'subject'(주제별)·
    'newspaper'(대한민국신문아카이브 1883-1960 고신문, 저작권만료 자유이용)·'gwanbo'(관보)·'exhibit'(전시)·
    'koreanmemory'(코리안메모리)·'overseas'(해외 한국관련자료). NLK_API_KEY(www.nl.go.kr Open API) 설정 시
    total/subject/gwanbo/overseas는 서버가 자동 검색. 그 외/키없음은 해당 컬렉션 열람 URL 반환."""
    COLL = {
        "total": ("전체 소장자료", "https://www.nl.go.kr/NL/contents/search.do?srchTarget=total&kwd=", True),
        "subject": ("주제별컬렉션", "https://www.nl.go.kr/NL/contents/N20103000000.do", True),
        "newspaper": ("대한민국신문아카이브", "https://www.nl.go.kr/newspaper/search_list.do?keyword=", False),
        "gwanbo": ("관보", "https://www.nl.go.kr/NL/contents/N20301000000.do", True),
        "exhibit": ("전시컬렉션(온라인전시)", "https://www.nl.go.kr/NL/contents/N20104000000.do", False),
        "koreanmemory": ("코리안메모리", "https://nl.go.kr/koreanmemory/", False),
        "overseas": ("해외 한국관련자료", "https://www.nl.go.kr/NL/contents/N20401010000.do", True),
    }
    NOTE = {"newspaper": "1883–1960 고신문 108종. 저작권 만료 — 출처표기 시 자유이용.",
            "koreanmemory": "구술·사진 큐레이션.", "exhibit": "온라인 전시(서사형).",
            "overseas": "해외 소재 한국 관련 자료 목록.", "gwanbo": "대한제국·총독부·대한민국 관보 원문.",
            "subject": "주제별 선별 디지털 컬렉션.", "total": "전체 소장자료."}
    c = collection.strip().lower()
    if c not in COLL:
        return "collection 값: " + ", ".join(COLL.keys())
    name, base, api_ok = COLL[c]
    open_url = (base + _up.quote(query)) if base.endswith(("kwd=", "keyword=")) else base
    note = NOTE.get(c, "")
    key = os.environ.get("NLK_API_KEY")
    if api_ok and key:
        api = ("https://www.nl.go.kr/NL/search/openApi/search.do?key=" + _up.quote(key)
               + "&apiType=xml&srchTarget=total&kwd=" + _up.quote(query)
               + f"&pageSize={min(max_results, 50)}&pageNum=1")
        try:
            xml = _http_text(api, 20)
            if "<error>" not in xml:
                def t(bl, x):
                    m = re.search(rf"<{x}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{x}>", bl, re.S)
                    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
                tot = t(xml, "total") or "?"
                items = re.findall(r"<item>(.*?)</item>", xml, re.S)
                lines = [f"- {t(i,'titleInfo')[:90]} / {t(i,'authorInfo')[:24]} ({t(i,'pubYearInfo')}) {t(i,'detailLink')}"
                         for i in items[:max_results]]
                return f"국립중앙도서관 · {name} '{query}' — 총 {tot}건:\n" + ("\n".join(lines) or "(0건)") + f"\n※ {note}"
            m = re.search(r"<msg>(.*?)</msg>", xml)
            return f"NLK OpenAPI 오류: {m.group(1) if m else '?'} — NLK_API_KEY 확인." + _browse(open_url)
        except Exception as e:
            return f"NLK API 오류({e})." + _browse(open_url)
    why = ("OpenAPI 키(NLK_API_KEY, www.nl.go.kr Open API) 미설정" if (api_ok and not key)
           else f"큐레이션/전용 컬렉션 — {note}")
    return _agent_browse(f"국립중앙도서관 · {name}", query, open_url, why)


@mcp.tool()
def seoul_archives_search(query: str, max_results: int = 15) -> str:
    """서울기록원(archives.seoul.go.kr) 카탈로그를 서버에서 직접 조회 — 검색어와 매칭되는 컬렉션
    목록과 전체 항목 URL을 반환한다. 서울시 행정기록·시정사진·구술 등 지방기록물."""
    land = "https://archives.seoul.go.kr/catalog?search_api_fulltext=" + _up.quote(query)
    deep = "https://archives.seoul.go.kr/catalog/result?regclass=RC_ITEM&search_api_fulltext=" + _up.quote(query)
    try:
        b = _http_text(land, 15)
        cols = []
        for href, inner in re.findall(r'href="(/catalog/result\?[^"]*collects=[^"]*)"[^>]*>(.*?)</a>', b, re.S):
            nm = _clean(inner)
            if nm and "컬렉션" in nm:
                cols.append((nm, "https://archives.seoul.go.kr" + href))
        if cols:
            lines = [f"- {n}\n  {u}" for n, u in cols[:max_results]]
            return f"서울기록원 '{query}' — 매칭 컬렉션 {len(cols)}개:\n" + "\n".join(lines) + f"\n전체 항목: {deep}"
        return _agent_browse("서울기록원", query, deep, "매칭 컬렉션 미검출")
    except Exception as e:
        return _agent_browse("서울기록원", query, deep, f"자동조회 실패({e})")


@mcp.tool()
def warmemo_search(query: str) -> str:
    """전쟁기념관 아카이브(archives.warmemo.or.kr) 통합검색을 서버에서 직접 조회 — 카테고리별
    (소장자료·유물·사진·영상·행사 등) 검색 건수를 반환한다. 한국전쟁·근현대 군사사 국내 1차 사료 —
    NARA(RG 111/342)·TNA(WO)의 해외 한국전쟁 기록과 교차검증에 강력."""
    url = "http://archives.warmemo.or.kr/intgsrch/intgsrchArchv.do?MID=UM00045&keyword=" + _up.quote(query)
    try:
        b = _http_text(url, 15)
        cats = re.findall(r'class="total-breadcrumb">(.*?)</span>\s*<span>\s*총\s*([\d,]+)', b, re.S)
        if cats:
            lines = [f"- {_clean(c)} : {n}건" for c, n in cats[:20]]
            return (f"전쟁기념관 '{query}' — 카테고리별 검색 건수:\n" + "\n".join(lines) + _browse(url)
                    + "\n한국전쟁·군사사 사료 — 해외(NARA·TNA)와 교차검증.")
        return _agent_browse("전쟁기념관", query, url, "통합검색 결과 미검출")
    except Exception as e:
        return _agent_browse("전쟁기념관", query, url, f"자동조회 실패({e})")


@mcp.tool()
def foia_search(query: str) -> str:
    """대한민국 정보공개포털(open.go.kr) — 원문정보공개(정부 결재문서 원문)·사전정보공표·정보공개청구.
    로그인 기반 포털이라 서버 자동 페치가 제한적 — 브라우저 도구로 열어 결과를 읽어오도록 안내한다.
    미공개 문서는 포털에서 정보공개청구로 요청 가능."""
    url = "https://www.open.go.kr/othicInfo/infoList/orginlInfoList.do?searchKeyword=" + _up.quote(query)
    return (_agent_browse("정보공개포털(원문정보공개)", query, url)
            + "\n※ 미공개 문서는 포털에서 정보공개청구로 요청.")


@mcp.tool()
def local_gov_search(query: str, source: str) -> str:
    """지방자치단체 정보공개·기록원 검색. source: 'seoul_opengov'(서울정보소통광장 — 서울시 결재문서
    원문공개, 서버 자동조회)·'sen'(서울시교육청 정보공개)·'gyeongnam'(경상남도기록원). 결재문서 원문·
    지방기록물은 지역사·특정사건 발굴의 1차 사료."""
    src = source.strip().lower()
    if src == "seoul_opengov":
        url = "https://opengov.seoul.go.kr/sanction/list?searchKeyword=" + _up.quote(query)
        try:
            b = _http_text(url, 15)
            items = re.findall(r'<a[^>]+href="(/sanction/\d+)"[^>]*>(.*?)</a>', b, re.S)
            uniq, seen = [], set()
            for h, t in items:
                tt = re.sub(r'^제목\s*:\s*', '', _clean(t))
                if h not in seen and tt:
                    seen.add(h); uniq.append((h, tt))
            if uniq:
                lines = [f"- {t}\n  https://opengov.seoul.go.kr{h}" for h, t in uniq[:15]]
                return f"서울정보소통광장 '{query}' — 결재문서 {len(uniq)}건:\n" + "\n".join(lines)
            return _agent_browse("서울정보소통광장", query, url, "결재문서 미검출")
        except Exception as e:
            return _agent_browse("서울정보소통광장", query, url, f"자동조회 실패({e})")
    if src == "sen":
        url = "https://open.sen.go.kr/"
        return _agent_browse("서울시교육청 정보공개(열린 서울교육)", query, url)
    if src == "gyeongnam":
        url = "https://archives.gyeongnam.go.kr/main.web"
        return _agent_browse("경상남도기록원", query, url)
    return "source 값: seoul_opengov, sen, gyeongnam"


@mcp.tool()
def scrape_plan(url: str) -> str:
    """임의 URL의 robots.txt를 확인해 직접 수집 가능 여부를 판정한다. robots가 차단했거나 JS 렌더라
    서버 페치로 안 되는 사이트는, 에이전트의 브라우저 도구(웹 열람)로 해당 URL을 열어 결과를 읽도록 안내."""
    p = _up.urlparse(url)
    root = f"{p.scheme}://{p.netloc}"
    path = p.path or "/"
    verdict = "robots 미확인"
    try:
        rb = _http_text(root + "/robots.txt", 12)
        blocked, agent_all = False, False
        for line in rb.splitlines():
            s = line.strip().lower()
            if s.startswith("user-agent:"):
                agent_all = ("*" in s)
            elif agent_all and s.startswith("disallow:"):
                d = s.split(":", 1)[1].strip()
                if d and path.startswith(d):
                    blocked = True
        verdict = "robots 차단 → 브라우저 도구로 열람" if blocked else "robots 허용(단 JS 렌더면 브라우저 필요)"
    except Exception as e:
        verdict = f"robots 미확인({e})"
    return (f"{url}\n판정: {verdict}\n"
            "권장: 에이전트 브라우저 도구로 이 URL을 열고, 결과 목록의 제목·링크·연대를 표로 정리한 뒤 "
            "report_template으로 HTML 보고서화. 과도한 요청은 피할 것.")


if __name__ == "__main__":
    mcp.run()
