"""기본 설정을 한곳에 모아요. ask.py(CLI)와 server.py(API)가 같은 값을 써요.

다른 fabatlas 모듈을 import하지 않아요(순환 import 방지).
"""

from __future__ import annotations

# 검색
CHUNKER = "w500o100"   # 청킹 기본값 (D-018)
RETRIEVER = "hybrid3"  # dense(한국어) + dense(번역) + BM25(번역), RRF (D-019, D-020)
RRF_K = 60             # RRF 상수 (D-014)
TOP_K = 5              # 근거로 쓸 청크 수
DEVICE = "cpu"         # 임베딩 계산 장치

# LLM (번역·답변)
LLM_MODEL = "gpt-4.1-mini-2025-04-14"  # 날짜가 붙은 스냅샷으로 고정해요(재현용)
LLM_TIMEOUT_S = 30.0                   # LLM 호출 한 번의 타임아웃

# API 서버
MAX_CONCURRENCY = 4    # 동시에 처리하는 /ask 요청 수
PREVIEW_CHARS = 200    # 응답에 넣는 청크 미리보기 길이
