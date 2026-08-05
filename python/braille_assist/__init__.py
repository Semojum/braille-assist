"""braille-assist — 점자 조판 공용 함수 3개.

FE(ts)·BE(java)·AI(python) 세 구현이 같은 출력을 내야 한다. 규칙이 바뀌면
세 구현과 `vectors.json`을 한 PR로 갱신한다.

이 모듈은 **한글을 점역하지 않는다.** 꼬리말은 이미 점역된 점자를 받아 배치만 한다.

근거: 「점자 도서 제작 지침」 1장 2절 2(페이지 구성) · 1장 3(꼬리말) · 2장 2절 2-3(원본 페이지 변경선).
"""

from .core import Options, build_pages, page_change_line, page_row, to_brf_ascii

__all__ = ["Options", "page_row", "page_change_line", "to_brf_ascii", "build_pages"]
__version__ = "0.1.0"
