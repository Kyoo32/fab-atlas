"""질의 번역용 표준 용어 매핑 (한국어 표현 → 업계 표준 영어 용어). 번역 프롬프트 v2에서만 써요.

v2는 효과가 흔들림 안이라 채택하지 않았어요(D-017). 기록과 재현을 위해 남겨 둬요.

출처는 평가셋이 아니라 프로젝트에 이미 있는 것만 써요. 평가셋에서 틀린 문항에 맞춰 늘리면
그 평가셋 점수가 실제보다 좋게 나오기 때문이에요.
  1. 8대 공정 이름 (web/src/data/processes.ts)
  2. 코퍼스 문서 23개의 제목 (data/sources.csv)
  3. 용어사전의 도메인 용어 (EDS의 회사별 명칭 등)
"""

from __future__ import annotations

# (한국어 표현들, 표준 영어 용어)
TERM_MAP: list[tuple[tuple[str, ...], str]] = [
    # 8대 공정 이름
    (("웨이퍼 제조",), "wafer fabrication"),
    (("산화", "열산화"), "thermal oxidation"),
    (("포토", "포토 공정", "노광"), "photolithography"),
    (("식각",), "etching"),
    (("증착",), "deposition"),
    (("이온주입", "이온 주입"), "ion implantation"),
    (("금속배선", "배선"), "metal interconnect (metallization)"),
    (("EDS", "웨이퍼 테스트", "프로브 테스트"), "wafer testing (wafer probing, die sort)"),
    (("패키징",), "integrated circuit packaging"),
    # 코퍼스 문서 제목
    (("웨이퍼",), "wafer"),
    (("초크랄스키법", "초크랄스키"), "Czochralski method"),
    (("CMP", "화학적 기계적 연마", "평탄화"), "chemical-mechanical polishing (CMP)"),
    (("산화막", "이산화규소", "실리콘 산화막"), "silicon dioxide"),
    (("감광액", "포토레지스트", "PR"), "photoresist"),
    (("극자외선 노광", "EUV"), "EUV lithography"),
    (("플라즈마 식각", "건식 식각"), "plasma etching"),
    (("반응성 이온 식각", "RIE"), "reactive-ion etching"),
    (("화학 기상 증착", "CVD"), "chemical vapor deposition"),
    (("원자층 증착", "ALD"), "atomic layer deposition"),
    (("물리 기상 증착", "PVD"), "physical vapor deposition"),
    (("구리 배선",), "copper interconnects"),
    (("프로브 카드",), "probe card"),
    (("플립칩",), "flip chip"),
    (("실리콘 관통 전극", "TSV"), "through-silicon via"),
    (("다이싱", "웨이퍼 절단"), "die singulation (wafer dicing)"),
]


def term_map_text() -> str:
    return "\n".join(f"- {' / '.join(ko)} → {en}" for ko, en in TERM_MAP)
