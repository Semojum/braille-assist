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
from braille_assist import Options, page_change_line, page_row, to_brf_ascii  # noqa: E402


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

BRF = [
    ("면 번호 12", "⠼⠁⠃", "조판 가이드 §3"),
    ("페이지행 전체", page_row(7, 0, 12, ""), "공백 셀은 리터럴 스페이스"),
    ("변경선 전체", page_change_line(8), "조판 가이드 §3"),
    ("꼬리말", FOOT_B, ""),
    ("줄바꿈 보존", "⠁\n⠃", ""),
    ("점자 아닌 문자", "⠁X⠃", "못 푸는 셀은 ⟨XXXX⟩로 남긴다"),
]


def build() -> dict:
    out = {"version": "0.1.0", "cases": {"page_row": [], "page_change_line": [], "to_brf_ascii": []}}
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
