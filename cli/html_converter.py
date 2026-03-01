#!/usr/bin/env python3
"""Confluence HTML to Markdown converter using BeautifulSoup."""

import re

from bs4 import BeautifulSoup, NavigableString, Tag


# Confluence chrome/navigation selectors to strip
STRIP_SELECTORS = [
    "#breadcrumb-section",
    "#navigation",
    ".page-metadata",
    "#footer",
    "#header",
    ".aui-header",
    "#sidebar",
    ".ia-secondary-container",
    "#likes-and-labels-container",
    ".page-restrictions",
    "#content-metadata-page-restrictions",
    "script",
    "style",
    "nav",
    ".confluence-information-macro-icon",
]

# Confluence panel/macro class prefixes
PANEL_TYPES = {
    "confluence-information-macro-information": ("Info", "info"),
    "confluence-information-macro-note": ("Note", "note"),
    "confluence-information-macro-warning": ("Warning", "warning"),
    "confluence-information-macro-tip": ("Tip", "tip"),
    "confluence-information-macro": ("Note", "note"),
}


def _get_text(element):
    """Get direct text content from an element, ignoring children."""
    if isinstance(element, NavigableString):
        return str(element)
    return ""


def _convert_element(element, list_depth=0):
    """Recursively convert an HTML element to Markdown.

    Args:
        element: BeautifulSoup element.
        list_depth: Current nesting depth for lists.

    Returns:
        Markdown string for this element and its children.
    """
    if isinstance(element, NavigableString):
        text = str(element)
        # Collapse whitespace in inline text but preserve intentional newlines
        text = re.sub(r"[ \t]+", " ", text)
        return text

    if not isinstance(element, Tag):
        return ""

    tag = element.name

    # Skip elements that were marked for removal
    if element.get("data-strip"):
        return ""

    # Headings
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        content = _convert_children(element, list_depth).strip()
        return f"\n\n{'#' * level} {content}\n\n"

    # Paragraphs
    if tag == "p":
        content = _convert_children(element, list_depth).strip()
        if not content:
            return "\n"
        return f"\n\n{content}\n\n"

    # Line breaks
    if tag == "br":
        return "\n"

    # Horizontal rule
    if tag == "hr":
        return "\n\n---\n\n"

    # Bold / Strong
    if tag in ("strong", "b"):
        content = _convert_children(element, list_depth).strip()
        if not content:
            return ""
        return f"**{content}**"

    # Italic / Emphasis
    if tag in ("em", "i"):
        content = _convert_children(element, list_depth).strip()
        if not content:
            return ""
        return f"*{content}*"

    # Strikethrough
    if tag in ("del", "s", "strike"):
        content = _convert_children(element, list_depth).strip()
        if not content:
            return ""
        return f"~~{content}~~"

    # Inline code
    if tag == "code" and not _is_block_code(element):
        content = element.get_text()
        return f"`{content}`"

    # Links
    if tag == "a":
        content = _convert_children(element, list_depth).strip()
        href = element.get("href", "")
        if not content:
            return ""
        if href:
            return f"[{content}]({href})"
        return content

    # Images
    if tag == "img":
        alt = element.get("alt", "")
        src = element.get("src", "")
        if src:
            return f"![{alt}]({src})"
        return alt

    # Unordered lists
    if tag == "ul":
        items = []
        for li in element.find_all("li", recursive=False):
            item_content = _convert_list_item(li, list_depth, ordered=False)
            items.append(item_content)
        result = "\n".join(items)
        if list_depth == 0:
            return f"\n\n{result}\n\n"
        return f"\n{result}"

    # Ordered lists
    if tag == "ol":
        items = []
        for i, li in enumerate(element.find_all("li", recursive=False), 1):
            item_content = _convert_list_item(
                li, list_depth, ordered=True, number=i
            )
            items.append(item_content)
        result = "\n".join(items)
        if list_depth == 0:
            return f"\n\n{result}\n\n"
        return f"\n{result}"

    # Blockquotes
    if tag == "blockquote":
        content = _convert_children(element, list_depth).strip()
        lines = content.split("\n")
        quoted = "\n".join(f"> {line}" for line in lines)
        return f"\n\n{quoted}\n\n"

    # Preformatted / code blocks
    if tag == "pre":
        code_elem = element.find("code")
        if code_elem:
            code_text = code_elem.get_text()
            lang = _detect_code_language(code_elem)
        else:
            code_text = element.get_text()
            lang = _detect_code_language(element)
        lang_spec = lang if lang else ""
        return f"\n\n```{lang_spec}\n{code_text}\n```\n\n"

    # Tables
    if tag == "table":
        return _convert_table(element)

    # Confluence macros
    if tag == "div":
        return _handle_div(element, list_depth)

    # Confluence status macro
    if tag == "span":
        return _handle_span(element, list_depth)

    # Default: just process children
    return _convert_children(element, list_depth)


def _convert_children(element, list_depth=0):
    """Convert all children of an element."""
    parts = []
    for child in element.children:
        parts.append(_convert_element(child, list_depth))
    return "".join(parts)


def _convert_list_item(li, list_depth, ordered=False, number=1):
    """Convert a list item, handling nested lists."""
    indent = "  " * list_depth
    prefix = f"{number}." if ordered else "-"

    # Separate nested lists from inline content
    inline_parts = []
    nested_parts = []

    for child in li.children:
        if isinstance(child, Tag) and child.name in ("ul", "ol"):
            nested = _convert_element(child, list_depth + 1)
            nested_parts.append(nested)
        else:
            inline_parts.append(_convert_element(child, list_depth + 1))

    content = "".join(inline_parts).strip()
    result = f"{indent}{prefix} {content}"

    for nested in nested_parts:
        result += nested

    return result


