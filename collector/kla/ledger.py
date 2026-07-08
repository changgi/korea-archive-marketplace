# -*- coding: utf-8 -*-
"""수집대장 (보고서 §28 — 17필드 스키마) + 권리 등급 자동 초기판정 (§30 5단계의 1~3단계).

원칙(§29): 출처주의 — archive/rg_series 공란 금지 · 진본성 — checksum 필수 ·
기록되지 않은 작업은 없었던 작업이다(§32).
"""
from __future__ import annotations
import csv, json, os, time

FIELDS = ["collection_id","title_orig","title_ko","archive","rg_series","local_id","naid",
          "date_content","format_orig","duration_ft","access_url","acq_status",
          "file_path","checksum","rights_class","rights_note","verified_date","research_topic"]

def auto_rights(rec: dict) -> tuple[str, str]:
    """§30 권리 판단 플로 1~3단계 자동 초기판정. 최종 확정은 사람이 한다(판정 근거 서면화).
    반환: (rights_class, rights_note)"""
    rg = (rec.get("rg_series") or "").upper()
    arch = (rec.get("archive") or "").upper()
    if "RG 242" in rg or rg.startswith("242"):
        return "D", "[자동초판] RG 242 노획필름 — 원산국 권리 잔존 가능(NARA 미보증, 36 CFR 1254.62). 이용자 책임 · 재검토 연1회"
    if "UNIVERSAL" in (rec.get("title_orig") or "").upper() or "200-UN" in rg:
        return "B", "[자동초판] Universal Newsreel — MCA가 1970년대 권리를 미 정부에 양도(NARA newsreels 페이지). 릴 내 제3자 콘텐츠 QC 필요"
    if any(x in rg for x in ("RG 111","RG 208","RG 306","RG 342","RG 428","RG 127","111-","208-","306-")):
        return "B", "[자동초판] 미 연방정부 직무저작물 추정(17 U.S.C. §105) — 카탈로그 Use Restriction 'Unrestricted' 확인 시 A로 상향"
    if "KOFA" in arch or "KBS" in arch:
        return "C", "[자동초판] 한국 저작물 — 저작권 존속 전제, 허가 취득 후 공개"
    return "D", "[자동초판] 지위 불명 — §30 플로 수동 수행 필요"

class Ledger:
    def __init__(self, path: str):
        self.path = path
        self.rows: list[dict] = []
        self._keys = set()
        if os.path.exists(path):
            with open(path, encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    self.rows.append(r); self._keys.add(self._key(r))
    def _key(self, r: dict) -> str:
        for k in ("local_id","naid"):
            if r.get(k): return f"{k}:{str(r[k]).lower()}"
        return "tt:" + (r.get("title_orig","") or "").lower()[:120]
    def has(self, r: dict) -> bool: return self._key(r) in self._keys
    def next_id(self) -> str:
        y = time.strftime("%Y")
        n = sum(1 for r in self.rows if (r.get("collection_id") or "").startswith(f"KLA-{y}")) + 1
        return f"KLA-{y}-{n:04d}"
    def add(self, rec: dict) -> dict | None:
        """3중 키 중복 대조(§28-3) 후 등록. 권리 미지정 시 자동 초기판정."""
        if self.has(rec): return None
        rec = {k: rec.get(k, "") for k in FIELDS}
        rec["collection_id"] = rec["collection_id"] or self.next_id()
        if not rec["rights_class"]:
            rec["rights_class"], rec["rights_note"] = auto_rights(rec)
        rec["acq_status"] = rec["acq_status"] or "목록화"
        self.rows.append(rec); self._keys.add(self._key(rec))
        return rec
    def update(self, collection_id: str, **kw):
        for r in self.rows:
            if r["collection_id"] == collection_id:
                r.update({k: v for k, v in kw.items() if k in FIELDS}); return r
    def save(self):
        with open(self.path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(self.rows)
    def stats(self) -> dict:
        from collections import Counter
        return {"total": len(self.rows),
                "rights": dict(Counter(r["rights_class"] for r in self.rows)),
                "status": dict(Counter(r["acq_status"] for r in self.rows)),
                "with_file": sum(1 for r in self.rows if r["file_path"]),
                "verified": sum(1 for r in self.rows if r["verified_date"])}
