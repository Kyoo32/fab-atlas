# FabAtlas 프로젝트 규칙

반도체 8대 공정 공개 문서 기반 RAG QA 프로젝트예요. 문서는 한국어 해요체로 써요. 작성자 표기는 Kyuwon Lee예요.

## 공개 안전 (절대 규칙)

이 저장소는 공개예요. 다음은 코드, 문서, 커밋 메시지 어디에도 쓰지 않아요.

- 내 회사명, 회사 서비스, 사내 시스템·프로젝트 내용
- 이직·지원 계획, 지원 회사, 일정
- 개인 연락처

작업일지를 쓰다 이런 내용이 나오면 빼고, 뺐다는 사실을 나에게 알려요.

## 저작권

- 코퍼스는 재배포가 허용된 공개 문서만 쓰고, `data/sources.csv`에 반드시 기록해요.
- 코드는 MIT, `data/` 폴더는 CC BY-SA 4.0이에요.
- 책 내용을 코퍼스나 문서에 옮기지 않아요. (D-002)

## 내 말로 쓰기

- 용어 정의를 새로 쓰면 항상 `<Badge text="초안" variant="caution" />` 배지를 붙여요.
- 내가 고친 문장(배지가 없는 항목 포함)을 덮어쓰지 않아요.

## 디자인 단계

- 2026-11-01까지는 v0이에요. 내가 요청하지 않으면 시각 디자인 작업은 하지 않아요.

## 문서화 예산

- 회당 15~20분 안에 끝나게 짧게 써요.

## 구조 메모

- 쇼케이스: `web/src/pages/` (`/`, `/report/`). 진행 현황은 `web/src/data/progress.json`.
- 작업노트(Starlight): `web/src/content/docs/notes/`
  - 작업일지 `devlog/YYYY-MM-DD-slug.md` (frontmatter: title, date, dateEnd, summary, tags, hours, sidebar.order)
  - 작업일지는 작업 주제 단위예요. 같은 주제가 이어지면 새 파일 대신 "Day N (날짜)" 소절을 추가하고 `dateEnd`(마지막 작업일)와 `hours`(누적)를 갱신해요.
  - 용어사전 `glossary.mdx`, 결정 기록 `decisions.md`
  - 작업일지 frontmatter의 `sidebar.order`는 시작한 시간순 일련번호예요. 새 작업일지는 기존 최댓값 + 1이고, Day를 추가할 때는 바꾸지 않아요.
  - 결정 번호는 결정한 시간순이에요. 같은 날 여러 개면 실제로 결정한 순서예요.
  - 공개 후에는 결정 번호를 다시 매기지 않아요. 바뀐 결정은 새 번호로 추가하고, 옛 결정에 "→ D-00N으로 대체"를 달아요.
  - `notebooks/`는 `scripts/nb2md.py`가 생성해요. 이미지 출력은 `web/public/notebooks/`에 생겨요. 둘 다 직접 고치지 않아요 (gitignore 대상).
- 템플릿: `templates/` (작업일지, 용어 항목, 결정)
- 마크다운 안의 내부 링크는 base를 포함한 절대 경로로 써요: `/fab-atlas/notes/...`
- 범위를 나타내는 물결표는 `\~`로 써요(예: `0.5\~0.7`). 한 줄에 `~`가 두 번 나오면 마크다운이 취소선으로 바꿔요.
- `sources.csv`의 `process` 값은 `web/src/data/processes.ts`의 여덟 개 이름 중 하나예요.

## 명령어

```bash
cd web && npm run dev      # nb2md 후 개발 서버
cd web && npm run build    # nb2md 후 빌드
uv run scripts/nb2md.py    # 노트북 변환만
uv run scripts/fetch_corpus.py  # sources.csv의 위키백과 문서 → data/raw/
uv run python -m fabatlas.ask "질문"  # 검색 + 근거 인용 답변 (키는 .env의 OPENAI_API_KEY)
uv run python scripts/eval_tool.py check  # 평가셋 검사
uv run python scripts/run_eval.py         # 9조합 Recall@5 → data/eval/results/
```

## 커밋

- 커밋과 push는 내 확인을 받은 뒤에 해요.
