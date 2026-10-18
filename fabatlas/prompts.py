"""답변 생성 프롬프트. 검색된 청크만 근거로 쓰게 하고, 근거가 없으면 거절하게 해요.

아직 LLM에 연결하지 않았어요(검색만 모드). `ask --show-prompt`로 보낼 내용을 미리 볼 수 있어요.
"""

from __future__ import annotations

from fabatlas.search import Hit

NO_ANSWER = "코퍼스에서 근거를 찾을 수 없어요."

SYSTEM = f"""당신은 반도체 공정 질문에 답하는 도우미예요.
규칙:
1. 아래 [근거]에 있는 내용만 사용해요. 근거에 없는 사실은 쓰지 않아요.
2. 한국어 해요체로 답해요. 근거는 영어지만 답은 한국어로 써요.
3. 모든 문장 끝에 그 문장의 근거 청크 표시를 달아요. 예: "...이에요. [S005§2]"
4. 근거가 질문에 답하기에 부족하면 다른 말 없이 "{NO_ANSWER}"라고만 답해요."""

USER = """[질문]
{question}

[근거]
{context}"""


def format_context(hits: list[Hit]) -> str:
    return "\n\n".join(
        f"[{h.chunk.chunk_id}] {h.chunk.title} — {h.chunk.section}\n{h.chunk.text}" for h in hits
    )


def build_messages(question: str, hits: list[Hit]) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER.format(question=question, context=format_context(hits))},
    ]
