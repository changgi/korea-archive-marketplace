"""
korea-archive MCP — 신규 도구 5종 구현
2026-08 실측 데이터 기반. 순수 파이썬, 외부 의존 없음.

사용:
    from korea_archive_tools import (
        query_scorecard, person_key_expand, decode_identifier,
        crosscheck_plan, preservation_referral,
    )
"""
from __future__ import annotations
import re
from typing import Any

# ─────────────────────────────────────────────────────────────
# 1. 검색어 성적표
# ─────────────────────────────────────────────────────────────

SCORECARD: dict[str, dict[str, Any]] = {
    # Europeana — 실측 2026-08
    "corea":      {"src": "europeana", "n": 6121,  "v": "noisy",
                   "traps": ["재즈 연주자 Chick Corea", "스페인어 의학용어 corea(무도병)",
                             "식물 학명 Anaxagorea", "바르셀로나 한식당 메뉴"],
                   "alt": ["Chemulpo", "Corea Japón", "Corea hermit nation", "coreana"]},
    "corée":      {"src": "europeana", "n": 47013, "v": "noisy",
                   "traps": ["도구가 Korea(영어)로 자동 번역함 — 넣은 대로 안 들어감"],
                   "alt": ["Coree", "Séoul", "Chemulpo"]},
    "chemulpo":   {"src": "europeana", "n": 58,   "v": "good",
                   "note": "1904 제물포 해전, 9개국 소장", "alt": []},
    "coreana":    {"src": "europeana", "n": 270,  "v": "good",
                   "note": "조선 채집 표본. koreana도 반드시 함께 넣을 것", "alt": ["koreana"]},
    "koreana":    {"src": "europeana", "n": 208,  "v": "good",
                   "note": "coreana와 겹치는 종이 거의 없음. 합계 478건", "alt": ["coreana"]},
    "wilfordi":   {"src": "europeana", "n": 31,   "v": "good",
                   "note": "가장 정확. 현호색 계열 집중", "alt": []},
    "fauriei":    {"src": "europeana", "n": 356,  "v": "mixed",
                   "traps": ["포리 신부는 일본·대만에서도 채집 — 조선분 비율 미확인"],
                   "alt": ["coreana fauriei"]},
    "oldhamii":   {"src": "europeana", "n": 296,  "v": "noisy",
                   "traps": ["올덤은 대만·일본 비중이 훨씬 큼", "Bambusa oldhamii = 대만 대나무"],
                   "alt": ["coreana", "wilfordi"]},
    "fusan":      {"src": "europeana", "n": 124,  "v": "noisy",
                   "traps": ["화물선 「Cap Delgado ex Fusan」(1959) 다수",
                             "Fusanus = 식물 학명"],
                   "alt": ["Chemulpo", "Fusan Korea"]},
    "vráz korea": {"src": "europeana", "n": 66,   "v": "good",
                   "note": "체코 대한제국 사진 컬렉션 전체", "alt": []},
    "hamel corea":{"src": "europeana", "n": 4,    "v": "good",
                   "note": "하멜 표류기 1672 독일어판", "alt": []},
    "corea korea 1919 independence":
                  {"src": "europeana", "n": 0,    "v": "zero",
                   "traps": ["영어 4단어 조합"], "alt": ["Corea 1919", "indépendance Corée"]},
    "koreana faurie":
                  {"src": "europeana", "n": 0,    "v": "zero",
                   "traps": ["학명+인명 조합은 금지"], "alt": ["koreana", "fauriei"]},
    # NARA
    "seoul korea 1945 photograph":
                  {"src": "nara", "n": 4250, "v": "good",
                   "note": "서울 거리 사진 컬렉션 2009-311~962", "alt": []},
    "chosen korea photographs album":
                  {"src": "nara", "n": 1957, "v": "noisy",
                   "traps": ["'album' 같은 일반명사가 노이즈를 부름"],
                   "alt": ["Seoul Korea 1945 photograph"]},
    # NARA — 신미양요 검증(2026-08)
    "rodgers colorado corea":
                  {"src": "nara", "n": 1580, "v": "good",
                   "note": "함대사령관+기함명 — 전투 당일 항해일지 도달(USS COLORADO·BENICIA·Palos)",
                   "alt": []},
    "korea 1871 expedition":
                  {"src": "nara", "n": 4054, "v": "noisy",
                   "traps": ["일반명사 'Expedition' — 상위 20건 전부 무관"],
                   "alt": ["Rodgers Colorado Corea", "USS Benicia log 1871", "Asiatic Squadron 1871"]},
    "log monocacy 1871":
                  {"src": "nara", "n": 590, "v": "good",
                   "note": "Monocacy 항해일지 3권 연속. 함선명만 넣은 것이 주효",
                   "alt": []},
    "신미양요":    {"src": "domestic", "n": 30, "v": "good",
                   "note": "국중도 10 + 국가기록원 20(1871 사진·그림, 한 파일 28건 연속)", "alt": []},
    # 국내
    "병인양요":    {"src": "domestic", "n": 12, "v": "good",
                   "note": "국중도 10 + 국가기록원 2, 전부 유효", "alt": []},
    "병인박해 베르뇌 다블뤼":
                  {"src": "domestic", "n": 0, "v": "zero",
                   "traps": ["인명 3개 조합"], "alt": ["병인양요", "베르뇌", "다블뤼"]},
}

