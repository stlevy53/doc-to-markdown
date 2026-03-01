---
name: "Confluence to Markdown"
description: "Convert Confluence HTML exports to clean Markdown handling macros and wiki-specific elements"
type: conversion-guide
---

# Confluence to Markdown

## Purpose

Confluence pages export as HTML, but it's not ordinary HTML. It's packed with custom macros, wiki-specific elements, and Atlassian-flavored markup that standard HTML-to-Markdown tools won't handle correctly. This skill translates all of those Confluence-specific constructs into clean Markdown equivalents.

## Export Method

Getting the content out of Confluence is the first step:

- Use **Confluence Space Export** (HTML format) for bulk conversion. This gives you an entire space as a set of HTML files with a consistent structure.
- **Individual page export** also works for one-off conversions. Use the page menu's export option.
- **Confluence Cloud vs Server** may differ slightly in their export format. Cloud exports tend to have more modern HTML and different macro representations. Server exports are often more verbose with older-style markup. The guidance here covers both, but note where differences may appear.

## Macro Handling

Macros are the biggest Confluence-specific challenge. Here's how to convert each common type:

- **Info/Note/Warning/Tip panels** — Convert to blockquotes with a bold label. An Info panel becomes `> **Info:**` followed by the panel content. Warning becomes `> **Warning:**`, and so on. Preserve the panel type so the reader knows the intent.
- **Code blocks** (with language specified) — Convert to fenced code blocks with the language identifier. A Confluence code macro with `language="python"` becomes a code block starting with ` ```python `.
- **Expand macros** — Use HTML `<details><summary>` elements. The expand title becomes the `<summary>` content, and the expand body goes inside the `<details>` block. This is one of the few places where inline HTML in Markdown is the right call.
- **Table of Contents macro** — Remove it. If a TOC is needed in the Markdown output, regenerate it from the actual headings rather than carrying over the Confluence-generated version.
- **Jira Issue macro** — Convert to a standard Markdown link: `[PROJ-123](jira-url)`. Preserve the issue key as the link text and the full Jira URL as the target.
- **Status macro** — Convert to bold inline code: **`STATUS`**. For example, a green "DONE" status becomes `**\`DONE\`**`.
- **Excerpt macro** — Keep the content inside the excerpt, but remove the excerpt wrapper markup. The content is what matters, not the Confluence metadata around it.

## Element Mapping

Standard HTML elements from Confluence map to Markdown as follows:

| Confluence HTML | Markdown |
|---|---|
| `<h1>` to `<h6>` | `#` to `######` |
| `<table>` | Pipe tables |
| `<ul>` / `<ol>` | `-` unordered / `1.` ordered lists |
| `<a href="...">` | `[text](url)` |
| `<img>` | `![alt](src)` |
| `<pre>` | Fenced code blocks |
| `<blockquote>` | `>` blockquotes |
| Emoticons | Remove or replace with text equivalent |

## Jira Links

Jira integration is deeply embedded in most Confluence installations. Handle these links carefully:

- Preserve Jira issue links as clickable Markdown links. The issue key should be the visible text.
- Convert Jira macro format to standard links. Confluence stores Jira references as macros with metadata — collapse all of that down to a simple `[PROJ-123](https://jira.example.com/browse/PROJ-123)` link.
- Handle both Cloud and Server URL formats. Cloud uses `https://yourorg.atlassian.net/browse/PROJ-123`, while Server uses `https://jira.yourcompany.com/browse/PROJ-123`. Preserve whichever format the source uses.

## Common Issues

These problems come up regularly with Confluence exports:

- **Nested macros** — Process inner macros first, then outer macros. A code block inside an expand macro should be converted to a fenced code block first, then the expand wrapper should be converted to `<details>`. Working inside-out prevents markup collisions.
- **User mentions** (`@user`) — Convert to plain text. Confluence stores mentions as links to user profiles, which won't resolve outside the wiki. Replace `@John Smith` with just "John Smith" or keep the `@` prefix if the context makes sense.
- **Page links** — Internal Confluence page links won't work outside the wiki. Convert them to relative links if you're converting an entire space and maintaining a file structure. For standalone conversions, replace the link with the page title in plain text and note it as an internal reference.
- **Attachments** — Confluence pages often reference attached files (PDFs, images, spreadsheets). Note these for manual handling since the attachments need to be downloaded separately from the space export. Flag each attachment reference so nothing gets lost.

## Quality Checklist

Verify these before the conversion is complete:

1. All macros converted? No raw Confluence macro markup in the output.
2. Panel types preserved as blockquotes? Info, Warning, Note, and Tip panels all have their labels.
3. Code blocks have language hints? Where the Confluence code macro specified a language, the fenced block includes it.
4. Jira links intact? Issue references are clickable links with the correct URL format.
5. Internal links flagged? Page-to-page links that won't resolve externally are noted or converted.
6. Emoticons removed? No Confluence emoticon markup or broken image references in the output.
