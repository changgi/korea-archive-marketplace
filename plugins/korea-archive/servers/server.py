#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""korea-archive MCP 서버 — 국내외 한국 기록 발굴 도구를 AI 에이전트에 장착.

해외(6): tna_search · tna_adjacent_mine · nara_search · ia_search(검색+identifier 메타 통합)
         gallica_search · europeana_search
국내(9): nedb_search(한국사DB) · archives_search(국가기록원) · nlk_search(국립중앙도서관)
         seoul_archives_search(서울기록원) · foia_search(정보공개포털+지방 정보공개·기록원 통합)
         warmemo_search(전쟁기념관) · koreanwar_search(통합검색+전투정보 scope)·koreanwar_item
         (건별 메타+radius 인접 채굴) (KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터 — 협약기관) · scrape_plan(폴백)
유틸(5): query_bank · judge_rights · report_template · cross_search(동시 교차수집·병합) · source_profile(기관 프로파일)
총 20개 — PlayMCP 개발가이드(서버당 도구 20개 이하) 준수.
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
try:  # 국내 아카이브 키워드셋 + 전 기관 프로파일 (선택 — 없어도 코어 동작)
    import keywords_nedb, keywords_archives, keywords_nlk, keywords_warmemo, keywords_seoul
    from profiles import PROFILES
    _DOM = {"nedb": keywords_nedb, "archives": keywords_archives, "nlk": keywords_nlk,
            "warmemo": keywords_warmemo, "seoul": keywords_seoul}
except Exception:
    _DOM, PROFILES = {}, {}
_DOM_NAME = {"nedb": "국사편찬위 한국사DB", "archives": "국가기록원", "nlk": "국립중앙도서관",
             "warmemo": "전쟁기념관", "seoul": "서울·지방기록원"}
def _dom_groups(mod):
    for _n in dir(mod):
        if _n.endswith("_GROUPS"):
            return getattr(mod, _n)
    return []

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
def ia_search(query: str = "", identifier: str = "", max_results: int = 15) -> str:
    """archive.org 고급 검색. 예: 'identifier:111-adc*', 'collection:universal_newsreels AND korea',
    'mediatype:movies AND (keijo OR chosen)'. identifier를 주면 해당 아이템의 메타데이터·원본 파일
    목록(다운로드 전 크기 파악)을 대신 반환한다."""
    if identifier:
        data = http_json(f"https://archive.org/metadata/{identifier}")
        md = data.get("metadata") or {}
        files = [f for f in (data.get("files") or []) if f.get("source") == "original"][:10]
        return (f"제목: {md.get('title')}\n설명: {str(md.get('description'))[:300]}\n"
                f"연대: {md.get('date')} | 라이선스: {md.get('licenseurl') or md.get('rights') or '표기 없음'}\n"
                "원본 파일:\n" + "\n".join(f"- {f['name']} ({int(f.get('size',0))/1e6:.1f}MB)" for f in files))
    if not query:
        return "query 또는 identifier 중 하나는 필수."
    import urllib.parse
    data = http_json("https://archive.org/advancedsearch.php?q=" + urllib.parse.quote(query) +
                     f"&fl[]=identifier&fl[]=title&fl[]=date&rows={max_results}&output=json")
    docs = (data.get("response") or {}).get("docs") or []
    nf = (data.get("response") or {}).get("numFound")
    return f"archive.org '{query}' — 총 {nf}건:\n" + "\n".join(
        f"- {d.get('identifier')} | {str(d.get('title'))[:90]} | https://archive.org/details/{d.get('identifier')}"
        for d in docs) if docs else f"archive.org '{query}' — 0건"

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
    tl = topic.strip().lower()
    if tl == "domestic":
        return "국내 아카이브 3대 부정합 키워드셋 (topic=기관키 또는 그룹ID):\n" + "\n".join(
            f"- {k} ({_DOM_NAME[k]}): 그룹 " + "·".join(g[0] for g in _dom_groups(mod))
            + f" | 분류맵 {len(getattr(mod,'CLASS_MAP',{}))} | 관행노트 {len(getattr(mod,'DESC_NOTES',[]))}"
            for k, mod in _DOM.items())
    if tl in _DOM:
        mod = _DOM[tl]
        gl = "\n".join(f"[{g[0]}] {g[2]} ({g[1]}, {len(g[4])}): " + ", ".join(g[4][:14])
                       + (" …" if len(g[4]) > 14 else "") for g in _dom_groups(mod))
        cm = "\n".join(f"- {c}: {', '.join(v[1])}" for c, v in getattr(mod, "CLASS_MAP", {}).items())
        nt = "\n- ".join(getattr(mod, "DESC_NOTES", []))
        return f"{_DOM_NAME[tl]}\n\n[① 언어적 부정합 — 검증 키워드]\n{gl}\n\n[② 분류 교차매핑]\n{cm}\n\n[③ 기술관행 노트]\n- {nt}"
    for k, mod in _DOM.items():
        for g in _dom_groups(mod):
            if g[0].upper() == topic.upper():
                return f"{g[0]} {g[2]} ({_DOM_NAME[k]}) [{g[1]}]:\n" + "\n".join(f"- {x}" for x in g[4])
    return "해당 그룹 없음 — topic='list'(해외 G/N/RG/TNA) 또는 'domestic'"

@mcp.tool()
def judge_rights(rg_series: str, title: str = "", archive: str = "") -> str:
    """권리 등급 자동 초기판정 (보고서 §30 플로 1~3단계). A/B=공개가능, C=허가필요, D=지위불명.
    ※ 최종 확정은 사람이 §30 5단계로 서면 판정할 것."""
    cls, note = auto_rights({"rg_series": rg_series, "title_orig": title, "archive": archive})
    return f"등급: {cls}\n근거: {note}\n※ 자동 초기판정 — 공개 전 수동 확정 필수, D등급 공개 금지"


