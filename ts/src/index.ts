/**
 * braille-assist — 점자 조판 공용 함수 3개 (TypeScript).
 *
 * python/java 구현과 출력이 같아야 한다. 규칙이 바뀌면 세 구현과 vectors.json을 한 PR로 갱신한다.
 * 이 모듈은 한글을 점역하지 않는다 — 꼬리말은 이미 점역된 점자를 받아 배치만 한다.
 *
 * 근거: 「점자 도서 제작 지침」 1장 2절 2 · 1장 3 · 2장 2절 2-3.
 */

export const SPACE = '⠀'; // 공백 셀 ⠀
const NUM_SIGN = '⠼'; // 수표 ⠼
const CHANGE_MARK = '⠤'; // 변경선 채움 ⠤

// 숫자·알파벳은 같은 점형(1=a=⠁ … 0=j=⠚). 수표가 앞에 오면 숫자로 읽는다.
const DIGIT_CELLS = '⠚⠁⠃⠉⠙⠑⠋⠛⠓⠊';
const ALPHA_CELLS = '⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚⠅⠇⠍⠝⠕⠏⠟⠗⠎⠞⠥⠧⠺⠭⠽⠵';

// BRF Braille ASCII 64셀 표준표(유니코드 오프셋 0..63 순).
const BRAILLE_ASCII =
  ' A1B\'K2L@CIF/MSP' +
  '"E3H9O6R^DJG>NTQ' +
  ',*5<-U8V.%[$+X!&' +
  ';:4\\0Z7(_?W]#Y)=';

export interface Options {
  cols: number;
  rows: number;
  showOrigPage: boolean;
  showBraillePage: boolean;
  /** 페이지행을 넣는 면. 지침은 홀수 면만이지만 1차 고정값은 every(원장 C-11 자문 예정). */
  pageRowOn: 'every' | 'odd' | 'even';
  coverPages: number;
}

/** 1차 PoC 고정값 (조판 가이드 §5). */
export const DEFAULT_OPTIONS: Options = {
  cols: 32,
  rows: 26,
  showOrigPage: true,
  showBraillePage: true,
  pageRowOn: 'every',
  coverPages: 0,
};

function resolve(opts?: Partial<Options>): Options {
  const o = { ...DEFAULT_OPTIONS, ...(opts ?? {}) };
  if (o.cols < 8) throw new Error(`cols는 8 이상이어야 한다: ${o.cols}`);
  if (!['every', 'odd', 'even'].includes(o.pageRowOn))
    throw new Error(`pageRowOn은 every|odd|even: ${o.pageRowOn}`);
  return o;
}

/** 정수 → 수표 + 숫자 점형. 예: 12 → ⠼⠁⠃ */
function num(n: number): string {
  if (!Number.isInteger(n) || n < 0) throw new Error(`페이지 번호는 0 이상 정수: ${n}`);
  let s = NUM_SIGN;
  for (const d of String(n)) s += DIGIT_CELLS[Number(d)];
  return s;
}

/**
 * 걸침 순번 → 알파벳 점형. 1→a, 2→b … 26→z, 27→aa.
 * 지침 1장2절2-2(3): 두 번째 점자 면부터 번호 **앞에** 로마자표 없이 알파벳.
 * 실물 [예 1-7]에서 105면(0)·107면(2=b)·109면(4=d) — 면 순번이지 페이지행 순번이 아니다.
 */
function alpha(idx: number): string {
  if (idx <= 0) return '';
  let out = '';
  let i = idx;
  while (i > 0) {
    const r = (i - 1) % 26;
    i = Math.floor((i - 1) / 26);
    out = ALPHA_CELLS[r] + out;
  }
  return out;
}

