import os
import tempfile
import pytest
from code_to_markdown_context_dumper.core import discover_files, is_binary_file, should_ignore, discover_filtered_files

def test_is_binary_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create text file
        txt_path = os.path.join(tmpdir, "test.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Hello World! This is a simple text file.")
        
        # Create binary file
        bin_path = os.path.join(tmpdir, "test.bin")
        with open(bin_path, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04\xff")
            
        assert not is_binary_file(txt_path)
        assert is_binary_file(bin_path)

def test_should_ignore():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock folder structure isn't fully needed, but we check path matching.
        root = tmpdir
        assert should_ignore(os.path.join(root, ".git", "config"), root)
        assert should_ignore(os.path.join(root, "node_modules", "package.json"), root)
        assert should_ignore(os.path.join(root, "subdir", ".DS_Store"), root)
        assert not should_ignore(os.path.join(root, "src", "main.py"), root)

def test_discover_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directories
        os.makedirs(os.path.join(tmpdir, "src"))
        os.makedirs(os.path.join(tmpdir, ".git"))
        os.makedirs(os.path.join(tmpdir, "node_modules"))
        
        # Create files
        with open(os.path.join(tmpdir, "src", "main.py"), "w") as f:
            f.write("print('hello')")
        with open(os.path.join(tmpdir, "src", "helper.py"), "w") as f:
            f.write("def help(): pass")
        with open(os.path.join(tmpdir, ".git", "config"), "w") as f:
            f.write("[core]")
        with open(os.path.join(tmpdir, "node_modules", "index.js"), "w") as f:
            f.write("// js file")
        with open(os.path.join(tmpdir, "src", "logo.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00") # binary
            
        files = discover_files(tmpdir)
        assert files == ["src/helper.py", "src/main.py"]
        
        # Discover files with binary included
        files_with_binary = discover_files(tmpdir, ignore_binary=False)
        assert files_with_binary == ["src/helper.py", "src/logo.png", "src/main.py"]



def test_discover_files_empty_dir():
    """File discovery on an empty directory returns an empty list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        assert discover_files(tmpdir) == []


def test_discover_files_non_existent_dir():
    """File discovery on a non-existent directory returns an empty list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent = os.path.join(tmpdir, "does_not_exist")
        assert discover_files(nonexistent) == []


def test_discover_files_all_ignored():
    """All files match ignore patterns -> empty result."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for d in (".git", "__pycache__"):
            os.makedirs(os.path.join(tmpdir, d))
        with open(os.path.join(tmpdir, ".git", "HEAD"), "w") as f:
            f.write("ref: refs/heads/main")
        with open(os.path.join(tmpdir, "__pycache__", "foo.cpython-311.pyc"), "w") as f:
            f.write("cached")
        with open(os.path.join(tmpdir, ".DS_Store"), "w") as f:
            f.write("")
        assert discover_files(tmpdir) == []


def test_discover_files_custom_ignore():
    """Custom ignore lists override defaults correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "mylogs"))
        os.makedirs(os.path.join(tmpdir, ".git"))
        with open(os.path.join(tmpdir, "mylogs", "app.log"), "w") as f:
            f.write("log")
        with open(os.path.join(tmpdir, ".git", "config"), "w") as f:
            f.write("[core]")
        with open(os.path.join(tmpdir, "readme.md"), "w") as f:
            f.write("# Readme")
        files = discover_files(tmpdir, ignore_dirs={"mylogs"}, ignore_files=set())
        assert ".git/config" in files
        assert "readme.md" in files
        assert "mylogs/app.log" not in files


def test_discover_files_only_text():
    """Binary files are excluded by default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "src"))
        with open(os.path.join(tmpdir, "src", "main.py"), "w") as f:
            f.write("x = 1")
        with open(os.path.join(tmpdir, "src", "data.bin"), "wb") as f:
            f.write(b"\x00\x01\x02\xff")
        with open(os.path.join(tmpdir, "src", "empty.bin"), "wb") as f:
            f.write(b"")
        files = discover_files(tmpdir)
        assert files == ["src/empty.bin", "src/main.py"]


def test_discover_files_deep_nesting():
    """Deeply nested non-ignored directories are discovered."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "a", "b", "c", "d")
        os.makedirs(path)
        with open(os.path.join(path, "deep.txt"), "w") as f:
            f.write("deep")
        files = discover_files(tmpdir)
        assert files == [os.path.join("a", "b", "c", "d", "deep.txt")]


