# Changelog

## 0.1.0

- Core dumper: `discover_files` and `dump_context` functions for
  directory-tree walking and markdown generation.
- Filtering: ignore patterns (glob-style), file-size limits, and
  binary/junk-directory detection.
- CLI entry point via `python -m code_to_markdown_context_dumper`
  with `argparse`-based argument handling.
- Zero dependencies — pure Python standard library (≥ 3.10).
