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
data/             코퍼스 (sources.csv 출처 대장, raw/ 본문)
scripts/          nb2md.py 노트북 변환, fetch_corpus.py 코퍼스 수집
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

## 코퍼스

코퍼스는 재배포가 허용된 공개 문서만 쓰고, 모든 출처와 판 번호를 `data/sources.csv`에 기록해요.

```bash
uv run scripts/fetch_corpus.py   # sources.csv의 위키백과 문서를 data/raw/로 받기
```

## 라이선스

이 저장소는 영역별로 라이선스가 달라요.

| 영역 | 라이선스 | 이유 |
| --- | --- | --- |
| 코드 (`data/` 밖 전부) | [MIT](LICENSE) | 직접 작성한 코드예요. |
| `data/` 폴더 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.ko) | 위키백과 문서에서 가져와서 원문의 조건(출처 표시, 같은 조건 공유)을 따라요. 자세한 내용은 [data/README.md](data/README.md)에 있어요. |

## 작성자

Kyuwon Lee