def _is_block_code(element):
    """Check if a code element is a block-level code (inside pre)."""
    parent = element.parent
    return parent is not None and parent.name == "pre"


def _detect_code_language(element):
    """Detect programming language from element classes.

    Handles both standard class conventions and Confluence-specific
    patterns like 'brush: python' or 'language-javascript'.
    """
    classes = element.get("class", [])
    if isinstance(classes, str):
        classes = classes.split()

    for cls in classes:
        # Standard: language-python, lang-python
        for prefix in ("language-", "lang-"):
            if cls.startswith(prefix):
                return cls[len(prefix):]

        # Confluence: brush: python (stored as separate classes sometimes)
        if cls in (
            "python", "java", "javascript", "js", "sql", "bash", "sh",
            "xml", "html", "css", "json", "yaml", "yml", "ruby", "go",
            "rust", "cpp", "c", "csharp", "typescript", "ts", "php",
            "powershell", "groovy", "scala", "kotlin", "swift",
        ):
            return cls

    # Check data attributes used by Confluence
    lang = element.get("data-language", "")
    if lang:
        return lang

    # Check for Confluence's brush syntax in parent or self
    brush = element.get("data-syntaxhighlighter-params", "")
    if brush:
        match = re.search(r"brush:\s*(\w+)", brush)
        if match:
            return match.group(1)

    return ""


def _handle_div(element, list_depth):
    """Handle div elements, including Confluence macros/panels."""
    classes = element.get("class", [])
    if isinstance(classes, str):
        classes = classes.split()

    # Check for Confluence panel macros
    for cls in classes:
        for panel_cls, (label, _) in PANEL_TYPES.items():
            if panel_cls in cls:
                # Extract panel body content
                body = element.find(
                    class_="confluence-information-macro-body"
                )
                if body:
                    content = _convert_children(body, list_depth).strip()
                else:
                    content = _convert_children(element, list_depth).strip()

                lines = content.split("\n")
                quoted = "\n".join(f"> {line}" for line in lines)
                return f"\n\n> **{label}:**\n{quoted}\n\n"

    # Confluence expand macro
    if "expand-container" in classes:
        title_elem = element.find(class_="expand-control-text")
        body_elem = element.find(class_="expand-content")

        title = title_elem.get_text().strip() if title_elem else "Details"
        body = _convert_children(body_elem, list_depth).strip() if body_elem else ""

        return f"\n\n<details>\n<summary>{title}</summary>\n\n{body}\n\n</details>\n\n"

    # Confluence panel (styled box)
    if "panel" in classes or "panelContent" in classes:
        content = _convert_children(element, list_depth).strip()
        if content:
            lines = content.split("\n")
            quoted = "\n".join(f"> {line}" for line in lines)
            return f"\n\n{quoted}\n\n"

    # Confluence code macro
    if "code-macro" in " ".join(classes) or "codeContent" in classes:
        pre = element.find("pre")
        if pre:
            return _convert_element(pre, list_depth)

    # Default div handling
    return _convert_children(element, list_depth)


def _handle_span(element, list_depth):
    """Handle span elements, including Confluence status macros."""
    classes = element.get("class", [])
    if isinstance(classes, str):
        classes = classes.split()

    # Confluence status/lozenge macro
    if "status-macro" in classes or "aui-lozenge" in classes:
        text = element.get_text().strip()
        return f"**`{text}`**"

    # Confluence user mention
    if "confluence-userlink" in classes:
        text = element.get_text().strip()
        return f"@{text}"

    # Default span handling
    return _convert_children(element, list_depth)


def _convert_table(table):
    """Convert an HTML table to a Markdown pipe table."""
    rows = []

    # Process thead + tbody, or just tr elements
    all_rows = table.find_all("tr")

    for tr in all_rows:
        cells = []
        for td in tr.find_all(["td", "th"]):
            cell_content = _convert_children(td).strip()
            # Replace newlines with spaces for table cells
            cell_content = re.sub(r"\s*\n\s*", " ", cell_content)
            # Escape pipes
            cell_content = cell_content.replace("|", "\\|")
            cells.append(cell_content)
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    # Normalize column count
    max_cols = max(len(row) for row in rows)
    for row in rows:
        while len(row) < max_cols:
            row.append("")

    lines = []

    # Header row
    lines.append("| " + " | ".join(rows[0]) + " |")

    # Separator
    lines.append("| " + " | ".join("---" for _ in range(max_cols)) + " |")

    # Data rows
    for row in rows[1:]:
        lines.append("| " + " | ".join(row[:max_cols]) + " |")

    return "\n\n" + "\n".join(lines) + "\n\n"


def convert_html(filepath):
    """Convert a Confluence HTML file to Markdown.

    Args:
        filepath: Path to the HTML file.

    Returns:
        Markdown string.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    # Strip Confluence navigation/chrome elements
    for selector in STRIP_SELECTORS:
        if selector.startswith("#"):
            elem = soup.find(id=selector[1:])
            if elem:
                elem.decompose()
        elif selector.startswith("."):
            for elem in soup.find_all(class_=selector[1:]):
                elem.decompose()
        else:
            for elem in soup.find_all(selector):
                elem.decompose()

    # Try to find the main content area
    main_content = (
        soup.find(id="main-content")
        or soup.find(class_="wiki-content")
        or soup.find(class_="confluence-content")
        or soup.find(id="content")
        or soup.find("article")
        or soup.find("main")
        or soup.find("body")
        or soup
    )

    # Convert to Markdown
    markdown = _convert_element(main_content)

    # Clean up excessive whitespace
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = markdown.strip() + "\n"

    return markdown
