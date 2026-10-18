"""청킹: 문서 → 청크. 방식을 바꿔 끼울 수 있게 CHUNKERS에 이름으로 등록해요.

모든 청크는 원문 위치(char_start, char_end)를 가져요.
평가셋 정답은 chunk_id가 아니라 doc_id + 원문 위치로 적어서, 청킹 방식이 바뀌어도 정답이 유지돼요.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Callable

from fabatlas.corpus import Document

WORD = re.compile(r"\S+")


@dataclass
class Chunk:
    chunk_id: str       # "{doc_id}§{문서 안 순번}" — 인용 표시에 그대로 써요. 예: S005§2
    doc_id: str
    title: str
    process: str
    level: str
    section: str        # 청크가 시작하는 섹션 경로
    char_start: int     # data/raw/{doc_id}.txt 원문 기준
    char_end: int
    url: str
    revision_id: str
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def _make(doc: Document, n: int, section: str, start: int, end: int, text: str) -> Chunk:
    return Chunk(
        chunk_id=f"{doc.doc_id}§{n}", doc_id=doc.doc_id, title=doc.title, process=doc.process,
        level=doc.level, section=section, char_start=start, char_end=end,
        url=doc.url, revision_id=doc.revision_id, text=text,
    )


def chunk_by_section(doc: Document) -> list[Chunk]:
    """섹션 하나 = 청크 하나."""
    return [_make(doc, i + 1, s.path, s.char_start, s.char_end, s.text) for i, s in enumerate(doc.sections)]


def chunk_fixed_words(doc: Document, size: int, overlap: int) -> list[Chunk]:
    """본문 단어를 이어 붙여 size단어씩 자르고, 다음 청크는 overlap단어 겹쳐 시작해요.

    섹션 경계는 무시하고 문서 전체를 이어서 잘라요. 제외 섹션(References 등)과 제목 줄은 단어에 넣지 않아요.
    """
    # (단어 시작, 단어 끝, 섹션 번호) — 위치는 원문 기준
    words = [(m.start() + s.char_start, m.end() + s.char_start, si)
             for si, s in enumerate(doc.sections) for m in WORD.finditer(s.text)]
    chunks: list[Chunk] = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        first, last = words[start], words[end - 1]
        # 여러 섹션에 걸치면 섹션별 조각을 빈 줄로 이어요(제목 줄은 빼요).
        pieces = []
        for si in range(first[2], last[2] + 1):
            sec = doc.sections[si]
            a, b = max(sec.char_start, first[0]), min(sec.char_end, last[1])
            if a < b:
                pieces.append(doc.text[a:b])
        chunks.append(_make(doc, len(chunks) + 1, doc.sections[first[2]].path, first[0], last[1], "\n\n".join(pieces)))
        if end == len(words):
            break
        start = end - overlap
    return chunks


CHUNKERS: dict[str, Callable[[Document], list[Chunk]]] = {
    "section": chunk_by_section,
    "w300o50": lambda d: chunk_fixed_words(d, 300, 50),
    "w500o100": lambda d: chunk_fixed_words(d, 500, 100),
}
DEFAULT_CHUNKER = "w300o50"  # D-007


def chunk_corpus(docs: list[Document], name: str = DEFAULT_CHUNKER) -> list[Chunk]:
    return [c for d in docs for c in CHUNKERS[name](d)]