_GENERIC = {"album", "photograph", "photographs", "document", "documents",
            "collection", "material", "conversation", "records", "file", "files"}
# NARA는 같은 계열에 두 형식을 함께 쓴다: "Log of U.S.S. X" / "Smooth Log of the USS X"
_FORM_VARIANTS = {"log", "smooth", "u.s.s.", "uss", "logbook"}
_COUNTRY = {"corea", "korea", "corée", "coree", "chosen", "tyosen"}
_TAXON_SUFFIX = ("ii", "iae", "ana", "anus", "anum", "ensis")

CITY_ALTERNATIVES = [
    "Chemulpo", "Tschemulpo", "Hemulpo", "Cemulpo",   # 제물포
    "Fusan", "Pusan", "Tsau-liang-hai",               # 부산
    "Keijo", "Séoul", "Seoul",                        # 서울
    "Quelpaert",                                      # 제주
    "Port Lazareff",                                  # 원산
    "Port Hamilton",                                  # 거문도
    "Soto Kongo",                                     # 외금강
    "Genzan", "Heijo", "Jinsen", "Chosin", "Changjin",
]


def query_scorecard(query: str, source: str = "any") -> dict[str, Any]:
    """검색어를 넣기 전에 성적을 조회한다."""
    q = query.strip()
    key = q.lower()

    if key in SCORECARD:
        e = SCORECARD[key]
        if source in ("any", e["src"]):
            return {
                "verdict": e["v"],
                "count": e["n"],
                "source": e["src"],
                "traps": e.get("traps", []),
                "better_alternatives": e.get("alt", []),
                "rationale": e.get("note", "실측치(2026-08)"),
                "measured": True,
            }

    # 규칙 기반 판정
    words = q.split()
    traps: list[str] = []
    alts: list[str] = []
    verdict = "unknown"

    if len(words) >= 4:
        verdict = "zero"
        traps.append(f"단어 {len(words)}개 — 검색엔진은 '전부 포함된 것'만 찾으므로 0건이 되기 쉽다")
        # 고유명·연도만 남긴다 (앞 두 단어를 자르면 엉뚱해진다)
        core = [w for w in words
                if (w[:1].isupper() or re.fullmatch(r"\d{3,4}", w))
                and w.lower().strip(",.\"'") not in _FORM_VARIANTS
                and w.lower().strip(",.\"'") not in _GENERIC
                and not re.fullmatch(r"(?:[A-Za-z]\.){2,}", w)]   # U.S.S. 같은 약어 제외
        if core:
            alts.append(" ".join(core[:2]))
            if len(core) > 1:
                alts.append(core[0])
        else:
            alts.append(" ".join(words[:2]))

    lowered = [w.lower().strip(",.\"'") for w in words]

    if any(w in _COUNTRY for w in lowered) and len(words) == 1:
        verdict = "noisy" if verdict == "unknown" else verdict
        traps.append("나라 이름 단독 — 동음이의어가 가장 많다")
        alts.extend(CITY_ALTERNATIVES[:4])

    if any(w in _GENERIC for w in lowered):
        verdict = "noisy" if verdict == "unknown" else verdict
        g = [w for w in lowered if w in _GENERIC]
        traps.append(f"일반명사 {g} 포함 — 고유명사 위주로 바꿀 것")
        alts.append(" ".join(w for w in words if w.lower().strip(",.\"'") not in _GENERIC))

    taxa = [w for w in lowered if w.endswith(_TAXON_SUFFIX)]
    propers = [w for w in words if w[:1].isupper() and w.lower() not in _COUNTRY]
    if taxa and propers:
        verdict = "zero"
        traps.append("학명과 인명을 섞으면 0건이 된다 — 하나씩 넣을 것")
        alts = taxa + propers

    if any(w in _FORM_VARIANTS for w in lowered) and len(words) > 1:
        traps.append("NARA는 같은 계열에 'Log of U.S.S. X'와 'Smooth Log of the USS X'를 "
                     "함께 쓴다 — 수식어를 빼고 고유명만 넣는 편이 안전하다")
        stripped = " ".join(w for w in words
                            if w.lower().strip(",.\"'") not in _FORM_VARIANTS
                            and w.lower() not in {"of", "the"}
                            and not re.fullmatch(r"(?:[A-Za-z]\.){2,}", w))
        if stripped and stripped != q:
            alts.append(stripped)

    hangul_names = re.findall(r"[가-힣]{2,4}", q)
    if len(hangul_names) >= 3:
        verdict = "zero"
        traps.append("인명 여러 개를 한꺼번에 넣으면 0건 — 하나씩")
        alts = hangul_names

    if verdict == "unknown" and 1 <= len(words) <= 2:
        verdict = "plausible"

    return {
        "verdict": verdict,
        "count": None,
        "source": source,
        "traps": traps,
        "better_alternatives": list(dict.fromkeys(a for a in alts if a and a != q)),
        "rationale": "미등재 검색어 — 규칙 기반 판정. "
                     "좋은 검색어는 보통 수십~수백 건에서 나온다; 수천 건이면 의심할 것.",
        "measured": False,
    }