/**
 * 페이지행 1줄(폭 = opts.cols).
 *
 * 지침 1장2절2·1장3: 원본 쪽 번호 왼쪽 정렬 첫 칸(걸침이면 번호 앞에 알파벳) ·
 * 꼬리말 가운데 정렬(항목 사이 두 칸 이상) · 점자 면 번호 오른쪽 정렬.
 *
 * ★ 가운데 정렬은 **올림**: start = (cols - footer.length + 1) >> 1.
 * 지침 실물 4건이 전부 이 값과 일치한다. 내림이면 [예 1-6](꼬리말 13칸)이 1칸 어긋난다.
 * ⚠ 조판 가이드 §4의 호출 예 두 개는 이 규칙과 다르다(예1은 33칸, 예2는 시작 2 어긋남) —
 * **지침 실물이 정본이다.**
 */
export function pageRow(
  origPage: number,
  contIdx: number,
  braillePage: number,
  footer = '',
  opts?: Partial<Options>,
): string {
  const o = resolve(opts);
  const n = o.cols;
  const left = o.showOrigPage ? alpha(contIdx) + num(origPage) : '';
  const right = o.showBraillePage ? num(braillePage) : '';
  if (left.length + right.length > n)
    throw new Error(`쪽 번호만으로 ${n}칸을 넘는다: ${left.length} + ${right.length}`);

  const cells: string[] = new Array(n).fill(SPACE);
  for (let i = 0; i < left.length; i++) cells[i] = left[i];
  for (let i = 0; i < right.length; i++) cells[n - right.length + i] = right[i];

  if (footer) {
    // 항목 사이 두 칸 이상(지침 1장3-1). 자리에 안 들어가면 뒤에서 자른다(1장3-4).
    const lo = left ? left.length + 2 : 0;
    const hi = right ? n - right.length - 2 : n;
    const f = footer.length > hi - lo ? footer.slice(0, hi - lo) : footer;
    if (f) {
      let start = (n - f.length + 1) >> 1; // ★ 올림 — 지침 실물로 확정
      start = Math.min(Math.max(start, lo), hi - f.length);
      for (let i = 0; i < f.length; i++) cells[start + i] = f[i];
    }
  }
  return cells.join('');
}

/**
 * 원본 페이지 변경선 1줄. 지침 2장2절2-3: 첫 칸부터 ⠤로 채우고 오른쪽 끝에 새 원본 쪽 번호.
 * 실물 [예 1-7]: 채움 29칸 + `#gb` 3칸 = 32.
 */
export function pageChangeLine(origPage: number, opts?: Partial<Options>): string {
  const o = resolve(opts);
  const s = o.showOrigPage ? num(origPage) : '';
  if (s.length > o.cols) throw new Error(`쪽 번호가 ${o.cols}칸을 넘는다: ${s.length}`);
  return CHANGE_MARK.repeat(o.cols - s.length) + s;
}

const CELL_TO_ASCII = new Map<string, string>();
for (let i = 0; i < 64; i++) CELL_TO_ASCII.set(String.fromCharCode(0x2800 + i), BRAILLE_ASCII[i]);
// 표준 ASCII `[ \ ] ^` 는 지침 표기에서 시프트형 `{ | } ~` 로 나온다.
const UNSHIFT: Record<string, string> = { '[': '{', '\\': '|', ']': '}', '^': '~' };

/**
 * 유니코드 점자 → BRF-ASCII(소문자). 파일에 쓰기 직전 한 번 호출한다.
 *
 * 공백 셀 ⠀는 **리터럴 스페이스**로 낸다(가이드 §3: `⠼⠛⠀⠀…` → `#g  …`).
 * ⚠ 코퍼스 .brl 관례의 백틱(` = ⠈ = 초성 ㄱ)과 혼동 금지 — 백틱을 공백으로 쓰면 초성 ㄱ이 사라진다.
 * 줄바꿈은 보존하고, 못 푸는 셀은 `⟨XXXX⟩`로 남긴다(조용히 버리지 않는다).
 */
