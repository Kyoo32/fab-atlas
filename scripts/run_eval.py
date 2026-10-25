"""9조합 검색 실험: 청킹 3종 × 검색 3종(dense / 번역+BM25 / 하이브리드 RRF), Recall@5.

    uv run python scripts/run_eval.py

- 정답 판정: 상위 5개 청크 중 하나라도 정답 근거(doc_id + 원문 글자 범위)와 겹치면 맞힘이에요.
- 답없음 문항은 근거가 없어 Recall에서 빼요.
- 질문 임베딩과 번역은 질문마다 한 번만 만들어 9조합이 같은 값을 써요.
- 결과는 data/eval/results/{날짜}_qa_v1.json에 문항별로 남겨요(실패 분석용).
"""

from __future__ import annotations

import json
import statistics as st
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from eval_tool import load_items  # noqa: E402
from fabatlas import llm  # noqa: E402
from fabatlas.bm25 import BM25Index, tokenize  # noqa: E402
from fabatlas.embedding import MODEL_ID, MODEL_REVISION, build_index, embed_texts, load_model  # noqa: E402
from fabatlas.hybrid import RRF_K, rrf  # noqa: E402
from fabatlas.translate import translate_query  # noqa: E402

CHUNKERS = ["section", "w300o50", "w500o100"]
RETRIEVERS = ["dense", "bm25", "hybrid"]
K = 5
OUT_DIR = ROOT / "data" / "eval" / "results"


def hit(chunk, evidence: list[dict]) -> bool:
    return any(chunk.doc_id == e["doc_id"] and chunk.char_start < e["char_end"] and e["char_start"] < chunk.char_end
               for e in evidence)


def main() -> None:
    items = [it for it in load_items() if it["type"] != "답없음"]
    print(f"문항 {len(items)}개 (답없음 제외)")

    model = load_model("cpu")
    q_vecs = embed_texts(model, [it["question"] for it in items])
    print("번역 중…")
    translations = [translate_query(it["question"]) for it in items]

    results = {}
    per_item = defaultdict(dict)
    chunk_stats = {}
    for cname in CHUNKERS:
        index = build_index(cname, "cpu", model=model)
        bm25 = BM25Index(index.chunks)
        words = [len(c.text.split()) for c in index.chunks]
        chunk_stats[cname] = {"n_chunks": len(index.chunks), "mean_words": round(st.mean(words), 1),
                              "embed_seconds": index.meta.get("embed_seconds")}
        for rname in RETRIEVERS:
            hits = []
            for i, it in enumerate(items):
                dense = index.embeddings @ q_vecs[i]          # 정규화돼 있어 내적 = 코사인
                sparse = bm25.bm25.get_scores(tokenize(translations[i].query))  # 번역한 영어 질의
                scores = {"dense": dense, "bm25": sparse, "hybrid": rrf(dense, sparse)}[rname]
                top = np.argsort(-scores, kind="stable")[:K]
                chunks = [index.chunks[j] for j in top]
                ok = any(hit(c, it["evidence"]) for c in chunks)
                first = next((r + 1 for r, c in enumerate(chunks) if hit(c, it["evidence"])), None)
                hits.append(ok)
                per_item[it["id"]][f"{cname}/{rname}"] = {"hit": ok, "first_rank": first,
                                                          "top5": [c.chunk_id for c in chunks]}
            results[f"{cname}/{rname}"] = sum(hits) / len(hits)
            print(f"  {cname:9s} {rname:6s} Recall@5 = {results[f'{cname}/{rname}']:.3f} ({sum(hits)}/{len(hits)})")

    # 문항 유형·level·공정별 Recall@5
    def breakdown(key):
        out = {}
        for combo in results:
            groups = defaultdict(list)
            for it in items:
                groups[it[key]].append(per_item[it["id"]][combo]["hit"])
            out[combo] = {g: round(sum(v) / len(v), 3) for g, v in groups.items()}
        return out

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{date.today().isoformat()}_qa_v1.json"
    report = {
        "date": date.today().isoformat(), "eval_set": "data/eval/qa_v1.jsonl", "n_items": len(items), "k": K,
        "config": {"embedding": f"{MODEL_ID}@{MODEL_REVISION}", "translate_model": llm.model_name(), "rrf_k": RRF_K},
        "chunkers": chunk_stats,
        "recall_at_5": {c: round(v, 3) for c, v in results.items()},
        "by_type": breakdown("type"), "by_level": breakdown("level"), "by_process": breakdown("process"),
        "translations": {it["id"]: t.query for it, t in zip(items, translations)},
        "per_item": per_item,
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n결과: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
