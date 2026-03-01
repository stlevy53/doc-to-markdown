#!/usr/bin/env python3
"""PDF to Markdown converter using pdfplumber."""

import re
from collections import Counter

import pdfplumber


def _detect_repeating_lines(pages_text):
    """Detect header/footer lines that repeat across pages."""
    if len(pages_text) < 3:
        return set()

    first_lines = Counter()
    last_lines = Counter()

    for lines in pages_text:
        if lines:
            first_lines[lines[0].strip()] += 1
        if lines:
            last_lines[lines[-1].strip()] += 1

    threshold = len(pages_text) / 2
    repeating = set()

    for line, count in first_lines.items():
        if count >= threshold and line:
            repeating.add(line)

    for line, count in last_lines.items():
        if count >= threshold and line:
            repeating.add(line)

    return repeating


def _is_page_number(line, page_num, total_pages):
    """Check if a line is just a page number."""
    stripped = line.strip()
    # Standalone digit(s), possibly matching page number
    if re.match(r"^\d{1,3}$", stripped):
        return True
    # "Page X" or "Page X of Y" patterns
    if re.match(r"^page\s+\d+", stripped, re.IGNORECASE):
        return True
    return False


def _get_font_segments(page, exclude_bboxes=None):
    """Extract text with font size information from a page.

    Args:
        page: pdfplumber page
        exclude_bboxes: list of (x0, top, x1, bottom) bounding boxes to skip

    Returns:
        List of (text, font_size, is_bold, top_position) tuples.
    """
    if not page.chars:
        return []

    chars = page.chars
    if exclude_bboxes:
        filtered = []
        for char in chars:
            skip = False
            cx, cy = float(char["x0"]), float(char["top"])
            for (bx0, btop, bx1, bbottom) in exclude_bboxes:
                if bx0 <= cx <= bx1 and btop <= cy <= bbottom:
                    skip = True
                    break
            if not skip:
                filtered.append(char)
        chars = filtered

    if not chars:
        return []

    segments = []
    current_text = []
    current_size = None
    current_bold = False
    current_top = None

    for char in chars:
        size = round(float(char.get("size", 12)), 1)
        fontname = char.get("fontname", "")
        bold = "bold" in fontname.lower() or "black" in fontname.lower()
        top = round(float(char.get("top", 0)), 1)

        if size != current_size or (bold != current_bold and char["text"].strip()):
            if current_text and current_size is not None:
                segments.append(("".join(current_text), current_size, current_bold, current_top))
            current_text = [char["text"]]
            current_size = size
            current_bold = bold
            current_top = top
        else:
            current_text.append(char["text"])

    if current_text and current_size is not None:
        segments.append(("".join(current_text), current_size, current_bold, current_top))

    return segments


def _build_heading_map(all_sizes_with_bold):
    """Map font sizes to heading levels.

    The most common font size is treated as body text.
    Larger sizes are mapped to headings H1-H6 in descending order.
    Sizes within 1.5pt of each other are merged into the same heading level.

    Returns:
        Dict mapping font_size -> heading_level (1-6).
        Also returns body_size for reference.
    """
    if not all_sizes_with_bold:
        return {}, 12.0

    size_counts = Counter()
    for size, _bold in all_sizes_with_bold:
        size_counts[size] += 1

    body_size = size_counts.most_common(1)[0][0]

    # Collect unique sizes larger than body, sorted descending
    heading_sizes = sorted(
        [s for s in size_counts if s > body_size],
        reverse=True,
    )

    if not heading_sizes:
        return {}, body_size

    # Merge sizes within 1.5pt into the same level
    MERGE_THRESHOLD = 1.5
    levels = []  # list of lists of sizes
    current_group = [heading_sizes[0]]

    for size in heading_sizes[1:]:
        if current_group[-1] - size <= MERGE_THRESHOLD:
            current_group.append(size)
        else:
            levels.append(current_group)
            current_group = [size]
    levels.append(current_group)

    heading_map = {}
    for i, group in enumerate(levels[:6]):
        for size in group:
            heading_map[size] = i + 1

    return heading_map, body_size


def _rejoin_hyphens(text):
    """Rejoin words that were hyphenated across line breaks."""
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def _convert_table_to_markdown(table):
    """Convert a pdfplumber table to Markdown pipe table."""
    if not table or not table[0]:
        return ""

    cleaned = []
    for row in table:
        cleaned_row = []
        for cell in row:
            val = str(cell).strip() if cell else ""
            val = val.replace("|", "\\|")
            val = val.replace("\n", " ")
            cleaned_row.append(val)
        cleaned.append(cleaned_row)

    if not cleaned:
        return ""

    max_cols = max(len(row) for row in cleaned)
    for row in cleaned:
        while len(row) < max_cols:
            row.append("")

    lines = []
    lines.append("| " + " | ".join(cleaned[0]) + " |")
    lines.append("| " + " | ".join("---" for _ in cleaned[0]) + " |")
    for row in cleaned[1:]:
        lines.append("| " + " | ".join(row[:max_cols]) + " |")

    return "\n".join(lines)


def _detect_list_item(text):
    """Detect if a line starts with a list marker and return (marker, content)."""
    # Bullet variants
    m = re.match(r"^[\u2022\u2023\u25E6\u2043\u2219\u25AA\u25CF\u25CB\u2013\u2014]\s*(.+)", text)
    if m:
        return "-", m.group(1)

    # Numbered list: "1." or "1)"
    m = re.match(r"^(\d+)[.)]\s+(.+)", text)
    if m:
        return "1.", m.group(2)

    # Letter list: "a." or "a)"
    m = re.match(r"^([a-z])[.)]\s+(.+)", text)
    if m:
        return "-", m.group(2)

    return None, text


