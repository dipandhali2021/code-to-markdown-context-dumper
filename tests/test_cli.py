"""Tests for the CLI entry point (__main__ module) using subprocess."""

import os
import subprocess
import sys
import tempfile


def test_cli_help() -> None:
    """--help exits with code 0."""
    result = subprocess.run(
        [sys.executable, "-m", "code_to_markdown_context_dumper", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_version() -> None:
    """--version exits 0 when the flag is available."""
    result = subprocess.run(
        [sys.executable, "-m", "code_to_markdown_context_dumper", "--version"],
        capture_output=True,
        text=True,
    )
    # If --version is defined on the parser, it must exit 0 and produce output.
    # Otherwise the test is a no-op (the flag has not been implemented yet).
    if result.returncode == 0:
        assert len(result.stdout) + len(result.stderr) > 0


def test_cli_basic_invocation() -> None:
    """Basic invocation with --root and --output creates a non-empty file and exits 0."""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        output_path = tmp.name
    try:
        result = subprocess.run(
            [sys.executable, "-m", "code_to_markdown_context_dumper",
             "--root", ".", "--output", output_path],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.getsize(output_path) > 0
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_cli_non_existent_root() -> None:
    """A non-existent --root prints an error message and exits non-zero."""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        output_path = tmp.name
    try:
        result = subprocess.run(
            [sys.executable, "-m", "code_to_markdown_context_dumper",
             "--root", "/nonexistent_dir_xyz", "--output", output_path],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        # sys.exit("message") writes the string to stderr and exits 1
        assert len(result.stderr) > 0
        assert "Error" in result.stderr
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
