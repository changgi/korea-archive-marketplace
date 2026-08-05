#!/usr/bin/env python3
"""인스타 캐러셀 렌더링 파이프라인.

템플릿 HTML 안의 {{img:...}} 토큰을 base64 데이터 URI로 치환하고,
.card 블록을 개별 페이지로 분리해 헤드리스 크롬/엣지로 PNG 캡처한 뒤
크기를 검증한다.

사용:
    python make_carousel.py template.html --outdir out
    python make_carousel.py template.html --outdir out --size 1080x1350
    python make_carousel.py template.html --outdir out --no-render   # HTML만
    python make_carousel.py template.html --outdir out --only 3,5    # 일부 카드만 재렌더

이미지 토큰 (경로는 템플릿 파일 기준 상대경로 또는 절대경로):
    {{img:photos/cover.jpg}}                  원본 그대로 임베드
    {{img:photos/cover.jpg|maxdim=760|q=72}}  최대 760px 리사이즈, JPEG 품질 72
"""
import argparse
import base64
import io
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Windows 콘솔(cp949)에서도 한글/특수문자 출력이 깨지지 않게
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

TOKEN_RE = re.compile(r"\{\{img:([^}|]+)((?:\|[a-z]+=\d+)*)\}\}")

BROWSER_CANDIDATES = [
    os.environ.get("CHROME_PATH", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def find_browser(override=None):
    if override:
        if Path(override).exists():
            return override
        sys.exit(f"[오류] 지정한 브라우저가 없습니다: {override}")
    for c in BROWSER_CANDIDATES:
        if c and Path(c).exists():
            return c
    for name in ("google-chrome", "chromium", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    sys.exit("[오류] Chrome/Edge를 찾지 못했습니다. --browser \"C:\\...\\chrome.exe\" 로 경로를 지정하세요.")


def embed_images(html, base_dir):
    """{{img:path|opts}} 토큰을 데이터 URI로 치환."""
    def repl(m):
        rel, opts_raw = m.group(1).strip(), m.group(2)
        opts = dict(kv.split("=") for kv in opts_raw.strip("|").split("|") if "=" in kv)
        path = Path(rel)
        if not path.is_absolute():
            path = base_dir / path
        if not path.exists():
            print(f"[경고] 이미지 없음: {path} — 토큰을 그대로 둡니다")
            return m.group(0)
        maxdim = int(opts.get("maxdim", 0))
        quality = int(opts.get("q", 72))
        if HAS_PIL and maxdim:
            im = Image.open(path).convert("RGB")
            im.thumbnail((maxdim, maxdim))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=quality, optimize=True)
            data, mime = buf.getvalue(), "image/jpeg"
        else:
            if maxdim and not HAS_PIL:
                print(f"[경고] Pillow 없음 — {path.name} 원본 그대로 임베드(파일이 커짐)")
            data = path.read_bytes()
            ext = path.suffix.lower().lstrip(".")
            mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                    "webp": "image/webp", "gif": "image/gif"}.get(ext, "application/octet-stream")
        return f"data:{mime};base64,{base64.b64encode(data).decode()}"
    return TOKEN_RE.sub(repl, html)


def split_cards(html):
    """<div class="card"...> 블록들을 div 깊이 추적으로 추출."""
    cards = []
    pos = 0
    open_re = re.compile(r"<div\b[^>]*class=\"[^\"]*\bcard\b[^\"]*\"[^>]*>", re.I)
    tag_re = re.compile(r"<div\b|</div\s*>", re.I)
    while True:
        m = open_re.search(html, pos)
        if not m:
            break
        depth, i = 1, m.end()
        while depth > 0:
            t = tag_re.search(html, i)
            if not t:
                sys.exit("[오류] .card div가 닫히지 않았습니다 — HTML을 확인하세요")
            depth += 1 if t.group(0).lower().startswith("<div") else -1
            i = t.end()
        cards.append(html[m.start():i])
        pos = i
    return cards


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template")
    ap.add_argument("--outdir", default="carousel_out")
    ap.add_argument("--size", default="1080x1080", help="WxH (기본 1080x1080)")
    ap.add_argument("--browser", default=None)
    ap.add_argument("--no-render", action="store_true", help="HTML 생성까지만")
    ap.add_argument("--only", default=None, help="재렌더할 카드 번호 (예: 3,5)")
    ap.add_argument("--expect", type=int, default=None,
                    help="기대 카드 수 — 다르면 오류로 중단 (사용자가 장수를 지정한 작업에 필수)")
    args = ap.parse_args()

    w, h = (int(x) for x in args.size.lower().split("x"))
    tpl_path = Path(args.template).resolve()
    out = Path(args.outdir).resolve()
    (out / "cards").mkdir(parents=True, exist_ok=True)
    (out / "png").mkdir(parents=True, exist_ok=True)

    html = tpl_path.read_text(encoding="utf-8")
    html = embed_images(html, tpl_path.parent)
    (out / "carousel.html").write_text(html, encoding="utf-8")
    print(f"[1/3] 임베드 완료 → {out / 'carousel.html'} ({len(html)//1024} KB)")

    styles = "\n".join(re.findall(r"<style>.*?</style>", html, re.S))
    cards = split_cards(html)
    if not cards:
        sys.exit('[오류] <div class="card"> 블록을 찾지 못했습니다')
    if args.expect is not None and len(cards) != args.expect:
        sys.exit(f"[오류] 카드 수 불일치 — 기대 {args.expect}장, 실제 {len(cards)}장. "
                 f"템플릿의 .card 블록을 수정한 뒤 다시 실행하세요.")
    override = ("<style>body{margin:0!important;padding:0!important;}"
                ".card{margin:0!important;box-shadow:none!important;}</style>")
    for i, c in enumerate(cards, 1):
        page = (f'<!DOCTYPE html><html><head><meta charset="UTF-8">{styles}{override}'
                f"</head><body>{c}</body></html>")
        (out / "cards" / f"card_{i:02d}.html").write_text(page, encoding="utf-8")
    print(f"[2/3] 카드 분리 완료 — {len(cards)}장")

    if args.no_render:
        return

    only = {int(x) for x in args.only.split(",")} if args.only else None
    browser = find_browser(args.browser)
    report = []
    for i in range(1, len(cards) + 1):
        if only and i not in only:
            continue
        src = (out / "cards" / f"card_{i:02d}.html").as_uri()
        png = out / "png" / f"card_{i:02d}.png"
        subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=1", f"--window-size={w},{h}",
             f"--screenshot={png}", src],
            capture_output=True, timeout=120,
        )
        if not png.exists():
            report.append((png.name, "실패", "PNG가 생성되지 않음"))
            continue
        if HAS_PIL:
            iw, ih = Image.open(png).size
            ok = "OK" if (iw, ih) == (w, h) else "크기불일치"
            report.append((png.name, ok, f"{iw}x{ih}"))
        else:
            report.append((png.name, "OK?", f"{png.stat().st_size//1024} KB (Pillow 없음, 크기 미검증)"))

    print(f"[3/3] 렌더링 완료 → {out / 'png'}")
    for name, status, detail in report:
        print(f"  {name}  {status}  {detail}")
    bad = [r for r in report if r[1] not in ("OK", "OK?")]
    if bad:
        print(f"[경고] {len(bad)}장 문제 있음 — 위 목록 확인")
    print("\n다음 단계: PNG를 눈으로 검수하세요 (세로 넘침·이미지 적합성·페이지번호).")


if __name__ == "__main__":
    main()