# ─────────────────────────────────────────────────────────────
# 2. 인명 열쇠 확장
# ─────────────────────────────────────────────────────────────

SURNAME_VARIANTS = {
    "이": ["Lee", "Yi", "Rhee", "Ri", "Li"],
    "김": ["Kim", "Gim", "Kym"],
    "박": ["Park", "Pak", "Bak"],
    "최": ["Choi", "Choe", "Chwe"],
    "정": ["Chung", "Jung", "Jeong", "Chong"],
    "강": ["Kang", "Gang"],
    "조": ["Cho", "Jo", "Joh"],
    "윤": ["Yoon", "Youn", "Yun"],
    "장": ["Chang", "Jang"],
    "서": ["Suh", "Seo", "Sue", "Su"],
    "신": ["Shin", "Sin"],
    "권": ["Kwon", "Gwon"],
    "황": ["Hwang", "Whang"],
    "안": ["Ahn", "An"],
    "송": ["Song", "Sohng"],
    "유": ["Yu", "Yoo", "Ryu", "Lyu"],
    "홍": ["Hong", "Hng"],
    "한": ["Han", "Hahn"],
    "오": ["Oh", "O", "Oe"],
}

# Index to Personalities (U.S. Army Signal Corps Photographic Files)
INDEX_CELLS = [
    ("109921404", "Choi - Chun",           "1940-1954", ["최", "천", "정", "조", "전"]),
    ("109921405", "Chun - Clark",          "1940-1954", ["천", "전"]),
    ("109921479", "Hillard - Ho",          "1940-1954", ["호", "홍"]),
    ("109921480", "Ho - Hofto",            "1940-1954", ["호", "홍"]),
    ("109921542", "Renner - Rhoads",       "1940-1954", ["이(Rhee)"]),
    ("109921544", "Richardson - R...",     "1940-1954", []),
    ("109921572", "Soon - Speir",          "1940-1954", ["순", "손"]),
    ("109921580", "Sue - Sun",             "1940-1954", ["서", "손", "신"]),
    ("109921616", "Y - Yoksi",             "1940-1954", ["윤", "양", "유"]),
    ("109921617", "Yokhama - Youn",        "1940-1954", ["윤"]),
    ("109921618", "Young - Zans",          "1940-1954", []),
    ("109921724", "Shi-Chi - Silv...",     "1955-1981", []),
    ("109921751", "Yu - Zywocinski",       "1955-1981", ["유", "이(Yi)"]),
]

# Personalities 알파벳 색인 (국적·시대 무관, 알파벳만이 기준)
ALPHA_INDEX = [
    ("102702358", "Conselman, Dierdre - Crow, \"Jim\" Major"),
    ("102702375", "Hershfield, Harry - Hofstetter, Chas."),
    ("102702378", "Iakovos - Jespersons"),
    ("102702380", "Jones, Bobby - Kelly, Father"),
    ("102702381", "Kelly, John - Kiner, Ralph"),
    ("102702382", "King - Kozubek, Clara"),
    ("102702390", "Masahito, Prince - Mary, Queen"),
    ("102702394", "Mountbatten, Lord - Myun Chang, Dr. John"),
    ("102702398", "Parker - Percy, Lady Elizabeth"),
    ("102702402", "Ransome, Capt. Stan - Richardson, Brig. Gen. Wm. L."),
    ("102702409", "Serando, Dr. - Sims, Geo"),
    ("102702411", "Soames, Christopher - Starzel, Fran"),
    ("102702414", "Taylor, Gen. Maxwell - Togo"),
    ("102702416", "Truman, Harry (Continued) - Uzcudun, Paolino"),
    ("102702418", "Vining, Mrs. - Wallack"),
]

