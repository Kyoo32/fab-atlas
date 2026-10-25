"""하이브리드 검색: dense 순위와 BM25 순위를 RRF(Reciprocal Rank Fusion)로 합쳐요.

RRF 점수 = Σ 1 / (k + 순위). 점수 크기가 아니라 순위만 써서, 단위가 다른 코사인 점수와 BM25 점수를
정규화하거나 가중치를 정할 필요가 없어요. k=60은 RRF를 제안한 논문(Cormack et al., 2009)의 기본값이에요.
"""

from __future__ import annotations

import numpy as np

RRF_K = 60


def ranks(scores: np.ndarray) -> np.ndarray:
    """점수 배열 → 순위 배열(1부터). 점수가 높을수록 순위가 앞이에요."""
    order = np.argsort(-scores, kind="stable")
    r = np.empty_like(order)
    r[order] = np.arange(1, len(scores) + 1)
    return r


def rrf(*score_lists: np.ndarray, k: int = RRF_K) -> np.ndarray:
    return sum(1.0 / (k + ranks(s)) for s in score_lists)
