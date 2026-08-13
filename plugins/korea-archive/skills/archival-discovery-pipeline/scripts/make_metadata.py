#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메타데이터 구조화 · 온톨로지 변환 · KARDA 연동

사용법
    # 판독 결과(JSON) → 여러 형식으로 한꺼번에
    python make_metadata.py build <판독.json> --out <디렉터리>

    # 개별 변환
    python make_metadata.py jsonld <판독.json>          # RiC-O + CIDOC-CRM
    python make_metadata.py karda  <판독.json> --out .  # 노드·엣지 CSV
    python make_metadata.py dc     <판독.json>          # Dublin Core
    python make_metadata.py check  <판독.json>          # 필수 항목 검사

판독 JSON 스키마 (최소)
    {
      "id": "111-ADC-7115",
      "naid": "20887",
      "title_original": "MAY DAY IN KOREA, CHEJU-DO",
      "title_ko": "제주, 1948년 4월 30일",
      "repository": "NARA",
      "record_group": "RG 111-ADC",
      "duration_sec": 401,
      "date": {"value": "1948-04-30", "basis": "slate", "confidence": "확정"},
      "readings": [
        {"time": 12, "target": "slate", "text": "DATE 4/30/48 UNIT FE SIGNAL C CORPS",
         "method": "VLM 3회 교차", "confidence": "확정"}
      ],
      "entities": {
        "places":  [{"name": "제주", "as_written": "CHEJU", "confidence": "확정"}],
        "agents":  [{"name": "SHAYDAK", "role": "촬영자", "confidence": "확정"}],
        "units":   [{"name": "FE Signal Corps", "confidence": "높음"}],
        "events":  [{"name": "무장 초소 설치", "confidence": "부분"}]
      },
      "unconfirmed": ["벽보 전문 판독 실패", "인물 비정 안 함"],
      "publication": {"tier": 1, "reason": ""},
      "rights": {"grade": "B", "basis": "17 U.S.C. §105"},
      "relations": [
        {"type": "sibling_of", "target": "111-ADC-7114", "basis": "동일 과제 FEC 67"},
        {"type": "precedes",   "target": "111-ADC-7122", "basis": "시간순"}
      ]
    }

왜 구조화하는가
    재기술 결과가 문서 안에만 있으면 그 한 건에서 끝난다.
    구조화하면 여러 건을 이어 붙일 수 있고, 관계 발견의 입력이 된다.
    「이 부대가 이 시기에 이 지역에서 찍었다」 같은 질의가 가능해진다.
