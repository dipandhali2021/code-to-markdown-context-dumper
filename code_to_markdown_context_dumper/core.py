import os
import mimetypes

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
    Reads a chunk of bytes and checks for null bytes or a high ratio of non-text bytes.
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

def should_ignore(path: str, root_dir: str, ignore_dirs=None, ignore_files=None) -> bool:
    """
    Check if a file or directory path should be ignored.
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

def discover_files(root_dir: str, ignore_dirs=None, ignore_files=None, ignore_binary=True) -> list:
    """
    List files in root_dir, ignoring directories and files in ignore list and optionally binary files.
    Returns sorted list of relative paths.
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
