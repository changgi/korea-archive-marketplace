"""keywords — 해외 아카이브 한국 관련 기록 발굴 키워드 프레임워크 (논문 3장 / 부록 B)"""
from .keywords_common import COMMON_GROUPS
from .keywords_nara import NARA_GROUPS, ONLINE_PRIORITY, RG_MAP
from .keywords_tna import TNA_LAYERS, TNA_DEPT_CODES, CITATION_SEEDS, generate as generate_tna_queries

__all__ = ["COMMON_GROUPS", "NARA_GROUPS", "ONLINE_PRIORITY", "RG_MAP",
           "TNA_LAYERS", "TNA_DEPT_CODES", "CITATION_SEEDS", "generate_tna_queries"]
