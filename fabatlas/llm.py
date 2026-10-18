"""답변 생성(LLM). OPENAI_API_KEY가 있을 때만 써요. 없으면 검색만 모드예요.

키는 환경 변수로 넣거나, 저장소 루트의 .env(gitignore 대상)에 `OPENAI_API_KEY=...`로 적어요.
모델은 FABATLAS_LLM_MODEL로 바꿀 수 있어요.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from fabatlas.corpus import ROOT
from fabatlas.prompts import build_messages
from fabatlas.search import Hit

DEFAULT_MODEL = "gpt-4.1-mini-2025-04-14"  # 날짜가 붙은 스냅샷으로 고정해요(재현용)
CITATION = re.compile(r"\[(S\d{3}§\d+)\]")
# 지시한 문장 그대로가 아니어도("코퍼스에서 ~에 관한 근거를 찾을 수 없어요") 거절로 봐요.
REFUSAL = re.compile(r"근거를.{0,20}찾을 수 없")


def _load_dotenv() -> None:
    """.env의 KEY=VALUE 줄을 환경 변수로 읽어요(이미 있는 값은 덮지 않아요)."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def available() -> bool:
    _load_dotenv()
    return bool(os.environ.get("OPENAI_API_KEY"))


def model_name() -> str:
    return os.environ.get("FABATLAS_LLM_MODEL", DEFAULT_MODEL)


@dataclass
class Answer:
    text: str
    model: str
    refused: bool             # "코퍼스에서 근거를 찾을 수 없어요"로 거절했는지
    cited: list[str]          # 답변에 나온 인용 표시(순서대로, 중복 제거)
    unknown_citations: list[str]  # 검색된 청크에 없는 인용 — 있으면 지어낸 인용이에요


def answer(question: str, hits: list[Hit]) -> Answer:
    from openai import OpenAI

    _load_dotenv()
    model = model_name()
    resp = OpenAI().chat.completions.create(
        model=model, messages=build_messages(question, hits), temperature=0,
    )
    text = (resp.choices[0].message.content or "").strip()
    cited = list(dict.fromkeys(CITATION.findall(text)))
    known = {h.chunk.chunk_id for h in hits}
    return Answer(
        text=text, model=model, refused=REFUSAL.search(text) is not None,
        cited=cited, unknown_citations=[c for c in cited if c not in known],
    )
