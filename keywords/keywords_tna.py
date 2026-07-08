#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════
  TNA Discovery 검색 쿼리 생성 모듈 — keywords_tna (참조 구현)
  국가기록원 기록관리교육센터 | 2026-07
═══════════════════════════════════════════════════════════════════
  [중요] 본 파일은 논문 3.5절·부록 B-3에 기술된 14개 전략 레이어의
  조합 생성 규칙을 코드로 재구성한 참조 구현(reference implementation)이다.
  운영 시스템의 로컬 원본 keywords_tna 모듈이 정본이며, 저장소 공개 전
  로컬 원본과 대조·병합할 것.

  구조: TNA_DEPT_CODES(부처 코드 체계) + CITATION_SEEDS(인용 역추적 시드)
        + generate() — 레이어별 규칙으로 1,222건(합계) 생성; 고유 1,210건
        (T-12 인용 시드가 T-13 반경-0에 구조적으로 재등장하는 중첩 12건 포함)
═══════════════════════════════════════════════════════════════════
"""
try:
    from .keywords_common import COMMON_GROUPS   # 패키지 경유 (import keywords)
except ImportError:
    from keywords_common import COMMON_GROUPS    # 단독 실행 (python keywords_tna.py)

# 그룹 ID → 키워드 리스트 빠른 접근
G = {gid: kws for gid, _ko, _en, _dim, kws in COMMON_GROUPS}

# TNA 14개 전략 레이어 — 구조 복원 (strategy_type: direct/indirect/citation/code)
# 개별 쿼리 전수(1,200+)는 코드 저장소(부록 참조)에 수록; 여기서는 레이어 구조와 대표 쿼리만 기재
TNA_LAYERS = [
    ("T-01", "direct",   "핵심 직접 검색", "Core Direct Search",
     "공통 G-01 핵심 키워드를 TNA Discovery 전문(full-text) 검색에 투입",
     ["Korea", "Corea", "Korean peninsula"]),
    ("T-02", "direct",   "한국전쟁 직접 검색", "Korean War Direct",
     "공통 G-02~G-06 전쟁 그룹을 영국군 관점 용어와 결합",
     ["Korean War", "Imjin River", "Gloucester Hill Korea"]),
    ("T-03", "direct",   "시대별 직접 검색", "Period-Specific Direct",
     "공통 G-07~G-10 시대 그룹 — 영국 외교문서의 시대별 표기 변화 반영",
     ["Corean treaty", "Japanese annexation Korea", "Korean armistice"]),
    ("T-04", "code",     "FO 371 정치문서 계열", "FO 371 Political Departments",
     "외무부 정치국 문서군 — 구체계(中Code10·日Code23)와 FK 등록코드 병용 열거",
     ["FO 371 Korea", "FO 371 Code 10", "FO 371 FK1015"]),
    ("T-05", "code",     "FO 기타 계열", "Other FO Series",
     "FO 17(중국 공관), FO 46(일본), FO 262(주일공사관), FO 483(한국 관련 확인 문서)",
     ["FO 17 Corea", "FO 262 Korea", "FO 483"]),
    ("T-06", "code",     "WO 육군부 계열", "WO War Office Series",
     "WO 281(한국전 전쟁일지), WO 308(전사 기록), WO madeleine 부대 기록",
     ["WO 281", "WO 308 Korea", "war diary Korea"]),
    ("T-07", "code",     "ADM·AIR 해공군 계열", "ADM and AIR Series",
     "ADM(해군부) 한국 해역 작전, AIR(공군부) 극동 항공작전",
     ["ADM Korea", "AIR Korea", "Fleet Air Arm Korea"]),
    ("T-08", "code",     "CAB·DEFE·PREM 최고정책 계열", "Cabinet, Defence, PM Series",
     "CAB(내각), DEFE(국방부), PREM(수상실) — 한국 정책 결정 문서",
     ["CAB Korea", "DEFE Korea", "PREM Korea"]),
    ("T-09", "code",     "FCO 현대 외교 계열", "FCO Modern Diplomatic Series",
     "1968년 이후 FCO 통합 문서군 — 한일수교·남북관계·경제협력",
     ["FCO 21 Korea", "FCO Korea normalization"]),
    ("T-10", "indirect", "영연방·식민지 경유", "Commonwealth and Colonial Indirect",
     "CO(식민지부)·DO(자치령부) 문서에서 홍콩·싱가포르 경유 한국 언급 발굴",
     ["CO Hong Kong Korea", "DO Korea Commonwealth"]),
    ("T-11", "indirect", "간접 맥락 키워드", "Indirect Contextual Terms",
     "공통 G-17 — Korea 표기 없이 기록된 문서 (Far East, 38th parallel 등)",
     ["Far East situation 1950", "Chinese intervention", "Panmunjom"]),
    ("T-12", "citation", "인용 역추적 시드", "Citation Back-tracing Seeds",
     "Farrar-Hockley·Yasamee & Hamilton 인용 참조코드를 시드로 확장 검색",
     ["FO 371/84053", "WO 281/1206"]),
    ("T-13", "citation", "시리즈 인접 확장", "Series-Adjacent Expansion",
     "검증된 시리즈의 인접 piece 번호 자동 순회 (Adaptive Mining 입력)",
     ["FO 371/840xx range crawl"]),
    ("T-14", "direct",   "시각·특수매체", "Visual and Special Media",
     "공통 G-20 + TNA 특유 사진·지도 컬렉션 (CN, WORK 계열)",
     ["Korea photographs", "Korea maps", "CN Korea"]),
]

# ═══════════════════════════════════════════════════════════════
# TNA 부처 코드 체계 (검증 코드: FO 371, WO 281 등 — 논문 표 B-2)
# lettercode → (국문 설명, 한국 관련 핵심 시리즈)
# ═══════════════════════════════════════════════════════════════
TNA_DEPT_CODES = {
    # 외무부 계열 (T-04, T-05)
    "FO 371": ("외무부 정치국 일반문서 — 1906–19년 한국파일은 中Code10·日Code23 하위 분류, 1920년 이후 FK 등록코드(FK1015 정치, FK1661 선전)", "political"),
    "FO 17":  ("외무부 중국 공관 문서 (구한말 한국 경유)", "legation"),
    "FO 46":  ("외무부 일본 문서 (병합 전후 한국)", "legation"),
    "FO 262": ("주일 영국공사관 문서", "legation"),
    "FO 483": ("한국 관련 확인 문서집 (Confidential Print)", "print"),
    # 육군부 계열 (T-06)
    "WO 281": ("한국전쟁 전쟁일지 (War Diaries)", "wardiary"),
    "WO 308": ("전사(戰史) 기록", "history"),
    "WO 32":  ("육군부 등록 문서 일반", "registry"),
    # 해·공군 계열 (T-07)
    "ADM 116": ("해군부 사건 문서 (Case Files)", "naval"),
    "ADM 1":   ("해군부 일반 서신", "naval"),
    "AIR 8":   ("공군참모총장 문서", "air"),
    "AIR 20":  ("공군부 미등록 문서", "air"),
    # 최고정책 계열 (T-08)
    "CAB 128": ("내각 회의록 (Conclusions)", "cabinet"),
    "CAB 129": ("내각 각서 (Memoranda)", "cabinet"),
    "DEFE 4":  ("참모총장위원회 회의록", "defence"),
    "DEFE 5":  ("참모총장위원회 각서", "defence"),
    "PREM 8":  ("수상실 문서 1945-1951 (Attlee)", "pm"),
    "PREM 11": ("수상실 문서 1951- (Churchill 이후)", "pm"),
    # 현대 외교 계열 (T-09)
    "FCO 21":  ("외무영연방부 극동국 1967-", "fco"),
    "FCO 51":  ("외무영연방부 조사국", "fco"),
    # 영연방·식민지 경유 (T-10)
    "CO 1030": ("식민지부 극동국 (홍콩·싱가포르)", "colonial"),
    "DO 35":   ("자치령부 일반문서", "dominion"),
    # 시각·특수매체 (T-14)
    "CN 3":    ("사진 컬렉션", "visual"),
    "WORK 10": ("공공건물·기념물 (한국전 기념)", "visual"),
}

# ═══════════════════════════════════════════════════════════════
# 인용 역추적 시드 (T-12) — 공간사·외교문서집 인용 참조코드
# (paper 검증 준거: Cumings, MacDonald, Farrar-Hockley,
#  Shaw, Yasamee & Hamilton, Park, Jung — validation_43.json)
# ═══════════════════════════════════════════════════════════════
CITATION_SEEDS = [
    # Farrar-Hockley, The British Part in the Korean War (1990, 1995)
    ("FO 371/84053", "Farrar-Hockley I"),
    ("FO 371/84057", "Farrar-Hockley I"),
    ("FO 371/84076", "Farrar-Hockley I"),
    ("FO 371/84097", "Farrar-Hockley I"),
    ("FO 371/84130", "Farrar-Hockley II"),
    ("WO 281/1206",  "Farrar-Hockley II"),
    ("WO 281/1211",  "Farrar-Hockley II"),
    ("WO 281/1257",  "Farrar-Hockley II"),
    ("CAB 128/17",   "Farrar-Hockley I"),
    ("CAB 128/18",   "Farrar-Hockley I"),
    ("DEFE 4/33",    "Farrar-Hockley I"),
    ("DEFE 4/38",    "Farrar-Hockley II"),
    ("PREM 8/1405",  "Farrar-Hockley I"),
    # Yasamee & Hamilton, DBPO Series (1991) — Korea 1950-1951
    ("FO 371/84059", "Yasamee & Hamilton"),
    ("FO 371/84081", "Yasamee & Hamilton"),
    ("FO 371/92756", "Yasamee & Hamilton"),
    ("FO 371/92847", "Yasamee & Hamilton"),
    ("CAB 129/41",   "Yasamee & Hamilton"),
    # Shaw (1999) — 영국-한국 관계사
    ("FO 17/1659",   "Shaw"),
    ("FO 262/785",   "Shaw"),
    ("FO 46/533",    "Shaw"),
]

# T-13 시리즈 인접 확장 파라미터: 시드 piece ± RANGE 순회 (Adaptive Mining 입력; RANGE=15에서 총 1,222건 생성 — 논문 "1,200건 이상" 실증)
ADJACENT_RANGE = 15


def _dedup(seq):
    seen = set(); out = []
    for q in seq:
        k = q.lower()
        if k not in seen:
            seen.add(k); out.append(q)
    return out

def _codes(kind):
    return [c for c, (_d, k) in TNA_DEPT_CODES.items() if k == kind]

def generate():
    """(layer_id, strategy_type, [queries]) 리스트 반환."""
    L = []

    # ── direct 계열 ────────────────────────────────────────────
    # T-01 핵심 직접: G-01 전체 + TNA 표기 관행 보정(Corea 지속 사용)
    t01 = list(G["G-01"]) + ["Corea Japan", "Corea China", "Corean peninsula"]
    L.append(("T-01", "direct", _dedup(t01)))

    # T-02 한국전쟁 직접: G-02~G-06 + 영국군 관점 재가중
    t02 = G["G-02"] + G["G-03"] + G["G-04"] + G["G-05"] + G["G-06"]
    t02 += ["Glosters", "Imjin battle", "Commonwealth Korea",
            "Hook Korea", "Second Battle of the Hook"]
    L.append(("T-02", "direct", _dedup(t02)))

    # T-03 시대별 직접: G-07~G-10 (영국 외교문서 표기 변화 반영)
    t03 = G["G-07"] + G["G-08"] + G["G-09"] + G["G-10"]
    L.append(("T-03", "direct", _dedup(t03)))

    # ── code 계열: 부처 코드 × 어휘 조합 ───────────────────────
    core6 = ["Korea", "Korean", "Corea", "Chosen", "Seoul", "Korean War"]

    # T-04 FO 371: 핵심 6 + 시대 어휘 전체와 결합 (한국 관련 최대 문서군)
    t04_vocab = core6 + G["G-09"] + G["G-10"] + G["G-18"]
    t04 = [f"FO 371 {kw}" for kw in _dedup(t04_vocab)] + ["FO 371 FK1015"]
    L.append(("T-04", "code", t04))

    # T-05 FO 기타(공관·확인문서): 구한말 어휘와 결합
    t05 = []
    for code in ["FO 17", "FO 46", "FO 262", "FO 483"]:
        for kw in core6 + G["G-19"][:8]:
            t05.append(f"{code} {kw}")
    L.append(("T-05", "code", _dedup(t05)))

    # T-06 WO: 전쟁일지 — 부대·전투 어휘와 결합
    t06 = []
    for code in ["WO 281", "WO 308", "WO 32"]:
        for kw in core6 + G["G-05"] + ["war diary", "Commonwealth Division",
                                        "29 Brigade", "Glosters"]:
            t06.append(f"{code} {kw}")
    L.append(("T-06", "code", _dedup(t06)))

    # T-07 ADM·AIR: 해·공군 작전 어휘와 결합
    naval_air = core6 + ["West coast blockade", "carrier operations Korea",
                         "Fleet Air Arm Korea", "HMS Triumph Korea",
                         "HMS Theseus Korea", "Sunderland Korea"]
    t07 = [f"{c} {kw}" for c in _codes("naval") + _codes("air")
           for kw in naval_air]
    L.append(("T-07", "code", _dedup(t07)))

    # T-08 CAB·DEFE·PREM: 최고정책 — 외교 정형구와 결합
    t08 = [f"{c} {kw}" for c in _codes("cabinet") + _codes("defence") + _codes("pm")
           for kw in core6 + G["G-18"]]
    L.append(("T-08", "code", _dedup(t08)))

    # T-09 FCO: 전후·현대 어휘와 결합
    t09 = [f"{c} {kw}" for c in _codes("fco")
           for kw in core6 + G["G-10"] + G["G-13"][:10]]
    L.append(("T-09", "code", _dedup(t09)))

    # ── indirect 계열 ──────────────────────────────────────────
    # T-10 영연방·식민지 경유
    t10 = [f"{c} {kw}" for c in _codes("colonial") + _codes("dominion")
           for kw in core6 + ["Hong Kong Korea", "Singapore Korea",
                              "Commonwealth Far East", "Korea refugees Hong Kong"]]
    L.append(("T-10", "indirect", _dedup(t10)))

    # T-11 간접 맥락: G-17 + 지역 총칭 확장
    t11 = G["G-17"] + ["Far East situation 1950", "Far East crisis",
                       "United Nations action Far East", "38th parallel crossing",
                       "Panmunjom talks", "Yalu bombing"]
    L.append(("T-11", "indirect", _dedup(t11)))

    # ── citation 계열 ──────────────────────────────────────────
    # T-12 인용 시드
    t12 = [ref for ref, _src in CITATION_SEEDS]
    L.append(("T-12", "citation", _dedup(t12)))

    # T-13 시리즈 인접 확장: 시드 piece ± ADJACENT_RANGE 순회
    t13 = []
    for ref, _src in CITATION_SEEDS:
        series, piece = ref.rsplit("/", 1)
        base = int(piece)
        for p in range(max(1, base - ADJACENT_RANGE), base + ADJACENT_RANGE + 1):
            if p != base:
                t13.append(f"{series}/{p}")
    L.append(("T-13", "citation", _dedup(t13)))

    # ── T-14 시각·특수매체 (direct) ────────────────────────────
    t14 = G["G-20"] + [f"{c} Korea" for c in _codes("visual")] + \
          ["Korean War memorial UK", "Korea photographs Commonwealth"]
    L.append(("T-14", "direct", _dedup(t14)))

    return L

def summary():
    layers = generate()
    total = 0
    by_type = {}
    print(f"{'ID':<6}{'유형':<10}{'쿼리 수':>8}")
    print("─" * 26)
    for lid, st, qs in layers:
        print(f"{lid:<6}{st:<10}{len(qs):>8}")
        total += len(qs)
        by_type[st] = by_type.get(st, 0) + len(qs)
    print("─" * 26)
    print(f"{'합계':<16}{total:>8}")
    for st, n in sorted(by_type.items()):
        print(f"  {st:<12}{n:>6}")
    return total

if __name__ == "__main__":
    print(f"전략 레이어: {len(TNA_LAYERS)}개 (논문 표 B-2)")
    _all = [q for _, _, qs in generate() for q in qs]
    print(f"레이어 합계 {len(_all)}건 / 고유 {len(set(_all))}건 "
          f"(전략 간 의도적 중첩 {len(_all)-len(set(_all))}건: "
          f"T-12 시드는 T-13 반경-0 순회에 재등장 — 수집기 실행 단계에서 dedup)")
    summary()
