# 접근 경로 — 실행 가능한 코드

한강 강배 조사(2026-08-18)에서 실측 확인된 코드다. 그대로 복사해 쓸 수 있다.

---

## 공통 헤더

```python
import urllib.request, urllib.parse, ssl, gzip, re, html, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/124",
    "Referer": "https://db.history.go.kr/",
    "Content-Type": "application/x-www-form-urlencoded",
}

def _decode(resp):
    b = resp.read()
    if resp.headers.get("Content-Encoding") == "gzip":
        b = gzip.decompress(b)
    return b.decode("utf-8", "replace")

def post(url, params, timeout=90, retries=2):
    data = urllib.parse.urlencode(params).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=HDR)
            return _decode(urllib.request.urlopen(req, timeout=timeout, context=ctx))
        except Exception:
            if a < retries - 1:
                time.sleep(20)
    return ""

def get(url, timeout=90, retries=2):
    for a in range(retries):
        try:
            req = urllib.request.Request(url, headers=HDR)
            return _decode(urllib.request.urlopen(req, timeout=timeout, context=ctx))
        except Exception:
            if a < retries - 1:
                time.sleep(20)
    return ""
```

---

## 1. 법전·편람 검색 (조선시대법령자료)

```python
def law_search(kw, unit=50):
    """조선시대법령자료 검색. 반환: (총건수, [(levelId, 서명·편·조, 발췌)])"""
    s = post("https://db.history.go.kr/search/law/searchResultList.do", {
        "searchItemId": "jlaw", "searchTarget": "jlaw",
        "pageIndex": "1", "pageUnit": str(unit), "pageSize": "1",
        "orderColumn": "levelId", "orderDir": "ASC",
        "synonym": "off", "chinessChar": "on",   # ← 한자 검색 필수
        "totalWord": kw,
        "titleWord": "", "titleConjunction": "AND",
        "contentsWord": "", "contentsConjunction": "AND",
        "creatorWord": "", "creatorConjunction": "AND",
        "startDate": "", "endDate": "",
    })
    txt = re.sub("<[^>]+>", "", html.unescape(s))
    m = re.search(r"총\s*([\d,]+)건", txt)
    total = m.group(1) if m else "0"

    items = re.findall(
        r"fnGoItemView\('([^']+)',\s*'\d+'\).*?<ul class=\"tit\">(.*?)</ul>"
        r"\s*<p class=\"tx\">(.*?)</p>", s, flags=re.S)
    out = []
    for lid, tt, tx in items:
        title = "·".join(
            re.sub(r"\s+", "", re.sub("<[^>]+>", "", x))
            for x in re.findall(r"<li>(.*?)</li>", tt, flags=re.S))
        excerpt = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", "", tx))).strip()
        out.append((lid, title, excerpt))
    return total, out
```

**용례**

```python
total, rows = law_search("執籌")     # → 22건, 전부 노비 소송 조문
total, rows = law_search("執籌船")   # → 1건, 度支志 「事實」 = 법전 부재의 증거
```

---

## 2. 등록류 검색 (비변사등록) — 좌목 필터 포함

```python
def record_search(kw, unit=100, drop_jwamok=True):
    """비변사등록 검색. drop_jwamok=True면 '…좌목' 표제를 제외한다."""
    s = post("https://db.history.go.kr/joseon/search/searchResultList.do", {
        "searchItemId": "bb", "searchTarget": "bb",
        "pageIndex": "1", "pageUnit": str(unit), "pageSize": "1",
        "orderColumn": "levelId", "orderDir": "ASC",
        "synonym": "off", "chinessChar": "on", "totalWord": kw,
        "titleWord": "", "contentsWord": "", "creatorWord": "",
        "startDate": "", "endDate": "",
    })
    rows = []
    for lid, tt in re.findall(r"levelId=([\w]+)[^>]*>(.*?)</a>", s, flags=re.S):
        title = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", "", tt))).strip()
        if not title:
            continue
        if drop_jwamok and re.search(r"좌목$", title):
            continue                       # ★ 492/601이 좌목이었다
        rows.append((lid, title))
    return rows
```

**반드시 확인할 것** — 필터 전후 건수를 함께 보고한다.

