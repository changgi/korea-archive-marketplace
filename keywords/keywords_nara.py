#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""keywords_nara — NARA 전용 키워드 7그룹 + 온라인 우선 목록 + RG 28 교차 매핑
═══════════════════════════════════════════════════════════════
Paper Section 3.4 / Appendix B-2 — 그룹 키워드 140개(중복 제거 136),
RG × 교차 키워드 = 63개 결합 쿼리. 공통 22그룹과 합산 시 529개(중복 제거).
Soli Deo Gloria.
"""

US_GOV_AGENCIES = [
    "USAMGIK", "United States Army Military Government in Korea",
    "American Military Government Korea", "military government Korea",
    "KMAG", "Korean Military Advisory Group",
    "ECA Korea", "USOM Korea",
    "AID Korea", "ICA Korea", "FOA Korea", "Point Four Korea",
    "Korean Civil Assistance Command",
    "KCOMZ", "Korean Communications Zone",
    "Korean Augmentation", "KATUSA", "KATCOM", "Korean Service Corps",
    "United States Forces Korea", "USFK",
    "Far East Command Korea", "FECOM Korea", "CINCUNC Korea",
    "Korean base section", "Pusan logistical command",
    "Korean reconstruction",
]

US_MILITARY_UNITS = [
    "Eighth Army Korea", "8th Army Korea",
    "X Corps Korea", "10th Corps Korea",
    "I Corps Korea", "IX Corps Korea",
    "1st Cavalry Division Korea", "2nd Infantry Division Korea",
    "3rd Infantry Division Korea", "7th Infantry Division Korea",
    "24th Infantry Division Korea", "25th Infantry Division Korea",
    "40th Infantry Division Korea", "45th Infantry Division Korea",
    "1st Marine Division Korea", "187th Airborne Korea",
    "Task Force 77 Korea", "7th Fleet Korea",
    "Fifth Air Force Korea",
    "Far East Air Forces Korea", "FEAF Korea",
    "USS Missouri Korea", "USS Iowa Korea",
]

US_PEOPLE = [
    "MacArthur Korea", "Douglas MacArthur Korea",
    "Ridgway Korea", "Matthew Ridgway Korea",
    "Mark Clark Korea", "Maxwell Taylor Korea",
    "James Van Fleet Korea", "Walton Walker Korea",
    "Dean Acheson Korea", "Dean Rusk Korea",
    "John Foster Dulles Korea",
    "Truman Korea", "Eisenhower Korea", "Marshall Korea",
    "Muccio Korea", "John Muccio Korea",
    "Coulter Korea", "Almond Korea", "Oliver Smith Korea",
    "Willoughby Korea", "Stratemeyer Korea",
    "Joy Korea", "Harrison Korea",
    "Horace Allen Korea", "Lucius Foote Korea",
    "George Foulk Korea", "Owen Denny Korea",
    "Homer Hulbert Korea", "Horace Underwood Korea",
    "Shufeldt Korea", "Shufeldt treaty",
    "Korean American Treaty 1882",
    "Hodge Korea", "John Hodge Korea", "Archer Lerch Korea",
    "Taft-Katsura agreement", "Root-Takahira agreement Korea",
]

US_INTEL = [
    "CIA Korea", "OSS Korea", "CIC Korea",
    "Voice of America Korea", "Radio Free Asia Korea",
    "covert operations Korea",
    "G-2 Korea", "G-3 Korea", "G-4 Korea",
]

NARA_SERIES = [
    "Decimal File 795", "Decimal File 895", "Decimal File 695",
    "Korean War files",
    "Bureau of Far Eastern Affairs Korea",
    "Office of Northeast Asian Affairs Korea",
    "Office of Korean Affairs",
    "CINCFE Korea", "FEC Korea", "Theater Commander Korea",
    "captured enemy documents Korea", "ATIS Korea",
    "enemy documents Korea", "North Korean documents",
    "Korean War Project",
    "Signal Corps Korea", "reconnaissance photo Korea",
]

US_TREATIES = [
    "Korean American Treaty 1882",
    "Mutual Defense Treaty Korea",
    "Status of Forces Agreement Korea", "Status of Forces Korea",
    "Korean free trade",
]

US_LIBERATION = [
    "Korean legation Washington", "Korean mission Washington",
    "Korean Commission Washington", "Syngman Rhee independence",
    "American expedition Korea 1871", "Low-Rogers expedition",
    "Korean expedition 1871", "Korea 1945 division",
    "McKenzie Korea", "Bethell Korea",
]

NARA_GROUPS = [
    ("N-01", "미군정·원조기관", "US Military Government and Aid Agencies", US_GOV_AGENCIES),
    ("N-02", "미군 부대 (한국전쟁)", "US Military Units (Korean War)", US_MILITARY_UNITS),
    ("N-03", "미국 인물", "US Persons", US_PEOPLE),
    ("N-04", "미국 정보기관", "US Intelligence Agencies", US_INTEL),
    ("N-05", "NARA 특유 시리즈·문서번호", "NARA-Specific Series and File Numbers", NARA_SERIES),
    ("N-06", "미국 조약·협정", "US Treaties and Agreements", US_TREATIES),
    ("N-07", "미국 소재 한국 관련 특화", "US-Located Korea-Specific Terms", US_LIBERATION),
]

# 온라인 우선 수집 (다운로드 가능 자료 집중, N-08)
ONLINE_PRIORITY = [
    "Korea", "Korean War", "Korean",
    "comfort women Korea", "Korean independence",
    "Korean POW", "Syngman Rhee",
    "USAMGIK", "Inchon landing",
    "photographs Korean War", "Signal Corps Korea",
    "captured enemy documents Korea",
]

# Record Group 28개 교차 매핑: RG번호 → (기관 설명, 교차 키워드)
RG_MAP = {
    59:  ("General Records of the Department of State (국무부 일반 기록)", ["Korea", "Korean", "Corea", "Seoul"]),
    84:  ("Records of the Foreign Service Posts (해외 공관 기록)", ["Korea", "Korean", "Seoul", "Pusan"]),
    127: ("Records of the U.S. Information Agency (미국 공보처)", ["Korea", "Korean"]),
    153: ("Records of the Office of the Judge Advocate General (법무감실)", ["Korea", "Korean War"]),
    218: ("Records of the U.S. Joint Chiefs of Staff (합동참모본부)", ["Korea", "Korean War"]),
    226: ("Records of the Office of Strategic Services (전략사무국 OSS)", ["Korea", "Korean", "Chosen"]),
    242: ("National Archives Collection of Foreign Records Seized (노획 외국 문서)", ["Korea", "Korean", "Chosen", "Corea"]),
    260: ("Records of U.S. Occupation Headquarters, WWII (SCAP 점령사령부)", ["Korea", "Korean"]),
    263: ("Records of the Central Intelligence Agency (중앙정보국)", ["Korea", "Korean", "North Korea"]),
    319: ("Records of the Army Staff, G-2 Intelligence (육군참모부 정보국)", ["Korea", "Korean War"]),
    330: ("Records of the Office of the Secretary of Defense (국방장관실)", ["Korea", "Korean War"]),
    332: ("Records of U.S. Theaters of War, WWII (전구 사령부)", ["Korea", "Korean"]),
    333: ("Records of International Military Agencies (국제 군사기구)", ["Korea"]),
    335: ("Records of the Office of the Secretary of the Army — AG (육군성 부관)", ["Korea", "Korean War"]),
    338: ("Records of U.S. Army Commands (육군 사령부 — KMAG 포함)", ["Korea", "Korean", "KMAG"]),
    340: ("Records of the Office of the Secretary of the Army (육군장관실)", ["Korea", "Korean War"]),
    342: ("Records of U.S. Air Force Commands (공군 사령부)", ["Korea", "Korean War"]),
    349: ("Records of Joint Commands — FECOM (극동사령부)", ["Korea", "Korean"]),
    389: ("Records of the Office of the Provost Marshal General (헌병감실 — 포로)", ["Korea", "Korean POW"]),
    407: ("Records of the Adjutant General's Office (부관참모실)", ["Korea", "Korean War"]),
    469: ("Records of U.S. Foreign Assistance Agencies (해외원조기관 — ECA)", ["Korea", "Korean", "ECA"]),
    490: ("Records of the Peace Corps (평화봉사단)", ["Korea"]),
    494: ("Records of U.S. Army Forces in Southeast Asia (동남아 주둔군)", ["Korea"]),
    500: ("Records of the Central Intelligence Agency — 추가 이관분", ["Korea", "Korean"]),
    523: ("Records of the U.S. Agency for International Development (USAID)", ["Korea"]),
    550: ("Records of U.S. Army, Pacific (태평양 육군)", ["Korea", "Korean"]),
    554: ("Records of General HQ, Far East Command (극동사령부 총사령부)", ["Korea", "Korean", "FECOM"]),
    556: ("Records of the Atomic Energy Commission — Foreign Intelligence (원자력위 해외정보)", ["Korea", "Korean"]),
}



if __name__ == "__main__":
    total = sum(len(g[3]) for g in NARA_GROUPS) + len(ONLINE_PRIORITY)
    rg_q = sum(len(v[1]) for v in RG_MAP.values())
    print(f"NARA 그룹+온라인우선: 원본 {total}개")
    print(f"RG 교차 결합 쿼리: {rg_q}개 (RG {len(RG_MAP)}개)")
