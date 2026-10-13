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
  - 작업일지 `devlog/YYYY-MM-DD-slug.md` (frontmatter: title, date, summary, tags, hours)
  - 용어사전 `glossary.mdx`, 결정 기록 `decisions.md`
  - `notebooks/`는 `scripts/nb2md.py`가 생성해요. 직접 고치지 않아요 (gitignore 대상).
- 템플릿: `templates/` (작업일지, 용어 항목, 결정)
- 마크다운 안의 내부 링크는 base를 포함한 절대 경로로 써요: `/fab-atlas/notes/...`
- `sources.csv`의 `process` 값은 `web/src/data/processes.ts`의 여덟 개 이름 중 하나예요.

## 명령어

```bash
cd web && npm run dev      # nb2md 후 개발 서버
cd web && npm run build    # nb2md 후 빌드
uv run scripts/nb2md.py    # 노트북 변환만
```

## 커밋

- 커밋과 push는 내 확인을 받은 뒤에 해요.
