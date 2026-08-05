"""공용 함수 3개 — 파이썬 기준 구현(ts·java가 이 동작을 따른다)."""

from __future__ import annotations

from dataclasses import dataclass

SPACE = "⠀"          # 공백 셀 ⠀
NUM_SIGN = "⠼"       # 수표 ⠼
CHANGE_MARK = "⠤"    # 원본 페이지 변경선 채움 ⠤

# 숫자·알파벳은 같은 점형을 쓴다(1=a=⠁ … 0=j=⠚). 수표가 앞에 오면 숫자로 읽는다.
_DIGIT_CELLS = "⠚⠁⠃⠉⠙⠑⠋⠛⠓⠊"  # 0..9 = j a b c d e f g h i
_ALPHA_CELLS = (
    "⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚"  # a..j
    "⠅⠇⠍⠝⠕⠏⠟⠗⠎⠞"  # k..t
    "⠥⠧⠺⠭⠽⠵"                          # u..z
)

# BRF Braille ASCII 64셀 표준표(유니코드 오프셋 0..63 순). 출처는 `code/AI/app/utils/braille_ascii.py`와
# 같은 표 — 여기 새로 만들지 않고 그대로 옮겼다(backtick=⠈ 사고 전례가 있어 임의 변형 금지).
_BRAILLE_ASCII = (
    " A1B'K2L@CIF/MSP"
    '"E3H9O6R^DJG>NTQ'
    ",*5<-U8V.%[$+X!&"
    ";:4\\0Z7(_?W]#Y)="
)
assert len(_BRAILLE_ASCII) == 64


@dataclass(frozen=True)
class Options:
    """조판 옵션. 1차 PoC 고정값이 기본값이다(조판 가이드 §5).

    page_row_on — 페이지행을 넣는 면. 지침 1장2절2-1은 **홀수 면만**이라고 하지만
    1차 고정값은 "매면"이다(원장 C-11로 점역사 자문 예정). 함수는 옵션만 처리하고
    어느 면에 넣을지 판단은 호출자 몫이다.
    """

    cols: int = 32
    rows: int = 26
    show_orig_page: bool = True      # 변경선·페이지행 왼쪽의 원본 쪽 번호
    show_braille_page: bool = True   # 페이지행 오른쪽의 점자 면 번호
    page_row_on: str = "every"       # every | odd | even
    cover_pages: int = 0             # 이 쪽수까지는 표지 — 페이지행 생략

    def __post_init__(self) -> None:
        if self.cols < 8:
            raise ValueError(f"cols는 8 이상이어야 한다: {self.cols}")
        if self.page_row_on not in ("every", "odd", "even"):
            raise ValueError(f"page_row_on은 every|odd|even: {self.page_row_on!r}")


DEFAULT = Options()


def _number(n: int) -> str:
    """정수 → 수표 + 숫자 점형. 예: 12 → ⠼⠁⠃"""
    if n < 0:
        raise ValueError(f"페이지 번호는 0 이상이어야 한다: {n}")
    return NUM_SIGN + "".join(_DIGIT_CELLS[int(d)] for d in str(n))


def _alpha(idx: int) -> str:
    """걸침 순번 → 알파벳 점형. 1→a, 2→b … 26→z, 27→aa(두 글자).

    지침 1장2절2-2(3): 원본 한 쪽이 여러 점자 면에 걸치면 **두 번째 면부터**
    번호 **앞에** 로마자표 없이 알파벳을 순차로 적는다. 그래서 idx는 1부터다.
    실물 [예 1-7]에서 105면(0)·107면(2=b)·109면(4=d) — 면 순번이지 페이지행 순번이 아니다.
    """
    if idx <= 0:
        return ""
    out = ""
    while idx > 0:
        idx, r = divmod(idx - 1, 26)
        out = _ALPHA_CELLS[r] + out
    return out


