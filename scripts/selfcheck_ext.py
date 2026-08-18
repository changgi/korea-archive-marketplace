#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selfcheck_ext.py — 해외·국내 아카이브 점검 확장 (discovery v2 경로)

기존 `selfcheck.py` 는 한국사DB·규장각만 본다. discovery v2가 다루는 경로
(갈리카·유러피아나·서울기록원·정보공개포털·6·25아카이브)는 점검 대상이 아니었다.

    점검되지 않는 경로는 낡아도 아무도 모른다.

전 항목 2026-08-18 실측. 표준 라이브러리만 쓴다.

붙이는 법
--------
`selfcheck.py` 끝에 두 줄:

    from selfcheck_ext import EXT_CHECKS
    CHECKS += EXT_CHECKS

또는 단독 실행:

    python selfcheck_ext.py
"""

from __future__ import annotations

import json
import re
import socket
import ssl
import sys
import time
import urllib.parse
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# ★ 헤더가 부실하면 기관 서버가 503으로 튕긴다. 실측으로 확인했다 —
#   Accept·Accept-Language 없이 요청하면 서울기록원·6·25아카이브가 503을 낸다.
#   그 503을 "서버 장애"로 읽으면 몇 시간을 허비한다.
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124 Safari/537.36"),
    "Accept": "*/*",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}


def get(url: str, accept: str | None = None, timeout: int = 30):
    h = dict(HEADERS)
    if accept:
        h["Accept"] = accept
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.status, r.read().decode("utf-8", "replace")


def tcp_open(host: str, port: int, timeout: int = 10) -> bool:
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# 점검 항목 — 각 함수는 (성공여부, 설명, None)
# ---------------------------------------------------------------------------

def c_gallica():
    """갈리카(BnF) SRU API — 프랑스어 표기 Corée"""
    q = urllib.parse.quote('gallica all "Corée"')
    url = (f"https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2"
           f"&query={q}&maximumRecords=5")
    # ★ Accept 헤더에 민감하다. 실측:
    #     application/xml → 200 · */* → 200 · text/xml → 406 Not Acceptable
    #   406을 "API 폐기"로 읽으면 안 된다. 헤더만 고치면 열린다.
    status, body = get(url, accept="application/xml")
    m = re.search(r"numberOfRecords>(\d+)", body)
    if not m:
        return False, f"HTTP {status} · numberOfRecords 패턴 미검출 — 응답 형식 변경", None
    n = int(m.group(1))
    if n == 0:
        return False, "0건 — 쿼리 문법 변경 의심", None
    return True, f'"Corée" {n:,}건', None


def c_europeana():
    """유러피아나 Search API — 데모 키로 동작 확인"""
    url = ("https://api.europeana.eu/record/v2/search.json"
           "?wskey=api2demo&query=Korea&rows=3")
    status, body = get(url)
    try:
        j = json.loads(body)
    except json.JSONDecodeError:
        return False, f"HTTP {status} · JSON 파싱 실패", None
    if not j.get("success"):
        return False, f"success=false · {str(j.get('error'))[:60]}", None
    return True, f"Korea {j.get('totalResults', 0):,}건 (데모 키)", None


def c_seoul_archives():
    """서울기록원 — 헤더 부실 시 503이 나는 대표 사례"""
    try:
        status, body = get("https://archives.seoul.go.kr/", accept="text/html")
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:60]}", None
    if status != 200:
        return False, f"HTTP {status}", None
    return True, f"HTTP 200 ({len(body):,}B)", None


def c_foia_portal():
    """정보공개포털 — 청구 필요 자료의 창구"""
    try:
        status, body = get("https://www.open.go.kr/", accept="text/html")
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:60]}", None
    return (status == 200), f"HTTP {status} ({len(body):,}B)", None


def c_koreanwar():
    """6·25전쟁 아카이브센터 — 포트 판정 포함

    ★ 이 항목이 이 확장의 존재 이유다.
      '포트 8443 도달 실패'가 보고된 적이 있는데, 실측 결과:
        · 443  TCP 연결 OK → HTTPS 200
        · 8443 TCP 연결 자체가 타임아웃
      ★ 환경 의존 판정: 일부 컨테이너/망에서는 8443 TCP가 막히지만,
      로컬 Windows·Vercel(icn1)에서는 8443이 정상 개통이다(2026-08-19 재실측 —
      검색·OpenAPI 모두 :8443 정식 host). 8443 실패 시 자기 망의 egress 정책을
      먼저 의심하고, 443 폴백은 임시 우회로만 쓸 것.
    """
    host = "www.koreanwar.or.kr"
    ok443 = tcp_open(host, 443)
    ok8443 = tcp_open(host, 8443, timeout=8)
    try:
        status, body = get(f"https://{host}/", accept="text/html")
    except Exception as e:
        return False, f"443 TCP={ok443} · HTTPS {type(e).__name__}", None
    note = "443 정상"
    if not ok8443:
        note += " · 이 환경에서 8443 TCP 실패 — egress 정책 의심(로컬·Vercel은 8443 정상). 443은 임시 우회"
    return (status == 200), f"HTTP {status} · {note}", None


EXT_CHECKS = [
    ("갈리카 SRU", c_gallica,
     "korea-archive-discovery/references/<유럽기관 지도>.md — Accept 헤더 주의"),
    ("유러피아나 API", c_europeana,
     "korea-archive-discovery/references/<유럽기관 지도>.md"),
    ("서울기록원", c_seoul_archives,
     "korea-archive-discovery/SKILL.md — 국내 아카이브 절"),
    ("정보공개포털", c_foia_portal,
     "korea-archive-discovery/SKILL.md — 청구 필요 자료"),
    ("6·25아카이브(포트)", c_koreanwar,
     "korea-archive-discovery/SKILL.md — 접근 주소는 443"),
]


def main() -> int:
    print("=" * 72)
    print("  확장 점검 — 해외·국내 아카이브  |  기준: 2026-08-18 실측")
    print("=" * 72 + "\n")
    bad = 0
    for name, fn, where in EXT_CHECKS:
        t0 = time.time()
        try:
            ok, detail, _ = fn()
        except Exception as e:
            ok, detail = False, f"예외: {repr(e)[:80]}"
        print(f"  {'OK ' if ok else '✕  '}{name:<20} {detail}   ({time.time() - t0:.1f}s)")
        if not ok:
            print(f"      → 고칠 곳: {where}")
            bad += 1
        time.sleep(0.5)

    print("\n" + "-" * 72)
    print(f"  {len(EXT_CHECKS)}항목 중 {bad}건 실패" if bad
          else f"  {len(EXT_CHECKS)}항목 전부 통과")
    print("-" * 72)
    print("""
  실패 해석 순서 (기존 selfcheck 와 동일)
    ① 네트워크·방화벽 — 다른 항목도 함께 실패했는가
    ② 일시 장애 — 몇 분 뒤 재시도
    ③ 마크업·API 변경 — '고칠 곳'의 패턴을 갱신

  이 확장에서 배운 것 두 가지
    · **503이 서버 장애가 아닐 수 있다.** Accept·Accept-Language 헤더가 없으면
      기관 서버가 튕긴다. 헤더를 채우면 200이 돌아온다.
    · **406은 API 폐기가 아닐 수 있다.** 갈리카 SRU는 Accept: text/xml 에 406을 내고
      application/xml 에 200을 낸다.
    둘 다 '서버가 죽었다'로 읽으면 몇 시간을 허비한다.
""")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
