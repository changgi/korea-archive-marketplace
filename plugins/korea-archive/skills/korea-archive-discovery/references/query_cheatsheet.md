# 쿼리 치트시트 (발췌 — 전체는 프로젝트 docs/02_query_corpus_v1.1.html)

## 발굴 우선 조합 Top 5 (비용 0·수확 최상)
1. archive.org: `identifier:111-adc*`
2. NARA: `("Chosen" OR "Keijo") newsreel` (+RG 242 필터)
3. NARA API: `recordGroupNumber=242` 전수 스캔
4. archive.org: `collection:universal_newsreels AND (korea OR seoul)`
5. JACAR: `引揚げ 朝鮮` (일본어)

## 지명 변형 (필수 병렬)
Seoul/Keijo/Kyongsong · Inchon/Jinsen/Chemulpo · Pusan/Fusan · Taegu/Taikyu · Taejon/Taiden ·
Pyongyang/Heijo · Wonsan/Genzan · Hungnam/Konan · Chongjin/Seishin · Cheju/Saishu/Quelpart ·
Koje-do · Chosin/Changjin · Yalu(압록강) · Naktong · Imjin · Suiho Dam(수풍댐)

## TNA 인용 역추적 시드 (검증됨)
FO 371/84053·84057·84076·84097·84130 · WO 281/1206·1211·1257 · CAB 128/17·18 ·
DEFE 4/33·38 · PREM 8/1405 · FO 371/84059·84081·92756·92847 · CAB 129/41 ·
FO 17/1659 · FO 262/785 · FO 46/533
→ 각 시드 ±15 인접 piece 순회 (실증: 84053="Annual political report for Korea 1949")

## NARA RG 교차 (Precision 90%+)
RG 59+Corea(구한말 국무부) · RG 84+Seoul · RG 226+Chosen(OSS) · RG 242+Chosen ·
RG 338+KMAG · RG 389+"Korean POW" · RG 469+ECA · RG 263+North Korea(CIA)

## 다국어
日: 朝鮮·京城·引揚げ·日本ニュース / 露: Корея·освобождение Кореи / 中: 光復軍·抗美援朝·上甘嶺 /
獨: Welt im Film Korea·Der Augenzeuge / 佛: Corée·bataillon français / 土: Kore Savaşı·Kunuri

## Gallica (프랑스 국립도서관 — 키 불요)
프랑스어 필수: Corée · Coréens · guerre de Corée · Séoul · Fusan · Tchosen · missionnaires Corée
구한말 프랑스 선교사·외교 문헌/사진의 최대 보고 ('Corée' 76,000+건 실측)

## Europeana (58개국 통합 — 무료 키: apis.europeana.eu)
query: Korea OR Corée OR Korea-Krieg OR Corea · qf=TYPE:VIDEO|IMAGE
독일 Welt im Film·이탈리아 Luce 등 유럽 기관 소장분 교차 확인용