export function toBrfAscii(braille: string): string {
  let out = '';
  for (const ch of braille) {
    if (ch === '\n') out += '\n';
    else if (ch === SPACE || ch === ' ') out += ' ';
    else {
      const a = CELL_TO_ASCII.get(ch);
      out += a === undefined
        ? `⟨${ch.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0')}⟩`
        : (UNSHIFT[a] ?? a.toLowerCase());
    }
  }
  return out;
}

// ── 문서 조립 (2026-08-05 추가) ──────────────────────────────────────────────
// 왜 여기 있나: ① 어느 면에 페이지행을 넣나 ② 걸침 순번(a·b·c)을 어떻게 세나
// ③ 표지를 어디까지 빼나 — 셋 다 지침 규칙이다. 호출자가 각자 구현하면 점자 규정이
// 레포 밖으로 흩어진다. 이 레포를 만든 이유가 그걸 막으려는 것이다.

export interface Block { order: number; text: string }
export interface Source { orig_page: number; blocks: Block[] }

/** 32칸이 차면 그대로 자른다. 어절 단위 줄바꿈 규칙은 없다(조판 가이드 §1 확정). */
function wrap(line: string, cols: number): string[] {
  if (!line) return [''];
  const out: string[] = [];
  for (let i = 0; i < line.length; i += cols) out.push(line.slice(i, i + cols));
  return out;
}

function hasPageRow(braillePage: number, on: string): boolean {
  if (on === 'odd') return braillePage % 2 === 1;
  if (on === 'even') return braillePage % 2 === 0;
  return true;
}

/**
 * 원본 쪽별 통 문자열 → 완성된 점자 면 배열. BRF 변환 직전 상태다.
 *
 * ★ 페이지행의 원본 번호 = **그 면 첫 줄이 속한 원본 쪽**(지침 1장2절2-2(4)).
 * ★ 걸침 순번 = 그 원본 쪽이 **처음 나온 면부터 센 순번**(0부터).
 *   지침 [예 1-7]이 105·107·109면에 없음·b·d를 붙이는 근거 — 페이지행이 홀수 면에만
 *   찍혀 a(106)·c(108)가 안 보이는 것이지 순번이 건너뛴 게 아니다.
 */
export function buildPages(
  sources: Source[],
  footer = '',
  startBraillePage = 1,
  opts?: Partial<Options>,
): string[][] {
  const o = resolve(opts);
  // 1) 원본 쪽 경계마다 변경선을 넣고 32칸으로 자른다. 줄마다 소속 원본 쪽을 들고 간다.
  const flat: Array<[string, number]> = [];
  sources.forEach((src, i) => {
    const op = src.orig_page;
    if (i > 0) flat.push([pageChangeLine(op, opts), op]);   // 첫 쪽 앞에는 두지 않는다
    const blocks = [...(src.blocks ?? [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
    const text = blocks.map((b) => b.text ?? '').join('');
    for (const logical of text.split('\n')) for (const w of wrap(logical, o.cols)) flat.push([w, op]);
  });

  // 2) 면으로 나눈다. 페이지행이 들어가는 면은 본문이 한 줄 줄어든다.
  const pages: string[][] = [];
  const firstSeen = new Map<number, number>();
  let pos = 0;
  while (pos < flat.length) {
    while (pos < flat.length && flat[pos][0].trim() === '') pos++;   // 면 첫 줄의 빈 줄은 버린다
    if (pos >= flat.length) break;
    const idx = pages.length;
    const bp = startBraillePage + idx;
    const head = flat[pos][1];
    const onCover = head <= o.coverPages;      // 표지 범위는 페이지행 생략
    const hasRow = hasPageRow(bp, o.pageRowOn) && !onCover;
    const cap = o.rows - (hasRow ? 1 : 0);
    const body = flat.slice(pos, pos + cap).map(([ln]) => ln);
    pos += cap;
    if (!firstSeen.has(head)) firstSeen.set(head, idx);
    while (body.length < cap) body.push('');
    if (hasRow) body.push(pageRow(head, idx - (firstSeen.get(head) as number), bp, footer, opts));
    pages.push(body);
  }
  return pages;
}
