// vectors.json 대조 — ts 구현. 빌드 없이 돈다(node --experimental-strip-types).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { pageRow, pageChangeLine, toBrfAscii } from '../src/index.ts';

const here = dirname(fileURLToPath(import.meta.url));
const data = JSON.parse(readFileSync(join(here, '..', '..', 'vectors.json'), 'utf8'));

// vectors.json은 언어 중립으로 snake_case를 쓴다 — ts는 camelCase라 여기서 옮긴다.
const toOpts = (o) => o && {
  cols: o.cols, rows: o.rows,
  showOrigPage: o.show_orig_page, showBraillePage: o.show_braille_page,
  pageRowOn: o.page_row_on, coverPages: o.cover_pages,
};

const call = {
  page_row: (a) => pageRow(a.orig_page, a.cont_idx, a.braille_page, a.footer ?? '', toOpts(a.opts)),
  page_change_line: (a) => pageChangeLine(a.orig_page, toOpts(a.opts)),
  to_brf_ascii: (a) => toBrfAscii(a.braille),
};

let total = 0, fails = 0;
for (const [fname, cases] of Object.entries(data.cases)) {
  for (const c of cases) {
    total++;
    const got = call[fname](c.args);
    if (got !== c.expect) {
      fails++;
      console.error(`FAIL ${fname} — ${c.name}`);
      console.error(`  got    ${JSON.stringify(got)}`);
      console.error(`  expect ${JSON.stringify(c.expect)}`);
    }
  }
}
console.log(`ts: ${total - fails}/${total} 통과${fails ? ` — 실패 ${fails}건` : ''}`);
process.exit(fails ? 1 : 0);
