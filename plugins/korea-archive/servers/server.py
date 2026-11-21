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
    # ── v1.17 증보: 6·25 후기 단계 전투·지명·개항기~해방 인물·사건 (route.js 패리티) ──
    ("지평리|砥平里", "Chipyong-ni", "bataillon français Corée Chipyong-ni"),
    ("가평\\s?전투|加平", "Kapyong", None),
    ("노근리|老斤里", "No Gun Ri", None),
    ("철의\\s?삼각지?대?", "Iron Triangle Korea", None),
    ("폭찹\\s?힐|폭찹\\s?고지", "Pork Chop Hill", None),
    ("피의\\s?능선", "Bloody Ridge Korea", None),
    ("저격\\s?능선|狙擊稜線|狙击岭", "Sniper Ridge Korea", None),
    ("삼각\\s?고지|상감령|上甘嶺|上甘岭", "Triangle Hill Korea", None),
    ("금성\\s?전투|金城\\s?戰鬪|金城战役", "Kumsong offensive 1953", None),
    ("청천강|淸川江|清川江", "Chongchon River", None),
    ("부산\\s?교두보|워커\\s?라인", "Pusan Perimeter", None),
    ("유엔군|국제연합군|국련군|联合国军", "United Nations forces Korea", "forces ONU Corée"),
    ("중공군|인민지원군|志願軍|志愿军", "Chinese forces Korea", None),
    ("리지웨이|リッジウェイ|李奇微", "Ridgway", None),
    ("밴\\s?플리트|밴플리트", "Van Fleet", None),
    ("원산|元山|Вонсан", "Wonsan", None),
    ("대구|大邱|Тэгу", "Taegu", None),
    ("대전\\s?전투|大田", "Taejon", None),
    ("개성|開城|开城|Кэсон", "Kaesong", None),
    ("철원|鐵原|铁原", "Chorwon", None),
    ("금강산|金剛山|金刚山", "Kumgang Diamond Mountains", "monts Kumgang"),
    ("독도|獨島|独岛|다케시마|竹島", "Dokdo Takeshima Liancourt Rocks", None),
    ("명성황후|명성왕후|민비|閔妃", "Queen Min Korea", "reine Min Corée"),
    ("고종\\s?황제|고종|高宗", "Kojong", None),
    ("안중근|安重根", "An Jung-geun Ito Hirobumi", None),
    ("이토\\s?히로부미|伊藤博文", "Ito Hirobumi Korea", None),
    ("김구|金九", "Kim Koo", None),
    ("안창호|安昌浩", "Ahn Chang-ho", None),
    ("3[·.]1\\s?운동|삼일\\s?운동|三一運動|만세\\s?운동", "March First Movement Korea 1919", "mouvement du 1er mars Corée"),
    ("위안부|慰安婦|慰安妇", "comfort women", "femmes de réconfort"),
    ("강제\\s?동원|강제\\s?징용|징용|徵用|征用", "Korean forced labor conscription", None),
    ("광복군|光復軍|光复军", "Korean Liberation Army", None),
    ("임시\\s?정부|臨時政府|临时政府", "Korean Provisional Government", None),
    ("동학|東學|东学|갑오\\s?농민", "Tonghak rebellion", "Tonghak"),
    ("의병|義兵|义兵", "Righteous Army Korea insurgents", "insurgés Corée"),
    ("을사\\s?조약|을사\\s?늑약|乙巳條約", "Japan Korea protectorate treaty 1905", None),
    ("아관\\s?파천|俄館播遷", "Kojong Russian legation 1896", None),
    ("헤이그\\s?특사|해아\\s?밀사", "Hague secret emissaries Korea 1907", "La Haye Corée 1907"),
    ("제주\\s?4[·.]3|4[·.]3\\s?사건", "Cheju uprising 1948", None),
    ("여순\\s?사건|여수.순천\\s?사건", "Yosu rebellion 1948", None),
    ("신탁\\s?통치", "Korea trusteeship", "tutelle Corée"),
    ("미군정|미\\s?군정", "USAMGIK military government Korea", None),
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
def tna_search(query: str, max_results: int = 20, year_from: int | None = None,
               year_to: int | None = None, page: int = 1) -> str:
    """영국 국립기록관(TNA) Discovery에서 한국 관련 기록 검색. 한국어·일본어·중국어·러시아어 등
    다국어 질의를 영문 색인어로 자동 변환(임진강→Imjin River, 長津湖→Chosin Reservoir,
    Корейская война→Korean War …). 참조코드('FO 371/84053')는 자동으로 정확구 처리.
    year_from/year_to=연대 범위(실측: Korea 13,533→1950~51 한정 2,553건), page=결과 페이지.
    예: '임진강 전투', 'Korea armistice', 'FO 371 FK1015'"""
    en = _ko_en(query)
    eff = en or query
    q = f'"{eff}"' if re.match(r"^[A-Z]+ \d+/\d+$", eff.strip()) else eff
    recs = []
    for batch, total in T._search(q, page_size=min(max_results, 100), max_pages=1, sleep=0,
                                  start_page=page,
                                  date_from=f"{year_from}-01-01" if year_from else None,
                                  date_to=f"{year_to}-12-31" if year_to else None):
        recs += [T._extract(r, "mcp", eff) for r in batch]
    tag = f" → 영문 자동 변환 '{eff}'" if en else ""
    yt = f" [연대 {year_from or ''}~{year_to or ''}]" if (year_from or year_to) else ""
    pt = f" (p.{page})" if page > 1 else ""
    hint = ("\n※ 연대 필터는 연대 미상(Date unknown) 기록을 제외합니다 — 무필터로 재시도해 비교하십시오."
            if (year_from or year_to) and not recs else "")
    return f"TNA 검색 '{query}'{tag}{yt}{pt} — 총 {total}건 중 {len(recs[:max_results])}건:\n" + _fmt(recs, max_results) + hint

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
                moving_images_only: bool = False, max_results: int = 20, page: int = 1,
                naid: int | None = None, radius: int = 3) -> str:
    """미국 NARA 카탈로그 검색 (환경변수 NARA_API_KEY 필요 — Catalog_API@nara.gov 발급).
    다국어 질의(한국어·日本語·中文·Русский 등)는 영문 색인어로 자동 변환(장진호/長津湖→Chosin Reservoir …).
    record_group으로 RG 교차 정밀검색(예: 242), moving_images_only로 영상 한정."""
    key = os.environ.get("NARA_API_KEY")
    if not key: return "NARA_API_KEY 미설정 — Catalog_API@nara.gov 로 무료 발급(이름+이메일)."
    if naid:  # NAID ± 인접 채굴 — v2는 단수 naId만 수용(naIds=400 실측) → 순차 조회. 간격: 사진 ±3·색인 ±1
        import time as _t
        ids = [i for i in range(naid - radius, naid + radius + 1) if i > 0]
        lines = []
        for i in ids:
            try:
                d2 = http_json(f"https://catalog.archives.gov/api/v2/records/search?naId={i}&limit=1",
                               headers={"x-api-key": key})
                hits2 = (((d2.get("body") or {}).get("hits") or {}).get("hits") or [])
                rec = ((hits2[0].get("_source") or {}).get("record") or {}) if hits2 else {}
                if rec.get("naId") and int(rec["naId"]) == i:
                    lines.append(f"{'★' if i == naid else ' '} [NAID {i}] {rec.get('title','')[:95]} | "
                                 f"{rec.get('localIdentifier','')} | https://catalog.archives.gov/id/{i}")
                else:
                    lines.append(f"  [NAID {i}] (없음)")
            except Exception as e:
                lines.append(f"  [NAID {i}] 오류({e})")
            _t.sleep(0.15)
        return (f"NARA NAID 인접 채굴 {naid}±{radius} (★=중심, 한국 관련 여부는 제목으로 판별):\n"
                + "\n".join(lines)
                + "\n※ 간격 지식: 사진 계열 ±3·색인 ±1 — 하나 찾으면 양옆을 훑는다(query_bank identifiers).")
    _en = _ko_en(query)
    query = _en or query
    params = {"q": query, "limit": min(max_results, 100), "page": page}
    if record_group: params["recordGroupNumber"] = record_group
    if moving_images_only: params["typeOfMaterials"] = "Moving Images"
    data = http_json("https://catalog.archives.gov/api/v2/records/search?" + qs(params),
                     headers={"x-api-key": key})
    hits = ((data.get("body") or {}).get("hits") or {})
    rows = []
    for h in (hits.get("hits") or [])[:max_results]:
        rec = (h.get("_source") or {}).get("record") or {}
        po = _nara_chain(rec)
        rows.append(f"- [NAID {rec.get('naId')}] {rec.get('title','')[:100]} "
                    f"| {rec.get('localIdentifier','')} | https://catalog.archives.gov/id/{rec.get('naId')}"
                    + (f"\n  계보: {po}" if po else ""))
    total = hits.get("total", {}); total = total.get("value") if isinstance(total, dict) else total
    rline = ""
    if record_group:
        rc, rb = auto_rights({"rg_series": f"RG {record_group}", "archive": "NARA"})
        rline = (f"\n권리 초판정(RG {record_group}): {rc} — {rb}"
                 f"\n※ 건별 실확인: judge_rights(naid=<NAID>) — 카탈로그 Use Restriction 실조회로 A/C 확정")
    return f"NARA '{query}'" + (f" (RG {record_group})" if record_group else "") + f" — 총 {total}건:\n" + ("\n".join(rows) or "(0건)") + rline

@mcp.tool()
def ia_search(query: str = "", identifier: str = "", max_results: int = 15,
              year_from: int | None = None, year_to: int | None = None, page: int = 1,
              radius: int = 0) -> str:
    """archive.org 고급 검색. 예: 'identifier:111-adc*', 'collection:universal_newsreels AND korea',
    'mediatype:movies AND (keijo OR chosen)'. 다국어 질의(한국어·日本語·中文 등)는 영문 색인어로
    자동 변환. identifier를 주면 해당 아이템의 메타데이터·원본 파일 목록(다운로드 전 크기 파악)을
    대신 반환한다."""
    if identifier and radius > 0:  # 일련번호 인접 채굴 — identifier 말미 숫자 ±N 존재 확인(TNA식)
        import time as _t
        m = re.match(r"^(.*?)(\d+)$", identifier)
        if not m:
            return f"'{identifier}' — 말미가 숫자가 아니라 인접 채굴 불가. radius=0으로 단건 메타 조회."
        stem, nums = m.group(1), m.group(2)
        base_n, pad = int(nums), len(nums)
        lines = []
        for i in range(base_n - min(radius, 8), base_n + min(radius, 8) + 1):
            if i < 0:
                continue
            id2 = stem + str(i).zfill(pad)
            try:
                md2 = (http_json(f"https://archive.org/metadata/{_up.quote(id2)}") or {}).get("metadata")
                lines.append(f"{'★' if i == base_n else ' '} {id2} | {str(md2.get('title',''))[:85]} "
                             f"({md2.get('date','')}) https://archive.org/details/{id2}" if md2 else f"  {id2} (없음)")
            except Exception:
                lines.append(f"  {id2} (없음)")
            _t.sleep(0.2)
        return (f"archive.org 인접 채굴 {stem}[{base_n}±{min(radius, 8)}] (★=중심):\n" + "\n".join(lines)
                + "\n※ 같은 컬렉션의 절반이 다른 표기로 기술돼 검색에 안 걸리는 사례 — 번호 옆 훑기로 복구(열한 겹의 벽 §8).")
    if identifier:
        data = http_json(f"https://archive.org/metadata/{identifier}")
        md = data.get("metadata") or {}
        files = [f for f in (data.get("files") or []) if f.get("source") == "original"][:10]
        return (f"제목: {md.get('title')}\n설명: {str(md.get('description'))[:300]}\n"
                f"연대: {md.get('date')} | 라이선스: {md.get('licenseurl') or md.get('rights') or '표기 없음'}\n"
                "원본 파일:\n" + "\n".join(f"- {f['name']} ({int(f.get('size',0))/1e6:.1f}MB)" for f in files))
    if not query:
        return "query 또는 identifier 중 하나는 필수."
    disp = query
    query = _ko_en(query) or query
    if year_from or year_to:  # date:[A TO B] + page 실측 검증 (2026-11-18)
        query = f"({query}) AND date:[{year_from or 1800}-01-01 TO {year_to or 2030}-12-31]"
    import urllib.parse
    data = http_json("https://archive.org/advancedsearch.php?q=" + urllib.parse.quote(query) +
                     f"&fl[]=identifier&fl[]=title&fl[]=date&fl[]=licenseurl&rows={max_results}&page={page}&output=json")
    docs = (data.get("response") or {}).get("docs") or []
    nf = (data.get("response") or {}).get("numFound")
    yt = f" [연대 {year_from or ''}~{year_to or ''}]" if (year_from or year_to) else ""
    pt = f" (p.{page})" if page > 1 else ""

    def _lshort(lu):
        m = re.search(r"(publicdomain/(?:mark|zero)|licenses/[a-z-]+)", str(lu or ""))
        return m.group(1).replace("licenses/", "CC ") if m else ""
    if not docs:
        return f"archive.org '{disp}'{yt}{pt} — 0건"
    body = "\n".join(
        f"- {d.get('identifier')} | {str(d.get('title'))[:90]}"
        + (f" | 권리:{_lshort(d.get('licenseurl'))}" if _lshort(d.get('licenseurl')) else "")
        + f" | https://archive.org/details/{d.get('identifier')}" for d in docs)
    return (f"archive.org '{disp}'{yt}{pt} — 총 {nf}건:\n" + body
            + "\n※ 권리 미표기 건은 judge_rights 초판정 — 발굴 우선, 권리는 표시.")

JB_STRAT = {
    'recipes': """발굴 완주 레시피 — 주제 유형별 발굴→판독→권리 순서 (전 단계 실측 검증, 2026-11-21)
공통 원칙: ①cross_search로 폭 확보(variants=당대 표기) ②신호가 나온 소스의 전용 도구/판독 모드로 심층 ③권리는 표시(judge_rights·naid·라이선스) ④0건=부재가 아니다(표기 변형·인접 채굴·관리 행정으로 전환).

① 인물(독립운동가): gonghun(이름→mngNo→공훈록·수형기록. 훈격·이명 확보) + i815 '사전:이름'(인명사전 — 전기 전문·생몰·본관·이명) → 이명·한자명으로 i815·oldnews 재검색(당대 신문 — oldnews는 '본문:이명' OCR 전문까지) → jacar(일본 측 — 한자명) → commons(초상·PD) → 수형기록의 판결문 원문은 indy(국가기록원 판결문 테마관 — 판결기관·주문·원문) 직행.
② 한국전쟁 전투·부대: koreanwar(협약 — archRfcd→koreanwar_item 인접 채굴) → nara(RG 교차+naid 인접, judge_rights(naid) 실확인) → tna(연대 필터)·awm(가평 등 영연방)·nlna(네덜란드) → un(안보리 결의 — recid 판독으로 PDF) → commons(PD 사진·원 소장처 역추적).
③ 조선 제도·고문헌: nedb law(법전 근거)→★sibling(형제 조 전수)→sjw(최초 용례) → kyujanggak(목록+해제)·jsg(청구기호→해제 전문) → aks(문중 고문서) → 인용 2층위 준수.
④ 일제강점기 정책·기관: ndl(총독부 간행물·통계연보·관보) ⇄ jacar(공문서 메타·인접 ±100) → nedb(한국사DB)·earchive('키워드|순번' 이용조건) → i815(민족 측 시각 대조).
⑤ 도시·공간사(서울 등): seoul_archives_search(기록 단위→상세 URL 판독) → heritage(국보·사적+해설 전문 — 공간의 유산 맥락) → archives → ktv(view URL 판독) → much(실물·포스터) → commons·ia(항공·거리 사진) → cities 열쇠(Keijo·1914 경계).
⑥ 사진·영상·실물 소싱(게재용): commons(File 판독 — PD→A, 원본 고해상) → ia(radius) → nara(naid 실확인) → ktv(KOGL) → much(공공누리 자동판정 — 포스터·실물) → heritage(유산 해설·공공누리) → 게재윤리 4단계·출처 표기.
※ 각 단계의 투입 형식은 cross_search 푸터와 nedb_search 설명이 안내. 전 산출물 제작은 "풀패키지".""",
    'allies': """한국전 참전·지원국 발굴 지도 — 22개국 소스 매핑 (◉=보유 소스 직행 / ○=대체 경로)
◉ 미국: nara(RG 111·127·242·342·428)·ia·earchive(국내 수집 원문) ◉ 영국: tna(WO 281 부대 전쟁일지·ADM·AIR)
◉ 호주: awm(사진·유물 — PD 다수, 가평) ◉ 네덜란드: nlna(주한대사관 2.05.202·UN파견대 2.13.56·적십자 2.19.309)
◉ 프랑스: gallica(차단 시 브라우저) + 지평리·단장의 능선 프랑스대대는 TOPICS 프랑스어 사상 자동
○ 캐나다: LAC는 Turnstile 차단 — PPCLI(가평)는 awm·tna 영연방 교차로 ○ 터키: nara RG 407 + ia "Turkish Brigade Kunu-ri"
○ 전투 참전(태국·필리핀·콜롬비아·에티오피아·그리스·벨기에·룩셈부르크·뉴질랜드·남아공): nara(유엔군 RG)·ia에서
  부대 고유명 영문 병기 — Kagnew Battalion(에티오피아)·PEFTOK/10th BCT(필리핀)·Gloster(영)·Van Heutsz(네)
○ 의료지원(스웨덴·덴마크·노르웨이·이탈리아·인도·서독): ia·europeana — 병원선 Jutlandia(덴)·NORMASH(노)·
  60th Parachute Field Ambulance(인도) 등 고유명 검색
※ 공통 열쇠: 부대 고유명(영문)+Korea 병기 · 유엔군 총괄은 nara RG 333(극동사령부) · UN 아카이브는 챌린지 보류(명세 참조).""",
    'walls': "열한 겹의 벽 — 한국 기록이 안 찾아지는 11가지 이유와 대응 (실증 기반)\n1 일본식 독음: 금강산→Soto Kongo — 일제기 자료는 일본식 지명 병렬 / 2 로마자 철자: Corea·Korea 둘 다 / 3 기계번역 함정: 번역이 아니라 대조표(사람이 만들고 조합은 AI) / 4 외래 명명: 원산=Port Lazareff·제주=Quelpaert·거문도=Port Hamilton / 5 인명 표기: topic=persons 참조 / 6 언어 8+개국어 / 7 출처주의 분류: 찍은 사람이 서랍을 정한다(이승만 사진이 해병대 127-R-1438에) / 8 식별자: topic=identifiers / 9 기술심도: 제목만 있고 내용 없음 — 안을 열어야 함 / 10 결락: ①물리 소실(되찾을 수 없음)·②목록에 없는 것(목록에 올리면 되찾음 — 궁내청 의궤 77종 2011 환수 실증) / 11 음력/양력: 조선 기록=음력·서양=양력(대한제국 양력 채택 1896.1.1) — 두 자료를 겹칠 때 사건 순서가 뒤집힐 수 있다.\n부록 — 한자 전사 오류 복원: 연호·간지·서명 3중 교차로 원 한자 확정(예: '한풍원년 신예'→咸豊元年 辛亥, 1851).",
    'identifiers': "식별자 해독 — 번호가 곧 정보다 (첫 건은 검색어로, 나머지 수십 건은 번호 규칙으로)\n· NARA 참조코드 127-GR-223-A164360 = 기록군-시리즈-주제묶음-낱건. 주제 묶음이 차면 다음 번호(223→226 실증). NAID 간격은 계열마다 다름(사진 3·색인 1) — 하나 찾으면 ±1·±3 다 넣기.\n· 컬렉션 번호대: 같은 컬렉션인데 절반은 Chosen, 절반은 Seoul로 기술 — 검색어로는 절반만 걸린다 → NAID 앞뒤 훑기.\n· 같은 기관 안에서도 표기가 갈린다: 'Log of U.S.S.' vs 'Smooth Log of the USS' → 수식어 빼고 고유명만.\n· TNA 옆 훑기: 계열번호만 넣기(OCB 1→부산항 해도 82건·140년). 금지: 계열번호+주제어 조합(0건). 결락은 X 접미어(FO 881/9951X 병합 선언 등) — 남은 짝으로 우회. 지도는 MPKK·MFQ 등으로 추출 이관 — 원 문서철 번호로 역검색.\n· Gallica ark: btv1b=도판·필사 / bpt6k=인쇄본 — 같은 책이 형태별로 갈린다. · 6·25아카이브: 수집연도-국가-매체-일련(인접 채굴 가능). [8층 코드 지도] 미 국무부 십진분류 895 실전: .00 정치(★625-711 구간=1919.4~1928.6 — 3·1운동·임시정부) · .04 재판·형무소 · .10 공안(치안유지법) · .20 군사 · .40 사회·교육 · .50 경제·이민(하와이·미주) · .60 산업 · .71 통신 — 총독부 재정은 일본 코드 894.51(895가 0건이어도 없는 게 아니다). 검색창에 숫자 그대로.",
    'persons': "인명 열쇠 — 지명은 나라마다 갈리지만 사람 이름은 하나다\n절차: 자료 하나를 찾으면 찍은·쓴·모은·채집한 사람 이름으로 재검색 — 한 건이 컬렉션으로 열린다(Vráz→대한제국 사진 66건: 기관이 지명을 현대 표기 Inchon으로 정비해 Chemulpo 검색은 2건뿐이었다).\n표기 변형 생성: 이=Lee·Yi·Rhee·Ri / 김=Kim·Gim / 박=Park·Pak·Bak + 성명 도치(장면=Myun Chang, Dr. John)·현지 발음(서영해=Seu Ring-Hai).\n색인 함정: NARA Personalities 색인은 알파벳만이 기준 — 편철 제목에 Korea가 없어 '한국 자료'로는 안 걸린다. 구간 경계 이름(Kim·Park)은 두 칸 다 열기. 시기 구간 1940-54/1955-81 별도.\n독립운동가는 독립기념관 인명사전(search.i815.or.kr)이 이명·가명·호를 대신 생성. 채집자명은 체류국 비중 확인 — coreana와 교집합 검색으로 판정. [성씨별 색인 칸 지도·NAID] 최 Choi=109921404 · 정/전/천=109921404-405 · 서/손 Sue-Sun=109921580·Soon=109921572 · 윤 Youn=109921617 · 유/이 Yu=109921751 · 양/안 Y-Yoksi=109921616 · 이 Rhee=109921542 · 호/홍=109921479+480(두 칸 걸침 — 둘 다 열 것).",
    'crosscheck': "국내외 대조 절차 — 순서를 틀리면 헛수고한다\n① 국내 연구사부터(사학사적 검토·수집정책 보고서 — 발굴의 첫 단계는 검색창이 아니라 보고서다) ② 번역본 존재 확인(원본 뒤지기 전에 우리말 번역으로 대목을 짚는다) ③ 해외 원본(번역에 없는 부분·사진·도판) ④ 국내 원사료와 같은 날짜 겹치기(승정원일기·실록 — 음/양력 주의).\n같은 전투가 한쪽엔 '부상 30여 명', 다른 쪽엔 '승리'로 적힌다 — 둘 다 봐야 그날이 보인다.\n국내 DB 요령: 검색어는 짧게(1단어), 인명은 하나씩. 국내 소장 해외자료 먼저(국편 NARA 문서·통일원 노획문서·국회도서관 국무부 문서·6·25아카이브 55,206건).\n미기술 자료를 만나면: 기증이 어려우면 사본수집(공공기록물법 46조 — 국가기록원)·국립중앙도서관 책다모아(02-590-0700). 판단은 기관이 한다, 소장자는 연락만 하면 된다.",
    'world': "세계 서고 지도 — 6개국+ 기관·분류체계 (조선 덱 2026-08-18 실측·조사분)\n🇯🇵 일본 JACAR(jacar.go.jp): 3기관 한 창구 — A=국립공문서관·B=외무성 외교사료관(재외 한인 감시·독립운동)·C=방위연구소(군). 레퍼런스코드=영문1+숫자11(예 B04014056900) — 첫 글자가 기관, 코드 그대로 문서 직행(상세검색 All→Reference Code). 외무성 기록은 門-類-項-目 4단(한자 부수 분류 전통).\n🇨🇳 중국: 제1역사당안관(베이징·명청 1,000만건·만주문 20%) / 제2역사당안관(난징·1912-49) — ★임시정부는 제2당안관(남경 임정 100여 권·괴뢰정권 91전종 10만권 — 재만 조선인 가능성). 체계: 全宗-类-案卷-文件(우리 철·건과 같은 자리). 당안관 4,234개 — 지방 당안관에 재만 기록 가능.\n🇷🇺 러시아: ГАРФ(중앙 — '무엇을 하라' 결정) vs ГАХК 하바롭스크(지방 — '어떻게 했다' 집행). 1937 강제이주는 두 곳을 겹쳐야 실제가 나온다. 체계 ф(폰드)-оп(목록)-д(건).\n🇲🇳 몽골 NCAM: 1674년~·126만 항목·6개 언어. 외국인은 다단계 허가 — '가서 보라' 할 수 없는 기관임을 명시.\n🇰🇿 카자흐: 고려인 10만 도착지 — 중앙국립문서보관소 계열.\n★비교표: 미 RG-Series-FileUnit-Item / 영 Dept-Series-Piece-Item / 일 소장관-資料群·門類項目-簿冊-件名 / 중 全宗-类-案卷-文件 / 러 ф-оп-д / 한 기록물군-계열-철-건 — 전부 ISAD(G) fonds·series·file·item 한 뼈대(출처주의). 하나를 익히면 여섯이 읽힌다.",
    'cities': '도시명 계보 대조 — 표기 변형 실전표 (해외 카탈로그는 당대 표기로 적혀 있다)\n서울: 한성·漢城 → 경성·京城·Keijo(일본 독음)·Kyongsong → Seoul (서울의 이름 13종 실측). 부산: Fusan(독음)·초량 Tsau-liang-hai(중국식) → Pusan → Busan. 평양: Heijo. 인천: Jinsen(독음)·Chemulpo(개항장) → Inchon. 원산: Gensan·Port Lazareff. 거문도: Port Hamilton. 제주: Quelpaert. 성진: Songchin → 김책(도시명 자체 소멸 — 이중 상실). 조선 국호 철자 7종: Corea·Korea·Chosen·Chosŏn·Joseon·Corée·朝鮮.\n★규칙 1 — 1914 경계: 부군면 통폐합(1914)을 경계로 검색 어휘가 갈린다. 연도만 알면 어느 어휘를 쓸지 정해진다(4층 외래 명명은 논리가 없어 외워야 하지만 3층 개명은 규칙이 있다).\n★규칙 2 — 로마자 표기법 연대: 1959 문교부식 → 1984 MR(매큔-라이샤워, 올림픽 계기) → 2000 국어의 로마자(인터넷 계기). 기록 생산·정리 시기를 알면 카탈로그 표기를 추정할 수 있다.\n★규칙 3 — 국내 목록에 옛 표기 병기: 국내 기관이 Joseon으로만 기술할수록 Chosen으로 채워진 해외 목록과 영영 만나지 못한다 — Goguryeo(Koguryo) 방식 병기.',
}


@mcp.tool()
def query_bank(topic: str = "list") -> str:
    """검증된 한국 기록 발굴 쿼리 세트 조회. topic: 'list'(그룹 목록) 또는 그룹ID
    (예 'G-07' 구한말, 'G-08' 일제강점기, 'G-17' 간접키워드, 'N-05' NARA 시리즈, 'RG' 교차매핑, 'TNA' 레이어)
    전략 지식: 'walls'(열한 겹의 벽), 'identifiers'(식별자 해독), 'persons'(인명 열쇠), 'crosscheck'(국내외 대조), 'world'(6개국 서고 지도), 'cities'(도시명 계보), 'allies'(한국전 참전·지원 22개국 발굴 지도)."""
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
    if topic.strip().lower() in JB_STRAT:
        return JB_STRAT[topic.strip().lower()]
    return "해당 그룹 없음 — topic='list'(해외 G/N/RG/TNA) 또는 'domestic'"

