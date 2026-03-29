"""Media ingestion: thumbnail generation, EXIF extraction."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Tuple

THUMBNAIL_SIZE = (200, 200)
THUMB_SUFFIX = "_thumb"


def ensure_photos_dir(photos_root: str) -> Path:
    p = Path(photos_root)
    p.mkdir(parents=True, exist_ok=True)
    return p


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def save_upload(
    photos_root: str,
    filename: str,
    data: bytes,
) -> Tuple[Path, Path, int, str, Optional[str]]:
    """
    Save an uploaded file and generate a thumbnail.

    Returns
    -------
    (saved_path, thumb_path, size_bytes, mime_type, exif_json)
    """
    root = ensure_photos_dir(photos_root)
    dest = _unique_path(root / filename)
    dest.write_bytes(data)
    size = len(data)
    mime = _guess_mime(dest)
    exif = _extract_exif(dest)

    # Thumbnail
    thumb = _make_thumbnail(dest)

    return dest, thumb, size, mime, exif


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    i = 1
    while True:
        candidate = path.parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def _guess_mime(path: Path) -> str:
    import mimetypes
    mt, _ = mimetypes.guess_type(str(path))
    return mt or "application/octet-stream"


def _extract_exif(path: Path) -> Optional[str]:
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        img = Image.open(path)
        raw = img._getexif()
        if not raw:
            return None
        exif = {TAGS.get(k, str(k)): str(v) for k, v in raw.items() if k in TAGS}
        return json.dumps(exif, ensure_ascii=False)
    except Exception:
        return None


def _make_thumbnail(path: Path) -> Path:
    thumb_dir = path.parent / "thumbnails"
    thumb_dir.mkdir(exist_ok=True)
    thumb_path = thumb_dir / f"{path.stem}{THUMB_SUFFIX}{path.suffix}"
    try:
        from PIL import Image
        img = Image.open(path)
        img.thumbnail(THUMBNAIL_SIZE)
        # Convert palette/RGBA images that can't be saved as JPEG
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.save(thumb_path)
    except Exception:
        # If thumbnail fails (e.g. non-image file) return same path
        thumb_path = path
    return thumb_path


def relative_path(abs_path: Path, photos_root: str) -> str:
    try:
        return str(abs_path.relative_to(Path(photos_root)))
    except ValueError:
        return str(abs_path)