# Gallica 한국어→프랑스어 자동 변환 — Gallica는 프랑스어 색인이라 한국어 질의는 0건
# ("병인양요 선교사" 0 vs "expédition de Corée 1866 missionnaires" 5,853, 실측).
_GALLICA_KO_FR = [
    (r"병인양요|병인박해", "expédition de Corée 1866"),
    (r"신미양요", "Corée expédition américaine 1871"),
    (r"강화도|강화", "île Kanghoa"),
    (r"파리\s?외방전교회", "Missions étrangères de Paris"),
    (r"선교사", "missionnaires"),
    (r"천주교|가톨릭|순교", "catholique Corée"),
    (r"한국전쟁|6[·.]25", "guerre de Corée"),
    (r"러일전쟁", "guerre russo-japonaise"),
    (r"서울|한양", "Séoul"),
    (r"부산", "Fusan"),
    (r"인천|제물포", "Chemulpo"),
    (r"제주", "Quelpaert"),
    (r"지도", "carte"),
    (r"사진", "photographie"),
    (r"신문", "journal"),
    (r"조선|한국|대한제국|고려", "Corée"),
    (r"기록|자료|문서|영상|관련", " "),
]

def _gallica_ko_fr(q):
    if not re.search(r"[가-힣]", q):
        return None
    f = q
    for pat, fr in _GALLICA_KO_FR:
        f = re.sub(pat, fr, f)
    f = re.sub(r"\s+", " ", re.sub(r"[가-힣]+", " ", f)).strip()
    if not re.search(r"cor[ée]e|séoul|fusan|chemulpo|quelpaert|missionnaires|tchosen", f, re.I):
        f = ("Corée " + f).strip()
    return f or "Corée"


@mcp.tool()
def gallica_search(query: str, max_results: int = 15) -> str:
    """프랑스 국립도서관 Gallica 검색 (SRU API, 키 불요). 한국어 질의는 프랑스어 검색어로
    자동 변환된다(병인양요→expédition de Corée 1866, 선교사→missionnaires, 조선→Corée …).
    프랑스어 직접 입력도 가능 — 'Corée', 'guerre de Corée', 'Séoul', 'Tchosen'. 구한말
    프랑스 선교사·외교 문헌과 사진의 보고. 예: gallica_search('병인양요 선교사')"""
    import urllib.parse, urllib.request, xml.etree.ElementTree as ET
    fr = _gallica_ko_fr(query)
    eff = fr or query
    q = urllib.parse.quote(f'gallica all "{eff}"' if '"' not in eff else f'gallica all {eff}')
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
    return (f"Gallica '{query}'" + (f" → 프랑스어 자동 변환 '{eff}'" if fr else "")
            + f" — 총 {total.text if total is not None else '?'}건:\n"
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
            + ("\n※ 공용 데모 키(api2demo) 사용 중 — 레이트리밋 시 EUROPEANA_API_KEY 설정 권장." if demo else "")
            + "\n팁: 다국어 병행 — Corée(불)·Korea-Krieg(독)·Corea(이/스)")



REPORT_RULES = """HTML 발굴 보고서 작성 규칙 (12가지)
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
11. 민감 주제(위안부·포로·학살·희생자)는 피해자 존엄·윤리적 사용 문구를 권리 절에 포함
12. 그림(선택, 없으면 생략): 대표 이미지·지도·연표·다이어그램을 <figure>로 본문에 삽입해 시각화. 자료 사진은 <img src="data:image/jpeg;base64,…">로 base64 임베드(외부 이미지 링크 금지 — 단일 HTML 파일 자기완결), 연표·관계도 등 도해는 인라인 <svg>로 직접 작성 가능. 각 그림에 <figcaption>그림 N. 설명</figcaption>. figure는 어느 절 사이에나 배치 가능"""

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
  figure{margin:22px 0;}
  figure img{width:100%; display:block; border:1px solid var(--line);}
  figure svg{width:100%; height:auto; display:block; border:1px solid var(--line); background:var(--card);}
  figcaption{font-size:13px; color:var(--sub); margin-top:6px;}
  footer{margin-top:48px; padding-top:16px; border-top:1px solid var(--line); font-size:12px; color:var(--sub);}
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>{{제목}} — 자료 발굴 보고</h1>
  <div class="meta">작성일: {{작성일}} · 대상 시기: {{대상시기}} · 대상 아카이브: {{아카이브 목록}}</div>
</header>

<!-- 그림(선택) — 대표 이미지·지도·연표·다이어그램. 없으면 이 <figure> 블록 삭제. figure는 어느 절 사이에나 넣을 수 있음. -->
<figure>
  <img src="data:image/jpeg;base64,{{BASE64 이미지 데이터 — 외부 링크 금지, 자기완결}}" alt="{{대체 텍스트}}">
  <figcaption>그림 1. {{그림 설명}}</figcaption>
</figure>

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


# ══════════ 상호보완 다중채널 수집 (동시 수집 + 병합/중복제거) ══════════
import concurrent.futures as _cf

def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(s or ""))).strip()

def _ddk(it):
    t = re.sub(r"[^a-z0-9가-힣一-鿿]", "", _norm(it.get("title", "")).lower())[:50]
    return (t + "|" + (it.get("id") or ""))[:80]

def _collect_merged(collectors):
    merged, stats = {}, []
    with _cf.ThreadPoolExecutor(max_workers=8) as ex:
        submitted = [(name, ex.submit(fn)) for name, fn in collectors]
        for name, fut in submitted:
            try:
                items = fut.result(timeout=45) or []
                stats.append(f"{name}:{len(items)}")
                for raw in items:
                    if not _norm(raw.get("title", "")):
                        continue
                    k = _ddk(raw)
                    if k in merged:
                        if name not in merged[k]["sources"]:
                            merged[k]["sources"].append(name)
                    else:
                        merged[k] = {"title": _norm(raw.get("title", "")), "date": raw.get("date", ""),
                                     "id": raw.get("id", ""), "url": raw.get("url", ""), "sources": [name]}
            except Exception:
                stats.append(f"{name}:—")
    return list(merged.values()), stats