@mcp.tool()
def judge_rights(rg_series: str = "", title: str = "", archive: str = "", naid: int | None = None) -> str:
    """권리 등급 자동 초기판정 (보고서 §30 플로 1~3단계). A/B=공개가능, C=허가필요, D=지위불명.
    공공누리(KOGL) 제1~4유형 자동 인식 — 어느 필드든 'KOGL 2'·'공공누리 제1유형' 표기 투입 시 조건 판정.
    naid 지정 시 NARA 카탈로그 Use Restriction 필드를 실제 조회해 자동판정(Unrestricted 실확인 → A 확정,
    Restricted → C). 발굴 우선, 권리는 표시. ※ 최종 확정은 사람이 §30 5단계로 서면 판정할 것."""
    if naid:  # NAID 실확인 자동판정 — "Unrestricted 확인 시 A 상향" 규칙의 자동화
        import re as _re
        key = os.environ.get("NARA_API_KEY")
        if not key:
            return (f"NAID 실확인은 서버 NARA_API_KEY 필요 — rg_series 초판정을 사용하거나 "
                    f"catalog.archives.gov/id/{naid} 의 Use Restriction을 직접 확인하십시오.")
        try:
            d = http_json(f"https://catalog.archives.gov/api/v2/records/search?naId={naid}&limit=1",
                          headers={"x-api-key": key})
            hits = (((d.get("body") or {}).get("hits") or {}).get("hits") or [])
            rec = ((hits[0].get("_source") or {}).get("record") or {}) if hits else {}
            if not rec.get("naId") or int(rec["naId"]) != naid:
                return f"[NAID {naid}] 카탈로그에 없음 — NAID를 확인하거나 rg_series 초판정을 사용하십시오."
            ur = rec.get("useRestriction") or {}
            urs = ur if isinstance(ur, str) else " · ".join(
                x for x in [ur.get("status"), ur.get("note"), "/".join(ur.get("specificUseRestrictions") or [])] if x)
            rgnum = rec.get("recordGroupNumber") or next(
                (a.get("recordGroupNumber") for a in (rec.get("ancestors") or []) if a.get("recordGroupNumber")), "")
            cls, basis = auto_rights({"rg_series": f"RG {rgnum}" if rgnum else rg_series,
                                      "title_orig": rec.get("title") or title, "archive": "NARA"})
            if _re.search(r"unrestricted", urs, _re.I) and not _re.search(r"restricted\s*[-–]|possibly|fully restricted", urs, _re.I):
                cls, basis = "A", f"NARA 카탈로그 Use Restriction '{urs}' 실확인 — 제한 없음 확정 (출처 표기 권장)"
            elif _re.search(r"restricted", urs, _re.I):
                cls, basis = "C", f"NARA 카탈로그 Use Restriction '{urs}' 실확인 — 제한 표기, 기관 확인 필요"
            elif urs:
                basis += f" · Use Restriction '{urs[:80]}' (판정 불변 — 문구 확인 필요)"
            else:
                basis += " · 카탈로그에 Use Restriction 미기재 — RG 초판정 유지"
            # 맥락(v1.80): ancestors 전 계층 체인 — RG › 시리즈 › 파일단위, 각 층 NAID 포함(상·하위 항행 좌표)
            chain = " › ".join(
                (f"{_re.sub(r'recordGroup', 'RG', str(a.get('levelOfDescription') or ''), flags=_re.I)} "
                 f"{a.get('recordGroupNumber') or ''}"
                 + (" " + str(a.get("title"))[:60] if a.get("title") else "")
                 + (f" [NAID {a.get('naId')}]" if a.get("naId") else "")).strip()
                for a in (rec.get("ancestors") or []))
            chain = _re.sub(r"\s+", " ", chain)
            # 증거성(v1.80): 범위·내용 기술(scope note) 발췌 + 판독 시점 본문 지문
            import hashlib as _hs
            scope = str(rec.get("scopeAndContentNote") or "").strip()
            sfp = _hs.sha256(scope.encode("utf-8")).hexdigest()[:16] if scope else ""
            return (f"[NAID {naid}] {rec.get('title','')[:95]}\n"
                    f"{f'RG {rgnum} · ' if rgnum else ''}https://catalog.archives.gov/id/{naid}\n"
                    + (f"계보: {chain[:280]}\n" if chain else "")
                    + (f"【범위·내용】 {scope[:400]}\n본문 지문(sha256-16): {sfp} — 판독 시점 기술(記述) 전문 기준. 재판독 지문 불일치=카탈로그 기술 개정 발생.\n" if scope else "")
                    + f"등급: {cls}\n근거: {basis}\n※ 카탈로그 실확인 기반 자동판정 — 공개 전 수동 확정 필수, D등급 공개 금지\n"
                    + f"※ 인접 채굴: nara_search(naid={naid}, radius=3) — 사진 ±3·색인 ±1 간격.")
        except Exception as e:
            return f"[NAID {naid}] 카탈로그 조회 실패({str(e)[:60]}) — rg_series 초판정으로 폴백하십시오."
    cls, note = auto_rights({"rg_series": rg_series, "title_orig": title, "archive": archive})
    return f"등급: {cls}\n근거: {note}\n※ 자동 초기판정 — 공개 전 수동 확정 필수, D등급 공개 금지"


def _gallica_ko_fr(q):
    return _to_index_lang(q, "fr")