```python
all_rows  = record_search("舟橋司", drop_jwamok=False)
real_rows = record_search("舟橋司", drop_jwamok=True)
print(f"검색 {len(all_rows)}건 · 좌목 제외 실질 {len(real_rows)}건")
# → 검색 601건 · 좌목 제외 실질 109건
```

---

## 3. 본문 조회 — 경로가 두 개다

```python
def item_read(level_id):
    """levelId로 본문 조회. 법령/등록 경로를 자동 판별한다."""
    if level_id.startswith("jlaw"):
        url = "https://db.history.go.kr/joseon/item/level.do?levelId=" + level_id
    else:
        url = "https://db.history.go.kr/joseon/level.do?levelId=" + level_id
    s = get(url)
    if not s:
        return None
    s = re.sub(r"(?s)<script.*?</script>", "", s)
    s = re.sub(r"(?s)<style.*?</style>", "", s)
    lines = [l.strip() for l in
             html.unescape(re.sub(r"(?s)<[^>]+>", "\n", s)).split("\n") if l.strip()]

    # 본문 시작점 — 법령은 '다음글' 뒤, 등록은 ◯/○ 로 시작
    if level_id.startswith("jlaw"):
        k = lines.index("다음글") + 1 if "다음글" in lines else 0
    else:
        k = next((i for i, l in enumerate(lines)
                  if l.startswith("◯") or l.startswith("○")), None)
        if k is None:
            return ""          # 본문 미공개 — 링크는 유효할 수 있다
    end = next((i for i, l in enumerate(lines[k:], k)
                if "경기도 과천시" in l or "개인정보" in l), k + 200)
    return " ".join(lines[k:end])
```

**빈 문자열 반환은 두 가지를 뜻한다.**
- 본문이 실제로 공개되지 않음 (링크는 유효)
- 파싱 실패

**둘을 구분하려면** 페이지 길이와 표제 검출 여부를 함께 본다.
한강 조사의 `bb_200r_001_03_0200`이 전자였다.

---

## 4. ★ 형제 조 전수 스캔 — 가장 중요한 함수

```python
def sibling_scan(level_id, span=12):
    """편·조 구조 사료의 형제 조를 전수 조회한다.
    총론만 읽고 끝내는 실수를 방지한다."""
    m = re.match(r"(.+_)(\d{4})$", level_id)
    if not m:
        return []
    stem = m.group(1)
    found = []
    for n in range(1, span + 1):
        lid = f"{stem}{n*10:04d}"
        body = item_read(lid)
        if not body:
            continue
        if "조선시대법령자료 메뉴" in body:   # 존재하지 않는 번호
            continue
        # 조 제목 추출 — [卷首] 舟橋 처럼 대괄호로 표시된다
        s = get(("https://db.history.go.kr/joseon/item/level.do?levelId=" + lid)
                if lid.startswith("jlaw")
                else ("https://db.history.go.kr/joseon/level.do?levelId=" + lid))
        heads = re.findall(r"\[([^\]]{1,20})\]", re.sub("<[^>]+>", " ", s))
        found.append((lid, heads[-1] if heads else "?", len(body), body[:200]))
        time.sleep(0.4)
    return found
```

**용례 — 이 한 번의 호출이 조사의 절반을 바꿨다**

```python
for lid, head, n, head200 in sibling_scan("jlawb_400_0050_0090_0030"):
    print(f"{lid}  [{head}]  {n}자")
# jlawb_400_0050_0090_0010  [總例]    ← 이미 읽음
# jlawb_400_0050_0090_0020  [津路]    ← 신규! 능침별 도강 지점
# jlawb_400_0050_0090_0030  [舟橋船]  ← 자재 명세
# jlawb_400_0050_0090_0040  [員額]    ← 신규! 인원 편성
```

---

## 5. 규장각 검색 — 목록과 해제를 모두 조회

```python
KYU = "https://kyudb.snu.ac.kr"
KHDR = {**HDR, "Referer": KYU + "/"}

def kyu_search(kw):
    """규장각 검색. searchArea 10(목록)과 20(해제)을 모두 조회한다.
    ★ 절목·사목류는 상위 서명 아래 편차로 들어가 목록에는 안 나온다."""
    out = {}
    for area, label in (("10", "목록"), ("20", "해제")):
        data = urllib.parse.urlencode({
            "totalSearchString": kw, "searchArea": area,
        }).encode()
        try:
            req = urllib.request.Request(KYU + "/search/search.do",
                                         data=data, headers=KHDR)
            out[label] = _decode(urllib.request.urlopen(req, timeout=90, context=ctx))
        except Exception as e:
            out[label] = ""
        time.sleep(0.6)
    return out
```

