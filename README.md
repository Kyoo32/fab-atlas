# FabAtlas

**8대 공정을 지도로 보고, 묻고, 근거로 답한다**

답을 잘하는 챗봇보다, 어디서 틀리는지 아는 챗봇.
반도체 8대 공정 공개 문서를 근거로 답하는 RAG QA 프로젝트예요.

- 사이트: https://kyoo32.github.io/fab-atlas/
- 작업노트: https://kyoo32.github.io/fab-atlas/notes/

## 계획

- **v1 공정 지식 QA**: 근거 인용 답변, 다축 강건성 검증
- **v2 MES 에이전트**: 가상 MES DB 툴 호출, 가드레일, 회귀 테스트

## 구조

```
web/              Astro + Starlight 사이트 (쇼케이스 + 작업노트)
fabatlas/         Python 패키지
notebooks/        실습 노트북 원본
data/sources.csv  코퍼스 출처 대장
scripts/nb2md.py  노트북 → 작업노트 마크다운 변환
templates/        작업일지·용어·결정 템플릿
```

## 로컬 실행

필요한 것: Node.js 22.12 이상, [uv](https://docs.astral.sh/uv/)

```bash
cd web
npm ci
npm run dev     # http://localhost:4321/fab-atlas/
npm run build
```

## 코퍼스와 라이선스

코퍼스는 재배포가 허용된 공개 문서만 쓰고, 모든 출처를 `data/sources.csv`에 기록해요.

## 작성자

Kyuwon Lee
