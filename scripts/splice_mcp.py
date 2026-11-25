#!/usr/bin/env python3
"""플러그인 server.py → mcp/server.py 본문 동기화(스플라이스).

mcp/server.py의 머리말(실행 경로 설정)은 보존하고 'from mcp.server.fastmcp' 이후를 플러그인 사본으로 교체한다.
서버를 고친 뒤 항상 실행 → py_compile → 커밋. korea-archive-mcp CI(ci-parity.mjs)가 두 본문의 일치를 검사한다.
사용: python3 scripts/splice_mcp.py   (저장소 루트 어디서든)
"""
import pathlib
import py_compile
import sys

R = pathlib.Path(__file__).resolve().parent.parent
K = 'from mcp.server.fastmcp'
src = (R / 'plugins/korea-archive/servers/server.py').read_text(encoding='utf-8')
dst = R / 'mcp/server.py'
old = dst.read_text(encoding='utf-8')
if K not in src or K not in old:
    sys.exit('기준 줄(from mcp.server.fastmcp)을 찾지 못함')
new = old.split(K, 1)[0] + src[src.index(K):]
if new == old:
    print('이미 일치 — 변경 없음')
else:
    dst.write_text(new, encoding='utf-8')
    print('mcp/server.py 갱신')
py_compile.compile(str(dst), doraise=True)
print('py_compile OK')
