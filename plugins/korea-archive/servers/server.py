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

# ── 다국어 주제 사전 → 색인 언어 자동 변환 ──
# 각 아카이브는 자기 색인 언어로만 검색된다(TNA·NARA·IA·Europeana=영어, Gallica=프랑스어).
# 한국어·일본어·중국어·러시아어·스페인어·독일어·베트남어·힌디어·히브리어·아랍어·카자흐어·
# 몽골어 등 어떤 언어로 질의해도 주제 사전이 인식해 대상 색인 언어로 변환한다.
# 실측: IA 장진호 1건 vs "Chosin Reservoir" 139건, Gallica 병인양요 0 vs 5,853건.
_TOPICS = [
    ("인천\\s?상륙\\s?작전|인천\\s?상륙|仁川上陸|仁川登陆|Инчхонская десантная", "Inchon landing", None),
    ("장진호|長津湖|长津湖", "Chosin Reservoir", None),
    ("흥남\\s?철수|흥남|興南", "Hungnam evacuation", None),
    ("백마고지|白馬高地|白马高地", "White Horse Hill Korea", None),
    ("단장의\\s?능선", "Heartbreak Ridge", None),
    ("펀치볼", "Punchbowl Korea", None),
    ("임진강|臨津江|临津江", "Imjin River", None),
    ("그로스터|글로스터", "Gloucestershire Regiment Korea", None),
    ("거제도|巨濟島|巨济岛", "Koje Island", None),
    ("판문점|板門店|板门店|Пханмунджом", "Panmunjom", None),
    ("38\\s?선|삼팔선|三八線|三八线", "38th parallel Korea", None),
    ("휴전\\s?협정|정전\\s?협정|휴전|정전|停戦|停战|休戰|перемирие|armisticio|Waffenstillstand", "Korea armistice", None),
    ("포로|捕虜|战俘|военнопленн\\w*", "prisoners of war Korea", None),
    ("노획", "captured Korea", None),
    ("병인양요|丙寅洋擾|병인박해", "French expedition Korea 1866", "expédition de Corée 1866"),
    ("신미양요|辛未洋擾", "United States expedition Korea 1871", "Corée expédition américaine 1871"),
    ("강화도|江華島|江华岛|강화", "Kanghwa", "île Kanghoa"),
    ("파리\\s?외방전교회", "Paris Foreign Missions Korea", "Missions étrangères de Paris"),
    ("선교사|宣教師|宣教师|传教士|missionnaires?|misioneros|Missionare|миссионер\\w*", "missionaries Korea", "missionnaires"),
    ("천주교|가톨릭|카톨릭|순교", "Catholic Korea martyrs", "catholique Corée"),
    ("한국전쟁|6[·.]25|조선전쟁|朝鮮戦争|朝鲜战争|朝鮮戰爭|抗美援朝|Корейская война|Корей соғысы"
     "|Солонгосын дайн|Chiến tranh Triều Tiên|कोरियाई युद्ध|מלחמת קוריאה|الحرب الكورية"
     "|Koreakrieg|Guerra de Corea|Guerra da Coreia|Guerre de Corée", "Korean War", "guerre de Corée"),
    ("러일전쟁|日露戦争|日俄战争", "Russo-Japanese War Korea", "guerre russo-japonaise"),
    ("청일전쟁|日清戦争|甲午战争", "Sino-Japanese War Korea 1894", None),
    ("일제\\s?강점기|조선총독부|朝鮮總督府|朝鮮総督府|植民地朝鮮", "Chosen Japan colonial", None),
    ("대한제국|大韓帝國|大韓帝国", "Korean Empire Corea", "Empire de Corée"),
    ("맥아더|マッカーサー|麦克阿瑟|Макартур", "MacArthur", None),
    ("이승만|李承晩|李承晚", "Syngman Rhee", None),
    ("김일성|金日成", "Kim Il Sung", None),
    ("압록강|鴨綠江|鸭绿江", "Yalu", None),
    ("낙동강|洛東江|洛东江", "Naktong", None),
    ("서울|한양|ソウル|首爾|首尔|漢城|汉城|Сеул|Seúl", "Seoul", "Séoul"),
    ("부산|釜山|Пусан", "Pusan", "Fusan"),
    ("평양|平壌|平壤|Пхеньян", "Pyongyang", None),
    ("인천|제물포|仁川", "Inchon", "Chemulpo"),
    ("제주|濟州|济州|Чеджу", "Cheju Quelpart", "Quelpaert"),
    ("해방|解放", "Korea liberation 1945", "Corée libération 1945"),
    ("영상|필름|映像|フィルム|视频|кинохроника", "film", None),
    ("사진|寫真|写真|照片|фотографи\\w*", "photograph", "photographie"),
    ("지도|地圖|地图|карт[аы]\\w*", "map", "carte"),
    ("신문|新聞|新闻|газет\\w*", "newspaper", "journal"),
    ("전투|戦闘|战斗|битва|сражение", "battle", "bataille"),
    # Corea·Coreia 등 라틴 표기는 넣지 않는다: 당대 표기 변형 검색(tna_search "Corea" 등)이
    # Korea로 강제 치환되면 방법론이 무력화됨. 악상 있는 Corée만 프랑스어 확정으로 사상.
    ("조선|한국|고려|朝鮮|韓國|韩国|朝鲜|Корея|Коре[еию]|Corée|كوريا|קוריאה"
     "|कोरिया|Hàn Quốc|Triều Tiên|Солонгос|Корей", "Korea", "Corée"),
    ("기록|자료|문서|관련|찾아줘|記録|資料|文書|档案|документ\\w*|материал\\w*", " ", " "),
]
_NON_LATIN = re.compile(r"[^\x00-ɏ]+")  # 라틴 확장(악상 포함) 밖 = 대상 색인이 못 읽는 스크립트
_EN_ANCHOR = re.compile(r"korea|corea|chosen|chosin|seoul|pusan|inchon|hungnam|panmunjom|imjin"
                        r"|koje|yalu|naktong|kanghwa|pyongyang|macarthur|rhee|kim il", re.I)
_FR_ANCHOR = re.compile(r"cor[ée]e|séoul|fusan|chemulpo|quelpaert|kanghoa|missionnaires|tchosen", re.I)

def _to_index_lang(q, lang):
    f = q
    for pat, en, fr in _TOPICS:
        f = re.sub(pat, " " + ((fr or en) if lang == "fr" else en) + " ", f, flags=re.I)
    changed = f != q
    foreign = bool(_NON_LATIN.search(f))
    if not changed and not foreign:
        return None
    f = _NON_LATIN.sub(" ", f)
    f = re.sub(r"\(\s*\)|\[\s*\]|\"\s*\"", " ", f)
    f = re.sub(r"\s+", " ", f).strip()
    anchor = _FR_ANCHOR if lang == "fr" else _EN_ANCHOR
    if not anchor.search(f):
        f = (("Corée " if lang == "fr" else "Korea ") + f).strip()
    return f or ("Corée" if lang == "fr" else "Korea")

def _ko_en(q):
    return _to_index_lang(q, "en")


@mcp.tool()
def tna_search(query: str, max_results: int = 20) -> str:
    """영국 국립기록관(TNA) Discovery에서 한국 관련 기록 검색. 한국어·일본어·중국어·러시아어 등
    다국어 질의를 영문 색인어로 자동 변환(임진강→Imjin River, 長津湖→Chosin Reservoir,
    Корейская война→Korean War …). 참조코드('FO 371/84053')는 자동으로 정확구 처리.
    예: '임진강 전투', 'Korea armistice', 'FO 371 FK1015'"""
    en = _ko_en(query)
    eff = en or query
    q = f'"{eff}"' if re.match(r"^[A-Z]+ \d+/\d+$", eff.strip()) else eff
    recs = []
    for batch, total in T._search(q, page_size=min(max_results, 100), max_pages=1, sleep=0):
        recs += [T._extract(r, "mcp", eff) for r in batch]
    tag = f" → 영문 자동 변환 '{eff}'" if en else ""
    return f"TNA 검색 '{query}'{tag} — 총 {total}건 중 {len(recs[:max_results])}건:\n" + _fmt(recs, max_results)

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
    다국어 질의(한국어·日本語·中文·Русский 등)는 영문 색인어로 자동 변환(장진호/長津湖→Chosin Reservoir …).
    record_group으로 RG 교차 정밀검색(예: 242), moving_images_only로 영상 한정."""
    key = os.environ.get("NARA_API_KEY")
    if not key: return "NARA_API_KEY 미설정 — Catalog_API@nara.gov 로 무료 발급(이름+이메일)."
    _en = _ko_en(query)
    query = _en or query
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
    'mediatype:movies AND (keijo OR chosen)'. 다국어 질의(한국어·日本語·中文 등)는 영문 색인어로
    자동 변환. identifier를 주면 해당 아이템의 메타데이터·원본 파일 목록(다운로드 전 크기 파악)을
    대신 반환한다."""
    if identifier:
        data = http_json(f"https://archive.org/metadata/{identifier}")
        md = data.get("metadata") or {}
        files = [f for f in (data.get("files") or []) if f.get("source") == "original"][:10]
        return (f"제목: {md.get('title')}\n설명: {str(md.get('description'))[:300]}\n"
                f"연대: {md.get('date')} | 라이선스: {md.get('licenseurl') or md.get('rights') or '표기 없음'}\n"
                "원본 파일:\n" + "\n".join(f"- {f['name']} ({int(f.get('size',0))/1e6:.1f}MB)" for f in files))
    if not query:
        return "query 또는 identifier 중 하나는 필수."
    query = _ko_en(query) or query
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


def _gallica_ko_fr(q):
    return _to_index_lang(q, "fr")


