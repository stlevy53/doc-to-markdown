"""Pyodide bridge — receives file bytes from JS, runs the CLI converters."""

import os
import sys

# cli/ modules are loaded into /home/pyodide/cli/ by app.js
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")

from cli.convert import detect_format, post_process


def convert_file(filename, file_bytes):
    """Convert an uploaded file to Markdown.

    Args:
        filename: Original filename (used for format detection).
        file_bytes: bytes object of the file content.

    Returns:
        Cleaned Markdown string.
    """
    fmt = detect_format(filename)
    if fmt is None:
        raise ValueError(
            f"Unsupported file type: {os.path.splitext(filename)[1]}\n"
            "Accepted formats: .docx, .pdf, .html"
        )

    # Write bytes to Pyodide virtual filesystem
    tmp_path = f"/tmp/{filename}"
    with open(tmp_path, "wb") as f:
        f.write(file_bytes)

    try:
        if fmt == "docx":
            import zipfile
            from cli.docx_converter import convert_docx
            try:
                markdown = convert_docx(tmp_path)
            except (zipfile.BadZipFile, Exception) as e:
                if "PackageNotFoundError" in type(e).__name__ or isinstance(e, zipfile.BadZipFile):
                    raise ValueError(
                        "This file appears to be password-protected and cannot be converted. "
                        "Remove the password in Word and try again."
                    )
                raise
        elif fmt == "pdf":
            raise ValueError(
                "PDF conversion is not available in the browser. "
                "Use the CLI: python -m cli input.pdf -o output.md"
            )
        elif fmt == "html":
            from cli.html_converter import convert_html
            markdown = convert_html(tmp_path)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        return post_process(markdown)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