def _c_tna(q, n):
    query = f'"{q.strip()}"' if re.match(r"^[A-Z]+ \d+/\d+$", q.strip()) else q
    out = []
    for batch, _t in T._search(query, page_size=min(n, 50), max_pages=1, sleep=0):
        for r in batch:
            rec = T._extract(r, "x", q)
            out.append({"title": rec.get("title", ""), "date": rec.get("date", ""),
                        "id": rec.get("local_id", ""), "url": rec.get("url", "")})
    return out[:n]

def _c_ia(q, n):
    import urllib.parse
    d = http_json("https://archive.org/advancedsearch.php?q=" + urllib.parse.quote(q) +
                  f"&fl[]=identifier&fl[]=title&fl[]=date&rows={n}&output=json")
    return [{"title": str(x.get("title", "")), "date": x.get("date", ""), "id": x.get("identifier"),
             "url": f"https://archive.org/details/{x.get('identifier')}"}
            for x in ((d.get("response") or {}).get("docs") or [])]

def _c_gallica(q, n):
    import urllib.parse, urllib.request
    q = _gallica_ko_fr(q) or q
    qq = urllib.parse.quote('gallica all "' + q.replace('"', '') + '"')
    url = f"https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2&query={qq}&maximumRecords={n}"
    req = urllib.request.Request(url, headers={"User-Agent": _UA_KO})
    with urllib.request.urlopen(req, timeout=30) as r:
        xml = r.read().decode("utf-8", "replace")
    out = []
    for b in xml.split("<srw:record>")[1:n + 1]:
        def g(t, _b=b):
            m = re.search(rf"<dc:{t}[^>]*>([^<]*)<", _b)
            return m.group(1).strip() if m else ""
        out.append({"title": g("title"), "date": g("date"), "id": g("identifier"), "url": g("identifier")})
    return out

def _c_europeana(q, n):
    import urllib.parse
    key = os.environ.get("EUROPEANA_API_KEY") or "api2demo"
    d = http_json("https://api.europeana.eu/record/v2/search.json?" +
                  urllib.parse.urlencode({"wskey": key, "query": q, "rows": n, "profile": "standard"}))
    return [{"title": (it.get("title") or ["?"])[0], "date": (it.get("year") or [""])[0],
             "id": it.get("id", ""), "url": it.get("guid", "")} for it in (d.get("items") or [])]

def _c_nara(q, n):
    key = os.environ.get("NARA_API_KEY")
    if not key:
        return []
    data = http_json("https://catalog.archives.gov/api/v2/records/search?" + qs({"q": q, "limit": n, "page": 1}),
                     headers={"x-api-key": key})
    hits = (((data.get("body") or {}).get("hits") or {}).get("hits")) or []
    out = []
    for h in hits:
        rec = (h.get("_source") or {}).get("record") or {}
        out.append({"title": rec.get("title", ""), "date": "", "id": f"NAID {rec.get('naId')}",
                    "url": f"https://catalog.archives.gov/id/{rec.get('naId')}"})
    return out

def _xtag(bl, x):
    m = re.search(rf"<{x}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{x}>", bl, re.S)
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""

def _c_archives(q, n):
    key = os.environ.get("ARCHIVES_API_KEY")
    if not key:
        return []
    sk = key if ("%" in key) else _up.quote(key)
    xml = _http_text("https://apis.data.go.kr/1741050/openapi/searcharc?serviceKey=" + sk +
                     "&query=" + _up.quote(q) + f"&start=1&limit={n}", 20)
    return [{"title": _xtag(i, "title"), "date": _xtag(i, "prod_year"), "id": _xtag(i, "prod_name"),
             "url": _xtag(i, "link")} for i in re.findall(r"<item>(.*?)</item>", xml, re.S)]

def _c_nlk(q, n):
    key = os.environ.get("NLK_API_KEY")
    if not key:
        return []
    xml = _http_text("https://www.nl.go.kr/NL/search/openApi/search.do?key=" + _up.quote(key) +
                     "&apiType=xml&srchTarget=total&kwd=" + _up.quote(q) + f"&pageSize={n}&pageNum=1", 20)
    out = []
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
        lk = _xtag(it, "detail_link") or _xtag(it, "org_link")
        if lk.startswith("/"):
            lk = "https://www.nl.go.kr" + lk
        out.append({"title": _xtag(it, "title_info") or _xtag(it, "title"), "date": _xtag(it, "pub_year_info"),
                    "id": _xtag(it, "type_name"), "url": lk})
    return out

# nedb: 국사편찬위 한국사DB의 data.go.kr 공식 개방파일(KOGL)을 인덱싱해 웹 배치한 것을 검색 — robots 무관(라이브 스크래핑 없음).
# NEDB_INDEX_URL 에 ingest-opendata.mjs로 만든 nedb_index.json(호스팅 URL) 지정 시 활성화.
_nedb_idx = None
_nedb_tried = False
def _load_nedb_index():
    global _nedb_idx, _nedb_tried
    if _nedb_tried:
        return _nedb_idx
    _nedb_tried = True
    url = os.environ.get("NEDB_INDEX_URL")
    if not url:
        return None
    try:
        d = http_json(url)
        _nedb_idx = d if isinstance(d, list) else (d.get("records") if isinstance(d, dict) else None)
    except Exception:
        _nedb_idx = None
    return _nedb_idx

