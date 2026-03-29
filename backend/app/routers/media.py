"""Media management: list, link, profile selection."""
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Media, Project
from ..schemas import MediaOut, MediaUpdate

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("", response_model=List[MediaOut])
def list_media(
    project_id: int = Query(...),
    linked_to_type: Optional[str] = Query(None),
    linked_to_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Media).filter_by(project_id=project_id)
    if linked_to_type:
        q = q.filter_by(linked_to_type=linked_to_type)
    if linked_to_id is not None:
        q = q.filter_by(linked_to_id=linked_to_id)
    return q.order_by(Media.created_at.desc()).all()


@router.get("/{media_id}", response_model=MediaOut)
def get_media(media_id: int, db: Session = Depends(get_db)):
    m = db.get(Media, media_id)
    if not m:
        raise HTTPException(404, "Media not found")
    return m


@router.patch("/{media_id}", response_model=MediaOut)
def update_media(media_id: int, body: MediaUpdate, db: Session = Depends(get_db)):
    m = db.get(Media, media_id)
    if not m:
        raise HTTPException(404, "Media not found")

    updates = body.model_dump(exclude_unset=True)

    # If setting this as profile, clear previous profile for same entity
    if updates.get("is_profile"):
        linked_type = updates.get("linked_to_type", m.linked_to_type)
        linked_id = updates.get("linked_to_id", m.linked_to_id)
        if linked_type and linked_id is not None:
            db.query(Media).filter_by(
                project_id=m.project_id,
                linked_to_type=linked_type,
                linked_to_id=linked_id,
                is_profile=True,
            ).update({"is_profile": False}, synchronize_session="fetch")

    for k, v in updates.items():
        setattr(m, k, v)
    db.commit()
    db.refresh(m)
    return m


@router.delete("/{media_id}", status_code=204)
def delete_media(media_id: int, db: Session = Depends(get_db)):
    m = db.get(Media, media_id)
    if not m:
        raise HTTPException(404, "Media not found")
    # Remove physical file (best effort)
    proj = db.get(Project, m.project_id)
    if proj and proj.photos_root_path:
        full_path = Path(proj.photos_root_path) / m.relative_path
        try:
            full_path.unlink(missing_ok=True)
        except Exception:
            pass
    db.delete(m)
    db.commit()


@router.get("/{media_id}/file")
def serve_media_file(media_id: int, db: Session = Depends(get_db)):
    """Serve the actual image file."""
    m = db.get(Media, media_id)
    if not m:
        raise HTTPException(404, "Media not found")
    proj = db.get(Project, m.project_id)
    if not proj or not proj.photos_root_path:
        raise HTTPException(404, "Photos folder not configured")
    full_path = Path(proj.photos_root_path) / m.relative_path
    if not full_path.exists():
        raise HTTPException(404, "File not found on disk")
    return FileResponse(str(full_path), media_type=m.mime_type or "application/octet-stream")


@router.get("/{media_id}/thumbnail")
def serve_thumbnail(media_id: int, db: Session = Depends(get_db)):
    """Serve thumbnail; falls back to full file if no thumbnail."""
    m = db.get(Media, media_id)
    if not m:
        raise HTTPException(404, "Media not found")
    proj = db.get(Project, m.project_id)
    if not proj or not proj.photos_root_path:
        raise HTTPException(404, "Photos folder not configured")

    if m.thumbnail_path:
        thumb = Path(proj.photos_root_path) / m.thumbnail_path
        if thumb.exists():
            return FileResponse(str(thumb), media_type=m.mime_type or "image/jpeg")

    full_path = Path(proj.photos_root_path) / m.relative_path
    if not full_path.exists():
        raise HTTPException(404, "File not found on disk")
    return FileResponse(str(full_path), media_type=m.mime_type or "application/octet-stream")