@mcp.tool()
def gallica_search(query: str, max_results: int = 15, year_from: int | None = None,
                   year_to: int | None = None, page: int = 1) -> str:
    """프랑스 국립도서관 Gallica 검색 (SRU API, 키 불요). 다국어 질의(한국어·日本語·中文 등)를
    프랑스어 색인어로 자동 변환(병인양요→expédition de Corée 1866, 선교사→missionnaires, 조선→Corée …).
    프랑스어 직접 입력도 가능 — 'Corée', 'guerre de Corée', 'Séoul', 'Tchosen'. 구한말
    프랑스 선교사·외교 문헌과 사진의 보고. 예: gallica_search('병인양요 선교사')"""
    import urllib.parse, urllib.request, xml.etree.ElementTree as ET
    fr = _gallica_ko_fr(query)
    eff = fr or query
    base = f'gallica all "{eff}"' if '"' not in eff else f'gallica all {eff}'
    # 연대 필터: BnF 공식 색인 dc.date(>=·<= 지원, api.bnf.fr) — 진단 응답이면 후처리 폴백
    date_clause = (f' and dc.date >= "{year_from}"' if year_from else "") + \
                  (f' and dc.date <= "{year_to}"' if year_to else "")
    ns = {"srw": "http://www.loc.gov/zing/srw/", "dc": "http://purl.org/dc/elements/1.1/"}

    def _sru(cql):
        url = (f"https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2"
               f"&query={urllib.parse.quote(cql)}&maximumRecords={min(max_results,50)}"
               f"&startRecord={(page - 1) * max_results + 1}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=40) as r:
            return ET.fromstring(r.read().decode("utf-8", "replace"))

    root = _sru(base + date_clause)
    total = root.find(".//srw:numberOfRecords", ns)
    post = False
    if date_clause and total is None:
        root = _sru(base); total = root.find(".//srw:numberOfRecords", ns); post = True
    if total is None:  # SRU XML 아님 — Cloudflare 차단/점검 (2026-11-18 실측: 서버 IP 403)
        return (f"Gallica '{query}'" + (f" → 프랑스어 자동 변환 '{eff}'" if fr else "")
                + " — 서버 자동 조회가 차단되었습니다(BnF측 봇 차단 — 간헐적).\n"
                + f"➤ 에이전트 지시: 웹 검색/브라우저 도구로 '{eff}'를 gallica.bnf.fr에서 검색해 "
                + "상위 결과(제목·연대·ark 링크)를 표로 정리해 제시하라.\n"
                + "공식 검색: https://gallica.bnf.fr/services/engine/search/sru?operation=searchRetrieve&query="
                + urllib.parse.quote(eff))

    def g(rec, tag):
        e = rec.find(f".//dc:{tag}", ns)
        return (e.text or "").strip() if e is not None and e.text else ""
    recs = root.findall(".//srw:record", ns)
    if post:
        def _y(rec):
            m = re.search(r"\d{4}", g(rec, "date"))
            return int(m.group(0)) if m else None
        recs = [r for r in recs if (_y(r) and (not year_from or _y(r) >= year_from)
                                    and (not year_to or _y(r) <= year_to))]
    lines = [f"- {g(r,'title')[:100]} ({g(r,'date')}) [{g(r,'type')[:20]}] {g(r,'identifier')}"
             for r in recs[:max_results]]
    yt = (f" [간행 {year_from or ''}~{year_to or ''}" + ("·후처리·연대 미상 제외" if post else "") + "]") if (year_from or year_to) else ""
    pt = f" (p.{page})" if page > 1 else ""
    return (f"Gallica '{query}'" + (f" → 프랑스어 자동 변환 '{eff}'" if fr else "") + yt + pt
            + f" — 총 {total.text if total is not None else '?'}건"
            + (f" 중 이 페이지 연대 일치 {len(lines)}건" if post else "") + ":\n"
            + ("\n".join(lines) or "(0건)")
            + "\n팁: 프랑스어 변형 — Corée·Coréens·Séoul·Fusan·guerre de Corée·Tchosen")

@mcp.tool()
def europeana_search(query: str, max_results: int = 15, media_type: str | None = None,
                     year_from: int | None = None, year_to: int | None = None, page: int = 1) -> str:
    """유럽 문화유산 통합 검색 Europeana (58개국 4,000+ 기관). 키 없이 즉시 작동(공용 데모 키) —
    대량 사용 시 apis.europeana.eu 무료 키를 EUROPEANA_API_KEY로. 다국어 질의(한국어·日本語·中文 등)는
    영문 색인어로 자동 변환. media_type: 'VIDEO'|'IMAGE'|'TEXT'|'SOUND'. 예: europeana_search('Corée', media_type='IMAGE')"""
    import urllib.parse, json as _json, urllib.request
    key = os.environ.get("EUROPEANA_API_KEY") or "api2demo"
    demo = not os.environ.get("EUROPEANA_API_KEY")
    query = _ko_en(query) or query
    params = [("wskey", key), ("query", query), ("rows", min(max_results, 50)),
              ("profile", "standard"), ("start", (page - 1) * max_results + 1)]
    if media_type: params.append(("qf", f"TYPE:{media_type.upper()}"))
    # YEAR:[A TO B] 열린 범위(*)·다중 qf 실측 검증 (2026-11-18)
    if year_from or year_to: params.append(("qf", f"YEAR:[{year_from or '*'} TO {year_to or '*'}]"))
    url = "https://api.europeana.eu/record/v2/search.json?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = _json.loads(r.read().decode())
    items = data.get("items") or []

    def _rshort(r):
        v = (r[0] if isinstance(r, list) and r else r) or ""
        m = re.search(r"(publicdomain/(?:mark|zero)|licenses/[a-z-]+|vocab/[A-Za-z-]+)", str(v))
        return m.group(1).replace("licenses/", "CC ").replace("vocab/", "") if m else ""
    lines = []
    for it in items[:max_results]:
        title = (it.get("title") or ["?"])[0]
        year = (it.get("year") or [""])[0]
        prov = (it.get("dataProvider") or [""])[0]
        rt = _rshort(it.get("rights"))
        lines.append(f"- {str(title)[:90]} ({year}) — {str(prov)[:40]}"
                     + (f" | 권리:{rt}" if rt else "") + f" | {it.get('guid','')}")
    return (f"Europeana '{query}'" + (f" [{media_type}]" if media_type else "")
            + f" — 총 {data.get('totalResults')}건:\n" + ("\n".join(lines) or "(0건)")
            + ("\n※ 공용 데모 키(api2demo) 사용 중 — 레이트리밋 시 EUROPEANA_API_KEY 설정 권장." if demo else "")
            + "\n팁: 다국어 병행 — Corée(불)·Korea-Krieg(독)·Corea(이/스)")



REPORT_RULES = """HTML 발굴 보고서 작성 규칙 (19) — 잡지·저널급 편집 기준
1. 파일명: [주제영문]_records_[연도범위].html — 조사 완료 시 기본 산출물
2. 지면 구조(잡지형): masthead → kicker → 표제(h1) → standfirst → byline(기관 chip) → 목차(nav.toc) → 히어로 figure → Ⅰ서사 → Ⅱ핵심 기록 카드 → Ⅲ영상 필름스트립 → Ⅳ전수 목록 표 → Ⅴ재현 쿼리(details) → Ⅵ권리·게재 윤리 → 출처 총람(.sources) → footer
3. 서사 우선: 표만 나열 금지 — 발굴 경위·의미를 에세이로 서술(리드 문단 .lead 드롭캡, 풀인용 .pull 1개 이상). 문단이 실물을 설명하면 그 문단 옆에 인라인 도판(.fig-inline 플로트)을 배치 — 잡지처럼 글과 그림이 같은 화면에 보이게. 문체는 담백·구체 — 과장어(놀라운·혁신적 등)와 AI투 금지
4. 실물 이미지 필수: 게재 가능(권리 A/B+게재윤리 1·2단계) 기록은 기관 공개 원본을 base64 임베드 — 히어로 1장+핵심 기록마다, 공개 컷은 전량(.sheet 콘택트시트·컷별 라벨). 비식별판 우선. 이미지는 max-width:100% 자동 축소. 환경별: 로컬=base64 임베드 / 웹·모바일(파일·base64 불가)=기관 공개 원본 URL을 img src로 직접 참조하고 footer에 그 사실을 명기. 한 장도 못 실으면 사유를 Ⅵ절에 명기
5. 모든 이미지에 figcaption + .credit 필수: "출처: 기관 정식명(국가) · 식별자 · 촬영자/생산자 · 원본 링크" — 출처 없는 이미지는 싣지 않는다
6. 영상 기록은 .film 필름스트립: 장면 전환마다 프레임을 충분히 추출(권장 8~16장)해 타임코드(.tc)+한 줄 설명으로 나열 — 표제가 가린 장면(ETC 뒤)을 드러내 원본을 직접 보고 싶게 만든다. 슬레이트·표지판 판독 프레임은 별도 확대 figure. 블록 끝에 .cta "▶ 원본 영상 보기 — [기관] 카탈로그"
7. 핵심 기록 3~6건은 .record 카드로: 이미지 + 한국어 제목(원제 병기) + .prov 출처 계보(국가→기관→RG/시리즈→상자→식별자) + 요약 + 바로가기 버튼 + 권리 배지 — .prov의 시리즈 층은 cross_search(format='csv'·'manifest')의 partOf 값을 그대로 옮긴다(수기 재구성 금지 — 지면과 데이터의 계보 일치)
8. 전수 목록 표(부록형): 식별자·원제 / 연대 / 소장처·계보(partOf — RG·시리즈·수집구조)·청구정보 / 내용 / 바로가기(원문→해제→카탈로그) / 권리초판 배지(b-A 공개확정 · b-B PD추정 · b-C 허가필요 · b-D 지위불명)
9. 출처 명시(전 지면): byline·본문에 기관 chip(국기 이모지+정식명 — 🇺🇸 NARA · 🇬🇧 TNA · 🇫🇷 BnF Gallica · 🇪🇺 Europeana · 🇺🇸 archive.org · 🇰🇷 국가기록원 · 🇰🇷 KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터 등), 말미 .sources에 인용 기관 총람(국기·정식명·청구정보·이용조건·링크)
10. 재현 쿼리는 details 접이식 — 실제 실행한 쿼리만(목적/쿼리/URL 인코딩 실행 링크). '0건 ≠ 부재' note(인접 상자 ±2·피스 ±15 권고) 포함
11. 종합 색인·최신 연구 목록(ul.src) — details로 접어도 된다
12. Ⅵ 권리 절: 법적 근거(17 U.S.C. §105 · 36 CFR 1254.62 · Crown/OGL · domaine public · KOGL) + '출판 전 인간 최종 확인 필수' + D등급 공개 금지. 민감 주제(위안부·포로·학살)는 피해자 존엄 문구와 게재윤리 4단계(거부할 수 없었던 처지의 촬영 = 화면 미사용) 적용
13. 링크·수치는 도구 호출로 실확인한 것만 — 추정 URL 금지, footer에 '모든 링크 [날짜] 접속 확인' 명기
14. 연표·지도·관계도는 인라인 svg로 직접 작성 가능. 외부 리소스 금지(폰트·CDN) — 로컬은 단일 파일 자기완결(base64), 웹·모바일 산출만 기관 공개 이미지 URL 참조 예외 허용
15. 인쇄 대응: 템플릿의 @media print 유지 — 보고서는 그대로 출판물처럼 인쇄 가능해야 한다
16. 링크 신뢰장치: ①digitised 기록은 카탈로그 무료 미리보기 이미지를 공식 엔드포인트로 확보해 원문 figure로 임베드(예: TNA /image/getimage — 워터마크 원상태, 유료 전체본은 안내만) ②그 외 주요 링크는 페이지 캡쳐본 figure+credit(갈무리 일자) ③자동화 차단 시 명기하고 API 기술 원문 인용표로 대체. 훈격·날짜·건수는 API 원문 대조 '검증 기록'으로 — 초판 오류는 정정 이력을 남긴다
17. 카드뉴스·포스터 병행: 보고서와 함께 캐러셀(기본 8장, 1080×1080)과 포스터 시리즈(1080×1350 세로형 4~6장 — 표제·인물·문서·검증·초대의 연작 서사, 같은 검수 기준 — insta-carousel 스킬 또는 report_template(kind='carousel') 참조)을 제작하고, 보고서 말미 '카드뉴스' 절에 .cards-grid로 임베드한다 — 무크롭 전체 노출 + 카드별 figcaption, 잘림·겹침 금지. 커버는 히어로와 같은 실물 이미지, 검증 노트·따라하기 카드 포함, 보고서와 출처 대장 공유. PNG 원본·caption.txt·sources.txt를 보고서와 함께 납품
18. 더 보기 절(Ⅷ): 출처 총람 직전에 관련 공개 콘텐츠 소개 — 뉴스(📰)·기관 아카이브(🏛️)·해설/백과(📚)·SNS/영상 등을 카테고리 이모지+한 줄 설명으로. 접속 확인한 링크만(확인일 명기), 미확보 카테고리는 그 사실+추천 검색어 명시 — 발굴을 현재의 기억과 잇는 절
19. 수집기록 매니페스트 부록(증거성 상속): 보고서 끝에 cross_search(format='manifest') JSON을 <details> 부록으로 그대로 수록 — provenance(질의·소스·수집시각·재현 호출)와 기록별 heldBy·영속 식별자가 보고서를 떠나 전파되어도 따라간다. 카드뉴스·포스터 등 2차 매체에는 sources.txt에 매니페스트 identifier(kad-…)와 재현 호출문을 1줄 명기 — 어떤 매개로 변환되어도 원 발굴로 되돌아올 수 있게(현용기록물의 맥락·증거성 유지)"""

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
4. 이미지 카드마다 출처 캡션(.credit) 필수: "출처: 기관 정식명, 식별번호 (라이선스)" — 식별번호를 알면서 생략하면 부정확한 출처다. 시리즈 계보(partOf)를 알면 "기관 › 시리즈" 1줄 병기(데이터의 partOf 값 그대로). 이미지별 출처 대장(sources.txt) 동봉, 라이선스 미확정이면 '게시 전 [권리자] 확인' 안내
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

CITATION_GUIDE = '인용 형식 가이드 — 한국사DB·국회도서관 (khdb-citation·nanet-citation 스킬의 서버판. 사용자의 논문·보고서 인용 요청에 이 형식을 적용하라)\n\n■ 한국사데이터베이스(db.history.go.kr) — 국사편찬위원회\n· 영구 인용 URL: http://db.history.go.kr/id/[기사ID]  (검색 URL은 POST라 재현 불가 — 반드시 /id/ 형식)\n· 각주(국내 표준): 저자, 〈[문서 제목]〉 작성일.(편찬기관 편, 연도, 《[총서명 권호]》) http://db.history.go.kr/id/[기사ID] (accessed YYYY.M.D.)\n· 참고문헌: [편찬기관]. 『[총서명]』. [권호]. 국사편찬위원회 한국사데이터베이스(http://db.history.go.kr), 검색일: YYYY.MM.DD.\n· 연대기(실록·승정원일기): 『[자료명]』 [왕명 연호년 월일(간지)], 국사편찬위원회 한국사데이터베이스, http://db.history.go.kr/id/[기사ID] (검색일: YYYY.MM.DD.)\n· 예: 조선총독부 고등법원 예심계, 〈한용운 신문조서〉 1919.8.27.(국사편찬위원회 편, 1990, 《한민족독립운동사자료집 12》) http://db.history.go.kr/id/hd_012r_0010_0310 (accessed 2026.3.13.)\n· ★인용 2층위 필수 고지 — 법전·편람(조선시대법령자료)은 한문 원문 제공 → 원문 인용 가능(표점은 DB 형태·교감본 미대조 명기). 등록·일기(비변사등록·승정원일기)는 국역만 노출 → 한문 역구성은 학술 인용 불가.\n· 출처 표기: KOGL — 국사편찬위원회 출처 표기.\n\n■ 국회도서관 전자도서관(dl.nanet.go.kr)\n· 영구 인용 URL: https://dl.nanet.go.kr/SearchDetailView.do?cn=[CN코드]  (CN코드가 식별자 — 예 KDMT1201319543)\n· 학위논문 각주: 저자명, 「논문 제목」, 학위논문(석사/박사), 대학교 대학원 학과명, YYYY.M, 쪽수.\n· 학위논문 참고문헌: 저자명. 「논문 제목」. 학위논문(석사/박사). 대학교 대학원 학과명, YYYY. 대한민국 국회도서관 전자도서관(https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드), 검색일: YYYY.MM.DD.\n· APA: 저자성, 이름. (연도). 제목 [학위 종류, 대학교명]. 국회도서관 전자도서관. https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드\n· Chicago: 저자명, “제목” (학위논문(박사), 대학교명, 연도), 쪽수. https://dl.nanet.go.kr/SearchDetailView.do?cn=CN코드 (검색일: YYYY년 MM월 DD일).\n· 단행본·학술기사·정부간행물도 같은 골격 — 「」=논문/기사, 『』=서명·총서명, CN코드 URL 동봉.\n\n공통 원칙: 검색일 명기 · 링크는 실확인한 것만 · 기사ID/CN코드 없는 인용은 재현 불가이므로 금지.'

ANNOTATION_GUIDE = "기록 해설형 어노테이션 규칙 — 상세판 (record-annotation 스킬의 서버판. 웹에서는 HTML/아티팩트로 동일 문법 구현)\n\n1. 영역 표시: 점선 영역 박스(dashed 1.5~2px) + 박스 모서리 바깥 번호 칩 — 점 찍기·내용 가림 금지. 좌표는 %(x,y,w,h)로 기록해 어느 해상도에서도 재현.\n2. 전처리: 레터박스(검은 띠) 자동 크롭 후 원본 비율 유지. 저해상 프레임은 확대 금지 — 원본 크기 근처로 배치.\n3. 메타데이터 표(7행 기준): 제목 · 식별번호(영구 식별자) · 원 제작(판독 근거 병기) · 사본 소재 · 생산시기 · 권리(원판/사본 구분) · 판독 근거.\n4. 범례: 번호 칩 + 굵은 요소명 + 한 줄 해설. 순서는 판독 서사(제작 주체→내용→좌표→판본) 순.\n5. ★추정 금지: 화면·원문에서 직접 읽히는 것만 적는다. 불명은 '판독 불가'로 명기 — '아마도·추정·으로 보임'류 어휘가 해설에 들어가면 재검토.\n6. 원판/사본 계보 필수: 원판 권리(PD 등)와 디지털화본 표시(워터마크·업체)를 구분 명기.\n7. 산출 3형: 보고서 부록 절('기록을 해설해 드립니다') · 카드뉴스(1080 — 범례 압축·2열 허용) · 슬라이드(도형 마커+노트에 판독 해설).\n8. 권리 고지: 기관 정식명·식별자·열람 URL — 협약기관(KOREAN WAR ARCHIVES) 출처 표기 필수, 게재윤리 4단계.\n9. 영상 프레임 판독 보강(슬레이트·화면 속 문자): 슬레이트/타이틀 카드에서 부대·촬영자·날짜·롤 번호·장소 필드를 파싱하고, 당대 지명(일본식 독음·외래 명명)은 현대 지명과 병기. 표지판·현수막·차량 표식 등 화면 속 문자는 OCR과 육안을 교차해 확정 — 불일치·판독 불가는 그대로 표기(추정 금지 원칙 동일)."

EXHIBIT_GUIDE = """고문서 전시형 산출물 규칙 — aks-archive-harvester 스킬 ④매개(Mediate) 단계의 서버판 (웹·모바일 동등성).
nedb_search(mode=aks)로 발굴한 문중·서원 고문서를 전시 페이지·카드뉴스·학습지로 만드는 규칙.

■ 산출물 4종
① 전시 페이지(단일 HTML): 표제·도입문(lead) → 시대 타임라인 → 문서별 패널(도판+캡션+이야기) → 출처 고지. 인쇄 시 패널 단위로 나뉘는 구성. 웹=아티팩트 미리보기, 로컬=파일 저장.
② 카드뉴스(1080×1350): 표지 1장 + 문서별 1장 + 클로징 1장. 문서 카드 = 도판(상단 70%)+캡션 띠(하단). 로컬=헤드리스 크롬 렌더, 웹=아티팩트/Canva 커넥터.
③ 학습지(A4 1장): "이 문서는 무엇인가"(유형·연대·발급자) · "찾아보기"(도판에서 날짜·수취인 찾기) · "생각해보기"(열린 질문 1개) · 요약 박스.
④ 게시 문구: 2~3문장 + 해시태그 — 기관명·소장처명 반드시 포함.

■ 캡션·서술 규칙 (추정 금지)
- 제목·문서유형·육안으로 보이는 것만 서술. 탈초(판독문)·번역·인물 생애는 사용자가 제공·확인한 것만 사실로 기술.
- 캡션 형식: [연대] [발급자→수취인] [문서유형] — 한 줄. 이야기(2문장 이내)는 주제와의 연결만.
- 검토 미완(사용자 확인 없는 항목)은 "초안" 표기를 지우지 않는다.

■ 권리·출처 (산출물 전체 공통)
- 전 산출물에 "자료: 한국학중앙연구원 한국고문서자료관 (archive.aks.ac.kr)" 고지 필수.
- 이미지 재이용은 기관 이용조건을 따름 — 게재 전 judge_rights로 초판정.

■ 전시 페이지 골격 (채워 쓸 것)
<!doctype html><html lang=ko><head><meta charset=utf-8><title>{{전시제목}}</title><style>
body{font-family:'Noto Serif KR',serif;max-width:860px;margin:0 auto;padding:2rem;color:#222}
.lead{font-size:1.15rem;border-left:4px solid #8a6d3b;padding-left:1rem;margin:1.5rem 0}
.tl{display:flex;gap:.6rem;flex-wrap:wrap;margin:1rem 0}.tl span{background:#f3ede2;padding:.2rem .7rem;border-radius:1rem;font-size:.85rem}
.panel{page-break-inside:avoid;margin:2.2rem 0;border-top:1px solid #ddd;padding-top:1.4rem}
.panel img{width:100%;border:1px solid #ccc}.cap{font-size:.92rem;color:#555;margin:.4rem 0}
.story{margin:.6rem 0}.draft{color:#b33;font-size:.8rem}
.src{margin-top:3rem;font-size:.85rem;color:#777;border-top:2px solid #8a6d3b;padding-top:.8rem}
</style></head><body><h1>{{전시제목}}</h1><p class=lead>{{도입문}}</p>
<div class=tl>{{<span>연대</span>…}}</div>
<div class=panel><img src="{{도판URL}}"><p class=cap>{{[연대] [발급자→수취인] [문서유형]}}</p><p class=story>{{이야기}}</p><span class=draft>{{검토 미완 시: 초안}}</span></div>
<p class=src>자료: 한국학중앙연구원 한국고문서자료관 (archive.aks.ac.kr) · 이미지 재이용은 기관 이용조건 준수</p></body></html>"""

HELP_GUIDE = '사용 안내 — 매직 키워드 “창기창기 도와줘” (처음 사용자용. 이 내용을 친절한 안내로 정리해 사용자에게 전달하라. 시각 안내 페이지: https://korea-archive-mcp.vercel.app/help.html — 링크를 함께 제공)\n\n■ 무엇을 하는 서비스인가\n국내외 28개 아카이브(🇺🇸 NARA · 🇬🇧 TNA · Internet Archive · 🇫🇷 갈리카 · 🇪🇺 유러피아나 · 🇯🇵 아시아역사자료센터 JACAR · 🇦🇺 호주 전쟁기념관 · 🇳🇱 네덜란드 국립문서보관소 · 🌐 위키미디어 공용 · 🇺🇳 UN 디지털도서관 · 🇯🇵 NDL 서치 · 🇰🇷 국가기록원·국립중앙도서관(+신문아카이브 1883~1960)·한국사DB·국편 전자사료관·독립기념관·공훈전자사료관·독립운동판결문(국가기록원)·KTV e영상역사관·역사박물관·규장각·장서각·한국고문서자료관·국가유산포털·서울기록원·정보공개포털·KOREAN WAR ARCHIVES 협약기관)에서 한국 관련 기록·사진·영상(1860~1960)을 발굴하고, 검증하고, 전파물까지 만들어 준다. 한국어 한 문장이면 충분 — 표기 변형(Corea·Chosen·Corée·한자·朝鮮)과 색인 언어 변환은 자동. 카카오 PlayMCP 마켓 등록본으로도 연결 가능(\'KOREA ARCHIVE 통합검색\' 검색 — 같은 서버).\n\n■ 매직 키워드 2개\n① “○○○ 풀패키지로 만들어줘” — 조사→검증→매거진 보고서→카드뉴스 8장→포스터→홍보·입문·메시지 카드→발표 PPTX(대본 포함)→기록 해설→Canva 편집본→KARDA 연구 데이터·시연 영상(데모 GIF)까지 전 산출물 자동(report_template kind=full_package 순서를 따름).\n② “창기창기 도와줘” — 이 사용 안내.\n\n■ 이렇게 물어보면 된다 (예시)\n· “할아버지가 참전한 글로스터 연대 기록 찾아줘” (실전 1호 — TNA 훈장 추천서 원문까지)\n· “장진호 전투 영상 기록 찾아줘” (실전 2호 — 3개국 3중 소장 실증)\n· “조선시대 한강 나루의 행정을 정리해줘” (법전 판독→형제 조 전수→연대 검증 제도사)\n· “병인양요 프랑스 기록 찾아줘” / “이 참조코드 주변을 더 캐줘”(인접 채굴) / “이 기록 게재 가능한지 판정해줘”\n· “안중근 공훈록 전문 보여줘”(독립유공자 — 공적조서·수형기록·현충시설까지) / “이 NARA 기록 권리 실확인해줘”(naid)\n· “이 의궤 해제 읽어줘”(장서각 K2-…) / “안보리 결의 원문 PDF”(UN recid) / “이 1910년 기사 전문”(독립기념관 URL)\n\n■ 검증 원칙(차별점) — 실물 기록만(AI 생성 인물·장면 금지)·원문 대조·출처 명시·정정 공개. 통과 산출물에만 검증 낙관.\n\n■ 자주 묻는 것\n· 0건 → 부재가 아니다. 표기 변형·인접 채굴·“대상을 관리한 행정”으로 전환.\n· ZIP 일괄 납품은 로컬 환경 전용 — 웹·모바일은 개별 아티팩트+manifest.\n· 이미지: 웹은 기관 공개 URL 참조 — 원본은 항상 기관 링크에서 열람.\n· 조선 주제 → nedb_search 심층 판독 모드(law·sibling·matrix·origin·record·sjw·kyujanggak·aks[한국고문서자료관 — 문중·서원 고문서 172곳]). 심층 판독 11채널 — 발굴 결과의 URL·번호를 nedb_search 모드에 재투입: i815(당대 신문 전문)·gonghun(공적조서·공훈록)·jacar(일본 공문서)·ktv(대한뉴스 해설)·earchive(수집 사료 이용조건)·commons(PD 라이선스)·jsg(장서각 해제)·un(UN 요약·PDF)·oldnews(신문 색인어·관련기사·\'본문:\' OCR 전문)·much(소장품·공공누리 자동판정) + seoul_archives_search(상세 URL). 연합 검색 푸터가 경로를 안내한다.\n· 연대로 좁히기 → 주요 검색 도구의 year_from/year_to. 번호 옆 훑기(인접 채굴) → TNA·NARA(naid)·archive.org(radius)·6·25아카이브. 당대 표기 자동 팬아웃 → cross_search(variants). 채널 상태 → source_profile(\'health\').\n· 데이터화 3종 → cross_search format=\'csv\'(표·통계) · \'karda\'(지식그래프 nodes/edges) · \'manifest\'(수집기록 매니페스트 JSON-LD — 증거성·맥락 보존, 기록관리시스템 등재·다매체 변환의 원천).\n\n커넥터: korea-archive-mcp.vercel.app/api/mcp · 안내 페이지: korea-archive-mcp.vercel.app/help.html'

FULL_PACKAGE = """풀패키지 오케스트레이션 — 발굴에서 전파물까지 한 번에 (매직 키워드: "풀패키지" · "전부 다 만들어줘")
입력은 주제 하나면 충분하다. 아래 순서를 전부 수행해 모든 산출물을 함께 납품한다.

1. 발굴 조사: cross_search + 전문 도구(tna_search/nara_search/koreanwar_search/gallica_search…) — 표기 변형 병렬,
   시리즈 특정+tna_adjacent_mine 인접 채굴(±5~15), 국내 협약기관 교차검증, 카탈로그 API 원문으로 훈격·날짜·건수 검증
   (정정 발생 시 이력 기록), judge_rights 권리 초판. 핵심 기록은 심층 판독으로 본문·권리 실확인: nedb_search 모드(i815 당대 신문·gonghun 공훈록·ktv 영상·earchive 수집사료·commons PD파일·jsg 해제)와 seoul_archives_search(상세URL)·koreanwar_item·judge_rights(naid). 조선~대한제국 주제면 심층 판독 경로 추가: nedb_search 모드 활용 — law(법전 근거)→★sibling(조문을 열었으면 형제 조 전수 — 총론만 읽으면 핵심을 놓친다)→matrix(법전 수록 대조로 부재 발견)→origin(어휘 연원)→record(등록류 — 座目 필터)→sjw(최초 용례로 연대 검증)→kyujanggak(목록+해제). 보고서에 제도 재구성 절(등록·측정·운항·동원·보상 + 제도의 끝)·법전 대조표·자기 정정 이력을 추가하고, 인용은 2층위(법전=원문 인용 가능/등록·일기=국역만·역구성 학술 인용 불가) 명기.
2. 실물 이미지 수집: 기관 공개 원본 전량(비식별판 우선) + digitised 기록의 카탈로그 무료 미리보기.
   수집 즉시 출처 대장(sources.txt) 기록. AI 생성 인물·역사 장면 절대 금지.
3. HTML 보고서: report_template(kind='report') 19규칙 전부 — 히어로 실물·인라인 도판·콘택트시트·원문 미리보기·
   검증 기록·전수 목록·재현 쿼리·더 보기·카드뉴스 갤러리. 매거진 완성판은 kind=magazine 확장팩을 덧입힌다. 산출 방식 — 로컬: .html 파일 저장 / 웹·모바일: HTML 아티팩트로 게시(파일 저장 불가), 이미지는 기관 공개 URL 참조. 수치는 모든 산출물에서 동일해야 한다.
4. 캐러셀 8장: report_template(kind='carousel') 12규칙 — 커버는 보고서 히어로와 같은 실물, 검증 노트·따라하기 포함.
   렌더는 환경별: 로컬=헤드리스 렌더 / 웹·모바일=Canva 커넥터 생성→페이지별 PNG 내보내기. 전 장 육안 검수 생략 금지.
   caption.txt + sources.txt 동봉.
5. Canva 산출물(커넥터 연결 시): 캐러셀 편집본 + report_template(kind='canva_prompts') 1번 템플릿으로 포스터 1종 —
   생성 직후 전 한국어 문구를 검증 카피로 교정(replace_text) 후 저장.
6. 납품: 보고서 HTML + 카드 8장 + 포스터 시리즈 + caption/sources + Canva 링크. 로컬: 전체를 [주제영문]_fullpackage_[날짜].zip으로 묶어 함께 납품 — 구조 report/·cards/·posters/·canva/·pptx/·manifest.txt(산출물 목록+검증 요약). 웹·모바일: zip 생성 불가 — 개별 아티팩트로 제시하고 manifest 목록을 함께 출력. SNS 게시·공개 푸시는 사용자 확인 후. 발표자료(pptx): 발표·강의용 16:9 슬라이드 12~16장 병행 제작 — 표지·목차·발굴 경위·핵심 기록(실물 프레임+보고서 지면 캡쳐)·검증과 윤리·KARDA·전파물·CTA·출처 총람. 전 슬라이드 발표 노트(대본)와 도판별 출처 표기 필수, 저해상 프레임은 풀블리드 확대 대신 필름스트립 다컷 배치. Canva 편집본: 로컬은 공개 쇼케이스 URL 경유 import-design-from-url, 웹은 Canva 커넥터로 직접 생성해 편집 링크 제공.
7. 작업 로그(activity_log.md): 조사 중 모든 행위를 시간순 표로 기록 — 단계(발굴/교차검증/검증/수집/산출)·행위·도구와 쿼리·결과 건수·응답 규모. 이어서 분석 절: 도구·채널별 호출 통계와 성과, 0건→방법 전환 회수율, 검증 정정률, 소요·병목, 산출물 규모. LLM 토큰은 정확 집계 불가(클라이언트 영역) — 대리 지표(호출 수·바이트·소요)로 기록하고 그 사실을 명시. 로그+보고서 Ⅴ절+manifest가 감사 추적 3종 세트로 zip에 포함된다.
8. KARDA 온톨로지 산출물(kad/): 발굴 결과를 관계 그래프 입력으로 변환해 zip에 포함 — karda_nodes.csv(id·type[record/agent/unit/place/event]·label·속성)·karda_edges.csv(source·target·relation·relation_ko·basis·confidence)·kad_readme.txt. 신뢰도 필터: 확정(API·원문 판독)·높음만 그래프 수록, 부분 이하는 tentative로 readme에 명기(그래프 오염 방지). 관계마다 근거(basis)를 남겨 연구 재검증 가능하게. 로컬은 make_metadata.py 활용 가능. 품질 게이트 추가: ①보고서 CSS는 템플릿 전체를 그대로 포함(부분 복사 금지 — 영상 절 등 미사용 스타일도 포함해야 절 추가 시 깨지지 않는다) ②핵심 기록 카드는 수집된 실물이 있으면 반드시 이미지 포함(자료 화면 대체 시 그 사실 명기) ③갤러리·절은 placeholder 주석이 아니라 실제 임베드 — 납품 전 잔존 placeholder 검사. 홍보 카드뉴스 제작 시: 텍스트 위주 금지 — 매거진 실제 지면 캡쳐(표지·차례·본문 스프레드·필름스트립·기록 카드·갤러리·검증 낙관)를 카드마다 수록해 산출물 품질을 눈으로 증명한다. 입문 카드뉴스(키워드 정복형) 병행 제작: 처음 접하는 일반 시민 대상 — 후킹 문구(“○○은 처음이지?”·“○○ 완벽 해설”·“3분 정복”) 적극 사용, 카드마다 키워드 1개를 초대형 타이포로 강조하고 한두 줄 쉬운 설명(중학생 눈높이·비유 허용·전문용어 풀어쓰기), 실물 프레임·지면 캡쳐 동반, 마지막 카드는 “정복 완료!”+다음 키워드 참여 유도. ZIP에는 intro/ 폴더로 수록. 메시지형(미장센 문법) 병행 제작: 강연 오프닝·SNS 임팩트용 카드뉴스+슬라이드 — 1장 = 실물 미장센 이미지 1 + 메시지 한 문장, 서사 아크는 충격 오프닝→과거→반전→블랙아웃 테제(텍스트만)→원칙→결과→선언→CTA. 이미지는 실물 기록만(AI 연출 이미지 금지 — 저해상 프레임은 어둡게 깔아 무드로 사용), 장마다 출처 1줄, 슬라이드판은 발표 노트에 미장센·디렉팅 의도 기록. ZIP에는 message/ 폴더로 수록. 시연 영상(선택): 산출물·서비스 데모 GIF/MP4 병행 — 로컬은 demo-video 스킬(실브라우저 구동 녹화), 웹은 페이지 연속 캡쳐 프레임을 GIF로 합성. ZIP에는 video/ 폴더로 수록. 기록 해설형(도큐먼트 애노테이션) 병행 제작: 서울기록원류 해설 지면 문법 — 기록·프레임 위에 점선 영역 박스+외곽 모서리 번호 칩으로 요소를 하나하나 판독(마커가 내용을 가리지 않게 — 점 찍기 금지, 레터박스 검은 띠 제거 후 원본 비율 유지, 색은 지면 팔레트와 조화)(인장·타이틀·타임코드·워터마크·부대 표식 등), 상단에 메타데이터 표(제목·식별번호·제작·소재·시기·권리), 원판/사본 계보 명기. 판독은 화면·원문에서 직접 읽히는 것만(추정 금지, 불명은 표기). 보고서에는 ‘기록을 해설해 드립니다’ 부록 절로, 카드뉴스·슬라이드로도 병행(슬라이드 노트에 판독 해설). ZIP에는 annotate/ 폴더로 수록.

9. 보존 패키지(SIP — 현용기록물화): cross_search(format='manifest')로 수집기록 매니페스트(JSON-LD — provenance·heldBy·영속 식별자)를 생성해 manifest.json으로 ZIP 최상위에 동봉하고, 보고서 <details> 부록(규칙 19)·sources.txt(identifier+재현 호출 1줄)·karda 산출물(node 키 공유)이 전부 이 매니페스트를 참조하게 한다 — 패키지 전체가 하나의 기록 단위(RecordSet)로 등재·재검증 가능. 다른 매개로 재가공·전파될 때도 manifest.json을 함께 옮기는 것이 원칙.

품질 게이트: 수치 정합 · 전 이미지 캡션+출처(기관 정식명·국가·식별자·링크) · 실확인 링크만(확인일 명기) ·
게재윤리 4단계(포로·사망자 존엄) · 협약기관 출처 표기 필수 · manifest.json 동봉(증거성 상속)."""

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
    사용자가 "풀패키지"(또는 full-package)라고 하면 kind="full_package"를 먼저 호출 — 조사→보고서→캐러셀→포스터
    전 산출물 제작 순서를 받아 그대로 수행한다. kind="help"는 매직 키워드 "창기창기 도와줘"(또는 changgi-help) —
    처음 사용자 안내(사용법·예시·FAQ+안내 페이지 링크)를 반환한다.
    kind="exhibit"은 고문서 전시형(AKS 문중·서원 고문서 — 전시 페이지·카드·학습지 규칙+HTML 골격)을 반환한다."""
    if kind == "magazine":
        return MAGAZINE_PACK
    if kind == "help":
        return HELP_GUIDE
    if kind == "citation":
        return CITATION_GUIDE
    if kind == "annotation":
        return ANNOTATION_GUIDE
    if kind == "exhibit":
        return EXHIBIT_GUIDE
    if kind == "full_package":
        return FULL_PACKAGE
    if kind == "canva_prompts":
        return CANVA_PROMPTS
    if kind == "carousel":
        return CAROUSEL_RULES + "\n\n===== CARD DESIGN SYSTEM (1080×1080 — .card를 그대로 복사해 채울 것) =====\n" + CAROUSEL_TEMPLATE
    return REPORT_RULES + "\n\n===== HTML TEMPLATE ({{플레이스홀더}}를 채울 것) =====\n" + REPORT_TEMPLATE


# ══════════ 국내 아카이브 수집기 — 자동 브라우징(서버 사이드 fetch·파싱) v1.9.0 ══════════
import urllib.parse as _up, urllib.request as _ur, html as _html, datetime as _dt, hashlib as _hl

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
                items = fut.result(timeout=12) or []  # 소스별 타임박스 — 최저속 소스가 전체 지연 지배 방지
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
                                     "id": raw.get("id", ""), "url": raw.get("url", ""), "sources": [name],
                                     **({"series": str(raw["series"])[:80]} if raw.get("series") else {})}
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
            ref = str(rec.get("local_id", "") or "")
            out.append({"title": rec.get("title", ""), "date": rec.get("date", ""),
                        "id": ref, **({"series": ref.split("/")[0]} if "/" in ref else {}),
                        "url": rec.get("url", "")})
    return out[:n]

def _c_ia(q, n):
    import urllib.parse
    q = _ko_en(q) or q
    d = http_json("https://archive.org/advancedsearch.php?q=" + urllib.parse.quote(q) +
                  f"&fl[]=identifier&fl[]=title&fl[]=date&fl[]=collection&rows={n}&output=json")
    def _col(x):
        c = x.get("collection")
        return (c[0] if isinstance(c, list) and c else c) or ""
    return [{"title": str(x.get("title", "")), "date": x.get("date", ""), "id": x.get("identifier"),
             **({"series": str(_col(x))} if _col(x) else {}),
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
        akm = re.search(r"ark:/12148/(btv|bpt6k|bd6t)", g("identifier"))
        akn = {"btv": "도판·사진(btv)", "bpt6k": "인쇄본(bpt6k)", "bd6t": "정기간행물(bd6t)"}.get(akm.group(1)) if akm else None
        out.append({"title": g("title"), "date": g("date"), "id": g("identifier"),
                    **({"series": akn} if akn else {}), "url": g("identifier")})
    return out

def _c_europeana(q, n):
    import urllib.parse
    q = _ko_en(q) or q
    key = os.environ.get("EUROPEANA_API_KEY") or "api2demo"
    d = http_json("https://api.europeana.eu/record/v2/search.json?" +
                  urllib.parse.urlencode({"wskey": key, "query": q, "rows": n, "profile": "standard"}))
    return [{"title": (it.get("title") or ["?"])[0], "date": (it.get("year") or [""])[0],
             "id": it.get("id", ""),
             **({"series": (it.get("dataProvider") or [""])[0]} if (it.get("dataProvider") or [""])[0] else {}),
             "url": it.get("guid", "")} for it in (d.get("items") or [])]

def _nara_chain(rec):
    # NARA 계보(v1.80): ancestors → "RG n › 시리즈" 축약 체인 (수집기·전용 도구·판정 공용)
    anc = rec.get("ancestors") or []
    rg = rec.get("recordGroupNumber") or next((a.get("recordGroupNumber") for a in anc if a.get("recordGroupNumber")), "")
    ser = next((a.get("title") for a in anc if re.search(r"series", str(a.get("levelOfDescription") or ""), re.I) and a.get("title")), "")
    return " › ".join(x for x in [f"RG {rg}" if rg else "", ser] if x)[:80]

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
        po = _nara_chain(rec)
        out.append({"title": rec.get("title", ""), "date": "", "id": f"NAID {rec.get('naId')}",
                    **({"series": po} if po else {}),
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
    return [{"title": _xtag(i, "title"), "date": _xtag(i, "prod_year"), "id": (lambda lk: ((re.search(r"rc_rfile_no=(\\d+)", lk).group(1) if re.search(r"rc_rfile_no=(\\d+)", lk) else "")
                               + ("-" + re.search(r"rc_ritem_no=0*(\\d+)", lk).group(1) if re.search(r"rc_ritem_no=0*(\\d+)", lk) else "")) or _xtag(i, "prod_name"))(_xtag(i, "link")),
             **({"series": _xtag(i, "prod_name")} if _xtag(i, "prod_name") else {}),
             "url": _xtag(i, "link")} for i in re.findall(r"<item>(.*?)</item>", xml, re.S)]

def _c_nlk(q, n):
    key = os.environ.get("NLK_API_KEY")
    if not key:
        return []
    # 실측 7.7s(최저속 축) — 6h TTL 캐시(마커 <item> — 정상 결과만)
    xml = _cached_text(f"nlk:{q}:{n}", 6 * 3600,
                       lambda: _http_text("https://www.nl.go.kr/NL/search/openApi/search.do?key=" + _up.quote(key) +
                                          "&apiType=xml&srchTarget=total&kwd=" + _up.quote(q) + f"&pageSize={n}&pageNum=1", 20),
                       "<item>")
    out = []
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
        lk = _xtag(it, "detail_link") or _xtag(it, "org_link")
        if lk.startswith("/"):
            lk = "https://www.nl.go.kr" + lk
        tn = _xtag(it, "type_name")
        out.append({"title": _xtag(it, "title_info") or _xtag(it, "title"), "date": _xtag(it, "pub_year_info"),
                    "id": tn, **({"series": tn} if tn else {}), "url": lk})
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

_KW_API_REFERER = "https://korea-archive-mcp.vercel.app/"  # 발급 토큰이 이 Referer에 바인딩됨(2026-08-19 실측)

def _kw_api_text(url, timeout=20):
    req = _ur.Request(url, headers={"User-Agent": _KW_UA, "Accept": "application/json",
                                    "Referer": _KW_API_REFERER})
    with _ur.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def _kw_api_scan(q, max_pages=None):
    """OpenAPI pbrcList.do — 토큰 인증 JSON 목록(Referer 바인딩 발급·키워드 파라미터 없음·pageSize 상한 100
    → 페이지 순회+로컬 필터). KOREANWAR_API_TOKEN 환경변수 설정 시 활성(미설정 시 None 반환으로 무시)."""
    token = os.environ.get("KOREANWAR_API_TOKEN")
    if not token:
        return None
    import time as _t
    pages = min(int(max_pages or os.environ.get("KOREANWAR_API_PAGES", 3)), 10)
    ql = q.lower(); hits = []; total = 0; checked = 0
    for p in range(1, pages + 1):
        d = json.loads(_kw_api_text(f"{_KW_BASE}/openapi/pbrcList.do?token={_up.quote(token)}&page={p}&pageSize=100"))
        if d.get("resultCode") != "OK":
            raise RuntimeError(f"OpenAPI {d.get('resultCode')}: {d.get('resultMsg', '')}"
                               " — 토큰이 Referer(korea-archive-mcp.vercel.app) 바인딩 발급인지 확인")
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

_JA_MAP = [("조선총독부", "朝鮮総督府"), ("이토 히로부미", "伊藤博文"), ("강제동원", "強制動員"), ("인천상륙", "仁川上陸"),
           ("한국전쟁", "朝鮮戦争"), ("창씨개명", "創氏改名"), ("동양척식", "東洋拓殖"), ("조선은행", "朝鮮銀行"),
           ("재일조선인", "在日朝鮮人"), ("독립운동", "独立運動"), ("임시정부", "臨時政府"), ("3·1운동", "三・一運動"),
           ("삼일운동", "三・一運動"), ("만주국", "満州国"), ("관동군", "関東軍"), ("황민화", "皇民化"), ("학도병", "学徒兵"),
           ("위안소", "慰安所"), ("위안부", "慰安婦"), ("독립군", "独立軍"), ("의열단", "義烈団"), ("광복군", "光復軍"),
           ("연해주", "沿海州"), ("사할린", "樺太"), ("신의주", "新義州"), ("총독부", "総督府"), ("장진호", "長津湖"),
           ("안중근", "安重根"), ("윤봉길", "尹奉吉"), ("이봉창", "李奉昌"), ("여운형", "呂運亨"), ("김구", "金九"),
           ("헌병", "憲兵"), ("특고", "特高"), ("징용", "徴用"), ("의병", "義兵"), ("간도", "間島"), ("만주", "満州"),
           ("경성", "京城"), ("평양", "平壌"), ("부산", "釜山"), ("인천", "仁川"), ("원산", "元山"), ("청진", "清津"),
           ("상해", "上海"), ("중경", "重慶"), ("조선", "朝鮮"), ("한국", "朝鮮")]


def _ko_ja(q):
    """한→일 출력 사전(JACAR 전용) — 일본어 질의가 영어와 다른 결과축을 연다(실측)."""
    out, hit = q, False
    for k, j in _JA_MAP:
        if k in out:
            out = out.replace(k, j); hit = True
    return out if hit else None


def _jacar_meta(code):
    try:
        h = _cached_text("jacarM:" + code, 24 * 3600,
                         lambda: _http_text("https://www.jacar.archives.go.jp/das/meta-en/" + code, 25),
                         "Reference Code")
    except Exception:
        return None
    def g(label):
        m = re.search(label + r"</(?:th|dt)>\s*<(?:td|dd)[^>]*>\s*(?:<[^>]+>\s*)*([^<]{1,160})", h)
        return _clean(m.group(1)) if m else ""
    return {"title": g("Title"), "creator": g("Creator"), "imgs": g("Number of Images"),
            "org": g("Organisation History"), "cls": g("Classification Levels")}


def _jacar_mode(q, span, max_results):
    """JACAR — 검색(한→일 우선)·레퍼런스코드 메타 직행·±span×100 인접 채굴(간격 100 실측)."""
    import time as _t
    try:
        cm = re.match(r"^([A-Z])(\d{11})$", q)
        if cm:
            base = _jacar_meta(q)
            if not base or not base["title"]:
                return f"JACAR '{q}' — 해당 레퍼런스코드 없음."
            out = (f"JACAR [{q}] {base['title']}\n생산: {base['creator'] or '-'} | 이미지 {base['imgs'] or '?'}면 | "
                   f"{base['org']}" + (f" | {base['cls']}" if base["cls"] else "")
                   + f"\n원문 뷰어: https://www.jacar.archives.go.jp/das/meta/{q}")
            sp = min(span, 8)
            n0 = int(cm.group(2)); lines = []
            for k in range(-sp, sp + 1):
                if not k:
                    continue
                code = cm.group(1) + str(n0 + k * 100).zfill(11)
                m3 = _jacar_meta(code)
                lines.append(f"  {code} | {m3['title'][:80]}" if (m3 and m3["title"]) else f"  {code} (없음)")
                _t.sleep(0.25)
            out += f"\n\n[인접 채굴 ±{sp}×100 — 簿冊 내 건 번호 간격 100 실측(±1·±10은 404)]\n" + "\n".join(lines)
            return out + "\n※ 출처 병기: 国立公文書館アジア歴史資料センター(JACAR), Ref. " + q
        eff = _ko_ja(q) or _ko_en(q) or q
        b = _http_text("https://www.jacar.archives.go.jp/aj/search-en?kw=" + _up.quote(eff), 30)
        rows = []
        for blk in b.split('<li class="archive-result-table__body-item"')[1:]:
            c = re.search(r'value="aj\d+/([A-Z]\d{11})"', blk)
            t = re.search(r'id="row-\d+-title"[\s\S]*?<span\s*>([^<]{3,150})', blk)
            if c and t:
                rows.append(f"- [{c.group(1)}] {_clean(t.group(1))[:90]}\n  https://www.jacar.archives.go.jp/das/meta-en/{c.group(1)}")
            if len(rows) >= max_results:
                break
        tag = f" → '{eff}'" if eff != q else ""
        return (f"JACAR '{q}'{tag} — 이 페이지 {len(rows)}건:\n" + ("\n".join(rows) or "(0건 — 일본어 원표기(한자) 병행 권장)")
                + "\n※ 레퍼런스코드(영문1+숫자11)를 query로 주면 메타 직행 + span 인접 채굴(±span×100). "
                  "A=공문서관·B=외무성 외교사료관·C=방위연구소.")
    except Exception as e:
        return f"JACAR 조회 실패({e}) — https://www.jacar.archives.go.jp 직접 검색."


def _c_ndl(q, n):
    """일본 국립국회도서관 서치 — OpenSearch 무키(2026-11-21). 총독부 간행물·관보·도판 축(JACAR 공문서와 상보). 한→일 JA_MAP 우선."""
    ja = _ko_ja(q) or _to_index_lang(q, "en") or q
    req = _ur.Request(f"https://ndlsearch.ndl.go.jp/api/opensearch?any={_up.quote(ja)}&cnt={min(n, 10)}",
                      headers={"User-Agent": "KoreaArchiveMCP/1.0 (https://github.com/changgi/korea-archive-mcp)"})
    with _ur.urlopen(req, timeout=25) as r:
        b = r.read().decode("utf-8", "replace")
    if "<error>" in b and "429" in b:
        raise RuntimeError("NDL 동시접속 제한(429) — 잠시 후 재시도")
    out = []
    for item in b.split("<item>")[1:]:
        g = lambda t: ((re.search(f"<{t}[^>]*>([^<]+)", item) or [None, ""])[1] or "").strip()
        title, link = g("title"), g("link")
        if not title or not link:
            continue
        cat_arr = re.findall(r"<category>([^<]+)", item)  # 자료형·매체(紙/デジタル)
        cats = "·".join(cat_arr)
        author = g("author")
        out.append({"title": (title + (f" [{cats}]" if cats else "") + (f" — {author}" if author else ""))[:120],
                    "date": g("dc:date"), "id": "",
                    **({"series": cat_arr[0]} if cat_arr else {}), "url": link})
        if len(out) >= n:
            break
    return out


def _c_un(q, n):
    """UN 디지털도서관 — Invenio of=xm(MARCXML) 무키 실측(2026-11-21). 안보리 결의·공식문서. UN Archives(AtoM)와 별개."""
    en = _to_index_lang(q, "en") or q
    # _http_text의 X-Requested-With 헤더에 Invenio가 빈 응답(실측) — 일반 헤더로 직접 요청
    req = _ur.Request(f"https://digitallibrary.un.org/search?p={_up.quote(en)}&of=xm&rg={min(n, 10)}",
                      headers={"User-Agent": "KoreaArchiveMCP/1.0 (https://github.com/changgi/korea-archive-mcp)"})
    with _ur.urlopen(req, timeout=25) as r:
        b = r.read().decode("utf-8", "replace")
    def sf(seg, tag, code):
        m = re.search(r'<datafield tag="' + tag + r'"[^>]*>([\s\S]*?)</datafield>', seg)
        if not m:
            return ""
        m2 = re.search(r'<subfield code="' + code + r'">([^<]+)', m.group(1))
        return m2.group(1) if m2 else ""
    out = []
    for seg in re.split(r"<record>", b)[1:]:
        rm = re.search(r'<controlfield tag="001">(\d+)', seg)
        if not rm:
            continue
        sym = sf(seg, "191", "a")
        title = _clean(sf(seg, "245", "a") + " " + sf(seg, "245", "b")).rstrip(" /:")
        out.append({"title": (f"[{sym}] " if sym else "") + title[:110], "date": sf(seg, "269", "a") or sf(seg, "260", "c"),
                    "id": sym or rm.group(1),
                    **({"series": "/".join(sym.split("/")[:2])} if sym and "/" in sym else {}),
                    "url": "https://digitallibrary.un.org/record/" + rm.group(1)})
        if len(out) >= n:
            break
    return out


def _c_heritage(q, n):
    """국가유산포털(국가유산청) OpenAPI — 무키 XML(작업망 차단·icn1 도달 확인). 국보·보물·사적 축."""
    b = _http_text("https://www.khs.go.kr/cha/SearchKindOpenapiList.do?ccbaMnm1=" + _up.quote(q)
                   + f"&pageUnit={min(n, 15)}", 25)
    out = []
    for it in b.split("<item>")[1:]:
        g = lambda t: ((re.search(f"<{t}>(?:<!\\[CDATA\\[)?([\\s\\S]*?)(?:\\]\\]>)?</{t}>", it) or [None, ""])[1] or "").strip()  # CDATA 대응
        name = g("ccbaMnm1")
        if not name:
            continue
        cpno = g("ccbaCpno")
        raw_id = (f"{g('ccbaKdcd')}-{g('ccbaAsno')}-{g('ccbaCtcd')}"
                  if g("ccbaKdcd") and g("ccbaAsno") and g("ccbaCtcd") else cpno)  # 상세 API 원값 보존
        title = name + (f"({g('ccbaMnm2')})" if g("ccbaMnm2") else "") + (f" [{g('ccmaName')}]" if g("ccmaName") else "") \
                + (f" — {g('ccbaCtcdNm')} {g('ccsiName')}" if g("ccbaCtcdNm") else "")
        out.append({"title": title[:110], "date": "", "id": raw_id,
                    **({"series": g("ccmaName")} if g("ccmaName") else {}),
                    "url": (f"https://www.heritage.go.kr/heri/cul/culSelectDetail.do?ccbaCpno={cpno}" if cpno else "https://www.heritage.go.kr")})
        if len(out) >= n:
            break
    return out


def _c_indy(q, n):
    """국가기록원 독립운동판결문 테마관 — GET 실측(2026-11-21). 판결기관·날짜·주문+상세 딥링크(gonghun 수형기록의 원문 창구)."""
    b = _http_text("https://theme.archives.go.kr/next/indy/listkeywordSrch.do?keyword=" + _up.quote(q)
                   + f"&listSize={min(n, 20)}", 25)
    out = []
    for m in re.finditer(r'<a href="(/next/indy/viewIndyDetail\.do[^"]+)">\s*<span>\s*([^<]+?)\s*</span>[\s\S]{0,400}?<td class="left">([^<]*)</td>\s*<td>(\d{8})</td>\s*<td class="left">([^<]*)</td>', b):
        out.append({"title": f"[판결문] {_clean(m.group(2))} — {_clean(m.group(3))} · {_clean(m.group(5))[:40]}"[:115],
                    **({"series": _clean(m.group(3))} if _clean(m.group(3)) else {}),
                    "date": m.group(4), "id": "",
                    "url": "https://theme.archives.go.kr" + m.group(1).replace("&amp;", "&")})
        if len(out) >= n:
            break
    return out


def _c_much(q, n):
    """대한민국역사박물관 근현대사아카이브 — POST 검색 역공학(2026-11-21). 소장품·포스터·간행물(근현대 실물)."""
    req = _ur.Request("https://archive.much.go.kr/search.do", data=_up.urlencode({"searchQuery": q}).encode(),
                      headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded"})
    with _ur.urlopen(req, timeout=25) as r:
        b = r.read().decode("utf-8", "replace")
    out = []
    for m in re.finditer(r'<a href="(/archive/[\w/]+view\.do\?idnbr=[^"]+)">[\s\S]{0,420}?<strong>([\s\S]*?)</strong>[\s\S]{0,320}?자료연대\s*:\s*([^<]{1,20})', b):
        idm = re.search(r"idnbr=([\w\-]+)", m.group(1))
        seg_cat = (m.group(1).split("/") + ["", "", ""])[2]
        out.append({"title": _clean(m.group(2))[:110], "date": _clean(m.group(3)), "id": idm.group(1) if idm else "",
                    **({"series": seg_cat} if seg_cat else {}),
                    "url": "https://archive.much.go.kr" + m.group(1)})
        if len(out) >= n:
            break
    if len(out) < n:
        for c in re.finditer(r'<strong>([가-힣 ]{2,12})</strong><span>총 "([\d,]+)건"', b):  # 카테고리 집계 보충
            if c.group(2) == "0":
                continue
            out.append({"title": f"역사박물관 {_clean(c.group(1))} {c.group(2)}건 — 사이트 검색(POST)으로 열람",
                        "date": "", "id": "", "url": "https://archive.much.go.kr/index.do"})
            if len(out) >= n:
                break
    return out


def _c_oldnews(q, n):
    """대한민국신문아카이브(국립중앙도서관) — POST JSON 역공학(2026-11-21). 1883~1960 신문 기사 전문."""
    req = _ur.Request("https://nl.go.kr/newspaper/search_newspaper.do",
                      data=json.dumps({"search_keyword": q, "page_size": min(n, 10), "page_no": 1}).encode(),
                      headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json",
                               "Referer": "https://nl.go.kr/newspaper/keyword_search.do"})
    with _ur.urlopen(req, timeout=25) as r:
        d = json.loads(r.read().decode("utf-8", "replace"))
    first = lambda v: (v[0] if isinstance(v, list) and v else v) or ""
    out = []
    for h in (d.get("hits") or [])[:n]:
        uri = first(h.get("uri"))
        out.append({"title": f"{first(h.get('label'))} — {first(h.get('newspaperKorName'))}"[:110],
                    "date": str(h.get("issued_date") or ""), "id": uri,
                    **({"series": first(h.get("newspaperKorName"))} if first(h.get("newspaperKorName")) else {}),
                    "url": (f"https://nl.go.kr/newspaper/detail.do?content_id={uri}" if uri else "https://nl.go.kr/newspaper/")})
    return out


def _c_commons(q, n):
    """위키미디어 공용 — 키 불요 검색 API(PD 사진·NARA/해군 재수집본 다수 — 원 소장처 역추적 창구). 공유 IP 429 시 채널 실패."""
    en = _to_index_lang(q, "en") or q
    # v1.81: list=search → generator=search + prop=categories 1콜 전환 — 소속 카테고리(큐레이션 계층)를 목록 레벨에서 확보
    d = http_json("https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&format=json"
                  f"&gsrlimit={min(n, 10)}&gsrsearch=" + _up.quote(en) + "&prop=categories&clshow=!hidden&cllimit=3",
                  headers={"User-Agent": "KoreaArchiveMCP/1.0 (https://github.com/changgi/korea-archive-mcp; archival discovery)"})
    pages = sorted(((d.get("query", {}) or {}).get("pages") or {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for it in pages:
        t = str(it.get("title", ""))
        cat = str(((it.get("categories") or [{}])[0] or {}).get("title", "")).removeprefix("Category:")
        out.append({"title": t.removeprefix("File:")[:110], "date": "", "id": "",
                    **({"series": cat[:80]} if cat else {}),
                    "url": "https://commons.wikimedia.org/wiki/" + _up.quote(t.replace(" ", "_"))})
    return out


def _c_nlna(q, n):
    """네덜란드 국립문서보관소 — 공개 JSON API 실측(2026-11-20, Playwright 역추적). 주한 대사관·파견부대 문서군."""
    # commons는 한국어 네이티브 검색 가능 — TOPICS 미등재어(인명 등)가 'Korea' 단독으로 뭉개지면 원질의 유지(v1.62)
    t = _ko_en(q)
    en = q if (not t or t == 'Korea') else t
    d = json.loads(_http_text(f"https://zvt.nationaalarchief.nl/api/search/eads?page=1&rows={min(n, 10)}"
                              f"&q={_up.quote(en)}&sortBy=_score", 25))
    # v1.81: 토이강(toegang) 번호 첫 두 세그먼트 = 형성기관 클러스터(2.05 외무부 등 — 2.05.202 'Zuid-Korea 대사관' 실측)
    NLNA_CL = {"2.04": "내무부(Binnenlandse Zaken)", "2.05": "외무부(Buitenlandse Zaken)", "2.09": "법무부(Justitie)",
               "2.10": "식민성(Koloniën)", "2.12": "해군(Marine)", "2.13": "국방부(Defensie)",
               "2.19": "민간단체 문서", "2.21": "개인·가문 문서", "2.24": "사진·영상 컬렉션"}
    out = []
    for r in (d.get("results") or [])[:n]:
        cl = ".".join(str(r.get("id", "")).split(".")[:2])
        ser = f"{cl} {NLNA_CL[cl]}" if cl in NLNA_CL else (f"토이강 {cl}" if "." in cl else "")
        out.append({"title": _clean(str(r.get("title", "")))[:95] + (" [문서군]" if r.get("type") == "ARCHIVE" else ""),
                    "date": str(r.get("period", "")), "id": str(r.get("id", "")),
                    **({"series": ser} if ser else {}),
                    "url": "https://www.nationaalarchief.nl/onderzoeken/archief/" + _up.quote(str(r.get("id", "")))})
    return out


def _c_nzarch(q, n):
    """Archives NZ Collections(Te Rua Mahara) — 연합검색 공개 API(SSE 프레임 JSON, 무키 평문 GET 실측).
    v1.58: GH 러너 역공학 10차로 완결. 0건 응답엔 hits 키 없음(totalHits로 판별). 간헐 Incapsula → 정적 인덱스 폴백."""
    en = _ko_en(q) or q

    def _row(rid, title, acc, date):
        return {"title": title[:92] + (f" [{acc}]" if acc else ""), "date": date, "id": rid,
                "url": "https://collections.archives.govt.nz/web/arena/search#/entity/aims-archive/" + rid}
    try:
        b = _http_text("https://collections.archives.govt.nz/federated-search/customers/aims/search?size=" + str(min(n, 20))
                       + "&facetSize=0&start=0&isFuzzy=true&sourceId=aims-archive&q=" + _up.quote(en), 25)
        line = next((l for l in b.split("\n") if l.startswith("data:") and '"totalHits"' in l), None)
        if not line:
            raise RuntimeError("no-stream")
        j = json.loads(line[5:])
        out = []
        for h in (j.get("hits") or []):
            e = h.get("entity") or {}

            def cf(k):
                try:
                    return str(e["custom"][k]["value"][0]["value"])
                except Exception:
                    return ""
            row = _row(str(e.get("id") or ""), _clean(str(e.get("name") or "(무제)")), cf("accessStatus"), cf("resultDate"))
            if cf("series"):
                row["series"] = cf("series")
            out.append(row)
        return out
    except Exception:  # 간헐 Incapsula — GH 주간 수확 정적 인덱스 폴백(자체 도메인)
        ix = _cached_text("nzIdx", 6 * 3600, lambda: _http_text("https://korea-archive-mcp.vercel.app/nz-index.json", 20), '"records"')
        j = json.loads(ix)
        ql = en.lower()
        return [_row(str(r.get("id") or ""), str(r.get("title") or "")[:86] + " ·주간인덱스", str(r.get("access") or ""), str(r.get("date") or ""))
                for r in (j.get("records") or []) if ql in str(r.get("title") or "").lower() or str(r.get("id") or "").lower() == ql][:n]


def _nzarch_mode(query: str) -> str:
    """Archives NZ 상세 판독 — R번호 투입 시 entity 전체 메타 + 메타 지문. Node nedb_search mode='nzarch' 패리티."""
    q = query.strip()
    m = re.match(r"^[Rr](\d{5,9})$", q) or re.match(r"^(\d{5,9})$", q)
    if not m:
        return "nzarch 판독: R번호(예 R17717658)를 입력하십시오. 번호는 cross_search(sources='nzarch')가 제공."
    rn = "R" + m.group(1)
    try:
        b = _http_text("https://collections.archives.govt.nz/federated-search/customers/aims/search"
                       "?size=3&facetSize=0&start=0&isFuzzy=false&sourceId=aims-archive&q=" + rn, 25)
        line = next((l for l in b.split("\n") if l.startswith("data:") and '"totalHits"' in l), None)
        if not line:  # 간헐 Incapsula — 주간 수확 인덱스로 축약 판독 폴백
            try:
                ix = _cached_text("nzIdx", 6 * 3600, lambda: _http_text("https://korea-archive-mcp.vercel.app/nz-index.json", 20), '"records"')
                r = next((x for x in (json.loads(ix).get("records") or []) if str(x.get("id")) == rn), None)
                if r:
                    meta = " · ".join(x for x in (
                        f"연대 {r.get('date')}" if r.get("date") else "",
                        f"시리즈 {r.get('series')}" if r.get("series") else "",
                        f"접근 상태 {r.get('access')}" if r.get("access") else "") if x)
                    return (f"Archives NZ 판독(축약 — ·주간인덱스, 라이브 간헐 차단 중) — {rn}\n제목: {r.get('title')}\n{meta}\n"
                            f"레코드: https://collections.archives.govt.nz/web/arena/search#/entity/aims-archive/{rn}\n"
                            "※ 전체 메타(생산 기관·열람 방법·메타 지문)는 라이브 재시도 시 제공. 출처: Archives New Zealand.")
            except Exception:
                pass
            return (f"[{rn}] 간헐 차단 — 잠시 후 재시도 또는 브라우저: "
                    f"https://collections.archives.govt.nz/web/arena/search#/entity/aims-archive/{rn}")
        j = json.loads(line[5:])
        hits = j.get("hits") or []
        h = next((x for x in hits if (x.get("entity") or {}).get("id") == rn), hits[0] if hits else None)
        if not h:
            return f"[{rn}] 레코드 미발견 — 번호를 확인하십시오."
        e = h.get("entity") or {}

        def cf(k):
            try:
                return " | ".join(str(v["value"]) for v in e["custom"][k]["value"])
            except Exception:
                return ""
        mfp = _hl.sha256((str(e.get("name") or "") + "\n" + json.dumps(e.get("custom") or {}, ensure_ascii=False, sort_keys=True)).encode("utf-8")).hexdigest()[:16]
        meta = " · ".join(x for x in (
            f"기술계층 {e.get('descriptionLevel')}" if e.get("descriptionLevel") else "",
            f"형태 {cf('itemLevel')}" if cf("itemLevel") else "",
            f"연대 {cf('resultDate')}" if cf("resultDate") else "",
            f"소장 {e.get('holdingsLocation')}" if e.get("holdingsLocation") else "") if x)
        return (f"Archives NZ(Te Rua Mahara) 판독 — {e.get('id') or rn}\n제목: {e.get('name') or '(무제)'}\n{meta}\n"
                + (f"시리즈: {cf('series')}" + (f" (Series {e.get('parentId')})" if e.get("parentId") else "") + "\n" if cf("series") else "")
                + (f"생산 기관: {re.sub(r'^Agency:\\s*', '', cf('resultField4'))}\n" if cf("resultField4") else "")
                + (f"접근 상태: {cf('accessStatus')} — 발굴 우선: 권리는 표시 대상\n" if cf("accessStatus") else "")
                + (f"열람 방법: {' · '.join(e.get('orderType') or [])}\n" if e.get("orderType") else "")
                + f"메타 지문(sha256-16): {mfp} — 판독 시점 기술(記述) 전체 기준. 재판독 지문 불일치=기술 개정 발생.\n"
                + f"레코드: https://collections.archives.govt.nz/web/arena/search#/entity/aims-archive/{e.get('id') or rn}\n"
                + "※ 출처: Archives New Zealand Te Rua Mahara o te Kāwanatanga — 게재 시 출처 표기. May be restricted는 기관 열람 신청 대상.")
    except Exception as err:
        return f"Archives NZ 오류({str(err)[:60]}) — 잠시 후 재시도."


def _c_dnz(q, n):
    """DigitalNZ 집계 API(무키 JSON) — v1.57 합류: Papers Past(직접 차단 — 본 API로 우회 복구)·터닝불도서관·Te Papa 등 NZ 30+기관."""
    en = _ko_en(q) or q
    d = json.loads(_http_text("https://api.digitalnz.org/v3/records.json?per_page=" + str(min(n, 20))
                              + "&fields=id,title,display_date,landing_url,content_partner,primary_collection"
                              + "&text=" + _up.quote(en), 25))
    out = []
    for r in ((d.get("search") or {}).get("results") or []):
        cp = (r.get("content_partner") or [""])[0]
        pc = (r.get("primary_collection") or [""])[0]
        out.append({"title": (_clean(str(r.get("title") or "(무제)")) + " — " + cp + ("·" + pc if pc else ""))[:115],
                    "date": str(r.get("display_date") or ""), "id": str(r.get("id") or ""),
                    **({"series": cp + (" › " + pc if pc else "")} if cp else {}),
                    "url": str(r.get("landing_url") or "")})
    return out


def _c_awm(q, n):
    """호주 전쟁기념관(AWM) — 검색 모자이크(SSR C-id) → 상세 순차로 제목·수장번호 (2026-11-20 실측)."""
    en = _ko_en(q) or q
    b = _http_text("https://www.awm.gov.au/advanced-search?query=" + _up.quote(en), 28)
    ids = []
    for m in re.finditer(r'href="/collection/(C\d+)"', b):
        if m.group(1) not in ids:
            ids.append(m.group(1))
        if len(ids) >= min(n, 5):
            break
    out = []
    for cid in ids:
        try:
            d = _cached_text("awm:" + cid, 24 * 3600, lambda cid=cid: _http_text("https://www.awm.gov.au/collection/" + cid, 25), "<h1")
            h1 = re.search(r"<h1[^>]*>\s*(?:<[^>]+>\s*)*([^<]{3,120})", d)
            acc = re.search(r"(?:Accession Number|ID number)[^A-Z0-9]{0,40}([A-Z0-9/.\-]{3,20})", d)
            pd = bool(re.search(r"Copyright expired - public domain|publicdomain/mark", d))
            conf = re.search(r"Conflict[^<]*</[a-z0-9]+>\s*<[^>]*>\s*(?:<[^>]+>\s*)*([^<]{4,40})", d)
            ot = re.search(r"Object type</th>\s*<td>\s*([^<]{2,40})", d)  # v1.81: 소장품 유형(Photograph·Film·Firearm 등 — C285584 실측)
            out.append({"title": (_clean(h1.group(1)) if h1 else cid) + (" · 권리:PD(저작권 만료)" if pd else ""),
                        "date": _clean(conf.group(1)) if conf else "",
                        "id": acc.group(1) if acc else cid,
                        **({"series": _clean(ot.group(1))} if ot else {}),
                        "url": "https://www.awm.gov.au/collection/" + cid})
        except Exception:
            continue
    return out


def _c_jsg(q, n):
    """AKS 장서각 — ★검색 파라미터는 q=query|<어> (플레인 q는 무시되고 전체 열람 반환 —
    Playwright 실브라우저 재역공학으로 확정, 2026-11-20)."""
    b = _http_text("https://jsg.aks.ac.kr/search/group?q=" + _up.quote("query|" + q), 28)
    out, seen = [], set()
    for m in re.finditer(r'href="/dir/view\?dataId=([^"]+)"[^>]*>([\s\S]*?)</a>', b):
        t = _clean(m.group(2))
        did = m.group(1)
        if not t or did in seen or re.match(r"^JSG_K1-[1-5]$", did):
            continue
        seen.add(did)
        jid = did[4:] if did.startswith("JSG_") else ""
        sb = {"K1": "經部(K1)", "K2": "史部(K2)", "K3": "子部(K3)", "K4": "集部(K4)"}.get(jid.split("-")[0])
        out.append({"title": t[:95], "date": "", "id": jid, **({"series": sb} if sb else {}),
                    "url": "https://jsg.aks.ac.kr/dir/view?dataId=" + _up.quote(did)})
        if len(out) >= n:
            break
    return out


def _c_kyudb(q, n):
    """서울대 규장각 — 기존 kyujanggak 코어(joseon_tools) 재사용.
    실측 ~10s(12s 타임박스 근접) → 6h TTL 캐시(마커 奎 — 결과 있을 때만 캐시)."""
    if _jt is None:
        return []
    raw = _cached_text("kyudb:" + q, 6 * 3600,
                       lambda: json.dumps(_jt.kyujanggak_search(q, area="both"), ensure_ascii=False), "奎")
    try:
        r = json.loads(raw)
    except Exception:
        return []
    sec = (r.get("sections") or {}) if isinstance(r, dict) else {}
    lst = sec.get("목록")
    if not isinstance(lst, list):
        return []
    def _kser(t):
        km = re.search(r"(奎|古|想白|一簑)\s*\d", str(t))
        return {"奎": "규장각도서(奎)", "古": "고도서(古)", "想白": "상백문고", "一簑": "일사문고"}.get(km.group(1)) if km else None
    return [{"title": str(t), "date": "", "id": "", **({"series": _kser(t)} if _kser(t) else {}),
             "url": "https://kyudb.snu.ac.kr"} for t in lst[:n]]


_I815_DETAIL = {  # 구분(gubun)→상세 GET 경로 — 목록 contentsFrm(method=get) 역공학(2026-11-20 실측)
    "2": ("contents/mijooAcademy/mijooAcademyDetailList.do", "mngNo"),
    "3": ("contents/proGovernment/proGovernmentDetailList.do", "mngNo"),
    "4": ("contents/independenceFighter/detail.do", "independenceFighterId"),
    "7": ("contents/missionary/detail.do", "missionaryId"),
    "8": ("contents/newsPaper/detail.do", "newsPaperId"),
    "9": ("contents/medicalData/MedicalDataDetailList.do", "mngNo"),
    "9999": ("contents/microFilm/detail.do", "adminId")}


def _c_i815(q, n):
    """독립기념관 — v1.32 목록 실체화: 최대 카테고리의 실제 자료 제목+GET 딥링크, 나머지는 집계 신호."""
    base = "https://search.i815.or.kr"
    b = _http_text(base + "/main/totalSearch.do?searchWord=" + _up.quote(q) + "&searchMenu=all", 28)
    cats = []
    for m in re.finditer(r'href="(/main/moreContentsSearchList\.do[^"]*)"[^>]*>([^<]+?)\s*([\d,]+)\s*건<', b):
        if m.group(3) == "0":
            continue
        cats.append({"u": m.group(1).replace("&amp;", "&"), "name": _clean(m.group(2)),
                     "cnt": int(m.group(3).replace(",", "")), "disp": m.group(3)})
    out = []
    if cats:
        top = max(cats, key=lambda c: c["cnt"])
        try:
            lb = _http_text(base + _up.quote(top["u"], safe="/?&="), 28)  # 한글·공백 인코딩(urllib는 비ASCII URL 거부)
            for m in re.finditer(r'data-mngno="([^"]+)"[^>]*data-gubun="(\d+)"[^>]*>([\s\S]*?)</strong>', lb):
                d = _I815_DETAIL.get(m.group(2))
                url = (f"{base}/{d[0]}?{d[1]}={_up.quote(m.group(1))}&sortNo={m.group(2)}" if d else base + top["u"])
                out.append({"title": f"[{top['name']}] {_clean(m.group(3))}"[:110], "date": "", "id": m.group(1), "series": top["name"], "url": url})
                if len(out) >= max(2, n - 2):
                    break
        except Exception:
            pass  # 목록 실패 — 집계 신호로 폴백
    for c in cats:
        if len(out) >= n:
            break
        out.append({"title": f"독립기념관 {c['name']} {c['disp']}건", "date": "", "id": "", "url": base + c["u"]})
    return out


def _c_gonghun(q, n):
    """공훈전자사료관(국가보훈부) — 독립유공자 공훈록. 2026-11-20 복구 실측(GET 검색·상세 딥링크).
    인명 검색 채널(nameKo) — 일반 키워드는 0건이 정상. 성명은 base64(utf8_decode JS), mngNo로 상세 GET 직행."""
    import base64 as _b64
    b = _http_text("https://e-gonghun.mpva.go.kr/user/ContribuReportList.do?goTocode=20001"
                   "&nameKd=NAME_KOR&nameKo=" + _up.quote(q) + "&pageIndex=1&pageUnit=" + str(min(max(n, 1), 10)), 28)
    out = []
    for seg in b.split("fnContribuReportView(")[1:]:
        mn = re.match(r"^'(\d+)'", seg)
        if not mn:
            continue
        bm = re.search(r"utf8_decode\('([A-Za-z0-9+/=]+)'", seg)
        try:
            name = _b64.b64decode(bm.group(1)).decode("utf-8") if bm else ""
        except Exception:
            name = ""
        tds = [_clean(x) for x in re.findall(r"<td[^>]*>\s*([^<]{1,60}?)\s*<", seg)]
        tds = [t for t in tds if t][:6]  # 한자명·생몰년·운동계열·포상년도·포상훈격·생존여부
        def g(i):
            return tds[i] if len(tds) > i else ""
        title = re.sub(r"\s+", " ", f"{name}{f'({g(0)})' if g(0) else ''} {g(1)} · {g(2)} · {g(3)} {g(4)}").strip()
        out.append({"title": title, "date": g(3), "id": mn.group(1),
                    **({"series": g(2)} if g(2) else {}),
                    "url": f"https://e-gonghun.mpva.go.kr/user/ContribuReportDetail.do?goTocode=20001&mngNo={mn.group(1)}&pageTitle=Report"})
        if len(out) >= n:
            break
    return out


def _heritage_mode(query: str, max_results: int) -> str:
    """국가유산 심층 — 키워드 목록 / ccbaCpno 상세(해설·시대·소유/관리). cpno=구분1+종목2+시도2+지정8. Node 패리티."""
    q = query.strip()
    try:
        rid = re.match(r"^(\d{2})-([0-9A-Za-z]+)-(\d{2})$", q)  # 목록이 보존한 원값
        if rid:
            kdcd, asno, ctcd = rid.group(1), rid.group(2), rid.group(3)
            b = _cached_text(f"heriD:{kdcd}|{asno}|{ctcd}", 24 * 3600,
                             lambda: _http_text(f"https://www.khs.go.kr/cha/SearchKindOpenapiDt.do?ccbaKdcd={kdcd}&ccbaAsno={asno}&ccbaCtcd={ctcd}", 25),
                             "<ccbaMnm1>")
            g = lambda t: _clean(((re.search(f"<{t}>(?:<!\\[CDATA\\[)?([\\s\\S]*?)(?:\\]\\]>)?</{t}>", b) or [None, ""])[1] or ""))
            name = g("ccbaMnm1")
            if not name:
                return f"[{q}] 상세 미매칭 — 포털에서 열람하십시오(목록의 딥링크)."
            content = g("content")
            hfp = _hl.sha256(content.encode("utf-8")).hexdigest()[:16] if content else ""  # 판독 시점 해설 지문
            if len(content) > 3500:
                content = content[:3500] + f" …(총 {len(content)}자 — 전문은 포털)"
            meta = " · ".join(x for x in (f"소유 {g('ccbaPoss')}" if g("ccbaPoss") else "",
                                          f"관리 {g('ccbaAdmin')}" if g("ccbaAdmin") else "",
                                          f"시대 {g('ccceName')}" if g("ccceName") else "",
                                          f"소재 {g('ccbaLcad')[:60]}" if g("ccbaLcad") else "") if x)
            return (f"국가유산 판독 — {name}" + (f"({g('ccbaMnm2')})" if g("ccbaMnm2") else "") + f" [{g('ccmaName')}]"
                    + f"\n{meta}\n" + (f"【해설】\n{content}\n" if content else "")
                    + (f"본문 지문(sha256-16): {hfp} — 판독 시점 해설 전문 기준. 재판독 지문 불일치=원문 개정 발생.\n" if hfp else "")
                    + "※ 출처: 국가유산청 국가유산포털 — 게재 시 출처 표기. 사진 이용은 공공누리 유형 확인.")
        hm = re.search(r"ccbaCpno=(\d{13})", q) or re.match(r"^(\d{13})$", q)
        if hm:
            cpno = hm.group(1)
            kdcd, ctcd, asno8 = cpno[1:3], cpno[3:5], cpno[5:]
            # asno 포맷이 종목별로 달라 후보 순차 시도(8자리·4자리·무패딩)
            b = ""
            # 기관 원값 asno는 13자리('00'+지정4+'0000000') — 실측 역산 후보 최우선
            for asno in dict.fromkeys(['00' + asno8[:4] + '0000000', asno8, asno8[:4]]):
                b = _cached_text(f"heriD:{kdcd}|{asno}|{ctcd}", 24 * 3600,
                                 lambda a2=asno: _http_text(f"https://www.khs.go.kr/cha/SearchKindOpenapiDt.do?ccbaKdcd={kdcd}&ccbaAsno={a2}&ccbaCtcd={ctcd}", 25),
                                 "<ccbaMnm1>")
                if re.search(r"<ccbaMnm1>(?:<!\[CDATA\[)?[^<]", b):
                    break
            g = lambda t: _clean(((re.search(f"<{t}>(?:<!\\[CDATA\\[)?([\\s\\S]*?)(?:\\]\\]>)?</{t}>", b) or [None, ""])[1] or ""))
            name = g("ccbaMnm1")
            if not name:
                return (f"[{cpno}] 상세 API 미매칭(기관 식별 편차 — 2026-11-21 명세 기록). "
                        f"해설은 포털에서: https://www.heritage.go.kr/heri/cul/culSelectDetail.do?ccbaCpno={cpno}")
            content = g("content")
            hfp = _hl.sha256(content.encode("utf-8")).hexdigest()[:16] if content else ""  # 판독 시점 해설 지문
            if len(content) > 3500:
                content = content[:3500] + f" …(총 {len(content)}자 — 전문은 포털)"
            meta = " · ".join(x for x in (f"소유 {g('ccbaPoss')}" if g("ccbaPoss") else "",
                                          f"관리 {g('ccbaAdmin')}" if g("ccbaAdmin") else "",
                                          f"시대 {g('ccceName')}" if g("ccceName") else "",
                                          f"소재 {g('ccbaLcad')[:60]}" if g("ccbaLcad") else "") if x)
            return (f"국가유산 판독 — {name}"
                    + (f"({g('ccbaMnm2')})" if g("ccbaMnm2") else "") + f" [{g('ccmaName')}]"
                    + f"\n{meta}\n"
                    + (f"【해설】\n{content}\n" if content else "")
                    + (f"본문 지문(sha256-16): {hfp} — 판독 시점 해설 전문 기준. 재판독 지문 불일치=원문 개정 발생.\n" if hfp else "")
                    + f"포털 상세: https://www.heritage.go.kr/heri/cul/culSelectDetail.do?ccbaCpno={cpno}\n"
                    + "※ 출처: 국가유산청 국가유산포털 — 게재 시 출처 표기(해설문 인용 시 포털 명기). 사진 이용은 공공누리 유형 확인.")
        items = _c_heritage(q, min(max_results, 15))
        if not items:
            return f"국가유산 '{q}' — 0건. 유산 명칭(전각·사적명 등)으로 재시도하십시오."
        return (f"국가유산 '{q}' — {len(items)}건:\n"
                + "\n".join(f"- {it['title']}" + (f" [{it['id']}]" if it.get("id") else "") + f"\n  {it['url']}" for it in items)
                + "\n※ 대괄호의 복합 id(예 11-0002230000000-11)를 mode=heritage query로 재투입 → 해설·시대·소유/관리 판독.")
    except Exception as e:
        return f"국가유산 오류({str(e)[:60]}) — 잠시 후 재시도 또는 브라우저: https://www.heritage.go.kr"


def _indy_mode(query: str, max_results: int) -> str:
    """독립운동판결문 심층 — 이름 목록 / 상세 URL 판독(죄명·주문·사건개요·원문 뷰어). Node 패리티."""
    q = query.strip()
    try:
        if re.search(r"viewIndyDetail\.do", q) and re.match(r"^https?://theme\.archives\.go\.kr/", q):
            evnt = (re.search(r"FK_ARCHIVE_EVNT_ID=(\d+)", q) or [None, ""])[1] or ""
            b = _cached_text("indyD:" + (evnt or q[-40:]), 24 * 3600, lambda: _http_text(q, 25), "판결기관")
            flat = _clean(b)
            pick = lambda rx: ((re.search(rx, flat) or [None, ""])[1] or "").strip()
            name = pick(r"이름/별명\s*(.{2,40}?)\s*당시나이")
            age = pick(r"당시나이\s*(.{1,20}?)\s*본적")
            addr = pick(r"본적/주소\s*(.{2,60}?)\s*판결기관")
            organ = pick(r"판결기관\s*(\S{2,20})")
            crime = pick(r"죄명\s*(.{2,50}?)\s*생산년도")
            sent = pick(r"주문\s*(.{2,100}?)\s*관리번호")
            vdate = pick(r"판결날짜\s*(\d{8})")
            kase = pick(r"사건개요\s*([\s\S]{5,900}?)\s*판결문 원문보기")
            if not name and not kase:
                return "판결문 상세 파싱 실패 — viewIndyDetail URL을 확인하거나 mode=indy에 이름을 넣으십시오."
            meta = " · ".join(x for x in (f"본적/주소 {addr}" if addr else "", f"판결기관 {organ}" if organ else "",
                                          f"판결 {vdate}" if vdate else "") if x)
            return (f"독립운동판결문 판독 — {name}{f' (당시 {age})' if age else ''}\n{meta}\n"
                    + (f"죄명: {crime}\n" if crime else "") + (f"주문: {sent}\n" if sent else "")
                    + (f"【사건개요】\n{kase}\n" if kase else "")
                    + (f"본문 지문(sha256-16): {_hl.sha256((kase + chr(10) + (sent or '')).encode('utf-8')).hexdigest()[:16]} — 판독 시점 사건개요·주문 기준. 재판독 지문 불일치=원문 개정 발생.\n" if kase else "")
                    + (f"판결문 원문 뷰어: https://theme.archives.go.kr/viewer/common/archWebViewer.do?archiveEventId={evnt}\n" if evnt else "")
                    + "※ 출처: 국가기록원 독립운동판결문 — 게재 시 출처 표기. 수형 사실의 존엄 고려(게재윤리). gonghun 수형기록과 교차검증 권장.")
        items = _c_indy(q, min(max_results, 15))
        if not items:
            return f"독립운동판결문 '{q}' — 0건. 이름(이명·한자 포함)으로 재시도하십시오."
        return (f"독립운동판결문 '{q}' — {len(items)}건:\n"
                + "\n".join(f"- {it['title']} ({it['date']})\n  {it['url']}" for it in items)
                + "\n※ 상세 URL을 mode=indy query로 재투입 → 죄명·주문·사건개요·원문 뷰어 판독.")
    except Exception as e:
        return f"독립운동판결문 오류({str(e)[:60]}) — 잠시 후 재시도: https://theme.archives.go.kr/next/indy/viewMain.do"


def _much_mode(query: str, max_results: int) -> str:
    """역사박물관 심층 — 키워드 목록 / idnbr·URL 판독(재질·크기·공공누리 유형·설명). Node 패리티."""
    q = query.strip()
    try:
        im = re.search(r"idnbr=([A-Z]{2}[\w\-]+)", q) or re.match(r"^(PS\d[\w\-]{8,})$", q)
        if im:
            id2 = im.group(1)
            b = _cached_text("muchD:" + id2, 24 * 3600,
                             lambda: _http_text("https://archive.much.go.kr/archive/nrms/view.do?idnbr=" + _up.quote(id2), 25),
                             "소장품번호")
            flat = _clean(b)
            pick = lambda rx: ((re.search(rx, flat) or [None, ""])[1] or "").strip()
            mat = pick(r"재질\s*(\S{1,14})\s*작가")
            artist = pick(r"작가\s*(.{1,40}?)\s*크기")
            size = pick(r"크기\s*(\S{1,50}?)\s*소장품번호")
            no2 = pick(r"소장품번호\s*(\S{2,20})")
            km = re.search(r"제\s*(\d)\s*유형\s*:\s*(.{3,60}?)\s*본 저작물", flat)
            di = flat.find("이용할 수 있습니다.")
            desc = flat[di + 11:di + 1700].strip() if di >= 0 else ""
            desc = re.sub(r"&times;|×", "", re.split(r"자료열람|활용정보|이전글|다음글|사이트맵|COPYRIGHT", desc, flags=re.I)[0]).strip()
            if not no2 and not desc:
                return f"[{id2}] 상세 미발견 또는 구조 상이 — idnbr을 확인하거나 mode=much에 검색어를 넣으십시오."
            rline = ""
            if km:
                rc, rb = auto_rights({"rg_series": f"KOGL {km.group(1)}", "title_orig": "", "archive": "역사박물관"})
                rline = f"\n권리 초판정(공공누리 제{km.group(1)}유형 — {km.group(2).strip()}): {rc} — {rb}"
            meta = " · ".join(x for x in (f"소장품번호 {no2}" if no2 else "", f"재질 {mat}" if mat else "",
                                          f"작가 {artist}" if artist else "", f"크기 {size}" if size else "") if x)
            return (f"역사박물관 소장품 판독 — [{id2}]\n{meta}{rline}\n"
                    + (f"【설명】\n{desc}\n" if desc else "")
                    + f"원문·이미지: https://archive.much.go.kr/archive/nrms/view.do?idnbr={_up.quote(id2)}\n"
                    + "※ 출처: 대한민국역사박물관 근현대사아카이브 — 게재 시 출처 표기, 공공누리 유형 조건 준수.")
        items = _c_much(q, min(max_results, 10))
        if not items:
            return f"역사박물관 '{q}' — 0건. 사건명·실물 유형(포스터·잡지 등)으로 재시도하십시오."
        return (f"역사박물관 '{q}' — {len(items)}건:\n"
                + "\n".join(f"- {it['title']}" + (f" ({it['date']})" if it.get("date") else "") + f"\n  {it['url']}" for it in items)
                + "\n※ idnbr(또는 상세 URL)을 mode=much query로 재투입 → 재질·크기·공공누리 유형·설명 판독.")
    except Exception as e:
        return f"역사박물관 오류({str(e)[:60]}) — 잠시 후 재시도 또는 브라우저: https://archive.much.go.kr"


def _oldnews_mode(query: str, max_results: int) -> str:
    """신문아카이브 심층 — 키워드 목록 / CNTS·URL 판독(색인어·관련기사·주제어). Node 패리티."""
    q = query.strip()
    try:
        bm = re.match(r"^본문[:：]\s*(.+?)(?:\|(\d{4})\s*[-~]\s*(\d{4}))?$", q)
        if bm:  # OCR 본문 전문('본문:키워드' 또는 '|1905-1910' 연대 한정 — 서버 faceted는 연결 거부라 후처리 필터)
            kw = bm.group(1).strip()
            y1 = int(bm.group(2)) if bm.group(2) else 0
            y2 = int(bm.group(3)) if bm.group(3) else 9999
            req = _ur.Request("https://nl.go.kr/newspaper/search_bodytext.do",
                              data=json.dumps({"search_keyword": kw, "page_size": (30 if y1 else min(max_results, 10)), "page_no": 1}).encode(),
                              headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json",
                                       "Referer": "https://nl.go.kr/newspaper/bodytext_search.do"})
            with _ur.urlopen(req, timeout=25) as r:
                d2 = json.loads(r.read().decode("utf-8", "replace"))
            f1 = lambda v: (v[0] if isinstance(v, list) and v else v) or ""
            dist = " · ".join(f"{k}:{v}" for k, v in sorted((d2.get("by_issuedYear") or {}).items(), key=lambda x: -x[1])[:6])
            hits2 = [h for h in (d2.get("hits") or [])
                     if y1 <= (int(str(h.get("issued_date") or "")[:4] or 0)) <= y2][:min(max_results, 10)]
            rows = []
            for h in hits2:
                ex = _clean(str(f1(h.get("highlight_abstract")) or f1(h.get("abstract")) or ""))
                link = f"https://nl.go.kr/newspaper/detail.do?content_id={f1(h.get('uri'))}" if f1(h.get("uri")) else ""
                rows.append(f"- {f1(h.get('label'))} — {f1(h.get('newspaperKorName'))} ({h.get('issued_date') or ''})\n  발췌: {ex[:180]}\n  {link}")
            if not rows:
                rng = f" ({y1}~{y2})" if y1 else ""
                return (f"신문아카이브 본문검색 '{kw}'{rng} — 0건."
                        + (" 상위 30건 내 해당 연대 없음 — 범위를 넓히거나" if y1 else "")
                        + " 당대 표기(국한문·옛 한글)로 재시도하십시오."
                        + (f"\n연도 분포(전체): {dist}" if dist else ""))
            rng = f" (연대 {y1}~{y2} 한정)" if y1 else ""
            return (f"신문아카이브 OCR 본문검색 '{kw}'{rng} — 전체 {d2.get('total_count') or len(rows)}건"
                    + (f" · 연도 분포 {dist}" if dist else "") + f"\n표시 {len(rows)}건:\n"
                    + "\n".join(rows)
                    + "\n※ 발췌는 OCR 원문(국한문 그대로). CNTS를 mode=oldnews로 재투입 → 색인어·관련기사 연쇄.")
        cm = re.search(r"content_id=(CNTS-\d+)", q) or re.match(r"^(CNTS-\d+)$", q)
        if cm:
            cid = cm.group(1)
            def fetch():
                req = _ur.Request(f"https://nl.go.kr/newspaper/news_detail.do?content_id={cid}&ko_trans=no&abstractExist=false",
                                  headers={"User-Agent": "Mozilla/5.0", "Referer": "https://nl.go.kr/newspaper/detail.do"})
                with _ur.urlopen(req, timeout=25) as r:
                    return r.read().decode("utf-8", "replace")
            d = json.loads(_cached_text("oldnewsD:" + cid, 24 * 3600, fetch, "newspaperKorName"))
            f1 = lambda v: (v[0] if isinstance(v, list) and v else v) or ""
            if not f1(d.get("label")):
                return f"[{cid}] 기사 미발견 — CNTS ID를 확인하십시오."
            subj = " · ".join(str(x).split("|")[0] for x in ((d.get("subjectEvent") or []) + (d.get("subjectPlace") or []))[:8])
            rel = "\n".join(f"  · {f1(r2.get('label'))} ({f1(r2.get('issued'))}) {f1(r2.get('uri'))}"
                            for r2 in (d.get("relatedArticles") or [])[:5])
            kws = ", ".join(d.get("keyword") or [])[:800]
            return (f"신문아카이브 기사 판독 — {f1(d.get('label'))}\n"
                    f"{f1(d.get('newspaperKorName'))}"
                    + (f"({f1(d.get('newspaperForeignName'))})" if f1(d.get("newspaperForeignName")) else "")
                    + f" · {f1(d.get('issued'))} · 발행 {f1(d.get('publisher'))}\n"
                    + (f"색인어(기사 내용 재구성): {kws}\n" if kws else "")
                    + (f"주제: {subj}\n" if subj else "")
                    + (f"관련기사 연쇄(→ CNTS를 mode=oldnews로 재투입):\n{rel}\n" if rel else "")
                    + (("원소장처: " + " / ".join(d.get("description") or [])[:200] + "\n") if d.get("description") else "")
                    + f"원문 이미지(뷰어): https://nl.go.kr/newspaper/detail.do?content_id={cid}\n"
                    + "※ 출처: 국립중앙도서관 대한민국신문아카이브 — 본문은 이미지 원문(뷰어 열람). 게재 시 신문명·발행일 출처 표기, 원소장처 병기.")
        items = _c_oldnews(q, min(max_results, 10))
        if not items:
            return f"신문아카이브 '{q}' — 0건. 당대 표기(한자·옛 한글)로 재시도하십시오."
        return (f"신문아카이브 '{q}' — {len(items)}건:\n"
                + "\n".join(f"- {it['title']} ({it['date']})\n  {it['url']}" for it in items)
                + "\n※ CNTS ID(또는 상세 URL)를 mode=oldnews query로 재투입 → 색인어·관련기사 연쇄·주제어 판독.")
    except Exception as e:
        return f"신문아카이브 오류({str(e)[:60]}) — 잠시 후 재시도 또는 브라우저: https://nl.go.kr/newspaper/"


def _un_mode(query: str, max_results: int) -> str:
    """UN 디지털도서관 심층 — 키워드 목록 / recid·URL 판독(요약·주제·언어별 PDF). Node 패리티."""
    q = query.strip()
    try:
        rm = re.search(r"digitallibrary\.un\.org/record/(\d+)", q) or re.match(r"^(\d{4,9})$", q)
        if rm:
            recid = rm.group(1)
            def fetch():
                req = _ur.Request(f"https://digitallibrary.un.org/search?p=recid%3A{recid}&of=recjson&rg=1",
                                  headers={"User-Agent": "KoreaArchiveMCP/1.0 (https://github.com/changgi/korea-archive-mcp)"})
                with _ur.urlopen(req, timeout=25) as r:
                    return r.read().decode("utf-8", "replace")
            d = json.loads(_cached_text("unD:" + recid, 24 * 3600, fetch, "recid"))
            r = d[0] if isinstance(d, list) and d else None
            if not r:
                return f"[recid {recid}] 레코드 미발견 — record URL 또는 recid를 확인하십시오."
            files = [f for f in (r.get("files") or []) if f and f.get("url")]
            sym = re.sub(r"-[A-Z]{2}\.pdf$", "", (files[0].get("full_name", "") if files else ""), flags=re.I).replace("_", "/")
            en = next((f for f in files if re.search(r"english", f.get("description") or "", re.I)
                       or re.search(r"-EN\.pdf$", f.get("full_name") or "", re.I)), None)
            subs = " · ".join([x.get("term") for x in (r.get("subject") or []) if x.get("term")][:6])
            abs_ = _clean(str((r.get("abstract") or {}).get("summary") or ""))
            head = " · ".join(x for x in (f"발행: {(r.get('imprint') or {}).get('date')}" if (r.get("imprint") or {}).get("date") else "",
                                          f"주제: {subs}" if subs else "") if x)
            return (f"UN 디지털도서관 판독 — {sym or f'recid {recid}'}\n{head}\n"
                    + (f"【요약】\n{abs_[:1500]}\n본문 지문(sha256-16): {_hl.sha256(abs_.encode('utf-8')).hexdigest()[:16]} — 판독 시점 요약 전문 기준. 재판독 지문 불일치=원문 개정 발생.\n" if abs_ else "")
                    + (f"영문 PDF: {en['url']}\n" if en else "")
                    + (("전체 언어판 %d종: " % len(files)) + "·".join(f.get("description") or "" for f in files) + "\n" if len(files) > 1 else "")
                    + f"레코드: https://digitallibrary.un.org/record/{recid}\n"
                    + "※ UN 공식문서 — 출처 표기 하에 인용 가능(문서기호 병기). 결의·보고서 원문은 PDF 직링크로 분석 투입.")
        items = _c_un(q, min(max_results, 10))
        if not items:
            return f"UN 디지털도서관 '{q}' — 0건. 영문 사건명·문서기호(S/RES/84 등)로 재시도하십시오."
        return (f"UN 디지털도서관 '{q}' — {len(items)}건:\n"
                + "\n".join(f"- {it['title']}" + (f" ({it['date']})" if it.get("date") else "") + f"\n  {it['url']}" for it in items)
                + "\n※ record URL(또는 recid 숫자)을 mode=un query로 재투입 → 요약·주제·언어별 PDF 직링크 판독.")
    except Exception as e:
        return f"UN 디지털도서관 오류({str(e)[:60]}) — 잠시 후 재시도 또는 브라우저: https://digitallibrary.un.org"


def _jsg_mode(query: str, max_results: int) -> str:
    """장서각 심층 — 키워드 목록 / 청구기호·URL 서지+해제 전문 판독(서버 렌더 실측 2026-11-21). Node 패리티."""
    q = query.strip()
    try:
        dm = (re.search(r"dataId=(JSG_[\w.\-]+)", q) or re.match(r"^(JSG_[\w.\-]+)$", q)
              or re.match(r"^([A-Z]\d+(?:-\d+)*(?:[A-Za-z]*\d*)?)$", q))
        if dm and not re.search(r"\s", q) and (dm.group(1).startswith("JSG_") or re.match(r"^[A-Z]\d", dm.group(1))):
            did = dm.group(1) if dm.group(1).startswith("JSG_") else "JSG_" + dm.group(1)
            b = _cached_text("jsgD:" + did, 24 * 3600,
                             lambda: _http_text("https://jsg.aks.ac.kr/dir/view?dataId=" + _up.quote(did), 25), "청구기호")
            flat = _clean(b).replace("&middot;", "·")
            pick = lambda rx: ((re.search(rx, flat) or [None, ""])[1] or "").strip()
            name = pick(r"자료명\(한글\)\s*([^·]{2,60}?)\s*·")
            callno = pick(r"청구기호\s*(\S{2,20})")
            mf = pick(r"MF번호\s*(\S{2,20})")
            cm = re.search(r"유형분류\s*(\S{2,20})\s*주제분류\s*(\S{2,30})\s*수집분류\s*(\S{2,30})", flat)
            i0 = flat.find("정의 ")
            haeje = ""
            jfp = ""
            if i0 >= 0:
                haeje = re.split(r"집필자|관련 멀티미디어|장서각 디지털아카이브 바로가기", flat[i0:i0 + 6000])[0].strip()
                jfp = _hl.sha256(haeje.encode("utf-8")).hexdigest()[:16]  # 판독 시점 해제 지문
                if len(haeje) > 4000:
                    haeje = haeje[:4000] + f" …(총 {len(haeje)}자 — 전문은 원문 링크)"
            if not callno and not haeje:
                return f"'{did}' — 상세 미발견 또는 구조 상이. 청구기호(K2-…)를 확인하거나 mode=jsg에 검색어를 넣으십시오."
            meta = " · ".join(x for x in (f"청구기호 {callno}" if callno else "", f"MF {mf}" if mf else "",
                                          cm.group(1) if cm else "", cm.group(2) if cm else "") if x)
            return (f"장서각 서지·해제 판독 — {name or did}\n{meta}\n"
                    + (f"【해제】\n{haeje}\n" if haeje else "")
                    + (f"본문 지문(sha256-16): {jfp} — 판독 시점 해제 전문 기준. 재판독 지문 불일치=원문 개정 발생.\n" if haeje else "")
                    + f"원문·이미지: https://jsg.aks.ac.kr/dir/view?dataId={_up.quote(did)}\n"
                    + "※ 출처: 한국학중앙연구원 장서각 — 게재 시 출처 표기, 이미지 재이용은 기관 이용조건 준수. "
                    "해제 인용은 국역·해설(학술 인용 시 집필 해제임을 명기).")
        items = _c_jsg(q, min(max_results, 10))
        if not items:
            return f"장서각 '{q}' — 0건. 서명·주제어(의궤·등록 등)로 재시도하십시오."
        return (f"장서각 '{q}' — {len(items)}건:\n"
                + "\n".join(f"- {it['title']}" + (f" [{it['id']}]" if it.get("id") else "") + f"\n  {it['url']}" for it in items)
                + "\n※ 청구기호(K2-… 등)나 상세 URL을 mode=jsg query로 재투입 → 서지·해제 전문 판독.")
    except Exception as e:
        return f"장서각 오류({str(e)[:60]}) — 잠시 후 재시도 또는 브라우저: https://jsg.aks.ac.kr"


def _commons_mode(query: str, max_results: int) -> str:
    """위키미디어 공용 심층 — 키워드 목록 / File URL 판독(라이선스·원 소장처·설명). Node 패리티."""
    q = query.strip()
    try:
        fm = re.match(r"^https?://commons\.wikimedia\.org/wiki/(File:.+)$", q, re.I) or re.match(r"^(File:.+)$", q, re.I)
        if fm:
            title = _up.unquote(fm.group(1)).replace("_", " ")
            raw = _cached_text("commonsD:" + title, 24 * 3600,
                               lambda: json.dumps(http_json(
                                   "https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo"
                                   "&iiprop=url%7Cextmetadata%7Csize&format=json&titles=" + _up.quote(title),
                                   headers={"User-Agent": "KoreaArchiveMCP/1.0 (https://github.com/changgi/korea-archive-mcp; archival discovery)"}),
                                   ensure_ascii=False), "imageinfo")
            d = json.loads(raw)
            page = list(((d.get("query", {}) or {}).get("pages", {}) or {"_": {}}).values())[0]
            ii = (page.get("imageinfo") or [{}])[0]
            em = ii.get("extmetadata", {}) or {}
            g = lambda k: _clean(str((em.get(k) or {}).get("value", "")))
            lic = g("LicenseShortName")
            if not ii.get("url") and not lic:
                return f"'{title}' — 파일 미발견 또는 메타 없음. File: 제목/URL을 확인하십시오."
            rights = ("A(퍼블릭 도메인 표기)" if re.search(r"public domain", lic, re.I)
                      else f"B({lic} — 조건 준수 시 이용)" if re.match(r"^cc", lic, re.I)
                      else f"D('{lic or '미표기'}' — 확인 필요)")
            meta = " · ".join(x for x in (
                f"촬영/제작: {g('DateTimeOriginal')[:40]}" if g("DateTimeOriginal") else "",
                f"작가: {g('Artist')[:70]}" if g("Artist") else "",
                f"원본 {ii.get('width')}×{ii.get('height')}" if ii.get("width") else "") if x)
            return (f"위키미디어 공용 파일 판독 — {title.removeprefix('File:')}\n{meta}\n"
                    f"라이선스: {lic or '(미표기)'} → 권리 초판정 {rights}\n"
                    + (f"출처(원 소장처): {g('Credit')[:160]}\n" if g("Credit") else "")
                    + (f"【설명】\n{g('ImageDescription')[:1200]}\n" if g("ImageDescription") else "")
                    + (f"원본 이미지: {ii.get('url')}\n" if ii.get("url") else "")
                    + "파일 페이지: https://commons.wikimedia.org/wiki/" + _up.quote(title.replace(" ", "_")) + "\n"
                    + "※ 라이선스는 업로더 기재 — 게재 전 원 소장처(NH·NARA 번호 등) 카탈로그와 교차검증(nara_search·judge_rights).")
        items = _c_commons(q, min(max_results, 10))
        if not items:
            return f"위키미디어 공용 '{q}' — 0건. 영문 지명·사건명으로 재시도하십시오."
        return (f"위키미디어 공용 '{q}' — {len(items)}건:\n"
                + "\n".join(f"- {it['title']}\n  {it['url']}" for it in items)
                + "\n※ 파일 URL(또는 File:제목)을 mode=commons query로 재투입 → 라이선스·원 소장처·설명 판독.")
    except Exception as e:
        return (f"위키미디어 공용 오류({str(e)[:60]}) — 공유 IP 요청 제한(429)일 수 있음. "
                "잠시 후 재시도 또는 브라우저: https://commons.wikimedia.org")


def _earchive_mode(query: str, max_results: int) -> str:
    """국편 전자사료관 심층 — 키워드 목록 / '키워드|순번' 세션 상세(검색 폼+searchPosition 재제출). Node 패리티."""
    import http.cookiejar as _cj
    q = query.strip()
    try:
        pm = re.match(r"^(.+)\|(\d{1,3})$", q)
        if pm:
            kw, pos = pm.group(1).strip(), pm.group(2)
            base = {"allSearchQuery": kw, "searchQuery": kw, "searchPageIndex": "1",
                    "searchPageUnit": "10", "searchPageSize": "10"}
            opener = _ur.build_opener(_ur.HTTPCookieProcessor(_cj.CookieJar()))
            def post(url, extra):
                req = _ur.Request(url, data=_up.urlencode({**base, **extra}).encode(),
                                  headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded",
                                           "Referer": "https://archive.history.go.kr/search/searchResult.do"})
                with opener.open(req, timeout=25) as r:
                    return r.read().decode("utf-8", "replace")
            post("https://archive.history.go.kr/search/searchResult.do", {})  # 세션 수립
            b = post("https://archive.history.go.kr/record/catalog/catalogView.do", {"searchPosition": pos})
            title = _clean((re.search(r'<div class="info-box">\s*<div>\s*<p>([\s\S]*?)</p>', b) or [None, ""])[1] or "")
            # 메타는 row-box(label/value) 앵커 — 평문 매칭은 내비게이션 메뉴와 혼동(실측)
            def row_val(name):
                m = re.search(r'<div class="label">' + name + r'</div>\s*<div class="value">\s*<p>([\s\S]*?)</p>', b)
                return _clean(m.group(1)) if m else ""
            sid = (re.search(r"사료건(?:&nbsp;|\s)*([0-9A-Za-z_]{6,})", b) or [None, ""])[1] or ""
            series = (re.search(r"사료계열\s+([0-9A-Za-z_]{5,24})", _clean(b)) or [None, ""])[1] or ""
            reg = re.search(r'<th scope="col">등록번호</th>\s*<th scope="col">청구기호</th>\s*</tr>\s*<tr>\s*<td>\s*([0-9A-Za-z]*)\s*</td>\s*<td>\s*([\s\S]*?)\s*</td>', b)
            if not title:
                return f"'{kw}' {pos}번 상세 파싱 실패 — 순번 범위(0~9, 페이지1 기준)와 키워드를 확인하십시오."
            meta = " · ".join(x for x in (f"사료건 {sid}" if sid else "", f"사료계열 {series}" if series else "",
                                          f"등록번호 {reg.group(1)}" if reg and reg.group(1) else "",
                                          f"청구기호 {_clean(reg.group(2))}" if reg and _clean(reg.group(2)) else "") if x)
            acc, use = row_val("열람조건"), row_val("이용조건")
            return (f"국편 전자사료관 상세 [{kw} · {pos}번] {title}\n{meta}\n"
                    + (f"열람조건: {acc}\n" if acc else "") + (f"이용조건: {use}\n" if use else "")
                    + "원문 열람: https://archive.history.go.kr 에서 사료ID·등록번호로 재검색\n"
                    + "※ 출처: 국사편찬위원회 전자사료관. 이용조건 문구를 judge_rights(archive 필드)에 투입해 초판정. 해외 수집 사료는 원 소장처(NARA 등) 권리 확인 병행.")
        items = _c_earchive(q, min(max_results, 10))
        if not items:
            return f"국편 전자사료관 '{q}' — 0건. 다른 표기·주제어로 재시도하십시오."
        return (f"국편 전자사료관 '{q}' — {len(items)}건:\n"
                + "\n".join(f"- [{i}] {it['title']}" + (f" ({it['id']})" if it.get("id") else "") for i, it in enumerate(items))
                + f"\n※ '{q}|순번'을 mode=earchive query로 재투입 → 상세 판독(열람·이용조건·등록번호). 순번은 위 대괄호(페이지1 기준 0~9).")
    except Exception as e:
        return f"국편 전자사료관 오류({str(e)[:60]}) — 잠시 후 재시도 또는 브라우저: https://archive.history.go.kr"


def _ktv_mode(query: str, max_results: int) -> str:
    """KTV e영상역사관 심층 — 키워드 목록 / ehistory view URL 판독(해설·제작연도·상영시간, KOGL). Node 패리티."""
    q = query.strip()
    try:
        if re.match(r"^https?://www\.ehistory\.go\.kr/view/", q):  # ehistory 도메인 한정(임의 URL 페치 방지)
            b = _cached_text("ktvD:" + q, 24 * 3600,
                             lambda: _http_text(_up.quote(q, safe="/?&=:%"), 28), "board_header")
            pick = lambda rx: _clean((re.search(rx, b) or [None, ""])[1] or "")
            title = pick(r"board_header[\s\S]*?<h4>\s*<strong>([\s\S]*?)</strong>")
            pdate = pick(r'<p class="date">[\s\S]*?</strong>([\s\S]*?)</p>')
            ptime = pick(r'<p class="time">[\s\S]*?</strong>([\s\S]*?)</p>')
            origin = pick(r'<p class="origin">[\s\S]*?</strong>([\s\S]*?)</p>')
            raw = (re.search(r'<div class="txt">([\s\S]*?)</div>', b) or [None, ""])[1] or ""
            body = re.sub(r"<[^>]+>", " ", re.sub(r"<br\s*/?>", "\n", raw, flags=re.I))
            body = "\n".join(re.sub(r"\s+", " ", l).strip() for l in body.split("\n"))
            body = re.sub(r"\n{3,}", "\n\n", body).strip()
            if not title and not body:
                return f"판독 실패 — 영상 상세 구조 상이. 브라우저로 열람: {q}"
            kfp = _hl.sha256(body.encode("utf-8")).hexdigest()[:16] if body else ""  # 판독 시점 해설 지문
            if len(body) > 4000:
                body = body[:4000] + f" …(총 {len(body)}자 — 전문은 원문 링크)"
            meta = " · ".join(x for x in (f"제작연도: {pdate}" if pdate else "", f"상영시간: {ptime}" if ptime else "",
                                          f"출처: {origin}" if origin else "") if x)
            return (f"KTV e영상역사관 영상 판독 — {title or '(제목 미상)'}\n{meta}\n"
                    + (f"【해설】\n{body}\n" if body else "")
                    + (f"본문 지문(sha256-16): {kfp} — 판독 시점 해설 전문 기준. 재판독 지문 불일치=원문 개정 발생.\n" if kfp else "")
                    + f"원문(영상 재생): {q}\n"
                    + '※ KTV 콘텐츠는 KOGL(공공누리) — judge_rights에 "KOGL" 표기로 초판정. 게재 시 출처 표기.')
        items = _c_ktv(q, min(max_results, 10))
        if not items:
            return f"KTV e영상역사관 '{q}' — 0건. '대한뉴스'·사건명·인명으로 재시도하십시오."
        return (f"KTV e영상역사관 '{q}' — {len(items)}건:\n"
                + "\n".join(f"- {it['title']}\n  {it['url']}" for it in items)
                + "\n※ view URL을 mode=ktv query로 재투입 → 영상 해설·제작연도·상영시간 판독.")
    except Exception as e:
        return f"KTV 오류({str(e)[:60]}) — 잠시 후 재시도 또는 브라우저: https://www.ehistory.go.kr"


def _i815_mode(query: str, max_results: int) -> str:
    """독립기념관 심층 — 키워드 목록 / detail.do URL 본문 판독. Node nedb_search mode='i815' 패리티."""
    q = query.strip()
    try:
        if re.match(r"^사전\s*[:：]", q):  # 한국독립운동인명사전 — v1.56 복구 합류(retry-blocked 주간 재점검 실측으로 감지)
            t = re.sub(r"^사전\s*[:：]", "", q).strip()
            noscript = lambda s: re.sub(r"<script[\s\S]*?</script>", "", s, flags=re.I)
            if re.match(r"^\d+$", t):  # 상세 — 기본정보(생몰·본관·이명·훈격) + 전기 본문
                du = ("https://search.i815.or.kr/dictionary/detail.do"
                      f"?searchWord=&reSearchWord=&searchType=all&index=&id={t}")
                b = _cached_text("i815W:" + t, 24 * 3600, lambda: _http_text(du, 28), "기본정보")
                flat = _clean(noscript(b))
                ix = flat.find("기본정보")
                if ix < 0:
                    return f"인명사전 상세 실패(id={t}) — \"사전:이름\" 검색으로 번호를 다시 확보하십시오. 브라우저: {du}"
                seg = flat[ix:]
                hm = re.match(r"^기본정보\s*([\s\S]{0,600}?포상훈격\(연도\)\s*\S+)\s", seg)
                head = hm.group(1) if hm else seg[:350]
                bio = seg[len(hm.group(0)) if hm else len(head):].strip()
                cut = re.search(r"참고문헌|저작권 안내", bio)
                if cut and cut.start() > 0:
                    bio = bio[:cut.start()].strip()
                fp = _hl.sha256((head + "\n" + bio).encode("utf-8")).hexdigest()[:16]  # 판독 시점 본문 지문(고정성)
                if len(bio) > 3200:
                    bio = bio[:3200] + f" …(전기 총 {len(bio)}자 — 전문은 원문)"
                return (f"독립기념관 한국독립운동인명사전 — 항목 {t}\n【기본정보】 {head}\n【전기】\n{bio}\n원문: {du}\n"
                        + f"본문 지문(sha256-16): {fp} — 판독 시점 전문(기본정보+전기) 기준. 재판독 지문 불일치=원문 개정 발생(인용 검증용).\n"
                        "※ 공공저작물 — 출처 표기(독립기념관 한국독립운동인명사전) 시 이용 가능. "
                        "이명·한자명은 gonghun·jacar·oldnews(\"본문:이명\") 재검색에 투입.")
            b = _http_text("https://search.i815.or.kr/dictionary/searchResult.do?searchType=all&searchWord="
                           + _up.quote(t), 28)
            rows = []
            for blk in noscript(b).split("thumb_txt_case01")[1:1 + min(max_results, 15)]:
                mid = re.search(r"goDetail\((\d+)\)", blk)
                tt = re.search(r"dict_txt_title[^>]*>([\s\S]*?)</strong>", blk)
                if not mid or not tt:
                    continue
                line = _clean(blk)
                ser = re.search(r"운동계열:\s*([\s\S]{1,40}?)\s*관련단체:", line)
                act = re.search(r"주요활동:\s*([\s\S]{1,130}?)\s*본문내용:", line)
                rows.append(f"- [{mid.group(1)}] {_clean(tt.group(1))}"
                            + (f" · {ser.group(1).strip()}" if ser else "")
                            + (f"\n  {act.group(1).strip()}" if act else ""))
            if not rows:
                return f"인명사전 '{t}' — 0건. 한자명·이명으로 재시도(이명은 mode=gonghun이 제공)."
            return (f"한국독립운동인명사전 '{t}' — {len(rows)}건:\n" + "\n".join(rows)
                    + "\n※ \"사전:번호\" 재투입 → 기본정보(생몰·본관·이명·포상훈격)+전기 전문 판독. 공공저작물(출처 표기).")
        if re.match(r"^https?://search\.i815\.or\.kr/", q):  # 상세 판독 — i815 도메인 한정(임의 URL 페치 방지)
            b = _cached_text("i815D:" + q, 24 * 3600,
                             lambda: _http_text(_up.quote(q, safe="/?&=:%"), 28), "explain")
            paras = [_clean(m.group(1)) for m in
                     re.finditer(r'<(?:strong|p)[^>]*class="explain[^"]*"[^>]*>([\s\S]*?)</(?:strong|p)>', b)]
            paras = [p for p in paras if p]
            if not paras:
                return f"판독 실패 — 본문(explain) 없음(목록형 상세 또는 구조 상이). 브라우저로 열람: {q}"
            flat = _clean(b)
            np = re.search(r"신문명\s+(.{1,40}?)\s+발행일\s+([\d.\-]+)", flat)
            prod = re.search(r"생산정보\s+(\S.{0,60}?)\s+(?:기사제목|자료명|자료내용)", flat)
            body = "\n".join(paras)
            if len(body) > 4000:
                body = body[:4000] + f" …(총 {len(body)}자 — 전문은 원문 링크)"
            return ("독립기념관 자료 판독\n"
                    + (f"신문명: {np.group(1)} · 발행일: {np.group(2)}\n" if np else "")
                    + (f"생산정보: {prod.group(1)}\n" if prod else "")
                    + f"【자료내용】\n{body}\n원문: {q}\n"
                    + "※ 출처: 독립기념관 한국독립운동정보시스템 — 게재 시 출처 표기. 원문이미지는 페이지 뷰어에서. 권리 초판정: judge_rights.")
        items = _c_i815(q, min(max_results, 10))
        if not items:
            return (f"독립기념관 '{q}' — 0건. 인명·사건명·부대명 등으로 재시도하거나 "
                    "cross_search(variants=True)로 표기 변형을 팬아웃하십시오.")
        return (f"독립기념관 '{q}' — {len(items)}건:\n"
                + "\n".join(f"- {it['title']}\n  {it['url']}" for it in items)
                + "\n※ detail.do URL을 mode=i815 query로 재투입 → 자료 본문 판독. \"사전:이름\" → 한국독립운동인명사전(전기·생몰·훈격).")
    except Exception as e:
        return f"독립기념관 오류({str(e)[:60]}) — 잠시 후 재시도 또는 브라우저: https://search.i815.or.kr"


def _gonghun_mode(query: str, max_results: int) -> str:
    """공훈전자사료관 심층 — 이름 목록 / mngNo 판독(공적조서·공훈록 본문). Node nedb_search mode='gonghun' 패리티."""
    import base64 as _b64
    q = query.strip()
    b64d = lambda s: (_b64.b64decode(s).decode("utf-8") if s else "")
    try:
        if re.match(r"^종합\s*[:：]", q):  # 인물 종합 대조 — 레시피 ①의 도구화: 공훈록·인명사전·판결문 3채널 병렬(v1.57)
            nm = re.sub(r"^종합\s*[:：]", "", q).strip()
            def _dict3():
                b = _http_text("https://search.i815.or.kr/dictionary/searchResult.do?searchType=all&searchWord="
                               + _up.quote(nm), 28)
                rows = []
                for blk in re.sub(r"<script[\s\S]*?</script>", "", b, flags=re.I).split("thumb_txt_case01")[1:4]:
                    mid = re.search(r"goDetail\((\d+)\)", blk)
                    tt = re.search(r"dict_txt_title[^>]*>([\s\S]*?)</strong>", blk)
                    if not mid or not tt:
                        continue
                    ser = re.search(r"운동계열:\s*([\s\S]{1,40}?)\s*관련단체:", _clean(blk))
                    rows.append(f"- [사전:{mid.group(1)}] {_clean(tt.group(1))}"
                                + (f" · {ser.group(1).strip()}" if ser else ""))
                return rows
            res = {}
            for key, fn in (("g", lambda: [f"- [mngNo {it['id']}] {it['title']}" for it in _c_gonghun(nm, 3)]),
                            ("d", _dict3),
                            ("j", lambda: [f"- {it['title']} ({it['date']})\n  {it['url']}" for it in _c_indy(nm, 3)])):
                try:
                    res[key] = (fn(), "")
                except Exception as e:
                    res[key] = ([], str(e)[:40])
            sec = lambda t, pair: f"【{t}】\n" + ("\n".join(pair[0]) if pair[0] else f"(0건{' — 오류: ' + pair[1] if pair[1] else ''})")
            return (f"인물 종합 대조 '{nm}' — 공훈록·인명사전·판결문 3채널 병렬:\n"
                    + sec("공훈전자사료관(국가보훈부) — 공적·훈격", res["g"]) + "\n"
                    + sec("한국독립운동인명사전(독립기념관) — 학술 전기", res["d"]) + "\n"
                    + sec("독립운동판결문(국가기록원) — 죄명·주문", res["j"]) + "\n"
                    + "※ 심층: mngNo 숫자 재투입=공적조서·공훈록·수형기록 · mode=i815 \"사전:번호\"=전기 전문 · mode=indy 상세URL=주문·사건개요·원문 뷰어.\n"
                    + "※ 대조 포인트: 한자명·생몰 일치로 동명이인 분리 → 훈격(공훈)↔전기(사전)↔형량(판결문) 정합 → 이명 확보 후 oldnews \"본문:이명\"으로 당대 신문 확장.")
        if re.match(r"^\d+$", q):  # mngNo 상세
            b = _cached_text("gonghunD:" + q, 24 * 3600,
                             lambda: _http_text(f"https://e-gonghun.mpva.go.kr/user/ContribuReportDetail.do?goTocode=20001&mngNo={q}&pageTitle=Report", 28),
                             "achivement_1")
            pick = lambda rx: (re.search(rx, b) or [None, ""])[1] or ""
            try:
                name = b64d(pick(r"utf8_decode\('([A-Za-z0-9+/=]+)',\s*'#namekoDiv'"))
            except Exception:
                name = ""
            hanja = _clean(pick(r"<th>한자</th>\s*<td>([\s\S]*?)</td>"))
            alias = _clean(pick(r"<th>이명</th>\s*<td>([\s\S]*?)</td>"))
            try:
                birth = b64d(pick(r"utf8_decode\('([A-Za-z0-9+/=]*)',\s*'#birthdayenm'"))
                death = b64d(pick(r"utf8_decode\('([A-Za-z0-9+/=]*)',\s*'#deathdatenm'"))
            except Exception:
                birth = death = ""
            bon = " ".join(x for x in (b64d(m.group(1)) for m in re.finditer(r"utf8_decode\('([A-Za-z0-9+/=]+)',\s*'#famp\d'", b)) if x)
            aw = re.search(r"포상년도\s*([\d/]+)\s*훈격\s*(\S{1,30})", _clean(b))
            summary = _clean(pick(r'id="achivement_1"[^>]*>([\s\S]*?)</div>'))
            i2 = b.find('id="tab2"')
            rok = rok_info = gfp = ""
            if i2 >= 0:
                seg = _clean(b[b.find(">", i2) + 1:i2 + 30000])
                mi = re.search(r"수록정보[:\s]*([^)]{3,40}\))", seg)
                rok_info = mi.group(1) if mi else ""
                body = re.sub(r"^[\s\S]{0,80}?수록정보[:\s]*[^)]{3,40}\)\s*", "", seg).strip()
                # 본문 경계: 게시판(감사의 글)·JS 찌꺼기 절단. 수형기록·묘소·현충시설 표는 분석 가치가 있어 유지
                body = re.sub(r"\$\{\w+\}", "", re.sub(r"function\s+fn[\s\S]*$", "", body.split("감사의 글")[0])).strip()
                rok = body[:4000] + (f" …(총 {len(body)}자 — 전문은 원문 링크)" if len(body) > 4000 else "")
                gfp = _hl.sha256(((summary or "") + "\n" + body).encode("utf-8")).hexdigest()[:16]  # 판독 시점 본문 지문(고정성)
            if not name and not summary:
                return f"[mngNo {q}] 공훈전자사료관 상세 파싱 실패 — 관리번호를 확인하거나 mode=gonghun에 이름으로 검색하십시오."
            return (f"공훈전자사료관 독립유공자 [관리번호 {q}] {name}{f'({hanja})' if hanja else ''}{f' — 이명: {alias}' if alias else ''}\n"
                    f"생몰: {birth or '?'} ~ {death or '?'}{f' · 본적: {bon}' if bon else ''}"
                    + (f"\n포상: {aw.group(1)} {aw.group(2)}" if aw else "") + "\n"
                    + f"【공적개요(공적조서)】\n{summary or '(없음)'}\n"
                    + (f"【공훈록{f' — {rok_info}' if rok_info else ''}】\n{rok}\n" if rok else "")
                    + f"원문: https://e-gonghun.mpva.go.kr/user/ContribuReportDetail.do?goTocode=20001&mngNo={q}&pageTitle=Report\n"
                    + (f"본문 지문(sha256-16): {gfp} — 판독 시점 전문(공적조서+공훈록) 기준. 재판독 지문 불일치=원문 개정 발생(인용 검증용).\n" if gfp else "")
                    + "※ 출처: 국가보훈부 공훈전자사료관 — 게재 시 출처 표기. 공적조서·공훈록은 원칙적 수정불가 원문(정부포상 결정·전문가 집필). 권리 초판정: judge_rights.")
        items = _c_gonghun(q, min(max_results, 10))
        if not items:
            return (f"공훈전자사료관 '{q}' — 0건. 인명 검색 채널(독립유공자 공훈록)이므로 이름으로 검색하십시오. "
                    "이명·한자명도 시도 가치(예: 안응칠→안중근).")
        return (f"공훈전자사료관 독립유공자 '{q}' — {len(items)}건:\n"
                + "\n".join(f"- [mngNo {it['id']}] {it['title']}\n  {it['url']}" for it in items)
                + "\n※ mngNo 숫자를 mode=gonghun query로 재투입 → 공적조서·공훈록 본문 판독.")
    except Exception as e:
        return (f"공훈전자사료관 오류({str(e)[:60]}) — 잠시 후 재시도 또는 브라우저: "
                "https://e-gonghun.mpva.go.kr/user/ContribuReportList.do?goTocode=20001")


def _c_ktv(q, n):
    """KTV e영상역사관(대한뉴스·기록영상, KOGL) — ktv.go.kr 통합검색 iframe GET 실측(2026-11-19)."""
    b = _http_text("https://www.ktv.go.kr/totalSearch/ehistory?design=new&collection=ehistory&baseKeyword="
                   + _up.quote(q), 28)
    out = []
    for m in re.finditer(r'href="(https://www\.ehistory\.go\.kr/view/[^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{4,80})', b):
        t = _clean(m.group(2))
        if not t or re.search(r"paging|overflow", t):
            continue
        ktm = re.match(r"^(대한뉴스|리버티뉴스|문화영화|대한뉴우스)", t)
        out.append({"title": t, "date": "", "id": "", **({"series": ktm.group(1)} if ktm else {}), "url": m.group(1).replace("&amp;", "&")})
        if len(out) >= n:
            break
    return out


def _c_earchive(q, n):
    """국사편찬위 전자사료관 — POST 검색 실측(2026-11-19). NARA 수집 사료(AUS…) 원문 소장. 상세는 세션 기반 — 사료ID 표기."""
    body = _up.urlencode({"allSearchQuery": q, "searchQuery": q, "searchPageIndex": "1",
                          "searchPageUnit": str(min(n, 20)), "searchPageSize": "10"}).encode()
    req = _ur.Request("https://archive.history.go.kr/search/searchResult.do", data=body,
                      headers={"User-Agent": "Mozilla/5.0",
                               "Content-Type": "application/x-www-form-urlencoded"})
    with _ur.urlopen(req, timeout=25) as r:
        b = r.read().decode("utf-8", "replace")
    out = []
    # v1.81: 행 하단 스팬 전면 수확 — code(사료ID)·국내외·국가·소장기관·생산기간 (2026-11-21 실측: AUS033… → 미국 › 국립문서기록관리청)
    for seg in b.split("fnGoCatalogView(")[1:]:
        tm = re.search(r'title="([^"]{3,140})', seg)
        if not tm:
            continue
        sid = (re.search(r'<span class="code">([^<]+)<', seg) or re.search(r"^'(\d+)'", seg))
        spans = [_clean(x) for x in re.findall(r'<span class="date">\s*([^<]{1,80}?)\s*</span>', seg[:2500])]
        meta = [s for s in spans if not s.startswith("생산")]  # [국내외, 국가, 소장기관]
        inst = (meta[2] if len(meta) > 2 else "").split("(")[0].strip()
        ser = " › ".join(x for x in [(meta[1] if len(meta) > 1 else ""), inst] if x)
        prod_s = next((s for s in spans if s.startswith("생산기간")), "")
        pm = re.search(r"[\d.~\s]{4,24}", prod_s) if prod_s else None
        prod = pm.group(0).strip() if pm else ""
        out.append({"title": _clean(tm.group(1))[:110], "date": prod,
                    "id": _clean(sid.group(1)) if sid else "",
                    **({"series": ser[:60]} if ser else {}),
                    "url": "https://archive.history.go.kr"})
        if len(out) >= n:
            break
    return out


def _c_jacar(q, n):
    """일본 아시아역사자료센터(JACAR) — GET 검색 실측(2026-11-19, docs/jacar-access-spec.md). 파라미터는 kw."""
    en = _ko_ja(q) or _ko_en(q) or q  # 일본어 사상 우선 → 영어 → 원문
    b = _http_text("https://www.jacar.archives.go.jp/aj/search-en?kw=" + _up.quote(en), 30)
    out = []
    for blk in b.split('<li class="archive-result-table__body-item"')[1:]:
        c = re.search(r'value="aj\d+/([A-Z]\d{11})"', blk)
        t = re.search(r'id="row-\d+-title"[\s\S]*?<span\s*>([^<]{3,150})', blk)
        if c and t:
            out.append({"title": _clean(t.group(1)), "date": "", "id": c.group(1),
                        "url": "https://www.jacar.archives.go.jp/das/meta-en/" + c.group(1)})
        if len(out) >= n:
            break
    return out


def _c_seoul(q, n):
    """서울기록원 — v1.36 기록 단위 실체화: /catalog/result 서버 렌더 파싱 + fnDetail 딥링크(/item·/aggregation GET)."""
    base = "https://archives.seoul.go.kr"
    deep = base + "/catalog/result?regclass=ALL&query=" + _up.quote(q)
    b = _http_text(deep, 20)
    out, used = [], set()
    # ① 시리즈형: fnDetail 직후 2600자 내 d02 제목 — 제목+딥링크 완결 / 사진 기록건은 상세 판독 안내
    for seg in b.split("fnDetail('")[1:]:
        pm = re.match(r"^(/[a-z-]+/\d+)", seg)
        if not pm:
            continue
        path = pm.group(1)
        tm = re.search(r'<p class="d02">\s*<span><b>([\s\S]*?)</b>', seg[:2600])
        if tm:
            tt = _clean(tm.group(1))
            used.add(tt)
            out.append({"title": tt[:110], "date": "", "id": path.split("/")[2], "series": path.split("/")[1], "url": base + path})
        else:
            out.append({"title": f"[기록건·사진] {path.split('/')[1]} {path.split('/')[2]} — 제목·이용조건은 상세 URL 판독",
                        "date": "", "id": path.split("/")[2], "url": base + path})
        if len(out) >= n:
            break
    # ② 컬렉션 카드형: d02 제목만(링크 JS 바인딩) — 제목+전체결과 URL 신호
    if len(out) < n:
        for m in re.finditer(r'<p class="d02">\s*<span><b>([\s\S]*?)</b>', b):
            tt = _clean(m.group(1))
            if not tt or tt in used:
                continue
            used.add(tt)
            out.append({"title": f"[컬렉션] {tt}"[:110], "date": "", "id": "", "url": deep})
            if len(out) >= n:
                break
    return out


def _c_foia(q, n):
    """정보공개 원문 라이브 채널: 서울정보소통광장 결재문서 — 전용 도구(foia_search)와 동일 경로."""
    # 기지 차단(연결 리셋) — 단발 6s fail-fast로 health·연합 탐침 시간 보호. 복구 시 자동 정상화
    b = _http_text("https://opengov.seoul.go.kr/sanction/list?searchKeyword=" + _up.quote(q), 6)
    seen, out = set(), []
    for m in re.finditer(r'<a[^>]+href="(/sanction/\d+)"[^>]*>(.*?)</a>', b, re.S):
        t = re.sub(r"^제목\s*:\s*", "", _clean(m.group(2)))
        if t and m.group(1) not in seen:
            seen.add(m.group(1))
            out.append({"title": t, "date": "", "id": "", "url": "https://opengov.seoul.go.kr" + m.group(1)})
        if len(out) >= n:
            break
    return out


def _c_aks(q, n):
    """한국고문서자료관 소장처 매칭(내장 카탈로그 — 네트워크 0)."""
    toks = [t for t in q.split() if t]
    hits = [c for c in _AKS_CAT if toks and all(t in (c["name"] + " " + c["grp"]) for t in toks)]
    return [{"title": f"[고문서 소장처] {c['name']} ({c['grp']})", "date": "", "id": c["id"],
             "series": c["grp"], "url": _AKS_BASE + "/viewer/viewer.do"} for c in hits[:n]]

# 소장기관 정식명·국가 — 맥락 강화(v1.71)
ARCHIVE_META = {
    "tna": {"n": "The National Archives (영국 국립기록관)", "c": "GB"}, "ia": {"n": "Internet Archive", "c": "INT"},
    "gallica": {"n": "Gallica (프랑스 국립도서관 BnF)", "c": "FR"}, "europeana": {"n": "Europeana", "c": "EU"},
    "nara": {"n": "U.S. National Archives (NARA)", "c": "US"}, "archives": {"n": "국가기록원", "c": "KR"},
    "nlk": {"n": "국립중앙도서관", "c": "KR"}, "nedb": {"n": "국가기록원 개방데이터", "c": "KR"},
    "koreanwar": {"n": "KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터", "c": "KR"},
    "jacar": {"n": "아시아역사자료센터 JACAR", "c": "JP"}, "earchive": {"n": "국사편찬위원회 전자사료관", "c": "KR"},
    "i815": {"n": "독립기념관 한국독립운동정보시스템", "c": "KR"}, "gonghun": {"n": "국가보훈부 공훈전자사료관", "c": "KR"},
    "ktv": {"n": "KTV e영상역사관", "c": "KR"}, "oldnews": {"n": "국립중앙도서관 대한민국 신문 아카이브", "c": "KR"},
    "much": {"n": "대한민국역사박물관", "c": "KR"}, "indy": {"n": "국가기록원 독립운동판결문", "c": "KR"},
    "heritage": {"n": "국가유산청 국가유산포털", "c": "KR"}, "kyudb": {"n": "서울대 규장각한국학연구원", "c": "KR"},
    "jsg": {"n": "한국학중앙연구원 장서각", "c": "KR"}, "awm": {"n": "Australian War Memorial", "c": "AU"},
    "nlna": {"n": "Nationaal Archief (네덜란드)", "c": "NL"}, "dnz": {"n": "DigitalNZ (뉴질랜드 집계)", "c": "NZ"},
    "nzarch": {"n": "Archives New Zealand Te Rua Mahara", "c": "NZ"}, "commons": {"n": "Wikimedia Commons", "c": "INT"},
    "un": {"n": "UN Digital Library", "c": "INT"}, "ndl": {"n": "일본 국립국회도서관 NDL", "c": "JP"},
    "seoul": {"n": "서울기록원", "c": "KR"}, "foia": {"n": "정보공개포털·서울소통광장", "c": "KR"},
    "aks": {"n": "한국학중앙연구원 한국고문서자료관", "c": "KR"},
}
# 증거성 강화(v1.71): 레코드별 심층 판독 재현 호출문
DEEP_READ = {
    "gonghun": lambda it: it.get("id") and f"nedb_search(mode='gonghun', query='{it['id']}')",
    "i815": lambda it: it.get("url") and f"nedb_search(mode='i815', query='{it['url']}')",
    "un": lambda it: it.get("url") and f"nedb_search(mode='un', query='{it['url']}')",
    "nzarch": lambda it: it.get("id") and f"nedb_search(mode='nzarch', query='{it['id']}')",
    "jsg": lambda it: it.get("id") and f"nedb_search(mode='jsg', query='{it['id']}')",
    "much": lambda it: it.get("url") and f"nedb_search(mode='much', query='{it['url']}')",
    "indy": lambda it: it.get("url") and f"nedb_search(mode='indy', query='{it['url']}')",
    "heritage": lambda it: it.get("id") and f"nedb_search(mode='heritage', query='{it['id']}')",
    "ktv": lambda it: it.get("url") and f"nedb_search(mode='ktv', query='{it['url']}')",
    "jacar": lambda it: it.get("id") and f"nedb_search(mode='jacar', query='{it['id']}')",
    "oldnews": lambda it: it.get("id") and f"nedb_search(mode='oldnews', query='{it['id']}')",
    "commons": lambda it: it.get("url") and f"nedb_search(mode='commons', query='{it['url']}')",
    "koreanwar": lambda it: it.get("id") and f"koreanwar_item(archRfcd='{it['id']}')",
    "nara": lambda it: it.get("id") and ("judge_rights(naid=" + re.sub(r"\D", "", str(it["id"])) + ")"),
    "seoul": lambda it: it.get("url") and f"seoul_archives_search(query='{it['url']}')",
}
# 데이터화×맥락 강화(v1.72): 레코드의 상위 계층(partOf) 추출
def _part_of(ch, it):
    if ch == "nara" and it.get("series"):
        return f"NARA › {it['series']}"
    if ch == "ndl" and it.get("series"):
        return f"NDL › {it['series']}"
    if ch == "awm" and it.get("series"):
        return f"AWM 유형 › {it['series']}"
    if ch == "nlna" and it.get("series"):
        return f"NA(NL) › {it['series']}"
    if ch == "earchive" and it.get("series"):
        return f"수집처 › {it['series']}"
    if ch == "commons" and it.get("series"):
        return f"Commons › {it['series']}"
    if ch == "nzarch" and it.get("series"):
        return f"Series: {it['series']}"
    if ch == "koreanwar":
        m = re.match(r"^(\d{4})-([A-Z]{2})-(\d{2})-([A-Z]+)-([A-Z])-\d+$", str(it.get("id") or ""))
        if m:
            return f"수집 {m.group(1)} › {m.group(2)} › {m.group(4)}-{m.group(5)}"
    if ch == "jacar":
        o = {"A": "국립공문서관", "B": "외무성 외교사료관", "C": "방위성 방위연구소"}.get(str(it.get("id") or "")[:1])
        if o:
            return f"JACAR › {o}"
    if ch == "oldnews" and it.get("series"):
        return f"신문 › {it['series']}"
    if ch == "aks" and it.get("series"):
        return f"고문서 › {it['series']}"
    if ch == "dnz" and it.get("series"):
        return f"NZ › {it['series']}"
    if ch == "ia" and it.get("series"):
        return f"IA Collection › {it['series']}"
    if ch == "tna" and it.get("series"):
        return f"TNA › {it['series']}"
    if ch == "europeana" and it.get("series"):
        return f"Europeana › {it['series']}"
    if ch == "gonghun" and it.get("series"):
        return f"운동계열 › {it['series']}"
    if ch == "indy" and it.get("series"):
        return f"판결기관 › {it['series']}"
    if ch == "heritage" and it.get("series"):
        return f"지정 › {it['series']}"
    if ch == "un" and it.get("series"):
        return f"UN › {it['series']}"
    if ch == "gallica" and it.get("series"):
        return f"Gallica › {it['series']}"
    if ch == "much" and it.get("series"):
        return f"박물관 › {it['series']}"
    if ch == "i815" and it.get("series"):
        return f"자료 › {it['series']}"
    if ch == "ktv" and it.get("series"):
        return f"영상 › {it['series']}"
    if ch == "seoul" and it.get("series"):
        return f"기술단위 › {it['series']}"
    if ch == "archives" and it.get("series"):
        return f"생산기관 › {it['series']}"
    if ch == "nlk" and it.get("series"):
        return f"자료유형 › {it['series']}"
    if ch == "jsg" and it.get("series"):
        return f"四部 › {it['series']}"
    if ch == "kyudb" and it.get("series"):
        return f"소장 › {it['series']}"
    return None


_COLLECT = {"tna": _c_tna, "ia": _c_ia, "gallica": _c_gallica, "europeana": _c_europeana,
            "nara": _c_nara, "archives": _c_archives, "nlk": _c_nlk, "nedb": _c_nedb,
            "koreanwar": _c_koreanwar, "jacar": _c_jacar, "earchive": _c_earchive, "i815": _c_i815, "gonghun": _c_gonghun, "kyudb": _c_kyudb, "jsg": _c_jsg, "awm": _c_awm, "nlna": _c_nlna, "dnz": _c_dnz, "nzarch": _c_nzarch, "commons": _c_commons, "un": _c_un, "ndl": _c_ndl, "oldnews": _c_oldnews, "much": _c_much, "indy": _c_indy, "heritage": _c_heritage,
            "ktv": _c_ktv, "seoul": _c_seoul,
            "foia": _c_foia, "aks": _c_aks}



# ══════════ 조선 사료 심층 판독 (joseon-source-mining 이식 — joseon_tools.py 위임) ══════════
try:
    import sys as _jsys, os as _jos
    _jsys.path.insert(0, _jos.path.dirname(_jos.path.abspath(__file__)))
    import joseon_tools as _jt
except Exception:
    _jt = None


def _joseon_mode(query: str, mode: str, span: int, n: int) -> str:
    if _jt is None:
        return "조선 심층 판독 모듈(joseon_tools.py)을 찾지 못했습니다 — servers/ 폴더 확인."
    q = query.strip()
    try:
        if mode == "law":
            r = _jt.joseon_law_search(q, n)
            lines = [f"- [{x['level_id']}] {x['source']} {x['section']}\n  {x['excerpt'][:150]}\n  {x['url']}"
                     for x in r.get("results", [])[:n]]
            out = f"법전·편람 '{q}' — 총 {r.get('total', 0)}건:\n" + ("\n".join(lines) or "(0건)")
            if r.get("finding"):
                out += "\n★ " + r["finding"]
            return out + "\n※ " + r.get("note", "") + " 조문을 열었으면 mode=sibling으로 형제 조 확인."
        if mode == "record":
            r = _jt.joseon_record_search(q, max_results=max(n, 50))
            lines = [f"- [{x['level_id']}] {x['title'][:90]}\n  {x['url']}" for x in r.get("results", [])[:n]]
            out = (f"등록류 '{q}' — 보고 총계 {r.get('total_hits', 0)}건 · 座目 {r.get('jwamok_filtered', 0)}건 제외"
                   f" → 실질 {r.get('substantive', 0)}건:\n" + ("\n".join(lines) or "(실질 기사 0건)"))
            if r.get("warning"):
                out += "\n★ " + r["warning"]
            return out + "\n※ " + r.get("note", "")
        if mode == "item":
            r = _jt.joseon_item_read(q, max_chars=3000)
            if r.get("body_status") == "ok":
                return (f"[{q}] {r.get('title', '')}\n{r['body']}\n({r['chars']}자) {r['url']}"
                        f"\n※ {r.get('citation_note', '')} 조문이면 mode=sibling으로 형제 조 확인.")
            return f"[{q}] {r.get('title', '')} — {r.get('body_status')}: {r.get('note', '')} {r.get('url', '')}"
        if mode == "sibling":
            r = _jt.joseon_sibling_scan(q, span=span)
            if r.get("error"):
                return r["error"]
            lines = [f"{'●' if x['is_requested'] else '○'} {x['level_id']} [{x['head']}] {x['chars']}자 {x['url']}"
                     for x in r.get("siblings", [])]
            out = f"형제 조 전수 스캔 {q} (편: {r.get('parent', '')}):\n" + ("\n".join(lines) or "(형제 조 미검출)")
            if r.get("alert"):
                out += "\n★ " + r["alert"]
            return out
        if mode == "matrix":
            terms = [t.strip() for t in q.split(",") if t.strip()][:8]
            r = _jt.law_presence_matrix(terms)
            out = "법전 수록 대조표:\n" + "\n".join(
                f"- {x['term']}: {x['count']}건" + (f" ({x['earliest']})" if x.get("earliest") else "")
                + (" — " + x["note"] if x.get("note") else "") for x in r.get("matrix", []))
            if r.get("finding"):
                out += "\n★ " + r["finding"]
            return out
        if mode == "origin":
            parts = [t.strip() for t in q.split(",")]
            r = _jt.term_origin_trace(parts[0], parts[1] if len(parts) > 1 else "")
            out = f"어휘 연원 '{parts[0]}' — 법전 {r.get('total_in_law', 0)}건"
            if r.get("domains"):
                out += "\n영역 분포: " + " · ".join(f"{k} {v}" for k, v in r["domains"].items())
            for x in r.get("representative", [])[:4]:
                out += f"\n- {x['source']} {x['section']} | {x['excerpt'][:110]}"
            if r.get("finding"):
                out += "\n★ " + r["finding"]
            return out
        if mode == "sjw":
            r = _jt.sjw_search(q, n)
            out = f"승정원일기 '{q}' — 총 {r.get('total', 0)}건"
            if r.get("reign_distribution"):
                out += "\n왕대 분포: " + " · ".join(f"{k} {v}" for k, v in r["reign_distribution"].items())
            if r.get("alert"):
                out += "\n★ " + r["alert"]
            return out
        if mode == "kyujanggak":
            r = _jt.kyujanggak_search(q, area="both")
            out = f"규장각 '{q}'"
            for label, sec in r.get("sections", {}).items():
                if "error" in sec:
                    out += f"\n{label}: 오류({sec['error']})"
                else:
                    out += f"\n{label}: {sec['count']}건 — " + " ".join(x["call_number"] for x in sec.get("items", [])[:12])
            if r.get("alert"):
                out += "\n★ " + r["alert"]
            return out + '\n■ 원문 이미지 접근 지식(실측 2026-08-18) — GET·web_fetch 불가, ImageServlet 직접 URL은 브라우저에서 열림:\nhttps://kyudb.snu.ac.kr/ImageServlet.do?imgFileNm=[파일명]&path=/data01/stream/[item_cd]/IMG/[book_cd]/[book_cd]_0001/\nitem_cd 5종(자료 성격별): ART 도설·회화 / ETC 두루마리·축 / DRR 등록류 / FND 재정·사목 / POL 정책·절목.\n파일명 2형: 표준 [book_cd]_00_IH_0001_[nnn]a.jpg · POL계 [book_cd]_00IH_0001_[nnnn].jpg (밑줄 없음·4자리).\n★반드시 첫 장 URL을 실제로 받아 패턴 확정 후 순회 — 추정 순회는 전부 실패한다(200 OK·0바이트 함정 포함). 게재는 소장기관 허가 확인(02-880-5316).'
    except Exception as e:
        return f"조선 심층 판독({mode}) 실패: {e} — 한국사DB 계열은 전부 POST이며 GET 재현 불가. 잠시 후 재시도."
    return f"알 수 없는 mode: {mode}"



# ── 한국고문서자료관(한국학중앙연구원, archive.aks.ac.kr) — 소장처 172곳 (2026-11-17 treeAjax 전수 실측) ──
# 형식: id|상위경로(upPath)|분류|소장처명. 트리·문서목록은 라이브 조회, 이미지 일괄 수집은 로컬 전용. route.js 패리티.
_AKS_BASE = "https://archive.aks.ac.kr"
_AKS_RAW = """L011146|01^0111|문중>서울특별시|서울 마포 반남박씨 대종중
L011143|01^0111|문중>서울특별시|서울 마포 성주이씨 대종회
L011144|01^0111|문중>서울특별시|서울 원주김씨 두암 김응남 종가
L011148|01^0111|문중>서울특별시|서울 전주이씨 경녕군 후손가
L011145|01^0111|문중>서울특별시|서울 전주이씨 장천군 이보생 후손가
L011117|01^0111|문중>서울특별시|서울 진주류씨 우강 유태영 후손가
L016909|01^0169|문중>대구광역시|대구 영천이씨 세효당 후손가
L013003|01^0130|문중>대전광역시|대전 무수동 안동권씨 유회당 권이진 종가
L013001|01^0130|문중>대전광역시|대전 회덕 은진송씨 동춘당 송준길 후손가
L014151|01^0141|문중>경기도|광주 기곡 광주안씨 순암 안정복 종가
L014160|01^0141|문중>경기도|광주 연안이씨 매간 이익상 종가
L014158|01^0141|문중>경기도|광주 평산신씨 신대우
L014153|01^0141|문중>경기도|군포 속달 동래정씨 동래부원군 정난종 종가
L014140|01^0141|문중>경기도|김포 의령남씨 서윤공 남두장 후손가
L014156|01^0141|문중>경기도|김포 전주이씨 효헌 이인철 후손가
L014139|01^0141|문중>경기도|성남 해주오씨 월곡공파 오윤함
L014163|01^0141|문중>경기도|시흥 반남박씨 금계군 박동량 종가
L014132|01^0141|문중>경기도|안산 부곡 진주류씨 경성당
L014115|01^0141|문중>경기도|안성 보체 동래정씨 정홍순 종가
L014131|01^0141|문중>경기도|안성 해주오씨 오치풍 후손가
L014154|01^0141|문중>경기도|양근 안동김씨 노가재 김창업 후손가
L014161|01^0141|문중>경기도|양주 광주정씨
L014168|01^0141|문중>경기도|양주 사릉 해주정씨 종가
L014164|01^0141|문중>경기도|여주 산북 전주이씨 완양부원군 이충원 종가
L014148|01^0141|문중>경기도|여흥민씨 민영환 후손가
L014152|01^0141|문중>경기도|용인 해주오씨 추탄 오윤겸 종가
L014167|01^0141|문중>경기도|의정부 장암 반남박씨 서계 박세당 종가
L014166|01^0141|문중>경기도|의정부 장암 반남박씨 서계 박세당 후손가
L014165|01^0141|문중>경기도|이천 풍천임씨
L014303|01^0143|문중>충청북도|제천 한수 연안이씨
L014423|01^0144|문중>충청남도|공주 안동김씨 청음 김상헌 후손가
L014421|01^0144|문중>충청남도|공주 전주이씨 숭선군파 종가
L014422|01^0144|문중>충청남도|공주 진주류씨 금사 유충걸 후손가
L014418|01^0144|문중>충청남도|논산 노성 파평윤씨 명재 윤증 종가
L014426|01^0144|문중>충청남도|보령 천궁 경주김씨 직각 김면주 종가
L014425|01^0144|문중>충청남도|부여 은산 함양박씨 구당 박세영 종가
L014429|01^0144|문중>충청남도|서산 대교 경주김씨 충민공 김홍익 후손가
L014432|01^0144|문중>충청남도|서산 대교 경주김씨 학주 김홍욱 종가
L014433|01^0144|문중>충청남도|서산 대교 경주김씨 학주 김홍욱 후손가
L014430|01^0144|문중>충청남도|아산 선교 장흥임씨 종가
L014427|01^0144|문중>충청남도|예산 한곡 한산이씨 수당 고택
L014431|01^0144|문중>충청남도|예산 한양조씨
L014428|01^0144|문중>충청남도|청양 안동김씨 삼당 김영 후손가
L014738|01^0147|문중>전북특별자치도|고창 광산김씨 노산사
L014734|01^0147|문중>전북특별자치도|고창 신천강씨
L014724|01^0147|문중>전북특별자치도|고창 흥덕 평해황씨 이재 황윤석 종가
L014731|01^0147|문중>전북특별자치도|남원 안터 순흥안씨 사제당 안처순 후손가
L014722|01^0147|문중>전북특별자치도|남원·구례 삭녕최씨
L014720|01^0147|문중>전북특별자치도|부안 우반 부안김씨
L014735|01^0147|문중>전북특별자치도|익산 함열 임천조씨
L014736|01^0147|문중>전북특별자치도|정읍 광산김씨 김흥암 후손가
L014737|01^0147|문중>전북특별자치도|정읍 광산김씨 옥산서원
L014719|01^0147|문중>전북특별자치도|진안 정천 전주이씨 서곡 이정영 후손가
L014804|01^0148|문중>전라남도|구례 오미 문화류씨 운조루
L014803|01^0148|문중>전라남도|나주 회진 나주임씨 창계 임영 후손가
L014810|01^0148|문중>전라남도|영광 연안김씨 종가
L014802|01^0148|문중>전라남도|영광 영월신씨
L014812|01^0148|문중>전라남도|영암 남평문씨
L014813|01^0148|문중>전라남도|해남 김해김씨
L014811|01^0148|문중>전라남도|해남 연동 해남윤씨 녹우당
L016792|01^0167|문중>경상북도|경주 구정 경주이씨
L016722|01^0167|문중>경상북도|경주 소정 경주이씨
L016762|01^0167|문중>경상북도|경주 양동 경주손씨 종가 송첨
L016712|01^0167|문중>경상북도|경주 옥산 여주이씨 독락당
L016794|01^0167|문중>경상북도|경주 옥산 여주이씨 치암 이순 종가
L016798|01^0167|문중>경상북도|경주 용산서원
L016706|01^0167|문중>경상북도|경주 이조 경주최씨
L016727|01^0167|문중>경상북도|고령 도진 고령박씨 소윤공 문연재
L016763|01^0167|문중>경상북도|고령 선산김씨 점필재 김종직 종가
L016768|01^0167|문중>경상북도|구미 옥산 인동장씨 여헌 장현광 종가
L016746|01^0167|문중>경상북도|김천 성산이씨 양계 이하 종가
L016724|01^0167|문중>경상북도|김천 진주강씨 학암 강석귀 종가
L016744|01^0167|문중>경상북도|봉화 꽃내 무안박씨 회이당 박한 종가
L016725|01^0167|문중>경상북도|봉화 법전 진주강씨 고암 강임 후손가
L016775|01^0167|문중>경상북도|봉화 유곡 안동권씨 충재 권벌 종가
L016776|01^0167|문중>경상북도|봉화 유곡 안동권씨 충재 권벌 후손가
L016785|01^0167|문중>경상북도|상주 낙동 풍양조씨 양진당 조정
L016793|01^0167|문중>경상북도|상주 성주이씨 묵재 종가
L016767|01^0167|문중>경상북도|상주 연안이씨 식산 이만부 종가
L016766|01^0167|문중>경상북도|상주 우산 진주정씨 우복 정경세 종가
L016761|01^0167|문중>경상북도|상주 충주박씨 충원군 박동형 종가
L016769|01^0167|문중>경상북도|성주 명곡 벽진이씨 완석정 이언영 종가
L016764|01^0167|문중>경상북도|안동 갈전 순흥안씨 종가
L016713|01^0167|문중>경상북도|안동 금계 의성김씨 학봉 김성일 종가
L016758|01^0167|문중>경상북도|안동 법흥 고성이씨 종가 임청각
L016709|01^0167|문중>경상북도|안동 송파 진주하씨 하위지 후손가
L016701|01^0167|문중>경상북도|안동 수곡 전주류씨 무실 종가
L016715|01^0167|문중>경상북도|안동 오천 광산김씨 후조당 김부필
L016717|01^0167|문중>경상북도|안동 주촌 진성이씨 경류정
L016707|01^0167|문중>경상북도|안동 천전 의성김씨 천상각파
L016708|01^0167|문중>경상북도|안동 하회 풍산류씨
L016728|01^0167|문중>경상북도|안동 하회 풍산류씨 북촌댁 화경당
L016759|01^0167|문중>경상북도|영덕 도곡 무안박씨 무의공 박의장 종가
L016765|01^0167|문중>경상북도|영덕 도곡 무안박씨 충효당 박선 종가
L016760|01^0167|문중>경상북도|영덕 재령이씨 충효당 이함 종가
L016791|01^0167|문중>경상북도|영주 화계 인동장씨 연복군 종가
L016795|01^0167|문중>경상북도|예천 맛질 함양박씨 미산 박득녕 종가
L016796|01^0167|문중>경상북도|예천 맛질 함양박씨 박현녕 후손가
L016780|01^0167|문중>경상북도|예천 진주류씨 서파 유희 가문
L016741|01^0167|문중>경상북도|의성 아주신씨 오봉 신지제 가문
L016742|01^0167|문중>경상북도|의성 아주신씨 호계 신적도 가문
L016774|01^0167|문중>경상북도|청도 함박김씨
L016721|01^0167|문중>경상북도|칠곡 석전 광주이씨
L015019|01^0150|문중>경상남도|거창 강동 초계정씨 동계 정온 종가
L015025|01^0150|문중>경상남도|거창 거창신씨
L015024|01^0150|문중>경상남도|거창 은진임씨
L015022|01^0150|문중>경상남도|밀양 밀성박씨 종가 모선정
L015020|01^0150|문중>경상남도|밀양 사촌 의령남씨 종가 침류정
L015026|01^0150|문중>경상남도|밀양 창녕조씨 오봉서원
L015007|01^0150|문중>경상남도|진주 단목 진양하씨 단지 하협 종가
L015004|01^0150|문중>경상남도|진주 단목 진양하씨 창주 하증 후손가
L015023|01^0150|문중>경상남도|진주 마진 재령이씨 이재관 후손가
L015018|01^0150|문중>경상남도|진주 마진 재령이씨 종가
L015011|01^0150|문중>경상남도|진주 안계 진양하씨 담헌 하우선 종가
L015005|01^0150|문중>경상남도|진주 운문 진양하씨
L015002|01^0150|문중>경상남도|함안 두릉 순흥안씨
L015021|01^0150|문중>경상남도|함양 안의 밀양박씨 지족당 박명부 종가
L017101|01^0171|문중>강원특별자치도|강릉 전주이씨 선교장 효령대군 후손가
L016821|01^0168|문중>제주특별자치도|서귀포 사계 진주강씨
L016814|01^0168|문중>제주특별자치도|제주 경주김씨 문중회
L016807|01^0168|문중>제주특별자치도|제주 구좌 동래정씨 정석록 후손가
L016816|01^0168|문중>제주특별자치도|제주 동래정씨 정희현 후손가
L016819|01^0168|문중>제주특별자치도|제주 애월 김해김씨 김용징 후손가
L016820|01^0168|문중>제주특별자치도|제주 애월 김해김씨 김희주 후손가
L016822|01^0168|문중>제주특별자치도|제주 어도 진주강씨 강봉지 후손가
L016817|01^0168|문중>제주특별자치도|제주 어도 진주강씨 강수황 후손가
L016818|01^0168|문중>제주특별자치도|제주 어도 진주강씨 강익진 후손가
L016815|01^0168|문중>제주특별자치도|제주 제주고씨 종친회
L016810|01^0168|문중>제주특별자치도|제주 조천 곡산강씨 강만식 후손가
L016811|01^0168|문중>제주특별자치도|제주 조천 곡산강씨 강이진 후손가
L016806|01^0168|문중>제주특별자치도|제주 조천 김해김씨 김희정 후손가
L017201|01^0172|문중>인천광역시|강화·부여 창원황씨
L024712|02^0247|서원향교>경상북도|경주 용산서원
L024711|02^0247|서원향교>경상북도|경주 장산서원
L024710|02^0247|서원향교>경상북도|안동 병산서원
L024807|02^0248|서원향교>경상남도|거창 거창향교
L024804|02^0248|서원향교>경상남도|김해 김해향교
L024808|02^0248|서원향교>경상남도|밀양 덕남서원
L024806|02^0248|서원향교>경상남도|산청 단성향교
L024802|02^0248|서원향교>경상남도|산청 덕천서원
L024803|02^0248|서원향교>경상남도|함양 남계서원
L024801|02^0248|서원향교>경상남도|합천 용연서원
L024805|02^0248|서원향교>경상남도|합천 합천향교
L031119|03^0311|박물관도서관>서울특별시|국립고궁박물관
L031121|03^0311|박물관도서관>서울특별시|한국연구원
L037702|03^0377|박물관도서관>경기도|경기도박물관
L037705|03^0377|박물관도서관>경기도|명성황후기념관
L037701|03^0377|박물관도서관>경기도|여주박물관
L037801|03^0378|박물관도서관>강원특별자치도|오죽헌·시립박물관
L037502|03^0375|박물관도서관>충청북도|국립청주박물관
L039202|03^0392|박물관도서관>세종특별자치시|미래엔 교과서박물관
L040102|04^0401|공공기관>경기도|국사편찬위원회
L040101|04^0401|공공기관>경기도|한국학중앙연구원 장서각
L040301|04^0403|공공기관>서울특별시|규장각한국학연구원
L054904|05^0549|사찰>경상북도|김천 직지사
L054901|05^0549|사찰>경상북도|예천 용문사
L054701|05^0547|사찰>경상남도|고성 옥천사 보장각
L054702|05^0547|사찰>경상남도|고성 옥천사 청련암
L061502|06^0615|개인>경기도|신상후 선생님 제공 자료
L061503|06^0615|개인>경기도|헤이리예술마을뮤지엄카페 타임캡슐
L061201|06^0612|개인>경상북도|경주 경주이씨 이찬우
L0619  F02|06^L0619|개인>개인|고문서
L062001|06^0620|개인>미상|개인
L074902|07^0749|촌락>경상북도|경주 외동 방어리
L074901|07^0749|촌락>경상북도|경주 지북동(황성동)
L074801|07^0748|촌락>경상남도|거제 일운 구조라리
L074702|07^0747|촌락>제주특별자치도|제주 애월 수산리
L074703|07^0747|촌락>제주특별자치도|제주 애월 중엄리
L074701|07^0747|촌락>제주특별자치도|제주 애월 하가리
L0807  F02|08^L0807|기타>기타|고문서
L0809  F02|08^L0809|기타>명성황후 편지글(이기대, 다운샘, 2007)|고문서
L0811  F02|08^L0811|기타>한글서예변천전 도록|고문서"""
_AKS_CAT = [dict(zip(("id", "up", "grp", "name"), l.split("|"))) for l in _AKS_RAW.strip().splitlines()]


def _aks_text(url, timeout=25):
    req = _ur.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                                    "Referer": _AKS_BASE + "/viewer/viewer.do"})
    with _ur.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _aks_chain(base, suf):
    c = []
    if suf:
        c.append(base + suf[:3])
        if len(suf) > 3:
            c.append(base + suf)
    return c


def _aks_mode(query: str) -> str:
    q = query.strip()
    try:
        if "/" in q:  # '분류ID/G002+AKS+...' — 문서 노드 면·썸네일(imgnode)
            fid, did = q.split("/", 1)
            exact = next((c for c in _AKS_CAT if c["id"] == fid), None)  # 비표준 ID(공백 포함 4건) 정확일치 우선
            fm = re.match(r"^(L\d{6})(F\d{2,4})?$", fid)
            col = exact or next((c for c in _AKS_CAT if fm and c["id"] == fm.group(1)), None)
            if not col:
                return f"'{fid}' — 소장처 ID 불인식. mode=aks에 소장처명으로 먼저 검색하십시오."
            up = (col["up"] + "^" + fid) if exact else \
                "^".join([col["up"], fm.group(1)] + _aks_chain(fm.group(1), fm.group(2) or ""))
            j = json.loads(_aks_text(f"{_AKS_BASE}/viewer/imgnode.do?itemId=book&gubun=booktree&depth={len(up.split('^')) + 1}"
                                     f"&upPath={_up.quote(up)}&dataId={_up.quote(did)}&itemType="))
            items = j.get("imgItems") or []
            lines = [f"- {i + 1}면: {it.get('filename', '')}"
                     + (f"\n  썸네일 {_AKS_BASE}{it['thumb']}" if it.get("thumb") else "")
                     for i, it in enumerate(items[:8])]
            return (f"한국고문서자료관 문서 '{j.get('infoTitle') or did}' — {len(items)}면"
                    + (f" · UCI {j['dataUCI']}" if j.get("dataUCI") else "") + "\n" + "\n".join(lines)
                    + (f"\n… 외 {len(items) - 8}면" if len(items) > 8 else "")
                    + f"\n※ 원본 고해상 이미지 일괄 수집은 로컬 전용(aks-archive-harvester 스킬 — DZI 타일 복원). "
                      f"웹에서는 뷰어 열람: {_AKS_BASE}/viewer/viewer.do"
                    + "\n출처 표기: 한국학중앙연구원 한국고문서자료관. 이미지 재이용은 기관 이용조건 준수.")
        exact_col = next((c for c in _AKS_CAT if c["id"] == q), None)  # 비표준 ID 포함 정확일치 우선
        # 비표준 하위 분류('L0809  F0206' — 공백 포함, 카탈로그 밖): 부모 분류(F02)를 카탈로그에서 유도
        nm = None if exact_col else re.match(r"^(L\d{4,6})(\s+)(F\d{4})$", q)
        nm_parent = nm and next((c for c in _AKS_CAT
                                 if c["id"] == nm.group(1) + nm.group(2) + nm.group(3)[:3]), None)
        m = None if (exact_col or nm_parent) else re.match(r"^(L\d{6})(F\d{2,4})?$", q)
        if exact_col or nm_parent or m:  # 소장처/분류 노드 → 하위 트리 라이브 조회
            col = exact_col or nm_parent or next((c for c in _AKS_CAT if c["id"] == m.group(1)), None)
            if not col:
                return f"'{q}' — 소장처 목록(172곳)에 없는 ID. mode=aks에 소장처명을 넣어 먼저 검색하십시오."
            chain = [] if (exact_col or nm_parent) else _aks_chain(m.group(1), m.group(2) or "")
            up = col["up"] if exact_col else (col["up"] + "^" + col["id"]) if nm_parent else \
                "^".join([col["up"]] + ([m.group(1)] + chain[:-1] if m.group(2) else []))
            _aks_url = (f"{_AKS_BASE}/viewer/treeAjax.do?itemId=book&gubun=booktree"
                        f"&depth={len(up.split('^')) + 1}&upPath={_up.quote(up)}&dataId={_up.quote(q)}&itemType=")
            b = _cached_text("aks:" + q, 6 * 3600, lambda: _aks_text(_aks_url), "data-dataId")
            kids = [{"id": k[0], "leaf": "nochild" in k[1], "name": k[2]} for k in
                    re.findall(r"data-dataId='([^']+)'[\s\S]{0,300}?<span(?:\s+class='([^']*)')?\s+title='([^']*)'", b)]
            lines = [(f"- [문서] {k['name']}\n  상세: mode=aks query='{q}/{k['id']}'" if k["leaf"]
                      else f"- [분류 {k['id']}] {k['name']} → mode=aks query='{k['id']}'") for k in kids[:25]]
            return (f"한국고문서자료관 {col['name']} [{q}] 하위 {len(kids)}건:\n" + ("\n".join(lines) or "(0건)")
                    + (f"\n… 외 {len(kids) - 25}건" if len(kids) > 25 else "")
                    + f"\n※ 이미지 일괄 수집=로컬 스킬(aks-archive-harvester), 웹 열람=뷰어 {_AKS_BASE}. "
                      f"출처 표기: 한국학중앙연구원 한국고문서자료관.")
        toks = [t for t in q.split() if t]
        hits = [c for c in _AKS_CAT if toks and all(t in (c["name"] + " " + c["grp"]) for t in toks)]
        body = "\n".join(f"- [{c['id']}] {c['name']} ({c['grp']})" for c in hits[:20]) \
            or "(0곳 — 지역명·성씨·호 등으로 재시도. 예: \"송준길\", \"문중 충청\")"
        return (f"한국고문서자료관 소장처 '{q}' — {len(hits)}/172곳:\n" + body
                + "\n※ 다음 단계: mode=aks query='L013001'(분류 목록) → query='L013001F02'(문서 목록) → "
                  "query='분류ID/문서ID'(면·썸네일)."
                + f"\n172곳 전수는 2026-11 실측 스냅숏 — 신규 소장처는 {_AKS_BASE}에서 확인.")
    except Exception as e:
        return (f"한국고문서자료관 자동조회 실패({e}) — 뷰어 직접 열람: {_AKS_BASE}/viewer/viewer.do "
                f"(분류 트리에서 소장처 탐색)")


@mcp.tool()
def nedb_search(query: str, db: str = "", max_results: int = 15, mode: str = "total", span: int = 8) -> str:
    """국사편찬위 한국사데이터베이스(db.history.go.kr) 통합검색 + 조선 사료 심층 판독(한강 강배 조사 실측 경로).
    mode: total=통합검색(기본) · law=법전·편람 조문(원문 제공 여부 판정) · record=등록류(座目 자동 필터) ·
    item=levelId 본문 판독(미공개/파싱실패 구분) · sibling=★형제 조 전수 스캔(조문을 열었으면 반드시 이어 호출) ·
    matrix=법전 수록 대조(쉼표구분 어휘 — 부재의 발견) · origin=어휘 연원('용어' 또는 '용어,영역') ·
    sjw=승정원일기(왕대 분포·최초 용례) · kyujanggak=규장각(목록+해제 동시 — 절목류는 해제에서 발견).
    aks=한국고문서자료관(소장처 172곳→분류→문서 면·썸네일) · jacar=일본 아시아역사자료센터(한→일 변환 검색·레퍼런스코드 메타 직행·±span×100 인접) ·
    gonghun=공훈전자사료관 독립유공자(query=이름 검색→mngNo 숫자 투입 시 공적조서·공훈록 본문 판독) ·
    i815=독립기념관(키워드 목록 · detail.do URL=자료 본문 · '사전:이름/번호'=한국독립운동인명사전 전기·생몰·훈격) ·
    ktv=KTV e영상역사관(키워드 목록→ehistory view URL 투입 시 영상 해설·상영정보 판독, KOGL) ·
    earchive=국편 전자사료관(키워드 목록→'키워드|순번' 투입 시 상세: 열람·이용조건·등록번호) ·
    commons=위키미디어 공용(키워드 목록→File URL 투입 시 라이선스·원 소장처·설명 판독) ·
    jsg=장서각(키워드 목록→청구기호 K2-…/URL 투입 시 서지·해제 전문 판독) ·
    un=UN 디지털도서관(키워드 목록→recid/URL 투입 시 요약·주제·언어별 PDF 직링크) ·
    oldnews=신문아카이브(키워드 목록 · CNTS/URL=색인어·관련기사 · '본문:키워드[|1905-1910]'=OCR 전문+연대) ·
    much=역사박물관(→idnbr/URL 투입 시 재질·공공누리·설명) ·
    indy=판결문(이름→상세 URL 투입 시 죄명·주문·사건개요·원문 뷰어) ·
    nzarch=NZ기록원(R번호=상세 메타) ·
    heritage=국가유산(키워드 목록 — 국보·보물·사적+딥링크. cpno 상세는 기관 식별 편차로 일부만)
    (query=소장처명 또는 L-ID·분류ID·'분류ID/문서ID').
    판정 우선: '601건'이 아니라 '492건이 座目'을 반환한다. 한자 원표기 병행 권장."""
    if mode == "aks":
        return _aks_mode(query)
    if mode == "jacar":
        return _jacar_mode(query.strip(), span, max_results)
    if mode == "gonghun":
        return _gonghun_mode(query, max_results)
    if mode == "i815":
        return _i815_mode(query, max_results)
    if mode == "ktv":
        return _ktv_mode(query, max_results)
    if mode == "earchive":
        return _earchive_mode(query, max_results)
    if mode == "commons":
        return _commons_mode(query, max_results)
    if mode == "jsg":
        return _jsg_mode(query, max_results)
    if mode == "un":
        return _un_mode(query, max_results)
    if mode == "oldnews":
        return _oldnews_mode(query, max_results)
    if mode == "much":
        return _much_mode(query, max_results)
    if mode == "indy":
        return _indy_mode(query, max_results)
    if mode == "nzarch":
        return _nzarch_mode(query)
    if mode == "heritage":
        return _heritage_mode(query, max_results)
    if mode != "total":
        return _joseon_mode(query, mode, span, max_results)
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
def archives_search(query: str, max_results: int = 10,
                    year_from: int | None = None, year_to: int | None = None) -> str:
    """국가기록원 국가기록포털(archives.go.kr). 정식 OpenAPI(RSS) — data.go.kr '나라기록물정보 서비스'
    (15000153) 무료 키를 환경변수 ARCHIVES_API_KEY로 설정하면 서버가 자동 검색해 결과를 반환한다.
    키가 없으면 포털 열람 URL을 반환. 노획문서·정부기록. 공공누리(KOGL) 유형 확인 후 이용."""
    key = os.environ.get("ARCHIVES_API_KEY")
    portal = "https://www.archives.go.kr/next/newsearch/listSubjectDescription.do?query=" + _up.quote(query)
    if key:
        sk = key if ('%' in key) else _up.quote(key)  # data.go.kr Encoding키는 그대로, Decoding키는 인코딩
        yfilt = bool(year_from or year_to); yf, yt2 = (year_from or 0), (year_to or 9999)
        api = ("https://apis.data.go.kr/1741050/openapi/searcharc?serviceKey=" + sk
               + "&query=" + _up.quote(query) + f"&start=1&limit={50 if yfilt else min(max_results, 50)}")
        try:
            xml = _http_text(api, 20)
            if "searchError" not in xml and "<item>" in xml:
                def t(bl, x):
                    m = re.search(rf"<{x}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{x}>", bl, re.S)
                    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
                tot = t(xml, "total") or "?"
                items = re.findall(r"<item>(.*?)</item>", xml, re.S)
                if yfilt:
                    def _py(i):
                        m = re.search(r"\d{4}", t(i, "prod_year"))
                        return int(m.group(0)) if m else None
                    items = [i for i in items if (_py(i) and yf <= _py(i) <= yt2)]
                lines = [f"- {t(i,'title')[:90]} ({t(i,'prod_year')}) · {t(i,'prod_name')[:20]} "
                         f"[{'공개' if t(i,'is_open')=='1' else '비공개'}] {t(i,'link')}"
                         for i in items[:max_results]]
                ytag = f" [생산 {year_from or ''}~{year_to or ''} · 상위 50건 내 후처리·연대 미상 제외]" if yfilt else ""
                return (f"국가기록원 '{query}'{ytag} — 총 {tot}건" + (f" 중 연대 일치 {len(items)}건" if yfilt else "") + ":\n"
                        + ("\n".join(lines) or "(0건)")
                        + "\n공공누리(KOGL) 유형 확인 후 이용. 비공개 항목은 정보공개청구 대상.")
            m = re.search(r"<message>(.*?)</message>", xml, re.S)
            return _agent_browse("국가기록원", query, portal, f"API 오류: {m.group(1).strip() if m else '결과 없음'}")
        except Exception as e:
            return _agent_browse("국가기록원", query, portal, f"API 오류({e})")
    return _agent_browse("국가기록원", query, portal,
                         "OpenAPI 키(ARCHIVES_API_KEY, data.go.kr 15000153) 미설정")


@mcp.tool()
def nlk_search(query: str, collection: str = "total", category: str = "", max_results: int = 15,
               year_from: int | None = None, year_to: int | None = None) -> str:
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
        yfilt = bool(year_from or year_to); yf, yt2 = (year_from or 0), (year_to or 9999)
        base_api = ("https://www.nl.go.kr/NL/search/openApi/search.do?key=" + _up.quote(key)
                    + "&apiType=xml&srchTarget=total&kwd=" + _up.quote(query)
                    + f"&pageSize={50 if yfilt else min(max_results, 50)}&pageNum=1")

        def t(bl, x):
            m = re.search(rf"<{x}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{x}>", bl, re.S)
            return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""

        def parse(xml):
            tot = t(xml, "total") or "?"
            items = re.findall(r"<item>(.*?)</item>", xml, re.S)
            if yfilt:
                def _py(it):
                    m = re.search(r"\d{4}", t(it, "pub_year_info") or t(it, "pubYearInfo"))
                    return int(m.group(0)) if m else None
                items = [it for it in items if (_py(it) and yf <= _py(it) <= yt2)]
            matched = len(items)

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
            return tot, lines, matched
        try:
            # 이중채널 동시 수집: (A) 전체 소장자료 + (B) 자료유형(category) 정밀 — 상호보완
            total_xml = _http_text(base_api, 20)
            if "<error" in total_xml:
                m = re.search(r"<msg>(.*?)</msg>", total_xml)
                return f"NLK OpenAPI 오류: {m.group(1) if m else '?'} — NLK_API_KEY 확인." + _browse(open_url)
            a_tot, a_lines, a_matched = parse(total_xml)
            ylab = (f" [발행 {year_from or ''}~{year_to or ''} · 상위 50건 내 후처리·연대 미상 제외]" if yfilt else "")
            out = (f"국립중앙도서관 자동검색(전체 소장자료) '{query}'{ylab} — 총 {a_tot}건"
                   + (f" 중 연대 일치 {a_matched}건" if yfilt else "") + ":\n"
                   + ("\n".join(a_lines) or "(0건)"))
            if category:
                try:
                    cat_xml = _http_text(base_api + "&category=" + _up.quote(category), 20)
                except Exception:
                    cat_xml = "<error/>"
                if "<error" not in cat_xml:
                    b_tot, b_lines, _bm = parse(cat_xml)
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
    """서울기록원(archives.seoul.go.kr) 기록 단위 검색 — 시리즈·기록건 제목+상세 딥링크.
    query에 /item·/aggregation 상세 URL 투입 시 심층 판독: 식별번호(RG-SR-IT)·기술계층·법적지위·
    이용조건(judge_rights 투입)·기술 본문. 서울시 행정기록·시정사진·구술 등 지방기록물."""
    q = query.strip()
    deep = "https://archives.seoul.go.kr/catalog/result?regclass=ALL&query=" + _up.quote(q)
    if re.match(r"^https?://archives\.seoul\.go\.kr/(item|aggregation)/\d+", q):  # 상세 판독 — 도메인 한정
        try:
            b = _cached_text("seoulD:" + q, 24 * 3600, lambda: _http_text(q, 25), "기술계층")
            flat = _clean(b)
            pick = lambda rx: ((re.search(rx, flat) or [None, ""])[1] or "").strip()
            title = pick(r"<-\s*(.{2,90}?)\s+(?:기술계층|생산자)")
            sid = pick(r"식별번호\s+(\S{4,30})")
            layers = re.findall(r"기술계층\s+(\S{2,20}\([A-Za-z]+\))", flat)
            layer = layers[-1] if layers else ""  # 첫 일치는 브레드크럼 — 마지막이 본 기록의 계층
            legal = pick(r"법적지위\s+(\S{2,12})")
            use = pick(r"이용조건\s*이용유형\s*(.{2,40}?)\s*(?:이용주기|검색도구|공개|관련)")
            use_note = pick(r"이용주기\s*(.{5,160}?)\s*(?:검색도구|공개|관련)")
            desc = pick(r"상세정보\s+기술\s+([\s\S]{10,1500}?)\s+(?:생산이력|입수이력|보존이력|관련 기록|열람|공개된)")
            if not sid and not title and not desc:
                return f"상세 파싱 실패 — URL을 확인하거나 브라우저로 열람: {q}"
            meta = " · ".join(x for x in (f"식별번호 {sid}" if sid else "", layer,
                                          f"법적지위 {legal}" if legal else "") if x)
            return (f"서울기록원 상세 — {title or '(제목 미상)'}\n{meta}\n"
                    + (f"이용조건: {use}{f' — {use_note}' if use_note else ''}\n" if use else "")
                    + (f"【기술】\n{desc}\n" if desc else "") + f"원문: {q}\n"
                    + "※ 출처: 서울기록원 — 게재 시 출처 표기. 이용조건·법적지위를 judge_rights에 투입해 초판정.")
        except Exception as e:
            return f"서울기록원 상세 오류({str(e)[:60]}) — 브라우저로 열람: {q}"
    try:
        items = _c_seoul(q, min(max_results, 20))
        if items:
            return (f"서울기록원 '{q}' — {len(items)}건(시리즈·기록건):\n"
                    + "\n".join(f"- {it['title']}\n  {it['url']}" for it in items)
                    + f"\n전체 결과: {deep}\n※ 상세 URL을 query로 재투입 → 식별번호·이용조건·기술 본문 판독.")
        return _agent_browse("서울기록원", q, deep, "기록 미검출")
    except Exception as e:
        return _agent_browse("서울기록원", q, deep, f"자동조회 실패({e})")


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
        # 구 통합검색 개편(2026-11 실측) → 동일 재단 신 플랫폼(6·25전쟁 아카이브센터)으로 폴백
        total, cards = _kw_search({"keyword": query, "viewType": "archive"})
        kl = [f"- [{c['id']}] {c['title'][:90]}\n  {c['url']}" for c in cards[:10]]
        if kl:
            return (f"전쟁기념관 구 통합검색(archives.warmemo.or.kr)이 개편되어 결과를 내지 않습니다 — "
                    f"동일 재단(전쟁기념사업회)의 6·25전쟁 아카이브센터(koreanwar.or.kr, 협약기관)에서 "
                    f"'{query}' 검색 결과로 대체합니다 (총 {total}건):\n" + "\n".join(kl)
                    + f"\n※ 상세·인접 채굴: koreanwar_item. 구 사이트 직접 확인: {url}")
        return _agent_browse("전쟁기념관", query, url, "구 통합검색 개편(결과 구조 소멸) — 신 플랫폼(koreanwar.or.kr)도 0건")
    except Exception as e:
        return _agent_browse("전쟁기념관", query, url, f"자동조회 실패({e})")


# ── KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터 (협약기관 — MOU) : TNA-style structured toolset ──
_KW_DEPTH1 = {"수집": "00001041", "기증": "00001042", "기타": "00001047", "구입": "00001054",
              "기탁": "00001073", "제작": "00001125", "이관": "00001179", "차입": "00001410"}

# 후기 단계 전투 검색 앵커 — 서버 큐레이션(기관 전투 DB 아님). 사이트 DB(개전 초기 69건) 미수록 시기 보완.
# t=통설 전사 시기, x=교차검색 앵커(쿼리·기록군 제안 — 수치·전과 주장 없음). route.js 패리티.
_KW_ANCHORS = [
    (r"인천\s?상륙|仁川上陸|(?i:Inchon)", "인천상륙작전", "1950-09-15 ~ 09-19", "en 'Inchon landing' · NARA RG 127(해병)·RG 80 · TNA ADM 116"),
    (r"서울\s?수복", "서울 수복", "1950-09-22 ~ 09-28", "en 'Seoul recapture 1950' · koreanwar_search(scope=archive '서울 수복')"),
    (r"장진호|長津湖|长津湖|(?i:Chosin)", "장진호 전투", "1950-11-27 ~ 12-11", "en 'Chosin Reservoir' · NARA RG 127 · ia_search 'Chosin'"),
    (r"청천강|淸川江|清川江", "청천강 전투", "1950-11-25 ~ 12-02", "en 'Chongchon River' · NARA RG 407"),
    (r"흥남|興南|(?i:Hungnam)", "흥남 철수", "1950-12 중순 ~ 12-24", "en 'Hungnam evacuation' · NARA RG 80·RG 127"),
    (r"1[·.]4\s?후퇴", "1·4 후퇴(서울 재실함)", "1951-01-04", "en 'fall of Seoul 1951'"),
    (r"지평리|砥平里|(?i:Chipyong)", "지평리 전투", "1951-02-13 ~ 02-15", "en 'Chipyong-ni' · 프랑스대대 — gallica_search 병행"),
    (r"임진강\s?전투|글로스터|그로스터|(?i:Imjin)", "임진강 전투(글로스터)", "1951-04-22 ~ 04-25", "en 'Imjin River' · TNA WO 281(부대 전쟁일지) — tna_search"),
    (r"가평|加平|(?i:Kapyong)", "가평 전투", "1951-04-23 ~ 04-25", "en 'Kapyong' · 영연방(호주·캐나다) — tna_search·archives 교차"),
    (r"피의\s?능선", "피의 능선 전투", "1951-08-18 ~ 09-05", "en 'Bloody Ridge'"),
    (r"단장의\s?능선|(?i:Heartbreak)", "단장의 능선 전투", "1951-09-13 ~ 10-15", "en 'Heartbreak Ridge' · 프랑스대대 — gallica_search 병행"),
    (r"백마고지|白馬高地|白马高地", "백마고지 전투", "1952-10-06 ~ 10-15", "en 'White Horse Hill' · NARA RG 407"),
    (r"저격\s?능선|삼각\s?고지|상감령|上甘[嶺岭]", "저격능선·삼각고지 전투", "1952-10-14 ~ 11월", "en 'Sniper Ridge'·'Triangle Hill'"),
    (r"폭찹", "폭찹힐 전투", "1953-04 · 1953-07", "en 'Pork Chop Hill'"),
    (r"금성\s?전투|金城", "금성 전투", "1953-07-13 ~ 07-19", "en 'Kumsong offensive'"),
    (r"휴전|정전|판문점|(?i:Panmunjom)", "정전협정 조인(판문점)", "1953-07-27", "en 'Korea armistice' · koreanwar_search(scope=archive '정전')"),
]


_TTL_CACHE: dict = {}


def _cached_text(key, ttl_s, fn, marker=None):
    """느리게 변하는 조회의 인메모리 TTL 캐시 — route.js 패리티."""
    import time as _t
    hit = _TTL_CACHE.get(key)
    if hit and _t.time() - hit[0] < ttl_s:
        return hit[1]
    v = fn()
    # 마커(기대 구조)가 있는 정상 응답만 캐시 — 차단·점검 페이지의 6시간 오염 방지
    if v and len(v) > 100 and (marker is None or marker in v):
        _TTL_CACHE[key] = (_t.time(), v)
    return v


def _kw_anchor_lines(q):
    if not q:
        return []
    return [f"- [앵커] {n} ({t}) → {x}" for p, n, t, x in _KW_ANCHORS if re.search(p, q)][:5]



@mcp.tool()
def koreanwar_search(query: str, scope: str = "archive", page: int = 1, max_results: int = 10,
                     year_from: int = 0, year_to: int = 0, acquisition: str = "") -> str:
    """KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터(koreanwar.or.kr, 전쟁기념관재단 — 협약기관) 통합검색을 서버에서 직접 조회.
    결과카드(제목·archRfcd 영속 참조코드·생산기관·상위계층)를 파싱하며, 상위계층의 NARA Record Group을
    추출해 원본 역추적 링크를 제공한다. 55,000여 건: 문서·지도·사진·필름·음원·구술.
    서버측 필터(실측 검증): year_from/year_to=생산연도 범위, acquisition=수집구분(수집·기증·구입·기탁·
    제작·이관·차입·기타), max_results는 pageSize(10/20/50)로 자동 매핑. scope='battle'이면 전투정보
    DB(개전 초기 69전투 + 후기 단계 서버 앵커 16건 인천상륙~금성 — TNA WO 281·NARA RG 407 교차검증 앵커)를 대신 검색. 자료유형·연대·이용조건
    코드는 source_profile('koreanwar') 참조. KOREANWAR_API_TOKEN 설정 시 OpenAPI 공식 메타 채널(KOGL
    권리정보) 자동 병행. 한글 질의 권장(미군 원본도 한글 재기술 제목으로 히트)."""
    if scope.strip().lower() == "battle":
        list_url = _KW_BASE + "/warList.do"
        try:
            b = _cached_text('kw:warList', 6 * 3600, lambda: _kw_text(list_url), 'warDetail.do?warIdx=')
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
                anchors = _kw_anchor_lines(t)
                ab = ("\n\n[후기 단계 검색 앵커 — 서버 큐레이션(기관 전투 DB 아님), 시기는 통설 전사 기준]\n"
                      + "\n".join(anchors)) if anchors else ""
                return (f"6·25 전투정보 '{t or '(전체)'}' — {len(matched)}/{len(cards)}건:\n" + "\n".join(lines) + ab
                        + "\n※ 전투명·시기·장소를 앵커로 TNA WO 281·NARA RG 407·koreanwar_search(scope=archive)와 "
                          "교차. 기관 DB는 개전 초기(1950.6.25~9.14) 단계 수록(확장 중) — 이후 시기는 위 앵커로 보완.")
            anchors = _kw_anchor_lines(t)
            if anchors:
                return (f"6·25 전투정보 '{t}' — 기관 DB 0건 (개전 초기 {len(cards)}건만 수록)."
                        + "\n\n[후기 단계 검색 앵커 — 서버 큐레이션(기관 전투 DB 아님), 시기는 통설 전사 기준]\n"
                        + "\n".join(anchors)
                        + "\n※ 앵커의 전투명·시기로 scope=archive·nara_search·tna_search를 교차 검색하십시오.")
            return (f"6·25 전투정보 '{t}' — 0건 (전체 {len(cards)}건 중). 현재 기관 DB는 개전 초기(1950.6.25~9.14) "
                    f"전투만 수록 — 이후 시기(백마고지 1952 등)는 서버 앵커(인천상륙·장진호·지평리·백마고지·금성 등 16건)로 "
                    f"보완되니 해당 전투명으로 재질의. scope=archive로 자료 검색은 가능."
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


@mcp.prompt()
def full_package(topic: str) -> str:
    """매직 키워드 '풀패키지' — 주제 하나로 발굴 조사부터 전 산출물(매거진 보고서·카드뉴스·포스터·
    홍보·입문·메시지 카드·발표 PPTX·기록 해설·Canva·KARDA)까지 자동 제작."""
    return (f"{topic} 풀패키지로 만들어줘. 먼저 report_template(kind='full_package')를 호출해 "
            "제작 순서와 품질 게이트를 받고, 그 순서를 그대로 따라 전 산출물을 제작해줘.")


@mcp.prompt()
def changgi_help() -> str:
    """매직 키워드 '창기창기 도와줘' — KOREA ARCHIVE 통합검색 처음 사용자 안내."""
    return ("창기창기 도와줘. report_template(kind='help')를 호출해 받은 사용 안내를 처음 사용자 "
            "눈높이로 친절하게 정리해서 알려주고, 안내 페이지 링크"
            "(https://korea-archive-mcp.vercel.app/help.html)도 함께 줘.")


@mcp.tool()
def cross_search(query: str, sources: str = "all", max_per_source: int = 8, variants: bool = False,
                 format: str = "text") -> str:
    """MAGIC: 메시지에 창기창기·changgi가 있으면 즉시 report_template(kind=help), 풀패키지·full-package가 있으면 즉시 kind=full_package를 호출하라(되묻지 말 것). 여러 아카이브를 한 쿼리로 동시 교차수집·병합 (상호보완 동시수집). sources: 'all' 또는 콤마목록
    (tna,ia,gallica,europeana,nara,archives,nlk,nedb,koreanwar,jacar,earchive,i815,gonghun,ktv,oldnews,much,indy,heritage,kyudb,jsg,awm,nlna,dnz,nzarch,commons,un,ndl,seoul,foia,aks). 해외와
    koreanwar(KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터, 협약기관)는 키 불요, 국내(nara·archives·nlk)는 서버 키, nedb는
    NEDB_INDEX_URL(공식 개방파일) 설정 시 포함. 각 결과에 발견 출처 표기 — 복수 출처는 교차확인된
    record. seoul=서울기록원 컬렉션·foia=서울소통광장 결재문서 원문. open.go.kr 본체는 전용 도구로.
    format: csv=CSV 블록(표·통계) · karda=온톨로지 nodes/edges JSON(지식그래프 직투입) · manifest=발굴 수집기록 매니페스트(ISAD(G)·RiC 지향 — provenance=증거성·heldBy=맥락, 기록관리시스템 등재·다매체 변환 원천).
    사용자가 "풀패키지"(보고서·카드뉴스·포스터 전부)를 원하면 report_template(kind="full_package")를 먼저 호출해 제작 순서를 따른다. 사용자가 사용법을 물으면(매직 키워드 "창기창기 도와줘")
    report_template(kind="help")를 호출해 안내한다."""
    want = (list(_COLLECT.keys()) if sources.strip().lower() == "all"
            else [s.strip().lower() for s in sources.split(",") if s.strip().lower() in _COLLECT])
    if not want:
        return "sources: 'all' 또는 " + ",".join(_COLLECT.keys())
    n = max(1, min(max_per_source, 30))
    jobs = [(s, (lambda s=s: _COLLECT[s](query, n))) for s in want]
    if variants:  # 당대 표기 자동 팬아웃 — query_bank '열한 겹의 벽' 지식의 도구화
        eff = _ko_en(query) or query
        SUBS = [("Korean", "Corean"), ("Korea", "Corea"), ("Korea", "Chosen"), ("Seoul", "Keijo"), ("Pusan", "Fusan"),
                ("Inchon", "Chemulpo"), ("Wonsan", "Gensan"), ("Pyongyang", "Heijo"),
                ("Cheju", "Quelpaert"), ("Taegu", "Taikyu")]
        vs = []
        for a, b in SUBS:
            if len(vs) >= 2:
                break
            if re.search(rf"\b{a}\b", eff, re.I):
                vs.append((b, re.sub(rf"\b{a}\b", b, eff, count=1, flags=re.I)))
        for src in ("tna", "ia", "nara", "europeana"):
            if src not in want:
                continue
            for label, vq in vs:
                jobs.append((f"{src}·{label}", (lambda src=src, vq=vq: _COLLECT[src](vq, n))))
    items, stats = _collect_merged(jobs)
    items.sort(key=lambda it: -len(it["sources"]))
    if format == "manifest":  # 발굴 수집기록 매니페스트 — 발굴 행위 자체를 맥락·증거성 갖춘 현용기록으로(ISAD(G)·RiC 지향)
        recs = items[:30]
        now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        h = 7
        for c in query:
            h = (h * 31 + ord(c)) & 0x7FFFFFFF
        def rid2(it, i):  # karda 그래프와 동일 키 — 상호 참조
            return "rec:" + (f"{it['sources'][0].split('·')[0]}:{it['id']}" if it.get("id") else f"m{i}")
        man = {
            "@context": {"dcterms": "http://purl.org/dc/terms/", "rico": "https://www.ica.org/standards/RiC/ontology#",
                         "title": "dcterms:title", "date": "dcterms:date", "identifier": "dcterms:identifier",
                         "provenance": "dcterms:provenance", "accessUrl": "dcterms:source",
                         "heldBy": {"@id": "rico:hasOrHadHolder"}, "records": {"@id": "rico:hasRecordSetMember"}},
            "@type": ["DiscoveryManifest", "rico:RecordSet"], "standard": "ISAD(G)/RiC-oriented",
            "identifier": f"kad-{now[:10]}-{h:x}",
            "provenance": {  # 증거성 — 수집의 재현 가능한 기술(누가·무엇을·언제·어떻게)
                "query": query, "sources": ",".join(want), "variants": variants, "collectedAt": now,
                "tool": "KOREA ARCHIVE 통합검색 cross_search (python plugin)",
                "reproduce": f"cross_search(query={query!r}, sources={sources!r}, format='manifest')",
                "channelStats": stats},
            "records": [(lambda hb, dr: {
                "@type": "rico:Record", "node": rid2(it, i),
                "identifier": it.get("id") or None, "title": it["title"], "date": it.get("date") or None,
                "heldBy": [{"id": k, "name": ARCHIVE_META.get(k, {}).get("n", k), "country": ARCHIVE_META.get(k, {}).get("c", "")} for k in hb],  # 맥락 — 기관 정식명·국가
                "accessUrl": it.get("url") or None, "evidence": f"API 실조회 {now[:10]}",
                **({"partOf": _part_of(hb[0], it)} if _part_of(hb[0], it) else {}),
                **({"deepRead": dr} if dr else {})})(  # 증거성 — 판독 재현 호출문
                sorted({s.split("·")[0] for s in it["sources"]}),
                (DEEP_READ.get(sorted({s.split("·")[0] for s in it["sources"]})[0], lambda _: None)(it)))
                for i, it in enumerate(recs)],
        }
        man["recordsFixity"] = "sha256:" + _hl.sha256(json.dumps(man["records"], ensure_ascii=False).encode("utf-8")).hexdigest()  # 내장 무결성
        mj = json.dumps(man, ensure_ascii=False)
        fx = _hl.sha256(mj.encode("utf-8")).hexdigest()  # 고정성(fixity) — 전파 중 변조 검증
        return (f"발굴 수집기록 매니페스트 '{query}' — {len(recs)}건 (재현 가능·기관 등재용):\n"
                + "```json\n" + mj + "\n```"
                + f"\nfixity(sha256): {fx} — 위 JSON 바이트의 지문. 전파·보관본 대조 시 불일치=변조/손상."
                + "\n공개 지문 원장(골든 기록 주간 감시·개정 이력): https://korea-archive-mcp.vercel.app/fixity-ledger.json"
                + "\n※ 현용기록물로서의 발굴기록: provenance(질의·소스·시각·재현 호출)=증거성 · heldBy·식별자=맥락 · fixity=고정성. 이 JSON을 그대로 기록관리시스템·KARDA에 등재."
                + "\n※ 다매체 변환 사슬: 이 매니페스트 → report_template(kind=report/carousel/full_package)=보고서·카드뉴스 · format='karda'=지식그래프 · format='csv'=데이터셋."
                + "\n※ 지속가능성: 영속 식별자(archRfcd·NAID·levelId·R번호) 우선 인용 — URL이 썩어도 재발굴 가능. 채널 생존은 source_profile(health)·주간 CI가 감시. 권리는 judge_rights로 기록 단위 표시.")
    if format == "karda":  # 온톨로지 직출력 — 로컬 스킬 전용이던 KARDA 노드·엣지 지식의 서버화(웹·모바일 동등성)
        recs = items[:30]
        srcs = sorted({s.split("·")[0] for it in recs for s in it["sources"]})

        def rid(it, i):
            return "rec:" + (f"{it['sources'][0].split('·')[0]}:{it['id']}" if it.get("id") else f"m{i}")
        nodes = [{"id": "topic:" + query, "type": "topic", "label": query}]
        nodes += [dict({"id": "archive:" + s2, "type": "archive", "label": ARCHIVE_META.get(s2, {}).get("n", s2)}, **({"country": ARCHIVE_META[s2]["c"]} if ARCHIVE_META.get(s2, {}).get("c") else {})) for s2 in srcs]
        for i, it in enumerate(recs):
            nd = {"id": rid(it, i), "type": "record", "label": it["title"][:90]}
            if it.get("id"):
                nd["identifier"] = it["id"]  # manifest와 동일 식별자 — 상호 참조
            if it.get("date"):
                nd["date"] = it["date"]
            if it.get("url"):
                nd["url"] = it["url"]
            nodes.append(nd)
        edges = []
        ser_seen = set()
        for i, it in enumerate(recs):
            edges.append({"from": "topic:" + query, "to": rid(it, i), "rel": "FOUND"})
            po = _part_of(it["sources"][0].split("·")[0], it)
            if po:  # 계층 맥락 — series 노드·PART_OF 엣지(v1.72)
                sid = "series:" + po
                if sid not in ser_seen:
                    ser_seen.add(sid)
                    nodes.append({"id": sid, "type": "series", "label": po})
                edges.append({"from": rid(it, i), "to": sid, "rel": "PART_OF"})
            for s in sorted({x.split("·")[0] for x in it["sources"]}):
                edges.append({"from": rid(it, i), "to": "archive:" + s, "rel": "HELD_BY"})
        return (f"교차수집 '{query}' KARDA 온톨로지 — 채널별 [{' · '.join(stats)}] → "
                f"노드 {len(nodes)}·엣지 {len(edges)} (레코드 {len(recs)}건, 상한 30):\n"
                + "```json\n" + json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False) + "\n```"
                + "\n※ 그대로 KARDA·지식그래프 도구(Gephi·Neo4j·vis.js)에 투입. 한 레코드의 복수 HELD_BY=기관 교차확인. "
                  "권리 초판정: judge_rights. 인물 중심 그래프는 nedb_search(mode=gonghun, \"종합:이름\")과 결합.")
    if format == "csv":  # 분석 투입용 구조화 출력 — "자료로써 분석할 수 있게"
        def esc(v):
            return '"' + str(v if v is not None else "").replace('"', '""') + '"'
        def ridc(it, i):
            return "rec:" + (f"{it['sources'][0].split('·')[0]}:{it['id']}" if it.get("id") else f"m{i}")
        rows = [",".join(esc(x) for x in (ridc(it, i), "+".join(it["sources"]), it["title"], it["date"], it["id"], it["url"],
                                           _part_of(it["sources"][0].split("·")[0], it) or ""))
                for i, it in enumerate(items[:45])]
        return (f"교차수집 '{query}' CSV — 채널별 [{' · '.join(stats)}] → 병합 {len(items)}건 (45건 상한):\n"
                + "node,sources,title,date,id,url,partOf\n" + "\n".join(rows)
                + "\n※ 그대로 스프레드시트·KARDA 온톨로지(nodes/edges)·통계 분석에 투입 가능. 권리 초판정: judge_rights.")
    lines = [f"- [{'+'.join(it['sources'])}] {it['title'][:95]}"
             + (f" ({it['date']})" if it['date'] else "") + (f" {it['url']}" if it['url'] else "")
             for it in items[:45]]
    return (f"교차수집 '{query}' — 채널별 [{' · '.join(stats)}] → 병합 {len(items)}건 (복수출처 우선 정렬):\n"
            + ("\n".join(lines) or "(0)")
            + "\n※ [출처] 복수 표기 = 교차확인된 record. 국내(nara·archives·nlk)는 서버 키, nedb는 "
            "NEDB_INDEX_URL(공식 개방파일) 설정 시 포함. open.go.kr 본체(브라우저 전용)는 foia_search 전용 도구로.\n※ 발굴 우선 — 권리는 표시: 게재 전 judge_rights(참조코드·KOGL·naid)로 초판정. variants=True로 당대 표기(Corea·Chosen·Keijo…) 자동 팬아웃.\n※ 심층 판독 이어가기: [i815]→nedb_search(mode=i815, 상세URL) · [gonghun]→mode=gonghun(mngNo) · [ktv]→mode=ktv(view URL) · [earchive]→mode=earchive('키워드|순번') · [jacar]→mode=jacar(레퍼런스코드) · [seoul]→seoul_archives_search(상세URL) · [koreanwar]→koreanwar_item(archRfcd) · [nara]→judge_rights(naid).")


@mcp.tool()
def source_profile(institution: str = "list") -> str:
    """기관 자료·이용·활용구조 프로파일 — 발굴 전략 수립용. 자료구조(계층·분류·식별자·메타),
    이용구조(API·인증·쿼리문법·robots·권리), 활용구조(3대 부정합·키워드셋·교차매핑·인접확장·교차검증 조합).
    institution: 'list' 또는 키 (tna·nara·ia·gallica·europeana·nedb·archives·nlk·seoul·warmemo·foia);
    'health'=30채널 골든 질의 일괄 헬스체크(🟢🟡🔴+키 설정 상태)."""
    t = (institution or "list").strip().lower()
    if t == "health":  # 발굴 우선 원칙의 전제: 깨짐을 스스로 발견한다
        GOLD = {"tna": "Korea", "ia": "Korea", "gallica": "Corée", "europeana": "Korea", "nara": "Korea",
                "archives": "한국전쟁", "nlk": "한국전쟁", "nedb": "한강", "koreanwar": "장진호",
                "jacar": "Chosen", "earchive": "제주도", "i815": "안중근", "gonghun": "안중근", "ktv": "대한뉴스", "oldnews": "의병", "much": "판문점", "indy": "유관순", "heritage": "숭례문", "kyudb": "절목", "jsg": "의궤", "awm": "Kapyong", "nlna": "Korea", "dnz": "Korean War", "nzarch": "Korea", "commons": "Seoul 1950", "un": "Korea armistice", "ndl": "조선총독부",
                "seoul": "한강", "foia": "회의", "aks": "문중"}
        keys = {k: bool(os.environ.get(k)) for k in
                ("NARA_API_KEY", "ARCHIVES_API_KEY", "NLK_API_KEY", "EUROPEANA_API_KEY",
                 "KOREANWAR_API_TOKEN", "NEDB_INDEX_URL")}
        import time as _t
        def _probe(kv):  # 30채널 병렬 탐침 (Node Promise.all 패리티 — 순차 실행은 합산 수십 초)
            k, q = kv
            s = _t.monotonic()
            try:
                r = _COLLECT[k](q, 3)
                return (k, q, True, len(r), None, int((_t.monotonic() - s) * 1000))
            except Exception as e:
                return (k, q, False, 0, str(e)[:60], int((_t.monotonic() - s) * 1000))
        with _cf.ThreadPoolExecutor(max_workers=8) as ex:
            probed = list(ex.map(_probe, GOLD.items()))
        rows = []
        for k, q, ok, cnt, err, ms in probed:
            if ok:
                rows.append(f"{'🟢' if cnt else '🟡'} {k}: {cnt}건 · {ms}ms (질의 '{q}')"
                            + ("" if cnt else " — 연결 정상·결과/파싱 0"))
            else:
                rows.append(f"🔴 {k}: {err} · {ms}ms")
        return ("30채널 헬스체크 (골든 질의 실측):\n" + "\n".join(rows)
                + "\n\n서버 키·설정: " + " · ".join(f"{k}={'✓' if v else '✗'}" for k, v in keys.items())
                + "\n※ 🟡=연결 정상이나 0건(질의 특성 또는 파서 점검 필요) · 🔴=채널 실패(차단·타임아웃) · ms=채널 응답시간. "
                  "nedb ✗=개방파일 인덱스 미설정.")
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


# ── PlayMCP 응답 24KB 한도 — UTF-8 바이트 실측 공통 가드(여유 23,800B). route.js 패리티. ──
_LIMIT_B = 23800


def _guard_24k_all():
    import functools
    try:
        tools = mcp._tool_manager._tools  # mcp 1.x 내부 — requirements에서 mcp<2 고정
    except AttributeError:
        return
    for t in tools.values():
        fn = t.fn

        @functools.wraps(fn)
        def wrapped(*a, __fn=fn, **k):
            r = __fn(*a, **k)
            if isinstance(r, str):
                b = r.encode("utf-8")
                if len(b) > _LIMIT_B:
                    r = (b[:_LIMIT_B].decode("utf-8", "ignore")
                         + f"\n…[응답 24KB 한도 — {len(b)}B 중 절단. page·max_results로 분할 조회]")
            return r
        t.fn = wrapped


_guard_24k_all()

if __name__ == "__main__":
    mcp.run()
