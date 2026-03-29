"""Export endpoints: CSV, Excel, DwC-A, project ZIP, project import."""
import json
import shutil
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Project
from ..schemas import ExportOptions
from ..services import export_service
from ..services.backup_service import create_backup

router = APIRouter(prefix="/api/exports", tags=["exports"])


def _csv_response(data: bytes, filename: str) -> Response:
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _zip_response(data: bytes, filename: str) -> Response:
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/csv/taxa")
def export_taxa_csv(project_id: int = Query(...), db: Session = Depends(get_db)):
    rows = export_service._taxa_rows(project_id, db)
    fields = ["id","parent_taxon_id","scientific_name","rank","common_name","alias","description","created_at","updated_at"]
    return _csv_response(export_service._write_csv(rows, fields), "taxa.csv")


@router.get("/csv/locations")
def export_locations_csv(project_id: int = Query(...), db: Session = Depends(get_db)):
    rows = export_service._locations_rows(project_id, db)
    fields = ["id","parent_location_id","name","type","latitude","longitude","altitude","description","created_at","updated_at"]
    return _csv_response(export_service._write_csv(rows, fields), "locations.csv")


@router.get("/csv/events")
def export_events_csv(project_id: int = Query(...), db: Session = Depends(get_db)):
    rows = export_service._events_rows(project_id, db)
    fields = ["id","location_id","start_date","end_date","description","created_at","updated_at"]
    return _csv_response(export_service._write_csv(rows, fields), "events.csv")


@router.get("/csv/replicates")
def export_replicates_csv(project_id: int = Query(...), db: Session = Depends(get_db)):
    rows = export_service._replicates_rows(project_id, db)
    fields = ["id","event_id","code","method_id","notes","created_at","updated_at"]
    return _csv_response(export_service._write_csv(rows, fields), "replicates.csv")


@router.get("/csv/records")
def export_records_csv(project_id: int = Query(...), db: Session = Depends(get_db)):
    rows = export_service._records_rows(project_id, db)
    fields = ["id","replicate_id","taxon_id","taxon_scientific_name","taxon_alias","individual_count","method_id","date_time","latitude","longitude","notes","created_at","updated_at"]
    return _csv_response(export_service._write_csv(rows, fields), "records.csv")


@router.get("/csv/methods")
def export_methods_csv(project_id: int = Query(...), db: Session = Depends(get_db)):
    rows = export_service._methods_rows(project_id, db)
    fields = ["id","code","label","description","created_at","updated_at"]
    return _csv_response(export_service._write_csv(rows, fields), "methods.csv")


@router.get("/csv/media")
def export_media_csv(project_id: int = Query(...), db: Session = Depends(get_db)):
    rows = export_service._media_rows(project_id, db)
    fields = ["id","file_name","relative_path","size_bytes","mime_type","linked_to_type","linked_to_id","is_profile","created_at"]
    return _csv_response(export_service._write_csv(rows, fields), "media.csv")


@router.get("/csv/abundance-matrix")
def export_abundance_matrix(project_id: int = Query(...), db: Session = Depends(get_db)):
    data = export_service._abundance_matrix(project_id, db)
    return _csv_response(data, "abundance_matrix.csv")


@router.get("/csv/presence-absence-matrix")
def export_presence_matrix(project_id: int = Query(...), db: Session = Depends(get_db)):
    data = export_service._presence_absence_matrix(project_id, db)
    return _csv_response(data, "presence_absence_matrix.csv")


@router.get("/excel")
def export_excel(project_id: int = Query(...), db: Session = Depends(get_db)):
    data = export_service.export_excel(project_id, db)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="econodex_export.xlsx"'},
    )


@router.get("/dwca")
def export_dwca(project_id: int = Query(...), db: Session = Depends(get_db)):
    data = export_service.export_dwca(project_id, db)
    return _zip_response(data, f"dwca_project_{project_id}.zip")


@router.get("/project")
def export_project(
    project_id: int = Query(...),
    include_photos: bool = Query(False),
    db: Session = Depends(get_db),
):
    data = export_service.export_project_zip(project_id, db, include_photos=include_photos)
    return _zip_response(data, f"project_{project_id}_export.zip")


@router.post("/backup")
def manual_backup(project_id: int = Query(...)):
    """Create a manual backup of the database."""
    backup_path = create_backup(project_id, label="manual")
    return {"backup_path": str(backup_path)}
