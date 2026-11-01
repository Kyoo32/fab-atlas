"""하이브리드 검색: 여러 검색기의 순위를 RRF(Reciprocal Rank Fusion)로 합쳐요.

RRF 점수 = Σ 1 / (k + 순위). 점수 크기가 아니라 순위만 써서, 단위가 다른 코사인 점수와 BM25 점수를
정규화하거나 가중치를 정할 필요가 없어요. k=60은 RRF를 제안한 논문(Cormack et al., 2009)의 기본값이에요.

기본 검색기(D-019, D-020): dense(한국어 질문) + dense(번역 질의) + BM25(번역 질의).
번역은 BM25용으로 한 번 만들고 dense에도 같이 써서, 질문마다 LLM 호출은 한 번이에요.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fabatlas.bm25 import BM25Index, tokenize
from fabatlas.embedding import Index, embed_texts
from fabatlas.search import Hit
from fabatlas.translate import Translation, translate_query

RRF_K = 60


def ranks(scores: np.ndarray) -> np.ndarray:
    """점수 배열 → 순위 배열(1부터). 점수가 높을수록 순위가 앞이에요."""
    order = np.argsort(-scores, kind="stable")
    r = np.empty_like(order)
    r[order] = np.arange(1, len(scores) + 1)
    return r


def rrf(*score_lists: np.ndarray, k: int = RRF_K) -> np.ndarray:
    return sum(1.0 / (k + ranks(s)) for s in score_lists)


@dataclass
class HybridResult:
    hits: list[Hit]            # score는 RRF 점수예요
    translation: Translation   # BM25와 dense(번역)에 쓴 영어 질의
    ranks: dict[str, dict[str, int]]  # chunk_id → 검색기별 순위 (설명·디버깅용)


def hybrid_search(index: Index, bm25: BM25Index, model, question: str, k: int = 5,
                  translation: Translation | None = None) -> HybridResult:
    """dense(한국어) + dense(번역) + BM25(번역)를 RRF로 합쳐 상위 k개를 골라요(D-020)."""
    tr = translation or translate_query(question)
    q_ko, q_en = embed_texts(model, [question, tr.query])
    scores = {
        "dense_ko": index.embeddings @ q_ko,   # 정규화돼 있어 내적 = 코사인
        "dense_en": index.embeddings @ q_en,
        "bm25_en": bm25.bm25.get_scores(tokenize(tr.query)),
    }
    fused = rrf(*scores.values())
    order = np.argsort(-fused, kind="stable")[:k]
    per = {name: ranks(sc) for name, sc in scores.items()}
    hits = [Hit(rank=r + 1, score=float(fused[i]), chunk=index.chunks[i]) for r, i in enumerate(order)]
    return HybridResult(hits=hits, translation=tr,
                        ranks={index.chunks[i].chunk_id: {n: int(per[n][i]) for n in per} for i in order})
