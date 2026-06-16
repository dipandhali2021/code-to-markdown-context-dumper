import os
import tempfile
import pytest
from code_to_markdown_context_dumper.core import discover_files, is_binary_file, should_ignore

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
