# Sub-task: [f03-s1] Expose the core API via __init__.py

from code_to_markdown_context_dumper.core import (
    discover_files,
    discover_filtered_files,
    is_binary_file,
    should_ignore,
)

__all__ = [
    "discover_files",
    "discover_filtered_files",
    "is_binary_file",
    "should_ignore",
]
