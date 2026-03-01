# Contributing to doc-to-markdown

## 👋 Who Can Contribute

Everyone. Seriously.

You don't need to be a developer. If you're a PM who found a weird edge case in a Google Doc conversion, that's a contribution. If you're a writer who knows a better way to phrase a conversion rule, that's a contribution. If you're a developer who wants to add EPUB support, that's definitely a contribution.

This project lives at the intersection of writing and code, so we need both kinds of expertise.

## 🤝 Ways to Contribute

- **Share conversion edge cases** — Found a document that doesn't convert cleanly? Open an issue with the source format and what went wrong. Bonus points if you include the source file and expected output.
- **Improve skills** — The conversion skills in `skills/` are living documents. If you know a better rule for handling nested tables or Confluence macros, propose the change.
- **Add format support** — Want to handle a new source format (EPUB, RTF, Notion exports)? Add a skill and/or a CLI handler.
- **Fix CLI bugs** — Something broken in the Python CLI? Fix it and submit a PR.
- **Add examples** — Real-world before/after conversion examples help everyone. Drop them in `examples/` with clear naming.

## 📝 Skill Format

Skills are Markdown files in `skills/` with YAML frontmatter. Here's the structure:

```markdown
---
name: Format Name Conversion
description: One-line description of what this skill covers
type: conversion-guide
---

## Purpose

Why this skill exists and when to use it.

## Common Artifacts

What this format typically produces that needs cleaning up.
List the specific patterns you'll encounter.

## Conversion Rules

Numbered, ordered rules for converting this format.
Later rules can assume earlier rules have been applied.

## Quality Checklist

- [ ] Specific checks for this format
- [ ] Things that commonly go wrong
- [ ] Edge cases to watch for

## Examples

### Before (source format)
Show what the input looks like.

### After (clean Markdown)
Show what the output should look like.
```

Every skill should be **self-contained**. An AI agent should be able to load it and immediately know what to do without reading anything else (except the baseline `conversion-rules.md`).

## 💻 CLI Contributions

If you're adding or modifying CLI code:

1. **Follow the existing converter pattern.** Look at any handler in `cli/` — new handlers should have the same structure (a function that takes input, returns a Markdown string).
2. **Add your handler to the dispatch in `cli/convert.py`.** The main script routes input to the right handler based on file extension or `--format` flag.
3. **Keep dependencies minimal.** This project intentionally has a tiny dependency footprint. If your change requires a new dependency, explain why in the PR and make sure there isn't a lighter alternative.
4. **Post-processing stays centralized.** Smart quote replacement, whitespace cleanup, and other universal fixes happen in `cli/convert.py`, not in individual handlers.

## 📋 Quality Checklist

Before submitting, make sure your contribution is:

- [ ] **Agent-ready** — An AI agent can load and use it without human interpretation
- [ ] **Self-contained** — Doesn't require external context to be useful (skills reference the baseline, but work independently)
- [ ] **Practical** — Solves a real conversion problem someone has actually encountered
- [ ] **Concrete** — Includes specific examples, not abstract descriptions
- [ ] **No fluff** — Every sentence earns its place. If it doesn't help someone convert a document, cut it

## 🔄 Process

1. **Fork** the repository.
2. **Create a branch** with a descriptive name (`skill/confluence-macros`, `cli/epub-handler`, `fix/nested-list-indent`).
3. **Make your changes** following the guidelines above.
4. **Submit a PR** with a clear description of what you changed and why. Include before/after examples where applicable.
5. **Review turnaround** — We aim to review all PRs within 7 days. If your PR needs changes, we'll explain what and why.

That's it. No CLA, no complex process. Just good work that helps people convert documents cleanly.