def page_row(
    orig_page: int,
    cont_idx: int,
    braille_page: int,
    footer: str = "",
    opts: Options = DEFAULT,
) -> str:
    """페이지행 1줄(폭 = opts.cols)을 만든다.

    지침 1장2절2·1장3:
      · 원본 쪽 번호 — 왼쪽 정렬, 첫 칸. cont_idx≥1이면 번호 **앞에** 알파벳(로마자표 없이)
      · 꼬리말 — 가운데 정렬, 항목 사이 **두 칸 이상**
      · 점자 면 번호 — 오른쪽 정렬

    ★ 가운데 정렬은 **올림**이다: start = (cols - len(footer) + 1) // 2.
    지침 실물 4건([예 1-6]·[예 1-7]×3·[예 1-8])이 전부 이 값과 일치한다.
    내림으로 하면 [예 1-6](꼬리말 13칸)이 1칸 어긋난다.
    ⚠ 조판 가이드(2026-08-05) §4의 호출 예 두 개는 이 규칙과 다르다 — 예1은 33칸이라
    폭 자체가 틀렸고 예2는 시작 칸이 2 어긋난다. **지침 실물이 정본이다.**

    footer는 이미 점역된 점자 문자열이다(이 함수는 점역하지 않는다).
    자리에 안 들어가면 지침 1장3-4)에 따라 **뒤에서 잘라** 넣는다.
    """
    n = opts.cols
    left = ""
    if opts.show_orig_page:
        left = _alpha(cont_idx) + _number(orig_page)
    right = _number(braille_page) if opts.show_braille_page else ""

    if len(left) + len(right) > n:
        raise ValueError(f"쪽 번호만으로 {n}칸을 넘는다: 원본 {len(left)} + 점자 {len(right)}")

    cells = [SPACE] * n
    for i, c in enumerate(left):
        cells[i] = c
    for i, c in enumerate(right):
        cells[n - len(right) + i] = c

    if footer:
        # 항목 사이 두 칸 이상(지침 1장3-1). 좌우 여백을 뺀 자리에만 놓는다.
        lo = len(left) + 2 if left else 0
        hi = n - len(right) - 2 if right else n
        room = hi - lo
        f = footer[:room] if len(footer) > room else footer
        if f:
            start = (n - len(f) + 1) // 2          # ★ 올림 — 지침 실물로 확정
            start = min(max(start, lo), hi - len(f))
            for i, c in enumerate(f):
                cells[start + i] = c

    return "".join(cells)


def page_change_line(orig_page: int, opts: Options = DEFAULT) -> str:
    """원본 페이지 변경선 1줄. 지침 2장2절2-3: 첫 칸부터 ⠤로 채우고 오른쪽 끝에 새 원본 쪽 번호.

    실물 [예 1-7]·[예 1-8]: `-----------------------------#gb` — 채움 29칸 + 번호 3칸 = 32.
    """
    n = opts.cols
    num = _number(orig_page) if opts.show_orig_page else ""
    if len(num) > n:
        raise ValueError(f"쪽 번호가 {n}칸을 넘는다: {len(num)}")
    return CHANGE_MARK * (n - len(num)) + num


_CELL_TO_ASCII = {chr(0x2800 + i): ch for i, ch in enumerate(_BRAILLE_ASCII)}
# 표준 ASCII `[ \ ] ^` 는 지침 표기에서 시프트형 `{ | } ~` 로 나온다.
_UNSHIFT = {"[": "{", "\\": "|", "]": "}", "^": "~"}


def to_brf_ascii(braille: str) -> str:
    """유니코드 점자 → BRF-ASCII(소문자). 파일에 쓰기 직전에 한 번 호출한다.

    공백 셀 ⠀는 **리터럴 스페이스**로 낸다(조판 가이드 §3: `⠼⠛⠀⠀…` → `#g  …`).
    ⚠ 코퍼스 `.brl` 관례의 백틱(``` ` ``` = ⠈ = 초성 ㄱ)과 혼동 금지 — 여기서 백틱을 공백으로
    쓰면 초성 ㄱ이 통째로 사라진다(2026-07-13 채점 붕괴 전례).
    줄바꿈은 보존한다. 못 푸는 셀은 `⟨XXXX⟩`로 남긴다(조용히 버리지 않는다).
    """
    out: list[str] = []
    for ch in braille:
        if ch == "\n":
            out.append("\n")
        elif ch == SPACE or ch == " ":
            out.append(" ")
        else:
            a = _CELL_TO_ASCII.get(ch)
            out.append(f"⟨{ord(ch):04X}⟩" if a is None else _UNSHIFT.get(a, a.lower()))
    return "".join(out)
