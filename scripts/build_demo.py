"""쇼케이스 데모용 응답 만들기: 추천 질문을 로컬 API 서버로 한 번씩 돌려 web/src/data/demo.json에 저장해요.

    uv run uvicorn fabatlas.server:app --port 8000   # 다른 터미널에서 먼저 띄워요
    uv run python scripts/build_demo.py

사이트(GitHub Pages)는 정적이라 서버를 돌릴 수 없어서, 미리 실행한 결과를 보여 줘요.
자유 질문은 받지 않고 아래 추천 질문만 보여 줘요.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "src" / "data" / "demo.json"
SERVER = "http://localhost:8000"

# (분류, 질문, 이 질문에서 볼 점)
QUESTIONS = [
    ("잘 되는 질문", "이온 주입 뒤에 왜 어닐링을 하나요?",
     "세 검색기가 모두 Ion implantation 문서를 위로 올리는 쉬운 경우예요."),
    ("잘 되는 질문", "EUV 노광에서 펠리클은 왜 필요한가요?",
     "한국어 질문으로 영어 EUV lithography 문서의 Pellicles 부분을 찾는지 봐요."),
    ("잘 되는 질문", "감광액의 양성과 음성은 무엇이 다른가요?",
     "포토레지스트의 두 종류를 근거와 함께 구분하는지 봐요."),
    ("표현 불일치", "EDS 공정에서는 무엇을 검사하나요?",
     "EDS는 국내 업계 용어라 영어 코퍼스에 없어요. 영어 위키백과는 Wafer testing이라고 불러요. 검색이 이 차이를 넘는지, 답변이 과잉 거절하지 않는지 봐요."),
    ("답이 없는 질문", "TSMC 2나노 공정의 양산 수율은 몇 퍼센트인가요?",
     "코퍼스에 답이 없어요. 수치를 지어내지 않고 거절해야 해요."),
    ("근거를 보지 않고 쓴 질문", "반도체 배선이 점점 가늘어지면 전기저항과 신호 전달에는 어떤 변화가 생기나요?",
     "원문을 보지 않고 쓴 평가 질문(B025)이에요. 원문 표현과 덜 겹쳐서 더 어려워요."),
    ("근거를 보지 않고 쓴 질문", "습식 식각과 건식 식각은 어떤 상황에서 각각 선택하나요?",
     "원문을 보지 않고 쓴 평가 질문(B019)이에요."),
]


def main() -> None:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    with httpx.Client(base_url=SERVER, timeout=120) as c:
        health = c.get("/health").json()
        if health.get("status") != "ok":
            sys.exit(f"서버가 준비되지 않았어요: {health}")
        items = []
        for category, question, note in QUESTIONS:
            r = c.post("/ask", json={"question": question})
            r.raise_for_status()
            items.append({"category": category, "question": question, "note": note, "response": r.json()})
            print(f"[{category}] {question} → {r.json()['latency_ms']['total']:.0f}ms")
    OUT.write_text(json.dumps({
        "generated_at": date.today().isoformat(), "commit": commit,
        "config": items[0]["response"]["config"], "items": items,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"저장: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
