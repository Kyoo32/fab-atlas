"""평가셋(data/eval/qa_v1.jsonl) 만들기 도우미.

    uv run python scripts/eval_tool.py find "probe card"
    uv run python scripts/eval_tool.py draft --doc S011 --n 3      (또는 --process 포토)
    uv run python scripts/eval_tool.py add                          (대화형)
    uv run python scripts/eval_tool.py add --json '{...}'           (초안 한 줄 추가)
    uv run python scripts/eval_tool.py check

원칙: 근거는 테스트 대상 검색기(bge-m3, BM25)가 아니라 단순 문자열 검색과 직접 읽기로 찾아요.
그래서 이 도구는 fabatlas.search, fabatlas.bm25, 임베딩을 전혀 쓰지 않아요.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from fabatlas.corpus import Document, load_corpus  # noqa: E402  (파싱만 써요. 검색기는 안 써요)

EVAL_PATH = ROOT / "data" / "eval" / "qa_v1.jsonl"
QUOTE_LEN = 80
PROCESSES = ["웨이퍼 제조", "산화", "포토", "식각", "증착·이온주입", "금속배선", "EDS", "패키징"]
TYPES = ["일반", "용어변형", "답없음"]
TARGET = {"일반": 36, "용어변형": 9, "답없음": 5}
EDS_GENERAL = 3          # EDS는 문서가 얇아서 일반 문항을 3개로 고정해요
DOC_WORD_CAP = 3000      # 배분 계산에서 문서 하나는 최대 3,000단어로 세요
MIN_CAUSAL = 8           # 여러 문장에 걸친 인과 관계 질문 최소 개수
VARIANT_GROUPS = {"EDS": 3, "CMP": 3, "감광액": 3}
# 원문 베낌 의심: 질문 속 영어 단어가 근거에 그대로 있는 비율이 크면 표시해요.
COPY_MIN_TOKENS = 3      # 근거와 겹치는 영어 단어가 3개 이상이거나
COPY_MIN_RATIO = 0.25    # 겹치는 영어 글자 수가 질문 글자 수(공백 제외)의 25% 이상
CAUSAL_CUES = re.compile(r"\b(because|due to|therefore|thus|so that|as a result|results? in|leads? to|caus\w+|allow\w*|enabl\w+|prevent\w*)\b", re.I)
LOW_PRIORITY = re.compile(r"History|Etymology|Expense|economic|Other names", re.I)
FIELDS = ["id", "question", "type", "process", "level", "answer", "evidence", "variant_group", "drafted_by", "note"]


# ---------- 공통 ----------

def docs_by_id() -> dict[str, Document]:
    return {d.doc_id: d for d in load_corpus()}


def sentences(doc: Document):
    """(섹션 경로, 시작, 끝, 문장)을 원문 위치와 함께 돌려줘요. 마침표 뒤 공백 기준의 단순 분리예요."""
    for sec in doc.sections:
        for para in re.finditer(r"[^\n]+", sec.text):
            base = sec.char_start + para.start()
            for m in re.finditer(r".+?(?:[.!?](?=\s+[A-Z0-9(\"])|$)", para.group()):
                text = m.group().strip()
                if text:
                    start = base + m.start() + (len(m.group()) - len(m.group().lstrip()))
                    yield sec.path, start, start + len(text), text


def evidence(doc: Document, start: int, end: int) -> dict:
    return {"doc_id": doc.doc_id, "char_start": start, "char_end": end,
            "quote": doc.text[start:min(end, start + QUOTE_LEN)]}


def load_items(path: Path = EVAL_PATH) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def next_id(items: list[dict]) -> str:
    nums = [int(i["id"][1:]) for i in items if re.fullmatch(r"E\d{3}", i.get("id", ""))]
    return f"E{max(nums, default=0) + 1:03d}"


def append(item: dict) -> None:
    EVAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVAL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({k: item.get(k, "" if k != "evidence" else []) for k in FIELDS}, ensure_ascii=False) + "\n")


def general_targets(docs: dict[str, Document]) -> dict[str, int]:
    """일반 36문항을 공정별 문서 단어 수에 비례해 나눠요. EDS는 3개로 고정하고 나머지를 최대 나머지법으로 배분해요.

    문서 하나의 단어 수는 DOC_WORD_CAP까지만 세요. 긴 문서 하나(EUV lithography, 10,550단어)가 배분을 끌고 가지 않게 하려는 거예요.
    """
    words = Counter()
    for d in docs.values():
        words[d.process] += min(sum(len(s.text.split()) for s in d.sections), DOC_WORD_CAP)
    rest = TARGET["일반"] - EDS_GENERAL
    others = [p for p in PROCESSES if p != "EDS"]
    total = sum(words[p] for p in others)
    exact = {p: rest * words[p] / total for p in others}
    alloc = {p: int(exact[p]) for p in others}
    for p in sorted(others, key=lambda p: exact[p] - alloc[p], reverse=True)[: rest - sum(alloc.values())]:
        alloc[p] += 1
    alloc["EDS"] = EDS_GENERAL
    return {p: alloc[p] for p in PROCESSES}


# ---------- find ----------

def cmd_find(args) -> None:
    kw = args.keyword.lower()
    n = 0
    for d in docs_by_id().values():
        for path, s, e, text in sentences(d):
            if kw in text.lower():
                n += 1
                print(f"{d.doc_id} | {path} | {s}–{e}\n  {text}\n")
    print(f"'{args.keyword}': {n}문장")


# ---------- draft ----------

def cmd_draft(args) -> None:
    """근거 후보 구절을 고르고 위치를 채운 초안 틀을 출력해요.

    질문·정답 문장은 테스트 대상 모델(gpt-4.1-mini)에게 맡기지 않아요. Claude가 대화에서 쓰고,
    `add --json`으로 drafted_by=claude 문항을 추가해요. 도구는 근거 위치를 기계적으로 채우는 일만 해요.
    """
    docs = docs_by_id()
    targets = [docs[args.doc]] if args.doc else [d for d in docs.values() if d.process == args.process]
    if not targets:
        sys.exit("문서를 찾지 못했어요.")
    # 무관 섹션과 아주 짧은 섹션은 빼고, 인과 표현이 있는 2~3문장 구절을 우선해요.
    cands = []
    for d in targets:
        sents = list(sentences(d))
        off = {s.path for s in d.sections if s.off_topic}
        for i in range(len(sents)):
            window = sents[i:i + 3]
            if len(window) < 2 or window[0][0] in off or any(w[0] != window[0][0] for w in window):
                continue
            text = " ".join(w[3] for w in window)
            if len(text.split()) < 35:
                continue
            cands.append((bool(CAUSAL_CUES.search(text)), d, window))
    # 인과 표현이 있는 구절을 앞에, 역사·어원 같은 섹션은 뒤로 보내요.
    cands.sort(key=lambda c: (LOW_PRIORITY.search(c[2][0][0]) is not None, not c[0]))
    # 문서를 번갈아 가며 고르고, 같은 섹션에서 두 번 고르지 않아요.
    queues = {d.doc_id: [c for c in cands if c[1].doc_id == d.doc_id] for d in targets}
    picked, used = [], set()
    while len(picked) < args.n and any(queues.values()):
        for q in queues.values():
            while q:
                causal, d, window = q.pop(0)
                if (d.doc_id, window[0][0]) not in used:
                    used.add((d.doc_id, window[0][0]))
                    picked.append((causal, d, window))
                    break
            if len(picked) == args.n:
                break
    for causal, d, window in picked:
        s, e = window[0][1], window[-1][2]
        skeleton = {"question": "", "type": "일반", "process": d.process, "level": d.level, "answer": "",
                    "evidence": [evidence(d, s, e)], "variant_group": "", "drafted_by": "claude",
                    "note": f"draft: {d.title} — {window[0][0]}" + (" / 인과" if causal else "")}
        print(f"--- {d.doc_id} {d.title} | {window[0][0]} | {s}–{e} | 인과 표현 {'있음' if causal else '없음'}")
        print(d.text[s:e])
        print(json.dumps(skeleton, ensure_ascii=False))
        print()


# ---------- add ----------

def cmd_add(args) -> None:
    items = load_items()
    if args.json:
        item = json.loads(args.json)
    else:
        docs = docs_by_id()
        ask = lambda label, default="": input(f"{label}{f' [{default}]' if default else ''}: ").strip() or default
        item = {"question": ask("질문(한국어)"), "type": ask("type (일반/용어변형/답없음)", "일반")}
        item["process"] = ask("process (8대 공정, 답없음은 비워도 돼요)")
        item["level"] = ask("level (기본/상세)")
        item["answer"] = ask("정답 핵심 한두 문장")
        item["evidence"] = []
        while item["type"] != "답없음":
            span = ask("근거 'doc_id char_start char_end' (빈 줄이면 끝)")
            if not span:
                break
            doc_id, s, e = span.split()
            item["evidence"].append(evidence(docs[doc_id], int(s), int(e)))
            print(f"  quote: {item['evidence'][-1]['quote']}")
        item["variant_group"] = ask("variant_group (용어변형만)")
        item["drafted_by"] = ask("drafted_by (kyoo/claude)", "kyoo")
        item["note"] = ask("note")
    item["id"] = item.get("id") or next_id(items)
    append(item)
    print(f"추가했어요: {item['id']} {item['question']}")


# ---------- check ----------

def english_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9\-]*", text)


def cmd_check(args) -> None:
    docs = docs_by_id()
    items = load_items()
    problems: list[str] = []
    print(f"평가셋: {EVAL_PATH.relative_to(ROOT)} — {len(items)}문항\n")

    # 1) 형식과 위치
    ids = Counter(i.get("id") for i in items)
    for dup in [k for k, v in ids.items() if v > 1]:
        problems.append(f"{dup}: id 중복")
    for it in items:
        iid = it.get("id", "?")
        for f in FIELDS:
            if f not in it:
                problems.append(f"{iid}: '{f}' 필드 없음")
        if it.get("type") not in TYPES:
            problems.append(f"{iid}: type '{it.get('type')}'")
        if it.get("type") != "답없음" and it.get("process") not in PROCESSES:
            problems.append(f"{iid}: process '{it.get('process')}'")
        for ev in it.get("evidence", []):
            d = docs.get(ev.get("doc_id"))
            if not d:
                problems.append(f"{iid}: 없는 문서 {ev.get('doc_id')}")
                continue
            s, e = ev["char_start"], ev["char_end"]
            if not (0 <= s < e <= len(d.text)):
                problems.append(f"{iid}: 위치 범위 오류 {ev['doc_id']} {s}–{e}")
            elif d.text[s:min(e, s + QUOTE_LEN)] != ev.get("quote"):
                problems.append(f"{iid}: quote가 원문과 달라요 ({ev['doc_id']} {s}–{e})")
        if it.get("type") == "답없음" and it.get("evidence"):
            problems.append(f"{iid}: 답없음인데 근거가 있어요")
        if it.get("type") != "답없음" and not it.get("evidence"):
            problems.append(f"{iid}: 근거가 없어요")

    # 2) 개수와 목표
    by_type = Counter(i.get("type") for i in items)
    print("type별 (현재/목표)")
    for t in TYPES:
        print(f"  {t}: {by_type[t]}/{TARGET[t]}" + (f"  부족 {TARGET[t] - by_type[t]}" if by_type[t] < TARGET[t] else ""))
    gt = general_targets(docs)
    gen = Counter(i.get("process") for i in items if i.get("type") == "일반")
    print(f"\n일반 문항 공정별 (현재/목표, 목표는 문서 단어 수 비례 · 문서당 {DOC_WORD_CAP:,}단어 상한 · EDS 3 고정)")
    for p in PROCESSES:
        print(f"  {p}: {gen[p]}/{gt[p]}" + (f"  부족 {gt[p] - gen[p]}" if gen[p] < gt[p] else ""))
    lv = Counter(i.get("level") for i in items if i.get("type") != "답없음")
    print(f"\nlevel별: 기본 {lv['기본']}, 상세 {lv['상세']}")
    causal = sum(1 for i in items if i.get("type") == "일반" and "인과" in i.get("note", ""))
    print(f"인과 관계 질문(note에 '인과'): {causal}/{MIN_CAUSAL}" + (f"  부족 {MIN_CAUSAL - causal}" if causal < MIN_CAUSAL else ""))

    # 3) 용어변형 묶음
    print("\n용어변형 묶음 (현재/목표)")
    groups: dict[str, list[dict]] = {}
    for it in items:
        if it.get("type") == "용어변형":
            groups.setdefault(it.get("variant_group", ""), []).append(it)
    for g, need in VARIANT_GROUPS.items():
        print(f"  {g}: {len(groups.get(g, []))}/{need}")
    for g, members in groups.items():
        spans = {tuple(sorted((e["doc_id"], e["char_start"], e["char_end"]) for e in m.get("evidence", []))) for m in members}
        if len(spans) > 1:
            problems.append(f"variant_group '{g}': 문항끼리 근거가 달라요")

    # 4) 질문과 근거의 영어 단어 겹침
    print("\n질문 속 영어 단어·약어가 근거에 그대로 있는지")
    flagged = 0
    for it in items:
        toks = english_tokens(it.get("question", ""))
        if not toks:
            continue
        ev_text = " ".join(docs[e["doc_id"]].text[e["char_start"]:e["char_end"]]
                           for e in it.get("evidence", []) if e.get("doc_id") in docs).lower()
        hit = [t for t in toks if t.lower() in ev_text]
        q_len = len(re.sub(r"\s", "", it["question"])) or 1
        ratio = sum(len(t) for t in hit) / q_len
        mark = "  ⚠ 원문 베낌 의심" if len(hit) >= COPY_MIN_TOKENS or ratio >= COPY_MIN_RATIO else ""
        flagged += bool(mark)
        print(f"  {it['id']}: 질문 영어 {toks} → 근거에 있음 {hit} (글자 비율 {ratio:.0%}){mark}")
    print(f"  원문 베낌 의심: {flagged}문항 (기준: 겹치는 영어 단어 {COPY_MIN_TOKENS}개 이상 또는 글자 비율 {COPY_MIN_RATIO:.0%} 이상)")

    # 5) 초안 남은 수
    claude_left = sum(1 for i in items if i.get("drafted_by") == "claude")
    print(f"\ndrafted_by=claude로 남은 문항: {claude_left} (목표 0)")

    print(f"\n문제: {len(problems)}건")
    for p in problems:
        print(f"  - {p}")


def main() -> None:
    ap = argparse.ArgumentParser(description="FabAtlas 평가셋 도우미")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("find", help="data/raw 단순 문자열 검색")
    p.add_argument("keyword")
    p.set_defaults(func=cmd_find)
    p = sub.add_parser("draft", help="근거 후보 구절과 초안 틀 출력")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--doc")
    g.add_argument("--process", choices=PROCESSES)
    p.add_argument("--n", type=int, default=3)
    p.set_defaults(func=cmd_draft)
    p = sub.add_parser("add", help="한 문항 추가 (대화형 또는 --json)")
    p.add_argument("--json")
    p.set_defaults(func=cmd_add)
    p = sub.add_parser("check", help="평가셋 검사와 요약")
    p.set_defaults(func=cmd_check)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