def _process_page(page, heading_map, body_size, exclude_bboxes=None):
    """Process a page into structured Markdown lines.

    Uses font size for heading detection and vertical gaps for paragraph breaks.
    """
    segments = _get_font_segments(page, exclude_bboxes)
    if not segments:
        text = page.extract_text()
        return text.split("\n") if text else []

    # Group segments into lines based on Y position (top coordinate)
    # Lines on the same Y (within tolerance) belong together
    LINE_TOLERANCE = 2.0
    lines = []  # list of (heading_level_or_None, text, top_y)

    current_parts = []
    current_heading = None
    current_top = None

    for text, size, bold, top in segments:
        level = heading_map.get(size)

        sub_lines = text.split("\n")

        for i, sub_text in enumerate(sub_lines):
            if i > 0:
                # Newline in segment = flush current line
                combined = "".join(current_parts).strip()
                if combined:
                    lines.append((current_heading, combined, current_top or 0))
                current_parts = []
                current_heading = None
                current_top = top

            if not sub_text:
                continue

            # If Y position changed significantly, flush (new line)
            if current_top is not None and abs(top - current_top) > LINE_TOLERANCE and current_parts:
                combined = "".join(current_parts).strip()
                if combined:
                    lines.append((current_heading, combined, current_top))
                current_parts = []
                current_heading = None

            current_parts.append(sub_text)
            if level is not None:
                current_heading = level
            if current_top is None or abs(top - current_top) > LINE_TOLERANCE:
                current_top = top

    # Flush remaining
    if current_parts:
        combined = "".join(current_parts).strip()
        if combined:
            lines.append((current_heading, combined, current_top or 0))

    # Now convert lines to Markdown with paragraph detection
    # Use vertical gaps between lines to detect paragraph breaks
    PARAGRAPH_GAP = 5.0  # points of vertical space indicating a paragraph break

    output = []
    prev_top = None
    prev_was_heading = False

    for heading_level, text, top in lines:
        # Detect paragraph break from vertical gap
        if prev_top is not None:
            gap = top - prev_top
            if gap > PARAGRAPH_GAP or prev_was_heading:
                output.append("")

        if heading_level:
            prefix = "#" * heading_level + " "
            output.append(prefix + text)
            prev_was_heading = True
        else:
            # Check for list items
            marker, content = _detect_list_item(text)
            if marker:
                output.append(f"{marker} {content}")
            else:
                output.append(text)
            prev_was_heading = False

        prev_top = top

    return output


def convert_pdf(filepath):
    """Convert a PDF file to Markdown."""
    with pdfplumber.open(filepath) as pdf:
        total_pages = len(pdf.pages)

        # First pass: collect font sizes for heading detection
        all_sizes = []
        for page in pdf.pages:
            if page.chars:
                for char in page.chars:
                    size = round(float(char.get("size", 12)), 1)
                    fontname = char.get("fontname", "")
                    bold = "bold" in fontname.lower()
                    all_sizes.append((size, bold))

        heading_map, body_size = _build_heading_map(all_sizes)

        # Collect raw lines per page for header/footer detection
        pages_lines = []
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split("\n") if text else []
            pages_lines.append(lines)

        repeating = _detect_repeating_lines(pages_lines)

        # Second pass: process each page
        output = []

        for page_num, page in enumerate(pdf.pages):
            # Find tables and their bounding boxes
            table_bboxes = []
            table_mds = []

            for table in page.find_tables():
                table_bboxes.append(table.bbox)
                table_data = table.extract()
                if table_data:
                    table_md = _convert_table_to_markdown(table_data)
                    if table_md:
                        table_mds.append((table.bbox[1], table_md))  # (top_y, markdown)

            # Process non-table text with table regions excluded
            lines = _process_page(page, heading_map, body_size, exclude_bboxes=table_bboxes)

            # Filter headers/footers and page numbers
            filtered_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped in repeating:
                    continue
                if _is_page_number(stripped, page_num + 1, total_pages):
                    continue
                filtered_lines.append(line)

            # Interleave tables at approximate positions
            # For simplicity, insert tables where they appear vertically
            if table_mds:
                # Sort tables by vertical position
                table_mds.sort(key=lambda t: t[0])

                # Add non-table lines first, then tables
                # (Better heuristic: insert tables between text blocks)
                for line in filtered_lines:
                    output.append(line)

                for _top_y, table_md in table_mds:
                    output.append("")
                    output.append(table_md)
                    output.append("")
            else:
                for line in filtered_lines:
                    output.append(line)

            # Page break
            output.append("")

    # Join and post-process
    text = "\n".join(output)
    text = _rejoin_hyphens(text)

    # Strip trailing standalone page numbers (e.g., "...display.   2")
    text = re.sub(r"\s{2,}\d{1,3}\s*$", "", text, flags=re.MULTILINE)

    # Split inline bullet markers (●, ○, ■) into separate lines
    text = re.sub(r"\s*[●]\s*", "\n- ", text)
    text = re.sub(r"\s*[○]\s*", "\n  - ", text)
    text = re.sub(r"\s*[■]\s*", "\n    - ", text)

    return text
