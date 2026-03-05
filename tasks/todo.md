# doc-to-markdown — Task List

## Completed

- [x] Initial repo scaffold (README, CLAUDE.md, AGENTS.md, CONTRIBUTING.md)
- [x] AI conversion skills (5 skill files)
- [x] Python CLI with format converters (docx, pdf, html)
- [x] Example files with expected outputs
- [x] Browser-based web UI (GitHub Pages, Pyodide, single-file conversion) — v0.2.0
- [x] Multi-file web UI — up to 5 simultaneous conversions, file nav chips, redesigned output pane — v0.3.0

## In Progress

- [ ] Test CLI with real documents (Word, PDF, Confluence export)
- [ ] Refine converters based on real-world edge cases

## Review — v0.3.0 Multi-file Web UI

**What shipped:**
- Drop zone accepts up to 5 files simultaneously (drag or browse)
- File nav chips appear below the drop zone; clicking switches the active reading pane
- Output pane header now holds: Start over (left), active filename (center), Copy + Download (right)
- Status bar updates dynamically as user navigates between files
- Unsupported file types render as error-state chips rather than blocking the session
- Subheader copy updated to reflect multi-file capability

**Verified manually:**
- Single file convert → chip + output render correctly
- Multi-file convert → chips and switching work
- 6th file attempt → warning shown, only 5 accepted
- Unsupported file → error chip, red state
- Download → correct filename per active file
- Start over → full session reset

## Backlog

- [ ] Add unit tests for each converter
- [ ] Add CI workflow (GitHub Actions)
- [ ] Create sample .docx and .pdf binary test files
- [ ] Add --verbose flag for debugging conversion issues
- [ ] Support batch conversion (directory of files)
- [ ] Add Confluence API direct fetch (optional, requires auth)
- [ ] Publish to PyPI as installable tool
