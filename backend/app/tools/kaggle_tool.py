"""Kaggle tools — wrapper over the OFFICIAL Kaggle API (kaggle package).

Auth uses the user's own kaggle.json — the standard Kaggle way:
  1. kaggle.com -> Settings -> API -> Create New Token (kaggle.json downloads)
  2. Put it in ~/.kaggle/kaggle.json  (Windows: %USERPROFILE%\\.kaggle\\kaggle.json)
No API key is ever asked for or stored by this code.

Covers: list competitions/datasets, download files, submit to a competition.
"""
import os
from pathlib import Path


def _api():
    """Build an authenticated Kaggle API client (lazy import, clear errors).

    Note: kaggle 2.x calls exit(1) when no credentials exist, which would
    kill the agent thread — so credentials are checked BEFORE authenticate().
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        raise RuntimeError(
            "kaggle package install nahi hai. Chalao: pip install kaggle"
        )

    kaggle_dir = Path.home() / ".kaggle"
    has_creds = bool(
        os.getenv("KAGGLE_API_TOKEN")
        or (os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"))
        or (kaggle_dir / "kaggle.json").exists()
        or (kaggle_dir / "access_token").exists()
    )
    if not has_creds:
        raise RuntimeError(
            "Kaggle login nahi hua. Sabse aasan tareeka:\n"
            "  Terminal me chalao: kaggle auth login\n"
            "(browser me Kaggle login hoga, phir token save ho jayega)\n"
            "Ya kaggle.com -> Settings -> API -> Create New Token, aur\n"
            "kaggle.json ko ~/.kaggle/ me rakho "
            "(Windows: C:\\Users\\<tum>\\.kaggle\\kaggle.json)"
        )

    api = KaggleApi()
    try:
        api.authenticate()
    except SystemExit:
        raise RuntimeError(
            "Kaggle authentication fail ho gaya. 'kaggle auth login' dobara "
            "chalao, ya kaggle.json dobara download karke ~/.kaggle/ me rakho."
        )
    except Exception as e:
        raise RuntimeError(f"Kaggle authentication fail ho gaya: {e}")
    return api


def _fmt_competitions(items):
    if not items:
        return "Koi competition nahi mila."
    lines = []
    for c in items[:20]:
        lines.append(
            f"- {c.ref} | {c.title} | deadline: {c.deadline} | "
            f"reward: {c.reward} | teams: {c.teamCount}"
        )
    return "\n".join(lines)


def kaggle_list_competitions(search: str = "") -> str:
    """List Kaggle competitions, optionally filtered by a search term."""
    api = _api()
    items = api.competitions_list(search=search or None)
    return _fmt_competitions(items)


def kaggle_list_datasets(search: str = "") -> str:
    """List Kaggle datasets, optionally filtered by a search term."""
    api = _api()
    items = api.dataset_list(search=search or None)
    if not items:
        return "Koi dataset nahi mila."
    lines = []
    for d in items[:20]:
        lines.append(f"- {d.ref} | {d.title} | downloads: {d.downloadCount}")
    return "\n".join(lines)


def kaggle_download_competition(competition: str, path: str = "kaggle_data") -> str:
    """Download a competition's data files into workspace/<path>/."""
    from ..config import settings

    dest = settings.workspace_dir / path / competition
    dest.mkdir(parents=True, exist_ok=True)
    api = _api()
    api.competition_download_files(competition, path=str(dest), quiet=False)
    files = [p.name for p in dest.iterdir()]
    return f"Download ho gaya: {competition} -> {dest}\nFiles: {', '.join(files)}"


def kaggle_download_dataset(dataset: str, path: str = "kaggle_data") -> str:
    """Download a dataset into workspace/<path>/<dataset>/ (unzipped)."""
    from ..config import settings

    dest = settings.workspace_dir / path / dataset.replace("/", "_")
    dest.mkdir(parents=True, exist_ok=True)
    api = _api()
    api.dataset_download_files(dataset, path=str(dest), unzip=True, quiet=False)
    files = [p.name for p in dest.iterdir()]
    return f"Download ho gaya: {dataset} -> {dest}\nFiles: {', '.join(files)}"


def kaggle_submit(competition: str, file: str, message: str) -> str:
    """Submit a CSV file to a competition. `file` is a workspace-relative path."""
    from ..config import settings

    target = (settings.workspace_dir / file).resolve()
    if not target.is_relative_to(settings.workspace_dir):
        raise ValueError("Submission file workspace ke andar honi chahiye.")
    if not target.exists():
        raise FileNotFoundError(f"Submission file nahi mili: {file}")
    api = _api()
    result = api.competition_submit(str(target), message, competition)
    return f"Submit ho gaya: {competition}\n{result}"