COLLECTOR_EPITHETS = {
    "faurie":  {"epithet": "fauriei",  "count": 356,
                "warning": "포리 신부는 일본·대만에서도 오래 채집 — 조선분 비율 미확인"},
    "oldham":  {"epithet": "oldhamii", "count": 296,
                "warning": "올덤은 대만·일본 비중이 훨씬 큼(Bambusa oldhamii = 대만 대나무)"},
    "wilford": {"epithet": "wilfordi", "count": 31,
                "warning": "가장 정확 — 현호색 계열 집중"},
}

KNOWN_PERSONS = {
    "서영해": {"variants": ["Seu Ring-Hai"], "note": "임시정부 파리 특파원. 『Autour d'une vie coréenne』(1929)"},
    "장면":   {"variants": ["Myun Chang", "Chang Myon", "John M. Chang"],
              "note": "NAID 102702394에 'Myun Chang, Dr. John'으로 수록 — Mountbatten과 같은 칸"},
    "이승만": {"variants": ["Syngman Rhee", "Rhee Syngman"],
              "note": "1,502건. 사진 예 127-R-1438(해병대 기록군)"},
}


def person_key_expand(name: str, type: str = "auto") -> dict[str, Any]:
    """인명 → 표기 변형 + 색인 구간 + 검색어 후보."""
    n = name.strip()
    variants: list[str] = []
    cells: list[dict[str, str]] = []
    caveats: list[str] = []
    queries: list[str] = []

    if n in KNOWN_PERSONS:
        k = KNOWN_PERSONS[n]
        variants += k["variants"]
        caveats.append(k["note"])

    # 한글 성씨 처리
    surname = n[0] if re.match(r"^[가-힣]", n) else None
    initials: list[str] = []
    if surname and surname in SURNAME_VARIANTS:
        romanized = SURNAME_VARIANTS[surname]
        variants += romanized
        initials += [r[0].upper() for r in romanized]
        given = n[1:]
        if given:
            caveats.append(
                f"이름 부분 '{given}'은 로마자로 옮겨 조합해야 한다 — "
                f"예: {romanized[0]}, [Given] / [Given] {romanized[0]}. "
                "띄어쓰기·붙여쓰기·하이픈 변형도 시도할 것."
            )
        caveats.append(
            f"'{surname}'는 로마자 표기가 {len(romanized)}가지({'·'.join(romanized)}) — "
            "각각 색인의 전혀 다른 칸을 가리킨다. 전부 시도할 것."
        )
        for naid, rng, period, sset in INDEX_CELLS:
            if any(surname in s for s in sset):
                cells.append({"naid": naid, "range": rng, "period": period,
                              "institution": "NARA Index to Personalities"})

    # 서양 채집자
    low = n.lower()
    for stem, info in COLLECTOR_EPITHETS.items():
        if stem in low:
            variants.append(info["epithet"])
            caveats.append(f"{info['epithet']}: {info['count']}건 — {info['warning']}")
            queries.append(f"coreana {info['epithet']}  # 조선분으로 좁히려면 겹칠 것")

    # 알파벳 색인 구간 추정 — 성씨 로마자 첫 글자 전부로 매칭
    if not initials:
        initials = [m.group(1) for v in variants
                    if (m := re.match(r"^([A-Z])", v))]
    for ini in dict.fromkeys(initials):
        for naid, rng in ALPHA_INDEX:
            lo = rng[0].upper()
            hi = rng.split(" - ")[-1][:1].upper() if " - " in rng else lo
            if lo <= ini <= hi:
                cells.append({"naid": naid, "range": rng, "period": "-",
                              "institution": "NARA Personalities (알파벳 색인)",
                              "matched_initial": ini})

    queries += list(dict.fromkeys(variants))[:12]

    caveats.append(
        "구간 경계에 걸리는 이름이 가장 위험하다 — 예: Kim은 "
        "102702381(Kelly,John–Kiner)과 102702382(King–Kozubek) 사이라 두 칸을 다 열어야 한다."
    )
    caveats.append(
        "기록군을 넓힐 것: 111(육군통신대)·127(해병대)·80(해군). 찍은 부대가 서랍을 정한다."
    )
    caveats.append(
        "독립운동가는 국내부터 — 독립기념관 독립운동인명사전(search.i815.or.kr)이 "
        "이명·가명·호를 함께 수록한다."
    )

    return {
        "variants": list(dict.fromkeys(variants)),
        "index_cells": cells,
        "caveats": caveats,
        "suggested_queries": list(dict.fromkeys(queries)),
    }


