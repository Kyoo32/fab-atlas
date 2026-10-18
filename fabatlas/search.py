"""검색: 질문 벡터와 모든 청크 벡터의 코사인 유사도를 구해 상위 k개를 골라요."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fabatlas.chunking import Chunk
from fabatlas.embedding import Index, embed_texts


@dataclass
class Hit:
    rank: int
    score: float
    chunk: Chunk


def top_k(index: Index, query_vec: np.ndarray, k: int = 5) -> list[Hit]:
    # 둘 다 L2 정규화돼 있어서 행렬곱(내적) 한 번이 곧 모든 청크와의 코사인 유사도예요.
    scores = index.embeddings @ query_vec
    order = np.argsort(-scores)[:k]
    return [Hit(rank=r + 1, score=float(scores[i]), chunk=index.chunks[i]) for r, i in enumerate(order)]


def search(index: Index, model, question: str, k: int = 5) -> list[Hit]:
    q = embed_texts(model, [question])[0]
    return top_k(index, q, k)
