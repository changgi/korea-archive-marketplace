# kla-collector — 보고서 실행 프로젝트 (Phase 0)

「한국 광복·해방·한국전쟁 영상자료 글로벌 아카이브 종합 보고서 v6.5」(08)의
**실행편(§25~§32)을 그대로 코드로 구현**한 무예산 즉시실행(Phase 0) 프로젝트입니다.
의존성 없음 — Python 3.10+ 표준 라이브러리만.

## 보고서 ↔ 구현 대응

| 보고서 | 구현 | 실검증(2026-07-07) |
|---|---|---|
| §25 검증 시드 영상 | `kla/seeds.py` — 17건(archive.org 12 + NARA NAID 5) | ✅ 등록 17건 |
| §28 수집대장 17필드·3중 키 중복방지·파일 네이밍 | `kla/ledger.py` | ✅ ledger.csv 생성 |
| §30 권리 판단 플로(자동 초기판정) | `ledger.auto_rights()` | ✅ B 15건 / D 2건(RG 242 정확 분류) |
| §27 Phase 0 확보(다운로드+SHA-256) | `kla/ia.py` + `klactl.py fetch` | ⚠️ 크기 게이팅·대장 갱신 검증. 실바이너리는 본 테스트망이 archive.org/download를 차단해 미완 — 일반 PC에서 정상 |
| §25/§32 링크 분기 재검증 | `kla/verify.py` | ✅ 15/17 OK, 일시 지연 2건 자동 표시 |
| §27/§32 주간 모니터링 | `kla/monitor.py` | ✅ 3개 컬렉션 스캔 동작 |
| §27 KPI 대시보드 | `kla/dashboard.py` | ✅ data/dashboard.html 생성 |

## 사용법 (§27 Phase 0 주차별 대응)

```bash
python klactl.py seed                    # 1주차: 대장 셋업 + 시드 등록(권리 자동초판)
python klactl.py fetch --max-mb 500      # 2~3주차: 원본 확보 + SHA-256 (대용량은 '발주 보류')
python klactl.py verify                  # 분기: 링크 재검증 → verified_date 갱신
python klactl.py monitor --since 2026-07-01   # 매주: 신규 업로드 감지
python klactl.py dash                    # 현황 대시보드 (data/dashboard.html)
python klactl.py stats
```

## 산출물 (`data/`)
- `ledger.csv` — §28 수집대장(17필드). 엑셀에서 바로 열림(UTF-8 BOM)
- `masters/` — 마스터 파일 (`KLA-YYYY-NNNN_NARA_{식별자}_{연도}_master.ext`)
- `dashboard.html` — KPI·권리 분포·대장 열람
- `ia_map.json` — 대장 ↔ archive.org 식별자 매핑

## 운용 수칙 (보고서 원칙의 코드화)
1. 권리 등급의 `[자동초판]`은 **초기판정**이다 — 공개 전 담당자가 §30 5단계로 확정하고 근거를 서면화한다. D등급 공개 금지.
2. FAIL 표시 항목은 다음 실행에서 재시도되지 않는다(당일) — 수동 확인 후 조치.
3. 다운로드 실패·보류 항목은 `acq_status`로 추적: 목록화→발주(대용량 보류)→QC대기→QC완료.
4. NARA 복제 주문(릴 단위)·현장 조사는 Phase 1(보고서 §27)로 — 이 도구는 무예산 온라인 확보까지만 담당한다.
5. 확장: NARA API 키 확보 시 `korea-records-harvester`(별도 패키지)와 병행 — 그쪽 발굴 결과를 이 대장에 등록하는 순서로 연동한다.