"""
import argparse, json, os, sys, csv, re
from datetime import datetime

# 신뢰도 등급 — 낮은 것은 확정 사실로 내보내지 않는다
CONF_RANK = {"확정": 4, "높음": 3, "부분": 2, "불가": 1, "": 0}
EXPORT_MIN = 3          # 「높음」 이상만 온톨로지 트리플로 내보낸다

# 관계 유형 — KARDA 엣지 라벨
RELATIONS = {
    "sibling_of":   ("자매편", "동일 과제·연속 릴"),
    "precedes":     ("선행", "시간순 앞"),
    "follows":      ("후행", "시간순 뒤"),
    "same_event":   ("동일 사건", "같은 사건의 다른 시점·장소"),
    "same_agent":   ("동일 촬영자", "촬영자 일치"),
    "same_unit":    ("동일 부대", "촬영 부대 일치"),
    "same_place":   ("동일 장소", "촬영지 일치"),
    "series_of":    ("계열", "같은 계열에 속함"),
    "corrects":     ("정정", "원 기술의 오류를 바로잡음"),
}


def load(p):
    d = json.load(open(p, encoding="utf-8"))
    return d if isinstance(d, list) else [d]


def ok(conf):
    return CONF_RANK.get(conf, 0) >= EXPORT_MIN


# ── 필수 항목 검사 ────────────────────────────────────────

def cmd_check(a):
    recs = load(a.src)
    bad = 0
    for r in recs:
        rid = r.get("id", "(id 없음)")
        problems = []
        for k in ("id", "title_original", "repository"):
            if not r.get(k):
                problems.append(f"필수 항목 없음: {k}")
        if not r.get("title_ko"):
            problems.append("한국어 제목 없음 — 검색 가능성이 떨어진다")
        if not r.get("unconfirmed"):
            problems.append("**확인하지 못한 것이 비어 있다** — 재기술 미완결")
        if not r.get("readings"):
            problems.append("판독 기록 없음")
        for rd in r.get("readings", []):
            if not rd.get("method"):
                problems.append(f"판독({rd.get('target','?')})에 방법 미기재 — 재검증 불가")
            if not rd.get("confidence"):
                problems.append(f"판독({rd.get('target','?')})에 신뢰도 미기재")
        if r.get("date") and not r["date"].get("basis"):
            problems.append("날짜의 근거 미기재")
        if not r.get("rights", {}).get("grade"):
            problems.append("권리 등급 미판정")
        if r.get("publication", {}).get("tier", 1) >= 3 and not r["publication"].get("reason"):
            problems.append("게재 제한인데 사유 미기재")

        if problems:
            bad += 1
            print(f"\n!! {rid}")
            for p in problems:
                print(f"     {p}")
        else:
            print(f"OK {rid}")
    print()
    print(f"{len(recs)}건 중 {bad}건에 조치 필요" if bad else f"{len(recs)}건 모두 통과")
    return bad


# ── JSON-LD (RiC-O + CIDOC-CRM) ──────────────────────────
# RiC-O: 국제기록평의회 Records in Contexts — 기록 기술 표준
# CIDOC-CRM: 문화유산 정보 참조 모형 — 사건 중심 모형

CTX = {
    "rico": "https://www.ica.org/standards/RiC/ontology#",
    "crm": "http://www.cidoc-crm.org/cidoc-crm/",
    "dct": "http://purl.org/dc/terms/",
    "schema": "https://schema.org/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "kad": "https://example.org/karda/",     # 로컬 확장 — 발굴 고유 속성
}


def to_jsonld(r):
    rid = r["id"]
    base = f"kad:record/{rid}"
    g = []

    rec = {
        "@id": base,
        "@type": ["rico:Record", "crm:E31_Document"],
        "rico:identifier": rid,
        "rico:title": r.get("title_original"),
        "dct:title": r.get("title_ko") or r.get("title_original"),
        "rico:hasOrHadHolder": {"@id": f"kad:agent/{r.get('repository','unknown')}"},
        "rico:isOrWasIncludedIn": {"@id": f"kad:series/{r.get('record_group','unknown')}"},
    }
    if r.get("naid"):
        rec["skos:exactMatch"] = {"@id": f"https://catalog.archives.gov/id/{r['naid']}"}
    if r.get("duration_sec"):
        rec["schema:duration"] = f"PT{r['duration_sec']}S"

    # 날짜 — 근거와 신뢰도를 함께 싣는다
    d = r.get("date") or {}
    if d.get("value") and ok(d.get("confidence", "")):
        rec["rico:hasCreationDate"] = {
            "@type": "rico:DateSet", "rico:normalizedDateValue": d["value"],
            "kad:basis": d.get("basis"), "kad:confidence": d.get("confidence"),
        }
    elif d.get("value"):
        # 신뢰도가 낮으면 확정 속성이 아니라 주석으로만
        rec["kad:tentativeDate"] = {"@value": d["value"],
                                    "kad:confidence": d.get("confidence")}

    ent = r.get("entities", {})
    for pl in ent.get("places", []):
        if not ok(pl.get("confidence", "")):
            continue
        pid = f"kad:place/{re.sub(r'[^A-Za-z0-9가-힣]', '_', pl['name'])}"
        rec.setdefault("rico:hasOrHadSubject", []).append({"@id": pid})
        g.append({"@id": pid, "@type": ["rico:Place", "crm:E53_Place"],
                  "skos:prefLabel": pl["name"],
                  "skos:altLabel": pl.get("as_written"),
                  "kad:confidence": pl.get("confidence")})

    for ag in ent.get("agents", []):
        if not ok(ag.get("confidence", "")):
            continue
        aid = f"kad:agent/{re.sub(r'[^A-Za-z0-9가-힣]', '_', ag['name'])}"
        rec.setdefault("rico:hasCreator", []).append({"@id": aid})
        g.append({"@id": aid, "@type": ["rico:Agent", "crm:E39_Actor"],
                  "skos:prefLabel": ag["name"], "kad:role": ag.get("role"),
                  "kad:confidence": ag.get("confidence")})

    for un in ent.get("units", []):
        if not ok(un.get("confidence", "")):
            continue
        uid = f"kad:group/{re.sub(r'[^A-Za-z0-9가-힣]', '_', un['name'])}"
        rec.setdefault("rico:hasCreator", []).append({"@id": uid})
        g.append({"@id": uid, "@type": ["rico:Group", "crm:E74_Group"],
                  "skos:prefLabel": un["name"], "kad:confidence": un.get("confidence")})

    # 사건 — CIDOC-CRM의 중심 개념
    for ev in ent.get("events", []):
        if not ok(ev.get("confidence", "")):
            continue
        eid = f"kad:event/{re.sub(r'[^A-Za-z0-9가-힣]', '_', ev['name'])}"
        rec.setdefault("crm:P70_documents", []).append({"@id": eid})
        g.append({"@id": eid, "@type": ["rico:Event", "crm:E5_Event"],
                  "skos:prefLabel": ev["name"], "kad:confidence": ev.get("confidence")})

    # 판독 근거 — 재검증 가능하게
    for rd in r.get("readings", []):
        rec.setdefault("kad:hasReading", []).append({
            "kad:timecode": rd.get("time"), "kad:target": rd.get("target"),
            "kad:text": rd.get("text"), "kad:method": rd.get("method"),
            "kad:confidence": rd.get("confidence"),
        })

    # 확인하지 못한 것 — 이것도 데이터다
    if r.get("unconfirmed"):
        rec["kad:unconfirmed"] = r["unconfirmed"]

    # 게재·권리
    pub = r.get("publication", {})
    rec["kad:publicationTier"] = pub.get("tier", 1)
    if pub.get("reason"):
        rec["kad:publicationRestriction"] = pub["reason"]
    rt = r.get("rights", {})
    if rt.get("grade"):
        rec["rico:hasOrHadLegalStatus"] = rt["grade"]
        rec["dct:rights"] = rt.get("basis")

    # 관계
    for rel in r.get("relations", []):
        rec.setdefault("rico:isRelatedTo", []).append({
            "@id": f"kad:record/{rel['target']}",
            "kad:relationType": rel["type"], "kad:basis": rel.get("basis"),
        })

    g.insert(0, rec)
    return g


def cmd_jsonld(a):
    recs = load(a.src)
    graph = []
    for r in recs:
        graph += to_jsonld(r)
    out = {"@context": CTX, "@graph": graph,
           "kad:generatedAt": datetime.now().strftime("%Y-%m-%d"),
           "kad:note": "신뢰도 「높음」 이상만 확정 속성으로 내보냄. "
                       "「부분」 이하는 kad:tentative* 로 표기."}
    txt = json.dumps(out, ensure_ascii=False, indent=1)
    if getattr(a, "out", None):
        p = os.path.join(a.out, "metadata.jsonld")
        os.makedirs(a.out, exist_ok=True)
        open(p, "w", encoding="utf-8").write(txt)
        print(f"JSON-LD: {p}  (노드 {len(graph)}개)")
    else:
        print(txt)
    return out


# ── KARDA 노드·엣지 ──────────────────────────────────────
# 관계 발견 에이전트의 입력 형식.
# 기록·인물·장소·부대·사건을 모두 노드로 두고, 관계를 엣지로 낸다.

def cmd_karda(a):
    recs = load(a.src)
    nodes, edges = {}, []

    def add_node(nid, ntype, label, **kw):
        if nid not in nodes:
            nodes[nid] = dict(id=nid, type=ntype, label=label, **kw)

    def add_edge(s, t, rel, basis="", conf=""):
        ko, desc = RELATIONS.get(rel, (rel, ""))
        edges.append(dict(source=s, target=t, relation=rel, relation_ko=ko,
                          basis=basis, confidence=conf))

    for r in recs:
        rid = r["id"]
        add_node(rid, "record", r.get("title_ko") or r.get("title_original"),
                 date=(r.get("date") or {}).get("value", ""),
                 repository=r.get("repository", ""),
                 tier=r.get("publication", {}).get("tier", 1))

        ent = r.get("entities", {})
        for pl in ent.get("places", []):
            if not ok(pl.get("confidence", "")): continue
            nid = f"place:{pl['name']}"
            add_node(nid, "place", pl["name"], as_written=pl.get("as_written", ""))
            add_edge(rid, nid, "same_place", "촬영지", pl.get("confidence", ""))
        for ag in ent.get("agents", []):
            if not ok(ag.get("confidence", "")): continue
            nid = f"agent:{ag['name']}"
            add_node(nid, "agent", ag["name"], role=ag.get("role", ""))
            add_edge(rid, nid, "same_agent", ag.get("role", ""), ag.get("confidence", ""))
        for un in ent.get("units", []):
            if not ok(un.get("confidence", "")): continue
            nid = f"unit:{un['name']}"
            add_node(nid, "unit", un["name"])
            add_edge(rid, nid, "same_unit", "촬영 부대", un.get("confidence", ""))
        for ev in ent.get("events", []):
            if not ok(ev.get("confidence", "")): continue
            nid = f"event:{ev['name']}"
            add_node(nid, "event", ev["name"])
            add_edge(rid, nid, "same_event", "기록 대상", ev.get("confidence", ""))

        for rel in r.get("relations", []):
            add_node(rel["target"], "record", rel["target"])
            add_edge(rid, rel["target"], rel["type"], rel.get("basis", ""), "명시")

    os.makedirs(a.out, exist_ok=True)
    np_ = os.path.join(a.out, "karda_nodes.csv")
    ep = os.path.join(a.out, "karda_edges.csv")

    nkeys = sorted({k for n in nodes.values() for k in n})
    with open(np_, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=nkeys); w.writeheader()
        for n in nodes.values(): w.writerow(n)
    with open(ep, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["source", "target", "relation",
                                          "relation_ko", "basis", "confidence"])
        w.writeheader(); w.writerows(edges)

    print(f"KARDA 노드: {np_}  ({len(nodes)}개)")
    print(f"KARDA 엣지: {ep}  ({len(edges)}개)")
    from collections import Counter
    print("\n노드 유형:", dict(Counter(n["type"] for n in nodes.values())))
    print("관계 유형:", dict(Counter(e["relation_ko"] for e in edges)))
    print("\n관계 발견 질의 예")
    print("  · 같은 부대가 다른 지역에서 찍은 기록은?")
    print("  · 같은 촬영자의 다른 과제는?")
    print("  · 같은 사건을 다른 시점에서 담은 기록은?")
    return nodes, edges


# ── Dublin Core ──────────────────────────────────────────

def cmd_dc(a):
    for r in load(a.src):
        d = r.get("date") or {}
        rows = [
            ("dc:identifier", r["id"]),
            ("dc:title", r.get("title_ko") or r.get("title_original")),
            ("dc:alternative", r.get("title_original")),
            ("dc:type", "MovingImage"),
            ("dc:date", d.get("value", "") + (f" ({d.get('confidence')})" if d.get("confidence") else "")),
            ("dc:publisher", r.get("repository", "")),
            ("dc:isPartOf", r.get("record_group", "")),
            ("dc:rights", r.get("rights", {}).get("basis", "")),
        ]
        for pl in r.get("entities", {}).get("places", []):
            rows.append(("dc:spatial", pl["name"]))
        for ag in r.get("entities", {}).get("agents", []):
            rows.append(("dc:creator", f"{ag['name']} ({ag.get('role','')})"))
        print(f"\n■ {r['id']}")
        for k, v in rows:
            if v: print(f"  {k:<16} {v}")
        if r.get("unconfirmed"):
            print(f"  {'dc:description':<16} 미확인: " + " · ".join(r["unconfirmed"]))


# ── 일괄 ─────────────────────────────────────────────────

def cmd_build(a):
    print("=" * 64); print("  ① 필수 항목 검사"); print("=" * 64)
    bad = cmd_check(a)
    if bad:
        print("\n⚠ 조치가 필요한 항목이 있으나 변환은 계속합니다.")
    print("\n" + "=" * 64); print("  ② JSON-LD (RiC-O + CIDOC-CRM)"); print("=" * 64)
    cmd_jsonld(a)
    print("\n" + "=" * 64); print("  ③ KARDA 노드·엣지"); print("=" * 64)
    cmd_karda(a)
    print("\n" + "=" * 64)
    print("  신뢰도 「높음」 이상만 확정 속성으로 내보냈습니다.")
    print("  「부분」 이하는 kad:tentative* 로 표기되며 그래프에 실리지 않습니다.")
    print("=" * 64)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("build", "jsonld", "karda", "dc", "check"):
        p = sub.add_parser(n)
        p.add_argument("src")
        p.add_argument("--out", default=".")
    a = ap.parse_args()
    dict(build=cmd_build, jsonld=cmd_jsonld, karda=cmd_karda,
         dc=cmd_dc, check=cmd_check)[a.cmd](a)


if __name__ == "__main__":
    main()
