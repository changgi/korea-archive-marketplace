#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""keywords_warmemo — 전쟁기념관 3대 부정합 대응 어휘층 + 분류 교차매핑
════════════════════════════════
전쟁기념관 (War Memorial of Korea) 국내 아카이브 발굴 어휘.
논문 3.3.1절 설계차원(linguistic / taxonomic / descriptive)을 국내 기관에 확장.
실증 검증: warmemo_search 통합검색으로 실측 — 카테고리별 건수 합계>0 확인.
Soli Deo Gloria.
"""

# ══════════ 언어적 부정합 (linguistic) — 실측 검증본 ══════════

# 한자 원표기 — Hanja original forms (19종)
L_HANJA = [
    "白馬高地",  # 백마고지 = White Horse Hill / Hill 395 (1952 전투) (hits=157)
    "義兵",  # 의병 = righteous army (구한말 항일 의병) (hits=45)
    "獨立軍",  # 독립군 = independence army (hits=2449)
    "光復軍",  # 광복군 = Korean Liberation Army (韓國光復軍) (hits=2440)
    "大韓帝國",  # 대한제국 = Korean Empire (1897-1910) (hits=347)
    "大韓民國",  # 대한민국 = Republic of Korea (hits=341)
    "勳章",  # 훈장 = military decoration/medal (hits=113)
    "記章",  # 기장 = service badge / 종군기장 (hits=17)
    "壬辰倭亂",  # 임진왜란 = Imjin War (1592 일본 침입) (hits=77)
    "火繩銃",  # 화승총 = matchlock musket (조선 화기) (hits=281)
    "銃劍",  # 총검 = bayonet (hits=8)
    "軍服",  # 군복 = military uniform (hits=35)
    "傷痍軍人",  # 상이군인 = disabled/wounded veteran (hits=505)
    "戰歿",  # 전몰 = killed in action / 전몰장병 (hits=2)
    "忠烈祠",  # 충렬사 = shrine to loyal war dead (hits=9)
    "國軍",  # 국군 = ROK Armed Forces (hits=405)
    "陸軍",  # 육군 = Army (海軍 해군 / 空軍 공군) (hits=4)
    "太極旗",  # 태극기 = Taegeukgi, national flag (한글 '태극기'도 실검증) (hits=543)
    "李承晩",  # 이승만 = Syngman Rhee (인물 hanja 색인) (hits=16)
]

# 일제식 표기 — Colonial-era Japanese forms (9종)
L_JPSTYLE = [
    "京城",  # 경성 = Keijō, 일제강점기 서울 명칭 (hits=4)
    "仁川",  # 인천 = Jinsen (일제식 독음), Inchon (hits=107)
    "朝鮮軍",  # 조선군 = Chōsen Army, 조선주둔 일본군 (hits=2638)
    "朝鮮總督府",  # 조선총독부 = Government-General of Korea (hits=728)
    "憲兵",  # 헌병 = Kempei, 일제 군사경찰 (hits=22)
    "日本軍",  # 일본군 = Japanese army (실검증 1977건) (hits=2659)
    "志願兵",  # 지원병 = (강제)지원병, 조선인 동원 (hits=1249)
    "學徒兵",  # 학도병 = student soldier (hits=1025)
    "大東亞戰爭",  # 대동아전쟁 = Greater East Asia War (일본측 명칭) (hits=5343)
]

# 옛 지명·행정명 — Old place & admin names (11종)
L_OLDPLACE = [
    "滿洲",  # 만주 = Manchuria (hits=20)
    "間島",  # 간도 = Kando/Jiandao, 독립군 활동지 (hits=6)
    "長津湖",  # 장진호 = Changjin/Chosin Reservoir (1950) (hits=783)
    "多富洞",  # 다부동 = Tabu-dong, 낙동강 방어전 (hits=647)
    "洛東江",  # 낙동강 = Nakdong River / Pusan Perimeter (hits=335)
    "鴨綠江",  # 압록강 = Yalu River (hits=232)
    "蓋馬高原",  # 개마고원 = Kaema Plateau (hits=232)
    "板門店",  # 판문점 = Panmunjom (정전회담) (hits=22)
    "三八線",  # 삼팔선 = 38th Parallel (hits=209)
    "龍山",  # 용산 = Yongsan, 기념관 소재지·주둔지 (hits=301)
    "咸鏡道",  # 함경도 = 옛 행정구역(평안도·황해도 등) (hits=1191)
]

# 옛한글·국한문 표기 — Old-Hangeul & mixed script (1종)
L_OLDHANGEUL = [
    "六·二五",  # 6·25 = 한국전쟁, '6·25전쟁실' 표기 (hits=1)
]

# 이표기·로마자 — Romanization & Western variants (5종)
L_ROMAN = [
    "Operation Chromite",  # 인천상륙작전 코드명 (NARA/TNA 교차검색) (hits=4)
    "Inchon",  # 인천 옛 로마자 (현행 Incheon) (hits=13)
    "White Horse Hill",  # 백마고지 / Hill 395 (hits=8)
    "Imjin River",  # 임진강 = Battle of the Imjin (WO 281, Glosters) (hits=21)
    "Pusan Perimeter",  # 낙동강 방어선 (미군 명칭) (hits=14)
]

# 연호·기년 — Era names & regnal dating (5종)
L_ERA = [
    "檀紀",  # 단기 = Dangi 연호 (檀紀4283=1950) (hits=9)
    "光武",  # 광무 = 대한제국 연호 (1897-1907) (hits=21)
    "隆熙",  # 융희 = 대한제국 연호 (1907-1910) (hits=6)
    "開國",  # 개국 = 조선 개국기년 (개국503년=1894) (hits=91)
    "昭和",  # 쇼와 = 일본 연호, 강점기 문서 기년 (hits=3)
]

# ══════════ 분류학적 부정합 (taxonomic) — 분류/컴렉션 교차 매핑 ══════════
# 전쟁기념관 아카이브 분류체계 (소장자료·전시·연구교육·기념관역사) (War Memorial of Korea Archive classification (Holdings / Exhibitions / Research-Education / Museum History)) — NARA RG_MAP 대응: code -> (설명, 교차 키워드)
CLASS_MAP = {
    "소장자료 > 유물일반": ("실물 유물(무기·훈장·군복·군기·문서) — 대다수가 hanja 원표기 유물명으로 색인, 유물번호 단위", ["火繩銃", "銃劍", "勳章", "軍服", "太極旗", "記章"]),
    "소장자료 > 사진/필름": ("사진·필름 원판 — 상당수가 미군(NARA RG 111) 유래, 전투·부대·인물 사진", ["인천상륙작전", "白馬高地", "日本軍", "獨立軍", "낙동강"]),
    "소장자료 > 영상/음원": ("동영상·음원 자료 (기록영상·군가·증언 녹음)", ["6·25전쟁", "군가", "기록영상"]),
    "소장자료 > 구술자료": ("참전용사·유가족 구술 증언 채록", ["구술", "참전용사 증언", "장진호", "白馬高地"]),
    "소장자료 > 인물": ("인물 카드 — 성명 hanja 병기 색인 (참전 장병·독립운동가)", ["李承晩", "義兵", "獨立軍", "勳章"]),
    "전시 > 상설전시 (전쟁역사실·6·25전쟁실·해외파병실·국군발전실·기증실·야외)": ("상설 전시실 단위 — 고대~근현대~한국전쟁~해외파병으로 시대·주제 구획", ["壬辰倭亂", "6·25전쟁", "해외파병", "國軍", "베트남"]),
    "전시 > 특별전시": ("기획·특별전 (연도·주제별)", ["義兵", "大韓帝國", "獨立軍", "광복"]),
    "연구·교육 (교육자료·학예지·학술회의·도록·소장자료집·해설자료)": ("연구간행물·도록·교육자료 — 논문·전시도록에 상세 서지", ["壬辰倭亂", "獨立軍", "大韓帝國", "학예지", "소장자료집"]),
    "기념관역사 (타임라인·행사이야기[추모·개막·방문·문화·기타행사])": ("기념관 자체 연혁·행사 기록 — 사료보다 기관활동 기록", ["추모행사", "개막행사", "타임라인"]),
}

# ══════════ 기술관행적 부정합 (descriptive) — 검색 관행 노트 ══════════
DESC_NOTES = [
    "유물 중심 박물관 아카이브라 대다수 유물명(勳章·火繩銃·軍服 등)이 한자 원표기로 색인됨 — 한글 검색과 한자 검색이 서로 다른 결과를 내므로 두 표기를 모두 질의해야 함(예: 백마고지 vs 白馬高地는 사진/필름 건수 차이).",
    "전쟁을 '한국전쟁'이 아니라 '6·25전쟁'으로 표기하며 상설전시실 이름도 '6·25전쟁실'. 중점검색은 '6·25' 또는 '六·二五' 병행.",
    "기술 단위가 문서 편철이 아니라 유물번호(accession no.) 단위 개별 오브젝트 — 시리즈/편철 기반 검색이 아닌 키워드 통합검색으로 접근.",
    "사진/필름 상당수가 미군 출처(NARA RG 111 Signal Corps, RG 342 USAF)라 원 캡션이 영어 로마자(Inchon, Chosin, Hill 395)일 수 있음 — 국문 배틀명과 미군 로마자·Hill 번호를 함께 검색하고 NARA와 교차검증.",
    "연호·기년이 혼재: 한국전쟁 이전 유물·문서는 檀紀(단기, 檀紀4283=서기1950)·干支·開國기년, 강점기 문서는 明治·大正·昭和 일본 연호로 기재될 수 있음.",
    "인물 카테고리는 성명을 한자로 병기 색인(李承晩 등) — 한글 성명과 한자 성명, 영문 로마자(Syngman Rhee)를 모두 시도.",
    "통합검색은 카테고리별 건수만 반환하는 브레드크럼 구조(소장자료>사진/필름:275건 형식) — 실제 항목 열람은 반환된 열어보기 URL로 이동해 카테고리를 좁혀야 함.",
    "의병·독립군·광복군 등 근현대 항일사 자료는 '전쟁역사실'·'특별전시'·'인물'에 분산 — 단일 카테고리가 아니라 소장자료+전시+연구교육을 교차로 훑어야 누락이 없음.",
]

# 그룹 등록: (id, 설계차원, 국문, 영문, 키워드리스트)
WMK_GROUPS = [
    ("WMK-L1", "linguistic", "한자 원표기", "Hanja original forms", L_HANJA),
    ("WMK-L2", "linguistic", "일제식 표기", "Colonial-era Japanese forms", L_JPSTYLE),
    ("WMK-L3", "linguistic", "옛 지명·행정명", "Old place & admin names", L_OLDPLACE),
    ("WMK-L4", "linguistic", "옛한글·국한문 표기", "Old-Hangeul & mixed script", L_OLDHANGEUL),
    ("WMK-L5", "linguistic", "이표기·로마자", "Romanization & Western variants", L_ROMAN),
    ("WMK-L6", "linguistic", "연호·기년", "Era names & regnal dating", L_ERA),
]


if __name__ == "__main__":
    _v = sum(len(g[4]) for g in WMK_GROUPS if "후보" not in g[1])
    _c = sum(len(g[4]) for g in WMK_GROUPS if "후보" in g[1])
    print(f"전쟁기념관: 언어 {_v}종" + (f"(+미검증 후보 {_c}종)" if _c else "") + f" / 분류맵 {len(CLASS_MAP)} / 관행노트 {len(DESC_NOTES)}")
