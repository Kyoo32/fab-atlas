---
title: 저장소·사이트 구축
date: 2026-10-13
summary: FabAtlas 공개 저장소와 사이트를 만들고, 쇼케이스와 작업노트를 두 영역으로 나눴어요.
tags: [저장소, 사이트]
hours:
sidebar:
  order: 1
---

## 1. 오늘의 목표와 완료 기준

- [x] 공개 저장소와 GitHub Pages 배포
- [x] 쇼케이스(/)와 작업노트(/notes/) 분리

## 2. 새로 만난 용어

## 3. 과정

### 저장소와 사이트 구조

한 저장소, 한 사이트 안에 두 영역을 나눴어요. ([D-004](/fab-atlas/notes/decisions/#d-004--문서-사이트-astro--starlight-두-영역-분리))

| 영역 | 누가 보나 | 무엇을 담나 |
| --- | --- | --- |
| 쇼케이스 (`/`, `/report/`) | 면접관과 방문자 | 프로젝트 소개, 8대 공정 띠, v1·v2 소개, 진행 현황, 검증 리포트 |
| 작업노트 (`/notes/`) | 나 (공부·작업 기록) | 타임라인, 작업일지, 용어사전, 결정 기록, 노트북 |

디자인 로드맵:

| 단계 | 쇼케이스에 더하는 것 |
| --- | --- |
| v0 | 깔끔한 기본형 (지금) |
| v1 | 실험 비교 차트 |
| v2 | 파이프라인 시각화 |
| v3 | 인터랙티브 공정 지도 |

```bash
npm create astro@latest web -- --template starlight
gh repo create Kyoo32/fab-atlas --public
gh api -X POST repos/Kyoo32/fab-atlas/pages -f build_type=workflow
```

## 4. 결정과 이유

- [D-004](/fab-atlas/notes/decisions/#d-004--문서-사이트-astro--starlight-두-영역-분리): Astro + Starlight로 쇼케이스와 작업노트를 한 사이트에서 나눠요.

## 5. 막힌 점과 해결

## 6. 숫자

- 결정 1건(D-004)

## 7. 면접 한 문장

## 8. 다음 할 일

> 한 줄 정리:
