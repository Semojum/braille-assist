package com.semojum.brailleassist;

/**
 * braille-assist — 점자 조판 공용 함수 3개 (Java).
 *
 * <p>python/ts 구현과 출력이 같아야 한다. 규칙이 바뀌면 세 구현과 vectors.json을 한 PR로 갱신한다.
 * 이 클래스는 한글을 점역하지 않는다 — 꼬리말은 이미 점역된 점자를 받아 배치만 한다.
 *
 * <p>근거: 「점자 도서 제작 지침」 1장 2절 2 · 1장 3 · 2장 2절 2-3.
 */
public final class BrailleAssist {

    /** 공백 셀 ⠀ */
    public static final char SPACE = '⠀';
    private static final char NUM_SIGN = '⠼';    // 수표 ⠼
    private static final char CHANGE_MARK = '⠤'; // 변경선 채움 ⠤

    // 숫자·알파벳은 같은 점형(1=a=⠁ … 0=j=⠚). 수표가 앞에 오면 숫자로 읽는다.
    private static final String DIGIT_CELLS = "⠚⠁⠃⠉⠙⠑⠋⠛⠓⠊";
    private static final String ALPHA_CELLS = "⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚⠅⠇⠍⠝⠕⠏⠟⠗⠎⠞⠥⠧⠺⠭⠽⠵";

    /** BRF Braille ASCII 64셀 표준표(유니코드 오프셋 0..63 순). */
    private static final String BRAILLE_ASCII =
            " A1B'K2L@CIF/MSP"
            + "\"E3H9O6R^DJG>NTQ"
            + ",*5<-U8V.%[$+X!&"
            + ";:4\\0Z7(_?W]#Y)=";

    private BrailleAssist() {}

    /** 조판 옵션. 1차 PoC 고정값이 기본값이다(조판 가이드 §5). */
    public static final class Options {
        public final int cols;
        public final int rows;
        public final boolean showOrigPage;
        public final boolean showBraillePage;
        /** 페이지행을 넣는 면. 지침은 홀수 면만이지만 1차 고정값은 every(원장 C-11 자문 예정). */
        public final String pageRowOn;
        public final int coverPages;

        public Options(int cols, int rows, boolean showOrigPage, boolean showBraillePage,
                       String pageRowOn, int coverPages) {
            if (cols < 8) throw new IllegalArgumentException("cols는 8 이상이어야 한다: " + cols);
            if (!pageRowOn.equals("every") && !pageRowOn.equals("odd") && !pageRowOn.equals("even"))
                throw new IllegalArgumentException("pageRowOn은 every|odd|even: " + pageRowOn);
            this.cols = cols;
            this.rows = rows;
            this.showOrigPage = showOrigPage;
            this.showBraillePage = showBraillePage;
            this.pageRowOn = pageRowOn;
            this.coverPages = coverPages;
        }

        public static Options defaults() {
            return new Options(32, 26, true, true, "every", 0);
        }
    }

    /** 정수 → 수표 + 숫자 점형. 예: 12 → ⠼⠁⠃ */
    private static String num(int n) {
        if (n < 0) throw new IllegalArgumentException("페이지 번호는 0 이상이어야 한다: " + n);
        StringBuilder sb = new StringBuilder().append(NUM_SIGN);
        for (char d : String.valueOf(n).toCharArray()) sb.append(DIGIT_CELLS.charAt(d - '0'));
        return sb.toString();
    }

    /**
     * 걸침 순번 → 알파벳 점형. 1→a, 2→b … 26→z, 27→aa.
     *
     * <p>지침 1장2절2-2(3): 두 번째 점자 면부터 번호 <b>앞에</b> 로마자표 없이 알파벳.
     * 실물 [예 1-7]에서 105면(0)·107면(2=b)·109면(4=d) — 면 순번이지 페이지행 순번이 아니다.
     */
    private static String alpha(int idx) {
        if (idx <= 0) return "";
        StringBuilder sb = new StringBuilder();
        int i = idx;
        while (i > 0) {
            int r = (i - 1) % 26;
            i = (i - 1) / 26;
            sb.insert(0, ALPHA_CELLS.charAt(r));
        }
        return sb.toString();
    }

