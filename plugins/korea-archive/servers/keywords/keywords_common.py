#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""keywords_common — 공통 키워드 22그룹 (Archive-Neutral Layer)
═══════════════════════════════════════════════════════════════
Paper: "An AI-based Systematic Methodology for Discovering and
Semantically Extracting Korea-related Records from Foreign Archives"
Section 3.3 / Appendix B-1 — 원본 412개 등재, 그룹 간 중복 제거 403개.

각 그룹은 3.3.1절의 설계 차원(linguistic / taxonomic / descriptive)을 가진다.
NARA·TNA 양측 모듈에서 재사용되는 아카이브 중립 어휘층.
Soli Deo Gloria.
"""

CORE = [
    "Korea", "Korean", "South Korea", "North Korea",
    "Corea", "Corean", "Choson", "Joseon", "Chosun", "Chosen",
    "Republic of Korea", "ROK", "DPRK", "Korean peninsula",
    "Hermit Kingdom", "Land of Morning Calm",
]

WAR_GENERAL = [
    "Korean War", "Korean conflict",
    "Korean armistice", "Korean truce", "Korean ceasefire",
    "Panmunjom", "Panmunjeom",
    "38th parallel", "38th parallel Korea",
    "Korean War casualties", "Korean War medal",
    "Korean War outbreak", "Korean War diary",
]

WAR_BATTLES = [
    "Inchon landing", "Incheon landing",
    "Pusan perimeter", "Busan perimeter",
    "Chosin reservoir", "Changjin reservoir",
    "Battle of Osan", "Battle of Taejon",
    "Naktong River", "Nakdong",
    "Battle of Unsan", "Chipyong-ni",
    "Heartbreak Ridge Korea", "Bloody Ridge Korea",
    "Pork Chop Hill", "Old Baldy Korea",
    "White Horse Korea", "Triangle Hill Korea",
    "Punch Bowl Korea", "Iron Triangle Korea",
    "Kunu-ri", "Battle of Wonju",
    "Imjin River", "Kapyong", "Kapyeong",
    "Maryang San", "Gloucester Hill Korea",
]

WAR_OPERATIONS = [
    "Operation Chromite",
    "Operation Killer Korea", "Operation Ripper Korea",
    "Operation Rugged", "Operation Dauntless Korea",
    "Operation Tomahawk Korea", "Operation Thunderbolt Korea",
    "Operation Roundup Korea", "Operation Courageous Korea",
    "Operation Strangle Korea",
    "Operation Big Switch", "Operation Little Switch",
    "Operation Glory Korea", "Operation Commando Korea",
    "Operation Ratkiller Korea", "Task Force Smith Korea",
]

WAR_UN_UNITS = [
    "United Nations Command Korea",
    "BCFK", "British Commonwealth Forces Korea",
    "Commonwealth Division Korea",
    "Turkish Brigade Korea", "Ethiopian Battalion Korea",
    "Colombian Battalion Korea", "Thai Battalion Korea",
    "Filipino Battalion Korea", "Greek Battalion Korea",
]

WAR_POW = [
    "Korean POW", "Korean prisoners of war",
    "POW Korea repatriation", "Koje-do", "Koje Island",
    "prisoner of war Korea", "Korean War prisoner exchange",
    "brainwashing Korea", "Korean War atrocity",
    "war crimes Korea", "missing in action Korea", "MIA Korea",
    "neutral nations Korea", "Indian custodial force Korea",
    "Korean War dead", "Korean War remains",
]

PREMODERN = [
    "Treaty of Chemulpo", "Treaty of Jemulpo", "Chemulpo",
    "Quelpart", "Port Hamilton Korea",
    "General Sherman Korea", "General Sherman incident", "Shinmiyangyo",
    "Emperor Gojong", "King Kojong", "Gojong",
    "Queen Min", "Empress Myeongseong", "Korean Empire",
    "Hague Conference Korea",
    "Sino-Japanese War Korea", "Russo-Japanese War Korea",
    "protectorate Korea", "annexation Korea 1910",
    "Ito Hirobumi", "An Jung-geun", "Eulsa Treaty",
    "Open door Korea", "Isabella Bird Korea", "Appenzeller Korea",
]

COLONIAL = [
    "Japanese occupation Korea", "Japanese annexation Korea",
    "Korean independence", "Korean independence movement",
    "March First Movement Korea", "March 1st Movement Korea", "Samil Movement",
    "Korean provisional government", "provisional government Shanghai Korea",
    "Kim Koo", "Kim Ku", "Kim Kyu-sik", "Kim Kiusic", "An Chang-ho",
    "Korean National Association", "comfort women Korea",
    "Korean forced labor", "Korean conscription",
    "Korean resistance", "Korean exile", "Korean Christians",
    "Tonghak", "Donghak", "Righteous Army Korea",
    "Governor-General Korea", "Chosen Governor",
    "Keijo", "Fusan", "Jinsen", "Gensan",
    "Korean YMCA", "Korea Daily News",
]

LIBERATION = [
    "trusteeship Korea", "Korean trusteeship",
    "38th parallel division", "Korea partition",
    "Korea occupation 1945", "Korea liberation 1945",
    "UNTCOK", "United Nations Temporary Commission Korea",
    "Korean election 1948", "Republic of Korea established",
    "DPRK established", "Korean interim government",
    "Yalta Korea", "Potsdam Korea", "Cairo Declaration Korea",
    "Japanese surrender Korea", "Soviet occupation Korea",
    "Jeju uprising", "Cheju uprising",
    "Yosu rebellion", "Yeosu rebellion",
    "Korean constabulary", "Rhee government",
]

POSTWAR = [
    "Korean unification", "Korean reunification",
    "DMZ Korea", "demilitarized zone Korea",
    "Neutral Nations Supervisory Commission Korea",
    "Military Armistice Commission Korea",
    "April Revolution Korea 1960", "military coup Korea 1961",
    "Korea Japan normalization", "Korean troops Vietnam",
    "Pueblo incident Korea", "Blue House raid 1968",
    "Kwangju", "Gwangju", "Gwangju uprising",
    "Korean Olympics 1988", "Seoul Olympics",
    "Korean democratization", "Korean economic miracle",
    "North Korea nuclear", "North Korea missile",
    "Korean summit", "six party talks Korea",
    "sunshine policy Korea", "KEDO",
    "Korean Air Lines 007", "KAL 007",
    "Rangoon bombing Korea",
    "Panmunjom Declaration", "Kaesong industrial",
]

PEOPLE_KOREAN = [
    "Syngman Rhee", "Rhee Korea",
    "Kim Il Sung", "Kim Il-sung",
    "Park Chung Hee", "Park Chung-hee",
    "Chun Doo Hwan", "Chun Doo-hwan",
    "Roh Tae-woo", "Roh Tae Woo",
    "Kim Young-sam", "Kim Dae-jung",
    "Kim Koo", "Kim Ku", "Kim Kyu-sik", "An Chang-ho",
    "Yo Un-hyong", "Lyuh Woon-hyung",
    "Song Chin-u", "Cho Man-sik", "Pak Hon-yong",
    "Paik Sun-yup", "Chung Il-kwon",
    "Kim Jong-il", "Kim Jong-un",
]

PLACES = [
    "Seoul", "Pusan", "Busan",
    "Pyongyang", "Pyeng Yang",
    "Inchon", "Incheon", "Kaesong", "Wonsan",
    "Hamhung", "Hungnam", "Chemulpo",
    "Taegu", "Daegu", "Taejon", "Daejeon",
    "Mokpo", "Kunsan", "Gunsan",
    "Kangnung", "Gangneung",
    "Suwon", "Chunchon", "Chuncheon",
    "Cheju", "Jeju", "Keijo",
    "Yalu River", "Yalu Korea", "Tumen River Korea",
    "Nakdong River", "Naktong", "Han River Korea",
    "Korea Strait", "Tsushima Korea",
]

ECONOMY = [
    "Korean economy", "Korean trade",
    "Korean aid", "Korean reconstruction",
    "Korean industry", "Korean investment", "Korean development",
    "Korean exports", "Korean imports",
    "Korean shipping", "Korean fisheries",
    "Korean mining", "Korean agriculture",
    "Korean textile", "Korean electronics",
    "Korean automobile", "Korean shipbuilding", "Korean steel",
    "Korean currency", "Korean won", "Korean debt",
    "Han River miracle", "Korean Five Year Plan", "Colombo Plan Korea",
]

INTEL = [
    "intelligence Korea",
    "signals intelligence Korea", "SIGINT Korea",
    "counterintelligence Korea",
    "psychological warfare Korea", "PSYWAR Korea",
    "propaganda Korea", "leaflet Korea",
    "North Korean espionage", "Korean spy",
]

HUMANITARIAN = [
    "Korean refugees", "Korean orphans", "Korean children",
    "Korean welfare", "Korean relief",
    "Red Cross Korea", "UNICEF Korea",
    "medical Korea", "hospital Korea",
    "war graves Korea", "Korean War remains recovery",
    "Korean civilian casualties", "Korean displaced persons",
    "adoption Korea", "Korean nurses",
]

CULTURE = [
    "missionary Korea",
    "Presbyterian Korea", "Methodist Korea", "Catholic Korea",
    "Korean church", "Korean Christians",
    "Korean education", "Korean university", "Korean school",
    "Korean language",
    "Korean art", "Korean ceramics", "Korean pottery",
    "Korean culture", "Korean heritage", "Korean customs",
    "Severance Korea", "Ewha", "Yonsei",
]

INDIRECT = [
    "Far Eastern Commission",
    "Chinese intervention Korea", "Chinese forces Korea",
    "Chinese Communist Korea", "Chinese People's Volunteer",
    "Peng Dehuai",
    "Soviet Korea", "Soviet occupation Korea",
    "Manchuria border", "Formosa Korea", "containment Asia",
]

DIPLOMATIC = [
    "Korean question", "Korean problem",
    "Korean situation", "Korean crisis",
    "Korean affairs", "Korean policy",
    "Korean settlement", "Korean political",
    "Korean boundary", "Korean frontier",
    "Korean government", "Korean minister",
    "Korean envoy", "Korean delegation", "Korean mission",
    "Korean king", "Korean emperor", "Korean court", "Korean nation",
]

COREA_COMPOUND = [
    "Corean government", "Corean treaty",
    "Corean king", "Corean court",
    "Corean minister", "Corean port",
    "Corean trade", "Corean customs",
    "Corean independence", "Corean concession",
    "Corean mining", "Coree",
]

VISUAL = [
    "photograph Korea", "photographs Korean War",
    "map Korea", "maps Korea", "chart Korea",
    "film Korea", "motion picture Korea", "newsreel Korea",
    "Korean War photograph", "Korean War film",
    "aerial photograph Korea",
]

TREATIES = [
    "Korean Armistice Agreement",
    "Korean peace treaty", "Korean trade agreement",
    "Treaty of Ganghwa", "Portsmouth Treaty Korea",
    "Geneva Conference 1954 Korea", "Korean normalization",
]

INTL_ORG = [
    "UNCURK", "UNTCOK", "UNKRA", "UNCACK", "UNCMAC",
    "United Nations Korea", "UN Command Korea", "UN Korean",
    "UN General Assembly Korea", "UN Security Council Korea",
    "NNSC Korea",
    "WHO Korea", "UNESCO Korea", "FAO Korea",
    "World Bank Korea", "IMF Korea",
]

# (그룹ID, 국문 라벨, 영문 라벨, 설계 근거 키, 리스트)
COMMON_GROUPS = [
    ("G-01", "핵심 직접 키워드", "Core Direct Terms", "linguistic", CORE),
    ("G-02", "한국전쟁 일반", "Korean War — General", "taxonomic", WAR_GENERAL),
    ("G-03", "한국전쟁 전투·고지", "Battles and Hills", "descriptive", WAR_BATTLES),
    ("G-04", "한국전쟁 작전명", "Operation Codenames", "descriptive", WAR_OPERATIONS),
    ("G-05", "유엔군·영연방 부대", "UN and Commonwealth Units", "taxonomic", WAR_UN_UNITS),
    ("G-06", "포로·실종·전쟁범죄", "POW, MIA, and War Crimes", "descriptive", WAR_POW),
    ("G-07", "구한말·개항기 (~1910)", "Late Choson and Open Ports", "linguistic", PREMODERN),
    ("G-08", "일제강점기 (1910–1945)", "Colonial Period", "linguistic", COLONIAL),
    ("G-09", "해방·분단 (1945–1950)", "Liberation and Division", "taxonomic", LIBERATION),
    ("G-10", "전후·냉전·현대 (1954~)", "Postwar and Cold War", "taxonomic", POSTWAR),
    ("G-11", "인물 — 한국", "Korean Persons", "linguistic", PEOPLE_KOREAN),
    ("G-12", "한국 지명 (역사적 표기 포함)", "Korean Place Names", "linguistic", PLACES),
    ("G-13", "경제·무역·원조", "Economy, Trade, and Aid", "taxonomic", ECONOMY),
    ("G-14", "정보·첩보·선전", "Intelligence and Propaganda", "descriptive", INTEL),
    ("G-15", "인도주의·의료·난민", "Humanitarian and Medical", "descriptive", HUMANITARIAN),
    ("G-16", "선교·교육·문화", "Mission, Education, Culture", "descriptive", CULTURE),
    ("G-17", "간접 키워드", "Indirect Terms (no 'Korea')", "descriptive", INDIRECT),
    ("G-18", "외교 용어·공식 표현", "Diplomatic Formulae", "descriptive", DIPLOMATIC),
    ("G-19", "Corea 구표기 복합", "Archaic 'Corea' Compounds", "linguistic", COREA_COMPOUND),
    ("G-20", "시각자료", "Visual Materials", "taxonomic", VISUAL),
    ("G-21", "조약·협정", "Treaties and Agreements", "taxonomic", TREATIES),
    ("G-22", "국제기구·유엔", "International Organizations", "taxonomic", INTL_ORG),
]

def common_total():
    seen = set()
    for _, _, _, _, kws in COMMON_GROUPS:
        for k in kws:
            seen.add(k.lower())
    return len(seen)

if __name__ == "__main__":
    raw = sum(len(g[4]) for g in COMMON_GROUPS)
    print(f"공통 22그룹: 원본 {raw}개 / 중복제거 {common_total()}개")
    for gid, ko, en, dim, kws in COMMON_GROUPS:
        print(f"  {gid} {ko:<24} {len(kws):>3}개")
