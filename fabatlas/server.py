"""FabAtlas RAG API 서버 (로컬 실행용).

    uv run uvicorn fabatlas.server:app --reload

- 인덱스와 bge-m3 모델은 서버가 뜰 때(lifespan) 한 번만 불러와요.
- LLM 호출(번역·답변)은 await로, 임베딩·검색 같은 CPU 작업은 asyncio.to_thread로 돌려 이벤트 루프를 막지 않아요.
- 동시에 처리하는 /ask 요청은 config.MAX_CONCURRENCY개까지예요. 나머지는 차례를 기다려요.
- 검색과 답변은 CLI와 같은 함수(hybrid_search, make_answer)를 써요.
"""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, StringConstraints
from typing_extensions import Annotated

from fabatlas import config, llm
from fabatlas.bm25 import BM25Index
from fabatlas.embedding import Index, build_index, load_model
from fabatlas.hybrid import hybrid_search
from fabatlas.translate import translate_query_async


# ---------- 요청·응답 형식 ----------

class AskRequest(BaseModel):
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Citation(BaseModel):
    tag: str          # 답변에 나온 인용 표시. 예: "S013§6"
    doc_id: str
    title: str
    url: str


class TopChunk(BaseModel):
    rank: int
    chunk_id: str
    doc_id: str
    title: str
    chunk_preview: str
    dense_ko_rank: int   # 전체 청크 중 dense(한국어 질문) 순위
    dense_en_rank: int   # dense(번역 질의) 순위
    bm25_rank: int       # BM25(번역 질의) 순위
    rrf_score: float


class Latency(BaseModel):
    translate: float
    retrieve: float
    generate: float
    total: float


class Config(BaseModel):
    chunking: str
    retriever: str
    model: str


class AskResponse(BaseModel):
    answer: str
    refused: bool
    citations: list[Citation]
    top5: list[TopChunk]
    translated_query: str
    latency_ms: Latency
    config: Config


# ---------- 서버 상태 ----------

@dataclass
class State:
    model: object
    index: Index
    bm25: BM25Index
    semaphore: asyncio.Semaphore


def load_state() -> State:
    """무거운 준비(모델·인덱스·BM25)를 한 번에 해요. 테스트에서는 이 함수를 가짜로 바꿔요."""
    model = load_model(config.DEVICE)
    index = build_index(config.CHUNKER, config.DEVICE, model=model)
    return State(model=model, index=index, bm25=BM25Index(index.chunks),
                 semaphore=asyncio.Semaphore(config.MAX_CONCURRENCY))


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.fab = await asyncio.to_thread(load_state)
    yield


app = FastAPI(title="FabAtlas", description="반도체 8대 공정 RAG QA", lifespan=lifespan)


async def _llm_step(stage: str, coro):
    """LLM 호출 하나를 타임아웃과 함께 기다리고, 실패하면 단계 이름이 들어간 에러로 바꿔요."""
    try:
        return await asyncio.wait_for(coro, timeout=config.LLM_TIMEOUT_S)
    except asyncio.TimeoutError:
        raise HTTPException(504, {"stage": stage, "error": "timeout",
                                  "message": f"{stage} 단계 LLM 호출이 {config.LLM_TIMEOUT_S:.0f}초 안에 끝나지 않았어요."})
    except HTTPException:
        raise
    except Exception as e:  # LLM API 오류(인증, 요청 한도 등)
        raise HTTPException(502, {"stage": stage, "error": type(e).__name__, "message": str(e)[:300]})


# ---------- 엔드포인트 ----------

@app.get("/health")
async def health(request: Request) -> dict:
    st: State | None = getattr(request.app.state, "fab", None)
    return {
        "status": "ok" if st else "loading",
        "chunking": config.CHUNKER,
        "retriever": config.RETRIEVER,
        "n_chunks": len(st.index.chunks) if st else 0,
        "llm_key": llm.available(),
    }


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest, request: Request) -> AskResponse:
    st: State = request.app.state.fab
    if not llm.available():
        raise HTTPException(503, {"stage": "config", "error": "no_api_key",
                                  "message": "OPENAI_API_KEY가 없어 번역과 답변을 할 수 없어요."})
    async with st.semaphore:
        t0 = time.perf_counter()
        tr = await _llm_step("translate", translate_query_async(req.question))
        t1 = time.perf_counter()
        # 임베딩·행렬곱·BM25는 CPU 작업이라 스레드로 넘겨요. 번역은 위에서 만든 것을 그대로 넘겨 다시 호출하지 않아요.
        result = await asyncio.to_thread(hybrid_search, st.index, st.bm25, st.model, req.question,
                                         config.TOP_K, tr)
        t2 = time.perf_counter()
        ans = await _llm_step("generate", llm.answer_async(req.question, result.hits))
        t3 = time.perf_counter()

    by_id = {h.chunk.chunk_id: h.chunk for h in result.hits}
    citations = [Citation(tag=t, doc_id=by_id[t].doc_id, title=by_id[t].title, url=by_id[t].url)
                 for t in ans.cited if t in by_id]
    top5 = []
    for h in result.hits:
        r = result.ranks[h.chunk.chunk_id]
        top5.append(TopChunk(
            rank=h.rank, chunk_id=h.chunk.chunk_id, doc_id=h.chunk.doc_id, title=h.chunk.title,
            chunk_preview=h.chunk.text[:config.PREVIEW_CHARS], dense_ko_rank=r["dense_ko"],
            dense_en_rank=r["dense_en"], bm25_rank=r["bm25_en"], rrf_score=round(h.score, 6)))
    ms = lambda a, b: round((b - a) * 1000, 1)
    return AskResponse(
        answer=ans.text, refused=ans.refused, citations=citations, top5=top5,
        translated_query=tr.query,
        latency_ms=Latency(translate=ms(t0, t1), retrieve=ms(t1, t2), generate=ms(t2, t3), total=ms(t0, t3)),
        config=Config(chunking=config.CHUNKER, retriever=config.RETRIEVER, model=ans.model),
    )
