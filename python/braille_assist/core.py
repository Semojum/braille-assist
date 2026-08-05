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


# ── 문서 조립 (2026-08-05 추가) ──────────────────────────────────────────────
# 왜 여기 있나: ① 어느 면에 페이지행을 넣나 ② 걸침 순번(a·b·c)을 어떻게 세나
# ③ 표지를 어디까지 빼나 — 셋 다 **지침 규칙**이다. 호출자(BE·FE)가 각자 구현하면
# 점자 규정이 레포 밖으로 흩어진다. 이 레포를 만든 이유가 그걸 막으려는 것이다.
# (2026-08-05 사용자 결정으로 함수 3개 → 4개. 초판은 "typeset 엔진 공용화 안 함"이었다.)


def _wrap(line: str, cols: int) -> list[str]:
    """32칸이 차면 **그대로 자른다**. 어절 단위 줄바꿈 규칙은 없다(조판 가이드 §1 확정).

    잘린 낱말은 점역사가 스페이스·delete로 조정한다.
    """
    if not line:
        return [""]
    return [line[i:i + cols] for i in range(0, len(line), cols)]


def _has_page_row(braille_page: int, on: str) -> bool:
    if on == "odd":
        return braille_page % 2 == 1
    if on == "even":
        return braille_page % 2 == 0
    return True


def build_pages(
    sources: list,
    footer: str = "",
    start_braille_page: int = 1,
    opts: Options = DEFAULT,
) -> list:
    """원본 쪽별 통 문자열 → **완성된 점자 면 배열**. BRF 변환 직전 상태다.

    sources — `[{"orig_page": int, "blocks": [{"order": int, "text": str}]}]`
      · `text`는 ProcessPage가 낸 통 문자열(조판성 줄바꿈은 `\n`으로 들어 있다)
      · `blocks`는 `order`로 정렬해 이어 붙인다
    footer — 이미 점역된 꼬리말 점자(없으면 빈 문자열). 이 레포는 점역하지 않는다.
    start_braille_page — 첫 면의 점자 면 번호. 표지 다음이 1이다(지침 1장2절2-3(1)).

    반환 — 면 배열. 각 면은 줄 배열이고 길이는 `opts.rows`다. 페이지행이 들어가는 면은
    마지막 줄이 페이지행이고 본문이 `rows-1`줄이다.

    ★ 페이지행의 원본 번호 = **그 면 첫 줄이 속한 원본 쪽**.
      지침 1장2절2-2(4) "점자 한 페이지에 원본 페이지 변경선이 2개 이상 나올 때에는
      해당 페이지에서 가장 먼저 나오는 원본 페이지 번호"와 같은 값이다.
      ⚠ 원장 **C-10**으로 자문 예정 — 면이 원본 쪽 중간에서 시작하면서 변경선이 2개 이상일 때
      두 해석이 갈릴 여지가 있다.
    ★ 걸침 순번(cont_idx) = 그 원본 쪽이 **처음 나온 면부터 센 순번**(0부터).
      지침 [예 1-7] 실물이 105·107·109면에 없음·b·d를 붙이는 근거다 — 페이지행이 홀수 면에만
      찍혀 a(106면)·c(108면)가 건너뛰어진 것이지 순번이 건너뛴 게 아니다.
    """
    # 1) 원본 쪽 경계마다 변경선을 넣고 32칸으로 자른다. 줄마다 소속 원본 쪽을 들고 간다.
    flat: list = []                       # (줄, 원본 쪽)
    for i, src in enumerate(sources):
        op = int(src["orig_page"])
        if i > 0:                         # 첫 원본 쪽 앞에는 변경선을 두지 않는다
            flat.append((page_change_line(op, opts), op))
        blocks = sorted(src.get("blocks") or [], key=lambda b: b.get("order", 0))
        text = "".join(b.get("text", "") for b in blocks)
        for logical in text.split("\n"):
            for w in _wrap(logical, opts.cols):
                flat.append((w, op))

    # 2) 면으로 나눈다. 페이지행이 들어가는 면은 본문이 한 줄 줄어든다.
    pages: list = []
    first_seen: dict = {}                 # 원본 쪽 → 그 쪽이 처음 나온 면 번호(0-based)
    pos = 0
    while pos < len(flat):
        while pos < len(flat) and not flat[pos][0].strip():
            pos += 1                      # 면 첫 줄의 빈 줄은 버린다
        if pos >= len(flat):
            break
        idx = len(pages)
        bp = start_braille_page + idx
        head_page = flat[pos][1]
        # 표지 범위 안이면 페이지행을 생략한다(조판 옵션 §5).
        on_cover = head_page <= opts.cover_pages
        has_row = _has_page_row(bp, opts.page_row_on) and not on_cover
        cap = opts.rows - (1 if has_row else 0)
        body = [ln for ln, _ in flat[pos:pos + cap]]
        pos += cap
        first_seen.setdefault(head_page, idx)
        body += [""] * (cap - len(body))
        if has_row:
            body.append(page_row(head_page, idx - first_seen[head_page], bp, footer, opts))
        pages.append(body)
    return pages