def _nedb_file_search(recs, q, n):
    ql = q.lower()
    out = []
    for r in recs:
        if ql in (r.get("title") or "").lower() or ql in (r.get("text") or "").lower():
            out.append({"title": r.get("title") or "", "date": r.get("date") or "",
                        "id": r.get("db") or "", "url": r.get("url") or ""})
            if len(out) >= n:
                break
    return out

def _c_nedb(q, n):
    recs = _load_nedb_index()
    return _nedb_file_search(recs, q, n) if recs else []


# ══════════ KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터 (koreanwar.or.kr:8443 — 전쟁기념관재단, 협약기관) ══════════
# MOU 협약: 모든 요청에 프로그램 식별 UA를 싣고 정중한 호출량을 유지한다
# (robots.txt 404 = 지시 부재; OpenAPI 약관상 대량 크롤링 금지 — 페이지 스캔은 소량으로).
_KW_BASE = "https://www.koreanwar.or.kr:8443"
_KW_UA = "KoreaArchiveMCP/1.11 (+https://github.com/changgi/korea-archive-mcp; MOU partner integration)"

def _kw_text(url, timeout=20):
    req = _ur.Request(url, headers={"User-Agent": _KW_UA, "Accept": "*/*"})
    with _ur.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def _kw_parse_cards(page_html):
    """/search.do 결과카드 파싱 — archRfcd(아카이브)·bookId(도서), 생산기관/생산자, 상위계층(NARA RG 노출)."""
    cards = []
    for b in page_html.split("result-card__body")[1:]:
        m = re.search(r'href="/(searchDetail(?:-book)?\.do)\?(archRfcd|bookId)=([^"]+)"[^>]*>(.*?)</a>', b, re.S)
        if not m:
            continue
        meta = {}
        for t, x in re.findall(r'<span class="tit">([^<]+)</span>\s*<span class="txt">(.*?)</span>', b, re.S):
            meta[_clean(t)] = _clean(x)
        rg = re.search(r"Record Group (\d+)", meta.get("상위계층", ""))
        cards.append({"title": _clean(m.group(4)),
                      "id": m.group(3) if m.group(2) == "archRfcd" else "book:" + m.group(3),
                      "url": f"{_KW_BASE}/{m.group(1)}?{m.group(2)}={_up.quote(m.group(3))}",
                      "producer": meta.get("생산기관/생산자", ""), "hierarchy": meta.get("상위계층", ""),
                      "rg": rg.group(1) if rg else ""})
    return cards

def _kw_search(params):
    q = _up.urlencode({k: v for k, v in params.items() if v not in (None, "")})
    b = _kw_text(f"{_KW_BASE}/search.do?{q}")
    mt = re.search(r'totalCount">\s*([\d,]+)', b)
    return (mt.group(1) if mt else "?"), _kw_parse_cards(b)

def _kw_api_scan(q, max_pages=None):
    """OpenAPI pbrcList.do — 토큰+IP 인증 JSON 목록(키워드 파라미터 없음 → 페이지 순회+로컬 필터).
    KOREANWAR_API_TOKEN 설정 즉시 활성(신청 승인 대기 중에는 None 반환으로 무시)."""
    token = os.environ.get("KOREANWAR_API_TOKEN")
    if not token:
        return None
    import time as _t
    pages = min(int(max_pages or os.environ.get("KOREANWAR_API_PAGES", 3)), 10)
    ql = q.lower(); hits = []; total = 0; checked = 0
    for p in range(1, pages + 1):
        d = json.loads(_kw_text(f"{_KW_BASE}/openapi/pbrcList.do?token={_up.quote(token)}&page={p}&pageSize=100"))
        if d.get("resultCode") != "OK":
            raise RuntimeError(f"OpenAPI {d.get('resultCode')}: {d.get('resultMsg', '')}"
                               " — 토큰 미승인이거나 서버 IP 미등록(승인 후 IP 등록 필요)")
        total = d.get("totalCount", total)
        lst = d.get("list") or []
        checked += len(lst)
        for it in lst:
            if any(f and ql in str(f).lower() for f in (it.get("sj"), it.get("engSj"), it.get("spln"), it.get("stmt"))):
                hits.append({"ref": it.get("archRfcd", ""), "title": it.get("sj") or it.get("engSj") or "",
                             "kogl": it.get("kogl", ""), "useCnd": it.get("useCnd", ""),
                             "cpyrYn": it.get("cpyrYn", ""), "olinYn": it.get("olinYn", "")})
        if len(lst) < 100:
            break
        _t.sleep(0.2)
    return {"total": total, "checked": checked, "hits": hits}

def _c_koreanwar(q, n):
    _, cards = _kw_search({"keyword": q, "viewType": "archive"})
    return [{"title": c["title"], "date": "", "id": c["id"], "url": c["url"]} for c in cards[:n]]

_COLLECT = {"tna": _c_tna, "ia": _c_ia, "gallica": _c_gallica, "europeana": _c_europeana,
            "nara": _c_nara, "archives": _c_archives, "nlk": _c_nlk, "nedb": _c_nedb,
            "koreanwar": _c_koreanwar}


