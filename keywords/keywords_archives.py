#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""keywords_archives — 국가기록원 3대 부정합 대응 어휘층 + 분류 교차매핑
════════════════════════════════
국가기록원 (National Archives of Korea (NAK)) 국내 아카이브 발굴 어휘.
논문 3.3.1절 설계차원(linguistic / taxonomic / descriptive)을 국내 기관에 확장.
실증 검증: archives_search(data.go.kr OpenAPI)로 실측 — 각 용어의 실제 히트수 확인(朝鮮總督府 77·鮮人 224·憲兵 102 등).
Soli Deo Gloria.
"""

# ══════════ 언어적 부정합 (linguistic) — 실측 검증본 ══════════

# 한자 원표기 — Hanja original forms (15종)
L_HANJA = [
    "朝鮮總督府",  # 조선총독부 = Government-General of Chosen (hits=77)
    "高等警察",  # 고등경찰 = Higher/political police (hits=14)
    "思想犯",  # 사상범 = thought criminal (political prisoner) (hits=1)
    "保安法",  # 보안법 = Security Law (used vs. independence activists) (hits=12)
    "內務局",  # 내무국 = Home Affairs Bureau (hits=1)
    "地方法院",  # 지방법원 = District Court (hits=1)
    "判決文",  # 판결문 = written judgment/verdict (hits=12)
    "恩給",  # 은급 = government pension (annuity records) (hits=52)
    "土地調査",  # 토지조사 = cadastral land survey (1910–1918) (hits=32)
    "民籍",  # 민적 = household register (pre-1923, later 戶籍) (hits=1)
    "創氏改名",  # 창씨개명 = forced Japanese-style name adoption (hits=2)
    "官報",  # 관보 = Official Gazette (hits=11)
    "大韓帝國",  # 대한제국 = Korean Empire (1897–1910) (hits=25)
    "統監府",  # 통감부 = Residency-General (1906–1910) (hits=10)
    "議政府",  # 의정부 = Korean Empire State Council (hits=6)
]

# 일제식 표기 — Colonial-era Japanese forms (6종)
L_JPSTYLE = [
    "京城府",  # 경성부 = Keijo-fu, colonial Seoul city government (hits=9)
    "鮮人",  # 선인 = colonial-era abbreviation for Korean person (hits=224)
    "半島",  # 반도 = 'the peninsula', colonial term for Korea (hits=30)
    "憲兵",  # 헌병 = military police (헌병경찰 rule 1910–1919) (hits=102)
    "巡査",  # 순사 = patrolman/policeman (hits=3)
    "供出",  # 공출 = forced wartime grain/goods requisition (hits=2)
]

# 옛 지명·행정명 — Old place & admin names (7종)
L_OLDPLACE = [
    "道知事",  # 도지사 = provincial governor (hits=2)
    "郡守",  # 군수 = county magistrate (hits=23)
    "面長",  # 면장 = township (myeon) head; 府郡面 admin units (hits=10)
    "京城",  # 경성 = Seoul (colonial name) (hits=92)
    "漢城",  # 한성 = Seoul (Korean Empire name) (hits=6)
    "京畿道",  # 경기도 = Gyeonggi Province (hits=28)
    "咸鏡北道",  # 함경북도 = North Hamgyong Province (hits=12)
]

# 이표기·로마자 — Romanization & Western variants (3종)
L_ROMAN = [
    "Chosen",  # 조선 (朝鮮) Japanese romanization of Korea (hits=7)
    "Keijo",  # 경성 (京城) Japanese romanization = Seoul (hits=1)
    "Corea",  # Korea (older Western/legation-era spelling) (hits=61)
]

# 연호·기년 — Era names & regnal dating (4종)
L_ERA = [
    "明治",  # 메이지 (Meiji) era — dates 1868–1912 (hits=127)
    "大正",  # 다이쇼 (Taisho) era — 1912–1926 (e.g. 大正8年=1919) (hits=164)
    "昭和",  # 쇼와 (Showa) era — 1926–1945 (hits=939)
    "檀紀",  # 단기 = Dangi calendar used by early ROK 1948–1961 (檀紀4281=1948) (hits=3)
]

# ══════════ 분류학적 부정합 (taxonomic) — 분류/컴렉션 교차 매핑 ══════════
# 생산기관별 기록물 계열 및 기록물분류기준표 / 정부기능분류체계(BRM) (Provenance-based record series (Records Classification Standard Table) and Business Reference Model (BRM)) — NARA RG_MAP 대응: code -> (설명, 교차 키워드)
CLASS_MAP = {
    "GGC-관방/총무": ("조선총독부 관방·총무 (Governor-General Secretariat: 訓令·例規·직원록)", ["朝鮮總督府", "政務總監", "官房", "職員錄", "訓令"]),
    "GGC-경무국": ("조선총독부 경무국 (Police Affairs Bureau: 치안·사상탄압·검열)", ["警務局", "高等警察", "思想犯", "治安維持法", "保安法", "出版法"]),
    "GGC-내무/지방": ("조선총독부 내무국·지방행정 (Home Affairs & local admin 道·府·郡·面)", ["內務局", "道知事", "郡守", "面長", "府郡面", "民籍"]),
    "GGC-재무국": ("조선총독부 재무국 (Finance: 세무·전매·은급)", ["財務局", "稅務", "專賣局", "恩給", "官報"]),
    "GGC-식산/농림": ("조선총독부 식산국·농림국 (Industry & Agriculture: 토지·임야조사·공출)", ["殖産局", "農林局", "土地調査", "林野調査", "地籍原圖", "供出"]),
    "GGC-학무국": ("조선총독부 학무국 (Education: 황국신민화·창씨개명·신사)", ["學務局", "皇國臣民", "創氏改名", "神社", "敎育"]),
    "GGC-법무/재판소": ("조선총독부 법무국·재판소 (Justice & Courts: 판결문·예심)", ["法務局", "高等法院", "覆審法院", "地方法院", "判決文", "豫審終結決定"]),
    "GGC-철도/체신": ("조선총독부 철도국·체신국 (Railway & Communications)", ["鐵道局", "遞信局", "郵便"]),
    "GGC-관보/통계": ("조선총독부 관보·통계연보 (Official Gazette & statistical yearbooks)", ["官報", "朝鮮總督府官報", "統計年報"]),
    "통감부·대한제국": ("통감부 및 대한제국 정부 기록 (Residency-General & Korean Empire ministries)", ["統監府", "理事廳", "度支部", "議政府", "光武", "隆熙"]),
    "독립운동판결문": ("독립운동 관련 판결문 컬렉션 (Independence Movement judgment records)", ["獨立運動", "判決文", "保安法違反", "三一運動", "治安維持法"]),
    "북한노획문서": ("한국전쟁기 노획문서 (Captured North Korean documents ↔ NARA RG 242)", ["鹵獲文書", "노획문서", "북한문서", "인민군"]),
    "미군정기록": ("재조선미육군사령부군정청 기록 (USAMGIK / 과도정부)", ["美軍政", "軍政廳", "過渡政府", "USAMGIK"]),
    "정부수립기록": ("정부수립·제1공화국 기록 (Govt establishment: 국무회의록·대통령기록·제헌)", ["國務會議錄", "大統領記錄", "制憲", "政府樹立", "李承晩"]),
}

# ══════════ 기술관행적 부정합 (descriptive) — 검색 관행 노트 ══════════
DESC_NOTES = [
    "편철(編綴) 단위: 일제·정부수립기 기록은 문서철(file/철) 아래 문서건(item/건)으로 편철됨. 국가기록원 검색은 철·건 이중 레벨 — 철 제목은 포괄적(예: '土地調査關係書類綴'), 건 제목이 구체적. 못 찾으면 상위 철 제목으로 다시 검색.",
    "생산기관·처리과 기준 분류: 주제가 아니라 생산기관(局)+처리과 기준으로 배열됨(기록물분류기준표 대·중·소분류). 특정 주제를 찾으려면 먼저 어느 局/課가 생산했는지 식별해야 함(예: 사상탄압→警務局, 판결→法務局).",
    "기년·연호: 생산연도가 明治·大正·昭和(일제), 光武·隆熙(대한제국), 檀紀(초기 ROK 1948–1961)로 기재됨. 검색·해석 시 西紀 환산 필요(大正8年=1919, 昭和20年=1945, 檀紀4281=1948).",
    "제목 원표기 보존: 문서철 제목이 원본의 국한문/日本式 한자 표기를 그대로 옮겨 등록됨. 현대 한글 검색으로는 매칭 실패가 잦으므로 원 한자 표제어(朝鮮總督府, 京城府, 判決 등)로 검색해야 함.",
    "관리번호 체계: 각 철에 관리번호가 부여되고 조선총독부 문서는 원본+마이크로필름 이중 관리. 관리번호·생산기관코드로도 조회 가능하며, 컬렉션(주제) 분류와 별개로 존재.",
    "형태별 유형: 기록물이 문서·도면·사진·필름·카드 유형으로 구분됨. 토지조사부·임야조사부·지적원도는 도면(圖面)/카드 유형이라 문서 텍스트 검색과 분리해 탐색해야 함.",
    "로마자·일본어 병기: 일부 finding aid·목록에서 지명이 일본식 로마자(Keijo, Fusan, Jinsen, Heijo)로 표기되거나 일본어로 기술됨. 영문 검색 시 Chosen/Corea/Chosun 이표기도 병행.",
    "노획문서·정부수립기 상호참조: 북한노획문서는 NARA RG 242와 상호참조되고, 미군정·정부수립 기록은 국무회의록·대통령기록 등 별도 컬렉션으로 분리 등록되므로 주제어와 컬렉션명을 함께 질의.",
]

# 그룹 등록: (id, 설계차원, 국문, 영문, 키워드리스트)
NAK_GROUPS = [
    ("NAK-L1", "linguistic", "한자 원표기", "Hanja original forms", L_HANJA),
    ("NAK-L2", "linguistic", "일제식 표기", "Colonial-era Japanese forms", L_JPSTYLE),
    ("NAK-L3", "linguistic", "옛 지명·행정명", "Old place & admin names", L_OLDPLACE),
    ("NAK-L4", "linguistic", "이표기·로마자", "Romanization & Western variants", L_ROMAN),
    ("NAK-L5", "linguistic", "연호·기년", "Era names & regnal dating", L_ERA),
]


if __name__ == "__main__":
    _v = sum(len(g[4]) for g in NAK_GROUPS if "후보" not in g[1])
    _c = sum(len(g[4]) for g in NAK_GROUPS if "후보" in g[1])
    print(f"국가기록원: 언어 {_v}종" + (f"(+미검증 후보 {_c}종)" if _c else "") + f" / 분류맵 {len(CLASS_MAP)} / 관행노트 {len(DESC_NOTES)}")
