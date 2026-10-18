"""notebooks/*.ipynb → web/src/content/docs/notes/notebooks/*.md 변환.

이미지 출력은 web/public/notebooks/{노트북}/cell{번호}-{순번}.{확장자}로 저장해요.
표준 라이브러리만 써요. web의 prebuild/predev에서 자동으로 실행돼요.
    uv run scripts/nb2md.py
"""

from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "notebooks"
OUT = ROOT / "web" / "src" / "content" / "docs" / "notes" / "notebooks"
IMG_OUT = ROOT / "web" / "public" / "notebooks"
IMG_URL = "/fab-atlas/notebooks"
# 한 출력에 여러 형식이 있으면 앞의 것을 써요.
IMAGE_TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/svg+xml": "svg"}
REPO = "Kyoo32/fab-atlas"
BRANCH = "main"


def _text(value: str | list[str]) -> str:
    return "".join(value) if isinstance(value, list) else value


def _yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _save_image(data: dict, stem: str, cell_no: int, seq: int) -> str | None:
    for mime, ext in IMAGE_TYPES.items():
        if mime not in data:
            continue
        name = f"cell{cell_no}-{seq}.{ext}"
        dest = IMG_OUT / stem / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if mime == "image/svg+xml":
            dest.write_text(_text(data[mime]), encoding="utf-8")
        else:
            dest.write_bytes(base64.b64decode(_text(data[mime])))
        return f"![{stem} cell {cell_no} 출력 {seq}]({IMG_URL}/{stem}/{name})"
    return None


def _outputs(outputs: list[dict], stem: str, cell_no: int) -> list[str]:
    parts: list[str] = []
    seq = 0
    # stderr(경고, 진행 막대)는 빼고, 이어진 stdout 조각은 하나로 합쳐요.
    merged: list[dict] = []
    for out in outputs:
        if out.get("output_type") == "stream":
            if out.get("name") == "stderr":
                continue
            if merged and merged[-1].get("output_type") == "stream":
                merged[-1] = {**merged[-1], "text": _text(merged[-1]["text"]) + _text(out.get("text", ""))}
                continue
        merged.append(out)
    for out in merged:
        kind = out.get("output_type")
        if kind == "stream":
            text = _text(out.get("text", ""))
        elif kind in ("execute_result", "display_data"):
            data = out.get("data", {})
            if any(m in data for m in IMAGE_TYPES):
                seq += 1
                parts.append(_save_image(data, stem, cell_no, seq))  # type: ignore[arg-type]
                continue
            if "text/markdown" in data:  # 표 같은 마크다운 출력은 그대로 넣어요
                parts.append(_text(data["text/markdown"]).rstrip())
                continue
            if "text/plain" not in data:
                continue
            text = _text(data["text/plain"])
        elif kind == "error":
            text = f"{out.get('ename', 'Error')}: {out.get('evalue', '')}"
        else:
            continue
        if text.strip():
            parts.append("```text\n" + text.rstrip() + "\n```")
    return parts


def convert(nb_path: Path) -> tuple[str, str]:
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    lang = nb.get("metadata", {}).get("kernelspec", {}).get("language", "python")
    title = nb_path.stem
    body: list[str] = []

    for i, cell in enumerate(nb.get("cells", [])):
        cell_no = i + 1
        src = _text(cell.get("source", "")).rstrip()
        if cell.get("cell_type") == "markdown":
            # 첫 마크다운 셀의 H1은 페이지 제목으로 올려요.
            if i == 0 and src.startswith("# "):
                first, _, rest = src.partition("\n")
                title = first[2:].strip()
                src = rest.strip()
            if src:
                body.append(src)
        elif cell.get("cell_type") == "code":
            if src:
                body.append(f"```{lang}\n{src}\n```")
            body.extend(_outputs(cell.get("outputs", []), nb_path.stem, cell_no))

    rel = nb_path.relative_to(ROOT).as_posix()
    github = f"https://github.com/{REPO}/blob/{BRANCH}/{rel}"
    colab = f"https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/{rel}"
    header = [
        "---",
        f"title: {_yaml_str(title)}",
        f"description: {_yaml_str(f'{nb_path.name}에서 자동 변환한 페이지예요.')}",
        "editUrl: false",
        "---",
        "",
        f"> 원본: [GitHub에서 보기]({github}) · [Colab에서 열기]({colab})",
        ">",
        "> `scripts/nb2md.py`가 자동 생성한 페이지예요. 고칠 때는 노트북 원본을 고쳐요.",
    ]
    return title, "\n".join(header) + "\n\n" + "\n\n".join(body) + "\n"


def main() -> None:
    for d in (OUT, IMG_OUT):
        if d.exists():
            shutil.rmtree(d)
    OUT.mkdir(parents=True)

    notebooks = sorted(SRC.glob("*.ipynb"))
    items: list[tuple[str, str]] = []
    for nb_path in notebooks:
        title, md = convert(nb_path)
        (OUT / f"{nb_path.stem}.md").write_text(md, encoding="utf-8")
        items.append((nb_path.stem, title))

    listing = "\n".join(f"- [{t}](/fab-atlas/notes/notebooks/{s}/)" for s, t in items)
    index = "\n".join(
        [
            "---",
            "title: 노트북 목록",
            "editUrl: false",
            "sidebar:",
            "  order: 0",
            "---",
            "",
            "`notebooks/`의 실습 노트북을 변환한 페이지예요.",
            "",
            listing or "아직 노트북이 없어요.",
            "",
        ]
    )
    (OUT / "index.md").write_text(index, encoding="utf-8")
    print(f"nb2md: {len(notebooks)}개 노트북 변환 → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
