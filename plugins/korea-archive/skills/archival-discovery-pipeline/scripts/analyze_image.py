#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이미지 분석 · OCR 보조 · 텍스트 식별

사용법
    # 이미지 한 장 종합 분석 (문자 영역 탐지 + OCR 시도 + 전처리 후보 생성)
    python analyze_image.py <이미지> --out <디렉터리>

    # OCR만 — 여러 전처리·언어·모드를 전수 시도해 후보를 낸다
    python analyze_image.py <이미지> --ocr --lang eng+chi_tra

    # 문자 영역만 잘라내기 — 사람이 볼 판독용 조각
    python analyze_image.py <이미지> --regions --out <디렉터리>

    # 추출된 텍스트를 식별 (슬레이트 필드·날짜·부대·지명)
    python analyze_image.py --identify "DATE 4/30/48 UNIT FE SIGNAL C CORPS"

⚠ OCR의 한계를 먼저 밝힌다
    사료 영상 프레임은 저해상도·필름 그레인·흔들림·비스듬한 각도가 겹쳐
    일반 OCR 정확도가 매우 낮다. 특히 다음은 사실상 실패한다.
      · 손글씨 (슬레이트 기입 내용 대부분)
      · 한자 (획이 뭉개짐)
      · 세로쓰기 간판
    반면 다음은 부분적으로 성공한다.
      · 인쇄체 영문 대문자 (표지판·현수막 영문 병기)
      · 큰 글씨의 고대비 문자

    **따라서 이 스크립트는 판독을 대신하지 않는다.**
    문자 영역을 찾아 잘라 주고, OCR 후보를 제시해 사람의 판독을 돕는다.
    OCR 결과를 그대로 재기술에 옮기면 안 된다.

의존
    tesseract (+ 언어팩) · pytesseract · opencv · Pillow · numpy
