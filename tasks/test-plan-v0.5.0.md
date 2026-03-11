# Test Plan — v0.5.0 MD→DOCX Conversion

Status: IN PROGRESS
Blocking: push to remote + GitHub release

---

## 1. CLI Behavior Tests

These run in seconds and verify the interface contract.

| # | Command | Expected |
|---|---------|----------|
| 1.1 | `python -m cli test.md -o out.docx` | exits 0, writes binary `.docx`, prints `Converted:` to stderr |
| 1.2 | `python -m cli test.md` (no `-o`) | exits 1, prints `MD to DOCX conversion requires an output file path` to stderr |
| 1.3 | `python -m cli missing.md -o out.docx` | exits 1, prints `File not found` |
| 1.4 | `python -m cli test.md --format md -o out.docx` | exits 0 (explicit format flag works) |
| 1.5 | `python -m cli test.docx -o out.md` | exits 0 (DOCX→MD unaffected — regression) |
| 1.6 | `python -m cli test.html -o out.md` | exits 0 (HTML→MD unaffected — regression) |

---

## 2. Element Coverage Tests

Create `tests/fixtures/elements.md` with every supported element. Convert and inspect programmatically.

**Fixture contents:**

```markdown
# H1 Title
## H2 Section
### H3 Subsection
#### H4
##### H5
###### H6

Plain paragraph.

**bold** and *italic* and `inline code` and a [link](https://example.com).

---

- Bullet A
- Bullet B
- Bullet C

1. One
2. Two
3. Three

> Blockquote text here.

    code block line 1
    code block line 2

| Col A | Col B | Col C |
|-------|-------|-------|
| 1A    | 1B    | 1C    |
| 2A    | 2B    | 2C    |
```

**Programmatic checks (run via `python -c "..."`):**

| # | Check | Pass Criteria |
|---|-------|--------------|
| 2.1 | Heading styles | paragraphs with `style.name` in `["Heading 1".."Heading 6"]` present for each level |
| 2.2 | Bold run | run with `bold=True` in paragraph containing "bold" |
| 2.3 | Italic run | run with `italic=True` in paragraph containing "italic" |
| 2.4 | Inline code run | run with `font.name == "Courier New"` in paragraph containing "inline code" |
| 2.5 | Link text | paragraph contains text matching `link (https://example.com)` |
| 2.6 | Bullet list | paragraphs with `style.name == "List Bullet"` count == 3 |
| 2.7 | Numbered list | paragraphs with `style.name == "List Number"` count == 3 |
| 2.8 | Blockquote | paragraph with `style.name == "Quote"` present |
| 2.9 | Code block | paragraph with `style.name == "No Spacing"` with monospace font present |
| 2.10 | Table structure | `doc.tables` count == 1; table has 3 rows × 3 cols; cell[0][0] == "Col A"; cell[2][2] == "2C" |
| 2.11 | Thematic break | paragraph with border XML present (check `w:pBdr` in paragraph XML) |

---

## 3. Edge Cases

| # | Input | Expected |
|---|-------|----------|
| 3.1 | Empty file (`""`) | Exits 0, writes valid (empty) `.docx` — no crash |
| 3.2 | Headings only (no body) | `.docx` contains only Heading paragraphs |
| 3.3 | Table with 1 column | Renders without IndexError |
| 3.4 | Nested list (list inside list item) | Inner list items render as separate paragraphs; no crash |
| 3.5 | Very long paragraph (1000+ words) | Renders as single paragraph; no truncation |
| 3.6 | Unicode content (CJK, emoji, accented chars) | Characters preserved in output |
| 3.7 | MD file with no trailing newline | Converts cleanly |
| 3.8 | Markdown with raw HTML (`<div>`, `<span>`) | HTML stripped silently; surrounding content preserved |

---

## 4. Visual / Manual Eval Checklist

Open `tests/fixtures/elements.docx` in Word or LibreOffice after conversion.

- [ ] **H1** renders large, bold heading at top
- [ ] **H2–H6** progressively smaller; all use native Word heading styles (navigable in doc outline)
- [ ] **Bold/italic/code** inline styles visible within the paragraph — not as raw `**` markers
- [ ] **Thematic break** renders as a visible horizontal rule
- [ ] **Bullet list** uses Word's native bullet formatting (not hyphens)
- [ ] **Numbered list** uses Word's native auto-numbering
- [ ] **Blockquote** visually indented or styled differently from body text
- [ ] **Code block** rendered in monospace font, no spacing between lines
- [ ] **Table** has visible grid borders; header row distinguishable (bold or background)
- [ ] **Link** displays as `label (url)` — no raw Markdown syntax visible
- [ ] File opens without warnings or repair prompts in Word

---

## 5. Regression — Existing Converters

Confirm the dispatcher changes don't break existing paths.

| # | Command | Expected |
|---|---------|----------|
| 5.1 | `python -m cli examples/confluence/sample-input.html -o /tmp/out.md` | exits 0 |
| 5.2 | Output of 5.1 contains expected Markdown structure (headings, no HTML tags) | pass |
| 5.3 | `detect_format` returns correct values: `.docx`→`docx`, `.pdf`→`pdf`, `.html`→`html`, `.htm`→`html`, `.md`→`md`, `.xyz`→`None` | pass |

---

## 6. Pass Criteria to Push

All of the following must be green before pushing the tag to remote:

- [ ] All CLI behavior tests (§1) pass
- [ ] All element coverage checks (§2) pass programmatically
- [ ] All edge cases (§3) pass without crash
- [ ] Visual eval (§4) — at minimum, heading styles, bold/italic/code, list styles, and table render correctly
- [ ] HTML regression (§5) passes
- [ ] `git diff main..HEAD` reviewed — no unintended changes

---

## Execution Log

_Fill in as tests are run._

| Test | Result | Notes |
|------|--------|-------|
| | | |
