# Code-to-Markdown Context Dumper

**Zero-dependency** Python library that walks a directory tree, discovers
text files, filters them by ignore patterns and size limits, and produces a
single markdown document — ready to paste into an LLM prompt as context.

Think of it as a minimal, library-form equivalent of `tree | grep` +
`cat` + fenced code blocks, without any external dependencies or a CLI.

## Features

- **File discovery** — walks any directory tree, skips binaries and junk
  dirs (`.git`, `node_modules`, `__pycache__`, `venv`, dot-directories, …).
- **Markdown generation** — produces a flat markdown document with a `###`
  heading per file and a fenced code block with language annotation.
- **Ignore patterns** — exclude files by glob-style patterns (`*.log`,
  `build/*`, …).
- **File-size limits** — cap files at N bytes to keep context windows under
  control.
- **Zero dependencies** — pure Python standard library. Works on ≥ 3.10.

## Installation

```bash
pip install code-to-markdown-context-dumper
```

Or add it to your project with `pip install -e .` from the cloned
repository. Because the library has zero dependencies, there is nothing
to resolve — it will install instantly.

## Usage

### Basic — discover and dump

```python
from code_to_markdown_context_dumper import discover_files, dump_context

# Walk the current directory and discover every text file.
files = discover_files(".")

# Turn them into a single markdown document.
markdown = dump_context(files)

print(markdown)
# ### setup.py
#
# ``` python
# from setuptools import setup
# setup(...)
# ```
#
# ### src/main.py
# ...
```

The result is a single markdown string you can paste directly into an
LLM chat, include in a system prompt, or route to a file for later use.

### Advanced — filtering by patterns and size

```python
from code_to_markdown_context_dumper import discover_files, filter_files, dump_context

# Discover all files first.
files = discover_files(".")

# Exclude log files and anything larger than 50 KB.
filtered = filter_files(
    files,
    root_dir=".",
    exclude_patterns=["*.log", "tmp/*"],
    max_size_bytes=50 * 1024,
)

context = dump_context(filtered)
```

### Composing the building blocks

Every function is exposed and independently usable:

```python
from code_to_markdown_context_dumper.core import (
    discover_files,
    format_file_block,
    dump_context,
    filter_files,
    matching_ignore_patterns,
    file_size_within_limit,
)

# Format a single file as a markdown block.
block = format_file_block("src/app.py", "def main():\n    pass\n")
# → "### src/app.py\n\n``` python\ndef main():\n    pass\n\n```"

# Check globs.
from code_to_markdown_context_dumper.core import matches_ignore_patterns
matches_ignore_patterns("debug.log", ["*.log"])  # True
matches_ignore_patterns("build/out.o", ["build/*"])  # True

# Check size.
file_size_within_limit("large.bin", max_size_bytes=1024)  # True/False
```

## API Reference

### `discover_files(root_dir, *, ignore_dirs=None, follow_symlinks=False)`

Walk *root_dir* and return a sorted list of relative paths for every
text file found. Automatically skips:

- Directories in [`DEFAULT_IGNORE_DIRS`](#default_ignore_dirs).
- Any directory whose name starts with `.` (dot-directories).
- Additional directories passed via *ignore_dirs*.
- Files whose extension is in the built-in binary list.
- Files containing a NUL byte (the same heuristic used by Git).

### `format_file_block(filepath, content)`

Return a markdown string with a `###` heading and a fenced code block
containing *content*. The language tag is inferred from the file
extension (Python → `python`, JavaScript → `javascript`, etc.).

### `dump_context(filepaths, *, root_dir=".")`

Read the given relative file paths and produce a single markdown
document by joining each file's [`format_file_block`](#format_file_block)
output with blank lines. Files that fail to read are silently skipped.

### `filter_files(filepaths, *, root_dir=".", exclude_patterns=None, max_size_bytes=None)`

Filter a list of relative file paths by glob patterns and/or a
byte-size cap. Returns the surviving paths in original order.

### `matches_ignore_patterns(filepath, patterns)`

Return `True` when *filepath* matches any of the glob-style *patterns*.
Patterns without a separator match against the filename portion only;
patterns with a separator match the full path from the right.

### `file_size_within_limit(filepath, max_size_bytes)`

Return `True` when *filepath* exists and its size ≤ *max_size_bytes*.
Pass `None` for *max_size_bytes* to disable size checks.

### `should_ignore_dir(name)`

Return `True` when *name* is a directory that should be skipped
(matched against `DEFAULT_IGNORE_DIRS` or starts with `.`).

### `is_binary_file(filepath)`

Heuristic binary detection — reads the first 8 KB and checks for a NUL
byte. Files that can't be opened are treated as binary.

### `DEFAULT_IGNORE_DIRS`

A frozenset of directory names that are always ignored during
discovery: `.git`, `.hg`, `.svn`, `.bzr`, `__pycache__`,
`.pytest_cache`, `.ruff_cache`, `.mypy_cache`, `node_modules`,
`.venv`, `venv`, `.tox`, `.eggs`, `egg-info`.

### `BINARY_EXTENSIONS`

A frozenset of file-extension suffixes that are skipped without
opening the file (compiled objects, executables, images, documents,
archives, media, fonts, databases, …).

## Project structure

```
code-to-markdown-context-dumper/
├── pyproject.toml              # Package metadata
├── code_to_markdown_context_dumper/
│   ├── __init__.py             # Public API re-exports
│   └── core.py                 # All implementation
├── tests/
│   └── test_core.py            # Full test suite
├── README.md
└── LICENSE
```

## Development

The test suite uses **pytest** and **only the standard library** — no
test dependencies beyond pytest itself.

```bash
# Install in editable mode
pip install -e .

# Run tests
python -m pytest -q
```

## License

MIT
