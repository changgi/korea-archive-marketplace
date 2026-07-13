#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profiles — 전 기관 3층 프로파일 애그리게이터.
기관별 profile_<key>.py 를 취합해 PROFILES 딕셔너리를 노출한다(자료구조/이용구조/활용구조).
source_profile 도구가 사용. Soli Deo Gloria.
"""
import profile_tna
import profile_nara
import profile_ia
import profile_gallica
import profile_europeana
import profile_nedb
import profile_archives
import profile_nlk
import profile_seoul
import profile_warmemo
import profile_foia

PROFILES = {
    "tna": profile_tna.PROFILE,
    "nara": profile_nara.PROFILE,
    "ia": profile_ia.PROFILE,
    "gallica": profile_gallica.PROFILE,
    "europeana": profile_europeana.PROFILE,
    "nedb": profile_nedb.PROFILE,
    "archives": profile_archives.PROFILE,
    "nlk": profile_nlk.PROFILE,
    "seoul": profile_seoul.PROFILE,
    "warmemo": profile_warmemo.PROFILE,
    "foia": profile_foia.PROFILE,
}

if __name__ == "__main__":
    for _k, _v in PROFILES.items():
        print(f"{_k}: {_v['name_ko']} [{_v['category']}] verify={_v['verify']['accurate'] if _v['verify'] else None}")
