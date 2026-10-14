---
title: 코퍼스 채우기
date: 2026-10-14
summary: 영어 위키백과 문서 23개로 8대 공정 코퍼스를 채우고 원문 스냅샷을 고정했어요.
tags: [코퍼스, 위키백과, EDS]
hours:
---

## 1. 오늘의 목표와 완료 기준

- [x] 8개 공정이 모두 채워진 sources.csv
- [x] 문서마다 data/raw/ 스냅샷과 revision_id

## 2. 새로 만난 용어

- [EDS](/fab-atlas/notes/glossary/#eds)
- [8대 공정](/fab-atlas/notes/glossary/#8대-공정)

## 3. 과정

### 3-1. 문서 확인 기준

위키백과 본문 텍스트는 모두 CC BY-SA 4.0이라 문서마다 라이선스를 다시 확인하지 않아요. 이미지는 파일마다 라이선스가 다르지만 우리는 텍스트만 받아요.

대신 문서마다 아래 네 가지를 봐요. 문서당 1~2분, 목차와 첫 문단 위주로요.

| 체크 | 보는 곳 | 빼는 경우 |
| --- | --- | --- |
| 맞는 문서인가 | 제목, 첫 문단 | 동음이의 문서, 다른 분야 |
| 분량이 있나 | 목차 | 토막 문서 |
| 공정 설명이 있나 | 목차 항목 | 역사·회사·시장 위주이고 원리 설명이 없음 |
| 질문 2개가 떠오르나 | 본문 몇 줄 | 질문이 떠오르지 않음 |

기록 방식: ✅/❌ + 뺀 이유 한 단어 + 떠오른 질문 메모

### 3-2. sources.csv 입력과 확인

[어제 3-4](/fab-atlas/notes/devlog/2026-10-13-corpus/#3-4-코퍼스-구조-기본-문서--상세-문서)의 후보 24개를 MediaWiki API로 한 번에 확인했어요.

```bash
curl -s -G "https://en.wikipedia.org/w/api.php" \
  --data-urlencode "action=query" --data-urlencode "format=json" \
  --data-urlencode "formatversion=2" --data-urlencode "redirects=1" \
  --data-urlencode "prop=pageprops|info" --data-urlencode "ppprop=disambiguation" \
  --data-urlencode "titles=Wafer (electronics)|Czochralski method|…|Wafer dicing"
```

| 확인 | 결과 |
| --- | --- |
| 없는 문서 | Damascene process (영어 위키백과에 해당 제목의 문서가 없어요. 넣지 않았어요) |
| 리다이렉트 | Extreme ultraviolet lithography → EUV lithography, Wafer dicing → Die singulation. 최종 제목으로 기록하고 notes에 `redirect from …`을 적었어요 |
| 동음이의 문서 | 없음 |

그래서 23개를 S001~S023으로 넣었어요. 공정 순서대로, 공정마다 기본 문서를 먼저 넣었어요.

### 3-3. 스냅샷

```bash
uv run scripts/fetch_corpus.py
wc -w data/raw/*.txt
```

23개 모두 받았고 실패는 없었어요. 단어 수는 `wc -w` 기준이고, 본문 끝의 See also·References 목록도 포함돼요.

| id | 공정 | 단계 | 문서 | 단어 수 |
| --- | --- | --- | --- | ---: |
| S001 | 웨이퍼 제조 | 기본 | Wafer (electronics) | 3,045 |
| S002 | 웨이퍼 제조 | 상세 | Czochralski method | 1,585 |
| S003 | 웨이퍼 제조 | 상세 | Chemical-mechanical polishing | 1,276 |
| S004 | 산화 | 기본 | Thermal oxidation | 1,136 |
| S005 | 산화 | 상세 | Silicon dioxide | 3,893 |
| S006 | 포토 | 기본 | Photolithography | 4,747 |
| S007 | 포토 | 상세 | Photoresist | 2,313 |
| S008 | 포토 | 상세 | EUV lithography | 10,597 |
| S009 | 식각 | 기본 | Etching (microfabrication) | 1,292 |
| S010 | 식각 | 상세 | Plasma etching | 1,264 |
| S011 | 식각 | 상세 | Reactive-ion etching | 622 |
| S012 | 증착·이온주입 | 기본 | Chemical vapor deposition | 3,739 |
| S013 | 증착·이온주입 | 기본 | Ion implantation | 2,836 |
| S014 | 증착·이온주입 | 상세 | Atomic layer deposition | 4,664 |
| S015 | 증착·이온주입 | 상세 | Physical vapor deposition | 1,465 |
| S016 | 금속배선 | 기본 | Interconnect (integrated circuits) | 1,336 |
| S017 | 금속배선 | 상세 | Copper interconnects | 1,392 |
| S018 | EDS | 기본 | Wafer testing | 658 |
| S019 | EDS | 상세 | Probe card | 1,056 |
| S020 | 패키징 | 기본 | Integrated circuit packaging | 2,706 |
| S021 | 패키징 | 상세 | Flip chip | 1,313 |
| S022 | 패키징 | 상세 | Through-silicon via | 1,098 |
| S023 | 패키징 | 상세 | Die singulation | 928 |

"short: 검토 필요" 표시(1,000단어 미만): S011 Reactive-ion etching, S018 Wafer testing, S023 Die singulation

### 3-4. 관찰: EDS는 어디에 있나

`data/raw/`에서 "EDS"를 세어 봤어요.

- S018 Wafer testing: 0번
- 코퍼스 전체 23개 문서: 0번. "EDS"가 나오는 문서가 없어요.

EDS(Electrical Die Sorting)는 회사마다 부르는 이름이 달라요. 삼성은 EDS, SK하이닉스 뉴스룸은 웨이퍼 테스트, 글로벌 테스트 기업은 wafer sort·wafer probe, 영어 위키백과는 Wafer testing이에요.

"EDS"는 에너지 분산형 X선 분광법(EDS/EDX)의 약어이기도 해요. 이것도 반도체 불량 분석에 쓰여서 키워드 검색이 엉뚱한 문서를 가져올 수 있어요.

그래서 2주차 평가셋에 EDS 질문을 세 가지 표현으로 넣어요: "EDS에서…", "웨이퍼 테스트에서…", "프로브 테스트에서…"

이후 강건성 축 후보로 "질문 표현 축"을 메모해요. 9조합 범위는 늘리지 않아요.

## 4. 결정과 이유

### 미결정 · 1,000단어 미만 문서를 넣을지

- 해당 문서: S011 Reactive-ion etching(622), S018 Wafer testing(658), S023 Die singulation(928)
- 결론:
- 이유:

## 5. 막힌 점과 해결

## 6. 숫자

- 총 문서 수: 23개 (기본 9, 상세 14)
- 공정별 문서 수(기본/상세): 웨이퍼 제조 1/2, 산화 1/1, 포토 1/2, 식각 1/2, 증착·이온주입 2/2, 금속배선 1/1, EDS 1/1, 패키징 1/3
- 총 단어 수: 54,961
- 가장 짧은 문서: S011 Reactive-ion etching, 622단어
- 가장 긴 문서: S008 EUV lithography, 10,597단어
- "EDS" 출현 문서 수: 0

## 7. 면접 한 문장

## 8. 다음 할 일

- **10/15 (2시간)**: 기본 RAG 뼈대(파싱 → 청킹 → 임베딩 → 검색). 오늘 단어 수 분포를 보고 청킹 크기 후보를 정해요.
- **평가셋 메모**: 오늘 떠오른 질문을 아래 "평가셋 후보 질문"에 적어요.

### 평가셋 후보 질문

> 한 줄 정리:
