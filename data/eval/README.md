# 평가셋

`qa_v1.jsonl`은 2주차 검색 비교용 평가셋이에요. 한 줄에 한 문항이에요. 만들고 검사할 때는 `scripts/eval_tool.py`를 써요.

## 라이선스

- 질문(`question`)과 정답(`answer`), 그 밖의 필드는 이 저장소의 저작물이라 저장소 코드와 같은 MIT를 따라요.
- 근거 발췌(`evidence[].quote`)는 위키백과 원문 발췌라 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.ko)을 따라요. 원문 출처와 판 번호는 [`../sources.csv`](../sources.csv)에 있어요.

## 필드

| 필드 | 내용 |
| --- | --- |
| `id` | E001~E050 |
| `question` | 한국어 질문 |
| `type` | 일반 / 용어변형 / 답없음 |
| `process` | 8대 공정 이름 (답없음은 비워도 돼요) |
| `level` | 기본 / 상세 (근거 문서의 level) |
| `answer` | 정답 핵심 한두 문장 (한국어) |
| `evidence` | `[{doc_id, char_start, char_end, quote}]`. 위치는 `data/raw/{doc_id}.txt` 기준, `quote`는 원문 앞 80자. 답없음은 빈 배열 |
| `variant_group` | 용어변형 묶음 이름. 같은 묶음은 같은 근거를 공유해요 |
| `drafted_by` | kyoo / claude |
| `note` | 자유 메모. 여러 문장에 걸친 인과 관계 질문은 "인과"를 넣어요 |
