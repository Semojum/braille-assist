# braille-assist

점자 조판 공용 라이브러리. **python · ts · java 세 구현이 같은 출력**을 내고,
`vectors.json` 하나로 CI가 그 동일성을 검증한다.

| 구현 | 쓰는 곳 | 하는 일 |
|---|---|---|
| `python/` | AI 점역 파트 | 기준 구현 |
| `ts/` | FE 에디터 | 화면에 점자 면을 그린다 |
| `java/` | BE | `.brf` · `.txt` 다운로드 파일을 만든다 |

FE·BE는 포팅 없이 가져다 쓰기만 한다. 규칙이 바뀌면 **세 구현 + 벡터를 한 PR로** 갱신한다.

> **이 라이브러리는 한글을 점역하지 않는다.** 꼬리말도 이미 점역된 점자 문자열을 받아
> 자리에만 놓는다. 묵자에서 점자로 바꾸는 일은 AI 서버가 한다.

---

## 5분 안에 쓰기

### 설치

```bash
# python — 경로를 추가하거나 python/ 를 그대로 복사한다(의존성 없음)
export PYTHONPATH=$PYTHONPATH:/path/to/braille-assist/python

# ts
npm install @semojum/braille-assist          # 또는 ts/ 를 워크스페이스로 참조

# java — pom.xml 에 추가 (com.semojum:braille-assist:0.1.0)
```

### BE — 다운로드 파일 만들기

BE가 받는 편집 최종본(Job JSON)을 그대로 넘기면 파일 내용이 나온다. **조판 규칙을 다시 짤 일이 없다.**

```python
from braille_assist import build_brf, build_pages_from_job

brf = build_brf(job)                                    # .brf 파일 내용 (BRF-ASCII)
pages = build_pages_from_job(job)                       # 점자 면 배열 (유니코드 점자)
txt = "\n".join(line for p in pages for line in p)      # .txt 파일 내용
```

```java
String brf = BrailleAssist.buildBrf(job);
List<List<String>> pages = BrailleAssist.buildPagesFromJob(job);
```

`.brf`와 `.txt`는 **같은 조판 결과의 다른 표기**다. `.brf`는 점역 프로그램이 읽는 ASCII,
`.txt`는 사람이 화면에서 읽는 유니코드 점자다. 면 사이에 별도 구분자를 넣지 않는다 —
면 경계는 줄 수(`rows`)로 정해진다. 점자 프린터가 면마다 폼피드를 요구하면
`"\f".join("\n".join(p) for p in pages)`처럼 호출부에서 넣는다.

### FE — 화면에 그리기

```ts
import { buildPagesFromJob, pageRow } from '@semojum/braille-assist';

const pages = buildPagesFromJob(job);   // string[][] — 면마다 rows 줄
// pages[0][25] 가 1면의 페이지행이다. 그대로 그리면 된다.
```

FE와 BE가 **같은 Job으로 같은 결과**를 얻는다. 화면과 다운로드가 갈라지지 않는 이유가 이것이다.

---

## Job JSON

BE가 편집 최종본을 모아 넘기는 형식이다. `build_brf` · `build_pages_from_job` 둘 다 이걸 받는다.

```jsonc
{
  "job_id": "j1",
  "options": {
    "include_page_number": true,   // 페이지행을 넣을지 (끄면 page_row_on 을 무시하고 안 넣는다)
    "page_row_on": "odd",          // 넣는다면 어느 면에 — odd | every | even | none
    "cols": 32,                    // 한 줄 칸 수
    "rows": 26,                    // 한 면 줄 수
    "show_orig_page": true,        // 페이지행 왼쪽의 원본 페이지 번호
    "show_braille_page": true,     // 페이지행 오른쪽의 점자 면 번호
    "cover_pages": 0,              // 앞에서 이만큼의 원본 페이지가 표지
    "orig_page_start": null,       // 표지 다음 첫 본문 페이지에 붙일 번호 (null = 준 값 그대로)
    "show_change_line": true,      // 원본 페이지 변경선
    "footer_align": "center"       // 꼬리말 정렬 — center | right
  },
  "footer_braille": "⠎⠣⠞⠕⠛⠕⠈⠮",       // 문서 전체 기본 꼬리말 (이미 점역된 점자)
  "footers_braille": { "3": "⠈⠮" },   // 면별 꼬리말 — 이 면만 다르게 (선택)
  "start_braille_page": 1,            // 첫 면의 점자 면 번호
  "pages": [
    { "orig_page_no": 7,
      "elements": [
        { "id": "e1", "type": "title", "heading_level": 1, "text": "⠀⠀⠠⠕⠂⠠⠪⠃\n" },
        { "id": "e2", "type": "text",  "heading_level": 0, "text": "⠀⠀⠕⠰⠗⠁⠵⠀⠙⠣⠕\n" }
      ] }
  ]
}
```

`options`의 모든 항목은 **선택**이다. 빠지면 위에 적힌 기본값이 쓰인다.

**`elements` 배열 순서가 읽기 순서다.** `order` 필드는 없다(BE가 정렬해 담는다).

**`type`과 `heading_level`은 조판에 쓰지 않는다.** 들여쓰기·가운데 정렬·구조적 빈 줄은
AI가 이미 `text` 안에 넣어 보낸다(점자 공백 셀과 `\n`). 여기서 또 넣으면 두 번 들어간다.
두 필드는 오류를 지목하거나 나중에 확장할 때 쓰려고 받아 두기만 한다.

---

## 조판 설정 화면과 옵션의 대응

FE 설정 화면의 항목이 어느 옵션으로 가는지다. **화면 항목 전부가 옵션 하나로 처리된다.**

| 설정 화면 | Job `options` | 비고 |
|---|---|---|
| 페이지행 넣기 (켜기·끄기) | `include_page_number` | 끄면 아래 "넣을 면"을 무시한다 |
| 넣을 면 (홀수 면만 · 모든 면) | `page_row_on` | `odd` · `every` · `even` |
| 원본 페이지 번호 (왼쪽) | `show_orig_page` | |
| 점자 면 번호 (오른쪽) | `show_braille_page` | |
| 꼬리말 | `footer_braille` | 묵자를 AI가 점역한 결과를 넣는다 |
| 꼬리말 정렬 | `footer_align` | `center` · `right` |
| 꼬리말 수정 범위 | `footers_braille` | 아래 "면별 꼬리말" 참고 |
| 원본 페이지 변경선 | `show_change_line` | |
| 표지 페이지 수 | `cover_pages` | |
| 원본 페이지 번호 시작 | `orig_page_start` | |
| 점자 페이지 번호 시작 | `start_braille_page` | `options` 밖, Job 최상위 |
| 한 줄 칸 수 · 한 면 줄 수 | `cols` · `rows` | |

### 면별 꼬리말

"이 면부터 끝까지 / 이 면만"은 **편집 시점의 뜻**이지 조판 규칙이 아니다. 이 라이브러리가
그걸 알려면 편집 이력을 들고 있어야 한다. 그래서 **FE가 범위를 풀어** 면별 값으로 펼쳐 넘긴다.

```
점역사가 5면 꼬리말을 "부록"으로 바꾸고 [이 면부터 끝까지]를 골랐다.
문서가 8면이면 FE는 이렇게 만든다.

  footers_braille = { "5": "⠘⠮", "6": "⠘⠮", "7": "⠘⠮", "8": "⠘⠮" }

[이 면만]이었다면 { "5": "⠘⠮" } 하나다.
```

없는 면은 `footer_braille`을 쓴다. 칸 수·줄 수는 변환이 끝나면 못 바꾸므로 면 번호가 밀릴 일은 없다.

### 꼬리말은 어디서 오나

이 라이브러리는 점역하지 않는다. 흐름은 이렇다.

```
점역사가 "수능특강 사회문화"를 입력
  → BE 가 AI 서버 TranslateText RPC 로 보낸다 (200자 초과는 거절된다)
  → 유니코드 점자 문자열을 받는다
  → Job 의 footer_braille 에 넣는다
  → build_brf / build_pages_from_job 이 자리에만 놓는다
```

---

## 함수

낮은 층(줄 하나)과 높은 층(문서 전체)이 있다. **보통은 높은 층만 쓴다.**

| 함수 | 무엇을 | 언제 |
|---|---|---|
| `build_brf(job)` | Job → `.brf` 파일 내용 | BE 다운로드 |
| `build_pages_from_job(job)` | Job → 점자 면 배열 | FE 화면 · BE `.txt` |
| `options_from_job(job)` | Job의 `options` → `Options` | 위 둘이 내부에서 쓴다 |
| `build_pages(sources, footer, start, opts, footers)` | 원본 쪽별 통 문자열 → 면 배열 | Job 형식을 안 쓸 때 |
| `page_row(orig, cont_idx, bp, footer, opts)` | 페이지행 한 줄 | 줄 하나만 다시 그릴 때 |
| `page_change_line(orig, opts)` | 원본 페이지 변경선 한 줄 | 〃 |
| `to_brf_ascii(braille)` | 유니코드 점자 → BRF-ASCII | 파일에 쓰기 직전 |

ts는 같은 이름의 camelCase(`buildBrf` · `buildPagesFromJob` · `pageRow` …),
java는 `BrailleAssist` 클래스의 정적 메서드다.

```python
from braille_assist import page_row, page_change_line, to_brf_ascii

page_row(orig_page=72, cont_idx=0, braille_page=105, footer="⠎⠣⠞⠕⠛⠕⠈⠮")
# → '⠼⠛⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠎⠣⠞⠕⠛⠕⠈⠮⠀⠀⠀⠀⠀⠀⠀⠀⠼⠁⠚⠑'   (32칸)

page_change_line(orig_page=72)
# → '⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠼⠛⠃'   (32칸)

to_brf_ascii(page_row(72, 0, 105, "⠎⠣⠞⠕⠛⠕⠈⠮"))
# → '#gb         s<togo@!        #aje'
```

### 옵션

```python
Options(
    cols=32,                  # 한 줄 칸 수
    rows=26,                  # 한 면 줄 수
    show_orig_page=True,      # 페이지행 왼쪽의 원본 페이지 번호
    show_braille_page=True,   # 페이지행 오른쪽의 점자 면 번호
    page_row_on="odd",        # 페이지행을 넣는 면 — odd | every | even | none
    cover_pages=0,            # 앞에서 이만큼의 원본 페이지가 표지
    orig_page_start=None,     # 표지 다음 첫 본문 페이지에 붙일 번호
    show_change_line=True,    # 원본 페이지 변경선
    footer_align="center",    # 꼬리말 정렬 — center | right
)
```

`Options`를 직접 만들 일은 드물다. Job을 쓰면 `options_from_job`이 알아서 만든다.

---

## 용어

이 두 낱말은 문서·코드·화면에서 같은 뜻으로만 쓴다.

**페이지행** — 점자 면의 **맨 아랫줄**. 원본 페이지 번호(왼쪽) · 꼬리말(가운데) ·
점자 면 번호(오른쪽)가 한 줄에 들어간다.

```
⠼⠛⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠎⠣⠞⠕⠛⠕⠈⠮⠀⠀⠀⠀⠀⠀⠀⠀⠼⠁⠚⠑
└ 원본 72쪽      └ 꼬리말             └ 점자 105면
```

**원본 페이지 변경선** — 원본 한 쪽의 내용이 끝나는 **바로 다음 줄**. `⠤`로 채우고
오른쪽 끝에 **새로 시작하는** 원본 페이지 번호만 적는다. 꼬리말도 점자 면 번호도 없다.

```
⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠤⠼⠛⠃
                              └ 여기부터 원본 72쪽
```

---

## 조판 규칙과 근거

전부 「점자 도서 제작 지침」 원문에 근거가 있다. **가정으로 채운 값은 없다.**

### 페이지행

지침 1장 2절 2 — 면의 마지막 줄에 원본 쪽 번호 · 꼬리말 · 점자 면 번호를 순서대로.

| 항목 | 규칙 | 근거 |
|---|---|---|
| 원본 쪽 번호 | 왼쪽 정렬, 첫 칸 | 1장 2절 2-2(2) |
| 걸침 알파벳 | 원본 한 쪽이 여러 면에 걸치면 **두 번째 면부터 번호 앞에** 로마자표 없이 a, b, c… | 1장 2절 2-2(3) · [예 1-7] |
| 꼬리말 | 가운데 정렬, **항목 사이 두 칸 이상** | 1장 3-1) |
| 꼬리말 초과 | 들어갈 칸수만큼만 적는다 | 1장 3-4) |
| 점자 면 번호 | 오른쪽 정렬 | 1장 2절 2-3(1) |

**가운데 정렬은 올림이다** — `start = (cols - len(footer) + 1) // 2`.
지침 실물 4건([예 1-6] · [예 1-7]×3 · [예 1-8])이 전부 이 값과 일치한다.
내림으로 하면 꼬리말이 홀수 칸일 때([예 1-6], 13칸) 한 칸 어긋난다.

**우측 정렬**(`footer_align="right"`)은 점자 면 번호에서 **두 칸 띄운 자리**가 오른쪽 끝이다.
항목 사이 두 칸 이상(1장 3-1)을 지킨 값이다.

**`cont_idx`는 점자 면 순번이지 페이지행 순번이 아니다.**
[예 1-7]은 105·107·109면에 `없음`·`b`·`d`를 붙인다. 지침이 페이지행을 홀수 면에만
찍기 때문에 `a`(106면)·`c`(108면)가 건너뛰어 **보이는 것**이지, 순번이 건너뛴 게 아니다.

```
105면 cont_idx=0 → #gb     (접두 없음)
106면 cont_idx=1 → a#gb    (짝수 면이라 페이지행이 안 찍힌다)
107면 cont_idx=2 → b#gb    ← 지침 실물
109면 cont_idx=4 → d#gb    ← 지침 실물
```

### 문서 조립

| 단계 | 규칙 | 근거 |
|---|---|---|
| 블록 이어붙임 | `order`로 정렬 | — |
| 32칸 줄바꿈 | **그대로 자른다.** 어절 단위 규칙은 없다 | 조판 가이드 §1 확정 |
| 변경선 삽입 | 원본 쪽 경계마다(첫 쪽 앞은 제외) | 지침 2장 2절 2-3(1) |
| 면 나눔 | `rows`줄. 페이지행이 들어가는 면은 본문이 한 줄 줄어든다 | 지침 1장 3 (32칸×26줄) |
| 페이지행 삽입 면 | `page_row_on` | 지침 1장 2절 2-1(홀수 면) · 원장 C-11 |
| 페이지행 원본 번호 | **그 면 첫 줄이 속한 원본 쪽** | 지침 1장 2절 2-2(4) |
| 걸침 순번 | 그 원본 쪽이 **처음 나온 면부터 센 순번**(0부터) | [예 1-7] 실물 |
| 표지 | 앞에서 `cover_pages`개 **원본 페이지**는 페이지행을 넣지 않는다 | 조판 옵션 §5 |
| 원본 번호 다시 매기기 | `orig_page_start`가 있으면 표지 뒤 n번째 = `orig_page_start + n` | 조판 설정 |

> **면 첫 줄의 빈 줄은 버린다.** 지침 개정 3("점자 페이지 첫 줄 … 예외 최소화")에 따른 처리다.

### BRF-ASCII 변환

표준 Braille ASCII 64셀 표. **공백 셀 `⠀`(U+2800)은 리터럴 스페이스로 낸다.**
못 푸는 셀은 조용히 버리지 않고 `⟨XXXX⟩`(코드포인트)로 남긴다.

