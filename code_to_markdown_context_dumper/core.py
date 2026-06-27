import os
from pathlib import PurePath

# Sub-task: [f01-s1] Implement basic file discovery and filtering in core.py
# Modify ONLY code_to_markdown_context_dumper/core.py
# Standard library only, dependency-free Python.
# Acceptance: Functions to list files while ignoring binary files and common directories (like .git) are implemented.

DEFAULT_IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
    ".idea",
    ".vscode",
    "build",
    "dist",
    "*.egg-info",
}

DEFAULT_IGNORE_FILES = {
    ".DS_Store",
    "thumbs.db",
    "desktop.ini",
}


def is_binary_file(filepath: str) -> bool:
    """
    Check if a file is binary by looking at its content.

    Reads the first 1024 bytes and checks for null bytes or a high ratio
    of non-text bytes. Non-existent paths and directories are treated as
    non-binary. Files that cannot be read are conservatively treated as
    binary.

    Parameters
    ----------
    filepath : str
        Path to the file to check.

    Returns
    -------
    bool
        ``True`` if the file is binary, ``False`` otherwise.

    Notes
    -----
    - Empty files are treated as non-binary.
    - Unreadable files (e.g. permission denied) are treated as binary.
    - The heuristic threshold (30% non-text bytes) may misclassify files
      with many non-ASCII text characters (e.g. UTF-16, heavily-encoded
      text) as binary.
    """
    if not os.path.exists(filepath) or os.path.isdir(filepath):
        return False

    # Try reading the first 1024 bytes
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            if not chunk:
                return False  # Empty file is not considered binary by default, or is text-safe
            # Simple check for null byte
            if b'\x00' in chunk:
                return True
            # High proportion of non-ascii or non-printable bytes could indicate binary,
            # but standard UTF-8 text might have non-ASCII characters. Let's do a basic check.
            # A common heuristic: if a large proportion of characters are control characters,
            # it's binary.
            text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
            non_text = sum(1 for byte in chunk if byte not in text_chars)
            if non_text / len(chunk) > 0.30:
                return True
    except IOError:
        return True
    return False


def should_ignore(path: str, root_dir: str, ignore_dirs: set[str] | None = None, ignore_files: set[str] | None = None) -> bool:
    """
    Determine whether a path should be ignored based on its directory
    ancestry and final component name.

    A path is ignored when any ancestor directory is in *ignore_dirs*, or
    when the final component is a matching directory name (in *ignore_dirs*)
    or a matching file name (in *ignore_files*).

    Parameters
    ----------
    path : str
        Absolute or relative path to the file or directory to check.
    root_dir : str
        Root directory used to compute the relative path for matching.
    ignore_dirs : set of str, optional
        Directory names to ignore (default: ``DEFAULT_IGNORE_DIRS``).
    ignore_files : set of str, optional
        File names to ignore (default: ``DEFAULT_IGNORE_FILES``).

    Returns
    -------
    bool
        ``True`` if the path should be ignored, ``False`` otherwise.
    """
    if ignore_dirs is None:
        ignore_dirs = DEFAULT_IGNORE_DIRS
    if ignore_files is None:
        ignore_files = DEFAULT_IGNORE_FILES

    # Get path parts relative to root_dir
    rel_path = os.path.relpath(path, root_dir)
    parts = rel_path.split(os.sep)

    # Check if any directory in the path matches ignore_dirs
    for part in parts[:-1]:
        if part in ignore_dirs:
            return True

    # Check if the final file/directory name matches ignore_dirs or ignore_files
    if parts:
        last_part = parts[-1]
        if os.path.isdir(path):
            if last_part in ignore_dirs:
                return True
        else:
            if last_part in ignore_files:
                return True

    return False


def discover_files(root_dir: str, ignore_dirs: set[str] | None = None, ignore_files: set[str] | None = None, ignore_binary: bool = True) -> list[str]:
    """
    Walk *root_dir* and collect relative paths of discoverable files.

    Ignores directories matching *ignore_dirs* and files matching
    *ignore_files*. Optionally skips binary files detected via a
    content heuristic.

    Parameters
    ----------
    root_dir : str
        Root directory to scan.
    ignore_dirs : set of str, optional
        Directory names to skip entirely (default: ``DEFAULT_IGNORE_DIRS``).
        Matched directories are pruned from ``os.walk`` so their contents
        are never visited.
    ignore_files : set of str, optional
        File names to skip (default: ``DEFAULT_IGNORE_FILES``).
    ignore_binary : bool
        Whether to skip binary files (default: ``True``).

    Returns
    -------
    list of str
        Sorted list of file paths relative to *root_dir*.

    Notes
    -----
    - Only files (not directories) are included in the result.
    - Symlinks are followed by ``os.walk`` on most platforms.
    - Binary detection uses :func:`is_binary_file` and may produce
      false positives for heavily-encoded text files.
    """
    discovered = []
    root_dir = os.path.abspath(root_dir)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Modify dirnames in-place to prune traversal of ignored directories
        if ignore_dirs is None:
            ignore_dirs_set = DEFAULT_IGNORE_DIRS
        else:
            ignore_dirs_set = set(ignore_dirs)

        dirnames[:] = [d for d in dirnames if d not in ignore_dirs_set]

        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, root_dir)

            # Check ignored files
            if ignore_files is None:
                ignore_files_set = DEFAULT_IGNORE_FILES
            else:
                ignore_files_set = set(ignore_files)

            if filename in ignore_files_set:
                continue

            if ignore_binary and is_binary_file(filepath):
                continue

            discovered.append(rel_path)

    return sorted(discovered)

# Sub-task: [f02-s1] Add support for custom ignore patterns and max file size limits


def matches_any_pattern(rel_path: str, patterns: list[str]) -> bool:
    """
    Check if a relative path matches any of the given glob-style patterns.

    Uses ``PurePath.match`` for matching, so a pattern like ``*.log``
    will match ``file.log`` at any directory depth.

    Parameters
    ----------
    rel_path : str
        Relative path to test (forward- or backslash-separated).
    patterns : list of str
        Glob-style patterns to check against.

    Returns
    -------
    bool
        ``True`` if *rel_path* matches at least one pattern,
        ``False`` otherwise.

    Notes
    -----
    - Matching is performed on the full relative path, not just the file
      name, so ``secret/*`` will correctly exclude files in a ``secret/``
      directory.
    - Patterns that are not valid globs may silently match nothing.
    """
    p = PurePath(rel_path)
    for pattern in patterns:
        if p.match(pattern):
            return True
    return False


def discover_filtered_files(
    root_dir: str,
    ignore_dirs: set[str] | None = None,
    ignore_files: set[str] | None = None,
    ignore_binary: bool = True,
    ignore_patterns: list[str] | None = None,
    max_size: int | None = None,
) -> list[str]:
    """
    Extended file discovery with glob-style ignore patterns and max file size.

    Parameters
    ----------
    root_dir : str
        Root directory to scan.
    ignore_dirs : set, optional
        Directory names to skip entirely (default: DEFAULT_IGNORE_DIRS).
    ignore_files : set, optional
        Filenames to skip (default: DEFAULT_IGNORE_FILES).
    ignore_binary : bool
        Whether to skip binary files (default: True).
    ignore_patterns : list of str, optional
        Glob-style patterns; any file whose relative path matches a pattern
        is excluded (e.g. ``['*.log', 'secret/*']``).
    max_size : int, optional
        Maximum file size in bytes. Files larger than this are excluded.

    Returns
    -------
    list of str
        Sorted list of relative paths for files that pass all filters.
    """
    files = discover_files(root_dir, ignore_dirs, ignore_files, ignore_binary)

    if not ignore_patterns and max_size is None:
        return files

    filtered = []
    for rel_path in files:
        filepath = os.path.join(root_dir, rel_path)

        if ignore_patterns and matches_any_pattern(rel_path, ignore_patterns):
            continue

        if max_size is not None:
            try:
                if os.path.getsize(filepath) > max_size:
                    continue
            except OSError:
                continue

        filtered.append(rel_path)

    return filtered


# Sub-task: [f01-s2] Implement markdown generation logic in core.py
# Acceptance: Function to format file contents into markdown code blocks
# with file path headers is implemented.


def _infer_language(file_path: str) -> str:
    """
    Infer a markdown code-fence language identifier from a file extension.
    Returns an empty string if the language cannot be determined.
    """
    _LANG_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".jsx": "jsx",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".fish": "fish",
        ".ps1": "powershell",
        ".bat": "batch",
        ".cmd": "batch",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "scss",
        ".less": "less",
        ".json": "json",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".md": "markdown",
        ".rst": "rst",
        ".tex": "latex",
        ".sql": "sql",
        ".r": "r",
        ".m": "matlab",
        ".pl": "perl",
        ".lua": "lua",
        ".dart": "dart",
        ".dockerfile": "dockerfile",
        ".makefile": "makefile",
        ".cmake": "cmake",
        ".gradle": "gradle",
        ".tf": "terraform",
        ".graphql": "graphql",
        ".proto": "protobuf",
    }
    ext = os.path.splitext(file_path)[1].lower()
    return _LANG_MAP.get(ext, "")


def format_markdown_context(
    files: list[tuple[str, str]],
    root_label: str = "Project Context",
) -> str:
    """
    Format a list of files and their contents into a markdown context document.

    Each file is rendered as a level‑2 heading followed by a fenced code block
    with syntax highlighting inferred from the file extension.

    Parameters
    ----------
    files : list of (str, str)
        List of ``(file_path, content)`` tuples.
    root_label : str
        Top-level heading label (default: ``"Project Context"``).

    Returns
    -------
    str
        Formatted markdown string.
    """
    lines = [f"# {root_label}", ""]
    for file_path, content in files:
        lines.append(f"## File: {file_path}")
        lang = _infer_language(file_path)
        code_fence = f"```{lang}" if lang else "```"
        lines.append(code_fence)
        if content:
            lines.append(content)
        lines.append("```")
        lines.append("")
    return "\n".join(lines)
