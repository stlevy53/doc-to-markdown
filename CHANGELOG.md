# Changelog

All notable changes to this project will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [0.4.1] — 2026-03-06

### Fixed
- Pyodide script load failure now shows a clear error instead of hanging silently
- Offline users see an immediate, actionable message on page load rather than a failed script error
- Files over 50MB now show a size error with a CLI fallback suggestion instead of hanging the browser
- Empty files (0 bytes) are caught before reaching the Python converter
- Password-protected DOCX files now return a user-friendly error instead of a raw Python traceback
- Download button on error-state files now shows feedback instead of silently doing nothing
- Copy button on error-state files now shows feedback instead of copying the error text
- Successful conversions producing empty output now warn the user instead of showing a blank textarea
- Raw Python tracebacks no longer leak through to the status bar or output pane

---

## [0.4.0] — 2026-03-05

### Added
- Side-by-side source preview pane in the web UI — see the original document next to the converted Markdown
- DOCX files render via docx-preview (lazy-loaded from CDN on first use; JSZip loaded as dependency)
- HTML/HTM files render in a sandboxed iframe (scripts blocked)
- "Preview not available" placeholder for unsupported file types (PDF, etc.)
- `docs/serve.py` — local dev server with COOP/COEP headers required for Pyodide SharedArrayBuffer support

### Changed
- Output area expands to 1200px max-width when split view is active; collapses back on "Start over"
- Both panes scroll to top on each file load or chip switch
- Panes stack vertically on mobile (source on top, Markdown below)

---

## [0.3.0] — 2026-03-04

### Added
- Multi-file support in the web UI — drop up to 5 files at once
- File nav chips below the drop zone; clicking a chip switches the active reading pane
- Output pane header with contextual controls: Start over (left), active filename (center), Copy + Download .md (right)
- Status bar updates dynamically when navigating between converted files
- Unsupported file types render as error-state chips rather than blocking the session

### Changed
- Drop zone text updated to reflect multi-file capability
- Subheader copy updated: "Drop up to 5 documents, and get clean Markdown files."
- Copy and Download buttons moved from a standalone actions row into the output pane header
- Reset action renamed "Start over" and moved into the output header for persistent visibility

---

## [0.2.0] — 2026-03-02

### Added
- Browser-based web UI hosted on GitHub Pages
- Client-side conversion via Pyodide (Python in the browser) — files never leave the user's machine
- Supports `.docx` and `.html`/`.htm` in the browser; PDF remains CLI-only
- Copy to Clipboard and Download .md actions

---

## [0.1.0] — 2026-02-28

### Added
- Initial repo scaffold: README, CLAUDE.md, AGENTS.md, CONTRIBUTING.md, LICENSE
- AI conversion skills: baseline rules, docx, pdf, confluence, google docs formats
- Python CLI with converters for `.docx`, `.pdf`, and `.html`
- Example files with expected Markdown output