    /**
     * 페이지행 1줄(폭 = opts.cols).
     *
     * <p>지침 1장2절2·1장3: 원본 쪽 번호 왼쪽 정렬 첫 칸(걸침이면 번호 앞에 알파벳) ·
     * 꼬리말 가운데 정렬(항목 사이 두 칸 이상) · 점자 면 번호 오른쪽 정렬.
     *
     * <p>★ 가운데 정렬은 <b>올림</b>: start = (cols - footer.length() + 1) / 2.
     * 지침 실물 4건이 전부 이 값과 일치한다. 내림이면 [예 1-6](꼬리말 13칸)이 1칸 어긋난다.
     * ⚠ 조판 가이드 §4의 호출 예 두 개는 이 규칙과 다르다(예1은 33칸, 예2는 시작 2 어긋남) —
     * <b>지침 실물이 정본이다.</b>
     */
    public static String pageRow(int origPage, int contIdx, int braillePage,
                                 String footer, Options opts) {
        int n = opts.cols;
        String left = opts.showOrigPage ? alpha(contIdx) + num(origPage) : "";
        String right = opts.showBraillePage ? num(braillePage) : "";
        if (left.length() + right.length() > n)
            throw new IllegalArgumentException(
                    "쪽 번호만으로 " + n + "칸을 넘는다: " + left.length() + " + " + right.length());

        char[] cells = new char[n];
        java.util.Arrays.fill(cells, SPACE);
        for (int i = 0; i < left.length(); i++) cells[i] = left.charAt(i);
        for (int i = 0; i < right.length(); i++) cells[n - right.length() + i] = right.charAt(i);

        if (footer != null && !footer.isEmpty()) {
            // 항목 사이 두 칸 이상(지침 1장3-1). 자리에 안 들어가면 뒤에서 자른다(1장3-4).
            int lo = left.isEmpty() ? 0 : left.length() + 2;
            int hi = right.isEmpty() ? n : n - right.length() - 2;
            String f = footer.length() > hi - lo ? footer.substring(0, Math.max(0, hi - lo)) : footer;
            if (!f.isEmpty()) {
                int start = (n - f.length() + 1) / 2; // ★ 올림 — 지침 실물로 확정
                start = Math.min(Math.max(start, lo), hi - f.length());
                for (int i = 0; i < f.length(); i++) cells[start + i] = f.charAt(i);
            }
        }
        return new String(cells);
    }

    public static String pageRow(int origPage, int contIdx, int braillePage, String footer) {
        return pageRow(origPage, contIdx, braillePage, footer, Options.defaults());
    }

