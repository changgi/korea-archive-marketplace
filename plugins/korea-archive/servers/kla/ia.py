# -*- coding: utf-8 -*-
"""archive.org 클라이언트 — §27 Phase 0: 메타데이터 확인·시드 등록·원본 다운로드·SHA-256.
표준 라이브러리만 사용. 파일 네이밍 규칙(§28-2): {ID}_{소장처}_{식별자}_{연도}_{버전}.{ext}"""
from __future__ import annotations
import hashlib, json, os, re, time, urllib.request, urllib.parse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"

def _get(url: str, binary=False, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if binary else json.loads(data.decode("utf-8", "replace"))

def metadata(ia_id: str, timeout: int = 25) -> dict:
    return _get(f"https://archive.org/metadata/{urllib.parse.quote(ia_id)}", timeout=timeout)

def search(query: str, rows: int = 100, page: int = 1) -> dict:
    q = urllib.parse.quote(query)
    return _get(f"https://archive.org/advancedsearch.php?q={q}&fl[]=identifier&fl[]=title"
                f"&fl[]=date&fl[]=addeddate&rows={rows}&page={page}&output=json")

def pick_original(md: dict) -> dict | None:
    """원본(파생 제외) 영상 파일 1건 선택 — 크기 오름차순(파일럿에서 최소본부터)."""
    vids = [f for f in md.get("files", []) if f.get("source") == "original"
            and re.search(r"\.(mp4|mpeg|mpg|mov|avi|mkv)$", f.get("name",""), re.I)]
    if not vids:  # 파생본만 있으면 mp4 파생 허용(열람용)
        vids = [f for f in md.get("files", []) if re.search(r"\.mp4$", f.get("name",""), re.I)]
    return min(vids, key=lambda f: int(f.get("size", 1 << 40))) if vids else None

def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

def fname(rec: dict, ext: str) -> str:
    year = (rec.get("date_content") or "")[:4] or "0000"
    lid = re.sub(r"[^A-Za-z0-9.-]+", "-", rec.get("local_id") or rec.get("naid") or "x")
    return f"{rec['collection_id']}_NARA_{lid}_{year}_master{ext}"

def download(ia_id: str, rec: dict, dest_dir: str, max_bytes: int | None = None) -> dict | None:
    """원본 파일 다운로드 + 체크섬. max_bytes 초과 파일은 보류(대장에 '발주' 상태로)."""
    md = metadata(ia_id)
    f = pick_original(md)
    if not f: return None
    size = int(f.get("size", 0))
    if max_bytes and size > max_bytes:
        return {"skipped": True, "name": f["name"], "size": size}
    url = f"https://archive.org/download/{urllib.parse.quote(ia_id)}/{urllib.parse.quote(f['name'])}"
    ext = os.path.splitext(f["name"])[1].lower()
    path = os.path.join(dest_dir, fname(rec, ext))
    data = _get(url, binary=True, timeout=300)
    with open(path, "wb") as fh: fh.write(data)
    return {"path": path, "size": len(data), "sha256": sha256(path),
            "ia_file": f["name"], "ia_sha1_listed": f.get("sha1")}