def test_discover_files_ignored_dirs_not_traversed():
    """Ignored directories are pruned from os.walk traversal (not just filtered)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, ".git", "objects", "pack"))
        with open(os.path.join(tmpdir, ".git", "objects", "pack", "big.pack"), "w") as f:
            f.write("packed")
        os.makedirs(os.path.join(tmpdir, "src"))
        with open(os.path.join(tmpdir, "src", "main.py"), "w") as f:
            f.write("code")
        files = discover_files(tmpdir)
        assert files == ["src/main.py"]
        assert ".git/objects/pack/big.pack" not in files


# ── Helper: format a list of file paths as a markdown context snippet ──────────

def _files_to_markdown(file_list, root_label="Project Context"):
    """Convert a sorted list of file paths into a markdown context string."""
    lines = [f"# {root_label}", ""]
    for path in file_list:
        lines.append(f"## File: {path}")
        lines.append("```")
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def test_markdown_format_empty():
    """An empty file list produces a minimal markdown document."""
    md = _files_to_markdown([])
    expected = "# Project Context\n"
    assert md == expected


def test_markdown_format_single_file():
    """Markdown output for a single file is well-formed."""
    md = _files_to_markdown(["src/main.py"])
    assert md.startswith("# Project Context")
    assert "## File: src/main.py" in md
    assert md.count("## File:") == 1


def test_markdown_format_multiple_files():
    """Markdown output lists multiple files in order."""
    paths = ["a.py", "b.py", "c.py"]
    md = _files_to_markdown(paths)
    idx_a = md.index("## File: a.py")
    idx_b = md.index("## File: b.py")
    idx_c = md.index("## File: c.py")
    assert idx_a < idx_b < idx_c


def test_markdown_format_integration():
    """Real discovered files are correctly formatted as markdown."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "src"))
        with open(os.path.join(tmpdir, "src", "main.py"), "w") as f:
            f.write("print('hi')")
        with open(os.path.join(tmpdir, "README.md"), "w") as f:
            f.write("# Project")
        files = discover_files(tmpdir)
        assert files == ["README.md", "src/main.py"]
        md = _files_to_markdown(files)
        assert "## File: README.md" in md
        assert "## File: src/main.py" in md
        assert md.index("## File: README.md") < md.index("## File: src/main.py")


# ── [f02-s2] Tests for custom ignore patterns and file size limits ───────────


def test_discover_filtered_files_custom_patterns():
    """Custom glob-style ignore patterns exclude matching files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "src"))
        os.makedirs(os.path.join(tmpdir, "logs"))
        with open(os.path.join(tmpdir, "src", "main.py"), "w") as f:
            f.write("code")
        with open(os.path.join(tmpdir, "src", "data.txt"), "w") as f:
            f.write("data")
        with open(os.path.join(tmpdir, "logs", "app.log"), "w") as f:
            f.write("log entry")
        with open(os.path.join(tmpdir, "logs", "access.log"), "w") as f:
            f.write("GET / 200")

        files = discover_filtered_files(tmpdir, ignore_patterns=["*.log"])
        assert "src/main.py" in files
        assert "src/data.txt" in files
        assert "logs/app.log" not in files
        assert "logs/access.log" not in files


def test_discover_filtered_files_max_size():
    """Files exceeding the size limit are excluded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "small.txt"), "w") as f:
            f.write("x" * 50)
        with open(os.path.join(tmpdir, "large.txt"), "w") as f:
            f.write("x" * 200)
        with open(os.path.join(tmpdir, "medium.txt"), "w") as f:
            f.write("x" * 100)

        files = discover_filtered_files(tmpdir, max_size=100)
        assert "small.txt" in files
        assert "medium.txt" in files
        assert "large.txt" not in files


def test_discover_filtered_files_patterns_and_size():
    """Both custom patterns and max_size filters are applied together."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "notes.txt"), "w") as f:
            f.write("hello")
        with open(os.path.join(tmpdir, "trace.log"), "w") as f:
            f.write("x" * 500)
        with open(os.path.join(tmpdir, "small.log"), "w") as f:
            f.write("tiny")

        files = discover_filtered_files(tmpdir, ignore_patterns=["*.log"], max_size=100)
        assert files == ["notes.txt"]


def test_discover_filtered_files_no_filters():
    """With no custom filters, behaves identically to discover_files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "src"))
        with open(os.path.join(tmpdir, "src", "main.py"), "w") as f:
            f.write("code")
        with open(os.path.join(tmpdir, "README.md"), "w") as f:
            f.write("# Project")
        assert discover_filtered_files(tmpdir) == discover_files(tmpdir)
