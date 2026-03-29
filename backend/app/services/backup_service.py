"""Project backup: creates a ZIP snapshot of the SQLite DB."""
from __future__ import annotations

import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from ..config import DATA_DIR, DATABASE_PATH


def create_backup(project_id: int, label: str = "backup") -> Path:
    """
    Copy the current SQLite DB into a timestamped ZIP inside DATA_DIR/backups/.
    Returns the path to the ZIP file.
    """
    backups_dir = DATA_DIR / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    zip_name = f"project_{project_id}_{label}_{ts}.zip"
    zip_path = backups_dir / zip_name

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATABASE_PATH, arcname="econodex.db")

    return zip_path
