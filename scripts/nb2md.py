"""notebooks/*.ipynb → web/src/content/docs/notes/notebooks/*.md 변환.

표준 라이브러리만 써요. web의 prebuild/predev에서 자동으로 실행돼요.
    uv run scripts/nb2md.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "notebooks"
OUT = ROOT / "web" / "src" / "content" / "docs" / "notes" / "notebooks"
REPO = "Kyoo32/fab-atlas"
BRANCH = "main"


def _text(value: str | list[str]) -> str:
    return "".join(value) if isinstance(value, list) else value


def _yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _outputs(outputs: list[dict]) -> list[str]:
    parts: list[str] = []
    for out in outputs:
        kind = out.get("output_type")
        if kind == "stream":
            text = _text(out.get("text", ""))
        elif kind in ("execute_result", "display_data"):
            data = out.get("data", {})
            if "text/plain" in data:
                text = _text(data["text/plain"])
            elif any(k.startswith("image/") for k in data):
                parts.append("_(이미지 출력은 원본 노트북에서 확인해요)_")
                continue
            else:
                continue
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
            body.extend(_outputs(cell.get("outputs", [])))

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
    if OUT.exists():
        shutil.rmtree(OUT)
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