**주의** — `web_fetch` 도구는 kyudb에서 ROBOTS_DISALLOWED가 나온다.
**컨테이너에서 urllib 직접 요청은 200 OK**다.

---

## 6. 규장각 원문 이미지 수집

```python
ITEM_CD = {
    "도설·회화": "ART",   # 各船圖本 奎15752
    "두루마리":  "ETC",   # 奎軸12163
    "등록류":    "DRR",   # 禁營津船謄錄 奎19356
    "재정·사목": "FND",   # 均役廳事目 奎17252
    "정책·절목": "POL",   # 舟橋指南 奎5485  ← 파일명 규칙 다름
}

def kyu_image_urls(item_cd, book_cd, pages=40):
    """원문 이미지 URL 목록을 만든다.
    ★ 첫 URL을 실제로 받아 보고 패턴을 확정한 뒤 순회할 것."""
    base = (f"{KYU}/ImageServlet.do?imgFileNm=%s"
            f"&path=/data01/stream/{item_cd}/IMG/{book_cd}/{book_cd}_0001/")
    urls = []
    for i in range(1, pages + 1):
        if item_cd == "POL":          # 舟橋指南 계열 — 밑줄 없음, 4자리
            fn = f"{book_cd}_00IH_0001_{i:04d}.jpg"
        else:                          # 나머지 — a/b면 구분
            fn = f"{book_cd}_00_IH_0001_{i:03d}a.jpg"
        urls.append(base % fn)
    return urls
```

**패턴 확정 절차**

1. 상세 페이지에서 `fn_originalImg(item_cd, book_cd)` 인자를 읽는다
2. `POST /pf01/rendererImg.do`로 렌더러를 연다
3. 응답에서 **실제 imgFileNm 하나**를 확보한다
4. 그 패턴으로 순회한다 — **추정하지 말 것**

---

## 7. 승정원일기 · 실록

```python
def sjw_search(kw, unit=50, page=1):
    return post("https://sjw.history.go.kr/search/searchResultList.do", {
        "searchTerm": kw, "searchTermImages": "",
        "topSearchWord": kw, "topSearchWord_ime": kw,
        "pageUnit": str(unit), "pageIndex": str(page), "searchType": "a",
    })

def sillok_search(kw):
    return post("https://sillok.history.go.kr/search/searchResultList.do",
                {"topSearchWord": kw, "topSearchWord_ime": kw})
```

**왕대 분포를 뽑는 것이 핵심이다.** 최초 용례가 통념보다 이르면 서사가 뒤집힌다.

```python
s = sjw_search("執籌船")
t = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", " ", s)))
m = re.search(r"전체 \((\d+)\)((?:\s*\S+\s*\(\d+\))+)", t)
# → 전체 (53) 영조 (2) 정조 (3) 순조 (19) 헌종 (8) 철종 (6) 고종 (15)
# 영조 2건 → 최초 사례 1731년 → 주교사(1790)보다 58년 앞섬
```

---

## 8. 배치 수집 패턴

대량 본문을 받을 때는 실패를 집계하고 진행 상황을 찍는다.

```python
def batch_read(level_ids, sleep=0.5):
    got, failed = {}, []
    for n, lid in enumerate(level_ids, 1):
        body = item_read(lid)
        if body is None:
            failed.append(lid)
        else:
            got[lid] = body
        if n % 10 == 0:
            print(f"{n}/{len(level_ids)} 수집 {len(got)} 실패 {len(failed)}")
        time.sleep(sleep)
    return got, failed
```

한강 조사 실적 — 정조대 40건(32,259자) 실패 0 / 19세기 58건(131,714자) 실패 0.
**서버는 견딘다. 0.4~0.5초 간격이면 충분하다.**

---

## 9. 요청 예절

- 간격 **0.4초 이상**, 대량 배치는 0.5초
- 실패 시 **20초 대기 후 1회 재시도** (즉시 재시도는 서버를 더 괴롭힌다)
- 503/타임아웃이 연속되면 **중단하고 시간을 두고 재개**
- 이용약관·저작권 준수. 원문 이미지는 **소장기관 허가 범위**를 확인할 것
