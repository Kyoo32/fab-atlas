"""임베딩과 인덱스. 벡터DB 없이 numpy 배열 하나로 저장해요.

data/index/{청킹이름}/
  chunks.jsonl     청크 메타데이터 (한 줄에 하나, embeddings.npy와 같은 순서)
  embeddings.npy   (청크 수, 1024) float32, L2 정규화됨
  meta.json        모델·판·청크 지문. 같으면 다시 계산하지 않아요(캐시).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from fabatlas.chunking import Chunk, chunk_corpus
from fabatlas.corpus import DATA, load_corpus

MODEL_ID = "BAAI/bge-m3"
MODEL_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"  # Hugging Face 커밋 해시로 고정 (D-008)
# dense 임베딩에 필요한 파일만 받아요. onnx·colbert·sparse 가중치는 받지 않아요.
MODEL_FILES = [
    "config.json", "config_sentence_transformers.json", "modules.json", "sentence_bert_config.json",
    "1_Pooling/config.json", "pytorch_model.bin",
    "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "sentencepiece.bpe.model",
]
MAX_SEQ_LENGTH = 1024  # 300단어 청크는 대략 400~500토큰이라 충분해요.
INDEX_DIR = DATA / "index"


def model_path() -> Path:
    from huggingface_hub import snapshot_download

    return Path(snapshot_download(MODEL_ID, revision=MODEL_REVISION, allow_patterns=MODEL_FILES))


def load_model(device: str = "cpu"):
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(str(model_path()), device=device)
    model.max_seq_length = MAX_SEQ_LENGTH
    return model


def l2_normalize(v: np.ndarray) -> np.ndarray:
    # 길이를 1로 맞추면 두 벡터의 내적이 곧 코사인 유사도가 돼요: cos = a·b / (|a||b|) = a·b
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def embed_texts(model, texts: list[str], batch_size: int = 8) -> np.ndarray:
    raw = model.encode(texts, batch_size=batch_size, normalize_embeddings=False, convert_to_numpy=True,
                       show_progress_bar=False)
    return l2_normalize(raw.astype(np.float32))


def _fingerprint(chunks: list[Chunk]) -> str:
    h = hashlib.sha256()
    for c in chunks:
        h.update(f"{c.chunk_id}\t{c.revision_id}\t{c.char_start}\t{c.char_end}\n".encode())
    return h.hexdigest()


@dataclass
class Index:
    name: str
    chunks: list[Chunk]
    embeddings: np.ndarray
    meta: dict


def build_index(name: str, device: str = "cpu", model=None, force: bool = False) -> Index:
    """청킹 → 임베딩 → 저장. 같은 청킹·같은 모델이면 저장된 것을 불러와요."""
    chunks = chunk_corpus(load_corpus(), name)
    out = INDEX_DIR / name
    meta_path = out / "meta.json"
    fp = _fingerprint(chunks)

    if not force and meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta.get("fingerprint") == fp and meta.get("model_revision") == MODEL_REVISION:
            return Index(name, chunks, np.load(out / "embeddings.npy"), meta)

    model = model or load_model(device)
    t0 = time.perf_counter()
    emb = embed_texts(model, [c.text for c in chunks])
    seconds = time.perf_counter() - t0

    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "embeddings.npy", emb)
    with (out / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
    meta = {
        "chunker": name, "model": MODEL_ID, "model_revision": MODEL_REVISION, "device": device,
        "n_chunks": len(chunks), "dim": int(emb.shape[1]), "embed_seconds": round(seconds, 1),
        "fingerprint": fp,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return Index(name, chunks, emb, meta)