@mcp.tool()
def nedb_search(query: str, db: str = "", max_results: int = 15) -> str:
    """국사편찬위원회 한국사데이터베이스(db.history.go.kr) 통합검색을 서버에서 직접 조회. 검색어가
    등장하는 DB(조선왕조실록·승정원일기·포로신문보고서·독립운동사 등) 목록과 열람 URL을 반환한다.
    조선~근현대 1차 사료 1,100만+ 건. 인명·기관명은 한자 원표기가 색인 정확도 높음."""
    browse = "https://db.history.go.kr/search/searchResultList.do?searchKeywordType=BI&searchKeyword=" + _up.quote(query)
    idx = _load_nedb_index()
    if idx:  # NEDB_INDEX_URL 설정 시 공식 개방파일(KOGL) 인덱스 검색 — robots 무관, 라이브 스크래핑 없음
        hits = _nedb_file_search(idx, query, max_results)
        body = "\n".join(f"- [{h['id']}] {h['title'][:95]}" + (f" {h['url']}" if h['url'] else "") for h in hits) \
            or "(0건 — 다른 표기(한자 원표기 등) 시도)"
        return (f"한국사DB(공식 개방파일 인덱스) '{query}' — {len(hits)}건:\n" + body
                + f"\n※ data.go.kr 공식 파일(KOGL) 기반 — robots 무관. 전체 통합검색(브라우저): {browse}")
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
        sk = key if ('%' in key) else _up.quote(key)  # data.go.kr Encoding키는 그대로, Decoding키는 인코딩
        api = ("https://apis.data.go.kr/1741050/openapi/searcharc?serviceKey=" + sk
               + "&query=" + _up.quote(query) + f"&start=1&limit={min(max_results, 50)}")
        try:
            xml = _http_text(api, 20)
            if "searchError" not in xml and "<item>" in xml:
                def t(bl, x):
                    m = re.search(rf"<{x}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{x}>", bl, re.S)
                    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
                tot = t(xml, "total") or "?"
                items = re.findall(r"<item>(.*?)</item>", xml, re.S)
                lines = [f"- {t(i,'title')[:90]} ({t(i,'prod_year')}) · {t(i,'prod_name')[:20]} "
                         f"[{'공개' if t(i,'is_open')=='1' else '비공개'}] {t(i,'link')}"
                         for i in items[:max_results]]
                return (f"국가기록원 '{query}' — 총 {tot}건:\n" + ("\n".join(lines) or "(0건)")
                        + "\n공공누리(KOGL) 유형 확인 후 이용. 비공개 항목은 정보공개청구 대상.")
            m = re.search(r"<message>(.*?)</message>", xml, re.S)
            return _agent_browse("국가기록원", query, portal, f"API 오류: {m.group(1).strip() if m else '결과 없음'}")
        except Exception as e:
            return _agent_browse("국가기록원", query, portal, f"API 오류({e})")
    return _agent_browse("국가기록원", query, portal,
                         "OpenAPI 키(ARCHIVES_API_KEY, data.go.kr 15000153) 미설정")


@mcp.tool()
def nlk_search(query: str, collection: str = "total", category: str = "", max_results: int = 15) -> str:
    """국립중앙도서관(nl.go.kr) 디지털 컬렉션 검색. collection: 'total'(전체 소장자료)·'subject'(주제별)·
    'newspaper'(대한민국신문아카이브 1883-1960 고신문, 저작권만료 자유이용)·'gwanbo'(관보)·'exhibit'(전시)·
    'koreanmemory'(코리안메모리)·'overseas'(해외 한국관련자료). NLK_API_KEY(www.nl.go.kr Open API)를 설정하면
    total/subject/gwanbo/overseas 선택 시 서버가 Open API로 자동 검색한다. category(자료유형: 도서·고문헌·
    학위논문·잡지/학술지·신문·기사·멀티미디어)를 주면 전체 카탈로그 채널과 자료유형 정밀 채널을 함께 수집한다
    (상호보완 이중수집). 큐레이션 컬렉션·키 없음은 해당 컬렉션 열람 URL을 반환."""
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
        base_api = ("https://www.nl.go.kr/NL/search/openApi/search.do?key=" + _up.quote(key)
                    + "&apiType=xml&srchTarget=total&kwd=" + _up.quote(query)
                    + f"&pageSize={min(max_results, 50)}&pageNum=1")

        def t(bl, x):
            m = re.search(rf"<{x}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{x}>", bl, re.S)
            return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""

        def parse(xml):
            tot = t(xml, "total") or "?"
            items = re.findall(r"<item>(.*?)</item>", xml, re.S)

            def pick(bl, tags):
                for tg in tags:
                    v = t(bl, tg)
                    if v:
                        return v
                return ""
            lines = []
            for it in items[:max_results]:
                title = pick(it, ["title_info", "titleInfo", "title"]) or \
                    re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", it)).strip()
                typ = pick(it, ["type_name", "typeName"])
                pub = pick(it, ["pub_info", "author_info", "authorInfo"])
                year = pick(it, ["pub_year_info", "pubYearInfo"])
                lk = pick(it, ["org_link", "detail_link", "detailLink"])
                if lk.startswith("/"):
                    lk = "https://www.nl.go.kr" + lk
                lines.append("- " + title[:80] + (f" [{typ}]" if typ else "")
                             + (f" · {pub[:20]}" if pub else "") + (f" ({year})" if year else "")
                             + (f" {lk}" if lk else ""))
            return tot, lines
        try:
            # 이중채널 동시 수집: (A) 전체 소장자료 + (B) 자료유형(category) 정밀 — 상호보완
            total_xml = _http_text(base_api, 20)
            if "<error" in total_xml:
                m = re.search(r"<msg>(.*?)</msg>", total_xml)
                return f"NLK OpenAPI 오류: {m.group(1) if m else '?'} — NLK_API_KEY 확인." + _browse(open_url)
            a_tot, a_lines = parse(total_xml)
            out = (f"국립중앙도서관 자동검색(전체 소장자료) '{query}' — 총 {a_tot}건:\n"
                   + ("\n".join(a_lines) or "(0건)"))
            if category:
                try:
                    cat_xml = _http_text(base_api + "&category=" + _up.quote(category), 20)
                except Exception:
                    cat_xml = "<error/>"
                if "<error" not in cat_xml:
                    b_tot, b_lines = parse(cat_xml)
                    out += (f"\n\n[② 자료유형 '{category}' 정밀 채널 — 총 {b_tot}건 (동시 수집)]\n"
                            + ("\n".join(b_lines) or "(0건)") + "\n※ 전체+자료유형 이중채널(상호보완).")
                else:
                    out += f"\n(자료유형 '{category}' 채널 오류)"
            else:
                out += "\n※ 전체 카탈로그 대상. category 인자(신문·고문헌 등)로 자료유형 정밀 이중수집 가능."
            out += f" '{name}' 컬렉션 정밀검색: {open_url}" + (f"\n※ {note}" if note else "")
            return out
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


# ── KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터 (협약기관 — MOU) : TNA-style structured toolset ──
_KW_DEPTH1 = {"수집": "00001041", "기증": "00001042", "기타": "00001047", "구입": "00001054",
              "기탁": "00001073", "제작": "00001125", "이관": "00001179", "차입": "00001410"}


@mcp.tool()
def koreanwar_search(query: str, scope: str = "archive", page: int = 1, max_results: int = 10,
                     year_from: int = 0, year_to: int = 0, acquisition: str = "") -> str:
    """KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터(koreanwar.or.kr, 전쟁기념관재단 — 협약기관) 통합검색을 서버에서 직접 조회.
    결과카드(제목·archRfcd 영속 참조코드·생산기관·상위계층)를 파싱하며, 상위계층의 NARA Record Group을
    추출해 원본 역추적 링크를 제공한다. 55,000여 건: 문서·지도·사진·필름·음원·구술.
    서버측 필터(실측 검증): year_from/year_to=생산연도 범위, acquisition=수집구분(수집·기증·구입·기탁·
    제작·이관·차입·기타), max_results는 pageSize(10/20/50)로 자동 매핑. scope='battle'이면 전투정보
    DB(개전 초기 69전투 — TNA WO 281·NARA RG 407 교차검증 앵커)를 대신 검색. 자료유형·연대·이용조건
    코드는 source_profile('koreanwar') 참조. KOREANWAR_API_TOKEN 설정 시 OpenAPI 공식 메타 채널(KOGL
    권리정보) 자동 병행. 한글 질의 권장(미군 원본도 한글 재기술 제목으로 히트)."""
    if scope.strip().lower() == "battle":
        list_url = _KW_BASE + "/warList.do"
        try:
            b = _kw_text(list_url)
            cards = []
            for blk in b.split("/warDetail.do?warIdx=")[1:]:
                mi = re.match(r"^(\d+)", blk)
                if not mi:
                    continue
                nm = re.search(r'<span class="text">(.*?)</span>', blk, re.S)
                metas = [f"{_clean(k)}:{_clean(v)}" for k, v in
                         re.findall(r"<dt>(.{1,30}?)</dt>\s*<dd>(.{0,120}?)</dd>", blk[:2500], re.S)]
                cards.append({"idx": mi.group(1), "name": _clean(nm.group(1)) if nm else "?",
                              "meta": " · ".join(metas)})
            t = query.strip()
            matched = [c for c in cards if t in (c["name"] + " " + c["meta"])] if t else cards
            if matched:
                lines = [f"- [warIdx {c['idx']}] {c['name']}{' | ' + c['meta'] if c['meta'] else ''}\n"
                         f"  {_KW_BASE}/warDetail.do?warIdx={c['idx']}" for c in matched[:25]]
                return (f"6·25 전투정보 '{t or '(전체)'}' — {len(matched)}/{len(cards)}건:\n" + "\n".join(lines)
                        + "\n※ 전투명·시기·장소를 앵커로 TNA WO 281·NARA RG 407·koreanwar_search(scope=archive)와 "
                          "교차. DB는 개전 초기(1950.6.25~9.14) 단계 수록(확장 중).")
            return (f"6·25 전투정보 '{t}' — 0건 (전체 {len(cards)}건 중). 현재 DB는 개전 초기(1950.6.25~9.14) "
                    f"전투만 수록 — 이후 시기(백마고지 1952 등)는 미수록. scope=archive로 자료 검색은 가능."
                    + _browse(list_url))
        except Exception as e:
            return _agent_browse("6·25 전투정보", query, list_url, f"자동조회 실패({e})")
    page_size = 50 if max_results > 20 else (20 if max_results > 10 else 10)
    params = {"keyword": query, "viewType": "archive", "page": page, "pageSize": page_size}
    if year_from or year_to or acquisition:
        params["detailYn"] = "Y"
        if year_from:
            params["detailPrdcBegnYYYY"] = year_from
        if year_to:
            params["detailPrdcEdYYYY"] = year_to
        if acquisition in _KW_DEPTH1:
            params["depth1"] = _KW_DEPTH1[acquisition]
    browse = f"{_KW_BASE}/search.do?detailYn=Y&keyword=" + _up.quote(query)
    try:
        total, cards = _kw_search(params)
        lines = []
        for c in cards[:max_results]:
            l = f"- [{c['id']}] {c['title'][:95]}"
            sub = (f"생산: {c['producer'][:70]} | " if c['producer'] else "") + \
                  (f"계층: {c['hierarchy'][:90]}" if c['hierarchy'] else "")
            if sub:
                l += "\n  " + sub
            if c["rg"]:
                l += f"\n  ↔ NARA RG {c['rg']} — nara_search(record_group={c['rg']})로 원본 역추적 가능"
            lines.append(l + "\n  " + c["url"])
        tags = " · ".join(t for t in [f"생산 {year_from or ''}~{year_to or ''}" if (year_from or year_to) else "",
                                      f"수집구분 {acquisition}" if acquisition else ""] if t)
        out = (f"6·25전쟁 아카이브센터 '{query}'{f' [{tags}]' if tags else ''} — 총 {total}건 "
               f"(p.{page}, {page_size}건/페이지):\n" + ("\n".join(lines) or "(0건 — 한글/한자/영문 표기 변형 시도)"))
        try:
            api = _kw_api_scan(query)
        except Exception as e:
            api = {"error": str(e)}
        if api and "hits" in api:
            out += (f"\n\n[② OpenAPI 공식 메타 채널 — {api['checked']}건 스캔 중 {len(api['hits'])}건 매칭 "
                    f"(전체 {api['total']}건)]")
            for h in api["hits"][:max_results]:
                out += (f"\n- [{h['ref']}] {str(h['title'])[:80]} | 공공누리:{h['kogl'] or '-'} · "
                        f"이용조건:{h['useCnd'] or '-'} · 저작권:{h['cpyrYn'] or '-'} · 원문온라인:{h['olinYn'] or '-'}")
        elif api and "error" in api:
            out += f"\n※ OpenAPI 채널 오류: {api['error']}"
        else:
            out += ("\n※ OpenAPI(공식 메타·KOGL 권리정보 채널)는 토큰 승인 후 KOREANWAR_API_TOKEN 설정 시 "
                    "자동 병행 활성 (승인 대기 중에도 이 검색은 정상 동작).")
        return (out + "\n협약기관 — 출처 표기 필수: KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터(전쟁기념관재단). "
                "건별 메타·인접 채굴: koreanwar_item."
                f"\n도서자료 포함 전체·상세검색폼(자료유형·연대·이용조건 코드 필터는 브라우저에서): {browse}")
    except Exception as e:
        return _agent_browse("6·25전쟁 아카이브센터", query, browse, f"자동조회 실패({e})")


