#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인용 링크 전수 검증 (link_check.py)

보고서가 인용한 levelId와 외부 URL이 실제로 열리는지 확인한다.
핵심은 두 가지를 분리해서 보는 것이다.

  ① HTTP 200      — 링크가 살아 있는가
  ② 본문 존재      — 내용이 실제로 있는가

이 둘은 별개다. 한강 강배 조사에서 1건이 '200 응답에 본문 없음'으로 나왔는데,
확인해 보니 항목은 존재하고 URL도 유효한데 본문이 공개되지 않은 것이었다.
'도달하지 못했다'와 '공개되지 않았다'는 다르고, 후자는 재시도로 해결되지 않는다.

사용법
  python3 link_check.py report.html [report2.html ...]
  python3 link_check.py --ids bb_187r_001_01_0710 jlawb_400_0020_0060_0070
"""
import sys, re, ssl, gzip, time, html, urllib.request, collections

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 Chrome/124"}

ID_PAT  = r'\b(jlaw[ab]_[\w]+|bb_\d+r_[\w]+)\b'
URL_PAT = r'https?://[^\s"\'<>)]+'


def fetch(url, timeout=30):
    """(상태코드, 본문) 반환. 실패 시 상태코드 자리에 사유 문자열."""
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, headers=HDR), timeout=timeout, context=ctx)
        b = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            b = gzip.decompress(b)
        return r.status, b.decode("utf-8", "replace")
    except Exception as e:
        return (getattr(e, "code", None) or type(e).__name__), ""


def check_level_id(lid):
    """levelId 검증. 200 여부와 본문 존재를 분리해 판정한다."""
    path = "/joseon/item/level.do?levelId=" if lid.startswith("jlaw") \
           else "/joseon/level.do?levelId="
    st, s = fetch("https://db.history.go.kr" + path + lid, timeout=45)
    if st != 200:
        return {"id": lid, "http": st, "body": False, "cause": "http_error"}
    has_body = ("다음글" in s) or ("◯" in s) or ("○" in s)
    if has_body:
        return {"id": lid, "http": 200, "body": True, "cause": "ok"}
    # 표제는 있는데 본문이 없으면 '미공개'다
    title = bool(re.search(r"啓|傳敎|節目|事目|條例|大典", re.sub("<[^>]+>", " ", s)))
    return {"id": lid, "http": 200, "body": False,
            "cause": "not_published" if title else "parse_failed"}


def classify_url_issue(url, st):
    """이상 URL의 원인을 분류한다. 대부분은 자료 소멸이 아니다."""
    if "&amp;" in url:
        return "html_entity", "HTML의 &amp; 미해제 — 해제하면 정상"
    if st == 202:
        return "async_202", "비동기 응답(봇 차단 아님) — 브라우저에서는 열림"
    if isinstance(st, str) and "Timeout" in st:
        return "server_slow", "기관 서버 지연 — 시간을 두고 재시도"
    if st == 400 and ("search" in url.lower() or "Result" in url):
        return "post_only", "POST 기반 검색 URL — GET으로 재현 불가"
    if st == 404:
        return "not_found", "★ 실제 사망 링크 가능성 — 수동 확인 필요"
    return "other", f"코드 {st}"


def main():
    args = sys.argv[1:]
    ids, urls = set(), set()

    if args and args[0] == "--ids":
        ids = set(args[1:])
    else:
        for path in args or []:
            try:
                t = open(path, encoding="utf-8").read()
            except Exception as e:
                print(f"  ✗ 읽기 실패 {path}: {e}")
                continue
            ids |= set(re.findall(ID_PAT, t))
            urls |= set(re.findall(URL_PAT, t))

    if not ids and not urls:
        print(__doc__)
        return

    print("=" * 74)
    print(f"링크 검증  ·  levelId {len(ids)}개  ·  외부 URL {len(urls)}개")
    print("=" * 74)

    # ── levelId ──────────────────────────────────────────────
    if ids:
        print("\n[1] 국사편찬위원회 levelId\n")
        rows = []
        for lid in sorted(ids):
            rows.append(check_level_id(lid))
            time.sleep(0.25)
        ok = [r for r in rows if r["cause"] == "ok"]
        bad = [r for r in rows if r["cause"] != "ok"]
        print(f"  정상 {len(ok)} / 이상 {len(bad)}")
        for r in bad:
            tag = {"not_published": "본문 미공개(URL은 유효)",
                   "parse_failed":  "파싱 실패 — 수동 확인",
                   "http_error":    f"HTTP {r['http']}"}.get(r["cause"], r["cause"])
            print(f"    ✗ {r['id']:<28} {tag}")
        if any(r["cause"] == "not_published" for r in bad):
            print("\n    ※ '본문 미공개'는 재시도로 해결되지 않습니다.")
            print("       자료의 공개 범위 문제이므로 소장기관에 문의하십시오.")

    # ── 외부 URL ─────────────────────────────────────────────
    if urls:
        print("\n[2] 외부 URL\n")
        ok, bad = [], []
        for u in sorted(urls):
            st, _ = fetch(html.unescape(u), timeout=25)
            (ok if st == 200 else bad).append((u, st))
            time.sleep(0.15)
        print(f"  정상 {len(ok)} / 이상 {len(bad)}")
        if bad:
            groups = collections.defaultdict(list)
            for u, st in bad:
                cause, note = classify_url_issue(u, st)
                groups[(cause, note)].append(u)
            print()
            for (cause, note), us in sorted(groups.items()):
                print(f"    [{cause}] {len(us)}건 — {note}")
                for u in us[:3]:
                    print(f"       {re.sub(r'^https?://', '', u)[:70]}")
            dead = sum(len(v) for (c, _), v in groups.items() if c == "not_found")
            print(f"\n    실제 사망 링크 후보: {dead}건")
            print("    ※ 나머지는 조회 방식 문제이며 자료 소멸이 아닙니다.")

    print("\n" + "=" * 74)


if __name__ == "__main__":
    main()
