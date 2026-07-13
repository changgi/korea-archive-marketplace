#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""keywords_nedb — 국사편찬위원회 한국사데이터베이스 3대 부정합 대응 어휘층 + 분류 교차매핑
════════════════════════════════
국사편찬위원회 한국사데이터베이스 (National Institute of Korean History — Korean History Database (NEDB)) 국내 아카이브 발굴 어휘.
논문 3.3.1절 설계차원(linguistic / taxonomic / descriptive)을 국내 기관에 확장.
실증 검증: nedb_search로 실측 — 통합검색이 검색어를 색인한 DB를 반환(항목이 동일 DB군으로 수렴해 검증은 coarse). 용어는 모두 실존 역사표기.
Soli Deo Gloria.
"""

# ══════════ 언어적 부정합 (linguistic) — 실측 검증본 ══════════

# 한자 원표기 — Hanja original forms (22종)
L_HANJA = [
    "高宗",  # 고종 (Emperor Gojong) (hits=2)
    "純宗",  # 순종 (Emperor Sunjong) (hits=2)
    "大院君",  # 흥선대원군 (Heungseon Daewongun) (hits=2)
    "明成皇后",  # 명성황후=閔妃 (Empress Myeongseong) (hits=2)
    "伊藤博文",  # 이토 히로부미 (Ito Hirobumi) (hits=2)
    "安重根",  # 안중근 (An Jung-geun) (hits=2)
    "統監府",  # 통감부 (Residency-General) (hits=2)
    "朝鮮總督府",  # 조선총독부 (Government-General of Korea) (hits=2)
    "大韓帝國",  # 대한제국 (Korean Empire) (hits=2)
    "大韓民國臨時政府",  # 대한민국임시정부 (Korean Provisional Government) (hits=2)
    "獨立協會",  # 독립협회 (Independence Club) (hits=2)
    "東學",  # 동학 (Donghak) (hits=2)
    "東學農民運動",  # 동학농민운동 (Donghak Peasant Revolution) (hits=2)
    "義兵",  # 의병 (Righteous Army) (hits=2)
    "乙巳條約",  # 을사조약 (Eulsa Treaty, 1905) (hits=2)
    "甲午改革",  # 갑오개혁 (Gabo Reform, 1894) (hits=2)
    "衛正斥邪",  # 위정척사 (hits=2)
    "俘虜",  # 포로 (POW) (hits=2)
    "憲兵",  # 헌병 (military police) (hits=2)
    "光復軍",  # 광복군 (Korean Restoration Army) (hits=2)
    "反民特委",  # 반민특위 (Anti-National Acts Investigation Committee) (hits=2)
    "保安法",  # 보안법 (Security Law) (hits=2)
]

# 일제식 표기 — Colonial-era Japanese forms (6종)
L_JPSTYLE = [
    "京城",  # 경성=Seoul (hits=2)
    "京城府",  # 경성부 (Keijo-fu) (hits=2)
    "朝鮮",  # 조선=Korea (Chosen) (hits=2)
    "官報",  # 조선총독부 관보 (Kanpo) (hits=2)
    "京城地方法院",  # 경성지방법원 (Keijo District Court) (hits=2)
    "内鮮一體",  # 내선일체 (naisen ittai) (hits=2)
]

# 옛 지명·행정명 — Old place & admin names (8종)
L_OLDPLACE = [
    "漢城府",  # 한성부 (pre-京城 서울) (hits=2)
    "濟州牧",  # 제주목 (Jeju; Quelpart) (hits=2)
    "全羅道",  # 전라도 (Jeolla province) (hits=2)
    "咸鏡道",  # 함경도 (Hamgyong province) (hits=2)
    "東萊",  # 동래 (옛 부산, 왜관 소재) (hits=2)
    "仁川",  # 인천 (Chemulpo, Jinsen) (hits=2)
    "元山",  # 원산 (Gensan) (hits=2)
    "巨文島",  # 거문도 (Port Hamilton, 1885) (hits=2)
]

# 옛한글·국한문 표기 — Old-Hangeul & mixed script (5종)
L_OLDHANGEUL = [
    "皇城新聞",  # 황성신문 (1898–1910) (hits=2)
    "大韓每日申報",  # 대한매일신보 (The Korea Daily News) (hits=2)
    "뎨국신문",  # 제국신문 (帝國新聞; 옛한글 '뎨국') (hits=2)
    "독립신문",  # 독립신문 (The Independent, 1896) (hits=2)
    "죠션",  # 조선의 옛한글 표기 (hits=2)
]

# 이표기·로마자 — Romanization & Western variants (7종)
L_ROMAN = [
    "Corea",  # Korea 구표기 (hits=2)
    "Chosen",  # 조선/朝鮮 일본식 로마자 (hits=2)
    "Keijo",  # 경성=Seoul 일본식 로마자 (hits=2)
    "Fusan",  # 부산 일본식 로마자 (hits=2)
    "Quelpart",  # 제주도 서구 지도 표기 (hits=2)
    "Chemulpo",  # 제물포/인천 개항장 서구 표기 (hits=2)
    "Port Hamilton",  # 거문도 영국식 지명 (巨文島) (hits=2)
]

# 연호·기년 — Era names & regnal dating (8종)
L_ERA = [
    "光武",  # 광무 연호 (Gwangmu) (hits=2)
    "隆熙",  # 융희 연호 (Yunghui) (hits=2)
    "開國",  # 개국 기년 (Gaeguk era-count) (hits=2)
    "建陽",  # 건양 연호 (Geonyang, 1896) (hits=2)
    "崇禎紀元後",  # 숭정기원후 (Ming loyalist dating) (hits=2)
    "大正",  # 다이쇼 연호 (Taisho) (hits=2)
    "昭和",  # 쇼와 연호 (Showa) (hits=2)
    "檀紀",  # 단기 (Dangi) (hits=2)
]

# 기타 발굴어 — Other discovery terms (1종)
L_MISC = [
    "HUSAFIK",  # 주한미군사 (History of the U.S. Armed Forces in Korea) (hits=2)
]

# ══════════ 분류학적 부정합 (taxonomic) — 분류/컴렉션 교차 매핑 ══════════
# 한국사데이터베이스 시대별·자료유형별 DB 계열 분류 (NEDB period- and material-type-based DB series classification) — NARA RG_MAP 대응: code -> (설명, 교차 키워드)
CLASS_MAP = {
    "조선-연대기": ("조선시대 사료 DB — 연대기: 조선왕조실록·승정원일기·비변사등록·일성록 (한문 원문+부분 국역)", ["實錄", "承政院日記", "備邊司謄錄", "日省錄", "干支", "王代"]),
    "조선-각사등록": ("조선시대 사료 DB — 관찬 행정·법령: 각사등록·조선시대법령자료 (官署別 편철)", ["各司謄錄", "關文", "牒呈", "傳令", "法令", "官署"]),
    "근대-개항대한제국": ("한국 근대 사료 DB — 개항·대한제국: 주한일본공사관기록·통감부문서·한국근대사자료", ["統監府", "駐韓日本公使館記錄", "大韓帝國", "光武", "隆熙", "開港場"]),
    "근대-독립운동": ("한국 근대 사료 DB — 독립운동: 한국독립운동사자료·대한민국임시정부자료집·동학농민혁명자료총서", ["獨立運動", "臨時政府", "義兵", "東學", "光復軍", "獨立協會"]),
    "근대-일제행정": ("한국 근대 사료 DB — 일제 행정·사법: 조선총독부관보·일제감시대상인물카드·경성지방법원 검사국 문서", ["朝鮮總督府", "官報", "京城地方法院", "監視對象", "保安法", "治安維持法"]),
    "현대-미군정해방": ("한국 현대 사료 DB — 해방·미군정: 자료대한민국사·주한미군사(HUSAFIK)·포로신문보고서", ["HUSAFIK", "美軍政", "軍政廳", "俘虜", "포로신문", "解放"]),
    "현대-정부수립": ("한국 현대 사료 DB — 정부수립·과거청산: 반민특위조사기록·헌정사 자료 DB·자료대한민국사", ["反民特委", "制憲", "憲政", "大韓民國", "國會", "親日"]),
    "보조-인물지리": ("총설/보조 DB — 인물·지리·회사: 한국근현대인물자료·역사지리정보DB·근현대회사조합자료", ["人物", "履歷", "職官", "歷史地理", "會社", "組合"]),
    "보조-시각자료": ("보조 DB — 시각자료: 사진유리필름자료·삽화·그림엽서 (硝子乾板)", ["寫眞", "硝子乾板", "유리필름", "그림엽서", "삽화"]),
    "국외소재": ("중국·일본 소재 한국사 자료 DB — 해외 소장 한국 관련 사료", ["中國所在", "日本所在", "韓國關係史料", "燕行", "通信使"]),
}

# ══════════ 기술관행적 부정합 (descriptive) — 검색 관행 노트 ══════════
DESC_NOTES = [
    "시대별 계열(총설·고대·고려·조선·근대·현대) 아래 편찬 서명(개별 DB)으로 다시 나뉜다. 통합검색이 서명 단위 하위 DB로 흩어지므로, 원하는 사료군(예: 승정원일기)을 먼저 지정해 해당 DB 내에서 재검색해야 정밀도가 오른다.",
    "연대기 사료(실록·승정원일기·일성록)는 기사(記事) 단위로 왕대·연월일·干支(간지) 기년으로 색인된다. 날짜 검색 시 서기 대신 '고종 O년', 干支(예: 甲午·乙巳·辛未), 또는 음력 간지월일로 접근해야 한다.",
    "국역(번역문)이 제공되는 DB는 현대 한국어로 검색되지만, 국역이 없는 원문 전용 DB(각사등록 일부·조선총독부 문서 등)는 한자 정자(正字) 원표기로만 잡힌다. 같은 사건도 국역어와 한자원문어의 히트 집합이 다르므로 병행 검색이 필수.",
    "인명은 초명·자(字)·호(號)·시호(諡號)·개명·창씨명 등 이표기가 많다. 근현대인물자료·감시대상인물카드는 한자 정자 색인이 정확하며, 일제 문서는 일본식 인명·창씨개명 표기가 병존한다.",
    "일제강점기 자료(총독부 관보·판결문·인물카드)는 지명·기관명을 일본식 표기(京城·仁川=Jinsen)와 일본 연호(明治·大正·昭和)로 등록한다. 검색 시 식민지 행정명과 광복 후 한국명을 함께 시도해야 한다.",
    "조선 고문서는 崇禎紀元後 등 명(明) 연호 기반 유민(遺民) 기년, 대한제국기는 開國·建陽·光武·隆熙, 광복 후는 檀紀를 쓴다. 연도 정규화 없이 원 기년 표기로 검색하는 것이 누락을 줄인다.",
    "편철(編綴) 단위가 문서 낱건이 아니라 등록(謄錄)·책(冊)·건별 묶음이므로, 상위 서명·권차·문서종류(關·牒·報·訓令 등)를 알면 브라우즈로 좁히기 쉽다.",
    "포로신문보고서·주한미군사(HUSAFIK) 등 미국 원자료 계열은 영문·로마자 표기(Corea·Chosen·Keijo·Fusan)와 한자가 섞여 색인되므로, 로마자 이표기도 함께 질의하면 해외 소장 계열까지 포괄된다.",
]

# 그룹 등록: (id, 설계차원, 국문, 영문, 키워드리스트)
KH_GROUPS = [
    ("KH-L1", "linguistic", "한자 원표기", "Hanja original forms", L_HANJA),
    ("KH-L2", "linguistic", "일제식 표기", "Colonial-era Japanese forms", L_JPSTYLE),
    ("KH-L3", "linguistic", "옛 지명·행정명", "Old place & admin names", L_OLDPLACE),
    ("KH-L4", "linguistic", "옛한글·국한문 표기", "Old-Hangeul & mixed script", L_OLDHANGEUL),
    ("KH-L5", "linguistic", "이표기·로마자", "Romanization & Western variants", L_ROMAN),
    ("KH-L6", "linguistic", "연호·기년", "Era names & regnal dating", L_ERA),
    ("KH-L7", "linguistic", "기타 발굴어", "Other discovery terms", L_MISC),
]


if __name__ == "__main__":
    _v = sum(len(g[4]) for g in KH_GROUPS if "후보" not in g[1])
    _c = sum(len(g[4]) for g in KH_GROUPS if "후보" in g[1])
    print(f"국사편찬위원회 한국사데이터베이스: 언어 {_v}종" + (f"(+미검증 후보 {_c}종)" if _c else "") + f" / 분류맵 {len(CLASS_MAP)} / 관행노트 {len(DESC_NOTES)}")
