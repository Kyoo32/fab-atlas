"""하이브리드 변형 비교 (LLM 호출 없음). BM25 실험의 v1 번역을 재사용해요.

    uv run python scripts/hybrid_variants.py

조합 (RRF k=60):
  (a) 현재 하이브리드 = dense(한국어) + BM25(번역)
  (b) dense(번역) + BM25(번역)
  (c) dense(한국어) + dense(번역) + BM25(번역)
  (d) 참고: dense(번역) 단독

결과는 data/eval/results/{날짜}_{평가셋}_hybrid_variants.json에 남겨요.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from dense_translate import SOURCES  # noqa: E402  (재사용할 번역 파일 목록)
from eval_tool import load_items  # noqa: E402
from fabatlas.bm25 import BM25Index, tokenize  # noqa: E402
from fabatlas.embedding import MODEL_ID, MODEL_REVISION, build_index, embed_texts, load_model  # noqa: E402
from fabatlas.hybrid import RRF_K, rrf  # noqa: E402
from run_eval import CHUNKERS, K, OUT_DIR, hit  # noqa: E402

COMBOS = {
    "a": "dense(한국어) + BM25(번역)",
    "b": "dense(번역) + BM25(번역)",
    "c": "dense(한국어) + dense(번역) + BM25(번역)",
    "d": "dense(번역) 단독",
}


def main() -> None:
    model = load_model("cpu")
    indexes = {c: build_index(c, "cpu", model=model) for c in CHUNKERS}
    bm25s = {c: BM25Index(idx.chunks) for c, idx in indexes.items()}
    for name, src in SOURCES.items():
        source = json.loads(src.read_text(encoding="utf-8"))
        items = [it for it in load_items(ROOT / "data" / "eval" / f"{name}.jsonl") if it["type"] != "답없음"]
        missing = [it["id"] for it in items if it["id"] not in source["translations"]]
        if missing:
            print(f"{name}: 재사용할 번역이 없는 문항 {missing} — 비교에서 빼요")
        items = [it for it in items if it["id"] in source["translations"]]
        queries = [source["translations"][it["id"]] for it in items]
        ko = embed_texts(model, [it["question"] for it in items])
        en = embed_texts(model, queries)

        recall, changed, per_item = {}, {}, {}
        for c, index in indexes.items():
            hits = {k: [] for k in COMBOS}
            for i, it in enumerate(items):
                d_ko = index.embeddings @ ko[i]
                d_en = index.embeddings @ en[i]
                sp = bm25s[c].bm25.get_scores(tokenize(queries[i]))
                scores = {"a": rrf(d_ko, sp), "b": rrf(d_en, sp), "c": rrf(d_ko, d_en, sp), "d": d_en}
                for k, sc in scores.items():
                    top = np.argsort(-sc, kind="stable")[:K]
                    chunks = [index.chunks[j] for j in top]
                    first = next((r + 1 for r, ch in enumerate(chunks) if hit(ch, it["evidence"])), None)
                    hits[k].append(first is not None)
                    per_item.setdefault(it["id"], {}).setdefault(c, {})[k] = {
                        "hit": first is not None, "first_rank": first, "top5": [ch.chunk_id for ch in chunks]}
            recall[c] = {k: round(sum(v) / len(v), 3) for k, v in hits.items()}
            changed[c] = {}
            for k in ("b", "c", "d"):
                changed[c][k] = {
                    "gained_vs_a": [it["id"] for i, it in enumerate(items) if hits[k][i] and not hits["a"][i]],
                    "lost_vs_a": [it["id"] for i, it in enumerate(items) if hits["a"][i] and not hits[k][i]],
                }
            print(f"{name:9s} {c:9s} " + "  ".join(f"({k}) {recall[c][k]:.3f}" for k in COMBOS))
            for k in ("b", "c", "d"):
                print(f"    ({k}) vs (a): 얻음 {changed[c][k]['gained_vs_a']} 잃음 {changed[c][k]['lost_vs_a']}")

        out = OUT_DIR / f"{date.today().isoformat()}_{name}_hybrid_variants.json"
        out.write_text(json.dumps({
            "date": date.today().isoformat(), "eval_set": f"data/eval/{name}.jsonl", "n_items": len(items), "k": K,
            "config": {"embedding": f"{MODEL_ID}@{MODEL_REVISION}", "translations_from": str(src.relative_to(ROOT)),
                       "translate_prompt": "v1", "rrf_k": RRF_K, "combos": COMBOS},
            "recall_at_5": recall, "changed": changed, "per_item": per_item,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  결과: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
