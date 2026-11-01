"""질문 CLI.

    uv run python -m fabatlas.ask "EUV 노광에서 펠리클은 왜 필요한가요?"

기본 검색기는 하이브리드예요(D-019, D-020): dense(한국어) + dense(번역) + BM25(번역)를 RRF로 합쳐요.
번역에 OPENAI_API_KEY가 필요해서, 키가 없으면 dense(한국어)만 써요. 청킹 기본값은 w500o100이에요(D-018).
키가 있으면 검색된 청크만 근거로 한국어 답변도 만들어요.
"""

from __future__ import annotations

import argparse
import textwrap

from fabatlas import config, llm
from fabatlas.bm25 import BM25Index
from fabatlas.chunking import CHUNKERS
from fabatlas.embedding import build_index, load_model
from fabatlas.hybrid import hybrid_search
from fabatlas.prompts import build_messages
from fabatlas.search import search


def main() -> None:
    ap = argparse.ArgumentParser(description="FabAtlas 질문")
    ap.add_argument("question")
    ap.add_argument("-k", type=int, default=config.TOP_K, help="가져올 청크 수")
    ap.add_argument("--chunker", default=config.CHUNKER, choices=sorted(CHUNKERS))
    ap.add_argument("--retriever", default="auto", choices=["auto", "hybrid3", "dense"],
                    help=f"auto: 키가 있으면 {config.RETRIEVER}, 없으면 dense")
    ap.add_argument("--device", default=config.DEVICE)
    ap.add_argument("--no-llm", action="store_true", help="답변 생성 없이 검색 결과만 보여 줘요")
    ap.add_argument("--show-prompt", action="store_true", help="LLM에 보낼 프롬프트를 출력")
    args = ap.parse_args()

    has_key = llm.available()
    retriever = args.retriever if args.retriever != "auto" else (config.RETRIEVER if has_key else "dense")
    if retriever == "hybrid3" and not has_key:
        ap.error("hybrid3는 번역에 OPENAI_API_KEY가 필요해요. 키를 넣거나 --retriever dense를 써요.")

    model = load_model(args.device)
    index = build_index(args.chunker, args.device, model=model)
    ranks = {}
    print(f"질문: {args.question}\n")
    if retriever == "hybrid3":
        result = hybrid_search(index, BM25Index(index.chunks), model, args.question, args.k)
        hits, ranks = result.hits, result.ranks
        print(f"번역 질의: {result.translation.query}  ({result.translation.latency_ms:.0f}ms)\n")
    else:
        hits = search(index, model, args.question, args.k)
        if args.retriever == "auto":
            print("[dense만] OPENAI_API_KEY가 없어 번역 없이 한국어 질문으로만 찾아요.\n")
    by_id = {h.chunk.chunk_id: h.chunk for h in hits}

    if has_key and not args.no_llm:
        ans = llm.answer(args.question, hits)
        print(f"답변 ({ans.model}):\n{ans.text}\n")
        if ans.cited:
            print("인용:")
            for cid in ans.cited:
                c = by_id.get(cid)
                print(f"- [{cid}] {c.title} — {c.section}: {c.url}" if c else f"- [{cid}] ⚠ 검색된 청크에 없는 인용이에요")
        elif not ans.refused:
            print("⚠ 인용 표시가 없는 답변이에요.")
        print()

    label = "RRF 점수" if retriever == "hybrid3" else "코사인"
    print(f"검색된 청크 (검색기={retriever}, 청킹={args.chunker}, top-{args.k}, 점수={label}):")
    for h in hits:
        c = h.chunk
        detail = ""
        if c.chunk_id in ranks:
            r = ranks[c.chunk_id]
            detail = f"  [순위 dense한 {r['dense_ko']} · dense번역 {r['dense_en']} · BM25 {r['bm25_en']}]"
        print(f"{h.rank}. {h.score:.4f}  [{c.chunk_id}] {c.title} — {c.section}  (원문 {c.char_start}–{c.char_end}){detail}")
        print(textwrap.indent(textwrap.shorten(c.text, 220, placeholder=" …"), "   "))

    if args.show_prompt:
        print("\n--- 프롬프트 ---")
        for m in build_messages(args.question, hits):
            print(f"[{m['role']}]\n{m['content']}\n")


if __name__ == "__main__":
    main()