    /**
     * 원본 페이지 변경선 1줄. 지침 2장2절2-3: 첫 칸부터 ⠤로 채우고 오른쪽 끝에 새 원본 쪽 번호.
     * 실물 [예 1-7]: 채움 29칸 + {@code #gb} 3칸 = 32.
     */
    public static String pageChangeLine(int origPage, Options opts) {
        String s = opts.showOrigPage ? num(origPage) : "";
        if (s.length() > opts.cols)
            throw new IllegalArgumentException("쪽 번호가 " + opts.cols + "칸을 넘는다: " + s.length());
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < opts.cols - s.length(); i++) sb.append(CHANGE_MARK);
        return sb.append(s).toString();
    }

    public static String pageChangeLine(int origPage) {
        return pageChangeLine(origPage, Options.defaults());
    }

    /**
     * 유니코드 점자 → BRF-ASCII(소문자). 파일에 쓰기 직전 한 번 호출한다.
     *
     * <p>공백 셀 ⠀는 <b>리터럴 스페이스</b>로 낸다(가이드 §3: {@code ⠼⠛⠀⠀…} → {@code #g  …}).
     * ⚠ 코퍼스 .brl 관례의 백틱(` = ⠈ = 초성 ㄱ)과 혼동 금지 — 백틱을 공백으로 쓰면 초성 ㄱ이 사라진다.
     * 줄바꿈은 보존하고, 못 푸는 셀은 {@code ⟨XXXX⟩}로 남긴다(조용히 버리지 않는다).
     */
    public static String toBrfAscii(String braille) {
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < braille.length(); i++) {
            char ch = braille.charAt(i);
            if (ch == '\n') {
                out.append('\n');
            } else if (ch == SPACE || ch == ' ') {
                out.append(' ');
            } else if (ch >= 0x2800 && ch < 0x2840) {
                char a = BRAILLE_ASCII.charAt(ch - 0x2800);
                out.append(unshift(a));
            } else {
                out.append(String.format("⟨%04X⟩", (int) ch));
            }
        }
        return out.toString();
    }

    /** 표준 ASCII {@code [ \ ] ^} 는 지침 표기에서 시프트형 {@code { | } ~} 로 나온다. */
    private static char unshift(char a) {
        switch (a) {
            case '[': return '{';
            case '\\': return '|';
            case ']': return '}';
            case '^': return '~';
            default: return Character.toLowerCase(a);
        }
    }

    // ── 문서 조립 (2026-08-05 추가) ─────────────────────────────────────────
    // 왜 여기 있나: ① 어느 면에 페이지행을 넣나 ② 걸침 순번(a·b·c)을 어떻게 세나
    // ③ 표지를 어디까지 빼나 — 셋 다 지침 규칙이다. 호출자가 각자 구현하면 점자 규정이
    // 레포 밖으로 흩어진다. 이 레포를 만든 이유가 그걸 막으려는 것이다.

    /** 원본 쪽 하나의 통 문자열 묶음. blocks는 order로 정렬해 이어 붙인다. */
    public static final class Source {
        public final int origPage;
        public final java.util.List<Block> blocks;

        public Source(int origPage, java.util.List<Block> blocks) {
            this.origPage = origPage;
            this.blocks = blocks;
        }
    }

    public static final class Block {
        public final int order;
        public final String text;

        public Block(int order, String text) {
            this.order = order;
            this.text = text;
        }
    }

    /** 32칸이 차면 그대로 자른다. 어절 단위 줄바꿈 규칙은 없다(조판 가이드 §1 확정). */
    private static java.util.List<String> wrap(String line, int cols) {
        java.util.List<String> out = new java.util.ArrayList<>();
        if (line.isEmpty()) {
            out.add("");
            return out;
        }
        for (int i = 0; i < line.length(); i += cols) {
            out.add(line.substring(i, Math.min(i + cols, line.length())));
        }
        return out;
    }

    private static boolean hasPageRow(int braillePage, String on) {
        if (on.equals("odd")) return braillePage % 2 == 1;
        if (on.equals("even")) return braillePage % 2 == 0;
        return true;
    }

    /**
     * 원본 쪽별 통 문자열 → 완성된 점자 면 배열. BRF 변환 직전 상태다.
     *
     * <p>★ 페이지행의 원본 번호 = <b>그 면 첫 줄이 속한 원본 쪽</b>(지침 1장2절2-2(4)).
     * <p>★ 걸침 순번 = 그 원본 쪽이 <b>처음 나온 면부터 센 순번</b>(0부터).
     * 지침 [예 1-7]이 105·107·109면에 없음·b·d를 붙이는 근거 — 페이지행이 홀수 면에만
     * 찍혀 a(106)·c(108)가 안 보이는 것이지 순번이 건너뛴 게 아니다.
     */
    public static java.util.List<java.util.List<String>> buildPages(
            java.util.List<Source> sources, String footer, int startBraillePage, Options opts) {
        // 1) 원본 쪽 경계마다 변경선을 넣고 32칸으로 자른다. 줄마다 소속 원본 쪽을 들고 간다.
        java.util.List<String> lines = new java.util.ArrayList<>();
        java.util.List<Integer> owner = new java.util.ArrayList<>();
        for (int i = 0; i < sources.size(); i++) {
            Source src = sources.get(i);
            if (i > 0) {                       // 첫 원본 쪽 앞에는 변경선을 두지 않는다
                lines.add(pageChangeLine(src.origPage, opts));
                owner.add(src.origPage);
            }
            java.util.List<Block> bs = new java.util.ArrayList<>(
                    src.blocks == null ? java.util.Collections.emptyList() : src.blocks);
            bs.sort(java.util.Comparator.comparingInt(b -> b.order));
            StringBuilder sb = new StringBuilder();
            for (Block b : bs) sb.append(b.text == null ? "" : b.text);
            for (String logical : sb.toString().split("\n", -1)) {
                for (String w : wrap(logical, opts.cols)) {
                    lines.add(w);
                    owner.add(src.origPage);
                }
            }
        }

        // 2) 면으로 나눈다. 페이지행이 들어가는 면은 본문이 한 줄 줄어든다.
        java.util.List<java.util.List<String>> pages = new java.util.ArrayList<>();
        java.util.Map<Integer, Integer> firstSeen = new java.util.HashMap<>();
        int pos = 0;
        while (pos < lines.size()) {
            while (pos < lines.size() && lines.get(pos).trim().isEmpty()) pos++;  // 면 첫 빈 줄은 버린다
            if (pos >= lines.size()) break;
            int idx = pages.size();
            int bp = startBraillePage + idx;
            int head = owner.get(pos);
            boolean onCover = head <= opts.coverPages;    // 표지 범위는 페이지행 생략
            boolean hasRow = hasPageRow(bp, opts.pageRowOn) && !onCover;
            int cap = opts.rows - (hasRow ? 1 : 0);
            java.util.List<String> body = new java.util.ArrayList<>(
                    lines.subList(pos, Math.min(pos + cap, lines.size())));
            pos += cap;
            firstSeen.putIfAbsent(head, idx);
            while (body.size() < cap) body.add("");
            if (hasRow) body.add(pageRow(head, idx - firstSeen.get(head), bp, footer, opts));
            pages.add(body);
        }
        return pages;
    }

    public static java.util.List<java.util.List<String>> buildPages(
            java.util.List<Source> sources, String footer) {
        return buildPages(sources, footer, 1, Options.defaults());
    }
}
