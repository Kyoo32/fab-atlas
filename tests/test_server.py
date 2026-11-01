"""API 서버 테스트. 네트워크 없이 돌아요.

- LLM(번역·답변)은 가짜 함수로 바꿔요.
- bge-m3 대신 가짜 임베딩 모델을 쓰고, 인덱스와 번역 로그는 임시 폴더에 만들어요(실제 data/index, logs를 건드리지 않아요).
- 코퍼스(data/raw)와 청킹·BM25·RRF·답변 해석 코드는 진짜를 써요.
"""

from __future__ import annotations

import asyncio
import hashlib
import re

import numpy as np
import pytest
from fastapi.testclient import TestClient

from fabatlas import config, embedding, llm, server, translate

TRANSLATION = "Why is annealing needed after ion implantation?"


class FakeModel:
    """문장마다 같은 벡터를 돌려주는 가짜 임베딩 모델(1024차원)."""

    def encode(self, texts, **kwargs):
        out = []
        for t in texts:
            seed = int(hashlib.md5(t.encode()).hexdigest()[:8], 16)
            out.append(np.random.default_rng(seed).normal(size=1024))
        return np.array(out, dtype=np.float32)


async def fake_acomplete(messages):
    """번역 요청이면 영어 질의를, 답변 요청이면 근거 중 첫 청크를 인용한 답을 돌려줘요."""
    system = messages[0]["content"]
    if "영어 검색 질의" in system:
        return TRANSLATION
    first_tag = re.search(r"\[(S\d{3}§\d+)\]", messages[1]["content"]).group(1)
    return f"이온 주입 뒤 열처리는 도펀트를 활성화해요. [{first_tag}]"


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(embedding, "INDEX_DIR", tmp_path)
    monkeypatch.setattr(translate, "LOG_PATH", tmp_path / "translate.jsonl")  # 실제 로그를 건드리지 않아요
    monkeypatch.setattr(server, "load_model", lambda device: FakeModel())
    monkeypatch.setattr(llm, "acomplete", fake_acomplete)
    with TestClient(server.app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["chunking"] == config.CHUNKER
    assert body["retriever"] == config.RETRIEVER
    assert body["n_chunks"] > 0


def test_ask_response_shape(client):
    r = client.post("/ask", json={"question": "이온 주입 뒤에 왜 어닐링을 하나요?"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"answer", "refused", "citations", "top5", "translated_query", "latency_ms", "config"}
    assert body["translated_query"] == TRANSLATION
    assert body["refused"] is False
    assert len(body["top5"]) == config.TOP_K
    top = body["top5"][0]
    assert set(top) == {"rank", "chunk_id", "doc_id", "title", "chunk_preview",
                        "dense_ko_rank", "dense_en_rank", "bm25_rank", "rrf_score"}
    assert [t["rank"] for t in body["top5"]] == [1, 2, 3, 4, 5]
    assert all(t["dense_ko_rank"] >= 1 and t["bm25_rank"] >= 1 for t in body["top5"])
    # 가짜 답변은 1위 청크를 인용해요.
    assert body["citations"][0]["tag"] == top["chunk_id"]
    assert set(body["citations"][0]) == {"tag", "doc_id", "title", "url"}
    assert set(body["latency_ms"]) == {"translate", "retrieve", "generate", "total"}
    assert body["config"] == {"chunking": config.CHUNKER, "retriever": config.RETRIEVER, "model": config.LLM_MODEL}


@pytest.mark.parametrize("question", ["", "   "])
def test_ask_empty_question_is_422(client, question):
    assert client.post("/ask", json={"question": question}).status_code == 422


def test_ask_llm_timeout_is_504(client, monkeypatch):
    async def slow(messages):
        await asyncio.sleep(1)

    monkeypatch.setattr(config, "LLM_TIMEOUT_S", 0.05)
    monkeypatch.setattr(llm, "acomplete", slow)
    r = client.post("/ask", json={"question": "이온 주입 뒤에 왜 어닐링을 하나요?"})
    assert r.status_code == 504
    assert r.json()["detail"]["stage"] == "translate"


def test_ask_llm_error_is_502(client, monkeypatch):
    async def broken(messages):
        raise RuntimeError("upstream failed")

    monkeypatch.setattr(llm, "acomplete", broken)
    r = client.post("/ask", json={"question": "이온 주입 뒤에 왜 어닐링을 하나요?"})
    assert r.status_code == 502
    assert r.json()["detail"] == {"stage": "translate", "error": "RuntimeError", "message": "upstream failed"}


def test_citations_grouped_in_one_bracket(client, monkeypatch):
    """[S013§4, S013§6]처럼 괄호 하나에 묶은 인용도 모두 citations로 나와요."""
    async def grouped(messages):
        if "영어 검색 질의" in messages[0]["content"]:
            return TRANSLATION
        tags = re.findall(r"\[(S\d{3}§\d+)\]", messages[1]["content"])[:2]
        return f"도펀트를 활성화해요. [{', '.join(tags)}]"

    monkeypatch.setattr(llm, "acomplete", grouped)
    body = client.post("/ask", json={"question": "이온 주입 뒤에 왜 어닐링을 하나요?"}).json()
    assert [c["tag"] for c in body["citations"]] == [t["chunk_id"] for t in body["top5"][:2]]