> 점자 도서 코퍼스(`*.brl`)는 백틱(`` ` ``)을 `⠈`(초성 ㄱ)으로 쓴다. 여기서 백틱을
> 공백으로 바꾸면 **초성 ㄱ이 통째로 사라진다**(2026-07-13 채점 붕괴 전례).
> 이 함수는 공백을 스페이스로만 내므로 그 사고가 재현되지 않는다.

---

## 이 라이브러리가 하지 않는 것

| 하지 않는 것 | 누가 하나 |
|---|---|
| 묵자 → 점자 점역 | AI 서버 (`ProcessPage` · 꼬리말은 `TranslateText`) |
| 들여쓰기 · 가운데 정렬 · 구조적 빈 줄 | AI 서버가 `text` 안에 넣어 보낸다 |
| 꼬리말 "이후 전부 / 이 면만" 해석 | FE (면별 값으로 펼쳐서 넘긴다) |
| 어절 단위 줄바꿈 | 아무도 하지 않는다. 32칸에서 그대로 자른다 |

### ⚠ `cols`를 32에서 바꿀 때

이 라이브러리는 본문을 새 폭으로 다시 접는다. 그런데 **글상자 테두리와 표 격자는
AI가 32칸으로 이미 만들어 보낸 뒤**라, 본문만 좁아지고 테두리는 32칸으로 남는다.

AI 쪽이 `cols`를 받아 만들도록 고치기 전에는 **화면에서 32 고정**으로 두는 편이 안전하다.
`rows`는 조판 단계에서만 쓰이므로 지금 바꿔도 문제없다.

---

## ⚠ 조판 가이드(2026-08-05) §4의 호출 예 두 개는 틀렸다

| 예 | 문제 |
|---|---|
| `page_row(orig_page=7, …)` | 결과가 **33칸**. 32칸 규격 위반 |
| `page_row(orig_page=8, …)` | 꼬리말 시작 칸이 규정값보다 **두 칸 앞** |

**지침 실물이 정본이다.** 이 레포는 지침을 따르고, 그 4건을 `vectors.json`에 근거와 함께 넣었다.

---

## 검증

`vectors.json`이 유일한 정답 파일이다. 케이스 **48건** 중 **12건이 지침 실물 근거**이고
(`source` 필드에 조항을 적었다), 나머지는 회귀 방지용으로 기준 구현을 굳힌 것이다.

```bash
python python/test_vectors.py     # python
cd ts && npm test                 # ts (빌드 없이 돈다)
cd java && mvn test               # java
```

벡터를 다시 만들 때는 `python tools/gen_vectors.py`.
⚠ **다시 만들기 전에 지침 근거 케이스가 그대로 통과하는지 먼저 확인할 것.**
그 값들은 사람이 원문과 대조한 정답이지 구현의 출력이 아니다.

**BRF 표는 두 겹으로 지킨다.**
1. **64셀 전수 벡터** — 표가 한 칸이라도 어긋나면 세 언어 CI에서 잡힌다.
2. **코퍼스 대조**(2026-08-05, 이 레포 밖) — 점자 도서 gold **1,251쪽 · 2,546,903셀**을
   `to_brf_ascii`와 정본 도구(`code/AI/app/utils/braille_ascii.py`)로 각각 변환해
   **불일치 0** 확인. 표를 여기서 새로 만든 게 아니라 정본을 옮긴 것임을 실증한 것이다.

---

## 바뀐 것

### 2026-09-01 — 조판 설정 화면이 쓰는 항목을 전부 연결

| 무엇 | 어떻게 |
|---|---|
| **표지 판정** | `쪽 번호 ≤ cover_pages` → **`sources` 순번**. 번호가 1부터 시작하지 않거나 `orig_page_start`로 다시 매기면 번호 비교가 어긋난다. 쪽 번호가 1부터인 기존 호출은 결과가 같다 |
| **켜기·끄기와 위치** | `include_page_number`와 `page_row_on`은 **같은 스위치**다. 끄기가 이긴다 |
| **변경선** | `show_change_line`으로 따로 끈다. `show_orig_page`가 꺼지면 적을 번호가 없어 함께 꺼진다 |
| **Job 어댑터** | `options_from_job`이 `cols·rows·include_page_number` 셋만 읽던 것을 위 항목 전부로 넓혔다. Options에 있어도 Job에서 안 읽히면 죽은 값이다 |
| **새 옵션** | `orig_page_start` · `show_change_line` · `footer_align` · `build_pages(footers=…)` |

### 2026-08-06 — `page_row_on` 기본값을 `every`에서 `odd`로

지침 1장 2절 2-1이 홀수 면만이라 하고, 점자 도서 82권 실측에서도 페이지행을 가진 면이
100% 홀수였다(원장 C-11 — 규정과 관행이 같음). 종전 기본값 `every`는 규정과 어긋났다.

## 버전

서비스 버전(v3.x)과 독립인 semver. `v0.1.0`부터.
