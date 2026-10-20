"""BM25 검색. 한국어 질문은 먼저 영어 검색 질의로 번역해요(D-011).

토큰은 소문자 단어(\\w+) 단위예요. 1주차 실험에서 한국어 질의는 모든 청크 점수가 0이었어요.
"""

from __future__ import annotations

import re

import numpy as np
from rank_bm25 import BM25Okapi

from fabatlas.chunking import Chunk
from fabatlas.search import Hit
from fabatlas.translate import Translation, translate_query

TOKEN = re.compile(r"\w+")


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


class BM25Index:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.bm25 = BM25Okapi([tokenize(c.text) for c in chunks])

    def search(self, query: str, k: int = 5) -> list[Hit]:
        scores = self.bm25.get_scores(tokenize(query))
        order = np.argsort(-scores)[:k]
        return [Hit(rank=r + 1, score=float(scores[i]), chunk=self.chunks[i]) for r, i in enumerate(order)]

    def search_korean(self, question: str, k: int = 5) -> tuple[Translation, list[Hit]]:
        """한국어 질문 → 번역 → BM25. 번역 결과도 함께 돌려줘서 단계별로 나눠 볼 수 있어요."""
        tr = translate_query(question)
        return tr, self.search(tr.query, k)
