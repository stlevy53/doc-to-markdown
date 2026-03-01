#!/usr/bin/env python3
"""Word .docx to Markdown converter using python-docx."""

from docx import Document
from docx.oxml.ns import qn


# Namespace constants for XML parsing
HYPERLINK_TAG = qn("w:hyperlink")
RUN_TAG = qn("w:r")
TEXT_TAG = qn("w:t")
RPROPS_TAG = qn("w:rPr")
BOLD_TAG = qn("w:b")
ITALIC_TAG = qn("w:i")
BOLD_CS_TAG = qn("w:bCs")
ITALIC_CS_TAG = qn("w:iCs")
RELS_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


# Map docx paragraph style names to Markdown prefixes
HEADING_MAP = {
    "Title": "# ",
    "Subtitle": "## ",
    "Heading 1": "# ",
    "Heading 2": "## ",
    "Heading 3": "### ",
    "Heading 4": "#### ",
    "Heading 5": "##### ",
    "Heading 6": "###### ",
}

QUOTE_STYLES = {"Quote", "Intense Quote", "IntenseQuote"}

LIST_BULLET_STYLES = {
    "List Bullet", "List Bullet 2", "List Bullet 3",
    "List Paragraph",
}

LIST_NUMBER_STYLES = {
    "List Number", "List Number 2", "List Number 3",
}


def _run_is_bold(run):
    """Check if a run has bold formatting."""
    if run.bold:
        return True
    # Check XML directly for complex cases
    rpr = run._element.find(RPROPS_TAG)
    if rpr is not None:
        b = rpr.find(BOLD_TAG)
        if b is not None and b.get(qn("w:val"), "true") != "false":
            return True
    return False


def _run_is_italic(run):
    """Check if a run has italic formatting."""
    if run.italic:
        return True
    rpr = run._element.find(RPROPS_TAG)
    if rpr is not None:
        i = rpr.find(ITALIC_TAG)
        if i is not None and i.get(qn("w:val"), "true") != "false":
            return True
    return False


def _format_run_text(run):
    """Apply bold/italic formatting to a single run's text."""
    text = run.text
    if not text:
        return ""

    bold = _run_is_bold(run)
    italic = _run_is_italic(run)

    if bold and italic:
        return f"***{text}***"
    elif bold:
        return f"**{text}**"
    elif italic:
        return f"*{text}*"
    return text


def _extract_hyperlinks(paragraph):
    """Extract hyperlink information from paragraph XML.

    Returns a list of (text, url) tuples for all hyperlinks in the paragraph.
    Also builds a map from run elements to their hyperlink URLs.
    """
    rels = paragraph.part.rels
    hyperlink_map = {}  # Maps run element -> (text, url)

    for child in paragraph._element:
        if child.tag == HYPERLINK_TAG:
            # Get the relationship ID
            r_id = child.get(qn("r:id"))
            url = ""
            if r_id and r_id in rels:
                url = rels[r_id].target_ref

            # Collect text from all runs inside the hyperlink
            link_text_parts = []
            for run_elem in child.findall(RUN_TAG):
                for t in run_elem.findall(TEXT_TAG):
                    if t.text:
                        link_text_parts.append(t.text)
                hyperlink_map[id(run_elem)] = url

            link_text = "".join(link_text_parts)
            if link_text and url:
                hyperlink_map[f"full_{id(child)}"] = (link_text, url)

    return hyperlink_map


def _get_paragraph_text(paragraph):
    """Extract paragraph text with inline formatting and hyperlinks.

    Walks the paragraph's XML children to handle both regular runs
    and hyperlink elements in document order.
    """
    rels = paragraph.part.rels
    parts = []

    for child in paragraph._element:
        if child.tag == HYPERLINK_TAG:
            # Extract hyperlink
            r_id = child.get(qn("r:id"))
            url = ""
            if r_id and r_id in rels:
                url = rels[r_id].target_ref

            link_text_parts = []
            for run_elem in child.findall(RUN_TAG):
                for t in run_elem.findall(TEXT_TAG):
                    if t.text:
                        link_text_parts.append(t.text)

            link_text = "".join(link_text_parts)
            if link_text and url:
                parts.append(f"[{link_text}]({url})")
            elif link_text:
                parts.append(link_text)

        elif child.tag == RUN_TAG:
            # Regular run - apply formatting
            from docx.text.run import Run
            run = Run(child, paragraph)
            parts.append(_format_run_text(run))

    return "".join(parts)


