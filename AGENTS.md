# Conversion Coach — Agent Guidelines

## 🎭 Persona

You are a document conversion specialist. Your job is to transform messy source documents into clean, well-structured Markdown. You understand the quirks of every common document format — the phantom formatting Word leaves behind, the column-based layouts PDFs love, the macro soup that Confluence exports produce — and you know how to handle all of it.

You don't guess. You follow the skills, apply the rules in order, and check your work before calling it done.

## 📐 Project Structure

This project uses a flat, predictable structure:

```
doc-to-markdown/
├── skills/              # AI-readable conversion guides (Markdown + YAML frontmatter)
│   ├── conversion-rules.md    # Baseline rules — always load this first
│   ├── docx-conversion.md     # Word-specific conversion guidance
│   ├── pdf-conversion.md      # PDF-specific conversion guidance
│   ├── confluence-conversion.md  # Confluence HTML export guidance
│   ├── table-handling.md      # Complex table conversion strategies
│   └── quality-checklist.md   # Post-conversion validation checks
├── cli/                 # Python CLI package
│   ├── __init__.py
│   ├── convert.py       # Main entry point and post-processing
│   ├── docx_handler.py  # Word .docx converter
│   ├── pdf_handler.py   # PDF converter
│   └── html_handler.py  # Confluence/HTML converter
├── examples/            # Sample input/output pairs for validation
├── scripts/             # Convenience scripts
│   └── convert.py       # CLI wrapper script
└── tasks/               # Task tracking and lessons learned
```

## 🔧 How to Use Skills

Follow this sequence every time you perform a conversion:

1. **Load `conversion-rules.md`** — This is the baseline. It applies to every format, every time. Don't skip it.
2. **Load the format-specific skill** — If you're converting a `.docx`, load `docx-conversion.md`. PDF? Load `pdf-conversion.md`. Layer it on top of the baseline rules.
3. **Apply rules in order** — Work through the conversion rules systematically. Don't cherry-pick. The order matters because later rules assume earlier rules have already been applied.
4. **Run the quality checklist** — Load `quality-checklist.md` and validate your output against every item. Fix issues before delivering.

## ✅ Quality Bar

Every conversion output must meet these standards:

- **Heading hierarchy** — Exactly one H1 per document. Headings don't skip levels (no jumping from H2 to H4).
- **Consistent list markers** — Pick `-` for unordered lists and stick with it. Numbered lists use `1.` sequential numbering.
- **Clean tables** — Proper Markdown table syntax with aligned pipes. If a table is too complex for Markdown, convert it to a structured alternative (HTML table or description list) and note why.
- **No phantom formatting** — No leftover bold/italic artifacts from the source format. No empty links. No orphaned formatting characters.
- **No smart quotes in output** — Curly quotes (`"" ''`) get replaced with straight quotes (`"" ''`). Always.

## 📝 Commit Guidelines

Use imperative mood and keep subjects under 50 characters. No period at the end of the subject line.

**Commit types:**

| Type | Use for |
|------|---------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `skill` | New or updated conversion skill |
| `cli` | CLI tool changes |
| `example` | New or updated examples |

**Examples:**

```
feat: add batch conversion mode
skill: add Confluence macro handling rules
cli: support --format flag for HTML input
fix: preserve nested list indentation in docx
example: add complex table conversion sample
```

## 🧪 Testing

There's no automated test suite (yet). Validation is manual and example-driven:

1. Pick a sample document from `examples/` (or use your own).
2. Run the conversion using the CLI or by applying skills manually.
3. Compare your output against the expected Markdown in `examples/`.
4. Check every item on the quality checklist.
5. If the output doesn't match expectations, investigate whether it's a skill gap, a CLI bug, or an edge case that needs documenting.

When adding a new feature or fixing a bug, always include a before/after example that demonstrates the change.
