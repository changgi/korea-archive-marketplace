#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
echo "1) TNA 파일럿 발굴"; (cd harvester && python3 cli.py tna --pilot)
echo "2) 시드 등록·검증·대시보드"; (cd collector && python3 klactl.py seed && python3 klactl.py verify --limit 5 && python3 klactl.py dash)
echo "완료 — collector/data/dashboard.html 확인"
