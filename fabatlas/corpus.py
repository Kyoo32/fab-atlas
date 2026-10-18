"""코퍼스 읽기: data/raw/{id}.txt + data/sources.csv 메타데이터 → 문서와 섹션.

섹션은 fetch_corpus.py가 남긴 `== 제목 ==` 줄로 나눠요.
위치(char_start, char_end)는 모두 data/raw/{id}.txt 원문 기준이에요.
2주차 평가셋의 정답 근거를 "doc_id + 원문 위치"로 적기 위해서예요.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# 이 섹션(과 그 하위 섹션)은 본문이 아니라 목록이라 빼요.
EXCLUDED_SECTIONS = {
    "References", "See also", "External links", "Further reading", "Notes",
    "Bibliography", "Related links",
}

# 반도체 공정과 무관해 보이는 섹션. 지우지 않고 개수만 세요(검색 잡음 관찰용).
OFF_TOPIC_SECTIONS = {
    "S005": {"Geology", "Biology", "Structural use", "Food, cosmetic, and pharmaceutical applications",
             "Health effects", "Occupational hazard", "Pathophysiology", "Regulation", "Safety"},
    "S013": {"Application in metal finishing", "Tool steel toughening", "Surface finishing"},
    "S014": {"Biomedical applications", "As a permeation barrier for plastics"},
    "S015": {"Anisotropic glasses", "Decorative applications", "Cutting tools"},
}

HEADING = re.compile(r"^(={2,6}) (.+?) \1$", re.MULTILINE)


@dataclass
class Section:
    doc_id: str
    index: int          # 문서 안에서의 순서. 0은 첫 제목 앞의 도입부
    title: str          # 도입부는 "(도입부)"
    path: str           # 상위 섹션까지 이은 이름. 예: "Natural occurrence > Geology"
    char_start: int     # 섹션 본문 시작 (제목 줄 다음)
    char_end: int
    text: str
    off_topic: bool = False


@dataclass
class Document:
    doc_id: str
    title: str
    process: str
    level: str
    parent_id: str
    url: str
    revision_id: str
    text: str
    sections: list[Section] = field(default_factory=list)


def load_sources(path: Path = DATA / "sources.csv") -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def split_sections(doc_id: str, text: str) -> list[Section]:
    """제목 줄을 경계로 나누고, 제외 섹션과 그 하위 섹션은 버려요."""
    heads = [(m.start(), m.end(), len(m.group(1)), m.group(2).strip()) for m in HEADING.finditer(text)]
    sections: list[Section] = []
    stack: list[tuple[int, str]] = []   # (레벨, 제목) — 상위 경로 계산용
    skip_level: int | None = None       # 제외 섹션의 레벨. 같거나 높은 레벨 제목이 나오면 해제
    off = OFF_TOPIC_SECTIONS.get(doc_id, set())

    bounds = [(0, 0, 1, "(도입부)")] + heads
    for i, (h_start, h_end, level, title) in enumerate(bounds):
        body_start = h_end
        body_end = bounds[i + 1][0] if i + 1 < len(bounds) else len(text)

        if skip_level is not None and level <= skip_level:
            skip_level = None
        if skip_level is None and title in EXCLUDED_SECTIONS:
            skip_level = level
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        if skip_level is not None:
            continue

        body = text[body_start:body_end]
        # 앞뒤 공백을 빼되 원문 위치는 유지해요.
        lead = len(body) - len(body.lstrip())
        stripped = body.strip()
        if not stripped:
            continue
        start = body_start + lead
        path = " > ".join(t for _, t in stack if t != "(도입부)") or "(도입부)"
        sections.append(Section(
            doc_id=doc_id, index=len(sections), title=title, path=path,
            char_start=start, char_end=start + len(stripped), text=stripped,
            off_topic=any(t in off for _, t in stack),
        ))
    return sections


def load_corpus(raw_dir: Path = DATA / "raw") -> list[Document]:
    docs = []
    for row in load_sources():
        text = (raw_dir / f"{row['id']}.txt").read_text(encoding="utf-8")
        doc = Document(
            doc_id=row["id"], title=row["title"], process=row["process"], level=row["level"],
            parent_id=row["parent_id"], url=row["url"], revision_id=row["revision_id"], text=text,
        )
        doc.sections = split_sections(doc.doc_id, text)
        docs.append(doc)
    return docs