# ─────────────────────────────────────────────────────────────
# 3. 식별자 해독
# ─────────────────────────────────────────────────────────────

DECIMAL_TOPICS = {
    "895.00": "정치 (특히 625-711 = 1919.4~1928.6)",
    "895.01": "정부·사법부", "895.10": "공안", "895.20": "군사",
    "895.40": "사회·교육", "895.50": "경제·이민", "895.60": "산업·제조",
    "895.71": "통신·우편", "894.51": "총독부 재정 (일본 코드)",
}

RG_NAMES = {"111": "육군통신대", "127": "미 해병대", "80": "해군",
            "242": "노획문서(권리 D — 공개 금지)", "208": "전시정보국", "306": "USIA"}

MISSING_X = {
    "FO 881/9951X": ("병합 선언(1910.8.29)", "FO 881/9813 연차보고서"),
    "FO 881/5364X": ("제물포 토지 규정(1886.7.1)", "FO 93/26/3"),
    "FO 881/6050X": ("조선 여행기 Vebel(1889)", "FO 881/6089 캠벨"),
    "FO 881/5526X": ("영사재판 수수료 칙령(1887)", None),
    "FO 881/9038X": ("공사관 건물 보고서(1899)", "WORK 55/5/133·134"),
    "FO 881/9419X": ("칙령·법정 규칙(1905)", None),
}


