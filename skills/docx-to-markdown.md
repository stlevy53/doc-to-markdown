---
name: "Word DOCX to Markdown"
description: "Convert Word documents to Markdown preserving structure and handling Word-specific features"
type: conversion-guide
---

# Word DOCX to Markdown

## Purpose

Word `.docx` files use an XML-based format with rich style definitions under the hood. This skill maps those Word structures to their Markdown equivalents, handling the features and edge cases that are unique to the Word ecosystem.

## Style Mapping

Word styles map to Markdown elements in a straightforward way:

| Word Style | Markdown Equivalent |
|---|---|
| Heading 1 | `#` |
| Heading 2 | `##` |
| Heading 3 | `###` |
| Heading 4 | `####` |
| Heading 5 | `#####` |
| Heading 6 | `######` |
| Normal | Paragraph text |
| List Paragraph | List item (`-` or `1.`) |
| Title | `#` (treat as H1) |
| Subtitle | `##` (treat as H2) |
| Quote | `>` blockquote |
| Code / Code Block | Fenced code block (triple backticks) |

If the document uses custom styles, map them based on their visual appearance and intent. A custom style called "Section Header" that looks like a heading should become a heading.

## Track Changes

Track changes must be resolved before conversion produces clean output.

- Accept all changes before conversion unless you've been told to accept specific changes and reject others.
- Remove revision markup completely. No `<ins>`, `<del>`, or revision metadata should survive into the Markdown output.
- If the document has unresolved comments, note them separately rather than embedding them in the Markdown. Comments aren't part of the document content.

## Embedded Objects

Word documents can contain a variety of embedded objects. Handle each type appropriately:

- **Tables** — Convert to pipe tables. If a table is too complex for pipe format (deeply nested, merged cells), simplify the structure. See Table Rules in the universal conversion rules.
- **Images** — Note the filename and extract the image file if possible. Word stores images in the `word/media/` directory inside the `.docx` archive. Reference them with `![alt text](path-to-image)`.
- **Charts** — Charts can't be directly converted to Markdown. Describe them in text and note the original with a placeholder: `[Chart: description of what the chart shows]`.
- **SmartArt** — Convert SmartArt diagrams to plain lists or descriptive text. A hierarchy diagram becomes a nested list. A process diagram becomes a numbered list. Capture the content, not the visual layout.
- **Text boxes** — Integrate text box content into the normal document flow at the position where the text box appears. Don't lose the content, but don't try to replicate the floating layout.

## Common Issues

These problems come up frequently with Word documents:

- **Nested tables** — Flatten them. Markdown doesn't support nested tables, so extract the inner table content and present it separately or integrate it into the outer table's cells as plain text.
- **Manual numbering mixed with auto-numbering** — Some documents have lists where items are manually typed as "1.", "2.", "3." but aren't actually using Word's list feature, mixed with sections that do use auto-numbering. Normalize everything to proper Markdown list syntax.
- **Soft returns vs hard returns** — Word distinguishes between soft returns (Shift+Enter, which stays in the same paragraph) and hard returns (Enter, which starts a new paragraph). Normalize soft returns within a paragraph to spaces, and treat hard returns as paragraph breaks.
- **Tab-based alignment** — Authors sometimes use tabs to create visual columns without using a table. If the content is genuinely tabular, convert it to a pipe table. If it's just indentation, remove the tabs and let the content flow naturally.

## Quality Checklist

Verify these before the conversion is complete:

1. All styles mapped? Every Word style in the document has been converted to its Markdown equivalent.
2. Track changes resolved? No revision markup, insertions, or deletions remain.
3. Tables simplified? All tables render as valid pipe tables, with no nesting.
4. Images cataloged? Every image is either extracted and referenced or noted as needing manual extraction.
5. No XML artifacts in output? No stray XML tags, namespace prefixes, or Word-internal markup in the final Markdown.
