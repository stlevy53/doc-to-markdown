#!/usr/bin/env python3
"""doc-to-markdown: Convert documents to clean Markdown."""

import sys
import os

# Add parent directory to path so cli package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.convert import main

if __name__ == "__main__":
    main()
