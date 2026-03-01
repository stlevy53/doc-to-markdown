#!/usr/bin/env python3
"""PDF to Markdown converter using pdfplumber."""

import re
from collections import Counter

import pdfplumber


def _detect_repeating_lines(pages_text):
    """Detect header/footer lines that repeat across pages.

    A line is considered a header if it appears as the first line
    on more than half the pages. Same logic for footers with the last line.

    Returns:
        set of line strings to strip.
    """
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


def _get_font_sizes(page):
    """Extract text with font size information from a page.

    Returns:
        List of (text, font_size) tuples for each character group.
    """
    segments = []
    if not page.chars:
        return segments

    current_text = []
    current_size = None

    for char in page.chars:
        size = round(char.get("size", 12), 1)
        if size != current_size:
            if current_text and current_size is not None:
                segments.append(("".join(current_text), current_size))
            current_text = [char["text"]]
            current_size = size
        else:
            current_text.append(char["text"])

    if current_text and current_size is not None:
        segments.append(("".join(current_text), current_size))

    return segments


def _build_heading_map(all_font_sizes):
    """Map font sizes to heading levels.

    The most common font size is treated as body text.
    Larger sizes are mapped to headings H1-H6 in descending order.

    Returns:
        Dict mapping font_size -> heading_level (1-6), or empty if no headings.
    """
    if not all_font_sizes:
        return {}

    size_counts = Counter()
    for size in all_font_sizes:
        size_counts[size] += 1

    # Most common size is body text
    body_size = size_counts.most_common(1)[0][0]

    # Sizes larger than body are potential headings
    heading_sizes = sorted(
        [s for s in size_counts if s > body_size],
        reverse=True,
    )

    heading_map = {}
    for i, size in enumerate(heading_sizes[:6]):
        heading_map[size] = i + 1  # H1 for largest, H2 for next, etc.

    return heading_map


def _rejoin_hyphens(text):
    """Rejoin words that were hyphenated across line breaks."""
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def _convert_table_to_markdown(table):
    """Convert a pdfplumber table to Markdown pipe table."""
    if not table or not table[0]:
        return ""

    # Clean cell values
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

    # Normalize column count
    max_cols = max(len(row) for row in cleaned)
    for row in cleaned:
        while len(row) < max_cols:
            row.append("")

    lines = []

    # Header
    lines.append("| " + " | ".join(cleaned[0]) + " |")

    # Separator
    lines.append("| " + " | ".join("---" for _ in cleaned[0]) + " |")

    # Data rows
    for row in cleaned[1:]:
        lines.append("| " + " | ".join(row[:max_cols]) + " |")

    return "\n".join(lines)


def _process_page_with_fonts(page, heading_map):
    """Process a page using font size information for heading detection.

    Returns:
        List of text lines with Markdown heading prefixes applied.
    """
    segments = _get_font_sizes(page)
    if not segments:
        text = page.extract_text()
        return text.split("\n") if text else []

    output_lines = []
    current_line_parts = []
    current_heading_level = None

    for text, size in segments:
        level = heading_map.get(size)

        # Split segment text by newlines
        sub_lines = text.split("\n")

        for i, sub_line in enumerate(sub_lines):
            if i > 0:
                # Newline encountered - flush current line
                line = "".join(current_line_parts).strip()
                if line:
                    if current_heading_level:
                        prefix = "#" * current_heading_level + " "
                        output_lines.append(prefix + line)
                    else:
                        output_lines.append(line)
                current_line_parts = []
                current_heading_level = None

            if sub_line:
                current_line_parts.append(sub_line)
                if level is not None:
                    current_heading_level = level

    # Flush remaining
    line = "".join(current_line_parts).strip()
    if line:
        if current_heading_level:
            prefix = "#" * current_heading_level + " "
            output_lines.append(prefix + line)
        else:
            output_lines.append(line)

    return output_lines


def convert_pdf(filepath):
    """Convert a PDF file to Markdown.

    Args:
        filepath: Path to the PDF file.

    Returns:
        Markdown string.
    """
    with pdfplumber.open(filepath) as pdf:
        # First pass: collect all font sizes for heading detection
        all_font_sizes = []
        for page in pdf.pages:
            if page.chars:
                for char in page.chars:
                    all_font_sizes.append(round(char.get("size", 12), 1))

        heading_map = _build_heading_map(all_font_sizes)

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
            # Extract tables first
            tables = page.extract_tables()
            table_regions = []

            if tables:
                for table_data in tables:
                    table_md = _convert_table_to_markdown(table_data)
                    if table_md:
                        output.append("")
                        output.append(table_md)
                        output.append("")

                # Get table bounding boxes to skip table text in main extraction
                for table in page.find_tables():
                    table_regions.append(table.bbox)

            # Extract text, optionally excluding table regions
            if table_regions:
                # Crop page to exclude table areas
                crop_page = page
                for bbox in table_regions:
                    # Filter chars outside table regions
                    pass
                # Fall back to font-based processing for non-table text
                lines = _process_page_with_fonts(page, heading_map)
            else:
                lines = _process_page_with_fonts(page, heading_map)

            # Filter headers/footers and add lines
            for line in lines:
                stripped = line.strip()
                if stripped in repeating:
                    continue
                if stripped:
                    output.append(line)
                else:
                    output.append("")

            # Page separator
            output.append("")

    # Join and post-process
    text = "\n".join(output)

    # Rejoin hyphenated words
    text = _rejoin_hyphens(text)

    return text
