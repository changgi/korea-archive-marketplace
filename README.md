<div align="center">

# 🇰🇷 Korea Archive — Claude 플러그인

**전 세계 문서고에 흩어진 한국 기록을 찾고, 읽고, 결과물까지 만들어 주는 Claude 플러그인**

[![30개 문서고](https://img.shields.io/badge/문서고-30곳_·_9개국-1f6feb?style=for-the-badge)](#-어디서-찾아-주나요)
[![스킬 11종](https://img.shields.io/badge/전문_스킬-11종-8250df?style=for-the-badge)](#-플러그인에-들어-있는-전문-스킬-11종)
[![무료](https://img.shields.io/badge/이용-무료-d4a72c?style=for-the-badge)](#-설치하기)

[**소개 페이지**](https://changgi.github.io/korea-archive-marketplace/) · [**예제 15선**](https://changgi.github.io/korea-archive-mcp/examples.html) · [**30곳 탐방 시리즈**](https://changgi.github.io/korea-archive-mcp/series.html) · [**사용 안내**](https://korea-archive-mcp.vercel.app/help.html) · [English](#english) · [원격 서버 버전](https://github.com/changgi/korea-archive-mcp) · [변경 이력](CHANGELOG.md)

</div>

---

## 💡 한 줄 요약

> 미국·영국·프랑스·일본·호주·뉴질랜드·네덜란드·UN과 국내 기관의 문서고 **30곳**을 한 번에 검색하고,
> 찾은 기록의 **원문·출처·이용 권리**를 정리한 뒤, 원하면 **보고서·카드뉴스·논문 각주**까지 만들어 주는 Claude 플러그인입니다.

**두 가지 방법으로 쓸 수 있습니다.**

| | 이런 분께 | 받는 것 |
|---|---|---|
| 🧩 **플러그인** (이 저장소) | Claude 데스크톱·Claude Code를 쓰는 분 | 검색 도구 20종 **+ 전문 스킬 11종**(카드뉴스 렌더링·영상 판독 등 컴퓨터에서 실행하는 작업 포함) |
| 🔗 **커넥터** | Claude 웹·스마트폰 앱을 쓰는 분 | 검색 도구 20종 (주소 하나만 등록, 설치 없음) |

---

## 🚀 설치하기

### 🧩 플러그인 (Claude 데스크톱 · Claude Code)

Claude 대화창에 아래 두 줄을 차례로 입력합니다.

```
/plugin marketplace add changgi/korea-archive-marketplace
/plugin install korea-archive@korea-archive-marketplace
```

### 🔗 커넥터 (Claude 웹 · 스마트폰 앱)

설정 → **커넥터** → **커스텀 커넥터 추가** → 아래 주소 붙여 넣기

```
https://korea-archive-mcp.vercel.app/api/mcp
```

설치 후 **"창기창기 도와줘"** 라고 말하면 사용법을 안내해 줍니다.

---

## 🤔 왜 필요한가요?

한국 관련 기록은 전 세계 문서고에 수백만 건이 있지만, **일반 검색으로는 대부분 찾을 수 없습니다.**

- **기록은 그 시대의 말로 적혀 있습니다.** 1910~45년 기록에서 서울은 **Keijo**, 부산은 **Fusan**, 한국은 **Chosen·Corea** 입니다. 오늘의 단어로 검색하면 대부분을 놓칩니다.
- **나라마다 언어와 검색법이 다릅니다.** "장진호"는 미국에선 `Chosin Reservoir`, 일본에선 `長津湖`로 검색해야 합니다.

이 플러그인은 한국어 질문을 각 문서고의 언어와 그 시대 표기로 바꿔 30곳을 동시에 찾습니다.
바탕이 된 방법론은 검증을 거쳤습니다(송창기 2026 — 재현율 93.0%, 정밀도 93.3%).

---

## 💬 이렇게 말해 보세요

평소 말투로 부탁하면 됩니다. 아래는 **실제로 돌려 본 결과**입니다.

| 이렇게 말하면 | 이런 결과를 받습니다 |
|---|---|
| 🗣️ "장진호 전투 기록 찾아줘" | `Chosin Reservoir`로 자동 변환해 미국 국립기록관리청에서만 **512건**을 찾고, 다른 문서고 결과와 합쳐 줍니다 |
| 🗣️ "안중근 의거 당시 신문 기사 찾아줘" | `안중근소식 — 대한매일신보 [3면 3단] (1909.11.9)`처럼 **면·단까지** 적힌 기사 목록 |
| 🗣️ "유관순 공훈록 보여줘" | 공적조서·공훈록 전문·수형 기록·묘소·현충시설을 한 번에 |
| 🗣️ "이 미국 기록 사진 써도 돼?" | 권리 **A등급**(이용 제한 없음) 확인, 촬영일, 실물 소장 위치, 원본 파일 주소 |
| 🗣️ "인천상륙작전 영상, 같은 묶음 더 찾아줘" | 기록 번호 앞뒤를 훑어 **D-DAY 연속 필름 5편**을 한 번에 |
| 🗣️ "찾은 거 표로 정리해줘" | 제목·날짜·소장 기관·소속 분류·원본 이미지 주소가 담긴 표(엑셀용 CSV) |
| 🗣️ "장진호 기록, 같은 것끼리 묶어서 보여줘" | 한국 기관 재수집본과 미국 원본을 **같은 기록으로 묶어** 줍니다 — 9건 중 5건이 두 기관에서 확인됨 (예: "장진호 전투에서 퇴각하는 미 제1해병사단 기록영상" = 미국 NAID 24033) |
| 🗣️ "장진호 풀패키지로 만들어줘" | 조사부터 **보고서·카드뉴스 8장·포스터·발표 자료**까지 이어서 제작 |

---

## 🌏 어디서 찾아 주나요?

| 지역 | 기관 |
|---|---|
| 🇺🇸 미국 | 국립기록관리청(NARA) · 인터넷 아카이브 |
| 🇬🇧 🇫🇷 🇳🇱 영국·프랑스·네덜란드 | 영국 국립기록관 · 프랑스 국립도서관(Gallica) · 네덜란드 국립문서보관소 |
| 🇪🇺 유럽 | 유로피아나(유럽 4,000여 기관 통합) |
| 🇯🇵 일본 | 아시아역사자료센터 · 국립국회도서관 |
| 🇦🇺 🇳🇿 호주·뉴질랜드 | 호주 전쟁기념관 · 뉴질랜드 국립기록원 · 디지털NZ |
| 🌐 국제 | UN 디지털도서관 · 위키미디어 공용 |
| 🇰🇷 한국 | **6·25전쟁 아카이브센터(협약기관)** · 국가기록원 · 국립중앙도서관 · 대한민국신문아카이브 · 서울기록원 · 국사편찬위원회 · 공훈전자사료관 · 독립기념관 · 독립운동판결문 · 국가유산포털 · 대한민국역사박물관 · KTV · 장서각 · 규장각 · 한국고문서자료관 · 정보공개포털 |

---

## 🧰 플러그인에 들어 있는 전문 스킬 11종

스킬은 Claude가 특정 작업을 할 때 꺼내 쓰는 **전문 작업 설명서**입니다. 해당하는 부탁을 받으면 Claude가 알아서 불러옵니다.

### 🔎 찾기
| 스킬 | 이럴 때 | 예시 말하기 |
|---|---|---|
| **korea-archive-discovery** | 국내외 문서고에서 한국 기록을 찾을 때. 표기 변형·교차검증 전략을 자동 적용 | "NARA에서 해방 직후 영상 찾아줘" |
| **joseon-source-excavation** | 한국사DB·규장각·승정원일기 등 조선 사료를 찾을 때 | "비변사등록에서 조운 관련 기사 찾아줘" |
| **kyujanggak-images** | 규장각 고문헌 원문 이미지를 찾아 내려받을 때 | "奎 도판 고해상으로 받아줘" |

### 📖 읽기
| 스킬 | 이럴 때 | 예시 말하기 |
|---|---|---|
| **joseon-source-mining** | 법전·등록·일기를 깊이 읽고 제도의 역사를 정리할 때 | "이 제도가 언제부터 있었는지 경국대전에서 확인해줘" |
| **archival-discovery-pipeline** | 영상·사진을 장면별로 분석하고 화면 속 글자(슬레이트·간판)를 읽을 때 | "이 필름 프레임별로 분석해줘" |
| **record-annotation** | 사진·문서에 번호 표시와 설명을 붙인 해설 이미지를 만들 때 | "이 사진에 뭐가 보이는지 표시해줘" |

### ✍️ 만들기
| 스킬 | 이럴 때 | 예시 말하기 |
|---|---|---|
| **korea-full-package** | 조사부터 모든 결과물까지 한 번에 | "○○ 풀패키지로 만들어줘" |
| **insta-carousel** | 인스타그램 카드뉴스(1080×1080 이미지)를 만들 때 | "이 기록으로 카드뉴스 만들어줘" |
| **khdb-citation** | 한국사DB 자료를 논문 각주·참고문헌으로 쓸 때 | "이 실록 기사 각주 형식으로 써줘" |
| **nanet-citation** | 국회도서관 자료를 논문 참고문헌으로 쓸 때 | "이 학위논문 APA로 써줘" |

### 🙋 안내
| 스킬 | 이럴 때 | 예시 말하기 |
|---|---|---|
| **changgi-help** | 처음 써 보거나 사용법이 궁금할 때 | "창기창기 도와줘" |

---

## 🛡️ 믿을 수 있게 만들었습니다

- **실제 기록만** — AI가 그린 인물이나 장면은 쓰지 않습니다.
- **직접 확인한 정보만** — 모든 주소와 수치는 각 기관 시스템을 실제로 조회한 결과입니다.
- **써도 되는지 표시** — 기록마다 이용 권리를 A~D 등급으로 알려 줍니다. 찾는 것은 막지 않고 표시만 하며, 최종 판단은 사람이 합니다.
- **원문이 바뀌면 알아챕니다** — 주요 기록 8건의 확인값을 [공개 장부](https://korea-archive-mcp.vercel.app/fixity-ledger.json)에 올려 두고 매주 대조합니다.
- **출처를 밝힙니다** — 협약기관 6·25전쟁 아카이브센터 기록에는 출처를 반드시 함께 적습니다.

---

## 🖼️ 실제로 만든 결과물

### 카드뉴스 — 8·15 광복 81주년 시리즈 (전부 저작권 만료 실물 기록으로 제작)

| | | |
|---|---|---|
| ![1945 개성, 미국 국립기록관리청 필름의 한 장면을 쓴 표지](docs/carousel/showcase_01_cover.png) | ![필름 장면을 이어 붙인 파노라마](docs/carousel/showcase_02_pano.png) | ![개성·경성·제주 세 도시의 1945년 촬영지 지도](docs/carousel/showcase_03_map.png) |
| **표지** — 1945 개성, 미국 필름 장면 | **파노라마** — 개성 필름 세 컷 | **지도** — 세 도시의 1945년 |
| ![서울을 찍은 필름 네 롤의 기록 목록](docs/carousel/showcase_04_stack.png) | ![유관순 인물 카드](docs/carousel/showcase_05_person.png) | ![관보 제1호 문서 판독](docs/carousel/showcase_06_document.png) |
| **기록 목록** — 수장고의 서울 필름 네 롤 | **인물** — 유관순 | **문서 읽기** — 관보 제1호 |

### 소개 카드 18장

<details>
<summary><b>펼쳐 보기</b></summary>

| | | |
|---|---|---|
| ![01](docs/cards/card_01.png) | ![02](docs/cards/card_02.png) | ![03](docs/cards/card_03.png) |
| ![04](docs/cards/card_04.png) | ![05](docs/cards/card_05.png) | ![06](docs/cards/card_06.png) |
| ![07](docs/cards/card_07.png) | ![08](docs/cards/card_08.png) | ![09](docs/cards/card_09.png) |
| ![10](docs/cards/card_10.png) | ![11](docs/cards/card_11.png) | ![12](docs/cards/card_12.png) |
| ![13](docs/cards/card_13.png) | ![14](docs/cards/card_14.png) | ![15](docs/cards/card_15.png) |
| ![16](docs/cards/card_16.png) | ![17](docs/cards/card_17.png) | ![18](docs/cards/card_18.png) |

01 표지 · 02 문제 · 03 능력 · 04 해외 문서고 · 05 국내 문서고 · 06 자동 조회 · 07~11 실전 사례 · 12 옛 표기 · 13 권리 판정 · 14 플러그인 설치 · 15 커넥터 연결 · 16 당신 차례 · 17 소개 · 18 GitHub
</details>

더 많은 실물 예시: [한강의 배 보고서](https://korea-archive-mcp.vercel.app/examples/hanriver.html) · [강연 자료 403장](https://korea-archive-mcp.vercel.app/examples/joseon-deck.html) · [기록잇다 — 브라우저 즉석 검색](https://korea-archive-mcp.vercel.app/ingitda.html)

---

## 📖 용어 풀이

| 용어 | 쉬운 설명 |
|---|---|
| **플러그인** | Claude에 도구와 스킬을 한꺼번에 설치하는 묶음 |
| **커넥터(MCP)** | AI 비서에 새 능력을 붙이는 연결 주소 |
| **스킬** | Claude가 특정 작업을 할 때 꺼내 쓰는 전문 작업 설명서 |
| **교차확인** | 같은 기록이 두 곳 이상의 문서고에서 나온 경우 |
| **원본확인** | 사본에 적힌 원본 번호로 미국 국립기록관리청 목록을 직접 조회해 원본이 실제로 있는지 확인한 것 |
| **판독** | 목록이 아니라 기록 본문·상세 정보를 가져와 읽는 것 |
| **옆 번호 훑기(인접 채굴)** | 찾은 기록의 앞뒤 번호를 확인해 같은 묶음을 찾는 방법 |

---

## 👩‍💻 개발자를 위한 정보

<details>
<summary><b>저장소 구조</b></summary>

- `plugins/korea-archive/servers/server.py` — 파이썬 MCP 서버(도구 20종)
- `mcp/server.py` — 단독 실행용 서버(위 파일에서 자동 생성)
- `plugins/korea-archive/skills/` — 전문 스킬 11종
- 원격 서버 버전([korea-archive-mcp](https://github.com/changgi/korea-archive-mcp), Node)과 기능이 같은지 코드를 올릴 때마다 자동으로 검사합니다.
</details>

<details>
<summary><b>선택 환경변수</b></summary>

모두 없어도 대부분 작동합니다.
`NARA_API_KEY`(미국 국립기록관리청) · `EUROPEANA_API_KEY` · `ARCHIVES_API_KEY`(국가기록원, data.go.kr 15000153) · `NLK_API_KEY`(국립중앙도서관)
</details>

---

## English

**Korea Archive** is a Claude plugin that searches **30 archives in 9 countries** (US NARA, UK TNA, Gallica, Europeana, JACAR, NDL, AWM, Archives NZ, UN, Wikimedia Commons and 16+ Korean institutions) with a single Korean or English question.

**Why:** records about Korea were indexed in the vocabulary of their era. Seoul was *Keijo*, Busan *Fusan*, Korea *Chosen* or *Corea*. Search with today's words and most of it stays hidden. The plugin translates each question into each archive's language and period spellings, then searches all 30 sources at once.

**What you get:**
- Merged results, with records found in two or more archives marked as **cross-checked**
- **Full-text reading** at 14 sources: merit records, court rulings, manuscript notes, heritage descriptions, old newspapers, UN documents and NARA catalog details
- **Rights grading (A–D)** for every record, including live NARA use-restriction lookups
- Export as **CSV**, a **knowledge graph**, or a **JSON-LD collection manifest** that records how each item was found
- **11 skills** for reports, card news, video-frame reading, annotation and academic citation

**Install:**
```
/plugin marketplace add changgi/korea-archive-marketplace
/plugin install korea-archive@korea-archive-marketplace
```
Web and mobile: add the custom connector `https://korea-archive-mcp.vercel.app/api/mcp`. Full guide: [help-en.html](https://korea-archive-mcp.vercel.app/help-en.html)

---

<div align="center">

MIT License · 방법론: 송창기 (2026), 국가기록원
협약: KOREAN WAR ARCHIVES 6·25전쟁 아카이브센터

</div>
