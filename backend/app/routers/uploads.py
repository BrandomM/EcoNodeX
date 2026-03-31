"""
LAN photo upload endpoint + QR code generation.
No authentication by design (MVP #1, LAN-only).
"""
import io
import socket
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..config import PORT, VITE_PORT, get_local_ip, is_dev_mode
from ..database import get_db
from ..models import Media, Project, Taxon, Location, Replicate, OccurrenceRecord, SamplingEvent
from ..schemas import QRResponse, UploadDestination
from ..services import media_service

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.get("/qr", response_model=QRResponse)
def get_upload_qr(project_id: int = Query(...)):
    """Generate a QR code pointing to the mobile upload page."""
    try:
        import qrcode
        import base64

        local_ip = get_local_ip()
        frontend_port = VITE_PORT if is_dev_mode() else PORT
        url = f"http://{local_ip}:{frontend_port}/upload?project={project_id}"

        qr = qrcode.QRCode(version=1, box_size=8, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()

        return QRResponse(upload_url=url, qr_b64=qr_b64)
    except ImportError:
        raise HTTPException(500, "qrcode library not available")


@router.get("/destinations")
def search_destinations(
    project_id: int = Query(...),
    q: str = Query(""),
    db: Session = Depends(get_db),
):
    """Search for taxa / locations / replicates to use as upload destinations."""
    search = f"%{q}%" if q else "%"
    results: List[dict] = []

    taxa = (
        db.query(Taxon)
        .filter(
            Taxon.project_id == project_id,
            (Taxon.scientific_name.ilike(search) | Taxon.alias.ilike(search)),
        )
        .limit(20)
        .all()
    )
    for t in taxa:
        results.append({
            "type": "taxon",
            "id": t.id,
            "label": f"{t.alias or t.scientific_name} ({t.rank})",
        })

    locs = (
        db.query(Location)
        .filter(Location.project_id == project_id, Location.name.ilike(search))
        .limit(10)
        .all()
    )
    for l in locs:
        results.append({"type": "location", "id": l.id, "label": l.name})

    reps = (
        db.query(Replicate)
        .join(SamplingEvent, Replicate.event_id == SamplingEvent.id)
        .filter(
            SamplingEvent.project_id == project_id,
            Replicate.code.ilike(search),
        )
        .limit(10)
        .all()
    )
    for r in reps:
        results.append({
            "type": "replicate",
            "id": r.id,
            "label": f"Rep {r.code} — Evento {r.event_id}",
        })

    return results


@router.post("/files")
async def upload_files(
    project_id: int = Form(...),
    linked_to_type: str = Form(...),
    linked_to_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Receive uploaded files and store them in the project's photos folder."""
    proj = db.get(Project, project_id)
    if not proj:
        raise HTTPException(404, "Project not found")
    if not proj.photos_root_path:
        raise HTTPException(400, "Photos folder not configured for this project. Set it in Settings first.")

    saved = []
    errors = []
    for upload in files:
        try:
            data = await upload.read()
            saved_path, thumb_path, size, mime, exif = media_service.save_upload(
                proj.photos_root_path, upload.filename or "upload", data
            )
            rel = media_service.relative_path(saved_path, proj.photos_root_path)
            thumb_rel = media_service.relative_path(thumb_path, proj.photos_root_path)

            m = Media(
                project_id=project_id,
                file_name=saved_path.name,
                relative_path=rel,
                thumbnail_path=thumb_rel,
                size_bytes=size,
                mime_type=mime,
                exif_json=exif,
                linked_to_type=linked_to_type,
                linked_to_id=linked_to_id,
                is_profile=False,
            )
            db.add(m)
            db.flush()
            saved.append({"id": m.id, "file_name": m.file_name})
        except Exception as e:
            errors.append({"file_name": upload.filename, "error": str(e)})

    db.commit()
    return {"saved": saved, "errors": errors}