def _get_list_level(paragraph):
    """Determine the nesting level of a list item (0-based)."""
    ppr = paragraph._element.find(qn("w:pPr"))
    if ppr is not None:
        numpr = ppr.find(qn("w:numPr"))
        if numpr is not None:
            ilvl = numpr.find(qn("w:ilvl"))
            if ilvl is not None:
                return int(ilvl.get(qn("w:val"), "0"))
    return 0


def _is_numbered_list(paragraph):
    """Check if a paragraph is part of a numbered list via numbering XML."""
    ppr = paragraph._element.find(qn("w:pPr"))
    if ppr is not None:
        numpr = ppr.find(qn("w:numPr"))
        if numpr is not None:
            return True
    return False


def _convert_table(table):
    """Convert a docx table to a Markdown pipe table."""
    rows = []
    for row in table.rows:
        cells = []
        for cell in row.cells:
            # Join paragraphs in cell with <br>
            cell_text = " ".join(
                p.text.strip() for p in cell.paragraphs if p.text.strip()
            )
            # Escape pipe characters in cell content
            cell_text = cell_text.replace("|", "\\|")
            cells.append(cell_text)
        rows.append(cells)

    if not rows:
        return ""

    lines = []

    # Header row
    header = rows[0]
    lines.append("| " + " | ".join(header) + " |")

    # Separator row
    lines.append("| " + " | ".join("---" for _ in header) + " |")

    # Data rows
    for row in rows[1:]:
        # Pad row to match header length
        while len(row) < len(header):
            row.append("")
        lines.append("| " + " | ".join(row[:len(header)]) + " |")

    return "\n".join(lines)


def convert_docx(filepath):
    """Convert a .docx file to Markdown.

    Args:
        filepath: Path to the .docx file.

    Returns:
        Markdown string.
    """
    doc = Document(filepath)
    output = []
    numbered_counters = {}  # Track numbering by list level

    for element in doc.element.body:
        # Handle tables
        if element.tag == qn("w:tbl"):
            from docx.table import Table
            table = Table(element, doc)
            table_md = _convert_table(table)
            if table_md:
                output.append("")
                output.append(table_md)
                output.append("")
            continue

        # Handle paragraphs
        if element.tag != qn("w:p"):
            continue

        from docx.text.paragraph import Paragraph
        paragraph = Paragraph(element, doc)

        style_name = paragraph.style.name if paragraph.style else "Normal"
        text = _get_paragraph_text(paragraph)

        # Headings
        if style_name in HEADING_MAP:
            prefix = HEADING_MAP[style_name]
            output.append("")
            output.append(f"{prefix}{text.strip()}")
            output.append("")
            numbered_counters.clear()
            continue

        # Block quotes
        if style_name in QUOTE_STYLES:
            for line in text.split("\n"):
                output.append(f"> {line.strip()}")
            output.append("")
            numbered_counters.clear()
            continue

        # Bullet lists
        if style_name in LIST_BULLET_STYLES and not _is_numbered_list(paragraph):
            level = _get_list_level(paragraph)
            indent = "  " * level
            output.append(f"{indent}- {text.strip()}")
            continue

        # Numbered lists (by style name or numbering XML)
        if style_name in LIST_NUMBER_STYLES or (
            style_name in LIST_BULLET_STYLES and _is_numbered_list(paragraph)
        ):
            level = _get_list_level(paragraph)
            indent = "  " * level

            # Track counter per level
            if level not in numbered_counters:
                numbered_counters[level] = 0
            numbered_counters[level] += 1

            # Reset deeper levels
            for k in list(numbered_counters):
                if k > level:
                    del numbered_counters[k]

            num = numbered_counters[level]
            output.append(f"{indent}{num}. {text.strip()}")
            continue

        # Normal paragraphs
        numbered_counters.clear()
        if text.strip():
            output.append("")
            output.append(text.strip())
            output.append("")
        else:
            output.append("")

    return "\n".join(output)
