# -*- coding: utf-8 -*-
"""LLM 4계층 의미 추출 (논문 §6) — 단일 호출로 ①주제 분류 ②개체명 인식(NER)
③사건-시기 연결 ④한국어 분석적 요약을 수행. 엄격한 출처 격리(source-isolation)
프롬프트 체제: 제공된 카탈로그 기술 외 외부 지식 사용 금지 → 환각 통제.

API: Anthropic Messages API (ANTHROPIC_API_KEY 환경변수). 표준 라이브러리만 사용.
"""
from __future__ import annotations
import json, os, sys, time, urllib.request
from .util import DATA, jsonl_writer, emit

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("HARVESTER_LLM_MODEL", "claude-haiku-4-5-20251001")

# 출처 격리 프롬프트 (논문 §6.2 체제 재구성): 근거 없는 생성 금지, 미상은 null, JSON만 출력
SYSTEM = """You are an archival semantic extraction module for Korea-related records.
STRICT SOURCE ISOLATION: Use ONLY the catalog description provided by the user.
Do NOT use external knowledge to add facts not present in the text.
If a field cannot be determined from the text alone, use null or [].
Output ONLY valid JSON, no prose."""

PROMPT = """Catalog record (sole source):
---
TITLE: {title}
DATE: {date}
REFERENCE: {ref}
SOURCE ARCHIVE: {src}
---
Extract as JSON:
{{
 "topics": [up to 3 from: independence-movement, liberation-1945, us-military-government,
            division-38th, korean-war-combat, armistice-pow, reconstruction, colonial-rule,
            premodern-diplomacy, society-culture, intelligence-propaganda, other],
 "entities": [{{"text": "...", "type": "PERSON|ORG|PLACE|UNIT|EVENT"}}],
 "event_date_links": [{{"event": "...", "date": "as stated in text or null"}}],
 "summary_ko": "카탈로그 기술만 근거로 한 2~3문장 한국어 분석 요약",
 "korea_relevance": 0.0~1.0,
 "confidence": 0.0~1.0
}}"""

def _call(api_key: str, title: str, date: str, ref: str, src: str) -> dict:
    body = json.dumps({
        "model": MODEL, "max_tokens": 700,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": PROMPT.format(
            title=title or "", date=date or "", ref=ref or "", src=src or "")}],
    }).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "Content-Type": "application/json", "x-api-key": api_key,
        "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode())
    txt = "".join(b.get("text", "") for b in data.get("content", []))
    txt = txt.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(txt)

def run(in_path: str, out_path: str | None = None, limit: int | None = None, sleep: float = 0.5):
    """JSONL 레코드에 semantic 필드 부가 → *_extracted.jsonl.
    ANTHROPIC_API_KEY 없으면 건너뛰고 안내만 출력(파이프라인은 추출 없이도 완결)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY 미설정 — 의미 추출 단계 생략(수집 산출물은 유효). "
              "키 설정 후 재실행하면 기존 수집분에 추출을 부가한다.")
        return 0
    out_path = out_path or in_path.replace(".jsonl", "_extracted.jsonl")
    out = jsonl_writer(out_path); n = 0
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            if limit and n >= limit: break
            rec = json.loads(line)
            try:
                sem = _call(api_key, rec.get("title"), rec.get("date"),
                            rec.get("local_id") or rec.get("naid") or rec.get("tna_id"), rec.get("src"))
                rec["semantic"] = sem
            except Exception as e:
                rec["semantic_error"] = str(e)
            emit(out, rec); n += 1; time.sleep(sleep)
    out.close()
    print(f"[extract] {n}건 → {out_path}")
    return n
