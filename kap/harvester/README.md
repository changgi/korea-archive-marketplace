# korea-records-harvester — 논문 방법론 실행 구현

송창기(2026), **"An AI-based Systematic Methodology for Discovering and Semantically
Extracting Korea-related Records from Foreign Archives"** (국가기록원 기록관리교육센터,
논문 v20)의 수집·추출 파이프라인을 실행 가능한 코드로 구현한 패키지입니다.
키워드 정본은 동반 저장소 **korea-records-keywords v1.0.0** (MIT, `keywords/`)을 그대로 사용합니다.

## 논문 ↔ 구현 대응

| 논문 | 구현 | 상태 |
|---|---|---|
| §4 10단계 수집 파이프라인 (P1~8 재현율 → P9 RG 교차 정밀도 → P10 통합) | `harvester/nara.py` | NARA API 키 필요 (미소지 시 안내 종료) |
| §3.5 TNA 14 전략 레이어 (1,222 쿼리) | `harvester/tna.py run_layers()` | ✅ **실검증 완료** — T-01 파일럿 292건 실수집 |
| T-12/13 인용 역추적 + 인접 확장 (Adaptive Mining) | `harvester/tna.py adaptive_mine()` | ✅ **실검증 완료** — FO 371/84053 시드→84054 승격, 84052(일본) 배제 |
| §6 LLM 4계층 의미 추출 (출처 격리) | `harvester/extract_llm.py` | ANTHROPIC_API_KEY 필요 (미소지 시 생략) |
| Gallica(BnF) 프랑스어 세트 수집 (확장층 — 병인양요·선교사·프랑스대대) | `harvester/gallica.py` | ✅ **실검증** — 파일럿 5쿼리 고유 159건 (1886 선교회 지도 등) |
| Europeana 다국어 세트 수집 (58개국 통합, 확장층) | `harvester/europeana.py` | EUROPEANA_API_KEY 필요 (미소지 시 안내 종료) |
| §12형 검색 로그·재현성 | `harvester/util.py SearchLog` | ✅ 전 쿼리 자동 기록 |
| 3중 키 중복 제거 | `harvester/util.py Dedup` | ✅ |

## 빠른 시작

```bash
# 0) 의존성 없음 — Python 3.10+ 표준 라이브러리만

# 1) TNA 파일럿 (키 불요, 즉시 실행)
python cli.py tna --pilot                 # 레이어당 3쿼리
python cli.py tna                          # 전체 14레이어 1,222쿼리 (수 시간, sleep 준수)

# 2) 인용 역추적 + 인접 확장 (Adaptive Mining)
python cli.py mine                         # 21 시드 × ±15 = 651 참조 순회

# 2.5) Gallica(프랑스 국립도서관) — 키 불요, 구한말 프랑스 사료
python cli.py gallica --pilot              # 5쿼리 파일럿
python cli.py gallica                      # 프랑스어 세트 20쿼리 전체

# 2.6) Europeana(58개국 통합) — 무료 키
EUROPEANA_API_KEY=... python cli.py europeana --type VIDEO
#   → data/promoted_series.csv 의 승격 후보를 사람이 검증 후 정식 편입 (논문 승격률 93.0%)

# 3) NARA 10단계 (API 키: Catalog_API@nara.gov 발급 — 보고서 §31-2 템플릿)
NARA_API_KEY=... python cli.py nara --moving-images --pilot   # 영상 한정 파일럿
NARA_API_KEY=... python cli.py nara                            # 전체 552+63 쿼리

# 4) LLM 의미 추출 (출처 격리 — 환각 통제)
ANTHROPIC_API_KEY=... python cli.py extract data/tna_records.jsonl --limit 50
```

## 산출물 (`data/`)

- `tna_records.jsonl` / `nara_records.jsonl` — 수집 레코드 (참조코드·제목·기술·날짜·URL·발견 레이어/단계)
- `search_log_tna.csv` / `search_log_nara.csv` — §12형 검색 로그 (재현성 담보)
- `tna_mined.jsonl` + `promoted_series.csv` — 인접 확장 결과와 승격 후보
- `*_extracted.jsonl` — semantic 필드(topics·entities·event_date_links·summary_ko·confidence) 부가본

## 운용 수칙

1. **로그 없는 검색 금지** — 모든 쿼리는 SearchLog에 자동 기록된다.
2. **요청 예절** — 기본 sleep(1.0~1.2s)을 줄이지 말 것. NARA 키는 월 10,000쿼리 한도.
3. **승격 3단계** — mined 결과는 후보→사람 검증→정식 편입 순서를 지킨다(논문 §5).
4. **출처 격리** — LLM 추출은 카탈로그 기술만 근거로 하며, 결과의 confidence<0.7은 재검토 대상.
5. TNA Discovery는 bot형 User-Agent를 403 차단하므로 브라우저형 UA를 사용한다(연구 목적, 간격 준수).

## 라이선스·출처

- 키워드(`keywords/`): korea-records-keywords v1.0.0 — MIT © 2026 Song, Chang-Gi (`LICENSE-keywords`)
- 하베스터 코드: 동일 조건 사용 가능. 논문·저장소를 함께 인용할 것.
- 연계 문서: 「글로벌 아카이브 종합 보고서 v6.5」(08) · 「마스터 쿼리 코퍼스 v1.1」(09) §13
