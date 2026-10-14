# data

FabAtlas 코퍼스 폴더예요.

## 출처와 라이선스

- 출처: 영어 위키백과 (D-005)
- 라이선스: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.ko)
- 문서별 제목, URL, 판 번호(`revision_id`), 수집일은 [`sources.csv`](sources.csv)에 있어요. 각 문서의 저자 목록은 원문 URL의 역사 탭에서 볼 수 있어요.

이 폴더의 내용은 CC BY-SA 4.0으로 배포해요. 저장소의 코드(MIT)와 라이선스가 달라요.

## 파일

| 경로 | 내용 |
| --- | --- |
| `sources.csv` | 코퍼스 출처 대장 |
| `raw/{id}.txt` | 위키백과 본문 평문. `scripts/fetch_corpus.py`가 만들어요. |

## 다시 받기

```bash
uv run scripts/fetch_corpus.py
```

`revision_id`가 채워진 문서는 같은 판을 다시 받아요. 비어 있으면 현재 판을 받고 번호를 채워요.
위키백과 본문을 평문으로 바꾸면서 표, 각주 번호, 그림 설명은 뺐어요.
