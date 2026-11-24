"""GitHub/git tools — a thin wrapper over the git CLI on the user's machine.

The agent uses YOUR git config and YOUR credentials (saved in your system
credential manager / SSH keys). No username, password or token is ever asked
for, stored, or written anywhere by this code.

Typical flow the agent follows:
  github_init(path) -> files_write(...) -> github_add_commit(...) ->
  github_remote_add(path, url) -> github_push(path)
"""
import subprocess
from pathlib import Path


def _run_git(repo_path, args, timeout=180):
    """Run a git command in a repo and return its output (raises on failure)."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    out = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{out}")
    return out or "(no output)"


def github_init(path: str) -> str:
    """Create a folder (if needed) and init a git repo in it (branch: main)."""
    repo = Path(path)
    repo.mkdir(parents=True, exist_ok=True)
    out = _run_git(repo, ["init", "-b", "main"])
    return f"{out}\nRepo created: {repo}"


def github_status(path: str) -> str:
    """Short git status of a repo."""
    return _run_git(path, ["status", "--short", "--branch"])


def github_remote_add(path: str, url: str, name: str = "origin") -> str:
    """Add a remote (or update it if the name already exists)."""
    result = subprocess.run(
        ["git", "remote", "add", name, url],
        cwd=str(path),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Remote already exists — just update its URL.
        _run_git(path, ["remote", "set-url", name, url])
        return f"Updated remote '{name}' URL: {url}"
    return f"Added remote '{name}': {url}"


def github_add_commit(path: str, message: str) -> str:
    """Stage everything and commit. If nothing changed, says so (not an error)."""
    _run_git(path, ["add", "-A"])
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(path),
        capture_output=True,
        text=True,
    )
    out = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        if "nothing to commit" in out:
            return "Nothing to commit — everything is already committed."
        raise RuntimeError(f"git commit failed:\n{out}")
    return out


def github_push(path: str, remote: str = "origin", branch: str = "main") -> str:
    """Push to a remote. Uses the user's saved git credentials.

    First push to a new empty GitHub repo: create the empty repo on github.com
    first, then github_remote_add(path, <repo url>), then github_push(path).
    """
    return _run_git(path, ["push", "-u", remote, branch], timeout=300)


def github_clone(url: str, path: str) -> str:
    """Clone a repo to a local folder."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "clone", url, str(dest)],
        cwd=str(dest.parent),
        capture_output=True,
        text=True,
        timeout=300,
    )
    out = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise RuntimeError(f"git clone failed:\n{out}")
    return f"Cloned: {url} -> {dest}\n{out}"
