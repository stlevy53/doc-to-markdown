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
    prev_x1 = None

    X_GAP_THRESHOLD = 12  # pts: large horizontal gap means separate fields
    X_WRAP_THRESHOLD = -50  # pts: text wrapped to far left

    for char in chars:
        size = round(float(char.get("size", 12)), 1)
        fontname = char.get("fontname", "")
        bold = "bold" in fontname.lower() or "black" in fontname.lower()
        top = round(float(char.get("top", 0)), 1)
        x0 = float(char.get("x0", 0))
        x1 = float(char.get("x1", 0))

        # Detect large horizontal gap (separate fields) or wrap to left
        # Only check gaps between non-whitespace chars to avoid stray spaces
        x_break = False
        if prev_x1 is not None and current_text and char["text"].strip():
            x_diff = x0 - prev_x1
            if x_diff > X_GAP_THRESHOLD or x_diff < X_WRAP_THRESHOLD:
                x_break = True

        if x_break or size != current_size or (bold != current_bold and char["text"].strip()):
            if current_text and current_size is not None:
                text_so_far = "".join(current_text)
                # If x-gap break on same Y line, append newline to force line separation
                if x_break and current_top is not None and abs(top - current_top) < 3.0:
                    text_so_far += "\n"
                segments.append((text_so_far, current_size, current_bold, current_top))
            current_text = [char["text"]]
            current_size = size
            current_bold = bold
            current_top = top
        else:
            current_text.append(char["text"])

        # Only track x1 for non-whitespace chars to avoid stray spaces
        # creating false gaps
        if char["text"].strip():
            prev_x1 = x1

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
        if text:
            return [(line, 0.0) for line in text.split("\n")]
        return []

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

    output = []  # list of (line_text, top_y)
    prev_top = None
    prev_was_heading = False

    for heading_level, text, top in lines:
        # Detect paragraph break from vertical gap
        if prev_top is not None:
            gap = top - prev_top
            if gap > PARAGRAPH_GAP or prev_was_heading:
                output.append(("", top))

        if heading_level:
            prefix = "#" * heading_level + " "
            output.append((prefix + text, top))
            prev_was_heading = True
        else:
            # Check for list items
            marker, content = _detect_list_item(text)
            if marker:
                output.append((f"{marker} {content}", top))
            else:
                output.append((text, top))
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

        # Second pass: collect all page data
        page_data = []  # list of (page_num, table_bboxes, detected_tables, line_tuples)

        for page_num, page in enumerate(pdf.pages):
            table_bboxes = []
            detected_tables = []  # (col_count, table_data, has_header)

            for table in page.find_tables():
                table_bboxes.append(table.bbox)
                table_data = table.extract()
                if table_data and table_data[0]:
                    # Check if first row looks like a header (non-empty text, not data-like)
                    first_row = table_data[0]
                    has_header = any(
                        cell and not re.match(r"^\d", str(cell).strip())
                        and len(str(cell).strip()) < 40
                        for cell in first_row
                    )
                    detected_tables.append((len(table_data[0]), table_data, has_header))

            line_tuples = _process_page(page, heading_map, body_size, exclude_bboxes=table_bboxes)
            page_data.append((page_num, table_bboxes, detected_tables, line_tuples))

        # Cross-page table merging: merge continuation tables into previous
        # A continuation table is at the top of a page with the same column count
        # as the last table on the previous page, and has no real header row
        all_page_tables = []  # list of (page_num, table_index, col_count, data, is_continuation)
        for page_num, _bboxes, detected_tables, _lines in page_data:
            for t_idx, (col_count, data, has_header) in enumerate(detected_tables):
                all_page_tables.append((page_num, t_idx, col_count, data, has_header))

        # Mark continuation tables and merge them
        def _looks_like_header_row(row):
            """Check if row looks like a table header (short labels, no digits)."""
            return all(
                cell and len(str(cell).strip()) < 30
                and not re.search(r"\d", str(cell))
                for cell in row if cell and str(cell).strip()
            )

        merged_away = set()  # (page_num, t_idx) of tables merged into a previous one
        for i in range(1, len(all_page_tables)):
            p_num, t_idx, cols, data, has_header = all_page_tables[i]
            prev_p, prev_t, prev_cols, prev_data, _ = all_page_tables[i - 1]
            # Continuation: first table on new page, same col count
            # Don't merge if the new table has a distinct header row
            is_different_table = (
                data[0] != prev_data[0]
                and _looks_like_header_row(data[0])
            )
            if (p_num == prev_p + 1 and t_idx == 0 and cols == prev_cols
                    and not is_different_table):
                # Merge into previous: skip header row if it duplicates column names
                if has_header and data[0] == prev_data[0]:
                    merge_rows = data[1:]
                else:
                    merge_rows = data
                # Update previous table's data in-place
                all_page_tables[i - 1] = (prev_p, prev_t, prev_cols, prev_data + merge_rows, True)
                merged_away.add((p_num, t_idx))

        # Build lookup of merged table data by (page_num, t_idx)
        merged_table_data = {}
        for p_num, t_idx, cols, data, _ in all_page_tables:
            if (p_num, t_idx) not in merged_away:
                merged_table_data[(p_num, t_idx)] = data

        # Third pass: build output
        output = []

        for page_num, table_bboxes, detected_tables, line_tuples in page_data:
            # Filter headers/footers and page numbers
            filtered_lines = []
            for line_text, top_y in line_tuples:
                stripped = line_text.strip()
                if stripped in repeating:
                    continue
                if _is_page_number(stripped, page_num + 1, total_pages):
                    continue
                filtered_lines.append((line_text, top_y))

            # Build tables for this page
            page_tables = []
            for t_idx, (col_count, _orig_data, _has_header) in enumerate(detected_tables):
                if (page_num, t_idx) in merged_away:
                    continue
                final_data = merged_table_data.get((page_num, t_idx), _orig_data)
                table_md = _convert_table_to_markdown(final_data)
                if table_md:
                    top_y = table_bboxes[t_idx][1] if t_idx < len(table_bboxes) else 0
                    page_tables.append((top_y, table_md))

            # Build unified list sorted by Y position
            unified = []
            for line_text, top_y in filtered_lines:
                unified.append((top_y, line_text))
            for top_y, table_md in page_tables:
                unified.append((top_y, "\n" + table_md + "\n"))

            unified.sort(key=lambda item: item[0])

            for _y, content in unified:
                output.append(content)

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