def _kw_item_title(page_html):
    ts = [_clean(x) for x in re.findall(r"<h2[^>]*>(.{1,300}?)</h2>", page_html, re.S)]
    ts = [t for t in ts if t and "KOREAN WAR ARCHIVE" not in t.upper()]
    return ts[0] if ts else ""


@mcp.tool()
def koreanwar_item(ref_code: str, radius: int = 0) -> str:
    """KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터 건별 상세 메타데이터 — 제목·생산처/생산자·생산시기·입수처(+입수처 링크:
    NARA 재수집본이면 catalog.archives.gov NAID 원본 직결)·열람 및 이용조건(judge_rights 투입용).
    radius=1~8이면 인접 확장 채굴: archRfcd 말미 일련번호 ±radius를 순회해 동일 시리즈 미발굴 건을
    찾는다(TNA 방식, 정중한 3건 배치 병렬). 협약기관 — 출처 표기 필수."""
    ref0 = ref_code.strip()
    url = f"{_KW_BASE}/searchDetail.do?archRfcd=" + _up.quote(ref0)
    if radius > 0:
        import time as _t
        m = re.match(r"^(.+-)(\d+)$", ref0)
        if not m:
            return "참조코드 형식 오류 — 예: 2022-US-02-AV-D-00207 (말미가 일련번호)"
        prefix, serial_s = m.group(1), m.group(2)
        serial, width = int(serial_s), len(serial_s)
        radius = min(radius, 8)
        refs = [prefix + str(s).zfill(width) for s in range(max(0, serial - radius), serial + radius + 1)]

        def probe(ref):
            try:
                t = _kw_item_title(_kw_text(f"{_KW_BASE}/searchDetail.do?archRfcd=" + _up.quote(ref)))
                mark = "●" if ref == ref0 else "○"
                return f"{mark} {ref} | {t[:90]}" if t else f"  {ref} | (없음)"
            except Exception as e:
                return f"  {ref} | ERROR {e}"

        lines = []
        for i in range(0, len(refs), 3):  # 정중한 병렬: 3건 배치 + 배치 간 200ms
            with _cf.ThreadPoolExecutor(max_workers=3) as ex:
                lines.extend(ex.map(probe, refs[i:i + 3]))
            if i + 3 < len(refs):
                _t.sleep(0.2)
        return (f"인접 채굴 {ref0} ±{radius} (● 기준 · ○ 인접 발굴):\n" + "\n".join(lines)
                + "\n※ 발굴 건은 koreanwar_item(radius=0)으로 메타 확인.")
    try:
        b = _kw_text(url)
        title = _kw_item_title(b)
        rows = [(_clean(k), _clean(v)) for k, v in re.findall(r"<dt[^>]*>\s*(.{1,60}?)\s*</dt>\s*<dd[^>]*>(.{0,400}?)</dd>", b, re.S)]
        rows = [(k, v) for k, v in rows if k and v and v != "~"]
        if not title and not rows:
            return _agent_browse("6·25전쟁 아카이브센터", ref0, url, "상세 메타 미검출 — 참조코드 확인")
        allv = " ".join(v for _, v in rows)
        naid = (re.search(r"catalog\.archives\.gov/id/(\d+)", allv) or [None, ""])[1]
        rg = (re.search(r"Record Group (\d+)", allv) or [None, ""])[1]
        out = f"6·25전쟁 아카이브센터 [{ref0}]\n제목: {title or '?'}\n"
        out += "\n".join(f"· {k}: {v[:200]}" for k, v in rows)
        if naid:
            out += (f"\n↔ NARA 원본 NAID {naid} (입수처 링크 직결) — "
                    f"https://catalog.archives.gov/id/{naid} 에서 고해상 원본·상세 기술 확인")
        if rg:
            out += f"\n↔ NARA RG {rg} — nara_search(record_group={rg})로 시리즈 확장 검색"
        return out + (f"\n{url}\n※ '열람 및 이용조건' 행을 judge_rights에 투입해 권리 초판 판정. "
                      "협약기관 — 출처 표기 필수.")
    except Exception as e:
        return _agent_browse("6·25전쟁 아카이브센터", ref0, url, f"자동조회 실패({e})")