@mcp.tool()
def gallica_search(query: str, max_results: int = 15) -> str:
    """프랑스 국립도서관 Gallica 검색 (SRU API, 키 불요). 다국어 질의(한국어·日本語·中文 등)를
    프랑스어 색인어로 자동 변환(병인양요→expédition de Corée 1866, 선교사→missionnaires, 조선→Corée …).
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
    대량 사용 시 apis.europeana.eu 무료 키를 EUROPEANA_API_KEY로. 다국어 질의(한국어·日本語·中文 등)는
    영문 색인어로 자동 변환. media_type: 'VIDEO'|'IMAGE'|'TEXT'|'SOUND'. 예: europeana_search('Corée', media_type='IMAGE')"""
    import urllib.parse, json as _json, urllib.request
    key = os.environ.get("EUROPEANA_API_KEY") or "api2demo"
    demo = not os.environ.get("EUROPEANA_API_KEY")
    query = _ko_en(query) or query
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



REPORT_RULES = """HTML 발굴 보고서 작성 규칙 (18) — 잡지·저널급 편집 기준
1. 파일명: [주제영문]_records_[연도범위].html — 조사 완료 시 기본 산출물
2. 지면 구조(잡지형): masthead → kicker → 표제(h1) → standfirst → byline(기관 chip) → 목차(nav.toc) → 히어로 figure → Ⅰ서사 → Ⅱ핵심 기록 카드 → Ⅲ영상 필름스트립 → Ⅳ전수 목록 표 → Ⅴ재현 쿼리(details) → Ⅵ권리·게재 윤리 → 출처 총람(.sources) → footer
3. 서사 우선: 표만 나열 금지 — 발굴 경위·의미를 에세이로 서술(리드 문단 .lead 드롭캡, 풀인용 .pull 1개 이상). 문단이 실물을 설명하면 그 문단 옆에 인라인 도판(.fig-inline 플로트)을 배치 — 잡지처럼 글과 그림이 같은 화면에 보이게. 문체는 담백·구체 — 과장어(놀라운·혁신적 등)와 AI투 금지
4. 실물 이미지 필수: 게재 가능(권리 A/B+게재윤리 1·2단계) 기록은 기관 공개 원본을 base64 임베드 — 히어로 1장+핵심 기록마다, 공개 컷은 전량(.sheet 콘택트시트·컷별 라벨). 비식별판 우선. 이미지는 max-width:100% 자동 축소. 환경별: 로컬=base64 임베드 / 웹·모바일(파일·base64 불가)=기관 공개 원본 URL을 img src로 직접 참조하고 footer에 그 사실을 명기. 한 장도 못 실으면 사유를 Ⅵ절에 명기
5. 모든 이미지에 figcaption + .credit 필수: "출처: 기관 정식명(국가) · 식별자 · 촬영자/생산자 · 원본 링크" — 출처 없는 이미지는 싣지 않는다
6. 영상 기록은 .film 필름스트립: 장면 전환마다 프레임을 충분히 추출(권장 8~16장)해 타임코드(.tc)+한 줄 설명으로 나열 — 표제가 가린 장면(ETC 뒤)을 드러내 원본을 직접 보고 싶게 만든다. 슬레이트·표지판 판독 프레임은 별도 확대 figure. 블록 끝에 .cta "▶ 원본 영상 보기 — [기관] 카탈로그"
7. 핵심 기록 3~6건은 .record 카드로: 이미지 + 한국어 제목(원제 병기) + .prov 출처 계보(국가→기관→RG/시리즈→상자→식별자) + 요약 + 바로가기 버튼 + 권리 배지
8. 전수 목록 표(부록형): 식별자·원제 / 연대 / 소장처·청구정보(RG·Entry·Box) / 내용 / 바로가기(원문→해제→카탈로그) / 권리초판 배지(b-A 공개확정 · b-B PD추정 · b-C 허가필요 · b-D 지위불명)
9. 출처 명시(전 지면): byline·본문에 기관 chip(국기 이모지+정식명 — 🇺🇸 NARA · 🇬🇧 TNA · 🇫🇷 BnF Gallica · 🇪🇺 Europeana · 🇺🇸 archive.org · 🇰🇷 국가기록원 · 🇰🇷 KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터 등), 말미 .sources에 인용 기관 총람(국기·정식명·청구정보·이용조건·링크)
10. 재현 쿼리는 details 접이식 — 실제 실행한 쿼리만(목적/쿼리/URL 인코딩 실행 링크). '0건 ≠ 부재' note(인접 상자 ±2·피스 ±15 권고) 포함
11. 종합 색인·최신 연구 목록(ul.src) — details로 접어도 된다
12. Ⅵ 권리 절: 법적 근거(17 U.S.C. §105 · 36 CFR 1254.62 · Crown/OGL · domaine public · KOGL) + '출판 전 인간 최종 확인 필수' + D등급 공개 금지. 민감 주제(위안부·포로·학살)는 피해자 존엄 문구와 게재윤리 4단계(거부할 수 없었던 처지의 촬영 = 화면 미사용) 적용
13. 링크·수치는 도구 호출로 실확인한 것만 — 추정 URL 금지, footer에 '모든 링크 [날짜] 접속 확인' 명기
14. 연표·지도·관계도는 인라인 svg로 직접 작성 가능. 외부 리소스 금지(폰트·CDN) — 로컬은 단일 파일 자기완결(base64), 웹·모바일 산출만 기관 공개 이미지 URL 참조 예외 허용
15. 인쇄 대응: 템플릿의 @media print 유지 — 보고서는 그대로 출판물처럼 인쇄 가능해야 한다
16. 링크 신뢰장치: ①digitised 기록은 카탈로그 무료 미리보기 이미지를 공식 엔드포인트로 확보해 원문 figure로 임베드(예: TNA /image/getimage — 워터마크 원상태, 유료 전체본은 안내만) ②그 외 주요 링크는 페이지 캡쳐본 figure+credit(갈무리 일자) ③자동화 차단 시 명기하고 API 기술 원문 인용표로 대체. 훈격·날짜·건수는 API 원문 대조 '검증 기록'으로 — 초판 오류는 정정 이력을 남긴다
17. 카드뉴스·포스터 병행: 보고서와 함께 캐러셀(기본 8장, 1080×1080)과 포스터 시리즈(1080×1350 세로형 4~6장 — 표제·인물·문서·검증·초대의 연작 서사, 같은 검수 기준 — insta-carousel 스킬 또는 report_template(kind='carousel') 참조)을 제작하고, 보고서 말미 '카드뉴스' 절에 .cards-grid로 임베드한다 — 무크롭 전체 노출 + 카드별 figcaption, 잘림·겹침 금지. 커버는 히어로와 같은 실물 이미지, 검증 노트·따라하기 카드 포함, 보고서와 출처 대장 공유. PNG 원본·caption.txt·sources.txt를 보고서와 함께 납품
18. 더 보기 절(Ⅷ): 출처 총람 직전에 관련 공개 콘텐츠 소개 — 뉴스(📰)·기관 아카이브(🏛️)·해설/백과(📚)·SNS/영상 등을 카테고리 이모지+한 줄 설명으로. 접속 확인한 링크만(확인일 명기), 미확보 카테고리는 그 사실+추천 검색어 명시 — 발굴을 현재의 기억과 잇는 절"""

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{제목}} — 기록 발굴 보고</title>
<style>
  :root{
    --paper:#f5f1e8; --card:#fffdf7; --ink:#211d18; --sub:#6b6257; --faint:#8d8477;
    --line:#dcd4c5; --hair:#c8beac; --accent:#8a3033; --deep:#5f1f22; --gold:#a8853c; --blue:#1d5fa8;
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;background:var(--paper);color:var(--ink);font-size:16.5px;line-height:1.78;
    font-family:'Noto Serif KR','Nanum Myeongjo','Apple Myungjo',Batang,Georgia,'Times New Roman',serif}
  .wrap{max-width:880px;margin:0 auto;padding:0 26px 90px}
  .sans{font-family:'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif}
  /* ── 머리지면 ── */
  .masthead{display:flex;justify-content:space-between;align-items:baseline;gap:12px;padding:24px 0 12px;
    border-bottom:3px double var(--ink);font-size:11.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--sub)}
  .masthead b{color:var(--accent)}
  .kicker{margin:52px 0 10px;font-size:12.5px;letter-spacing:.3em;color:var(--accent);text-transform:uppercase;font-weight:700}
  h1{margin:0 0 16px;font-size:clamp(30px,5.4vw,46px);line-height:1.22;font-weight:800;letter-spacing:-.01em}
  .standfirst{font-size:19px;line-height:1.68;color:var(--sub);margin:0 0 22px}
  .byline{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;padding:13px 0;margin-bottom:6px;
    border-top:1px solid var(--hair);border-bottom:1px solid var(--hair);font-size:12.5px;color:var(--sub)}
  nav.toc{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 30px;font-size:12.5px}
  nav.toc a{border:1px solid var(--hair);border-radius:999px;padding:4px 13px;color:var(--sub);text-decoration:none}
  nav.toc a:hover{border-color:var(--accent);color:var(--accent)}
  /* ── 본문 ── */
  h2{margin:64px 0 18px;font-size:23px;font-weight:800;scroll-margin-top:20px}
  h2 .no{font-family:Georgia,serif;font-style:italic;color:var(--accent);margin-right:10px}
  h2::after{content:"";display:block;width:54px;height:3px;background:var(--accent);margin-top:10px}
  p{margin:12px 0}
  .lead::first-letter{float:left;font-size:56px;line-height:.9;padding:7px 10px 0 0;font-weight:800;color:var(--accent)}
  .pull{margin:34px 8px;padding:4px 0 4px 22px;border-left:3px solid var(--gold);
    font-size:20.5px;line-height:1.6;color:var(--deep);font-style:italic}
  a{color:var(--blue);text-decoration:none;border-bottom:1px dotted #9ab6d6}
  a:hover{color:var(--accent);border-bottom-color:var(--accent)}
  /* ── 그림·크레디트 ── */
  figure{margin:34px 0}
  figure img{width:100%;display:block;border:1px solid var(--line);background:#171412}
  figure svg{width:100%;height:auto;display:block;border:1px solid var(--line);background:var(--card)}
  figcaption{font-size:13px;color:var(--sub);margin-top:9px;line-height:1.6}
  figcaption b{color:var(--ink)}
  .credit{display:block;font-size:11.5px;color:var(--faint);letter-spacing:.04em;margin-top:3px}
  img{max-width:100%;height:auto}
  h2{clear:both}
  /* 인라인 도판 — 문단 옆 플로트, 좁으면 전폭 */
  .fig-inline{float:right;width:min(46%,360px);margin:6px 0 14px 26px}
  .fig-inline.left{float:left;margin:6px 26px 14px 0}
  @media (max-width:640px){.fig-inline{float:none;width:100%;margin:16px 0}}
  /* 콘택트시트 — 공개 컷 전량 수록(.sub 라벨) */
  .sheet{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  .sheet figure{margin:0}
  .sheet img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;border:1px solid var(--line)}
  .sheet .sub{font-size:12px;color:var(--sub);margin-top:5px;line-height:1.5}
  @media (max-width:640px){.sheet{grid-template-columns:1fr 1fr}}
  /* 카드 갤러리 — 무크롭+카드별 캡션, 잘림 금지 */
  .cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px;margin:20px 0}
  .cards-grid figure{margin:0}
  .cards-grid img{width:100%;height:auto;display:block;border:1px solid var(--line)}
  .cards-grid figcaption{font-size:12px;color:var(--sub);margin-top:5px;line-height:1.5}
  /* ── 출처 chip ── */
  .chip{display:inline-flex;align-items:center;gap:6px;padding:3px 11px;border:1px solid var(--hair);
    border-radius:999px;background:var(--card);font-size:12px;color:var(--sub);white-space:nowrap}
  /* ── 기록 카드 ── */
  .record{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--accent);
    margin:26px 0;padding:22px 24px;display:grid;grid-template-columns:210px 1fr;gap:20px}
  .record>img{width:100%;border:1px solid var(--line);align-self:start}
  .record h3{margin:0 0 6px;font-size:18px}
  .record .prov{font-size:12px;color:var(--faint);letter-spacing:.03em;margin:4px 0 10px}
  .record .prov b{color:var(--sub)}
  .btns{margin-top:12px;display:flex;flex-wrap:wrap;gap:8px}
  .btns a{border:1px solid var(--hair);border-radius:4px;padding:5px 13px;font-size:12.5px;background:var(--paper)}
  @media (max-width:640px){.record{grid-template-columns:1fr}}
  /* ── 영상 필름스트립 ── */
  .film{background:#171412;color:#e9e2d6;border:1px solid #000;margin:38px 0;padding:22px 22px 24px}
  .film h3{margin:0 0 4px;font-size:19px;color:#f4ecdd}
  .film .prov{font-size:12px;color:#9d9384;margin-bottom:6px}
  .film p{color:#cfc5b4;font-size:14.5px}
  .filmstrip{display:flex;gap:10px;overflow-x:auto;padding:12px 2px 14px;scroll-snap-type:x mandatory}
  .frame{flex:0 0 200px;scroll-snap-align:start;margin:0}
  .frame img{width:100%;aspect-ratio:4/3;object-fit:cover;border:1px solid #3a332c;transition:.18s;filter:sepia(.08)}
  .frame:hover img{filter:none;transform:scale(1.02)}
  .frame figcaption{font-size:12px;color:#bdb3a2;margin-top:5px}
  .tc{display:inline-block;font:700 11px/1.7 Consolas,Menlo,monospace;background:#2a241f;color:#d9c691;
    padding:0 7px;border-radius:3px;margin-right:6px}
  .cta{display:inline-block;margin-top:14px;padding:11px 24px;background:var(--accent);color:#fff!important;
    font-weight:700;letter-spacing:.05em;border:none;border-radius:4px}
  .cta:hover{background:var(--deep)}
  .hint{font-size:11.5px;color:#7d7466;margin-top:6px}
  /* ── 표(부록형) ── */
  table{width:100%;border-collapse:collapse;font-size:13.5px;margin:18px 0;background:var(--card)}
  th{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--sub);text-align:left;
    padding:10px;border-bottom:2px solid var(--ink);white-space:nowrap}
  td{padding:11px 10px;border-bottom:1px solid var(--line);vertical-align:top}
  .badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11.5px;font-weight:700;white-space:nowrap}
  .b-A{background:#e3f0fb;color:#1d5fa8;border:1px solid #b9d4ee}
  .b-B{background:#e6f2e6;color:#2c6e2f;border:1px solid #bcd9bd}
  .b-C{background:#fff3df;color:#9a6b15;border:1px solid #ead9b0}
  .b-D{background:#fbe7e7;color:#a33333;border:1px solid #e6bcbc}
  code{background:#eee9dd;padding:2px 6px;border-radius:4px;font-size:13px;font-family:Consolas,Menlo,monospace}
  .note{background:#fbf5e3;border:1px solid #e2d5ad;border-radius:8px;padding:14px 18px;margin:16px 0;font-size:14px}
  ul.src{padding-left:20px;font-size:14px}
  ul.src li{margin:6px 0}
  .small{font-size:13px;color:var(--sub)}
  /* ── 접이식 ── */
  details{background:var(--card);border:1px solid var(--line);border-radius:6px;margin:14px 0}
  summary{cursor:pointer;padding:13px 18px;font-weight:700;font-size:14.5px;list-style:none}
  summary::-webkit-details-marker{display:none}
  summary::before{content:"▸";display:inline-block;color:var(--accent);margin-right:9px;transition:.15s}
  details[open] summary::before{transform:rotate(90deg)}
  details .inner{padding:0 18px 16px}
  /* ── 출처 총람·꼬리 ── */
  .sources{margin-top:64px;padding:20px 22px;background:var(--card);border:1px solid var(--line)}
  .sources h2{margin-top:0}
  .sources li{margin:7px 0;font-size:13.5px}
  footer{margin-top:44px;border-top:3px double var(--ink);padding-top:14px;font-size:12px;color:var(--sub)}
  @media print{
    body{background:#fff;font-size:11pt}
    .wrap{max-width:100%;padding:0}
    nav.toc,.hint{display:none}
    .film{-webkit-print-color-adjust:exact;print-color-adjust:exact}
    details{border:none}details .inner{display:block}
  }
</style>
</head>
<body>
<div class="wrap">

<div class="masthead sans"><span><b>KOREA ARCHIVE</b> 통합검색 — 기록 발굴 보고</span><span>{{호수 또는 시리즈명}} · {{작성일}}</span></div>

<div class="kicker sans">{{분류 킥커 — 예: 발굴 보고 · 1950 한국전쟁 영상}}</div>
<h1>{{표제 — 신문 표제처럼, 발굴의 핵심을 한 문장으로}}</h1>
<p class="standfirst">{{스탠드퍼스트 2~3문장 — 무엇을·어디서·왜}}</p>
<div class="byline sans">
  <span>대상 시기 <b>{{대상시기}}</b></span> · <span>조사 도구 <b>KOREA ARCHIVE 통합검색</b></span>
  <span class="chip">🇺🇸 {{NARA · RG 111}}</span><span class="chip">🇬🇧 {{TNA · FO 371}}</span><span class="chip">🇰🇷 {{KOREAN WAR ARCHIVES}}</span>
  <!-- 조사 기관 전부 chip -->
</div>
<nav class="toc sans"><a href="#s1">서사</a><a href="#s2">핵심 기록</a><a href="#s3">영상</a><a href="#s4">전수 목록</a><a href="#s5">재현 쿼리</a><a href="#s6">권리·출처</a><a href="#s7">카드뉴스</a><a href="#s8">더 보기</a></nav>

<!-- 히어로: 실물 1장(권리·윤리 통과), credit 필수 -->
<figure>
  <img src="data:image/jpeg;base64,{{BASE64}}" alt="{{대체 텍스트}}">
  <figcaption><b>그림 1.</b> {{한 줄 설명 — 보는 이가 멈추게 되는 이유}}
  <span class="credit">출처: {{기관 정식명}}({{국가}}) · {{식별자}} · {{촬영자/생산자, 연도}} · <a href="{{원본URL}}">원본</a></span></figcaption>
</figure>

<h2 id="s1"><span class="no">I.</span> {{서사 절 제목 — 발굴 경위}}</h2>
<p class="lead">{{리드(드롭캡) — 질문에서 발견까지}}</p>
<p>{{서사 — 전략·단서·판독, 확인/추정 구분}}</p>
<!-- 인라인 도판: 설명하는 문단 옆에 배치 -->
<figure class="fig-inline">
  <img src="data:image/jpeg;base64,{{BASE64}}" alt="{{설명}}">
  <figcaption><b>그림 N.</b> {{이 문단이 설명하는 실물 — 판독 포인트(새김 문자·손글씨 등)}}
  <span class="credit">출처: {{기관 정식명(국가) · 식별자 · <a href="{{원본URL}}">원본</a>}}</span></figcaption>
</figure>
<p>{{인라인 도판이 붙는 문단 — 도판 속 실물을 직접 설명한다.}}</p>
<blockquote class="pull">{{풀인용 — 슬레이트 판독문·문서 원문·핵심 발견 한 구절}}</blockquote>
<p>{{서사 계속. 문단이 실물을 설명하면 반드시 그 옆에 figure 배치(각각 figcaption+credit 필수).}}</p>

<h2 id="s2"><span class="no">II.</span> 핵심 기록</h2>
<!-- 핵심 3~6건 카드. 이미지 없으면 img 생략 -->
<div class="record">
  <img src="data:image/jpeg;base64,{{BASE64}}" alt="{{설명}}">
  <div>
    <h3>{{한국어 제목 — 원제 병기}}</h3>
    <div class="prov sans">{{🇺🇸 미국}} → <b>{{NARA}}</b> → {{RG 111 · Entry NM-xx · Box nn}} → <b>{{식별자}}</b></div>
    <p>{{요약 2문장 — 표제가 가린 것부터}}</p>
    <div class="btns sans"><a href="{{원문URL}}">원문 보기</a><a href="{{카탈로그URL}}">카탈로그</a><span class="badge b-B">B · PD 추정</span></div>
  </div>
</div>

<h2 id="s3"><span class="no">III.</span> 영상 기록 — 프레임으로 먼저 본다</h2>
<!-- 영상 1건당 .film 1개 — 프레임 8~16장, 표제가 가린 장면을 드러낸다 -->
<div class="film">
  <h3>{{영상 제목 (원제)}}</h3>
  <div class="prov sans">{{🇺🇸 NARA · RG 111 · 식별자}} · {{러닝타임}} · {{연대}} · 촬영 {{부대/촬영자}}</div>
  <p>{{왜 중요한가 — 표제와 실제의 간극 2문장}}</p>
  <div class="filmstrip">
    <figure class="frame"><img src="data:image/jpeg;base64,{{BASE64}}" alt="{{장면}}"><figcaption><span class="tc">{{00:00:12}}</span>{{한 줄 장면 설명}}</figcaption></figure>
    <!-- 프레임 반복 (tc 타임코드+한 줄 설명) -->
  </div>
  <div class="hint sans">← 좌우 스크롤 · {{N}}장</div>
  <a class="cta sans" href="{{원본영상URL}}">▶ 원본 영상 보기 — {{기관}} 카탈로그</a>
</div>

<h2 id="s4"><span class="no">IV.</span> 발굴 기록 전수 목록</h2>
<table>
  <thead><tr><th>#</th><th>식별자 · 원제</th><th>연대</th><th>소장처 / 청구정보</th><th>관련 내용</th><th>바로가기</th><th>권리초판</th></tr></thead>
  <tbody>
    <tr><td>1</td><td><strong>{{원제}}</strong><br><span class="small">{{생산기관·시리즈}}</span></td><td>{{연대}}</td><td>{{소장처}} <strong>{{RG/참조코드}}</strong>{{, Entry·Box}}</td><td>{{핵심 내용}}</td><td><a href="{{원문URL}}">원문</a> · <a href="{{카탈로그URL}}">카탈로그</a></td><td><span class="badge b-B">B</span></td></tr>
    <!-- 행 반복. 사진·영상 사료가 많으면 표②로 분리 -->
  </tbody>
</table>

<h2 id="s5"><span class="no">V.</span> 재현 가능한 조사</h2>
<details open>
  <summary>재현용 검색 쿼리 — 실제 실행분만</summary>
  <div class="inner">
  <table>
    <thead><tr><th>목적</th><th>쿼리</th><th>실행</th></tr></thead>
    <tbody><tr><td>{{목적}}</td><td><code>{{쿼리}}</code></td><td><a href="{{URL인코딩된 검색URL}}">검색 실행</a></td></tr></tbody>
  </table>
  </div>
</details>
<div class="note"><strong>0건 ≠ 부재.</strong> {{미전산화 + 인접 상자·피스 추가 조사 권고}}</div>
<details>
  <summary>종합 색인 · 최신 연구</summary>
  <div class="inner"><ul class="src"><li><a href="{{URL}}">{{제목}}</a> — {{한 줄 설명}}</li></ul></div>
</details>

<h2 id="s6"><span class="no">VI.</span> 권리 판정과 게재 윤리</h2>
<p>{{판정 요약+법적 근거}}. <strong>출판 전 인간 최종 확인 필수</strong>, <span class="badge b-D">D등급</span> 공개 금지. {{민감 주제면 존엄·게재윤리 4단계 문구}}</p>

<!-- Ⅶ(선택) 카드뉴스 갤러리 — 미제작 시 절·toc 삭제 -->
<h2 id="s7"><span class="no">VII.</span> 카드뉴스 — 이 발굴을 {{N}}장으로</h2>
<p>{{소개 1문장 — 커버=히어로 실물, 출처 대장 공유}}</p>
<div class="cards-grid">
  <figure><img src="data:image/jpeg;base64,{{카드1 축소본}}" alt="카드 1 — 커버"><figcaption>{{1 — 커버 한 줄 설명}}</figcaption></figure>
  <!-- 카드 반복 (권장 8장, 축소 maxdim 540) — 무크롭 전체 노출·카드별 figcaption 필수, 잘림·겹침 금지 -->
</div>
<p class="small">게시용 1080×1080 PNG 원본 + 캡션(caption.txt) + 이미지 출처 대장(sources.txt)을 보고서와 함께 납품.</p>

<!-- Ⅷ 더 보기 — 접속 확인 링크만, 미확보 카테고리는 명시 -->
<h2 id="s8"><span class="no">VIII.</span> 더 보기 — 관련 기사·콘텐츠</h2>
<p>{{한 줄 — 발굴과 현재의 기억}}</p>
<ul class="src">
  <li>📰 <a href="{{URL}}">{{기사 제목}}</a> — {{매체(보도일)}} · {{한 줄 설명}}</li>
  <li>🏛️ <a href="{{URL}}">{{기관 아카이브·현장 기록}}</a> — {{기관명}}</li>
  <li>📚 <a href="{{URL}}">{{해설·백과}}</a> — {{한 줄 설명}}</li>
  <!-- 유튜브·인스타 등 SNS/영상: 검증된 공식 게시물만. 미확보 시 아래 문구로 대체 -->
</ul>
<p class="small">※ {{미확보 카테고리 명시 + 추천 검색어}} · 전부 {{확인일}} 접속 확인.</p>

<div class="sources">
  <h2 style="margin:0 0 10px;font-size:17px">기록 출처 <span class="small">Archives cited</span></h2>
  <ul class="src">
    <li>{{국기}} <b>{{기관 정식명}}</b> — {{청구정보·이용조건}} · <a href="{{URL}}">{{도메인}}</a></li>
    <!-- 전 기관: 국기·정식명·청구정보·이용조건·링크 -->
  </ul>
</div>

<footer>
  발굴 방법론: KOREA ARCHIVE 통합검색 · 모든 링크·수치 {{확인일}} 도구 확인 · 이미지 출처 표기 유지.{{웹 산출이면: 이미지는 기관 공개 URL 참조임을 명기}}
</footer>
</div>
</body>
</html>"""

CAROUSEL_RULES = """인스타 캐러셀 카드뉴스 제작 규칙 (12) — 1080×1080 PNG 6~10장 + 캡션·출처 대장
1. 파이프라인: 재료 파악 → 발굴조사(실존 대상이면) → 실물 이미지 소싱·라이선스 판정 → 서사 설계 → HTML 카드 작성 → 1080×1080 렌더 → 전 카드 육안 검수(생략 금지) → 캡션·해시태그
2. 서사 아크(장수에 맞게 병합, 기본 8장): ①커버 후킹(실물 풀블리드+숫자·반전 훅) ②디테일/원리 확대 ③~⑥증거(실물 이미지 카드 — 심장) ⑦정리(표·지도·타임라인) ⑧검증 노트 ⑨따라하기(재현 단계) ⑩CTA(행동 1개+댓글 유도+출처·권리 고지)
3. 실물 이미지가 신뢰를 만든다: 주제가 실존 대상(기관·유물·사건·인물)이면 퍼블릭 도메인/공공누리 실물을 능동 발굴해 쓴다. 기관 비식별(블러)판 제공 시 우선 사용
4. 이미지 카드마다 출처 캡션(.credit) 필수: "출처: 기관 정식명, 식별번호 (라이선스)" — 식별번호를 알면서 생략하면 부정확한 출처다. 이미지별 출처 대장(sources.txt) 동봉, 라이선스 미확정이면 '게시 전 [권리자] 확인' 안내
5. 사실 검증: 제목만 믿지 않는다 — 생산일자·원판번호·카탈로그 API 원문까지 대조. 실증 안 된 어록 금지(전승은 '전해지는 말'). 검증 불가한 비교 대신 산술
6. 레이아웃 다양화: 같은 아키타입 반복 금지 — 한 캐러셀에 3개 이상 혼합(풀블리드 커버·타임라인·인물+폴라로이드·문서 인용 docquote·빅넘버·목록 reel·파노라마 필름스트립·부채꼴 스택)
7. 겹침·잘림 절대 금지(최다 결함): 모든 콘텐츠는 .col(하단 안전영역 150px) 안에 — 페이지번호·브랜드와 구조적으로 안 겹치게. credit에 margin-top:auto 금지(고정 마진). 이미지는 고정 높이+object-fit:cover. 세로 예산: 키커+제목 제외 콘텐츠 가용 ~650px — 초과하면 잘린다
8. 검증 노트 카드가 차별점: 조사 중 발견한 반전(오표기·훈격 정정·인접 발굴)을 한 장으로 — 콘텐츠의 백미이자 신뢰 장치
9. 민감 주제(포로·사망자·학살·희생자): 존엄을 지키는 서술 + 보수적 이미지 선택 + 캡션에 존엄 문구
10. 캡션(caption.txt): 본문은 한 줄 한 호흡(긴 문단 금지), 질문형 오프닝, 한두 문장마다 빈 줄, 이모지 불릿 — 스크롤을 멈추는 시각 리듬. 릴스용 짧은 버전 + 해시태그(본문 ~20+첫 댓글 확장) + 게시 전 체크리스트
11. 렌더·검수: 아래 디자인 시스템의 .card(1080×1080)를 그대로 복사해 채우고, 카드별로 1080×1080 이미지로 캡처한다. 환경별 경로 — ①로컬(Claude Code): 헤드리스 브라우저 렌더 스크립트 ②웹·모바일: 카드 HTML을 아티팩트로 만들어 보여주고, Canva 커넥터가 있으면 report_template(kind='canva_prompts')의 프롬프트로 Canva 디자인 생성·교정 후 Canva에서 페이지별 PNG 내보내기(완전한 웹 완결 경로). 렌더 후 전 장을 눈으로 검수 — 하단 겹침·세로 넘침·이미지 적합성(빈 컷·워터마크·무관 컷)·어색한 줄바꿈. 결함 카드만 수정해 재렌더
12. 납품: 순서 번호 PNG 전체 + caption.txt + sources.txt + 자기완결 carousel.html. 발굴 보고서와 병행 제작 시 보고서 '카드뉴스' 절에 무크롭(.cards-grid)으로 임베드 — report_template(kind='report') 규칙 17 참조"""

CAROUSEL_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>카드뉴스 디자인 시스템 v2 — 시작 템플릿</title>
<!--
  검증된 고대비 디자인 시스템. 이 파일을 복사해 카드를 채운다.
  팔레트는 :root만 바꾸면 전체 적용 (기본: 순흑+크림+크림슨/골드 — 아카이브·스토리텔링 무드.
  밝은 브랜드면 --bg를 밝게, --cream을 잉크색으로 뒤집는다).
  이미지는 {{img:경로|maxdim=760|q=72}} 토큰 (scripts/make_carousel.py가 처리).
  레이아웃 선택 기준은 references/layouts.md 참조.

  ★ 핵심 안전 규칙 ★
  - 모든 카드 콘텐츠는 <div class="col"> 안에 — 하단 안전영역 150px가 페이지번호·브랜드
    겹침을 구조적으로 막는다 (이 겹침이 실전에서 가장 잦은 결함이었다)
  - credit에 margin-top:auto 금지 — 고정 마진 사용
  - 이미지는 고정 height + object-fit:cover
-->
<style>
  :root{
    --bg:#0a0c10; --panel:#14171d; --crimson:#e03540; --gold:#e8b45a; --cream:#faf3e3;
    --sub:#8d94a2; --green:#5fd07f; --amber:#e8b45a;
  }
  *{box-sizing:border-box; margin:0; padding:0;}
  body{background:#000; font-family:'Noto Sans KR','Apple SD Gothic Neo','Malgun Gothic',sans-serif; padding:40px; color:var(--cream);}
  .card{width:1080px; height:1080px; margin:0 auto 56px; position:relative; overflow:hidden;
        background:var(--bg); box-shadow:0 10px 60px rgba(0,0,0,.7);}
  /* 콘텐츠 컬럼 — 하단 안전영역 150px (brand/pageno와 절대 안 겹침) */
  .col{position:relative; z-index:4; height:100%; display:flex; flex-direction:column; padding:70px 86px 150px;}
  /* 장식 */
  .grain{position:absolute; inset:0; pointer-events:none; opacity:.45; mix-blend-mode:overlay;
    background-image:repeating-linear-gradient(0deg, rgba(255,255,255,.03) 0 1px, transparent 1px 3px);}
  .frame{position:absolute; inset:24px; border:2px solid rgba(232,180,90,.55); pointer-events:none;}
  .corner{position:absolute; width:34px; height:34px; border:4px solid var(--gold);}
  .c-tl{top:16px; left:16px; border-right:none; border-bottom:none;}
  .c-tr{top:16px; right:16px; border-left:none; border-bottom:none;}
  .c-bl{bottom:16px; left:16px; border-right:none; border-top:none;}
  .c-br{bottom:16px; right:16px; border-left:none; border-top:none;}
  /* 타이포 */
  .kicker{display:inline-block; background:var(--crimson); color:#fff; font-weight:900;
          letter-spacing:.28em; font-size:24px; padding:13px 30px 13px 36px;}
  h1{font-size:80px; line-height:1.24; font-weight:900; word-break:keep-all; color:#fff;}
  h2{font-size:54px; line-height:1.27; font-weight:900; word-break:keep-all; color:#fff;}
  .gold{color:var(--gold);} .red{color:var(--crimson);}
  .lead{font-size:31px; line-height:1.6; word-break:keep-all; color:#e5ddc9;}
  .lead b{color:var(--gold);}
  .credit{font-size:19px; color:var(--sub); line-height:1.5;}
  .divider{height:6px; width:150px; background:linear-gradient(90deg,var(--gold),var(--crimson)); margin:24px 0;}
  .years{font-size:26px; color:var(--gold); font-weight:700; letter-spacing:.05em; margin:4px 0 12px; word-break:keep-all;}
  /* 하단 고정 표기 */
  .pageno{position:absolute; bottom:46px; right:76px; font-size:23px; color:var(--sub); letter-spacing:.12em; z-index:9;}
  .brand{position:absolute; bottom:46px; left:76px; font-size:23px; color:var(--sub); z-index:9;}
  .stamp{position:absolute; border:5px solid var(--crimson); color:var(--crimson); border-radius:10px;
         padding:10px 22px; font-weight:900; font-size:28px; letter-spacing:.1em;
         transform:rotate(-8deg); background:rgba(224,53,64,.08); z-index:6;}
  /* 사진 프레임 */
  .polaroid{background:#fbf8f1; padding:14px 14px 0; box-shadow:0 14px 34px rgba(0,0,0,.55);}
  .polaroid img{display:block; width:100%;}
  .polaroid .cap{font-size:20px; color:#3a3f49; padding:10px 4px 12px; font-weight:700; text-align:center; word-break:keep-all;}
  .tape{position:absolute; width:140px; height:38px; background:rgba(232,180,90,.75); box-shadow:0 2px 8px rgba(0,0,0,.3); z-index:3;}
  .shot{background:#fff; padding:10px; box-shadow:0 18px 44px rgba(0,0,0,.7);}
  .shot img{display:block; width:100%;}
  .shot .cap{font-size:20px; color:#3a3f49; padding:10px 4px 4px; font-weight:700; text-align:center; word-break:keep-all;}
  /* 파노라마 필름스트립 */
  .pano{border-top:16px solid #000; border-bottom:16px solid #000; background:#000; position:relative;
        box-shadow:0 14px 40px rgba(0,0,0,.6);}
  .pano:before,.pano:after{content:''; position:absolute; left:0; right:0; height:14px;
    background-image:repeating-linear-gradient(90deg, #fff 0 22px, transparent 22px 44px); opacity:.9;}
  .pano:before{top:-15px;} .pano:after{bottom:-15px;}
  .pano .row{display:flex; gap:6px;}
  .pano img{flex:1; height:300px; object-fit:cover; display:block; filter:contrast(1.15) brightness(1.05);}
  /* 시리즈 스트립 */
  .strip{display:flex; gap:10px;}
  .strip img{flex:1; height:130px; object-fit:cover; border:2px solid #3a4152;}
  /* 목록·상태 */
  .reel{background:var(--panel); border:1px solid #262b35; border-left:10px solid var(--gold); padding:16px 24px; margin:11px 0;}
  .reel .no{font-size:24px; font-weight:900; color:var(--gold); letter-spacing:.06em; font-family:Consolas,Menlo,monospace;}
  .reel .t{font-size:26px; font-weight:700; margin-top:4px; word-break:keep-all; line-height:1.4; color:#f2ecdb;}
  .reel .d{font-size:20px; color:var(--sub); margin-top:4px; word-break:keep-all;}
  .reel.locked{border-left-color:var(--crimson);}
  .badge{display:inline-block; border-radius:30px; padding:4px 16px; font-size:19px; font-weight:900; margin-left:8px; vertical-align:middle;}
  .b-lock{background:#38151a; color:#ff7a83; border:1px solid #ff7a83;}
  .b-half{background:#3a2c12; color:var(--amber); border:1px solid var(--amber);}
  .b-open{background:#153019; color:var(--green); border:1px solid var(--green);}
  .org{background:var(--panel); border:1px solid #262b35; border-left:8px solid var(--gold);
       padding:13px 22px; margin:10px 0; display:flex; justify-content:space-between; align-items:center; gap:16px;}
  .org .name{font-size:28px; font-weight:900; word-break:keep-all;}
  .org .name small{display:block; font-size:19px; color:var(--sub); font-weight:400; margin-top:2px;}
  .org .hits{font-size:26px; font-weight:900; white-space:nowrap;}
  .hit-y{color:var(--green);} .hit-w{color:var(--amber);} .hit-n{color:#ff7a83;}
  /* 3단계 분류 */
  .tier{flex:1; background:var(--panel); border:1px solid #262b35; border-top:10px solid; padding:24px;}
  .tier .icon{font-size:52px;}
  .tier .t{font-size:29px; font-weight:900; margin-top:10px; word-break:keep-all;}
  .tier .d{font-size:21px; color:var(--sub); margin-top:6px; line-height:1.5; word-break:keep-all;}
  /* 타임라인 */
  .tl{border-left:5px solid var(--gold); margin:20px 0 0 24px; padding-left:36px;}
  .tl .ev{margin:0 0 24px; position:relative;}
  .tl .ev:before{content:''; position:absolute; left:-47px; top:8px; width:18px; height:18px; border-radius:50%;
    background:var(--crimson); border:4px solid var(--bg); box-shadow:0 0 0 3px var(--gold);}
  .tl .yr{font-size:29px; font-weight:900; color:var(--gold); letter-spacing:.04em;}
  .tl .tx{font-size:27px; line-height:1.5; color:#e5ddc9; word-break:keep-all; margin-top:2px;}
  /* 인용 */
  .quote{border-left:6px solid var(--gold); padding:14px 22px; margin-top:20px;
         font-size:29px; line-height:1.55; color:#f2ecdb; font-style:italic; word-break:keep-all; background:rgba(232,180,90,.07);}
  .docquote{border-left:6px solid var(--gold); padding:16px 24px; margin-top:18px;
            font-size:30px; line-height:1.6; color:#f2ecdb; word-break:keep-all; background:rgba(232,180,90,.07);}
  .docquote small{display:block; font-size:21px; color:var(--sub); margin-top:8px; font-style:normal;}
  /* 빅넘버 */
  .bignum{font-size:190px; font-weight:900; color:var(--gold); line-height:1; letter-spacing:-.02em;}
  /* 번호 리스트 */
  .li{display:flex; gap:22px; align-items:flex-start; margin:22px 0; font-size:31px; line-height:1.5; word-break:keep-all; color:#eee6d2;}
  .li .n{flex:0 0 54px; height:54px; border-radius:50%; background:var(--crimson); color:#fff;
         font-weight:900; font-size:27px; display:flex; align-items:center; justify-content:center;}
  .li b{color:var(--gold);}
  /* 부채꼴 스택 — 제목 아래에만 배치할 것 */
  .fanwrap{position:relative; height:480px;}
  .fcard{position:absolute; width:600px; background:#f5efdf; color:#20242c; padding:22px 26px;
         box-shadow:0 18px 40px rgba(0,0,0,.65); border:1px solid #d8d0bc;}
  .fcard .no{font-family:Consolas,Menlo,monospace; font-weight:900; font-size:25px; color:#b3262f;}
  .fcard .t{font-size:25px; font-weight:900; margin-top:4px; line-height:1.35; word-break:keep-all;}
  .fcard .d{font-size:19px; color:#5a6070; margin-top:4px;}
</style>
</head>
<body>

<!-- 예시 1 · 풀블리드 커버: 실물 이미지 + 그라디언트 + 훅 -->
<div class="card">
  <img src="{{img:cover.jpg|maxdim=1000|q=76}}" alt=""
       style="position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:center 30%; filter:contrast(1.2) brightness(.95) sepia(.2);">
  <div style="position:absolute; inset:0; background:linear-gradient(180deg, rgba(0,0,0,.25), rgba(0,0,0,.92) 68%);"></div>
  <div class="grain"></div><div class="frame"></div>
  <div class="col">
    <div><span class="kicker">키커 문구</span></div>
    <div class="stamp" style="top:142px; right:82px;">도장</div>
    <div style="margin-top:auto;">
      <h1>훅 첫 줄,</h1>
      <h1 class="gold">숫자·반전이 있는 둘째 줄</h1>
      <div class="divider"></div>
      <p class="lead">부제 — <b>핵심어</b> 강조. 이미지의 정체와 연결.</p>
      <p class="credit" style="margin-top:16px;">출처: (정식 명칭, 라이선스)</p>
    </div>
  </div>
  <div class="brand">브랜드명</div><div class="pageno">1 / 10</div>
</div>

<!-- 예시 2 · 파노라마 필름스트립 -->
<div class="card">
  <div class="grain"></div><div class="frame"></div>
  <div class="col">
    <div><span class="kicker">장면 ①</span></div>
    <h2 style="margin:22px 0 8px;">제목 — <span class="gold">세 컷을 펼치다</span></h2>
    <div class="pano" style="margin-top:20px;">
      <div class="row">
        <img src="{{img:f1.jpg|maxdim=600|q=74}}"><img src="{{img:f2.jpg|maxdim=600|q=74}}"><img src="{{img:f3.jpg|maxdim=600|q=74}}">
      </div>
    </div>
    <p class="lead" style="margin-top:24px; font-size:29px;">컷1 — 컷2 — 컷3.<br>한 문장 해설로 <b>움직임</b>을 전달.</p>
    <p class="credit" style="margin-top:16px;">출처 · 링크</p>
  </div>
  <div class="brand">브랜드명</div><div class="pageno">4 / 10</div>
</div>

<!-- 예시 3 · 부채꼴 스택 (제목 아래에만!) -->
<div class="card">
  <div class="grain"></div><div class="frame"></div>
  <div class="col" style="padding-bottom:140px;">
    <div><span class="kicker">🔴 잠긴 기록</span></div>
    <h2 style="margin:20px 0 6px;">제목은 스택 위에,<br><span class="red">스택은 제목 아래에</span></h2>
    <div class="fanwrap" style="height:500px; margin-top:30px;">
      <div class="fcard" style="top:300px; left:0; transform:rotate(-6deg);"><div class="no">ID-004</div><div class="t">네 번째 기록</div><div class="d">부가 정보</div></div>
      <div class="fcard" style="top:210px; left:120px; transform:rotate(4deg); z-index:2;"><div class="no">ID-003</div><div class="t">세 번째 기록</div><div class="d">부가 정보</div></div>
      <div class="fcard" style="top:115px; left:230px; transform:rotate(-3deg); z-index:3;"><div class="no">ID-002 <span class="badge b-lock">미공개</span></div><div class="t">두 번째 기록</div><div class="d">부가 정보</div></div>
      <div class="fcard" style="top:20px; left:330px; transform:rotate(5deg); z-index:4;"><div class="no">ID-001 <span class="badge b-lock">미공개</span></div><div class="t">맨 위 카드는 정보 전부 보이게</div><div class="d">아래 카드는 일부만 보여도 OK</div></div>
    </div>
    <p class="lead" style="margin-top:16px; font-size:27px;">마무리 한 줄.</p>
  </div>
  <div class="brand">브랜드명</div><div class="pageno">7 / 10</div>
</div>

<!-- 예시 4 · 인물 카드 -->
<div class="card">
  <div class="grain"></div><div class="frame"></div>
  <div class="col">
    <div><span class="kicker">첫 번째 이름</span></div>
    <div style="display:flex; gap:40px; margin-top:28px; align-items:flex-start;">
      <div style="position:relative; flex:0 0 380px;">
        <div class="tape" style="top:-16px; left:32%; transform:rotate(-4deg);"></div>
        <div class="polaroid"><img src="{{img:person.jpg|maxdim=760|q=75}}" style="height:520px; object-fit:cover; object-position:center 15%;"><div class="cap">사진 캡션</div></div>
      </div>
      <div style="flex:1; padding-top:6px;">
        <h2><span class="gold">이름</span></h2>
        <div class="years">1900 – 1950 · 직함</div>
        <p class="lead" style="font-size:29px;">업적 3~4줄.<br><b>핵심</b>만 강조.</p>
        <div class="quote">"실증된 어록만.<br>전승이면 '전해지는 말' 표기."</div>
      </div>
    </div>
    <p class="credit" style="margin-top:20px;">출처: (라이선스)</p>
  </div>
  <div class="brand">브랜드명</div><div class="pageno">2 / 10</div>
</div>

<!-- 예시 5 · 지도 여정 (SVG 약식 지도 + 마커 + 목록 병치) -->
<div class="card">
  <div class="grain"></div><div class="frame"></div>
  <div class="col" style="padding-bottom:140px;">
    <div><span class="kicker">지도 위의 여정</span></div>
    <h2 style="margin:20px 0 4px;">지점들을 <span class="gold">한 장</span>에</h2>
    <div style="display:flex; gap:30px; align-items:center; margin-top:6px;">
      <svg viewBox="0 0 380 560" style="flex:0 0 380px; height:600px;">
        <path d="M150 30 L235 46 L300 70 L306 108 L282 196 L322 268 L296 322 L282 392 L240 444 L188 462 L142 478 L120 400 L108 288 L100 176 L126 92 Z"
              fill="#14171d" stroke="#e8b45a" stroke-width="3"/>
        <line x1="70" y1="218" x2="330" y2="218" stroke="#e03540" stroke-width="3" stroke-dasharray="14 10"/>
        <circle cx="152" cy="208" r="13" fill="#5fd07f"/>
        <text x="30" y="168" fill="#5fd07f" font-size="24" font-weight="bold">지점A</text>
        <circle cx="170" cy="248" r="13" fill="#e03540"/>
        <text x="200" y="258" fill="#ff7a83" font-size="24" font-weight="bold">지점B</text>
        <path d="M152 208 Q150 230 170 248" stroke="#faf3e3" stroke-width="2" stroke-dasharray="4 6" fill="none"/>
      </svg>
      <div style="flex:1;">
        <div class="reel" style="margin-top:0;"><div class="no">지점A</div><div class="t">설명</div><div class="d">🟢 상태</div></div>
        <div class="reel"><div class="no">지점B</div><div class="t">설명</div><div class="d">🔴 상태</div></div>
        <p class="credit" style="margin-top:14px;">라벨은 마커와 안 겹치게 — 렌더 후 확인</p>
      </div>
    </div>
  </div>
  <div class="brand">브랜드명</div><div class="pageno">3 / 10</div>
</div>

</body>
</html>"""

CANVA_PROMPTS = """# Canva 생성 프롬프트 모음 — KOREA ARCHIVE 홍보물

발굴 조사 결과를 Canva AI(generate-design)로 홍보물화할 때 쓰는 검증된 프롬프트 템플릿.
2026-08-13 그로스터 연대 포스터 실전에서 검증·교정된 버전이다.

## 공통 원칙 (모든 프롬프트에 적용 — 어기면 실패한다)

1. **실물 자산 필수**: 반드시 asset_ids로 실물 기록 사진을 전달한다(공개 URL → upload-asset-from-url).
   자산 없이 역사 주제를 생성시키면 **가짜 병사·가짜 유물 이미지**가 나온다 (실측: 후보 4개 중 3개가 가짜 이미지 사용).
2. **AI 인물·역사장면 생성 금지 문구**를 프롬프트에 명시: "Do NOT generate any people, soldiers,
   or war imagery — only use the provided photos plus typographic and abstract archival motifs."
3. **한국어 텍스트는 반드시 환각 검수**: 생성 결과의 한국어는 깨지거나("사진 한 장 활서")
   광고 관용구가 끼어든다("20% 할인 제공"). 생성 후 **read-design → edit-design(replace_text)으로
   전 문구를 검증 카피로 교체**하는 것까지가 제작 절차다.
4. **후보 선별 기준**: 후보 중 제공한 실물 자산을 실제로 쓴 것만 채택. 하나도 없으면 재생성.
5. **카피는 조사에서**: 훅·수치·식별자는 보고서에서 검증된 것만 슬롯에 넣는다. 출처 크레디트 슬롯은 생략 불가.
6. **필기체 라틴 폰트 주의**: 영문이 스크립트체로 나오면 해당 요소를 delete_element 후 add_text로 재삽입(폰트 변경 연산 없음).

## 공통 스타일 블록 (프롬프트에 붙여넣기)


Mood: prestigious history journal — dignified, quiet, powerful. NOT playful, NOT colorful advertising.
Color palette: aged cream paper (#f5f1e8), deep crimson (#8a3033), antique gold (#a8853c), near-black ink (#211d18).
Subtle paper texture, thin double-rule borders like a newspaper masthead.
Treat the provided archival photographs with respect: duotone/sepia, generous margins, thin gold frame.
Do NOT generate any people, soldiers, or war imagery — only the provided photos + typographic archival motifs
(reference-code typography, subtle stamp marks, thin rules).
Typography: elegant Korean serif (명조) headline, clean sans labels. All Korean text professionally typeset.
Full-bleed, no watermark, no mockup.


## 1. 발굴 보고 포스터 (design_type: poster) — 검증본


Create a premium archival-journal style vertical poster for a historical records discovery report.
[공통 스타일 블록]
Top small kicker: 발굴 보고 · {{시기·주제}}
Large headline (2 lines): {{훅 헤드라인 — 예: 임진강에 남은 / 이름들}}
Subheadline: {{조사 훅 문장 — 예: 「할아버지가 참전한 부대를 찾아줘」— 한국어 한 문장이 연 두 나라 기록 65건}}
Credential lines with thin gold rules:
· {{검증 수치 1 — 예: 무공훈장 추천서 49건, 이름·군번 그대로}}
· {{검증 수치 2 — 예: 키워드 0건의 부대 일지, 인접 채굴로 발견}}
· {{검증 수치 3 — 예: 포로수용소에서 새긴 석조각, 한국에 실물}}
Bottom CTA: KOREA ARCHIVE 통합검색 — 발굴 보고서 공개
Tiny credit: 사진: {{기관 정식명}} · 실물 기록


## 2. 전시·추모행사 안내 포스터 (design_type: poster)


Create an announcement poster for a memorial/exhibition event, archival-journal style.
[공통 스타일 블록]
Kicker: {{행사 구분 — 예: 추모 · 전시 안내}}
Headline: {{행사명}}
Date/venue block in clean sans with gold rules: {{일시}} · {{장소}}
One-line story hook: {{이 행사의 역사적 근거 한 문장 — 검증된 사실만}}
Bottom: 주최 {{기관}} · 문의 {{연락처}} / Tiny credit: 사진: {{출처}}


## 3. 카드뉴스 시리즈 예고 (design_type: instagram_post)


Create a series-teaser social post, archival-journal style, 4:5 portrait.
[공통 스타일 블록]
Kicker: 연재 예고
Headline: {{시리즈명}} — 전 {{N}}부작
Use the provided cover photos as a small filmstrip row (do not crop faces).
Schedule lines: {{1부 제목 · 공개일}} / {{2부 제목 · 공개일}} / ...
CTA: 팔로우하고 첫 공개를 받아보세요
Tiny credit: 사진: {{출처 목록}}


## 4. 인물 조명 포스터 (design_type: poster)


Create a single-figure tribute poster, archival-journal style.
[공통 스타일 블록 + 인물 사진 존엄 조항: use the provided portrait respectfully, no colorization, no AI retouching]
Kicker: {{기록이 증언하는 사람}}
Headline: {{인물명}}
Fact lines (verified only): {{직위·부대}} / {{검증된 행적 1}} / {{검증된 행적 2 — 식별자 포함}}
Quote block only if verified from documents: {{문서 판독 인용 or 생략}}
Bottom: 기록 {{참조코드}} · KOREA ARCHIVE 통합검색 / Tiny credit: {{출처}}
※ 포로·사망자·희생자는 게재윤리 4단계 적용 — 존엄 우선, 확신 없으면 만들지 않는다.


## 5. 기록영상 공개 알림 (design_type: instagram_post)


Create a film-release announcement post, archival cinema mood (dark charcoal #171412 background variant).
[공통 스타일 블록 — 배경만 다크, 크림 텍스트]
Kicker: 기록영상
Headline: {{영상 제목}} ({{연대}})
Use provided real film frames as a horizontal filmstrip with timecode chips.
One line: {{표제가 가린 내용 훅 — 예: 카탈로그 한 줄 뒤에 숨어 있던 장면들}}
CTA: ▶ 원본 보기 — {{기관}} 카탈로그
Tiny credit: {{RG·식별자·출처}}


## 6. A4 리플릿 (design_type: flyer_a4 / import 시 a4)


Create a single-page A4 information leaflet, archival-journal style, print-ready.
[공통 스타일 블록]
Masthead: KOREA ARCHIVE 통합검색 — 기록 발굴 보고
Headline + standfirst: {{보고서 제목·요지 2문장}}
Three-column facts: {{핵심 기록 3건 — 식별자·한 줄 설명}}
Photo band: provided real photos with captions
Footer: 전체 보고서 QR/URL {{링크}} · 출처 총람 요약 · {{확인일}}


## 생성 후 체크리스트 (생략 금지)

1. 후보 전부 썸네일 검수 — 실물 자산 사용 여부·가짜 이미지 혼입 확인
2. 채택본 create-design-from-candidate → read-design(open_transaction)
3. **모든 한국어 문구를 검증 카피로 replace_text** (환각 문구는 반드시 있다)
4. 겹침·줄바꿈·폰트(필기체 라틴) 검수 → 교정 → commit
5. 출처 크레디트 존재 확인 — 없으면 add_text로 추가

# 7. 커머셜 임팩트 포스터 (design_type: poster) — 화려·그래픽·패셔너블

Create a BOLD, commercial, fashion-forward vertical poster — streetwear-drop / fashion-magazine energy, maximalist, NOT quiet.
Color blocking: deep crimson #8a3033 + warm gold #e8b45a + cream #f5f1e8 + black. Oversized Korean display typography,
the provided REAL photo as duotone hero inside a bold geometric frame, graphic accents (waves, starbursts, sticker badges,
thick rules, halftone). CRITICAL: only provided real photos — no AI people or history scenes.
Top badge: {{발굴 완료}} / Huge headline: {{찾았다, N건}} / Sub: {{훅 한 줄}} / Stat badges 3: {{검증 수치}} /
CTA bar: 발굴 보고서 공개 — KOREA ARCHIVE 통합검색 / Tiny credit: {{사진 출처·식별자}}
검증 실측: 후보 4개 중 3개가 가짜 이미지 — 실물 사용 후보만 채택하고 환각 문구는 전량 교정할 것."""

FULL_PACKAGE = """풀패키지 오케스트레이션 — 발굴에서 전파물까지 한 번에 (매직 키워드: "풀패키지" · "전부 다 만들어줘")
입력은 주제 하나면 충분하다. 아래 순서를 전부 수행해 모든 산출물을 함께 납품한다.

1. 발굴 조사: cross_search + 전문 도구(tna_search/nara_search/koreanwar_search/gallica_search…) — 표기 변형 병렬,
   시리즈 특정+tna_adjacent_mine 인접 채굴(±5~15), 국내 협약기관 교차검증, 카탈로그 API 원문으로 훈격·날짜·건수 검증
   (정정 발생 시 이력 기록), judge_rights 권리 초판.
2. 실물 이미지 수집: 기관 공개 원본 전량(비식별판 우선) + digitised 기록의 카탈로그 무료 미리보기.
   수집 즉시 출처 대장(sources.txt) 기록. AI 생성 인물·역사 장면 절대 금지.
3. HTML 보고서: report_template(kind='report') 18규칙 전부 — 히어로 실물·인라인 도판·콘택트시트·원문 미리보기·
   검증 기록·전수 목록·재현 쿼리·더 보기·카드뉴스 갤러리. 매거진 완성판은 kind=magazine 확장팩을 덧입힌다. 산출 방식 — 로컬: .html 파일 저장 / 웹·모바일: HTML 아티팩트로 게시(파일 저장 불가), 이미지는 기관 공개 URL 참조. 수치는 모든 산출물에서 동일해야 한다.
4. 캐러셀 8장: report_template(kind='carousel') 12규칙 — 커버는 보고서 히어로와 같은 실물, 검증 노트·따라하기 포함.
   렌더는 환경별: 로컬=헤드리스 렌더 / 웹·모바일=Canva 커넥터 생성→페이지별 PNG 내보내기. 전 장 육안 검수 생략 금지.
   caption.txt + sources.txt 동봉.
5. Canva 산출물(커넥터 연결 시): 캐러셀 편집본 + report_template(kind='canva_prompts') 1번 템플릿으로 포스터 1종 —
   생성 직후 전 한국어 문구를 검증 카피로 교정(replace_text) 후 저장.
6. 납품: 보고서 HTML + 카드 8장 + 포스터 시리즈 + caption/sources + Canva 링크. 로컬: 전체를 [주제영문]_fullpackage_[날짜].zip으로 묶어 함께 납품 — 구조 report/·cards/·posters/·canva/·manifest.txt(산출물 목록+검증 요약). 웹·모바일: zip 생성 불가 — 개별 아티팩트로 제시하고 manifest 목록을 함께 출력. SNS 게시·공개 푸시는 사용자 확인 후.

품질 게이트: 수치 정합 · 전 이미지 캡션+출처(기관 정식명·국가·식별자·링크) · 실확인 링크만(확인일 명기) ·
게재윤리 4단계(포로·사망자 존엄) · 협약기관 출처 표기 필수."""

MAGAZINE_PACK = """매거진 확장팩 — kind='report' 보고서에 덧입히는 표지·목차·뒷표지·시그니처·테마 (일류 저널급)
사용법: 보고서 골격(kind='report') 완성 후 아래를 추가한다. 표지는 발굴 포스터를 겸한다(별도 포스터 제작 시 같은 구성).

[구조] <body> 직후: <section class='cover'> → <section class='contents'> → 기존 .wrap 본문 → </div> 뒤 <section class='backcover'>
[표지] 실물 히어로 사진 풀블리드 배경(.bg data URI)+그라디언트(.shade) 위에: KA인장+매스트헤드(제N호·날짜) /
 킥커 / 대형 제호 h1 / 훅 문장 .sub / 검증 팩트 3줄 .facts(골드 좌보더) / .foot "표지 겸 발굴 포스터 — 실물 사진과 검증 카피로만 구성"+사진 출처
[목차] .contents: CONTENTS 라벨 / 차례 ol — 각 항목: 로마숫자(.no2 이탤릭 세리프)+절 제목 앵커+우측 한 줄 설명(.d)
[뒷표지] .backcover(다크): KA인장+워드마크 / 서비스 소개 2줄 / 이 호의 기록 출처(국기+정식명) / 함께 나온 산출물 / 커넥터 URL+매직 키워드 '풀패키지' / 확인일
[스프레드 폴리시] h2 고스트 로마숫자(.no 64px opacity .13)+골드 틱(::before 26×3px) / figcaption b는 스몰캡스 /
 절 사이 풀블리드 포토 브레이크 .photobreak(실물 배경+어두운 오버레이+이탤릭 인용+출처 한 줄)
[시그니처 — KA 인장·검증 낙관] 인장 SVG(72 viewBox): 크림슨 라운드 사각 + 크림 이중 테두리 + K·A 스트로크 모노그램 + 상하좌우 조준 틱.
 검증 낙관 .ka-verified: 크림슨 2.5px 보더 라운드 박스 -1.2도 회전, 인장+"검증 낙관 — KOREA ARCHIVE"+
 "실물 이미지·훈격·건수·링크는 기관 원본 수집과 API 원문 대조를 마쳤습니다. 정정 이력은 Ⅴ절 공개 · [확인일]" — Ⅵ 권리절 끝에 배치. 검증 없이 낙관 금지.
[테마 5종 — data-theme 속성, CSS 변수 오버라이드] 기본 Injang(시그니처: 크림 종이+크림슨+골드 세리프) /
 minimal(화이트·#0071e3·산세리프, 애플풍) / dark(#0b0d12·#4c8dff, 삼성풍) / pop(#fee500 포인트, 카카오풍) / blue(#0064e0·산세리프, 메타풍).
 우하단 고정 .themebar(반투명 필, 5색 원 버튼, onclick으로 documentElement data-theme 토글, @media print 숨김)

[핵심 CSS — 그대로 복사]
.cover{position:relative;min-height:100vh;display:flex;flex-direction:column;background:#171412;color:#f4ecdd;overflow:hidden}
.cover .bg{position:absolute;inset:0;background-size:cover;background-position:70% center}
.cover .shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,8,6,.35),rgba(10,8,6,.94) 70%)}
.cover .in{position:relative;z-index:2;display:flex;flex-direction:column;flex:1;max-width:880px;width:100%;margin:0 auto;padding:34px 26px 48px}
.cover .mast{display:flex;justify-content:space-between;font-size:12px;letter-spacing:.24em;text-transform:uppercase;color:#cbbfa8;border-bottom:3px double rgba(232,224,205,.6);padding-bottom:12px}
.cover .kick{margin-top:auto;font-size:13px;letter-spacing:.3em;color:#e8b45a;font-weight:700}
.cover h1{font-size:clamp(38px,7.5vw,68px);line-height:1.18;margin:10px 0 16px;color:#fff}
.cover .facts li{margin:6px 0;padding-left:16px;border-left:2px solid #a8853c;list-style:none}
.contents li{display:flex;gap:16px;align-items:baseline;padding:13px 2px;border-bottom:1px solid var(--line)}
.contents .no2{font-family:Georgia,serif;font-style:italic;color:var(--accent);flex:0 0 34px;font-size:19px}
.contents .d{color:var(--sub);font-size:13px;margin-left:auto;text-align:right;max-width:46%}
.backcover{background:#171412;color:#cbbfa8;margin-top:70px;padding:70px 26px 60px}
.photobreak{position:relative;margin:70px calc(50% - 50vw);padding:110px 26px;background-size:cover;color:#f4ecdd;text-align:center}
.photobreak::before{content:'';position:absolute;inset:0;background:rgba(12,9,7,.62)}
.photobreak blockquote{position:relative;z-index:1;max-width:640px;margin:0 auto;font-size:clamp(22px,3.4vw,30px);font-style:italic}
.ka-verified{display:flex;gap:16px;align-items:center;margin-top:26px;padding:16px 20px;border:2.5px solid var(--accent);border-radius:8px;max-width:560px;transform:rotate(-1.2deg)}
h2 .no{font-size:64px;position:absolute;top:-14px;left:-6px;opacity:.13}
@media print{.cover{page-break-after:always}.contents{page-break-after:always}.themebar{display:none}}

[KA 인장 SVG — 그대로 복사]
<svg class='ka-seal' viewBox='0 0 72 72' width='30' height='30'><path d='M36 1v6M36 65v6M1 36h6M65 36h6' stroke='#8a3033' stroke-width='2.6'/><rect x='9' y='9' width='54' height='54' rx='7' fill='#8a3033'/><rect x='13.5' y='13.5' width='45' height='45' rx='4.5' fill='none' stroke='#f5f1e8' stroke-width='1.6' opacity='.75'/><path d='M22 22v28M22 36l11-14M22 36l11 14' stroke='#f5f1e8' stroke-width='4.6' fill='none' stroke-linecap='square'/><path d='M38 50l7-28 7 28M41 41h8' stroke='#f5f1e8' stroke-width='4.6' fill='none' stroke-linecap='square'/></svg>"""


@mcp.tool()
def report_template(kind: str = "report") -> str:
    """발굴 조사를 마친 뒤 결과를 HTML 보고서로 만들 때 호출 (조사 마무리 단계의 기본 산출물).
    잡지·저널급 보고서 골격(HTML/CSS)과 17개 작성 규칙을 반환한다 — 편집 지면(masthead·
    standfirst·드롭캡·풀인용·기록 카드), 실물 이미지 base64 임베드+이미지별 출처 크레디트 필수,
    영상은 타임코드 필름스트립+원본 시청 CTA, 기관별 출처 chip(국기+정식명)과 인용 기관 총람.
    {{플레이스홀더}}를 검증된 발굴 결과로 채워 [주제영문]_records_[연도범위].html로 저장할 것.
    kind="carousel"이면 카드뉴스 캐러셀 디자인 시스템을 반환 — 검증된 1080×1080 카드 CSS 컴포넌트
    + 제작 12규칙(서사 아크·실물 이미지·출처 캡션·겹침 방지·육안 검수). 어디서든 같은 품질 재현용.
    kind="canva_prompts"면 Canva AI(generate-design) 홍보물 프롬프트 6종(포스터·행사·시리즈 예고·인물·
    영상 알림·A4 리플릿)과 실전 검증된 환각 교정 절차를 반환한다.
    사용자가 "풀패키지"라고 하면 kind="full_package"를 먼저 호출 — 조사→보고서→캐러셀→포스터
    전 산출물 제작 순서를 받아 그대로 수행한다."""
    if kind == "magazine":
        return MAGAZINE_PACK
    if kind == "full_package":
        return FULL_PACKAGE
    if kind == "canva_prompts":
        return CANVA_PROMPTS
    if kind == "carousel":
        return CAROUSEL_RULES + "\n\n===== CARD DESIGN SYSTEM (1080×1080 — .card를 그대로 복사해 채울 것) =====\n" + CAROUSEL_TEMPLATE
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
    q = _ko_en(q) or q
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
    q = _ko_en(q) or q
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
    q = _ko_en(q) or q
    key = os.environ.get("EUROPEANA_API_KEY") or "api2demo"
    d = http_json("https://api.europeana.eu/record/v2/search.json?" +
                  urllib.parse.urlencode({"wskey": key, "query": q, "rows": n, "profile": "standard"}))
    return [{"title": (it.get("title") or ["?"])[0], "date": (it.get("year") or [""])[0],
             "id": it.get("id", ""), "url": it.get("guid", "")} for it in (d.get("items") or [])]

def _c_nara(q, n):
    key = os.environ.get("NARA_API_KEY")
    if not key:
        return []
    q = _ko_en(q) or q
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
    record. robots가 막은 opengov·서울기록원은 미포함 — 전용 도구/브라우저 도구로.
    사용자가 "풀패키지"(보고서·카드뉴스·포스터 전부)를 원하면 report_template(kind="full_package")를 먼저 호출해 제작 순서를 따른다."""
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