def decode_identifier(identifier: str, system: str = "auto") -> dict[str, Any]:
    """식별자를 해독하고 인접 탐색 후보를 만든다."""
    s = identifier.strip()
    parts: list[dict[str, str]] = []
    neighbors: list[str] = []
    warnings: list[str] = []
    strategy = ""
    detected = system

    # NARA 참조코드  예: 127-GR-223-A164360
    m = re.match(r"^(\d{1,3})-([A-Z]{1,4})-(\d+)(?:-(\S+))?$", s)
    if m and system in ("auto", "nara_ref"):
        detected = "nara_ref"
        rg, series, topic, item = m.groups()
        parts = [
            {"segment": rg, "meaning": f"기록군 — {RG_NAMES.get(rg, '미확인')}"},
            {"segment": series, "meaning": "시리즈 구분"},
            {"segment": topic, "meaning": "주제 묶음 (다 차면 다음 번호로 넘어감)"},
        ]
        if item:
            parts.append({"segment": item, "meaning": "개별 건"})
        t = int(topic)
        neighbors = [f"{rg}-{series}-{t+d}" for d in (1, 2, 3)]
        strategy = ("주제 묶음 번호를 올려가며 검색한다. 127-GR-223→224→225→226 실증. "
                    "낱건 번호는 시간순이 아니라 주제순으로 섞여 있다.")
        if rg == "242":
            warnings.append("RG 242 노획필름 — 권리 지위 불명(D). 공개 금지.")

    # NAID (순수 숫자 6~10자리)
    elif re.match(r"^\d{6,10}$", s) and system in ("auto", "naid"):
        detected = "naid"
        v = int(s)
        parts = [{"segment": s, "meaning": "NAID — 그 자체로는 정보 없음"}]
        neighbors = [str(v + d) for d in (-3, -1, 1, 3)]
        strategy = ("계열마다 간격이 다르다: 127-GR 사진 계열은 3 간격, "
                    "Personalities 색인 계열은 1 간격. ±1과 ±3을 모두 넣어볼 것. "
                    "예측 검증 실증: 74248123 → 74248126이 실재(127-GR-225-9302).")
        warnings.append("같은 컬렉션이라도 검색어가 갈릴 수 있다(Chosen/Seoul). 번호대 훑기가 필수.")

    # TNA
    elif re.match(r"^[A-Z]{2,5}\s?\d+/\d+", s) and system in ("auto", "tna"):
        detected = "tna"
        dept = s.split()[0]
        parts = [{"segment": dept, "meaning": "부처 코드"},
                 {"segment": s[len(dept):].strip(), "meaning": "시리즈/piece"}]
        if s.upper().endswith("X"):
            info = MISSING_X.get(s.upper())
            warnings.append("X 접미어 — Missing at transfer(결락) 가능성이 매우 높다.")
            if info:
                warnings.append(f"사라진 것: {info[0]}" + (f" / 남은 짝: {info[1]}" if info[1] else ""))
        mm = re.search(r"(\d+)$", s)
        if mm:
            base = int(mm.group(1))
            head = s[: mm.start()]
            neighbors = [f"{head}{base+d}" for d in (-2, -1, 1, 2)]
        strategy = ("계열번호만 넣어 옆 훑기를 한다. 계열번호+주제어 조합은 0건이 되므로 금지. "
                    "실증: OCB 1/1259 → 부산항 해도 82건(1860~2003).")
        warnings.append("지도·도면은 원 문서철에서 추출돼 MPKK/MFQ/MPK/MR 계열로 이관됐을 수 있다.")

    # Gallica ark
    elif re.match(r"^(btv1b|bpt6k)[0-9a-z]+$", s) and system in ("auto", "gallica_ark"):
        detected = "gallica_ark"
        pre = "btv1b" if s.startswith("btv1b") else "bpt6k"
        kind = "도판·필사 계열" if pre == "btv1b" else "인쇄본 계열"
        parts = [{"segment": pre, "meaning": kind},
                 {"segment": s[len(pre):], "meaning": "자료 일련번호"}]
        strategy = ("같은 저작이라도 원본(btv1b)과 번역본(bpt6k)이 다른 제목 표기를 쓴다. "
                    "실증: Sangoku tsûran zusetsu(btv1b) vs San kokf tsou ran to sets(bpt6k).")
        warnings.append("필사본이면 OCR 불가 — 본문 검색으로는 안 걸린다(9층).")

    # 표본 번호
    elif re.match(r"^[A-Z]{1,3}\d{5,9}$", s) and system in ("auto", "specimen"):
        detected = "specimen"
        inst = {"E": "에든버러 왕립식물원", "K": "큐 왕립식물원",
                "P": "파리 자연사박물관"}.get(s[0], "미확인")
        num = re.search(r"\d+", s)
        parts = [{"segment": s[0], "meaning": f"기관 약자 — {inst}"},
                 {"segment": num.group(0), "meaning": "표본 일련번호"}]
        if num:
            b, w = int(num.group(0)), len(num.group(0))
            neighbors = [f"{s[0]}{str(b+d).zfill(w)}" for d in (-2, -1, 1, 2)]
        strategy = "연속 등록이 흔하다(E00677904~912 = 9점 연속). 앞뒤를 훑을 것."
        warnings.append("채집지·채집일은 목록에 없고 라벨에만 있다 — 최종 판정은 원본 확인 필요.")

    # 십진분류
    elif re.match(r"^\d{3}\.\d+", s) and system in ("auto", "decimal"):
        detected = "decimal"
        base = s[:6]
        topic = next((v for k, v in DECIMAL_TOPICS.items() if base.startswith(k[:6])), "미확인")
        parts = [{"segment": s, "meaning": f"미국 십진분류 — {topic}"}]
        strategy = "구간 검색이 단독 코드보다 낫다."
        warnings.append("894(일본)와 895(한국) 경계를 가로지른 편철이 있다"
                        "(NAID 87680287: 894.00/107–895.927/2). 895만 보면 앞부분을 놓친다.")
        warnings.append("별도로 394/395 체계도 존재한다(NAID 206540212). 소관 부처 미확인.")

    else:
        parts = [{"segment": s, "meaning": "인식되지 않는 형식"}]
        strategy = "체계를 지정해 다시 호출하거나, 소장 기관의 식별자 규칙을 먼저 확인할 것."

    return {"system": detected, "parts": parts, "neighbors": neighbors,
            "strategy": strategy, "warnings": warnings}


# ─────────────────────────────────────────────────────────────
# 4. 대조 계획
# ─────────────────────────────────────────────────────────────

DOMESTIC_HOLDINGS = [
    ("국사편찬위원회", "NARA 한국관계 문서"),
    ("통일원 자료실", "북한 노획문서"),
    ("국회도서관", "미 국무부 문서"),
    ("국방군사연구소", "한국전쟁 자료"),
    ("한림대·경남대", "미 NARA 문서(각각 수집)"),
    ("국가보훈부", "독립운동 자료"),
    ("6·25전쟁 아카이브센터", "55,206건 — koreanwar.or.kr"),
]


