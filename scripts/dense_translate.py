"""dense 검색: 한국어 질문 그대로 vs 영어 번역 질의, Recall@5 비교.

    uv run python scripts/dense_translate.py

- 번역은 새로 만들지 않아요. BM25 실험 결과 파일(번역 프롬프트 v1)에 저장된 번역을 그대로 써요.
- 번역이 없는 문항이 있으면 목록만 보여 주고 그 문항은 빼요.
- 정답 판정은 run_eval.py와 같아요: 상위 5개 청크 중 하나라도 정답 근거와 겹치면 맞힘.
- 결과는 data/eval/results/{날짜}_{평가셋}_dense_translate.json에 남겨요.
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

from eval_tool import load_items  # noqa: E402
from fabatlas.embedding import MODEL_ID, MODEL_REVISION, build_index, embed_texts, load_model  # noqa: E402
from run_eval import CHUNKERS, K, OUT_DIR, hit  # noqa: E402

RESULTS = ROOT / "data" / "eval" / "results"
# 평가셋 → 번역을 가져올 BM25 실험 결과 파일 (모두 번역 프롬프트 v1)
SOURCES = {
    "qa_v1": RESULTS / "2026-10-25_qa_v1.json",
    "qa_blind": RESULTS / "2026-10-25_qa_blind_reviewed.json",
}


def top5_hits(index, qvec, evidence):
    scores = index.embeddings @ qvec  # 정규화돼 있어 내적 = 코사인
    top = np.argsort(-scores, kind="stable")[:K]
    chunks = [index.chunks[j] for j in top]
    first = next((r + 1 for r, c in enumerate(chunks) if hit(c, evidence)), None)
    return first is not None, first, [c.chunk_id for c in chunks]


def main() -> None:
    model = load_model("cpu")
    indexes = {c: build_index(c, "cpu", model=model) for c in CHUNKERS}
    for name, src in SOURCES.items():
        source = json.loads(src.read_text(encoding="utf-8"))
        items = [it for it in load_items(ROOT / "data" / "eval" / f"{name}.jsonl") if it["type"] != "답없음"]
        missing = [it["id"] for it in items if it["id"] not in source["translations"]]
        if missing:
            print(f"{name}: 재사용할 번역이 없는 문항 {missing} — 비교에서 빼요")
        items = [it for it in items if it["id"] in source["translations"]]

        ko = embed_texts(model, [it["question"] for it in items])
        en = embed_texts(model, [source["translations"][it["id"]] for it in items])
        per_item, recall, changed = {}, {}, {}
        for c, index in indexes.items():
            r_ko, r_en, gain, loss = 0, 0, [], []
            for i, it in enumerate(items):
                ok_ko, f_ko, t_ko = top5_hits(index, ko[i], it["evidence"])
                ok_en, f_en, t_en = top5_hits(index, en[i], it["evidence"])
                r_ko += ok_ko
                r_en += ok_en
                if ok_en and not ok_ko:
                    gain.append(it["id"])
                if ok_ko and not ok_en:
                    loss.append(it["id"])
                per_item.setdefault(it["id"], {})[c] = {
                    "ko": {"hit": ok_ko, "first_rank": f_ko, "top5": t_ko},
                    "en": {"hit": ok_en, "first_rank": f_en, "top5": t_en},
                }
            recall[c] = {"ko": round(r_ko / len(items), 3), "en": round(r_en / len(items), 3)}
            changed[c] = {"gained_with_translation": gain, "lost_with_translation": loss}
            print(f"{name:9s} {c:9s} 번역 없음 {recall[c]['ko']:.3f} ({r_ko}/{len(items)})  "
                  f"번역 {recall[c]['en']:.3f} ({r_en}/{len(items)})  얻음 {gain} 잃음 {loss}")

        out = OUT_DIR / f"{date.today().isoformat()}_{name}_dense_translate.json"
        out.write_text(json.dumps({
            "date": date.today().isoformat(), "eval_set": f"data/eval/{name}.jsonl", "n_items": len(items), "k": K,
            "config": {"embedding": f"{MODEL_ID}@{MODEL_REVISION}", "translations_from": str(src.relative_to(ROOT)),
                       "translate_prompt": "v1"},
            "recall_at_5": recall, "changed": changed, "per_item": per_item,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  결과: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
