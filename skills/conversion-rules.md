---
name: "Universal Conversion Rules"
description: "Baseline rules for converting any document format to clean Markdown"
type: conversion-guide
---

# Universal Conversion Rules

## Purpose

These are the universal rules that apply regardless of what source format you're converting from. Always load this skill first before any format-specific skill. Think of this as your baseline — every conversion starts here, and format-specific skills layer on top.

## Heading Hierarchy

Get headings right and the rest of the document falls into place.

- Use a single `#` (H1) for the document title. One per document, no exceptions.
- Use `##` (H2) for major sections.
- Use `###` (H3) for subsections within those sections.
- Never skip heading levels. Don't jump from H2 to H4 — if you need a sub-subsection, use H3 first.
- Remove numbering artifacts from headings. If the source has "1.2.3 My Section," the heading should just be `### My Section`. Let the document structure convey the hierarchy, not manual numbering.

## List Rules

Lists should be clean, consistent, and correctly nested.

- Use `-` for unordered lists. Not `*`, not `+` — just `-` for consistency.
- Use `1.` for all ordered list items. Let Markdown handle the auto-numbering. Don't manually number them `1.`, `2.`, `3.` — just use `1.` for every item.
- Indent nested lists with 2 spaces. This keeps nesting visually clear without wasting horizontal space.
- Preserve the list type from the source. If it was a numbered list in the original, keep it numbered. If it was bulleted, keep it bulleted. Don't change the author's intent.

## Table Rules

Tables in Markdown are inherently limited. Work within those limits gracefully.

- Use pipe tables (`| col1 | col2 |`). They're the most widely supported format.
- Always include a header row. Every table needs one — it's required by the Markdown spec.
- Always include an alignment row (`|---|---|`). Use `---` for left-aligned (default), `:---:` for centered, `---:` for right-aligned.
- Keep cells concise. If a cell has a paragraph of text, the table format is probably wrong for that content.
- Break complex tables into multiple simple tables if needed. A table with merged cells, nested tables, or heavily formatted content is better represented as multiple simple tables with explanatory text between them.

## Text Cleanup

Clean text is the foundation of good Markdown. Be thorough here.

- Remove smart quotes and replace them with straight quotes. `"` and `"` become `"`. `'` and `'` become `'`.
- Remove non-breaking spaces (`\u00A0`). Replace them with regular spaces.
- Remove zero-width characters (zero-width spaces, zero-width joiners, etc.). They're invisible troublemakers.
- Normalize whitespace: use a single blank line between block-level elements (paragraphs, headings, lists, tables). No double blank lines, no trailing spaces at the end of lines.
- Remove trailing whitespace from every line. It serves no purpose and clutters diffs.

## Link Handling

Links should be functional and clean.

- Preserve hyperlinks using standard Markdown format: `[link text](url)`.
- Convert footnotes to inline links where practical. If a footnote just contains a URL, bring it inline. If the footnote has substantial explanatory content, consider keeping it as a footnote or converting it to parenthetical text.
- Remove broken or internal-only links. If a link points to an intranet resource, a dead page, or a relative path that won't resolve, remove the link and keep the text. Optionally note that a link was removed if the context matters.

## Image Handling

Images need clear references even when the image itself can't be embedded.

- Use standard Markdown image syntax: `![alt text](path)`.
- Preserve meaningful alt text from the source. If the source has no alt text, write a brief description of the image content.
- Note images that can't be extracted. If an image is embedded in the source and can't be saved as a separate file, add a placeholder like `![Image: description of what was here](image-not-extracted)` so the gap is visible and actionable.

## Quality Checklist

Run through this before you call a conversion done:

1. Single H1? The document should have exactly one H1, used as the title.
2. Heading hierarchy intact? No skipped levels, logical nesting throughout.
3. Lists consistent? All unordered lists use `-`, all ordered lists use `1.`, nesting is correct.
4. Tables render correctly? Preview the output — do the tables actually display as tables?
5. No smart quotes? Search for curly quotes and apostrophes. They should all be straight.
6. No phantom formatting? No invisible spans, no empty bold/italic markers, no stray HTML tags.
7. Links work? Verify that links point somewhere real and use proper Markdown syntax.
8. Clean whitespace? Single blank lines between blocks, no trailing spaces, no double blanks.