TOPIC_FOREIGN = {
    "병인양요": ["Roze Corea 1866", "French expedition Corea", "Ganghwa 1866",
                "Corée expédition 1866"],
    "신미양요": ["Rodgers Colorado Corea", "Shinmiyangyo",
                "United States Expedition to Korea 1871", "USS Benicia log 1871"],
    "운요호":   ["Un'yo Korea 1875", "Ganghwa incident 1875"],
    "제너럴셔먼호": ["General Sherman Korea 1866", "General Sherman Pyongyang"],
    "거문도":   ["Port Hamilton", "Port Hamilton occupation"],
    "을미사변": ["Queen Min assassination", "Miura Korea 1895"],
    "헤이그특사": ["Hague 1907 Korea", "Corea Hague peace conference"],
    "임시정부": ["Korean Provisional Government Shanghai", "Seu Ring-Hai"],
    "간도":     ["Chientao", "Kantō Korea boundary"],
    "장진호":   ["Chosin Reservoir", "Changjin"],
}


def crosscheck_plan(topic: str, period: str = "", known_sources=None) -> dict[str, Any]:
    """국내 먼저 → 해외 순서의 실행 계획을 만든다."""
    known_sources = known_sources or []
    t = topic.strip()
    short = t.split()[0] if t.split() else t

    # 3단계용 외국어 검색어 — 한글을 그대로 넣거나 영어와 섞으면 0건이다
    foreign_queries = list(TOPIC_FOREIGN.get(short, []))
    foreign_queries += [s for s in known_sources if not re.search(r"[가-힣]", s)]
    if not foreign_queries:
        foreign_queries = [
            "⚠ 외국어 검색어 미확보 — 2단계에서 먼저 얻을 것",
            "국내 학술자료의 병기 영문 제목(= …영문표기)을 확인",
            "관련 인명·함선명·부대명을 국내 연구사에서 추출",
        ]

    steps = [
        {"order": 1, "action": "국내 연구사 확인",
         "queries": [f"{short} 연구", f"{short} 사학사적 검토", f"{short} 연구사"],
         "targets": ["국립중앙도서관", "국가기록원", "RISS", "KCI"],
         "why": "무엇이 이미 밝혀졌는지 알아야 헛수고를 막는다. 발굴의 첫 단계는 검색창이 아니라 보고서다."},
        {"order": 2, "action": "번역본 존재 확인 — 그리고 영문 제목을 확보",
         "queries": [f"{short} 번역", f"{short} 역주", f"{short} 국역", f"{short} 기록"],
         "targets": ["국립중앙도서관", "한국고문헌종합목록"],
         "why": "이미 우리말로 나와 있을 수 있다. **국내 학술자료의 병기 영문 제목이 3단계 검색어가 된다** — "
                "실증: 「신미양요: 참전 미군 기록과 두 미군의 편지」의 병기 제목에서 "
                "'United States Expedition to Korea in 1871'을 얻었다."},
        {"order": 3, "action": "해외 원본 검색 — 반드시 외국어 검색어로",
         "queries": foreign_queries,
         "targets": ["NARA", "TNA", "Europeana", "Gallica"],
         "why": "⚠ 한글 주제어를 그대로 넣거나 영어와 섞으면 0건이다. "
                "2단계에서 얻은 영문 제목·인명·함선명·부대명을 쓴다. "
                "검색어는 짧게·하나씩·여러 번. query_scorecard로 먼저 검증할 것.",
         "key_hint": "지명·사건명보다 **인명·함선명·부대명**이 정확하다. "
                     "실증: 'Korea 1871 Expedition' 4,054건 상위 전부 무관 vs "
                     "'Rodgers Colorado Corea' → 전투 당일 항해일지 도달."},
        {"order": 4, "action": "국내 원사료와 대조",
         "queries": [short],
         "targets": ["승정원일기", "일성록", "추안급국안", "조선왕조실록", "한국사DB"],
         "why": "같은 날짜를 양쪽에서 찾는다. 한쪽만 보면 한쪽 이야기만 남는다."},
    ]

    warning = None
    yrs = re.findall(r"(1[0-8]\d\d)", f"{t} {period}")
    if yrs and min(int(y) for y in yrs) < 1896:
        warning = ("⚠ 음력/양력 주의 — 조선 기록은 시헌력(음력), 서양 기록은 그레고리력(양력)이다. "
                   "대한제국의 양력 공식 채택은 1896.1.1부터. "
                   "'○월 ○일'을 보면 어느 역법인지 먼저 확인하지 않으면 사건 순서가 뒤집힌다.")

    return {
        "topic": t,
        "steps": steps,
        "calendar_warning": warning,
        "domestic_holdings": [{"institution": a, "holds": b} for a, b in DOMESTIC_HOLDINGS],
        "notes": [
            "국내 DB는 짧은 검색어가 낫다 — 인명 3개 조합은 0건, 한 단어는 12건 전부 유효.",
            "한국사DB API는 HTTP 400이 잦다 — db.history.go.kr/search 공식 검색창으로 우회.",
            "미기술 자료를 발견하면 preservation_referral을 호출할 것.",
        ],
    }


