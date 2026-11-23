"""Code-run tool — run a Python file the agent wrote, inside the workspace.

This closes the loop for a coding agent: write code -> run it -> read the
output or the error -> fix it -> run again. Only files inside the workspace
sandbox may run, and every run has a timeout.
"""
import subprocess
import sys
from pathlib import Path

from ..config import settings

DEFAULT_TIMEOUT = 120


def run_python(path: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Run a workspace Python file and return its stdout/stderr."""
    base = settings.workspace_dir
    target = (base / path).resolve()
    if not target.is_relative_to(base):
        raise ValueError("Sirf workspace ke andar ki file chala sakte ho.")
    if not target.exists():
        raise FileNotFoundError(f"File nahi mili: {path}")
    if target.suffix != ".py":
        raise ValueError("Sirf .py file chala sakte ho.")

    result = subprocess.run(
        [sys.executable, str(target)],
        cwd=str(base),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    out = result.stdout.strip()
    err = result.stderr.strip()
    report = f"Exit code: {result.returncode}\n"
    if out:
        report += f"--- stdout ---\n{out[-4000:]}\n"
    if err:
        report += f"--- stderr ---\n{err[-4000:]}\n"
    if not out and not err:
        report += "(koi output nahi)"
    return report
