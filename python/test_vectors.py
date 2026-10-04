"""vectors.json 대조 — python 구현.

세 언어가 같은 벡터로 같은 출력을 내야 한다. 실패하면 어느 케이스가 어떻게 다른지 찍는다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from braille_assist import (Options, build_brf, build_pages,  # noqa: E402
                            page_change_line, page_row, pages_to_brf, to_brf_ascii)

VECTORS = Path(__file__).resolve().parent.parent / "vectors.json"
FN = {"page_row": page_row, "page_change_line": page_change_line,
      "to_brf_ascii": to_brf_ascii, "build_pages": build_pages,
      "build_brf": build_brf, "pages_to_brf": pages_to_brf}


def run() -> int:
    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    fails = 0
    total = 0
    for fname, cases in data["cases"].items():
        for c in cases:
            total += 1
            args = dict(c["args"])
            if "opts" in args:
                args["opts"] = Options(**args["opts"])
            got = FN[fname](**args)
            if got != c["expect"]:
                fails += 1
                print(f"FAIL {fname} — {c['name']}")
                print(f"  got    {got!r}")
                print(f"  expect {c['expect']!r}")
    print(f"python: {total - fails}/{total} 통과" + (f" — 실패 {fails}건" if fails else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
