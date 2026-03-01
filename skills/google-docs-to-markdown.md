---
name: "Google Docs to Markdown"
description: "Handle Google Docs artifacts when converting to Markdown"
type: conversion-guide
---

# Google Docs to Markdown

## Purpose

Google Docs introduces specific artifacts when exported that don't exist in the original document's visual appearance. Things like smart quotes, phantom formatting spans, and comment anchors sneak into the export and need to be cleaned up. This skill handles all of those quirks.

Prerequisite: export the Google Doc as `.docx` first. This is the cleanest export path and doesn't require any API access. Go to File > Download > Microsoft Word (.docx).

## Common Artifacts

These are the usual suspects you'll encounter in Google Docs exports:

- **Smart quotes and curly apostrophes** — Google Docs loves its typographic quotes. Replace all `"` `"` with `"` and `'` `'` with `'`. This includes apostrophes in contractions like "don't" and "it's."
- **Phantom bold/italic** — Spans that carry bold or italic formatting but have no visible effect on the text. These show up as empty `<b>` or `<i>` tags or as style attributes on spans that contain only whitespace. Strip them entirely.
- **Comment anchors** — Invisible bookmark spans left behind by Google Docs comments. Even after comments are resolved, the anchor markup can persist. Strip all comment anchor elements.
- **Suggested edits markup** — If the document had suggestions that weren't fully accepted or rejected, the tracking markup will be in the export. Accept or reject all suggestions before exporting, then remove any remaining tracking artifacts.
- **Extra line breaks in table cells** — Google Docs frequently adds spurious line breaks inside table cells during export. Collapse these to single spaces unless the line breaks are intentional (like a list inside a cell).
- **Non-standard list numbering** — Google Docs sometimes exports numbered lists with restart numbering or custom start values embedded in styles. Normalize these to standard `1.` Markdown list items.

## Conversion Rules

Follow this process for a clean conversion:

- Export the Google Doc as `.docx`, then apply the docx-to-markdown conversion skill. The `.docx` intermediate format is more structured than HTML export and easier to work with.
- Strip Google-specific metadata. This includes document properties, revision history metadata, and any Google-internal identifiers that made it into the export.
- Watch for heading styles that are actually just bold + large text. Google Docs users frequently format text as bold and increase the font size instead of using actual heading styles. Detect these by their visual properties and convert them to proper Markdown headings at the appropriate level.
- Handle the Google Docs Table of Contents. If the document has an auto-generated TOC, remove it from the Markdown output. If a TOC is needed, regenerate it from the actual heading structure rather than carrying over the exported version (which will have stale page numbers and broken links).

## Quality Checklist

Before calling the conversion complete, verify:

1. No comment anchor remnants? Search for bookmark or anchor spans — they should all be gone.
2. Smart quotes replaced? Every curly quote and apostrophe should be straight.
3. Phantom formatting removed? No empty bold, italic, or styled spans in the output.
4. TOC stripped or regenerated? The old TOC is gone, and if needed, a fresh one is built from headings.
5. Images noted for manual extraction? Google Docs images don't always export cleanly — flag any that need manual handling.
