---
title: 검색 비교 실험
date: 2026-10-20
summary: 2주차 검색 비교 실험이에요. Day 1에는 BM25 축에 쓸 질의 번역 단계를 만들고 질의 10개로 번역 결과와 지연을 쟀어요.
tags: [검색, BM25, 번역, 평가]
hours:
sidebar:
  order: 4
---

## 1. 목표와 완료 기준

- [x] BM25 경로용 질의 번역 단계와 로그 (Day 1)
- [x] 질의 10개 × 3회 번역 지연 측정 (Day 1)
- [x] 측정 표의 용어 오역 여부 판정 (Day 1)
- [x] 평가 기준 통일: 스모크 테스트와 본 평가 (Day 1)

## 2. 새로 만난 용어

## 3. 과정

### Day 1 (10/20) 질의 번역 단계

#### 번역 단계 만들기

- `fabatlas/translate.py`: 한국어 질문을 영어 검색 질의로 번역해요. 번역할 때마다 원문, 번역, 지연(ms)을 `logs/translate.jsonl`에 남겨요(gitignore 대상).
- `fabatlas/prompts.py`: 번역 프롬프트를 분리했어요. 규칙은 "반도체 공정 용어는 업계 표준 영어 용어로 옮겨요"와 "영어 질의 한 줄만 출력해요" 두 줄이에요.
- `fabatlas/bm25.py`: 한국어 질문 → 번역 → BM25 경로예요. dense 검색(bge-m3)은 번역 없이 한국어 질문을 그대로 써요([D-011](/fab-atlas/notes/decisions/#d-011--bm25-축-전용-질의-번역)).
- `fabatlas/llm.py`: 답변과 번역이 같은 호출 함수(`complete`)를 써서 모델 스냅샷(`gpt-4.1-mini-2025-04-14`)과 온도(0)가 같아요.

```python
from fabatlas.translate import translate_query
tr = translate_query("웨이퍼 테스트에서 프로브 카드는 어떤 역할을 하나요?")
tr.query        # 'What is the role of a probe card in wafer testing?'
tr.latency_ms   # 지연(ms)
```

#### 측정: 질의 10개 × 3회

질의는 기존 테스트 5개(Q1~Q5)와 새 5개(Q6~Q10)예요. 새 질의에는 회사별 표현(Q6 "웨이퍼 테스트")과 약어(Q7 "CMP")를 넣었어요.

| 질의 | 번역 결과 | 지연 중앙값(ms) | 핵심 용어 | 용어 오역 여부 |
| --- | --- | ---: | --- | --- |
| Q1 포토 공정에서 감광액(포토레지스트)은 왜 바르나요? | Why is photoresist applied in the photolithography process? | 1,401 | 감광액, 포토레지스트 || 아니요 |
| Q2 이온 주입을 한 뒤에 왜 어닐링(열처리)을 해야 하나요? | Why is annealing (thermal treatment) necessary after ion implantation in semiconductor processing? | 1,671 | 이온 주입, 어닐링 || 아니요 |
| Q3 반응성 이온 식각(RIE)은 왜 습식 식각과 달리 수직으로 깎이나요(이방성)? | Why is reactive ion etching (RIE) anisotropic and etches vertically unlike wet etching? | 1,002 | 반응성 이온 식각, 이방성, 습식 식각 || 아니요 |
| Q4 EDS 공정에서는 무엇을 검사하나요? | What is inspected in the EDS process in semiconductor manufacturing? | 1,085 | EDS || 아니요 |
| Q5 삼성 3나노 공정의 수율은 얼마인가요? | What is the yield of Samsung's 3nm process? | 1,147 | 수율, 3나노 || 아니요 |
| Q6 웨이퍼 테스트에서 프로브 카드는 어떤 역할을 하나요? | What is the role of a probe card in wafer testing? | 922 | 웨이퍼 테스트, 프로브 카드 || 아니요 |
| Q7 CMP는 화학적 작용과 기계적 작용을 어떻게 함께 쓰나요? | How does Chemical Mechanical Planarization (CMP) combine chemical and mechanical actions? | 1,378 | CMP || 아니요 |
| Q8 열산화 공정에서 딜-그로브 모델은 무엇을 설명하나요? | What does the Deal-Grove model explain in the thermal oxidation process? | 1,042 | 열산화, 딜-그로브 모델 || 아니요 |
| Q9 원자층 증착은 화학 기상 증착보다 두께를 왜 더 정밀하게 조절할 수 있나요? | Why can atomic layer deposition control thickness more precisely than chemical vapor deposition? | 992 | 원자층 증착, 화학 기상 증착 || 아니요 |
| Q10 구리 배선에서 배리어 메탈은 왜 필요한가요? | Why is barrier metal necessary in copper interconnects? | 820 | 구리 배선, 배리어 메탈 || 아니요 |

- 질의마다 3번 번역한 결과가 모두 같았어요(10개 모두).
- 판정 기준: 핵심 도메인 용어가 업계 표준 영어 용어로 옮겨졌는가

#### 평가 기준

README의 "평가 기준"과 같아요.

- 스모크 테스트: 동작 확인용. 기대 문서가 검색 top-3 안에 있으면 통과.
- 본 평가: 평가셋 50문항, 정답 근거가 상위 5개 안에 들어오는 비율(Recall@5) 하나로 비교.

## 4. 결정과 이유

- [D-011](/fab-atlas/notes/decisions/#d-011--bm25-축-전용-질의-번역): 번역은 BM25 축에만 쓰고, 번역 모델은 답변 모델과 같은 gpt-4.1-mini 스냅샷으로 고정해요.

## 5. 막힌 점과 해결

## 6. 숫자

- 번역 호출: 30회 (질의 10개 × 3회), 실패 0회
- 번역 지연 전체: 중앙값 1,050ms, 최댓값 2,374ms
- 질의별 지연 최댓값(ms): Q1 2,374 / Q2 1,781 / Q3 1,075 / Q4 1,470 / Q5 1,863 / Q6 923 / Q7 1,452 / Q8 1,059 / Q9 1,230 / Q10 950
- 3회 번역 결과가 서로 다른 질의: 0개
- 용어 오역: 0/10 (Kyuwon Lee 판정). D-011의 다시 볼 조건(3개 이상)에 해당하지 않아요.

## 7. 면접 한 문장

## 8. 다음 할 일

- 평가셋 50문항 만들기: 정답 근거는 doc_id + 원문 위치로 적기, EDS 질문은 세 가지 표현으로
- 9조합 실험

> 한 줄 정리:
