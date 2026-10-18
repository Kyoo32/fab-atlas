"""질문 CLI.

    uv run python -m fabatlas.ask "EUV 노광에서 펠리클은 왜 필요한가요?"

OPENAI_API_KEY가 있으면 검색된 청크만 근거로 한국어 답변을 만들어요. 없으면 검색만 모드예요.
"""

from __future__ import annotations

import argparse
import textwrap

from fabatlas import llm
from fabatlas.chunking import CHUNKERS, DEFAULT_CHUNKER
from fabatlas.embedding import build_index, load_model
from fabatlas.prompts import build_messages
from fabatlas.search import search


def main() -> None:
    ap = argparse.ArgumentParser(description="FabAtlas 질문")
    ap.add_argument("question")
    ap.add_argument("-k", type=int, default=5, help="가져올 청크 수")
    ap.add_argument("--chunker", default=DEFAULT_CHUNKER, choices=sorted(CHUNKERS))
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--no-llm", action="store_true", help="키가 있어도 검색만 해요")
    ap.add_argument("--show-prompt", action="store_true", help="LLM에 보낼 프롬프트를 출력")
    args = ap.parse_args()

    model = load_model(args.device)
    index = build_index(args.chunker, args.device, model=model)
    hits = search(index, model, args.question, args.k)
    by_id = {h.chunk.chunk_id: h.chunk for h in hits}

    print(f"질문: {args.question}\n")
    if llm.available() and not args.no_llm:
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
    else:
        print("[검색만 모드] OPENAI_API_KEY가 없거나 --no-llm이에요.\n")

    print(f"검색된 청크 (청킹={args.chunker}, top-{args.k}):")
    for h in hits:
        c = h.chunk
        print(f"{h.rank}. {h.score:.3f}  [{c.chunk_id}] {c.title} — {c.section}  (원문 {c.char_start}–{c.char_end})")
        print(textwrap.indent(textwrap.shorten(c.text, 220, placeholder=" …"), "   "))

    if args.show_prompt:
        print("\n--- 프롬프트 ---")
        for m in build_messages(args.question, hits):
            print(f"[{m['role']}]\n{m['content']}\n")


if __name__ == "__main__":
    main()
