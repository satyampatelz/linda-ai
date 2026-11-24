"""File tools — read, write, list and delete files.

Everything is sandboxed to the workspace directory (WORKSPACE_DIR in .env,
default: linda-ai/workspace/). Paths that try to escape it ("../...") are
refused. This keeps the agent's file work in one place you can inspect.
"""
import shutil
from pathlib import Path

from ..config import settings

MAX_READ_CHARS = 12000


def _resolve(rel_path: str) -> Path:
    """Resolve a workspace-relative path, refusing escapes."""
    base = settings.workspace_dir
    target = (base / rel_path).resolve()
    if not target.is_relative_to(base):
        raise ValueError(
            f"Path '{rel_path}' is outside the workspace. "
            f"Allowed folder: {base}"
        )
    return target


def files_list(path: str = ".") -> str:
    """List files and folders in a workspace directory."""
    target = _resolve(path)
    if not target.exists():
        return f"Not found: {path}"
    if target.is_file():
        return f"File: {path} ({target.stat().st_size} bytes)"
    items = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    if not items:
        return f"Contents of {path}:\n(empty)"
    lines = []
    for p in items:
        if p.is_dir():
            lines.append(f"[dir]  {p.name}/")
        else:
            lines.append(f"       {p.name} ({p.stat().st_size} bytes)")
    return f"Contents of {path}:\n" + "\n".join(lines)


def files_read(path: str) -> str:
    """Read a text file from the workspace."""
    target = _resolve(path)
    if not target.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if target.is_dir():
        raise ValueError(f"'{path}' is a folder, not a file. Use files_list.")
    text = target.read_text(encoding="utf-8", errors="replace")
    if len(text) > MAX_READ_CHARS:
        text = text[:MAX_READ_CHARS] + "\n... (file is too long, cut off here)"
    return text


def files_write(path: str, content: str) -> str:
    """Write text to a file in the workspace (creates parent folders)."""
    target = _resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {path}"


def files_mkdir(path: str) -> str:
    """Create a folder (and parents) in the workspace."""
    target = _resolve(path)
    target.mkdir(parents=True, exist_ok=True)
    return f"Folder created: {path}"


def files_delete(path: str) -> str:
    """Delete a file or folder (with contents) from the workspace."""
    target = _resolve(path)
    if not target.exists():
        return f"Doesn't exist: {path}"
    if target.is_dir():
        shutil.rmtree(target)
        return f"Folder deleted: {path}"
    target.unlink()
    return f"File deleted: {path}"