"""
import argparse, os, re, sys, json, subprocess

try:
    import cv2, numpy as np
    from PIL import Image
except ImportError:
    print("opencv-python · Pillow · numpy 가 필요합니다.", file=sys.stderr); sys.exit(1)

HAS_OCR = True
try:
    import pytesseract
except ImportError:
    HAS_OCR = False


# ── 전처리 후보 ───────────────────────────────────────────
# 사료 이미지는 전처리에 따라 결과가 크게 달라진다.
# 하나만 쓰지 않고 여러 후보를 만들어 전부 시도한다.

def variants(path, upscale=None):
    g = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if g is None:
        return []
    h, w = g.shape
    s = upscale or (3 if max(h, w) < 600 else 2)
    g = cv2.resize(g, (w * s, h * s), interpolation=cv2.INTER_CUBIC)
    out = [("원본확대", g)]
    out.append(("대비강화", cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(g)))
    out.append(("노이즈제거", cv2.fastNlMeansDenoising(g, None, 10, 7, 21)))
    out.append(("이진화", cv2.threshold(g, 0, 255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]))
    out.append(("이진화반전", cv2.threshold(g, 0, 255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]))
    out.append(("적응형", cv2.adaptiveThreshold(g, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10)))
    sh = cv2.filter2D(g, -1, np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]))
    out.append(("샤픈", sh))
    return out


# ── 문자 영역 탐지 ────────────────────────────────────────
# MSER + 형태학 연산으로 문자처럼 보이는 덩어리를 찾는다.
# OCR보다 이쪽이 실용적이다 — 어디를 확대해 볼지 알려 주기 때문.

def find_text_regions(path, min_area=400):
    img = cv2.imread(path)
    if img is None:
        return [], None
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(g)

    # 문자 획은 국소 대비가 크다
    grad = cv2.morphologyEx(g, cv2.MORPH_GRADIENT,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    _, bw = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # 가로로 이어 붙여 글자 뭉치를 만든다
    con = cv2.morphologyEx(bw, cv2.MORPH_CLOSE,
                           cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5)))
    cnts, _ = cv2.findContours(con, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    H, W = g.shape
    regions = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if w * h < min_area or h < 12 or w < 20:
            continue
        ar = w / h
        if ar < 0.8 or ar > 25:          # 너무 세로거나 너무 납작한 것 제외
            continue
        if w > W * 0.95 and h > H * 0.95:  # 전체 프레임 제외
            continue
        roi = g[y:y+h, x:x+w]
        # 문자 영역은 명암이 갈린다
        sep = min((roi > roi.mean()).mean(), (roi < roi.mean()).mean()) * 2
        score = round(float(roi.std() * (0.4 + sep)), 1)
        regions.append(dict(x=int(x), y=int(y), w=int(w), h=int(h),
                            score=score, area=int(w * h)))
    regions.sort(key=lambda r: -r["score"])
    return regions, img


def crop_regions(path, out_dir, top=6, pad=8):
    regions, img = find_text_regions(path)
    if not regions:
        return []
    os.makedirs(out_dir, exist_ok=True)
    made = []
    H, W = img.shape[:2]
    for i, r in enumerate(regions[:top], 1):
        x0 = max(0, r["x"] - pad); y0 = max(0, r["y"] - pad)
        x1 = min(W, r["x"] + r["w"] + pad); y1 = min(H, r["y"] + r["h"] + pad)
        crop = img[y0:y1, x0:x1]
        # 판독용이므로 크게 키운다
        sc = max(1, int(900 / max(1, crop.shape[1])))
        if sc > 1:
            crop = cv2.resize(crop, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC)
        p = os.path.join(out_dir, f"region_{i:02d}_s{int(r['score'])}.jpg")
        cv2.imwrite(p, crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
        made.append((p, r))
    # 표시 이미지
    vis = img.copy()
    for i, r in enumerate(regions[:top], 1):
        cv2.rectangle(vis, (r["x"], r["y"]), (r["x"]+r["w"], r["y"]+r["h"]),
                      (0, 220, 255), 2)
        cv2.putText(vis, str(i), (r["x"], max(14, r["y"]-6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
    vp = os.path.join(out_dir, "_regions.jpg")
    cv2.imwrite(vp, vis)
    return made


# ── OCR 전수 시도 ─────────────────────────────────────────

def ocr_all(path, lang="eng", psms=(6, 7, 11, 12)):
    if not HAS_OCR:
        return []
    results = []
    for name, img in variants(path):
        for psm in psms:
            try:
                t = pytesseract.image_to_string(img, lang=lang,
                                                config=f"--psm {psm}").strip()
            except Exception:
                continue
            t = " ".join(t.split())
            if len(t) < 3:
                continue
            # 잡음 비율 — 의미 있는 문자의 비중
            good = sum(1 for c in t if c.isalnum() or '\uac00' <= c <= '\ud7a3'
                       or '\u4e00' <= c <= '\u9fff')
            ratio = good / max(1, len(t))
            results.append(dict(prep=name, psm=psm, text=t,
                                score=round(ratio * min(len(t), 60), 1)))
    results.sort(key=lambda r: -r["score"])
    # 중복 제거
    seen, uniq = set(), []
    for r in results:
        k = r["text"][:40]
        if k in seen:
            continue
        seen.add(k); uniq.append(r)
    return uniq


# ── 텍스트 식별 ───────────────────────────────────────────
# OCR이든 사람이 읽었든, 추출된 문자열에서 구조를 뽑는다.

# 다음 필드 이름이 나오면 값이 끝난 것으로 본다.
# 이것이 없으면 「UNIT ... SCENE ... ROLL ...」이 통째로 한 값이 된다.
_STOP = (r"(?=\s*(?:DATE|UNIT|SCENE|PROJECT|ROLL|CAMERAMAN|PHOTOG|OFFICER"
         r"|CAMERA|EFFECT|LOCATION|SOUND|TAKE|날짜|부대|과제|릴|촬영자|장소)\b|$)")

SLATE_FIELDS = {
    "date": r"(?:DATE|날짜)[\s:]*([0-9]{1,2}[/\-][0-9]{1,2}[/\-][0-9]{2,4}"
            r"|[0-9]{1,2}\s*[A-Z]{3,9}\.?\s*[0-9]{2,4}"
            r"|[A-Z]{3,9}\.?\s*[0-9]{1,2}[,\s]*[0-9]{2,4})" + _STOP,
    "unit": r"(?:UNIT|부대)[\s:]*([A-Z0-9][A-Z0-9\s\.\-]{2,30}?)" + _STOP,
    "scene": r"(?:SCENE|PROJECT|과제)[\s:]*([A-Z0-9][A-Z0-9\s\.\-]{2,30}?)" + _STOP,
    "roll": r"(?:ROLL|릴)[\s#:]*([0-9]{1,3})",
    "cameraman": r"(?:CAMERAMAN|촬영자|PHOTOG)[\s:]*([A-Z][A-Za-z\.\s,]{2,25}?)" + _STOP,
    "officer": r"(?:OFFICER[\s\w]*|담당관)[\s:]*((?:LT|CPT|MAJ|COL)?\.?\s*[A-Z][A-Za-z\.\s]{2,25})",
    "camera": r"(?:CAMERA(?!MAN)|기종)[\s:]*([A-Za-z][A-Za-z0-9\-]{2,15}?)" + _STOP,
    "location": r"(?:LOCATION|장소)[\s:]*([A-Z][A-Za-z\-\s]{2,25}?)" + _STOP,
}

# 당대 표기 — 판독된 지명이 어디인지 알려 준다
PLACE = {
    "SAISHU": "제주 (일본식 독음)", "QUELPART": "제주 (서구 관용)",
    "CHEJU": "제주", "JEJU": "제주",
    "KEIJO": "서울 (일제기 표기)", "KYONGSONG": "경성", "SEOUL": "서울",
    "FUSAN": "부산 (일본식)", "PUSAN": "부산 (구 로마자)", "BUSAN": "부산",
    "JINSEN": "인천 (일본식)", "CHEMULPO": "제물포", "INCHON": "인천",
    "KAIJO": "개성 (일본식)", "KAESONG": "개성",
    "HEIJO": "평양 (일본식)", "PYONGYANG": "평양",
    "TAIKYU": "대구 (일본식)", "TAEGU": "대구",
    "GENZAN": "원산 (일본식)", "WONSAN": "원산",
    "MUNSAN": "문산", "KOJE": "거제", "PANMUNJOM": "판문점",
    "UIJONGBU": "의정부", "YONG DONG PO": "영등포", "KUMWHA": "금화",
}

UNIT_HINT = [
    (r"SIGNAL\s*(?:C\s*)?CORPS", "통신대 (Signal Corps)"),
    (r"(\d+)(?:ST|ND|RD|TH)?\s*SIG(?:NAL)?\s*(?:SVC|SERVICE)?\s*(?:CO|BN|DET)",
     "통신 부대 — 번호 확인 요"),
    (r"DASPO", "국방부 특수사진파견대 (DASPO)"),
    (r"FE(?:C)?\s*SIGNAL", "극동 통신대 (Far East)"),
    (r"PHOTO\s*(?:SQ|SQUADRON)", "사진중대"),
    (r"(\d+)(?:ST|ND|RD|TH)\s*(?:INF|INFANTRY)\s*DIV", "보병사단"),
    (r"(?:F\.?A\.?|FIELD\s*ARTILLERY)\s*(?:BTRY|BATTERY)", "야전포병중대"),
    (r"CAVALRY", "기병연대"),
    (r"EUSAK|8TH\s*ARMY", "미 제8군"),
]

WARN_WORDS = [
    (r"\bETC\b", "「ETC」 — 표제가 가린 내용이 있을 수 있다. 전 구간 확인 필수"),
    (r";", "세미콜론 — 두 번째 주제가 있을 수 있다"),
]


def identify(text):
    t = text.upper()
    out = dict(fields={}, places=[], units=[], warnings=[], dates=[])

    for k, pat in SLATE_FIELDS.items():
        m = re.search(pat, t)
        if m:
            out["fields"][k] = " ".join(m.group(1).split())

    for k, v in PLACE.items():
        if k in t:
            out["places"].append(dict(found=k, means=v))

    for pat, label in UNIT_HINT:
        if re.search(pat, t):
            out["units"].append(label)

    for pat, msg in WARN_WORDS:
        if re.search(pat, t):
            out["warnings"].append(msg)

    # 날짜 후보 — 슬레이트 필드 밖에 있어도 잡는다
    for m in re.finditer(r"\b([0-9]{1,2})[/\-]([0-9]{1,2})[/\-]([0-9]{2,4})\b", t):
        a, b, c = m.groups()
        yr = int(c) if len(c) == 4 else (1900 + int(c) if int(c) > 30 else 2000 + int(c))
        out["dates"].append(dict(raw=m.group(0), reading=f"{yr}년 {int(a)}월 {int(b)}일",
                                 note="미군 자료는 월/일/년 순"))
    for m in re.finditer(r"\b([0-9]{1,2})\s*(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
                         r"[A-Z]*\.?\s*([0-9]{2,4})\b", t):
        d, mo, y = m.groups()
        mi = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"].index(mo)+1
        yr = int(y) if len(y) == 4 else (1900 + int(y) if int(y) > 30 else 2000 + int(y))
        out["dates"].append(dict(raw=m.group(0), reading=f"{yr}년 {mi}월 {int(d)}일"))
    for m in re.finditer(r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\.?\s*"
                         r"([0-9]{1,2})[,\s]+([0-9]{2,4})\b", t):
        mo, d, y = m.groups()
        mi = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"].index(mo)+1
        yr = int(y) if len(y) == 4 else (1900 + int(y) if int(y) > 30 else 2000 + int(y))
        out["dates"].append(dict(raw=m.group(0), reading=f"{yr}년 {mi}월 {int(d)}일"))
    return out


def print_identify(r):
    if r["fields"]:
        print("■ 슬레이트 필드")
        for k, v in r["fields"].items():
            print(f"  {k:<11} {v}")
    if r["dates"]:
        print("\n■ 날짜 후보")
        for d in r["dates"]:
            print(f"  {d['raw']:<14} → {d['reading']}"
                  + (f"   ({d['note']})" if d.get("note") else ""))
    if r["places"]:
        print("\n■ 지명")
        for p in r["places"]:
            print(f"  {p['found']:<14} → {p['means']}")
    if r["units"]:
        print("\n■ 부대 추정")
        for u in r["units"]:
            print(f"  {u}")
    if r["warnings"]:
        print("\n■ ⚠ 주의")
        for w in r["warnings"]:
            print(f"  {w}")
    if not any([r["fields"], r["dates"], r["places"], r["units"]]):
        print("  식별된 구조가 없습니다.")
    print("\n⚠ 식별 결과는 후보입니다. 원본 화면으로 반드시 육안 확인하십시오.")


# ── 종합 분석 ─────────────────────────────────────────────

def analyze(path, out_dir, lang, top):
    os.makedirs(out_dir, exist_ok=True)
    print("=" * 66)
    print(f"  이미지 분석 — {os.path.basename(path)}")
    print("=" * 66)

    im = cv2.imread(path)
    if im is None:
        print("이미지를 읽지 못했습니다.", file=sys.stderr); sys.exit(1)
    h, w = im.shape[:2]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    print(f"\n크기 {w}×{h} · 평균 밝기 {g.mean():.0f} · 대비 {g.std():.0f}")
    if g.std() < 25:
        print("  ⚠ 대비가 낮습니다 — 판독이 어려울 수 있습니다")
    if g.mean() < 45 or g.mean() > 215:
        print("  ⚠ 밝기가 극단적입니다 — 보정이 필요합니다")

    print("\n■ 문자 영역 탐지")
    made = crop_regions(path, out_dir, top=top)
    if made:
        for i, (p, r) in enumerate(made, 1):
            print(f"  {i}. 점수 {r['score']:>6}  위치 ({r['x']},{r['y']})"
                  f"  크기 {r['w']}×{r['h']}  →  {os.path.basename(p)}")
        print(f"\n  표시 이미지: {os.path.join(out_dir,'_regions.jpg')}")
    else:
        print("  문자 영역을 찾지 못했습니다.")

    print(f"\n■ OCR 시도 (lang={lang})")
    if not HAS_OCR:
        print("  pytesseract 미설치 — 건너뜁니다")
    else:
        res = ocr_all(path, lang=lang)[:5]
        if res:
            for r in res:
                print(f"  [{r['score']:>5}] {r['prep']:<7} psm{r['psm']:<3} {r['text'][:60]}")
        else:
            print("  읽어낸 문자가 없습니다.")
        joined = " ".join(r["text"] for r in res)
        if joined.strip():
            print("\n■ 식별")
            print_identify(identify(joined))

    print("\n" + "=" * 66)
    print("  ⚠ OCR은 보조 도구입니다")
    print("=" * 66)
    print("  사료 프레임은 저해상도·그레인·흔들림이 겹쳐 정확도가 낮습니다.")
    print("  손글씨·한자·세로쓰기는 사실상 실패합니다.")
    print("  잘라낸 region_*.jpg 를 직접 보고 판독하십시오.")
    print("  OCR 결과를 그대로 재기술에 옮기지 마십시오.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", nargs="?")
    ap.add_argument("--out", default="./img_analysis")
    ap.add_argument("--lang", default="eng")
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--ocr", action="store_true", help="OCR 결과만 출력")
    ap.add_argument("--regions", action="store_true", help="문자 영역만 잘라내기")
    ap.add_argument("--identify", help="추출된 텍스트를 식별")
    a = ap.parse_args()

    if a.identify:
        print_identify(identify(a.identify)); return
    if not a.image:
        ap.error("이미지 경로가 필요합니다 (또는 --identify)")

    if a.ocr:
        for r in ocr_all(a.image, lang=a.lang)[:8]:
            print(f"[{r['score']:>5}] {r['prep']:<8} psm{r['psm']:<3} {r['text']}")
        return
    if a.regions:
        made = crop_regions(a.image, a.out, top=a.top)
        for p, r in made:
            print(f"점수 {r['score']:>6}  →  {p}")
        return
    analyze(a.image, a.out, a.lang, a.top)


if __name__ == "__main__":
    main()
