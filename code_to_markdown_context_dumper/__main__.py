"""CLI entry point for code-to-markdown-context-dumper.

Usage:
    python -m code_to_markdown_context_dumper --root <dir> --output <file>
"""

import argparse
import os
import sys

from code_to_markdown_context_dumper.core import (
    discover_filtered_files,
    format_markdown_context,
)


def main() -> None:
    """Parse arguments, discover files, generate markdown, and write output."""
    parser = argparse.ArgumentParser(
        description="Convert a source code tree into structured markdown for LLM context."
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Root directory to scan.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output markdown file path.",
    )
    parser.add_argument(
        "--ignore-patterns",
        nargs="*",
        default=None,
        help="Glob-style ignore patterns (e.g. '*.log' 'secret/*').",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=None,
        help="Maximum file size in bytes. Larger files are excluded.",
    )
    parser.add_argument(
        "--no-ignore-binary",
        action="store_true",
        help="Include binary files in the output.",
    )

    args = parser.parse_args()

    root_dir = os.path.abspath(args.root)
    output_path = os.path.abspath(args.output)

    if not os.path.isdir(root_dir):
        sys.exit(f"Error: {args.root} is not a directory or does not exist.")

    files = discover_filtered_files(
        root_dir=root_dir,
        ignore_patterns=args.ignore_patterns,
        max_size=args.max_size,
        ignore_binary=not args.no_ignore_binary,
    )

    file_contents: list[tuple[str, str]] = []
    for rel_path in files:
        filepath = os.path.join(root_dir, rel_path)
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            continue
        file_contents.append((rel_path, content))

    markdown = format_markdown_context(file_contents)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)


if __name__ == "__main__":
    main()
