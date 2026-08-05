"""vectors.json 생성 — 기준 구현(python)의 출력을 굳힌다.

★ 지침 실물에서 나온 케이스는 `source`에 근거를 적는다. 그 값들은 사람이 확인한 정답이고,
나머지는 기준 구현의 현재 동작을 굳힌 것(회귀 방지용)이다. 규칙이 바뀌면 이 스크립트를
다시 돌리기 전에 **지침 근거 케이스가 그대로 통과하는지 먼저 확인할 것.**
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, "/home/pj14/v2/code/AI")   # ascii_to_unicode (벡터 작성 편의용, 런타임 의존 아님)

from app.utils.braille_ascii import ascii_to_unicode  # noqa: E402
from braille_assist import (Options, build_pages, page_change_line,  # noqa: E402
                            page_row, to_brf_ascii)


def U(brf: str) -> str:
    return ascii_to_unicode(brf, backtick="space")


FOOT_A = U("0,i4`c<w`^1@*")        # [예 1-6] 꼬리말 13칸
FOOT_B = U(",8ir^a0'w`@].nja")     # [예 1-7] 꼬리말 16칸
FOOT_C = U("es\"oe1")              # [예 1-8] 꼬리말 6칸

DEFAULT_OPTS = {"cols": 32, "rows": 26, "show_orig_page": True,
                "show_braille_page": True, "page_row_on": "every", "cover_pages": 0}


def opt(**kw):
    o = dict(DEFAULT_OPTS)
    o.update(kw)
    return o


# (이름, 인자, 근거) — expect는 기준 구현으로 채운다
PAGE_ROW = [
    ("지침 [예 1-6] 25쪽·21면", dict(orig_page=25, cont_idx=0, braille_page=21, footer=FOOT_A),
     "지침 1장2절2 [예 1-6] 실물"),
    ("지침 [예 1-7] 72쪽·105면", dict(orig_page=72, cont_idx=0, braille_page=105, footer=FOOT_B),
     "지침 1장2절2-2(3) [예 1-7] 실물"),
    ("지침 [예 1-7] b72·107면", dict(orig_page=72, cont_idx=2, braille_page=107, footer=FOOT_B),
     "지침 [예 1-7] 실물 — 걸침 알파벳은 번호 앞"),
    ("지침 [예 1-7] d72·109면", dict(orig_page=72, cont_idx=4, braille_page=109, footer=FOOT_B),
     "지침 [예 1-7] 실물 — cont_idx는 점자 면 순번(a·c는 짝수 면이라 안 보임)"),
    ("지침 [예 1-8] 10쪽·5면", dict(orig_page=10, cont_idx=0, braille_page=5, footer=FOOT_C),
     "지침 [예 1-8] 실물 — 가운데 정렬 올림 검증"),
    ("꼬리말 없음 · 7쪽 12면", dict(orig_page=7, cont_idx=0, braille_page=12, footer=""), ""),
    ("꼬리말 없음 · 걸침 a · 8쪽 13면", dict(orig_page=8, cont_idx=1, braille_page=13, footer=""), ""),
    ("한 자리 쪽·면", dict(orig_page=1, cont_idx=0, braille_page=1, footer=""), ""),
    ("세 자리 면 번호", dict(orig_page=250, cont_idx=0, braille_page=321, footer=FOOT_C), ""),
    ("걸침 26번째 = z", dict(orig_page=9, cont_idx=26, braille_page=40, footer=""), ""),
    ("걸침 27번째 = aa", dict(orig_page=9, cont_idx=27, braille_page=41, footer=""), ""),
    ("꼬리말 잘림 — 자리보다 김", dict(orig_page=100, cont_idx=0, braille_page=200,
                              footer=U("abcdefghijklmnopqrstuvwxyz")), "지침 1장3-4) 칸수만큼만"),
    ("원본 번호 끔", dict(orig_page=7, cont_idx=0, braille_page=12, footer=FOOT_C,
                    opts=opt(show_orig_page=False)), "조판 옵션 §5"),
    ("면 번호 끔", dict(orig_page=7, cont_idx=0, braille_page=12, footer=FOOT_C,
                   opts=opt(show_braille_page=False)), "조판 옵션 §5"),
    ("폭 40칸", dict(orig_page=7, cont_idx=0, braille_page=12, footer=FOOT_C,
                  opts=opt(cols=40)), "조판 옵션 §5 — 면 규격 변경"),
]

CHANGE_LINE = [
    ("지침 [예 1-7] 72쪽", dict(orig_page=72), "지침 2장2절2-3 실물"),
    ("지침 [예 1-8] 10쪽", dict(orig_page=10), "지침 [예 1-8] 실물"),
    ("지침 [예 1-8] 11쪽", dict(orig_page=11), "지침 [예 1-8] 실물"),
    ("한 자리", dict(orig_page=8), ""),
    ("세 자리", dict(orig_page=250), ""),
    ("원본 번호 끔", dict(orig_page=8, opts=opt(show_orig_page=False)), ""),
    ("폭 40칸", dict(orig_page=8, opts=opt(cols=40)), ""),
]

# ★ 64셀 전수 — BRF 표가 한 칸이라도 어긋나면 여기서 잡힌다. 표는 이 레포에서 새로 만든 것이
#   아니라 `code/AI/app/utils/braille_ascii.py`의 정본을 옮긴 것이고, gold 코퍼스
#   2,546,903셀 대조에서 불일치 0으로 확인했다(2026-08-05). 그 대조는 코퍼스가 있어야
#   돌아가므로 CI에서는 이 전수 벡터가 대신 지킨다.
_ALL_CELLS = "".join(chr(0x2800 + i) for i in range(64))

BRF = [
    ("64셀 전수", _ALL_CELLS, "BRF 표 잠금 — 정본 표(app/utils/braille_ascii.py)와 동일해야 한다"),
    ("실제 gold 한 줄", "⠠⠍⠓⠪⠁⠀⠇⠚⠽⠐⠆⠑⠛⠚⠧⠀⠼⠁⠃", "코퍼스 표본"),
    ("면 번호 12", "⠼⠁⠃", "조판 가이드 §3"),
    ("페이지행 전체", page_row(7, 0, 12, ""), "공백 셀은 리터럴 스페이스"),
    ("변경선 전체", page_change_line(8), "조판 가이드 §3"),
    ("꼬리말", FOOT_B, ""),
    ("줄바꿈 보존", "⠁\n⠃", ""),
    ("점자 아닌 문자", "⠁X⠃", "못 푸는 셀은 ⟨XXXX⟩로 남긴다"),
]


# ── build_pages ──────────────────────────────────────────────────────────────
# 지침 [예 1-7] 재현이 핵심 벡터다 — 원본 72가 여러 면에 걸칠 때 105·107·109면에
# 접두 없음·b·d가 붙는다. 페이지행이 홀수 면에만 찍혀 a(106)·c(108)가 안 보이는 것이지
# 순번이 건너뛴 게 아니라는 것을 이 벡터가 고정한다.
_LONG = "\n".join("⠁⠃⠉" for _ in range(103)) + "\n"
_TWO_PAGES = [
    {"orig_page": 7, "blocks": [{"order": 1, "text": "⠁" * 70 + "\n"}]},
    {"orig_page": 8, "blocks": [{"order": 1, "text": "\n⠃⠃⠃\n\n" + "⠉" * 40 + "\n"}]},
]

BUILD = [
    ("지침 [예 1-7] 걸침 — 72쪽이 105~109면", 
     dict(sources=[{"orig_page": 72, "blocks": [{"order": 1, "text": _LONG}]}],
          footer=FOOT_B, start_braille_page=105, opts=opt(page_row_on="odd")),
     "지침 1장2절2-2(3)·[예 1-7] — 105 접두없음 · 107 b · 109 d"),
    ("원본 두 쪽 · 변경선 삽입", dict(sources=_TWO_PAGES, footer=FOOT_C,
                             opts=opt(rows=6)), "지침 2장2절2-3 변경선 위치"),
    ("꼬리말 없음", dict(sources=_TWO_PAGES, opts=opt(rows=6)), ""),
    ("블록 order 정렬", dict(sources=[{"orig_page": 3, "blocks": [
        {"order": 2, "text": "⠃⠃\n"}, {"order": 1, "text": "⠁⠁\n"}]}],
        opts=opt(rows=4)), ""),
    ("표지 범위는 페이지행 생략", dict(sources=_TWO_PAGES, footer=FOOT_C,
                            opts=opt(rows=6, cover_pages=7)), "조판 옵션 §5"),
    ("페이지행 끔(짝수만)", dict(sources=_TWO_PAGES, footer=FOOT_C,
                        opts=opt(rows=6, page_row_on="even")), ""),
    ("빈 입력", dict(sources=[], opts=opt(rows=6)), ""),
]


def build() -> dict:
    out = {"version": "0.2.0", "cases": {"page_row": [], "page_change_line": [],
                                         "to_brf_ascii": [], "build_pages": []}}
    for name, kw, src in PAGE_ROW:
        o = kw.pop("opts", None)
        got = page_row(**kw, opts=Options(**o) if o else Options())
        assert len(got) == (o or DEFAULT_OPTS)["cols"], f"{name}: 폭 불일치 {len(got)}"
        out["cases"]["page_row"].append(
            {"name": name, "args": {**kw, "opts": o or DEFAULT_OPTS}, "expect": got,
             **({"source": src} if src else {})})
    for name, kw, src in CHANGE_LINE:
        o = kw.pop("opts", None)
        got = page_change_line(**kw, opts=Options(**o) if o else Options())
        out["cases"]["page_change_line"].append(
            {"name": name, "args": {**kw, "opts": o or DEFAULT_OPTS}, "expect": got,
             **({"source": src} if src else {})})
    for name, kw, src in BUILD:
        o = kw.pop("opts", None)
        got = build_pages(**kw, opts=Options(**o) if o else Options())
        for pg in got:
            assert len(pg) == (o or DEFAULT_OPTS)["rows"], f"{name}: 줄 수 불일치 {len(pg)}"
        out["cases"]["build_pages"].append(
            {"name": name, "args": {**kw, "opts": o or DEFAULT_OPTS}, "expect": got,
             **({"source": src} if src else {})})
    for name, arg, src in BRF:
        out["cases"]["to_brf_ascii"].append(
            {"name": name, "args": {"braille": arg}, "expect": to_brf_ascii(arg),
             **({"source": src} if src else {})})
    return out


if __name__ == "__main__":
    v = build()
    p = ROOT / "vectors.json"
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n = sum(len(c) for c in v["cases"].values())
    print(f"저장: {p} — 케이스 {n}건 "
          f"(지침 근거 {sum(1 for c in v['cases'].values() for x in c if 'source' in x and '지침' in x['source'])}건)")