@mcp.tool()
def foia_search(query: str, source: str = "open_go") -> str:
    """정보공개(FOIA) 통합 검색. source: 'open_go'(대한민국 정보공개포털 open.go.kr — 원문정보공개·
    정보공개청구; 로그인 기반이라 브라우저 열람 안내)·'seoul_opengov'(서울정보소통광장 — 서울시 결재문서
    원문공개, 서버 자동조회)·'sen'(서울시교육청 정보공개)·'gyeongnam'(경상남도기록원). 결재문서 원문·
    지방기록물은 지역사·특정사건 발굴의 1차 사료. 미공개 문서는 포털에서 정보공개청구로 요청 가능."""
    src = source.strip().lower()
    if src == "open_go" or not src:
        url = "https://www.open.go.kr/othicInfo/infoList/orginlInfoList.do?searchKeyword=" + _up.quote(query)
        return (_agent_browse("정보공개포털(원문정보공개)", query, url)
                + "\n※ 미공개 문서는 포털에서 정보공개청구로 요청.")
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
    return "source 값: open_go, seoul_opengov, sen, gyeongnam"


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


@mcp.tool()
def cross_search(query: str, sources: str = "all", max_per_source: int = 8) -> str:
    """여러 아카이브를 한 쿼리로 동시 교차수집·병합 (상호보완 동시수집). sources: 'all' 또는 콤마목록
    (tna,ia,gallica,europeana,nara,archives,nlk,nedb,koreanwar). 해외(tna·ia·gallica·europeana)와
    koreanwar(KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터, 협약기관)는 키 불요, 국내(nara·archives·nlk)는 서버 키, nedb는
    NEDB_INDEX_URL(공식 개방파일) 설정 시 포함. 각 결과에 발견 출처 표기 — 복수 출처는 교차확인된
    record. robots가 막은 opengov·서울기록원은 미포함 — 전용 도구/브라우저 도구로."""
    want = (list(_COLLECT.keys()) if sources.strip().lower() == "all"
            else [s.strip().lower() for s in sources.split(",") if s.strip().lower() in _COLLECT])
    if not want:
        return "sources: 'all' 또는 " + ",".join(_COLLECT.keys())
    n = max(1, min(max_per_source, 30))
    items, stats = _collect_merged([(s, (lambda s=s: _COLLECT[s](query, n))) for s in want])
    items.sort(key=lambda it: -len(it["sources"]))
    lines = [f"- [{'+'.join(it['sources'])}] {it['title'][:95]}"
             + (f" ({it['date']})" if it['date'] else "") + (f" {it['url']}" if it['url'] else "")
             for it in items[:45]]
    return (f"교차수집 '{query}' — 채널별 [{' · '.join(stats)}] → 병합 {len(items)}건 (복수출처 우선 정렬):\n"
            + ("\n".join(lines) or "(0)")
            + "\n※ [출처] 복수 표기 = 교차확인된 record. 국내(nara·archives·nlk)는 서버 키, nedb는 "
            "NEDB_INDEX_URL(공식 개방파일) 설정 시 포함. robots가 막은 opengov·서울기록원은 미포함 — 전용 도구/브라우저로.")


@mcp.tool()
def source_profile(institution: str = "list") -> str:
    """기관 자료·이용·활용구조 프로파일 — 발굴 전략 수립용. 자료구조(계층·분류·식별자·메타),
    이용구조(API·인증·쿼리문법·robots·권리), 활용구조(3대 부정합·키워드셋·교차매핑·인접확장·교차검증 조합).
    institution: 'list' 또는 키 (tna·nara·ia·gallica·europeana·nedb·archives·nlk·seoul·warmemo·foia)."""
    t = (institution or "list").strip().lower()
    if t == "list" or t not in PROFILES:
        lines = "\n".join(f"- {k} ({v['name_ko']}) [{v['category']}]" for k, v in PROFILES.items())
        extra = f"\n\n('{institution}' 프로파일 없음)" if (t != "list" and t not in PROFILES) else ""
        return "기관 프로파일 (source_profile institution=<key>):\n" + (lines or "(프로파일 데이터 없음)") + extra
    p = PROFILES[t]; D = p["data"]; A = p["access"]; U = p["use"]
    combos = "\n".join(f"    · {c}" for c in U.get("cross_archive_combos", []))
    vn = ("\n\n【팩트체크 교정】\n- " + "\n- ".join(p["verify"]["notes"])) if (p.get("verify") and p["verify"].get("notes")) else ""
    rob = p["verify"]["robots"] if p.get("verify") else "n/a"
    return (f"{p['name_ko']} ({p['name_en']}) — {p['category']}\n"
            f"════════ ① 자료구조 (Data structure) ════════\n"
            f"· 계층/단위: {D['hierarchy']}\n· 분류체계: {D['classification']}\n· 식별자: {D['identifiers']}\n"
            f"· 기술규칙: {D['metadata_standard']}\n· 범위/규모: {D['scope']}\n· 디지털화: {D['digitization']}\n"
            f"════════ ② 이용구조 (Access structure) ════════\n"
            f"· 채널/엔드포인트: {A['channel']}\n· 인증: {A['auth']}\n· 쿼리문법: {A['query_syntax']}\n"
            f"· 응답형식: {A['response_format']}\n· robots/차단: {A['blocking_notes']}\n· 원문 권리: {A['rights_access']}\n· robots(실측): {rob}\n"
            f"════════ ③ 활용구조 (Utilization structure) ════════\n"
            f"· 3대 부정합: {U['mismatch_summary']}\n· 키워드셋: {U['keyword_ref']}\n· 분류 교차맵: {U['crossmap_ref']}\n"
            f"· 인접확장: {U['adjacent_mining']}\n· 교차검증 조합:\n{combos}\n· 권리판정: {U['rights_rule']}" + vn)


if __name__ == "__main__":
    mcp.run()