# ─────────────────────────────────────────────────────────────
# 5. 목록에 올리기 안내
# ─────────────────────────────────────────────────────────────

def preservation_referral(material_type: str,
                          period: str = "",
                          owner_willing_to_donate: bool = False) -> dict[str, Any]:
    """미기술 자료를 만났을 때 어디로 연결할지."""
    institutions = [
        {"name": "국가기록원 (민간기록물 수집)",
         "contact": "archives.go.kr — 민간기록물 수집 담당",
         "accepts": "개인 편지·일기·메모·수첩·사진·포스터·간행물·회보·공문서 등 모든 형태. "
                    "시기 제한 없음(근·현대 중심). 해외 동포 기록도 대상.",
         "method": "기증 · 구입 · **사본수집**",
         "legal_basis": "공공기록물 관리에 관한 법률 제46조",
         "aftercare": "소독·탈산·수선·복원 후 항온항습 보존서고"},
        {"name": "국립중앙도서관 「책다모아」",
         "contact": "02-590-0700 (교환 4)",
         "accepts": "고문헌 필사본 — 저서·편지·**일기** 등. "
                    "「연구적 또는 심미적 중요성과 역사적 가치」 기준. 귀중서는 1659년 이전.",
         "method": "방문(평일 10:00~18:00) · 우편 · **우체국 택배(착불)**",
         "note": "등록 시 기증자명 표시"},
    ]

    if owner_willing_to_donate:
        primary = "기증 — 위 기관에 직접 연락"
    else:
        primary = ("**사본수집** — 원본은 그대로 두고 사본만 제작하거나 디지털화해 보존한다. "
                   "국가기록원은 「기증이 어려운 경우」를 위해 이 경로를 두고 있다.")

    return {
        "primary_route": primary,
        "institutions": institutions,
        "copy_collection_note":
            "기증하지 않아도 목록에는 오를 수 있다. 「병인양요 일록」(1989 발굴)은 "
            "개인 소장·미기증이었고 현재 소재가 확인되지 않는다 — 사본 한 부만 남았어도 읽을 수 있었다.",
        "why_it_matters":
            "10층의 두 가지 사라짐: ①물리적 소실은 되찾을 수 없지만 "
            "②목록에 없는 것은 되찾을 수 있다. 그 방법은 목록에 올리는 것뿐이다. "
            "2001년 궁내청 서릉부 목록이 있었기에 2011년 의궤 환수가 가능했다. "
            "그리고 ②는 기증되지 않으면 다음 세대에게는 ①이 된다.",
        "checklist": [
            "한국고문헌종합목록에서 이미 알려진 자료인지 먼저 확인",
            "동일 판본이 없으면 → 알려지지 않은 자료. 연락할 근거가 된다",
            "가치 판단은 기관이 한다 — 소장자가 혼자 고민할 필요 없다",
            f"자료 유형: {material_type}" + (f" / 시기: {period}" if period else ""),
        ],
    }


# ─────────────────────────────────────────────────────────────
TOOLS = {
    "query_scorecard": query_scorecard,
    "person_key_expand": person_key_expand,
    "decode_identifier": decode_identifier,
    "crosscheck_plan": crosscheck_plan,
    "preservation_referral": preservation_referral,
}

if __name__ == "__main__":
    import json
    for label, out in [
        ("query_scorecard('Corea')", query_scorecard("Corea")),
        ("query_scorecard('Corea Korea 1919 independence')",
         query_scorecard("Corea Korea 1919 independence")),
        ("person_key_expand('이승만')", person_key_expand("이승만")),
        ("decode_identifier('127-GR-223-A164360')", decode_identifier("127-GR-223-A164360")),
        ("decode_identifier('74248123')", decode_identifier("74248123")),
        ("decode_identifier('FO 881/9951X')", decode_identifier("FO 881/9951X")),
        ("crosscheck_plan('병인양요', '1866')", crosscheck_plan("병인양요", "1866")),
        ("preservation_referral('필사본 일기')", preservation_referral("필사본 일기")),
    ]:
        print(f"\n{'='*70}\n{label}\n{'='*70}")
        print(json.dumps(out, ensure_ascii=False, indent=2)[:1400])
