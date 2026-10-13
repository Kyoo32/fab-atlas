"""data/sources.csv의 위키백과 문서를 내려받아 data/raw/{id}.txt로 저장해요.

- MediaWiki API로 본문 평문과 판 번호(revision_id)를 받아요.
- revision_id가 비어 있으면 현재 판을 받고 revision_id·collected_at을 채워요.
- revision_id가 있으면 그 판을 다시 받아요(재현용). collected_at은 비어 있을 때만 채워요.
- 위키백과가 아닌 URL은 건너뛰고 경고만 출력해요.

표준 라이브러리만 써요.
    uv run scripts/fetch_corpus.py
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "FabAtlas/0.1 (https://github.com/Kyoo32/fab-atlas)"

# 본문에서 뺄 요소: 각주 번호, 편집 링크, 스타일·스크립트, 표·탐색 상자
SKIP_TAGS = {"style", "script", "table", "figure"}
SKIP_CLASSES = {"reference", "hatnote", "shortdescription", "mw-editsection", "reflist", "references", "navbox", "toc", "mw-references-wrap"}
BLOCK_TAGS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "dd", "dt", "br", "blockquote", "pre"}
VOID_TAGS = {"br", "img", "hr", "meta", "link", "input", "wbr", "source", "col", "area"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0
        self.stack: list[bool] = []  # 태그별로 건너뛰기 시작점인지 기록

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in VOID_TAGS:
            if tag == "br" and not self.skip_depth:
                self.parts.append("\n")
            return
        classes = set((dict(attrs).get("class") or "").split())
        starts_skip = tag in SKIP_TAGS or bool(classes & SKIP_CLASSES)
        self.stack.append(starts_skip)
        if starts_skip:
            self.skip_depth += 1
        elif not self.skip_depth and tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_TAGS or not self.stack:
            return
        if self.stack.pop():
            self.skip_depth -= 1
        elif not self.skip_depth and tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        raw = "".join(self.parts)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw.splitlines()]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"


def _api(host: str, params: dict[str, str]) -> dict:
    query = urlencode({**params, "format": "json", "formatversion": "2"})
    req = Request(f"https://{host}/w/api.php?{query}", headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "error" in data:
        raise RuntimeError(f"{data['error'].get('code')}: {data['error'].get('info')}")
    return data


def _wiki_target(url: str) -> tuple[str, str] | None:
    parsed = urlparse(url)
    if not parsed.netloc.endswith(".wikipedia.org") or not parsed.path.startswith("/wiki/"):
        return None
    return parsed.netloc, unquote(parsed.path[len("/wiki/") :]).replace("_", " ")


def current_revision(host: str, title: str) -> int:
    data = _api(host, {"action": "query", "prop": "revisions", "rvprop": "ids", "titles": title, "redirects": "1"})
    page = data["query"]["pages"][0]
    if page.get("missing"):
        raise RuntimeError(f"문서를 찾을 수 없어요: {title}")
    return int(page["revisions"][0]["revid"])


def revision_text(host: str, revid: int) -> str:
    data = _api(host, {"action": "parse", "oldid": str(revid), "prop": "text", "disablelimitreport": "1"})
    parser = _TextExtractor()
    parser.feed(data["parse"]["text"])
    return parser.text()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sources", type=Path, default=ROOT / "data" / "sources.csv")
    ap.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    args = ap.parse_args()

    with args.sources.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    args.raw_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    failed = 0

    for row in rows:
        rid = row["id"]
        target = _wiki_target(row["url"])
        if target is None:
            print(f"[경고] {rid}: 위키백과 URL이 아니라 건너뛰어요 → {row['url']}", file=sys.stderr)
            continue
        host, title = target
        try:
            pinned = row.get("revision_id", "").strip()
            revid = int(pinned) if pinned else current_revision(host, title)
            text = revision_text(host, revid)
        except Exception as e:  # 한 문서 실패가 전체를 멈추지 않게 해요
            print(f"[실패] {rid}: {e}", file=sys.stderr)
            failed += 1
            continue

        (args.raw_dir / f"{rid}.txt").write_text(text, encoding="utf-8")
        row["revision_id"] = str(revid)
        if not row.get("collected_at", "").strip():
            row["collected_at"] = today
        print(f"{rid}: {title} (판 {revid}{', 고정' if pinned else ''}) → {len(text):,}자")
        time.sleep(0.5)  # API 예의상 간격

    with args.sources.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
