package com.semojum.brailleassist;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;

/** vectors.json 대조 — java 구현. 세 언어가 같은 벡터로 같은 출력을 내야 한다. */
class VectorsTest {

    /** vectors.json은 언어 중립으로 snake_case를 쓴다 — java는 camelCase라 여기서 옮긴다. */
    private static BrailleAssist.Options toOpts(JsonNode o) {
        if (o == null || o.isNull()) return BrailleAssist.Options.defaults();
        return new BrailleAssist.Options(
                o.get("cols").asInt(),
                o.get("rows").asInt(),
                o.get("show_orig_page").asBoolean(),
                o.get("show_braille_page").asBoolean(),
                o.get("page_row_on").asText(),
                o.get("cover_pages").asInt());
    }

    private static String call(String fname, JsonNode a) {
        switch (fname) {
            case "page_row":
                return BrailleAssist.pageRow(
                        a.get("orig_page").asInt(),
                        a.get("cont_idx").asInt(),
                        a.get("braille_page").asInt(),
                        a.has("footer") ? a.get("footer").asText() : "",
                        toOpts(a.get("opts")));
            case "page_change_line":
                return BrailleAssist.pageChangeLine(a.get("orig_page").asInt(), toOpts(a.get("opts")));
            case "to_brf_ascii":
                return BrailleAssist.toBrfAscii(a.get("braille").asText());
            default:
                throw new IllegalArgumentException("모르는 함수: " + fname);
        }
    }

    @TestFactory
    List<DynamicTest> vectors() throws Exception {
        Path p = Path.of("..", "vectors.json");
        JsonNode root = new ObjectMapper().readTree(Files.readString(p));
        List<DynamicTest> tests = new ArrayList<>();
        root.get("cases").fields().forEachRemaining(e -> {
            String fname = e.getKey();
            for (JsonNode c : e.getValue()) {
                tests.add(DynamicTest.dynamicTest(
                        fname + " — " + c.get("name").asText(),
                        () -> assertEquals(c.get("expect").asText(), call(fname, c.get("args")))));
            }
        });
        return tests;
    }
}
