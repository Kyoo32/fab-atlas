"""질의 번역: 한국어 질문 → 영어 검색 질의. BM25 경로에서만 써요(D-011).

dense 검색(bge-m3)은 다국어 임베딩이라 번역 없이 한국어 질문을 그대로 써요.
번역할 때마다 원문, 번역, 지연(ms)을 logs/translate.jsonl에 한 줄씩 남겨요.
실패가 번역 단계 문제인지 검색 단계 문제인지 나눠 보려는 거예요.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from fabatlas import llm
from fabatlas.corpus import ROOT
from fabatlas.prompts import TRANSLATE_PROMPT_VERSION, build_translate_messages

LOG_PATH = ROOT / "logs" / "translate.jsonl"


@dataclass
class Translation:
    question: str
    query: str
    latency_ms: float
    model: str


def translate_query(question: str, log: bool = True) -> Translation:
    t0 = time.perf_counter()
    query = llm.complete(build_translate_messages(question))
    latency_ms = (time.perf_counter() - t0) * 1000
    tr = Translation(question=question, query=query, latency_ms=round(latency_ms, 1), model=llm.model_name())
    if log:
        LOG_PATH.parent.mkdir(exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            row = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "prompt_version": TRANSLATE_PROMPT_VERSION, **asdict(tr)}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return tr
