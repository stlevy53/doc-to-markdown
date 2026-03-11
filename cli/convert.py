#!/usr/bin/env python3
"""Core conversion dispatcher."""

import argparse
import sys
import os
import re


def detect_format(filepath):
    """Detect document format from file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    format_map = {
        ".docx": "docx",
        ".pdf": "pdf",
        ".html": "html",
        ".htm": "html",
        ".md": "md",
    }
    return format_map.get(ext)


def post_process(markdown):
    """Clean up converted Markdown."""
    # Replace smart quotes
    replacements = {
        "\u2018": "'", "\u2019": "'",  # single curly quotes
        "\u201c": '"', "\u201d": '"',  # double curly quotes
        "\u2013": "--", "\u2014": "---",  # en/em dashes
        "\u00a0": " ",  # non-breaking space
        "\u200b": "",  # zero-width space
    }
    for old, new in replacements.items():
        markdown = markdown.replace(old, new)

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in markdown.split("\n")]
    markdown = "\n".join(lines)

    # Collapse 3+ consecutive newlines to 2
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    # Ensure file ends with single newline
    markdown = markdown.strip() + "\n"

    return markdown


def convert(filepath, fmt=None):
    """Convert a document to Markdown."""
    if fmt is None:
        fmt = detect_format(filepath)

    if fmt is None:
        raise ValueError(
            f"Cannot detect format for '{filepath}'. "
            "Use --format to specify: docx, pdf, html, md"
        )

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    if fmt == "docx":
        from cli.docx_converter import convert_docx
        return convert_docx(filepath)
    elif fmt == "pdf":
        from cli.pdf_converter import convert_pdf
        return convert_pdf(filepath)
    elif fmt == "html":
        from cli.html_converter import convert_html
        return convert_html(filepath)
    elif fmt == "md":
        from cli.md_converter import convert_md
        return convert_md(filepath)
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert documents to clean Markdown.",
        epilog="Supported formats: .docx, .pdf, .html/.htm",
    )
    parser.add_argument("input", help="Path to the input document")
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--format",
        choices=["docx", "pdf", "html", "md"],
        help="Force input format (auto-detected from extension if omitted)",
    )

    args = parser.parse_args()

    try:
        fmt = args.format or detect_format(args.input)
        result = convert(args.input, fmt=fmt)

        if fmt == "md":
            # Binary output: DOCX bytes
            if not args.output:
                print(
                    "Error: MD to DOCX conversion requires an output file path (-o output.docx).",
                    file=sys.stderr,
                )
                sys.exit(1)
            with open(args.output, "wb") as f:
                f.write(result)
            print(f"Converted: {args.input} -> {args.output}", file=sys.stderr)
        else:
            markdown = post_process(result)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(markdown)
                print(f"Converted: {args.input} -> {args.output}", file=sys.stderr)
            else:
                sys.stdout.write(markdown)

    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
