---
name: "PDF to Markdown"
description: "Reconstruct document structure from PDF layout for Markdown conversion"
type: conversion-guide
---

# PDF to Markdown

## Purpose

PDFs are fundamentally different from other document formats. They don't have semantic structure — no "this is a heading" or "this is a list item." They only have visual layout: text at specific coordinates, in specific fonts, at specific sizes. This skill reconstructs document hierarchy from those visual cues, which makes it the most interpretive of the conversion guides.

## Layout Reconstruction

Since PDFs lack semantic markup, you have to infer structure from visual properties:

- **Detect headings** by font size combined with weight. Text that is larger than body text and bold is almost certainly a heading. Text that is larger but not bold may still be a heading — use context to decide.
- **Determine heading level** by relative size. Don't map absolute font sizes to heading levels. Instead, rank the distinct font sizes used in the document and assign heading levels based on that ranking.
- **Detect paragraphs** by line spacing. A gap larger than the normal line-to-line spacing signals a paragraph break. Consecutive lines with uniform spacing are part of the same paragraph.
- **Detect lists** by leading characters. Lines starting with bullet characters, numbers followed by periods, or letters followed by parentheses are list items. Indentation level indicates nesting.

## Header/Footer Stripping

Repeating content at the top and bottom of pages needs to be removed.

- Identify repeating content across pages. Page numbers, document titles, author names, dates, and confidentiality notices that appear in the same position on every page are headers or footers.
- Remove headers and footers from the body text. They're structural chrome, not content.
- Watch for false positives. A section title that happens to appear at the top of multiple pages isn't a header — it's a coincidence of pagination. Compare the position and content carefully before stripping.

## Table Reconstruction

Tables in PDFs are just text positioned in a grid. Reconstructing them takes care.

- Detect tables by column alignment. When multiple lines of text have consistent horizontal positioning across several columns, that's likely a table.
- Use pdfplumber's table extraction when available. It does a solid job of detecting table boundaries and cell contents from the PDF's internal coordinates.
- Handle merged cells by repeating content. If a cell spans multiple columns or rows in the original, repeat its content in each cell of the Markdown table to preserve readability.
- Handle spanning headers. A header that spans the full width of a multi-column table should be placed above the table as a heading or introductory text, not crammed into the first cell.

## Font-Based Heading Detection

This is the primary method for establishing document hierarchy in PDFs.

- Map font sizes to heading levels by surveying the entire document first. Identify all distinct font sizes used, then assign heading levels relative to each other.
- The largest unique size becomes H1. There should typically be only one or a few instances.
- The second largest becomes H2. These are your major sections.
- Continue the pattern for H3 and below.
- Consider bold as a heading indicator. Text that is the same size as body text but bold may be a sub-heading, especially if it appears on its own line followed by regular text.

## Common Issues

PDFs throw unique curveballs that other formats don't:

- **Multi-column layouts** — Reflow to single column. Read the left column top-to-bottom first, then the right column. Don't interleave lines from different columns. This requires detecting column boundaries, which is usually identifiable by a consistent vertical gap in the middle of the page.
- **Hyphenated words at line breaks** — Rejoin them. If a word is split with a hyphen at the end of a line and continues on the next line, merge it back into a single word. Be careful with words that are legitimately hyphenated (like "well-known") — context and dictionary lookups help here.
- **Watermarks** — Remove watermark text. Watermarks are typically large, rotated, light-colored text overlaid on the page content. They're not part of the document content and should be stripped.
- **Scanned PDFs** — These contain images of text rather than actual text. OCR is required to extract content, which is outside the scope of this conversion guide. Note when a PDF appears to be scanned so the user knows an OCR step is needed first.

## Quality Checklist

Run through this before finalizing:

1. Headings detected correctly? Spot-check that font-size-based heading detection produced a logical hierarchy.
2. Headers/footers removed? No page numbers, repeated titles, or footer text in the body content.
3. Tables reconstructed? Tabular data is in pipe tables, not free-floating aligned text.
4. Columns reflowed? Multi-column layouts read in the correct order as single-column text.
5. Hyphens rejoined? No broken words at former line boundaries.
6. No watermark text? Background watermarks are stripped from the output.
