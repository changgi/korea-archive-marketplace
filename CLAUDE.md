# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A **Claude plugin marketplace** that discovers Korea-related records (1860–1960) scattered across 14 archives — overseas (NARA, TNA/UK, archive.org, Gallica/BnF, Europeana) and domestic Korean institutions (한국사DB, 국가기록원, 국립중앙도서관, 정보공개포털, 서울기록원, 전쟁기념관, etc.). It packages a peer-validated discovery methodology (Song 2026, F1 = 0.931) into MCP tools and a skill that Claude invokes automatically.

The user-facing deliverable is the **`korea-archive` plugin** (installed via `/plugin marketplace add changgi/korea-archive-marketplace`) plus a hosted MCP connector at `https://korea-archive-mcp.vercel.app/api/mcp`. The `harvester/` and `collector/` packages are the standalone research/batch-collection implementations of the same methodology (the paper's pipeline), not shipped in the plugin.

Documentation is primarily in Korean; code, identifiers, and tool names are English.

## Core domain concept — the "structural mismatch"

Korea records are undiscoverable by naive search because they were cataloged in the vocabulary of their era, along three dimensions (this drives nearly every design decision):

1. **Linguistic** — spelling variants. Seoul was indexed as **Keijo** (1910–45), Busan as *Fusan*, Incheon as *Jinsen/Chemulpo*, Korea itself as *Chosen/Corea/Tyosen*. Searches MUST inject period spellings in parallel, not just "Korea"/"Seoul".
2. **Taxonomic** — records hide inside Record Groups / ministry codes (NARA RG 242, TNA `FO 371` + FK codes). Recall-first broad scans, then RG/code cross-filters.
3. **Descriptive** — "0 results ≠ absence." ~7.5M NARA catalog cards are not digitized; a zero hit is recorded as a "not-yet-digitized candidate," never a dead end. Adjacent mining (piece ±15, box ±2) surfaces uncatalogued files.

## Repository layout & the vendoring relationship (important)

This repo contains the **same tool code in two places**. Understand this before editing:

- **`plugins/korea-archive/`** — the shipped plugin. `servers/server.py` is the canonical, full **18-tool** MCP server. Its `servers/harvester/`, `servers/keywords/`, `servers/kla/` are **vendored copies** of the top-level packages so the plugin is self-contained (`.mcp.local.json.example` runs `servers/server.py` via stdio). Note: `gallica_search`, `europeana_search`, `report_template`, and all 8 domestic-archive tools are inlined directly into this `server.py` (not as separate `harvester/` modules).
- **`mcp/server.py`** — a smaller **7-tool** dev server that imports from the *top-level* `harvester/`, `keywords/`, `collector/` via `sys.path`. Older/subset of the plugin server.
- **`harvester/`** — standalone paper-pipeline CLI (`cli.py`): TNA 14-layer sweep, NARA 10-stage, adaptive mining, Gallica, Europeana, LLM semantic extraction. Std-lib only except `extract_llm.py`.
- **`collector/`** — `klactl.py` CLI + `kla/` package: the "수집대장" (acquisition ledger, 17 fields), automatic rights triage, link re-verification, monitoring, HTML dashboard. Std-lib only.
- **`keywords/`** — the validated keyword corpus (`keywords_common.py`, `keywords_nara.py`, `keywords_tna.py`), MIT-licensed separately. The source of truth for `query_bank` groups, RG cross-mappings, and TNA layers.
- **`skill/`** and **`plugins/korea-archive/skills/korea-archive-discovery/`** — the discovery skill (search strategy Claude applies automatically). The plugin copy is the fuller/canonical one; `skill/` at the root is an older copy.
- **`.claude-plugin/marketplace.json`** — marketplace manifest. **`docs/`** — generated HTML reports. **`cap_*.png` / `docs/cards/`** — gallery card images.

**When you change tool behavior, update it in `plugins/korea-archive/servers/server.py` (canonical) and keep the vendored `servers/{harvester,keywords,kla}/` in sync with their top-level counterparts.** A change to a single top-level module is not live in the plugin until the vendored copy is updated. The hosted Vercel connector must be redeployed to reflect server changes.

## Commands

No build step, no test suite. Pure Python 3.10+ standard library (except optional `mcp` package and `ANTHROPIC_API_KEY`-gated LLM extraction).

```bash
# End-to-end smoke test (TNA pilot → seed ledger → verify → dashboard)
bash scripts/quickstart.sh

# --- harvester (run from harvester/) ---
python cli.py tna --pilot            # 3 queries/layer, no key, instant
python cli.py tna                     # full 14 layers / 1,222 queries (hours; respects sleep)
python cli.py tna --layers T-01 T-12  # specific layers only
python cli.py mine                    # adaptive mining (citation trace + adjacency)
python cli.py gallica --pilot         # BnF French sources, no key
EUROPEANA_API_KEY=... python cli.py europeana --type VIDEO
NARA_API_KEY=... python cli.py nara --moving-images --pilot
ANTHROPIC_API_KEY=... python cli.py extract data/tna_records.jsonl --limit 50

# --- collector (run from collector/) ---
python klactl.py seed                 # register 17 verified seeds + auto rights
python klactl.py fetch --max-mb 500   # download originals + SHA-256 (gates large files)
python klactl.py verify               # re-check links → verified_date
python klactl.py monitor --since 2026-07-01
python klactl.py dash                 # → data/dashboard.html
python klactl.py stats

# --- MCP server locally ---
pip install mcp
python plugins/korea-archive/servers/server.py   # full 18-tool plugin server (stdio)
python mcp/server.py                              # smaller dev server
```

Optional env keys (all optional; most tools work keyless): `NARA_API_KEY`, `EUROPEANA_API_KEY` (falls back to shared `api2demo` key), `ARCHIVES_API_KEY` (data.go.kr 15000153), `NLK_API_KEY`, `ANTHROPIC_API_KEY`.

## Domestic-tool auto-browsing pattern

The 8 domestic tools handle JS-rendered / login-gated Korean sites with a two-tier fallback (see the `_http_text` / `_agent_browse` helpers in `server.py`):

1. **Server-side fetch & parse** — the tool fetches the site directly and regex-parses real results (decision-document lists, category hit-counts, matching DBs/collections).
2. **Agent hand-off** — when a site needs a key that isn't set, or blocks server fetch, the tool returns an *instruction to the agent* (via `_agent_browse`) to gather results with WebSearch or its browser tool and present them as a table. `scrape_plan(url)` checks robots.txt and advises which path to take.

## Conventions & operating rules

- **No search without a log.** Every harvester query is auto-recorded to a `SearchLog` (§12 format) in `data/search_log_*.csv`. Reproducibility is mandatory.
- **Politeness / rate limits.** Do not reduce the default `sleep` (≈1.0–1.2s). Use a browser-style `User-Agent` — TNA Discovery 403s bot-style UAs. NARA key = 10,000 queries/month.
- **Rights triage is an initial pass only.** `judge_rights` / `ledger.auto_rights()` return A/B (releasable) / C (permission needed) / **D (status unknown — never publish)**. A human must finalize per the report's §30 5-step flow before any release. RG 242 captured film → D.
- **Promotion is 3-stage.** Mined/adjacent results go candidate → human verification → formal inclusion (never auto-promote).
- **Source isolation for LLM extraction.** `extract_llm.py` reasons only from catalog descriptions; `confidence < 0.7` is flagged for review.
- **Spelling variants are non-negotiable** in any search you construct — inject period romanizations (`query_cheatsheet.md`), and AND-combine ambiguous terms like "Chosen" with `newsreel`/`Japan`/`film`.
- **HTML discovery report is the default final artifact.** After a discovery task, don't stop at a table — generate a styled report via the skill's `report_template.html` / the `report_template` MCP tool, following its 11 rules (rights badges, reproducible query table, "0 results ≠ absence" note, ethical-use note for sensitive topics like comfort women / POWs / massacres).

## Versioning

The version string is duplicated across `.claude-plugin/marketplace.json` (marketplace + plugin entry), `plugins/korea-archive/.claude-plugin/plugin.json`, and both READMEs. Bump them together and add a `CHANGELOG.md` entry. Current: **1.10.1**.
